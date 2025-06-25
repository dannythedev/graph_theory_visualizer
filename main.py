import math
import sys
import string
import json
from graph import apply_graph_complement
from diagnostics import GraphDiagnostics
from config import *
from graph import Vertex, Edge, get_vertex_at_pos, get_edge_at_pos, duplicate_graph
from physics import PhysicsSystem
from np_problems import get_all_problems, mark_all_problems_dirty

def save_graph(vertices, edges, directed=False, filename="graph.json"):
    with open(filename, "w") as f:
        json.dump({
            "directed": directed,
            "vertices": [{"name": v.name, "pos": v.pos} for v in vertices],
            "edges": [{"start": e.start.name, "end": e.end.name, "value": e.value} for e in edges]
        }, f)


def load_graph(filename, vertices, edges):
    try:
        with open(filename, "r") as f:
            data = json.load(f)

        if "vertices" not in data or "edges" not in data:
            raise ValueError("Invalid file format: missing 'vertices' or 'edges'.")

        directed = data.get("directed", False)  # default to False for backward compatibility

        name_map = {
            v["name"]: Vertex(v["pos"], v["name"])
            for v in data["vertices"]
        }

        vertices.clear()
        vertices.extend(name_map.values())
        edges.clear()
        edges.extend(
            Edge(name_map[e["start"]], name_map[e["end"]], e.get("value"))
            for e in data["edges"]
        )

        return iter(name for name in string.ascii_uppercase if name not in name_map), directed

    except Exception as e:
        print(f"[ERROR] Failed to load graph from '{filename}': {e}")
        return iter(string.ascii_uppercase), False


def draw_button(screen, rect, text, hovered):
    pygame.draw.rect(screen, BUTTON_HOVER_COLOR if hovered else BUTTON_COLOR, rect, border_radius=8)
    label = FONT.render(text, True, BUTTON_TEXT_COLOR)
    screen.blit(label, label.get_rect(center=rect.center))

def draw_slider(screen, duplicate_count, SLIDER_MIN, SLIDER_MAX):
    slider_rect = DUPLICATE_SLIDER_RECT
    slider_x = slider_rect.x
    slider_y = slider_rect.y
    slider_w = slider_rect.width
    slider_h = slider_rect.height
    slider_radius = slider_h // 2

    # Track
    pygame.draw.rect(screen, (50, 50, 50), slider_rect, border_radius=slider_radius)

    # Fill
    fill_ratio = (duplicate_count - SLIDER_MIN) / (SLIDER_MAX - SLIDER_MIN)
    fill_width = int(fill_ratio * slider_w)
    pygame.draw.rect(screen, (180, 180, 180), (slider_x, slider_y, fill_width, slider_h), border_radius=slider_radius)

    # Knob position
    knob_x = slider_x + fill_width
    knob_y = slider_y + slider_h // 2
    knob_radius = slider_radius + 4
    knob_rect = pygame.Rect(knob_x - knob_radius, knob_y - knob_radius, knob_radius * 2, knob_radius * 2)

    # Detect hover
    mouse_pos = pygame.mouse.get_pos()
    is_hovered = knob_rect.collidepoint(mouse_pos)
    knob_color = (240, 240, 180) if is_hovered else (200, 200, 200)

    # Knob
    pygame.draw.circle(screen, knob_color, (knob_x, knob_y), knob_radius)

    # Label inside knob
    dup_count_text = FONT.render(f"x{duplicate_count}", True, (30, 30, 30))
    screen.blit(dup_count_text, dup_count_text.get_rect(center=(knob_x, knob_y)))


def update_k_value_from_input(input_text):
    try:
        return max(1, int(input_text))
    except ValueError:
        return None

def draw_fps(screen, clock):
    fps = int(clock.get_fps())
    text = DEBUG_FONT.render(f"{fps} FPS", True, (150, 255, 150))
    screen.blit(text, text.get_rect(bottomright=(screen.get_width()-20, screen.get_height()-5)))

import colorsys

# Colors to avoid (RGB)
AVOID_COLORS = [
    (100, 149, 237),  # VERTEX_COLOR
    (70, 130, 180),   # VERTEX_HOVER_COLOR
    (255, 99, 71),    # SELECTED_COLOR
]

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


def apply_kcolor_highlight(solver, hovered, vertices):
    # Clear all custom colors by default
    for v in vertices:
        v.custom_color = None

    # Only highlight if hovering and result is valid
    if hovered and solver.result[0] and solver.result[1]:
        groups = solver.result[1]
        for i, group in enumerate(groups):
            try:
                group_label, raw_members = group.split(":")
                node_names = raw_members.strip(" []").split(", ")
                color = generate_color_for_index(i)
                for v in vertices:
                    if v.name in node_names:
                        v.custom_color = color
            except Exception as e:
                print(f"Error parsing k-color group '{group}':", e)

