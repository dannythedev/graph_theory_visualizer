import itertools
import threading
import pygame
from math_text import get_math_surface
from functools import lru_cache


class NPProblem:
    def __init__(self, name, vertices, edges):
        self.name = name
        self.vertices = vertices
        self.edges = edges
        self.k = None
        self.result = (None, [])  # None = still computing
        self.needs_update = True
        self._thread = None

    def compute(self, k, directed):  # Override in subclasses
        return False, []

    def _run_compute_thread(self, k, directed):
        result = self.compute(k, directed)
        self.result = result
        self.needs_update = False

    def update(self, k, directed=False):
        if self.needs_update or self.k != k:
            self.k = k
            self.result = (None, [])  # Mark as computing
            self.needs_update = False
            self._thread = threading.Thread(target=self._run_compute_thread, args=(k, directed))
            self._thread.start()


    def render_debug(self, screen, font, k, y, mouse_pos, directed):
        self.update(k, directed)
        found, members = self.result

        # Check hover over row
        full_area = pygame.Rect(10, y, 780, 20)
        hovered = full_area.collidepoint(mouse_pos)
        color = (255, 255, 100) if hovered else (200, 200, 200)

        # Column values
        title = self.name
        k_input = f"k={k}" if self.name not in ["HAMPATH", "HAMCYCLE", "LONGEST-PATH"] else ""

        # Render result
        if found is None:
            result = "Undefined"
        elif found and members:
            latex_expr = r",\ ".join(members)
            result = get_math_surface(latex_expr, color, fontsize=6)
        else:
            result = "None"

        # Fixed column x-positions
        title_x = 10
        k_x = 160
        result_x = 220

        # Render and blit each column
        screen.blit(font.render(title, True, color), (title_x, y))
        screen.blit(font.render(k_input, True, color), (k_x, y))
        if isinstance(result, pygame.Surface):
            screen.blit(result, (result_x, y))
        else:
            screen.blit(font.render(result, True, color), (result_x, y))

        y += 20
        return y, hovered, members


class IndependentSetSolver(NPProblem):
    def __init__(self, v, e): super().__init__("INDEPENDENT-SET", v, e)
    def compute(self, k, directed=False):
        if k > len(self.vertices):
            return False, []

        # Optional: skip if graph is fully connected
        edge_count = len(self.edges)
        if not directed and edge_count >= len(self.vertices) * (len(self.vertices) - 1) // 2:
            return False, []

        adj = {v.name: set() for v in self.vertices}
        for e in self.edges:
            adj[e.start.name].add(e.end.name)
            if not directed:
                adj[e.end.name].add(e.start.name)
        for combo in itertools.combinations(self.vertices, k):
            names = [v.name for v in combo]
            if all(n2 not in adj[n1] for i, n1 in enumerate(names) for n2 in names[i+1:]):
                return True, names
        return False, []


class CliqueSolver(NPProblem):
    def __init__(self, v, e):
        super().__init__("CLIQUE", v, e)

    def compute(self, k, directed=False):
        if k < 1 or len(self.vertices) < k:
            return False, []

        # Always treat as undirected
        adj = {v.name: set() for v in self.vertices}
        for edge in self.edges:
            adj[edge.start.name].add(edge.end.name)
            adj[edge.end.name].add(edge.start.name)

        # Try all vertex sets of size k
        for group in itertools.combinations(self.vertices, k):
            names = [v.name for v in group]
            if all(n2 in adj[n1] for n1, n2 in itertools.combinations(names, 2)):
                return True, names

        return False, []

class VertexCoverSolver(NPProblem):
    def __init__(self, v, e): super().__init__("VERTEX-COVER", v, e)
    def compute(self, k, directed=False):
        if k > len(self.vertices):
            return False, []

        if k < 1 and self.edges:
            return False, []

        edge_set = {(e.start.name, e.end.name) for e in self.edges}
        for combo in itertools.combinations(self.vertices, k):
            cover = {v.name for v in combo}
            if all(e[0] in cover or e[1] in cover for e in edge_set):
                return True, list(cover)
        return False, []


class HamiltonianPathSolver(NPProblem):
    def __init__(self, v, e):
        super().__init__("HAMPATH", v, e)

    def compute(self, k, directed=False, cancel_event=None):
        if len(self.vertices) < 2:
            return False, []

        # Map vertex names to indices for bitmasking
        index_map = {v.name: i for i, v in enumerate(self.vertices)}
        name_map = {i: v.name for v, i in zip(self.vertices, index_map.values())}
        n = len(self.vertices)

        # Build adjacency list (indexed)
        adj = {i: set() for i in range(n)}
        for edge in self.edges:
            u = index_map[edge.start.name]
            v = index_map[edge.end.name]
            adj[u].add(v)
            if not directed:
                adj[v].add(u)

        @lru_cache(maxsize=None)
        def dp(current, visited):
            if visited == (1 << n) - 1:
                return [current]  # path ends here

            for neighbor in adj[current]:
                if not (visited & (1 << neighbor)):
                    suffix = dp(neighbor, visited | (1 << neighbor))
                    if suffix:
                        return [current] + suffix
            return []

        # Try starting from each node
        for start in range(n):
            path = dp(start, 1 << start)
            if path and len(path) == n:
                return True, [name_map[i] for i in path]

        return False, []

