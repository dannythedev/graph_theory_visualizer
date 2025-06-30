import colorsys
import re
from string import ascii_uppercase
from config import AVOID_COLORS, VERTEX_RADIUS, DEBUG_FONT
import pygame

class GraphState:
    def __init__(self, get_vertices, get_edges):
        self.get_vertices = get_vertices
        self.get_edges = get_edges
        self._last_hash = None
        self._adj = None
        self._rev_adj = None
        self._indexed_adj = {}

    def _hash_graph(self):
        v = tuple(sorted(v.name for v in self.get_vertices()))
        e = tuple(sorted((e.start.name, e.end.name) for e in self.get_edges()))
        return hash((v, e))

    def invalidate(self):
        self._last_hash = None

    def _check_update(self):
        new_hash = self._hash_graph()
        if new_hash != self._last_hash:
            self._adj_dict = {}
            self._rev_adj = None
            self._indexed_adj.clear()
            self._last_hash = new_hash

    def get_adj(self, directed=False):
        self._check_update()
        key = "directed" if directed else "undirected"
        if not hasattr(self, "_adj_dict"):
            self._adj_dict = {}

        if key in self._adj_dict:
            return self._adj_dict[key]

        adj = {v.name: [] for v in self.get_vertices()}
        for e in self.get_edges():
            w = float(e.value) if e.value is not None else 1.0
            adj[e.start.name].append((e.end.name, w))
            if not directed:
                adj[e.end.name].append((e.start.name, w))

        self._adj_dict[key] = adj
        return adj

    def get_rev_adj(self):
        self._check_update()
        if self._rev_adj is None:
            rev = {v.name: set() for v in self.get_vertices()}
            for e in self.get_edges():
                rev[e.end.name].add(e.start.name)
            self._rev_adj = rev
        return self._rev_adj

    def get_indexed_adj(self, directed=False):
        self._check_update()
        key = directed
        if key in self._indexed_adj:
            return self._indexed_adj[key]

        index_map = {v.name: i for i, v in enumerate(self.get_vertices())}
        adj = {i: set() for i in index_map.values()}
        for e in self.get_edges():
            i = index_map[e.start.name]
            j = index_map[e.end.name]
            adj[i].add(j)
            if not directed:
                adj[j].add(i)

        self._indexed_adj[key] = adj
        return adj, index_map


def dfs_stack(adj, start, visited):
    """Iterative DFS to visit all reachable nodes from `start`."""
    stack = [start]
    while stack:
        node = stack.pop()
        if node in visited:
            continue
        visited.add(node)
        neighbors = adj.get(node, [])
        stack.extend(n for n, _ in neighbors if n not in visited)


def generic_dfs(adj, v, visited, *, parent=None, rec_stack=None,
                tin=None, low=None, time=None, bridges=None,
                on_path=None, on_exit=None):
    """
    Generic DFS with customizable hooks:
    - `rec_stack`: for cycle detection in directed graphs
    - `tin`, `low`, `time`, `bridges`: for bridge-finding
    - `on_path(path)`: for longest path backtracking
    - `on_exit(node)`: for postorder (Kosaraju)
    """

    visited.add(v)
    if rec_stack is not None:
        rec_stack.add(v)
    if tin is not None:
        tin[v] = low[v] = time[0]
        time[0] += 1

    neighbors = adj[v]
    for n, _ in neighbors:
        if n == parent:
            continue
        if n not in visited:
            generic_dfs(adj, n, visited,
                        parent=v, rec_stack=rec_stack,
                        tin=tin, low=low, time=time, bridges=bridges,
                        on_path=on_path, on_exit=on_exit)
            if low is not None:
                low[v] = min(low[v], low[n])
                if bridges is not None and low[n] > tin[v]:
                    bridges.append((min(v, n), max(v, n)))
        else:
            if low is not None:
                low[v] = min(low[v], tin[n])
            if rec_stack is not None and n in rec_stack:
                raise Exception("CycleDetected")

    if rec_stack is not None:
        rec_stack.remove(v)
    if on_exit:
        on_exit(v)


def dfs_paths_backtrack(adj, path, visited, on_path_found):
    """Simple recursive DFS for full-path traversal (used for longest paths)."""
    on_path_found(path)
    for neighbor, _ in adj[path[-1]]:
        if neighbor not in visited:
            dfs_paths_backtrack(adj, path + [neighbor], visited | {neighbor}, on_path_found)

def color_distance(c1, c2):
    # Euclidean distance in RGB
    return sum((a - b) ** 2 for a, b in zip(c1, c2)) ** 0.5

def generate_color_for_index(i):
    for attempt in range(10):  # Try 10 variations per index
        h = ((i + attempt * 0.2) * 0.618033988749895) % 1.0  # Golden ratio spread
        s = 0.5  # Moderate saturation
        v = 0.85  # Not too bright

        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        rgb = (int(r * 255), int(g * 255), int(b * 255))

        # Make sure it's not too close to any UI color
        if all(color_distance(rgb, avoid) > 60 for avoid in AVOID_COLORS):
            return rgb

    # Fallback if all were too close
    return rgb