from string import ascii_uppercase

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

class ZoomManager:
    def __init__(self):
        self.scale = 1.0
        self.min_scale = 0.4
        self.max_scale = 2.0

    def apply_zoom(self, zoom_in, center, vertices):
        factor = 1.1 if zoom_in else 0.9
        new_scale = self.scale * factor
        if not (self.min_scale <= new_scale <= self.max_scale):
            return

        cx, cy = center
        for v in vertices:
            dx = v.pos[0] - cx
            dy = v.pos[1] - cy
            v.pos[0] = int(cx + dx * factor)
            v.pos[1] = int(cy + dy * factor)

        self.scale = new_scale

def apply_highlights(elements, vertices, edges):
    for v in vertices:
        v.highlight = False
    for e in edges:
        e.highlight = False

    if not elements:
        return

    if all(isinstance(e, tuple) and len(e) == 2 for e in elements):  # edge list
        # Normalize element pairs to sorted names
        edge_set = set((min(str(a), str(b)), max(str(a), str(b))) for a, b in elements)

        for edge in edges:
            a, b = edge.start.name, edge.end.name
            edge_key = (min(a, b), max(a, b))
            if edge_key in edge_set:
                edge.highlight = True

    else:  # vertex list
        name_set = set(map(str, elements))  # Ensure string comparison
        for v in vertices:
            v.highlight = v.name in name_set

def apply_bipartite_highlight(np_problems, vertices, directed):
    for solver in np_problems:
        if solver.name == "k-COLORING":
            solver.update(k=2, directed=directed)
            found, groups = solver.result
            if found:
                apply_kcolor_highlight(solver, hovered=True, vertices=vertices)
            break

def also_highlight_edges(hovered_problem, members, edges):
    # 2) If this is a path/cycle problem, also highlight the path edges
    name = hovered_problem.name
    if name in ("HAMPATH", "HAMCYCLE", "LONGEST-PATH") and len(members) > 1:
        # walk consecutive pairs
        for i in range(len(members) - 1):
            u, v = members[i], members[i + 1]
            for edge in edges:
                if {edge.start.name, edge.end.name} == {u, v}:
                    edge.highlight = True

        # for HAMCYCLE, also close the loop back to the start
        if name == "HAMCYCLE":
            u, v = members[-1], members[0]
            for edge in edges:
                if {edge.start.name, edge.end.name} == {u, v}:
                    edge.highlight = True

