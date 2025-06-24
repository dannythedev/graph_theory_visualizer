from math_text import get_math_surface
import pygame
import re
import math
from config import *

class Vertex:
    def __init__(self, pos, name):
        self.pos = list(pos)
        self.name = name
        self.highlight = False

    def draw(self, screen, selected=False, hovered=False):
        if self.custom_color:
            color = self.custom_color
        else:
            color = SELECTED_COLOR if self.highlight or selected else VERTEX_HOVER_COLOR if hovered else VERTEX_COLOR

        pygame.draw.circle(screen, VERTEX_OUTLINE_COLOR, self.pos, VERTEX_RADIUS + 2)
        pygame.draw.circle(screen, color, self.pos, VERTEX_RADIUS)
        # label = FONT.render(self.name, True, (255, 255, 255))
        # screen.blit(label, label.get_rect(center=self.pos))
        label = get_math_surface(self.name)
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

    def draw(self, screen, directed=False, offset_angle=0):
        color = EDGE_HOVER_COLOR if self.highlight else EDGE_COLOR
        x1, y1 = self.start.pos
        x2, y2 = self.end.pos

        # Optional offset for opposite direction arrow
        dx, dy = x2 - x1, y2 - y1
        angle = math.atan2(dy, dx)
        if offset_angle != 0:
            offset = 5
            x1 += -offset * math.sin(angle + offset_angle)
            y1 += offset * math.cos(angle + offset_angle)
            x2 += -offset * math.sin(angle + offset_angle)
            y2 += offset * math.cos(angle + offset_angle)

        pygame.draw.line(screen, color, (x1, y1), (x2, y2), 2)

        if self.value:
            mid = ((x1 + x2) // 2, (y1 + y2) // 2)
            # label = FONT.render(str(self.value), True, color)
            # screen.blit(label, label.get_rect(center=mid))
            label = get_math_surface(str(self.value), color)
            screen.blit(label, label.get_rect(center=mid))

        if directed:
            self._draw_arrowhead(screen, x1, y1, x2, y2, color)

    def _draw_arrowhead(self, screen, x1, y1, x2, y2, color):
        angle = math.atan2(y2 - y1, x2 - x1)
        offset = VERTEX_RADIUS + 4  # Pull arrow back from center
        tip_x = x2 - offset * math.cos(angle)
        tip_y = y2 - offset * math.sin(angle)

        length = 10
        left = (tip_x - length * math.cos(angle - math.pi / 6),
                tip_y - length * math.sin(angle - math.pi / 6))
        right = (tip_x - length * math.cos(angle + math.pi / 6),
                 tip_y - length * math.sin(angle + math.pi / 6))
        pygame.draw.polygon(screen, color, [(tip_x, tip_y), left, right])

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

def duplicate_graph(vertices, edges, offset_step=(200, 0), max_attempts=5):
    """
    Tries to duplicate graph to the right, then down, based on screen space.
    Falls back to offscreen duplication only if needed.
    """
    # Get current screen size

    screen_rect = pygame.display.get_surface().get_rect()

    name_map = {}
    existing_names = {v.name for v in vertices}
    new_vertices = []

    # Prepare potential offsets: right first, then down
    offset_directions = [
        (offset_step[0], 0),  # right
        (0, offset_step[0]),  # down
        (offset_step[0], offset_step[0])  # fallback: diagonal
    ]

    for dx, dy in offset_directions:
        candidate_positions = [(v.pos[0] + dx, v.pos[1] + dy) for v in vertices]
        if is_clear_position(vertices, candidate_positions) and is_within_screen(candidate_positions, screen_rect):
            chosen_offset = (dx, dy)
            break
    else:
        # If nothing fits onscreen and clean, just shift right far
        chosen_offset = (offset_step[0] * (max_attempts + 2), 0)

    dx, dy = chosen_offset

    for v in vertices:
        base, _ = get_base_and_index(v.name)

        used_suffixes = {
            get_base_and_index(name)[1]
            for name in existing_names
            if get_base_and_index(name)[0] == base
        }

        new_index = 2
        while new_index in used_suffixes:
            new_index += 1

        new_name = f"{base}_{new_index}"
        existing_names.add(new_name)

        new_pos = [v.pos[0] + dx, v.pos[1] + dy]
        dup = Vertex(new_pos, new_name)
        name_map[v.name] = dup
        new_vertices.append(dup)

    if len(vertices) + len(new_vertices) > 50:
        print("[INFO] Duplication would exceed 50 vertex limit. Aborting.")
        return False

    vertices.extend(new_vertices)

    for e in edges:
        if e.start.name in name_map and e.end.name in name_map:
            edges.append(Edge(name_map[e.start.name], name_map[e.end.name], e.value))

    return True
