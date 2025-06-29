import math
import sys
import string
import json

from algorithms import get_all_algorithms, mark_all_algorithms_dirty
from diagnostics import GraphDiagnostics
from config import *
from graph import Vertex, Edge, get_vertex_at_pos, get_edge_at_pos, duplicate_graph, apply_graph_complement
from math_text import clear_math_surface_cache
from physics import PhysicsSystem
from np_problems import get_all_problems, mark_all_problems_dirty
from utils import generate_color_for_index, update_k_value_from_input, get_next_available_vertex_name, draw_fps, \
    deduplicate_edges_for_undirected, generate_random_graph
from zoom_manager import ZoomManager

def save_graph(vertices, edges, directed=False, show_weights=False, filename="graph.json"):
    with open(filename, "w") as f:
        json.dump({
            "directed": directed,
            "show_weights": show_weights,
            "vertices": [{"name": v.name, "pos": v.pos} for v in vertices],
            "edges": [{"start": e.start.name, "end": e.end.name, "value": e.value} for e in edges]
        }, f)

def load_graph(filename, vertices, edges):
    try:
        with open(filename, "r") as f:
            data = json.load(f)

        if "vertices" not in data or "edges" not in data:
            raise ValueError("Invalid file format")

        directed = data.get("directed", False)
        show_weights = data.get("show_weights", False)

        name_map = {
            v["name"]: Vertex(v["pos"], v["name"])
            for v in data["vertices"]
        }

        vertices.clear()
        vertices.extend(name_map.values())
        edges.clear()
        edges.extend(
            Edge(name_map[e["start"]], name_map[e["end"]], str(e.get("value")) if e.get("value") is not None else None)
            for e in data["edges"]
        )

        return iter(name for name in string.ascii_uppercase if name not in name_map), directed, show_weights

    except Exception as e:
        print(f"[ERROR] Failed to load graph from '{filename}': {e}")
        return iter(string.ascii_uppercase), False, False

def draw_button(screen, rect, text, hovered, override_color=None):
    color = override_color if override_color else (BUTTON_HOVER_COLOR if hovered else BUTTON_COLOR)
    pygame.draw.rect(screen, color, rect, border_radius=8)
    label = FONT.render(text, True, BUTTON_TEXT_COLOR)
    screen.blit(label, label.get_rect(center=rect.center))


def is_over_slider_knob(mouse_pos, duplicate_count, SLIDER_MIN, SLIDER_MAX):
    slider_x = DUPLICATE_SLIDER_RECT.x
    slider_y = DUPLICATE_SLIDER_RECT.y
    slider_w = DUPLICATE_SLIDER_RECT.width
    slider_h = DUPLICATE_SLIDER_RECT.height
    fill_ratio = (duplicate_count - SLIDER_MIN) / (SLIDER_MAX - SLIDER_MIN)
    knob_x = slider_x + int(fill_ratio * slider_w)
    knob_y = slider_y + slider_h // 2
    knob_radius = slider_h // 2 + 4
    knob_rect = pygame.Rect(knob_x - knob_radius, knob_y - knob_radius, knob_radius * 2, knob_radius * 2)
    return knob_rect.collidepoint(mouse_pos)


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

def highlight_edges(hovered_problem, members, edges):
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

def highlight_edges_for_algorithms(members, edges, directed=False):
    members = [item for item in members if isinstance(item, tuple)]
    for u, v in members:
        for edge in edges:
            if directed:
                if edge.start.name == u and edge.end.name == v:
                    edge.highlight = True
            else:
                if {edge.start.name, edge.end.name} == {u, v}:
                    edge.highlight = True


def reset_all(vertices, edges, algorithms, np_problems, diagnostics, physics):
    # Clear vertex and edge containers
    vertices.clear()
    edges.clear()
    clear_math_surface_cache()
    # Reset simulation and analysis systems
    physics.reset()
    diagnostics.reset()

    # Reset all NP problems
    for problem in np_problems:
        problem.reset()
    for algorithm in algorithms:
        algorithm.source = None
        algorithm.target = None
        algorithm.reset()
    return None, None, None