def main():
    pygame.init()

    directed = False  # start with undirected mode

    screen = pygame.display.set_mode((800, 600), pygame.RESIZABLE)
    pygame.display.set_caption("Graph Theory Drawer")
    clock = pygame.time.Clock()
    zoom = ZoomManager()
    mouse_down_time = None
    mouse_down_pos = None
    panning = False
    last_mouse_pos = None

    vertices, edges = [], []
    vertex_names = iter(string.ascii_uppercase)
    selected_vertex = None
    moving_vertex = None
    dragging = False
    input_mode, input_target, input_text = None, None, ""
    click_times = []
    k_input_active = False
    k_value = 3
    duplicate_count = 1  # From 1 (x2) to 9 (x10)
    SLIDER_MIN = 1
    SLIDER_MAX = 9
    slider_dragging = False

    np_problems = get_all_problems(vertices, edges)
    diagnostics = GraphDiagnostics(vertices, edges)
    physics = PhysicsSystem(vertices, edges)
    drag_start_pos = None
    DRAG_THRESHOLD = 5  # Minimum pixels before treating as a drag

    def logic_all_buttons():
        return not hovered_vertex and not hovered_edge and not (
                SAVE_BUTTON_RECT.collidepoint(pos) or
                LOAD_BUTTON_RECT.collidepoint(pos) or
                K_INPUT_BOX_RECT.collidepoint(pos) or
                TOGGLE_DIRECTED_RECT.collidepoint(pos) or
                CLEAR_BUTTON_RECT.collidepoint(pos) or
                DUPLICATE_BUTTON_RECT.collidepoint(pos) or
                COMPLEMENT_BUTTON_RECT.collidepoint(pos))

    def draw_all_buttons():
        save_hovered = SAVE_BUTTON_RECT.collidepoint(pos)
        load_hovered = LOAD_BUTTON_RECT.collidepoint(pos)
        toggle_hovered = TOGGLE_DIRECTED_RECT.collidepoint(pos)
        clear_hovered = CLEAR_BUTTON_RECT.collidepoint(pos)
        complement_hovered = COMPLEMENT_BUTTON_RECT.collidepoint(pos)
        duplicate_hovered = DUPLICATE_BUTTON_RECT.collidepoint(pos)
        draw_slider(screen, duplicate_count, SLIDER_MIN, SLIDER_MAX)
        toggle_text = "Directed: ON" if directed else "Directed: OFF"
        draw_button(screen, TOGGLE_DIRECTED_RECT, toggle_text, toggle_hovered)
        draw_button(screen, SAVE_BUTTON_RECT, "Save", save_hovered)
        draw_button(screen, LOAD_BUTTON_RECT, "Load", load_hovered)
        draw_button(screen, CLEAR_BUTTON_RECT, "Clear", clear_hovered)
        draw_button(screen, DUPLICATE_BUTTON_RECT, "Duplicate", duplicate_hovered)
        draw_button(screen, COMPLEMENT_BUTTON_RECT, "Complement", complement_hovered)

    while True:
        screen.fill(BACKGROUND_COLOR)
        pos = pygame.mouse.get_pos()  # Needed outside event loop

        # fast lookup from (u,v) → Edge object
        edge_map = {
            (min(e.start.name, e.end.name), max(e.start.name, e.end.name)): e
            for e in edges
        }

        hovered_vertex = get_vertex_at_pos(vertices, pos)
        hovered_edge = get_edge_at_pos(edges, pos)
        for e in edges:
            e.highlight = (e == hovered_edge)



        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            elif event.type == pygame.VIDEORESIZE:
                screen = pygame.display.set_mode(event.size, pygame.RESIZABLE)


            elif event.type == pygame.KEYDOWN:
                if k_input_active:
                    if event.key == pygame.K_RETURN:
                        new_k = update_k_value_from_input(input_text)
                        if new_k is not None:
                            k_value = new_k
                            mark_all_problems_dirty(np_problems)
                            diagnostics.mark_dirty()

                        k_input_active = False
                        input_text = ""
                    elif event.key == pygame.K_BACKSPACE:
                        input_text = input_text[:-1]
                    elif event.key == pygame.K_ESCAPE:
                        k_input_active = False
                        input_text = ""
                    elif event.unicode.isdigit():
                        input_text += event.unicode
                elif input_mode:
                    if event.key == pygame.K_RETURN:
                        if input_mode == 'vertex' and input_text and all(v.name != input_text for v in vertices):
                            input_target.name = input_text
                        elif input_mode == 'edge':
                            input_target.value = input_text or None
                        input_mode = None
                        input_text = ""
                        mark_all_problems_dirty(np_problems)
                        diagnostics.mark_dirty()

                    elif event.key == pygame.K_BACKSPACE:
                        input_text = input_text[:-1]
                    elif event.key == pygame.K_ESCAPE:
                        input_mode = None
                        input_text = ""
                    else:
                        input_text += event.unicode

            elif event.type == pygame.MOUSEBUTTONDOWN and not input_mode:
                pos = event.pos
                if event.button == 4:  # Scroll up = zoom in
                    zoom.apply_zoom(zoom_in=True, center=pos, vertices=vertices)
                    continue
                elif event.button == 5:  # Scroll down = zoom out
                    zoom.apply_zoom(zoom_in=False, center=pos, vertices=vertices)
                    continue
                elif event.button == 1:  # Left mouse down
                    mouse_down_time = pygame.time.get_ticks()
                    mouse_down_pos = pos
                    if not hovered_vertex and not hovered_edge and not DUPLICATE_SLIDER_RECT.collidepoint(pos):
                        panning = True
                        last_mouse_pos = pos


                elif event.button == 2 and hovered_vertex:
                    moving_vertex = hovered_vertex
                    drag_start_pos = pos
                    dragging = False
                    scroll_drag_strength = 0.25  # Much stronger nudge
                    continue

                if SAVE_BUTTON_RECT.collidepoint(pos):
                    save_graph(vertices, edges, directed)
                    continue
                elif LOAD_BUTTON_RECT.collidepoint(pos):
                    vertex_names, loaded_directed = load_graph("graph.json", vertices, edges)
                    directed = loaded_directed  # Update current mode
                    mark_all_problems_dirty(np_problems)
                    diagnostics.mark_dirty()
                    continue

                elif DUPLICATE_BUTTON_RECT.collidepoint(pos):
                    if duplicate_graph(vertices, edges, times=duplicate_count):
                        mark_all_problems_dirty(np_problems)
                        diagnostics.mark_dirty()
                    continue

                elif COMPLEMENT_BUTTON_RECT.collidepoint(pos):
                    apply_graph_complement(vertices, edges, directed)
                    mark_all_problems_dirty(np_problems)
                    diagnostics.mark_dirty()
                    continue

                elif DUPLICATE_SLIDER_RECT.collidepoint(pos):
                    slider_dragging = True

                elif K_INPUT_BOX_RECT.collidepoint(pos):
                    k_input_active = True
                    input_text = str(k_value)
                    continue
                elif CLEAR_BUTTON_RECT.collidepoint(pos):
                    vertices.clear()
                    edges.clear()
                    selected_vertex = None
                    vertex_names = iter(string.ascii_uppercase)
                    mark_all_problems_dirty(np_problems)
                    diagnostics.mark_dirty()

                    continue
                elif TOGGLE_DIRECTED_RECT.collidepoint(pos):
                    directed = not directed
                    if directed:
                        # Convert undirected to directed (random directions)
                        import random
                        new_edges = []
                        for e in edges:
                            if not any(e2.start == e.end and e2.end == e.start for e2 in edges):
                                if random.choice([True, False]):
                                    new_edges.append(e)
                                else:
                                    new_edges.append(Edge(e.end, e.start, e.value))
                            else:
                                new_edges.append(e)  # already bidirectional
                        edges[:] = new_edges
                    else:
                        # Remove reverse-direction duplicates
                        seen = set()
                        new_edges = []
                        for e in edges:
                            key = tuple(sorted([e.start.name, e.end.name]))
                            if key not in seen:
                                new_edges.append(e)
                                seen.add(key)
                        edges[:] = new_edges

                    mark_all_problems_dirty(np_problems)
                    diagnostics.mark_dirty()

                    continue

                clicked_vertex = hovered_vertex
                clicked_edge = hovered_edge

                def is_double_click():
                    if event.button != 1:  # Only count left clicks
                        return False
                    now = pygame.time.get_ticks()
                    click_times.append(now)
                    if len(click_times) > 2:
                        click_times.pop(0)
                    return len(click_times) == 2 and (click_times[1] - click_times[0]) < DOUBLE_CLICK_TIME

                if event.button == 3:
                    # Right click = delete
                    if clicked_vertex:
                        edges[:] = [e for e in edges if e.start != clicked_vertex and e.end != clicked_vertex]
                        vertices.remove(clicked_vertex)
                        selected_vertex = None
                    elif clicked_edge:
                        edges.remove(clicked_edge)
                    mark_all_problems_dirty(np_problems)
                    diagnostics.mark_dirty()
                    continue

                if is_double_click():
                    if clicked_vertex:
                        input_mode = 'vertex'
                        input_target = clicked_vertex
                        input_text = clicked_vertex.name
                    elif clicked_edge:
                        input_mode = 'edge'
                        input_target = clicked_edge
                        input_text = clicked_edge.value or ""
                    continue

                if clicked_vertex:
                    if selected_vertex == clicked_vertex:
                        # Clicking again unselects
                        selected_vertex = None
                        moving_vertex = None
                        dragging = False
                    elif selected_vertex:
                        # Add edge if not duplicate
                        already_exists = any(e.start == selected_vertex and e.end == clicked_vertex for e in edges)
                        if not already_exists:
                            edges.append(Edge(selected_vertex, clicked_vertex))
                        selected_vertex = None
                        mark_all_problems_dirty(np_problems)
                        diagnostics.mark_dirty()

                    else:
                        selected_vertex = clicked_vertex
                        moving_vertex = clicked_vertex
                        drag_start_pos = pos
                        dragging = False

            elif event.type == pygame.MOUSEBUTTONUP:
                slider_dragging = False
                dragging = False
                moving_vertex = None

                if event.button == 1:
                    panning = False
                    last_mouse_pos = None
                    if mouse_down_time:
                        held = pygame.time.get_ticks() - mouse_down_time
                        dist = math.hypot(pos[0] - mouse_down_pos[0], pos[1] - mouse_down_pos[1])

                        if held <= 200 and dist <= 5:
                            if logic_all_buttons():
                                if len(vertices) >= VERTEX_LIMIT:
                                    print(f"[INFO] Vertex limit reached ({VERTEX_LIMIT}). Cannot add more.")
                                else:
                                    name = get_next_available_vertex_name(vertices, vertex_names)
                                    if name:
                                        new_vertex = Vertex(pos, name)
                                        vertices.append(new_vertex)

                                        if selected_vertex:
                                            edges.append(Edge(selected_vertex, new_vertex))
                                            selected_vertex = None  # optionally clear selection

                                        mark_all_problems_dirty(np_problems)
                                        diagnostics.mark_dirty()




            elif event.type == pygame.MOUSEMOTION:
                if slider_dragging:
                    rel_x = min(max(pos[0] - DUPLICATE_SLIDER_RECT.x, 0), DUPLICATE_SLIDER_RECT.width)
                    ratio = rel_x / DUPLICATE_SLIDER_RECT.width
                    duplicate_count = int(SLIDER_MIN + (SLIDER_MAX - SLIDER_MIN) * ratio)

                if moving_vertex:
                    dx = pos[0] - drag_start_pos[0]
                    dy = pos[1] - drag_start_pos[1]
                    if not dragging and (dx * dx + dy * dy) > DRAG_THRESHOLD * DRAG_THRESHOLD:
                        dragging = True  # Now start dragging
                    if dragging:
                        old_pos = moving_vertex.pos[:]
                        moving_vertex.pos = list(pos)
                        physics.velocities[moving_vertex] = [0.0, 0.0]  # Freeze physics interference
                        is_middle = pygame.mouse.get_pressed()[1]  # True if scroll button held
                        strength = scroll_drag_strength if is_middle else 0.02
                        if is_middle:
                            physics.move_component(moving_vertex, moving_vertex.pos, old_pos)
                        else:
                            physics.nudge_neighbors(moving_vertex, moving_vertex.pos, old_pos, strength=strength)

                else:
                    if panning and last_mouse_pos:
                        dx = pos[0] - last_mouse_pos[0]
                        dy = pos[1] - last_mouse_pos[1]
                        for v in vertices:
                            v.pos[0] += dx
                            v.pos[1] += dy
                        last_mouse_pos = pos
        for v in vertices:
            v.highlight = False
        # for e in edges:
        #     e.highlight = False

        hovered_problem = None
        y = 60
        for solver in np_problems:
            y, hovered, members = solver.render_debug(screen, DEBUG_FONT, k_value, y, pos, directed)

            if solver.name == "k-COLORING":
                apply_kcolor_highlight(solver, hovered, vertices)

            if hovered:
                hovered_problem = solver

        if hovered_problem:
            found, members = hovered_problem.result
            if found:
                apply_highlights(members, vertices, edges)
                # old nested loops here…
                for i in range(len(members) - 1):
                    u, v = members[i], members[i + 1]
                    for edge in edges:
                        if {edge.start.name, edge.end.name} == {u, v}:
                            edge.highlight = True

                if hovered_problem.name == "HAMCYCLE":
                    u, v = members[-1], members[0]
                    for edge in edges:
                        if {edge.start.name, edge.end.name} == {u, v}:
                            edge.highlight = True

        if not input_mode:
            diagnostics.update(directed=directed)
            diagnostics.render(screen, DEBUG_FONT, pos)
            if diagnostics.hovered_diagnostic:
                key, elements = diagnostics.hovered_diagnostic
                apply_highlights(elements, vertices, edges)
                if key == "Bipartite" and diagnostics.info.get("Bipartite") is True:
                    apply_bipartite_highlight(np_problems, vertices, directed)

        for edge in edges:
            is_opposite = any(e.start == edge.end and e.end == edge.start for e in edges if e != edge)
            offset = math.pi / 18 if is_opposite and directed else 0
            edge.draw(screen, directed=directed, offset_angle=offset)

        for vertex in vertices:
            vertex.draw(screen, selected=(vertex == selected_vertex), hovered=(vertex == hovered_vertex))
        draw_all_buttons()

        pygame.draw.rect(screen, (100, 100, 100), K_INPUT_BOX_RECT, border_radius=6)
        k_label = FONT.render(f"k={input_text if k_input_active else k_value}", True, BUTTON_TEXT_COLOR)
        label_rect = k_label.get_rect(center=K_INPUT_BOX_RECT.center)
        screen.blit(k_label, label_rect)

        if input_mode:
            EDIT_RECT_DYNAMIC = pygame.Rect(
                10,
                screen.get_height() - 50,
                max(screen.get_width() - 500, 300),
                40
            )
            pygame.draw.rect(screen, INPUT_BOX_COLOR, EDIT_RECT_DYNAMIC, border_radius=6)
            label = "Editing Vertex Name:" if input_mode == 'vertex' else "Editing Edge Value:"
            prompt = INPUT_FONT.render(f"{label} {input_text}", True, INPUT_TEXT_COLOR)
            screen.blit(prompt, (20, EDIT_RECT_DYNAMIC.top + 15))

        draw_fps(screen, clock)

        physics.update()


        pygame.display.flip()
        clock.tick(60)

if __name__ == '__main__':
    main()
