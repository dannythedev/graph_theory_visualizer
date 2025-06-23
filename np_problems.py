import itertools

import pygame


class NPProblem:
    def __init__(self, name, vertices, edges):
        self.name = name
        self.vertices = vertices
        self.edges = edges
        self.k = None
        self.result = (False, [])
        self.needs_update = True

    def compute(self, k, directed=False):
        pass

    def update(self, k, directed=False):
        if self.needs_update or self.k != k:
            self.k = k
            self.result = self.compute(k, directed)
            self.needs_update = False

    def render_debug(self, screen, font, k, y, mouse_pos, directed):
        self.update(k, directed)
        found, members = self.result
        lines = [f"{self.name} <G,{k}> = {found}", f"Set: {', '.join(members) if found else 'None'}"]
        area = pygame.Rect(10, y, 300, len(lines) * 20)
        hovered = area.collidepoint(mouse_pos)
        for line in lines:
            text = font.render(line, True, (255, 255, 100) if hovered else (200, 200, 200))
            screen.blit(text, (10, y))
            y += 20
        return y, hovered, members

class IndependentSetSolver(NPProblem):
    def __init__(self, v, e): super().__init__("INDEPENDENT-SET", v, e)
    def compute(self, k, directed=False):
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
    def __init__(self, v, e): super().__init__("CLIQUE", v, e)
    def compute(self, k, directed=False):
        adj = {v.name: set() for v in self.vertices}
        for e in self.edges:
            adj[e.start.name].add(e.end.name)
            if not directed:
                adj[e.end.name].add(e.start.name)
        for combo in itertools.combinations(self.vertices, k):
            names = [v.name for v in combo]
            if all(n2 in adj[n1] for i, n1 in enumerate(names) for n2 in names[i+1:]):
                return True, names
        return False, []

class VertexCoverSolver(NPProblem):
    def __init__(self, v, e): super().__init__("VERTEX-COVER", v, e)
    def compute(self, k, directed=False):
        edge_set = {(e.start.name, e.end.name) for e in self.edges}
        for combo in itertools.combinations(self.vertices, k):
            cover = {v.name for v in combo}
            if all(e[0] in cover or e[1] in cover for e in edge_set):
                return True, list(cover)
        return False, []

class HamiltonianPathSolver(NPProblem):
    def __init__(self, v, e): super().__init__("HAMPATH", v, e)
    def compute(self, k, directed=False):
        if len(self.vertices) < 2: return False, []
        adj = {v.name: set() for v in self.vertices}
        for e in self.edges:
            adj[e.start.name].add(e.end.name)
            if not directed:
                adj[e.end.name].add(e.start.name)
        for path in itertools.permutations([v.name for v in self.vertices]):
            if all(path[i+1] in adj[path[i]] for i in range(len(path)-1)):
                return True, list(path)
        return False, []

def get_all_problems(vertices, edges):
    return [
        IndependentSetSolver(vertices, edges),
        CliqueSolver(vertices, edges),
        VertexCoverSolver(vertices, edges),
        HamiltonianPathSolver(vertices, edges)
    ]

def mark_all_problems_dirty(problems):
    for p in problems:
        p.needs_update = True
