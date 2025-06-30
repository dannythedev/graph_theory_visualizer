import pygame
from math_text import get_math_surface
from utils import generic_dfs, dfs_stack, GraphState


class GraphDiagnostics:
    def __init__(self, vertices, edges):
        self.hovered_diagnostic = None
        self.needs_update = True
        self.vertices = vertices
        self.edges = edges
        self.info = {}
        self.bridges = []
        self.graph_state = GraphState(lambda: self.vertices, lambda: self.edges)

    def reset(self):
        self.hovered_diagnostic = None
        self.needs_update = True
        self.info.clear()
        self.bridges.clear()

    def mark_dirty(self):
        self.needs_update = True
        self.graph_state.invalidate()

    def update(self, directed=False, compute_enabled=True):
        if compute_enabled:
            if not self.needs_update:
                return
            self.needs_update = False

            self.adj = self.graph_state.get_adj(directed)
            self.rev_adj = self.graph_state.get_rev_adj() if directed else None

            # Core structure
            self.info.clear()
            visited = set()
            self.info["Cyclic"] = self._has_cycle(directed, visited.copy())
            self.info["Components"] = self._component_count(visited.copy())

            self.info["SCCs"] = (
                self._strongly_connected_components() if directed else self.info["Components"]
            )

            self.info["Tree"] = not directed and not self.info["Cyclic"] and self.info["Components"] == 1
            self.info["Forest"] = not directed and not self.info["Cyclic"]
            self.info["Bipartite"] = self._is_bipartite() if not directed else "N/A"

            # Bridges
            self.bridges = self._find_bridges()
            self.info["Bridges"] = (len(self.bridges), self.bridges)

            # Degree stats
            degrees = [(v.name, len(self.adj[v.name])) for v in self.vertices]
            if degrees:
                max_val = max(degrees, key=lambda x: x[1])[1]
                min_val = min(degrees, key=lambda x: x[1])[1]
                max_nodes = [name for name, deg in degrees if deg == max_val]
                min_nodes = [name for name, deg in degrees if deg == min_val]
            else:
                max_val, min_val, max_nodes, min_nodes = 0, 0, [], []

            self.info["Max Degree"] = (max_val, max_nodes)
            self.info["Min Degree"] = (min_val, min_nodes)

    def _find_bridges(self):
        time = [0]
        visited = set()
        tin = {}
        low = {}
        bridges = []

        for v in self.adj:
            if v not in visited:
                generic_dfs(self.adj, v, visited, tin=tin, low=low, time=time, bridges=bridges)

        return bridges

    def _has_cycle(self, directed, visited):
        if directed:
            rec_stack = set()
            try:
                for v in self.adj:
                    if v not in visited:
                        generic_dfs(self.adj, v, visited, rec_stack=rec_stack)
                return False
            except Exception as e:
                if str(e) == "CycleDetected":
                    return True
                return None
        else:
            def dfs(u, parent):
                visited.add(u)
                for v, _ in self.adj[u]:
                    if v not in visited:
                        if dfs(v, u):
                            return True
                    elif v != parent:
                        return True
                return False

            for v in self.adj:
                if v not in visited:
                    if dfs(v, None):
                        return True
            return False

    def _component_count(self, visited):
        count = 0
        for v in self.adj:
            if v not in visited:
                dfs_stack(self.adj, v, visited)
                count += 1
        return count

    def _strongly_connected_components(self):
        visited = set()
        order = []

        for v in self.adj:
            if v not in visited:
                generic_dfs(self.adj, v, visited, on_exit=order.append)

        visited.clear()
        count = 0
        for v in reversed(order):
            if v not in visited:
                dfs_stack(self.rev_adj, v, visited)
                count += 1

        return count

    def _is_bipartite(self):
        color = {}
        for v in self.adj:
            if v not in color:
                queue = [v]
                color[v] = 0
                while queue:
                    u = queue.pop()
                    for n, _ in self.adj[u]:
                        if n not in color:
                            color[n] = 1 - color[u]
                            queue.append(n)
                        elif color[n] == color[u]:
                            return False
        return True

    def render(self, screen, font, mouse_pos=None):
        y_start = screen.get_height() - len(self.info) * 15 - 115
        self.hovered_diagnostic = None

        for key, val in self.info.items():
            is_hovered = mouse_pos and pygame.Rect(10, y_start, 190, 15).collidepoint(mouse_pos)
            color = (255, 255, 100) if is_hovered else (180, 180, 180)

            screen.blit(font.render(f"{key}:", True, color), (10, y_start))

            if isinstance(val, tuple) and len(val) == 2:
                count, elements = val
                screen.blit(font.render(f"{count}", True, color), (150, y_start))

                if all(isinstance(x, tuple) and len(x) == 2 for x in elements):  # edges
                    latex_expr = r",\ ".join(f"({a},{b})" for a, b in elements)
                else:  # vertices
                    latex_expr = r",\ ".join(elements)

                latex_surface = get_math_surface(latex_expr, color, fontsize=5)
                baseline = y_start + (font.get_height() - latex_surface.get_height()) // 2
                screen.blit(latex_surface, (200, baseline))

                if is_hovered:
                    self.hovered_diagnostic = (key, elements)

            else:
                screen.blit(font.render(str(val), True, color), (150, y_start))
                if is_hovered:
                    self.hovered_diagnostic = (key, None)  # Mark row as hovered, but no elements

            y_start += 14
