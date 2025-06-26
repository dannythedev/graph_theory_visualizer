import colorsys
import re
from string import ascii_uppercase
from config import AVOID_COLORS, VERTEX_RADIUS, DEBUG_FONT


def dfs_stack(adj, start, visited):
    """Iterative DFS to visit all reachable nodes from `start`."""
    stack = [start]
    while stack:
        node = stack.pop()
        if node in visited:
            continue
        visited.add(node)
        stack.extend(n for n in adj[node] if n not in visited)


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
    for n in neighbors:
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
    for neighbor in adj[path[-1]]:
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