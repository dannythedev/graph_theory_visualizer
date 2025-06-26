# algorithms.py
import pygame
import heapq
import threading
from math_text import get_math_surface
import math

class GraphAlgorithm:
    def __init__(self, name, vertices, edges):
        self.name = name
        self.vertices = vertices
        self.edges = edges
        self.result = []         # e.g., list of vertex names
        self.edge_result = []    # edge path
        self.active = False

        self.source = None
        self.target = None
        self.needs_update = True

        self._thread = None
        self._result_ready = False

    def reset(self):
        self.result.clear()
        self.edge_result.clear()
        self.active = False
        self.needs_update = True
        self._thread = None
        self._result_ready = False

    def update(self, source, target, directed=False):
        if source != self.source or target != self.target:
            self.needs_update = True

        self.source = source
        self.target = target

        if self.needs_update and source and target and self._thread is None:
            self.result.clear()
            self.edge_result.clear()
            self.active = False
            self.needs_update = False
            self._result_ready = False
            self._thread = threading.Thread(target=self._run_thread, args=(source, target, directed))
            self._thread.start()

    def _run_thread(self, source, target, directed):
        self.run(source, target, directed)
        self._result_ready = True
        self.active = True
        self._thread = None

    def render_debug(self, screen, font, y, mouse_pos, directed):
        self.update(self.source, self.target, directed)
        row_rect = pygame.Rect(10, y, 780, 20)
        hovered = row_rect.collidepoint(mouse_pos)
        color = (255, 255, 100) if hovered else (200, 200, 200)

        if self.source and self.target:
            st_label = f"({self.source},{self.target})"
        else:
            st_label = "-"

        if not self.source or not self.target:
            result_surface = font.render("Choose S/T", True, color)
            elements = []
        elif not self._result_ready:
            result_surface = font.render("Computing...", True, color)
            elements = []
        elif self.result == [] and self.active:
            result_surface = font.render("Undefined", True, color)
            elements = []
        elif not self.active:
            result_surface = font.render("Undefined", True, color)
            elements = []
        else:
            result_surface = get_math_surface(", ".join(self.result), color, fontsize=6)
            elements = [(self.result[i], self.result[i + 1]) for i in range(len(self.result) - 1)]
            elements += [self.result[0], self.result[-1]]

        screen.blit(font.render(self.name.upper(), True, color), (10, y))
        screen.blit(get_math_surface(st_label, color, fontsize=5), (160, y))
        screen.blit(result_surface, (220, y))

        return y + 20, hovered, elements

    def has_negative_weights(self):
        for e in self.edges:
            try:
                w = float(e.value) if e.value is not None else 1.0
            except ValueError:
                w = 1.0
            if w < 0:
                return True
        return False


class DijkstraSolver(GraphAlgorithm):
    def __init__(self, vertices, edges):
        super().__init__("DIJKSTRA", vertices, edges)

    def run(self, source_name, target_name=None, directed=False):
        if self.has_negative_weights():
            self.result = []
            self.edge_result = []
            self.active = True
            return

        adj = {v.name: [] for v in self.vertices}
        for e in self.edges:
            try:
                w = float(e.value) if e.value is not None else 1.0
            except ValueError:
                w = 1.0
            adj[e.start.name].append((e.end.name, w))
            if not directed:
                adj[e.end.name].append((e.start.name, w))

        dist = {v: float('inf') for v in adj}
        prev = {}
        dist[source_name] = 0
        heap = [(0, source_name)]

        while heap:
            d, u = heapq.heappop(heap)
            if u == target_name:
                break
            if d > dist[u]:
                continue
            for v, w in adj[u]:
                if dist[u] + w < dist[v]:
                    dist[v] = dist[u] + w
                    prev[v] = u
                    heapq.heappush(heap, (dist[v], v))

        if source_name == target_name:
            self.result = [source_name]
            self.edge_result = []
            self.active = True
            return

        path = [target_name]
        while path[-1] != source_name:
            if path[-1] not in prev:
                self.result = []
                self.edge_result = []
                self.active = False
                return
            path.append(prev[path[-1]])
        path.reverse()

        self.result = path
        self.edge_result = [(path[i], path[i + 1]) for i in range(len(path) - 1)]
        self.active = True


