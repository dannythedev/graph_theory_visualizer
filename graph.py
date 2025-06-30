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

    def draw(self, screen, selected=False, hovered=False, st_highlight=False, live_name=None):
        if self.custom_color:
            color = self.custom_color
        else:
            if self.custom_color:
                color = self.custom_color
            elif selected:
                color = SELECTED_COLOR
            elif self.highlight:
                color = HIGHLIGHT_COLOR
            elif hovered:
                color = VERTEX_HOVER_COLOR
            else:
                color = VERTEX_COLOR

        outline_color = ST_OUTLINE_COLOR if st_highlight else VERTEX_OUTLINE_COLOR
        pygame.draw.circle(screen, outline_color, self.pos, VERTEX_RADIUS + 2)
        pygame.draw.circle(screen, color, self.pos, VERTEX_RADIUS)
        label_text = live_name if live_name is not None else self.name
        label_color = DEBUG_HOVER_COLOR if live_name is not None else (255, 255, 255)
        label = get_math_surface(label_text, color=label_color)
        screen.blit(label, label.get_rect(center=self.pos))
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

    def draw(self, screen, directed=False, offset_angle=0, show_weight=False, live_value=None):
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
        thickness = 3 if self.highlight else 2
        pygame.draw.line(screen, color, (x1, y1), (x2, y2), thickness)
        if show_weight:
            display_value = live_value if live_value is not None else self.value
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
                label_color = DEBUG_HOVER_COLOR if live_value is not None else (255, 255, 255)
                label = get_math_surface(str(display_value), label_color)
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


def duplicate_graph(og_vertices, og_edges, spacing=(70, 70), times=1):
    """
    Duplicates the original graph `times` times in a grid layout,
    avoiding overlap and off-screen placement.
    """
    screen_rect = pygame.display.get_surface().get_rect()

    total_vertices_needed = len(og_vertices) * times
    total_vertices_available = VERTEX_LIMIT - len(og_vertices)
    if total_vertices_needed > total_vertices_available:
        print(f"[INFO] Duplication cancelled: {total_vertices_needed} vertices needed exceeds available {total_vertices_available}.")
        return False

    def get_bounding_box_padding():
        xs = [v.pos[0] for v in og_vertices]
        ys = [v.pos[1] for v in og_vertices]
        return (max(xs) - min(xs)) + spacing[0], (max(ys) - min(ys)) + spacing[1]

    def is_valid_placement(candidate_positions):
        return (
            is_clear_position(og_vertices + all_new_vertices, candidate_positions)
            and is_within_screen_margin(candidate_positions, screen_rect, *spacing)
        )

    def get_fallback_offset_positions():
        fallback_offsets = [
            (-cell_w, 0), (0, -cell_h), (-cell_w, -cell_h),
            (cell_w, -cell_h), (-cell_w, cell_h),
            (0, 2 * cell_h), (2 * cell_w, 0), (-2 * cell_w, 0)
        ]
        for fx, fy in fallback_offsets:
            fallback = [(v.pos[0] + fx, v.pos[1] + fy) for v in og_vertices]
            if is_valid_placement(fallback):
                print(f"[INFO] Using fallback offset ({fx},{fy}) for duplicate #{i + 1}")
                return fx, fy, fallback
        return None, None, None

    def create_unique_vertices(dx, dy):
        name_map = {}
        new_vertices = []
        base_suffix_cache = {}
        for v in og_vertices:
            if v.name not in base_suffix_cache:
                base, _ = get_base_and_index(v.name)
                used = {get_base_and_index(n)[1] for n in existing_names if get_base_and_index(n)[0] == base}
                base_suffix_cache[v.name] = (base, used)

            base, used_suffixes = base_suffix_cache[v.name]
            new_index = 2
            while new_index in used_suffixes:
                new_index += 1
            used_suffixes.add(new_index)

            new_name = f"{base}_{new_index}"
            existing_names.add(new_name)
            new_pos = [v.pos[0] + dx, v.pos[1] + dy]
            dup = Vertex(new_pos, new_name)
            name_map[v.name] = dup
            new_vertices.append(dup)
        return name_map, new_vertices

    def create_edges(name_map):
        return [Edge(name_map[e.start.name], name_map[e.end.name], e.value) for e in og_edges]

    cell_w, cell_h = get_bounding_box_padding()
    max_cols = max(1, screen_rect.width // cell_w)

    all_new_vertices, all_new_edges = [], []
    existing_names = {v.name for v in og_vertices}

    for i in range(times):
        col, row = (i + 1) % max_cols, (i + 1) // max_cols
        dx, dy = cell_w * col, cell_h * row
        candidate_positions = [(v.pos[0] + dx, v.pos[1] + dy) for v in og_vertices]

        if not is_valid_placement(candidate_positions):
            dx, dy, candidate_positions = get_fallback_offset_positions()
            if candidate_positions is None:
                print(f"[INFO] Skipping duplication #{i + 1} — no nearby space.")
                continue

        name_map, new_vertices = create_unique_vertices(dx, dy)
        new_edges = create_edges(name_map)

        all_new_vertices.extend(new_vertices)
        all_new_edges.extend(new_edges)

    og_vertices.extend(all_new_vertices)
    og_edges.extend(all_new_edges)
    return True



def apply_graph_complement(vertices, edges, directed=False):
    """Replace edges with their complement, unless it exceeds EDGE_LIMIT."""
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

    # Count how many complement edges would be created
    num_new_edges = len(all_pairs - existing)

    if num_new_edges > EDGE_LIMIT:
        print(f"[INFO] Complement aborted: {num_new_edges} edges would exceed the limit of {EDGE_LIMIT}.")
        return

    for edge in edges:
        edge.start = None
        edge.end = None
        edge.value = None
    edges.clear()  # Remove all old edges in-place

    # Now create the complement edges
    edges.extend([
        Edge(name_to_vertex[a], name_to_vertex[b], value="1")
        for a, b in all_pairs
        if (a, b) not in existing
    ])



