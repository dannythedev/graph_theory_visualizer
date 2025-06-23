import pygame
from config import VERTEX_RADIUS, EDGE_CLICK_RADIUS, VERTEX_OUTLINE_COLOR, VERTEX_COLOR, VERTEX_HOVER_COLOR, SELECTED_COLOR
from config import FONT

class Vertex:
    def __init__(self, pos, name):
        self.pos = list(pos)
        self.name = name
        self.highlight = False

    def draw(self, screen, selected=False, hovered=False):
        color = SELECTED_COLOR if self.highlight or selected else VERTEX_HOVER_COLOR if hovered else VERTEX_COLOR
        pygame.draw.circle(screen, VERTEX_OUTLINE_COLOR, self.pos, VERTEX_RADIUS + 2)
        pygame.draw.circle(screen, color, self.pos, VERTEX_RADIUS)
        label = FONT.render(self.name, True, (255, 255, 255))
        screen.blit(label, label.get_rect(center=self.pos))

    def is_clicked(self, pos):
        dx = self.pos[0] - pos[0]
        dy = self.pos[1] - pos[1]
        return dx * dx + dy * dy <= VERTEX_RADIUS ** 2

class Edge:
    def __init__(self, start, end, value=None):
        self.start = start
        self.end = end
        self.value = value
        self.highlight = False

    def draw(self, screen):
        color = (225, 225, 225) if self.highlight else (170, 170, 170)
        pygame.draw.line(screen, color, self.start.pos, self.end.pos, 2)
        if self.value:
            mid = [(s + e) // 2 for s, e in zip(self.start.pos, self.end.pos)]
            label = FONT.render(str(self.value), True, color)
            screen.blit(label, label.get_rect(center=mid))

    def is_clicked(self, pos):
        x1, y1 = self.start.pos
        x2, y2 = self.end.pos
        px, py = pos
        dx, dy = x2 - x1, y2 - y1
        if dx == dy == 0:
            return False
        t = ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)
        if not (0 <= t <= 1):
            return False
        closest = (x1 + t * dx, y1 + t * dy)
        dist_sq = (closest[0] - px) ** 2 + (closest[1] - py) ** 2
        return dist_sq <= EDGE_CLICK_RADIUS ** 2

def get_vertex_at_pos(vertices, pos):
    return next((v for v in vertices if v.is_clicked(pos)), None)

def get_edge_at_pos(edges, pos):
    return next((e for e in edges if e.is_clicked(pos)), None)

def edge_exists(v1, v2, edge_lookup):
    return (min(v1.name, v2.name), max(v1.name, v2.name)) in edge_lookup

def rebuild_edge_lookup(edges):
    return set((min(e.start.name, e.end.name), max(e.start.name, e.end.name)) for e in edges)
