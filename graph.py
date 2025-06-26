from math_text import get_math_surface
import math
from config import *
from utils import get_base_and_index, is_within_screen_margin, is_clear_position


class Vertex:
    def __init__(self, pos, name, custom_color=None):
        self.pos = list(pos)
        self.name = name
        self.highlight = False
        self.custom_color = custom_color

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
            # Midpoint of the edge
            mid_x = (x1 + x2) / 2
            mid_y = (y1 + y2) / 2

            # Compute perpendicular offset (normal vector)
            normal_len = 15  # pixels away from the line
            nx = -dy
            ny = dx
            length = math.hypot(nx, ny)
            if length != 0:
                nx /= length
                ny /= length

            # Apply the perpendicular offset
            label_offset_x = mid_x + nx * normal_len
            label_offset_y = mid_y + ny * normal_len

            label = get_math_surface(str(self.value), color)
            rect = label.get_rect(center=(label_offset_x, label_offset_y))
            screen.blit(label, rect)

        if directed:
            self._draw_arrowhead(screen, x1, y1, x2, y2, color)

    @staticmethod
    def _draw_arrowhead(screen, x1, y1, x2, y2, color):
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

# def get_edges_at_pos_original(edges, pos):
#     return [e for e in edges if e.is_clicked(pos)]

def get_edge_at_pos(edges, pos):
    closest_edge = None
    closest_dist_sq = float('inf')

    for e in edges:
        # Determine if this edge has an opposite
        is_opposite = any(e2.start == e.end and e2.end == e.start for e2 in edges if e2 != e)
        offset_angle = math.pi / 18 if is_opposite else 0

        # Compute offset positions to match how it's drawn
        x1, y1 = e.start.pos
        x2, y2 = e.end.pos
        dx, dy = x2 - x1, y2 - y1
        angle = math.atan2(dy, dx)

        if offset_angle != 0:
            offset = 5
            x1 += -offset * math.sin(angle + offset_angle)
            y1 += offset * math.cos(angle + offset_angle)
            x2 += -offset * math.sin(angle + offset_angle)
            y2 += offset * math.cos(angle + offset_angle)

        # Same logic for finding the closest point
        px, py = pos
        dx, dy = x2 - x1, y2 - y1
        if dx == dy == 0:
            continue
        t = ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)
        t = max(0, min(1, t))  # Clamp t to [0, 1]
        closest = (x1 + t * dx, y1 + t * dy)
        dist_sq = (closest[0] - px) ** 2 + (closest[1] - py) ** 2

        if dist_sq <= EDGE_CLICK_RADIUS ** 2 and dist_sq < closest_dist_sq:
            closest_edge = e
            closest_dist_sq = dist_sq

    return closest_edge



def edge_exists(v1, v2, edge_lookup, directed=False):
    if directed:
        return (v1.name, v2.name) in edge_lookup
    return (min(v1.name, v2.name), max(v1.name, v2.name)) in edge_lookup


def rebuild_edge_lookup(edges):
    return set((min(e.start.name, e.end.name), max(e.start.name, e.end.name)) for e in edges)


def duplicate_graph(og_vertices, og_edges, spacing=(50, 50), times=1):
    """
    Duplicates the original graph `times` times by laying out copies in a grid of cells
    determined by the graph's bounding box and the given spacing.
    - spacing: (horizontal_spacing, vertical_spacing) between cells.
    """
    screen_rect = pygame.display.get_surface().get_rect()

    # Compute bounding box of the original graph
    xs = [v.pos[0] for v in og_vertices]
    ys = [v.pos[1] for v in og_vertices]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    graph_w = max_x - min_x
    graph_h = max_y - min_y
    cell_w = graph_w + spacing[0]
    cell_h = graph_h + spacing[1]

    # Determine how many columns fit on screen
    max_cols = max(1, screen_rect.width // cell_w)

    all_new_vertices = []
    all_new_edges = []
    existing_names = {v.name for v in og_vertices}
    base_vertices = list(og_vertices)
    base_edges = list(og_edges)

    for i in range(times):

        # Enforce maximum vertex count
        if len(og_vertices) + len(all_new_vertices) > VERTEX_LIMIT:
            print(f"[INFO] Duplication would exceed {VERTEX_LIMIT} vertex limit. Aborting further duplicates.")
            break
        # Calculate grid cell for this duplicate (skip cell 0,0 reserved for original)
        col = (i + 1) % max_cols
        row = (i + 1) // max_cols
        dx = cell_w * col
        dy = cell_h * row

        # Proposed positions for the new copy
        candidate_positions = [(v.pos[0] + dx, v.pos[1] + dy) for v in base_vertices]

        # Skip if it would overlap or be too far off-screen
        if not (is_clear_position(og_vertices + all_new_vertices, candidate_positions)
                and is_within_screen_margin(candidate_positions, screen_rect, spacing[0], spacing[1])):
            print(f"[INFO] Skipping duplication #{i+1} — cell ({col},{row}) not available.")
            continue

        # Create duplicated vertices with new unique names
        name_map = {}
        new_vertices = []
        for v in base_vertices:
            base, _ = get_base_and_index(v.name)
            used_suffixes = {get_base_and_index(n)[1] for n in existing_names if get_base_and_index(n)[0] == base}
            new_index = 2
            while new_index in used_suffixes:
                new_index += 1
            new_name = f"{base}_{new_index}"
            existing_names.add(new_name)
            new_pos = [v.pos[0] + dx, v.pos[1] + dy]
            dup = Vertex(new_pos, new_name)
            name_map[v.name] = dup
            new_vertices.append(dup)

        # Create duplicated edges between the new vertices
        new_edges = [
            Edge(name_map[e.start.name], name_map[e.end.name], e.value)
            for e in base_edges
        ]

        all_new_vertices.extend(new_vertices)
        all_new_edges.extend(new_edges)


    # Append all the new copies to the original lists
    og_vertices.extend(all_new_vertices)
    og_edges.extend(all_new_edges)
    return True


def apply_graph_complement(vertices, edges, directed=False):
    """Replace edges with their complement."""
    name_to_vertex = {v.name: v for v in vertices}
    all_pairs = {
        (a.name, b.name)
        for i, a in enumerate(vertices)
        for j, b in enumerate(vertices)
        if i != j and (directed or a.name < b.name)
    }

    existing = {(e.start.name, e.end.name) for e in edges}
    if not directed:
        existing |= {(e.end.name, e.start.name) for e in edges}

    new_edges = [
        Edge(name_to_vertex[a], name_to_vertex[b])
        for a, b in all_pairs
        if (a, b) not in existing
    ]

    edges[:] = new_edges