def get_next_available_vertex_name(vertices, name_iter):
    """Returns the next available vertex name (A-Z, then A', B', ..., then A'', B'', ...)"""
    used_names = {v.name for v in vertices}

    # Step 1: Try basic iterator first (A–Z)
    try:
        while True:
            name = next(name_iter)
            if name not in used_names:
                return name
    except StopIteration:
        pass

    # Step 2: Fallback: iterate over A–Z with increasing apostrophe suffixes
    suffix = "'"
    while True:
        for base in ascii_uppercase:
            candidate = base + suffix
            if candidate not in used_names:
                return candidate
        suffix += "'"  # Increase suffix for next round (e.g., A'', B'', ...)


def get_base_and_index(name):
    match = re.match(r"^(.*?)(?:_(\d+))?$", name)
    if match:
        base = match.group(1)
        index = int(match.group(2)) if match.group(2) else 1
        return base, index
    return name, 1

def is_clear_position(vertices, new_positions, min_dist=2 * VERTEX_RADIUS + 5):
    """Check if new positions avoid overlaps with any existing vertex."""
    for nx, ny in new_positions:
        for v in vertices:
            dx, dy = nx - v.pos[0], ny - v.pos[1]
            if dx * dx + dy * dy < min_dist * min_dist:
                return False
    return True

def is_within_screen(positions, screen_rect):
    """Returns True if all positions fall within screen bounds."""
    for x, y in positions:
        if not screen_rect.collidepoint(x, y):
            return False
    return True

def is_within_screen_margin(positions, rect, margin_x, margin_y):
    for x, y in positions:
        if x < -margin_x or x > rect.width + margin_x:
            return False
        if y < -margin_y or y > rect.height + margin_y:
            return False
    return True


def update_k_value_from_input(input_text):
    try:
        return max(1, int(input_text))
    except ValueError:
        return None

def draw_fps(screen, clock):
    fps = int(clock.get_fps())
    text = DEBUG_FONT.render(f"{fps} FPS", True, (150, 255, 150))
    screen.blit(text, text.get_rect(bottomright=(screen.get_width()-20, screen.get_height()-5)))

def deduplicate_edges_for_undirected(edges):
    seen = set()
    new_edges = []
    for edge in edges:
        u, v = edge.start, edge.end
        key = tuple(sorted([u.name, v.name]))
        if key not in seen:
            seen.add(key)
            new_edges.append(edge)
    edges[:] = new_edges  # Update the list in-place


def generate_random_graph(vertices, edges, name_iter, min_v=5, max_v=24, min_e=5, max_e=30):
    from graph import Vertex, Edge  # Already imported
    import random

    vertices.clear()
    edges.clear()

    n = random.randint(min_v, max_v)
    max_possible_edges = n * (n - 1) // 2
    m = min(random.randint(min_e, max_e), max_possible_edges)

    screen_rect = pygame.display.get_surface().get_rect()

    # Define a central region (half the screen size)
    graph_width = screen_rect.width // 2
    graph_height = screen_rect.height // 2

    # Center the graph within the screen
    left = (screen_rect.width - graph_width) // 2
    top = (screen_rect.height - graph_height) // 2
    right = left + graph_width
    bottom = top + graph_height

    # Generate vertices with spacing
    attempts = 0
    max_attempts = 500  # Prevent infinite loops

    while len(vertices) < n and attempts < max_attempts:
        name = get_next_available_vertex_name(vertices, name_iter)
        x = random.randint(left, right)
        y = random.randint(top, bottom)

        candidate = [(x, y)]
        if is_clear_position(vertices, candidate):
            vertices.append(Vertex([x, y], name))
        attempts += 1

    if len(vertices) < n:
        print(f"[WARN] Only placed {len(vertices)} of {n} requested vertices due to spacing limits.")

    # Build all potential edges (undirected)
    potential_edges = [
        (a, b) for i, a in enumerate(vertices) for b in vertices[i + 1:]
    ]
    random.shuffle(potential_edges)

    # Step 1: Build a random spanning tree (ensures connectivity)
    connected = set()
    unconnected = set(vertices)
    current = unconnected.pop()
    connected.add(current)

    while unconnected:
        next_v = unconnected.pop()
        target = random.choice(list(connected))
        weight = str(random.randint(1, 99))
        edges.append(Edge(target, next_v, value=weight))
        connected.add(next_v)

    # Step 2: Add remaining random edges, avoiding duplicates
    edge_set = {(min(e.start.name, e.end.name), max(e.start.name, e.end.name)) for e in edges}
    for a, b in potential_edges:
        key = (min(a.name, b.name), max(a.name, b.name))
        if key not in edge_set:
            edges.append(Edge(a, b, value=str(random.randint(1, 99))))
            edge_set.add(key)
        if len(edges) >= m:
            break