class KColoringSolver(NPProblem):
    def __init__(self, v, e):
        super().__init__("k-COLORING", v, e)

    def compute(self, k, directed=False):
        if directed:
            return None, []

        if k < 1 or len(self.vertices) == 0:
            return False, []

        # Build adjacency map
        adj = {v.name: set() for v in self.vertices}
        for e in self.edges:
            adj[e.start.name].add(e.end.name)
            if not directed:
                adj[e.end.name].add(e.start.name)

        # Recursive backtracking to try color assignments
        names = [v.name for v in self.vertices]
        color_map = {}

        def backtrack(index):
            if index == len(names):
                return True  # all nodes colored

            node = names[index]
            for color in range(k):
                if all(color_map.get(neigh) != color for neigh in adj[node]):
                    color_map[node] = color
                    if backtrack(index + 1):
                        return True
                    del color_map[node]  # backtrack

            return False

        success = backtrack(0)
        if success:
            # Create a sorted color-class output
            colored_groups = {}
            for node, color in color_map.items():
                colored_groups.setdefault(color, []).append(node)

            # Flatten groups for display
            flat_list = [f"{color}: [{', '.join(sorted(group))}]" for color, group in sorted(colored_groups.items())]
            return True, flat_list
        else:
            return False, []

class HamiltonianCycleSolver(NPProblem):
    def __init__(self, v, e):
        super().__init__("HAMCYCLE", v, e)

    def compute(self, k, directed=False, cancel_event=None):
        if len(self.vertices) < 2:
            return False, []

        index_map = {v.name: i for i, v in enumerate(self.vertices)}
        name_map = {i: v.name for v, i in zip(self.vertices, index_map.values())}
        n = len(self.vertices)

        # Build adjacency list (indexed)
        adj = {i: set() for i in range(n)}
        for edge in self.edges:
            u = index_map[edge.start.name]
            v = index_map[edge.end.name]
            adj[u].add(v)
            if not directed:
                adj[v].add(u)

        @lru_cache(maxsize=None)
        def dp(current, visited):
            if visited == (1 << n) - 1:
                return current in adj[start]  # cycle if can return to start

            for neighbor in adj[current]:
                if not (visited & (1 << neighbor)):
                    if dp(neighbor, visited | (1 << neighbor)):
                        path_map[(visited, current)] = neighbor
                        return True
            return False

        for start in range(n):
            path_map = {}
            if dp(start, 1 << start):
                # Reconstruct path
                path = [start]
                visited = 1 << start
                curr = start
                while len(path) < n:
                    curr = path_map[(visited, curr)]
                    visited |= 1 << curr
                    path.append(curr)
                path.append(start)  # close the cycle
                return True, [name_map[i] for i in path]

        return False, []

class MinCutSolver(NPProblem):
    def __init__(self, v, e):
        super().__init__("MIN-CUT", v, e)

    def compute(self, k, directed=False):
        from itertools import combinations

        if k >= len(self.vertices) - 1:
            return False, []

        # Build adjacency map
        adj = {v.name: set() for v in self.vertices}
        for edge in self.edges:
            adj[edge.start.name].add(edge.end.name)
            if not directed:
                adj[edge.end.name].add(edge.start.name)

        def is_disconnected(excluded):
            seen = set()
            remaining = [v.name for v in self.vertices if v.name not in excluded]
            if not remaining:
                return True

            def dfs(u):
                seen.add(u)
                for v in adj[u]:
                    if v not in excluded and v not in seen:
                        dfs(v)

            dfs(remaining[0])
            return len(seen) < len(remaining)

        # Try all sets of size k
        for group in combinations(self.vertices, k):
            names = {v.name for v in group}
            if is_disconnected(names):
                return True, list(names)

        return False, []

class LongestPathSolver(NPProblem):
    def __init__(self, v, e):
        super().__init__("LONGEST-PATH", v, e)

    def compute(self, k, directed=False):
        adj = {v.name: set() for v in self.vertices}
        for e in self.edges:
            adj[e.start.name].add(e.end.name)
            if not directed:
                adj[e.end.name].add(e.start.name)

        longest = []

        def dfs(path, visited):
            nonlocal longest
            if len(path) > len(longest):
                longest = list(path)
            for neighbor in adj[path[-1]]:
                if neighbor not in visited:
                    dfs(path + [neighbor], visited | {neighbor})

        for v in self.vertices:
            dfs([v.name], {v.name})

        return (len(longest) > 1), longest


def get_all_problems(vertices, edges):
    return [
        KColoringSolver(vertices, edges),
        VertexCoverSolver(vertices, edges),
        HamiltonianCycleSolver(vertices, edges),
        HamiltonianPathSolver(vertices, edges),
        LongestPathSolver(vertices, edges),
        IndependentSetSolver(vertices, edges),
        CliqueSolver(vertices, edges),
        MinCutSolver(vertices, edges),

    ]



def mark_all_problems_dirty(problems):
    for p in problems:
        p.needs_update = True