class BellmanFordSolver(GraphAlgorithm):
    def __init__(self, vertices, edges):
        super().__init__("BELLMAN-FORD", vertices, edges)

    def run(self, source_name, target_name=None, directed=False):
        adj = {v.name: [] for v in self.vertices}
        for e in self.edges:
            try:
                w = float(e.value) if e.value is not None else 1.0
            except ValueError:
                w = 1.0
            adj[e.start.name].append((e.end.name, w))
            if not directed:
                adj[e.end.name].append((e.start.name, w))

        dist = {v: float('inf') for v in adj}
        prev = {}
        dist[source_name] = 0

        for _ in range(len(self.vertices) - 1):
            for u in adj:
                for v, w in adj[u]:
                    if dist[u] + w < dist[v]:
                        dist[v] = dist[u] + w
                        prev[v] = u

        for u in adj:
            for v, w in adj[u]:
                if dist[u] + w < dist[v]:
                    self.result = []
                    self.edge_result = []
                    self.active = False
                    return

        if source_name == target_name:
            self.result = [source_name]
            self.edge_result = []
            self.active = True
            return

        path = []
        v = target_name
        while v in prev:
            path.append(v)
            v = prev[v]
        if v != source_name:
            self.result = []
            self.edge_result = []
            self.active = False
            return

        path.append(source_name)
        path.reverse()
        self.result = path
        self.edge_result = [(path[i], path[i + 1]) for i in range(len(path) - 1)]
        self.active = True


class AStarSolver(GraphAlgorithm):
    def __init__(self, vertices, edges):
        super().__init__("A*", vertices, edges)

    def heuristic(self, a, b):
        v1 = next((v for v in self.vertices if v.name == a), None)
        v2 = next((v for v in self.vertices if v.name == b), None)
        if v1 and v2 and hasattr(v1, 'pos') and hasattr(v2, 'pos'):
            x1, y1 = v1.pos
            x2, y2 = v2.pos
            return math.hypot(x2 - x1, y2 - y1)
        return 0

    def run(self, source_name, target_name=None, directed=False):
        adj = {v.name: [] for v in self.vertices}
        for e in self.edges:
            try:
                w = float(e.value) if e.value is not None else 1.0
            except ValueError:
                w = 1.0
            adj[e.start.name].append((e.end.name, w))
            if not directed:
                adj[e.end.name].append((e.start.name, w))

        if self.has_negative_weights():
            self.result = []
            self.edge_result = []
            self.active = True
            return

        open_set = [(0 + self.heuristic(source_name, target_name), 0, source_name)]
        came_from = {}
        g_score = {v: float('inf') for v in adj}
        g_score[source_name] = 0

        while open_set:
            _, current_cost, current = heapq.heappop(open_set)

            if current == target_name:
                break

            for neighbor, weight in adj[current]:
                tentative_g = g_score[current] + weight
                if tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score = tentative_g + self.heuristic(neighbor, target_name)
                    heapq.heappush(open_set, (f_score, tentative_g, neighbor))

        if source_name == target_name:
            self.result = [source_name]
            self.edge_result = []
            self.active = True
            return

        path = [target_name]
        while path[-1] != source_name:
            if path[-1] not in came_from:
                self.result = []
                self.edge_result = []
                self.active = False
                return
            path.append(came_from[path[-1]])
        path.reverse()

        self.result = path
        self.edge_result = [(path[i], path[i + 1]) for i in range(len(path) - 1)]
        self.active = True


def get_all_algorithms(vertices, edges):
    return [
        DijkstraSolver(vertices, edges),
        BellmanFordSolver(vertices, edges),
        AStarSolver(vertices, edges)
    ]

def mark_all_algorithms_dirty(algorithms):
    for alg in algorithms:
        alg.needs_update = True