def handle_all_buttons(pos, vertices, edges, np_problems, algorithms, diagnostics, directed_state, duplicate_count, physics, show_weights, include_algorithms, source_vertex, target_vertex, k_value, directed):
    """
    Handles clicks on top-row buttons.
    Returns: (handled: bool, new_directed: bool)
    """
    if INCLUDE_ALGO_BUTTON_RECT.collidepoint(pos):
        include_algorithms = not include_algorithms
        if include_algorithms:
            # Recompute everything now
            for alg in algorithms:
                alg.reset()
                alg.update(source_vertex.name if source_vertex else None,
                           target_vertex.name if target_vertex else None,
                           directed=directed,
                           compute_enabled=True)

            for problem in np_problems:
                problem.reset()
                problem.update(k_value, directed=directed, compute_enabled=True)

            diagnostics.reset()
            diagnostics.update(directed=directed, compute_enabled=True)

        else:
            # Clear all states if turning off
            for alg in algorithms:
                alg.reset()
            for problem in np_problems:
                problem.reset()
            diagnostics.reset()
        return True, directed_state, show_weights, include_algorithms

    if SAVE_BUTTON_RECT.collidepoint(pos):
        save_graph(vertices, edges, directed_state, show_weights=show_weights)
        return True, directed_state, show_weights, include_algorithms

    elif DUPLICATE_BUTTON_RECT.collidepoint(pos):
        if duplicate_graph(vertices, edges, times=duplicate_count):
            mark_all_problems_dirty(np_problems)
            mark_all_algorithms_dirty(algorithms)
            diagnostics.mark_dirty()
        return True, directed_state, show_weights, include_algorithms

    elif COMPLEMENT_BUTTON_RECT.collidepoint(pos):
        apply_graph_complement(vertices, edges, directed_state)
        mark_all_problems_dirty(np_problems)
        mark_all_algorithms_dirty(algorithms)
        diagnostics.mark_dirty()
        return True, directed_state, show_weights, include_algorithms

    elif SELECT_ST_BUTTON_RECT.collidepoint(pos):
        return True, directed_state, True, include_algorithms

    elif CLEAR_BUTTON_RECT.collidepoint(pos):
        return "reset", directed_state, show_weights, include_algorithms
    return False, directed_state, show_weights, include_algorithms

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

    include_algorithms = True
    np_problems = get_all_problems(vertices, edges)
    algorithms = get_all_algorithms(vertices, edges)
    for alg in algorithms:
        if not alg.requires_source_target:
            alg.update(None, None, directed=False, compute_enabled=include_algorithms)

    diagnostics = GraphDiagnostics(vertices, edges)
    physics = PhysicsSystem(vertices, edges)
    drag_start_pos = None
    DRAG_THRESHOLD = 5  # Minimum pixels before treating as a drag
    source_vertex = None
    target_vertex = None
    selecting_st_mode = False
    show_weights = False

    def logic_all_buttons():
        return not hovered_vertex and not hovered_edge and not (
                SAVE_BUTTON_RECT.collidepoint(pos) or
                LOAD_BUTTON_RECT.collidepoint(pos) or
                K_INPUT_BOX_RECT.collidepoint(pos) or
                TOGGLE_DIRECTED_RECT.collidepoint(pos) or
                CLEAR_BUTTON_RECT.collidepoint(pos) or
                DUPLICATE_BUTTON_RECT.collidepoint(pos) or
                COMPLEMENT_BUTTON_RECT.collidepoint(pos) or
                SELECT_ST_BUTTON_RECT.collidepoint(pos) or
                INCLUDE_ALGO_BUTTON_RECT.collidepoint(pos))

    def draw_edges_and_vertices():
        for edge in edges:
            is_opposite = any(e.start == edge.end and e.end == edge.start for e in edges if e != edge)
            offset = math.pi / 18 if is_opposite and directed else 0
            edge.draw(screen, directed=directed, offset_angle=offset, show_weight=show_weights)

        for vertex in vertices:
            is_st = vertex == source_vertex or vertex == target_vertex
            vertex.draw(screen,
                        selected=(vertex == selected_vertex),
                        hovered=(vertex == hovered_vertex),
                        st_highlight=is_st)

    def draw_all_buttons():
        save_hovered = SAVE_BUTTON_RECT.collidepoint(pos)
        load_hovered = LOAD_BUTTON_RECT.collidepoint(pos)
        toggle_hovered = TOGGLE_DIRECTED_RECT.collidepoint(pos)
        clear_hovered = CLEAR_BUTTON_RECT.collidepoint(pos)
        complement_hovered = COMPLEMENT_BUTTON_RECT.collidepoint(pos)
        duplicate_hovered = DUPLICATE_BUTTON_RECT.collidepoint(pos)
        random_hovered = RANDOM_BUTTON_RECT.collidepoint(pos)

        draw_slider(screen, duplicate_count, SLIDER_MIN, SLIDER_MAX)
        toggle_text = "Directed: ON" if directed else "Directed: OFF"
        draw_button(screen, TOGGLE_DIRECTED_RECT, toggle_text, toggle_hovered)
        draw_button(screen, SAVE_BUTTON_RECT, "Save", save_hovered)
        draw_button(screen, LOAD_BUTTON_RECT, "Load", load_hovered)
        draw_button(screen, CLEAR_BUTTON_RECT, "Clear", clear_hovered)
        draw_button(screen, DUPLICATE_BUTTON_RECT, "Duplicate", duplicate_hovered)
        draw_button(screen, COMPLEMENT_BUTTON_RECT, "Complement", complement_hovered)
        draw_button(screen, RANDOM_BUTTON_RECT, "Random", random_hovered)

        include_algo_hovered = INCLUDE_ALGO_BUTTON_RECT.collidepoint(pos)
        algo_text = f"Include Algorithms: {'ON' if include_algorithms else 'OFF'}"
        draw_button(screen, INCLUDE_ALGO_BUTTON_RECT, algo_text, include_algo_hovered)

        st_hovered = SELECT_ST_BUTTON_RECT.collidepoint(pos)
        st_text = "Select S/T" if not (
                    source_vertex and target_vertex) else f"S/T: {source_vertex.name},{target_vertex.name}"
        st_override = (90, 90, 90) if selecting_st_mode else None
        draw_button(screen, SELECT_ST_BUTTON_RECT, st_text, st_hovered, override_color=st_override)


    while True:
        screen.fill(BACKGROUND_COLOR)
        pos = pygame.mouse.get_pos()  # Needed outside event loop

        # fast lookup from (u,v) → Edge object
        edge_map = {
            (min(e.start.name, e.end.name), max(e.start.name, e.end.name)): e
            for e in edges
        }

        hovered_vertex = get_vertex_at_pos(vertices, pos)
        if not hovered_vertex:
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
                            mark_all_algorithms_dirty(algorithms)
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
                            try:
                                input_target.value = str(int(input_text)) if input_text else None
                            except ValueError:
                                input_target.value = None
                        input_mode = None
                        input_text = ""
                        mark_all_problems_dirty(np_problems)
                        mark_all_algorithms_dirty(algorithms)
                        diagnostics.mark_dirty()

                    elif event.key == pygame.K_BACKSPACE:
                        input_text = input_text[:-1]
                    elif event.key == pygame.K_ESCAPE:
                        input_mode = None
                        input_text = ""
                    elif input_mode == "edge" and (event.unicode.isdigit() or (event.unicode == '-' and input_text == '')):
                        input_text += event.unicode
                    elif input_mode == "vertex":
                        input_text += event.unicode


            elif event.type == pygame.MOUSEBUTTONDOWN and not input_mode:
                pos = event.pos
                if is_over_slider_knob(pos, duplicate_count, SLIDER_MIN, SLIDER_MAX):
                    slider_dragging = True
                    continue
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

                    if selecting_st_mode and hovered_vertex:
                        if not source_vertex:
                            source_vertex = hovered_vertex
                        elif hovered_vertex != source_vertex:
                            target_vertex = hovered_vertex
                            selecting_st_mode = False
                            for alg in algorithms:
                                alg.reset()
                                alg.source = source_vertex.name
                                alg.target = target_vertex.name
                            continue
                        break


                elif event.button == 2 and hovered_vertex:
                    moving_vertex = hovered_vertex
                    drag_start_pos = pos
                    dragging = False
                    scroll_drag_strength = 0.25  # Much stronger nudge
                    continue

                handled, directed, show_weights, include_algorithms = handle_all_buttons(pos, vertices, edges, np_problems, algorithms, diagnostics, directed,
                                                       duplicate_count, physics, show_weights=show_weights, include_algorithms=include_algorithms,
                                                                                         source_vertex=source_vertex, target_vertex=target_vertex, k_value=k_value, directed=directed)
                if SELECT_ST_BUTTON_RECT.collidepoint(pos):
                    selecting_st_mode = True
                    source_vertex = None
                    target_vertex = None
                    continue

                if K_INPUT_BOX_RECT.collidepoint(pos):
                    k_input_active = True
                    input_text = ""
                    continue

                elif TOGGLE_DIRECTED_RECT.collidepoint(pos):
                    directed = not directed
                    if not directed:
                        deduplicate_edges_for_undirected(edges)
                    mark_all_problems_dirty(np_problems)
                    mark_all_algorithms_dirty(algorithms)
                    diagnostics.mark_dirty()
                    continue

                elif RANDOM_BUTTON_RECT.collidepoint(pos):
                    vertex_names = iter(string.ascii_uppercase)
                    selected_vertex, source_vertex, target_vertex = reset_all(vertices, edges, algorithms, np_problems,
                                                                              diagnostics, physics)
                    source_vertex, target_vertex = None, None
                    selecting_st_mode = False  # optional if you want to cancel selection mode
                    generate_random_graph(vertices, edges, vertex_names)
                    mark_all_problems_dirty(np_problems)
                    mark_all_algorithms_dirty(algorithms)
                    diagnostics.mark_dirty()
                    continue

                elif LOAD_BUTTON_RECT.collidepoint(pos):
                    selected_vertex, source_vertex, target_vertex = reset_all(vertices, edges, algorithms, np_problems,
                                                                              diagnostics, physics)
                    source_vertex, target_vertex = None, None
                    selecting_st_mode = False

                    vertex_names, directed, show_weights = load_graph("graph.json", vertices, edges)
                    mark_all_problems_dirty(np_problems)
                    mark_all_algorithms_dirty(algorithms)
                    diagnostics.mark_dirty()
                    continue

                if handled == "reset":
                    selected_vertex, source_vertex, target_vertex = reset_all(vertices, edges, algorithms, np_problems,
                                                                              diagnostics, physics)
                    source_vertex, target_vertex = None, None
                    selecting_st_mode = False  # optional if you want to cancel selection mode
                    continue

                elif handled:
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
                        if selected_vertex == source_vertex or selected_vertex == target_vertex:
                            source_vertex = None
                            target_vertex = None
                        selected_vertex = None
                    elif clicked_edge:
                        edges.remove(clicked_edge)
                    mark_all_problems_dirty(np_problems)
                    mark_all_algorithms_dirty(algorithms)
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
                        input_text = clicked_edge.value or "1"
                        show_weights = True
                    continue

                if clicked_vertex:
                    if selected_vertex == clicked_vertex:
                        # Clicking again unselects
                        selected_vertex = None
                        moving_vertex = None
                        dragging = False

                    elif selected_vertex:
                        if directed:
                            already_exists = any(
                                e.start == selected_vertex and e.end == clicked_vertex
                                for e in edges
                            )
                        else:
                            already_exists = any(
                                {e.start, e.end} == {selected_vertex, clicked_vertex}
                                for e in edges
                            )

                        if not already_exists:
                            if len(edges) >= EDGE_LIMIT:
                                print("[INFO] Cannot add edge: edge limit reached.")
                            else:
                                edges.append(Edge(selected_vertex, clicked_vertex, value="1"))
                                mark_all_problems_dirty(np_problems)
                                mark_all_algorithms_dirty(algorithms)
                                diagnostics.mark_dirty()
                            selected_vertex = None
                        else:
                            # Edge exists → treat this like a selection change
                            selected_vertex = clicked_vertex
                            moving_vertex = clicked_vertex
                            drag_start_pos = pos
                            dragging = False
                            # Don't mark dirty or add edge
                            continue

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

                        if held <= 100 and dist <= 5:
                            if logic_all_buttons():
                                if len(vertices) >= VERTEX_LIMIT:
                                    print(f"[INFO] Vertex limit reached ({VERTEX_LIMIT}). Cannot add more.")
                                else:
                                    name = get_next_available_vertex_name(vertices, vertex_names)
                                    if name:
                                        new_vertex = Vertex(pos, name)
                                        vertices.append(new_vertex)

                                        if selected_vertex:
                                            edges.append(Edge(selected_vertex, new_vertex, value="1"))
                                            selected_vertex = None  # optionally clear selection

                                        mark_all_problems_dirty(np_problems)
                                        mark_all_algorithms_dirty(algorithms)
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

        if include_algorithms:
            if not input_mode:
                hovered_problem = None
                y = 67
                for solver in np_problems:
                    y, hovered, members = solver.render_debug(screen, DEBUG_FONT, k_value, y, pos, directed, compute_enabled=include_algorithms)

                    if solver.name == "k-COLORING":
                        apply_kcolor_highlight(solver, hovered, vertices)

                    if hovered:
                        hovered_problem = solver

                if hovered_problem:
                    found, members = hovered_problem.result
                    if found:
                        apply_highlights(members, vertices, edges)
                        highlight_edges(hovered_problem, members, edges)

                hovered_algorithm = None
                y_start = screen.get_height() - len(algorithms) * 20 - 15
                y = y_start
                for alg in algorithms:
                    y, hovered, elements = alg.render_debug(screen, DEBUG_FONT, y, pos, directed)
                    if hovered:
                        hovered_algorithm = (alg, elements)

                if hovered_algorithm:
                    _, elements = hovered_algorithm
                    if hovered_algorithm[0].name in ["PRIM", "KRUSKAL"]:
                        elements = _.edge_result
                    apply_highlights(elements, vertices, edges)
                    highlight_edges_for_algorithms(elements, edges)

                if not input_mode:
                    diagnostics.update(directed=directed, compute_enabled=include_algorithms)
                    diagnostics.render(screen, DEBUG_FONT, pos)
                    if diagnostics.hovered_diagnostic:
                        key, elements = diagnostics.hovered_diagnostic
                        apply_highlights(elements, vertices, edges)
                        if key == "Bipartite" and diagnostics.info.get("Bipartite") is True:
                            apply_bipartite_highlight(np_problems, vertices, directed)

        draw_edges_and_vertices()
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
