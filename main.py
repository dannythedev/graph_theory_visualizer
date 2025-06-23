import sys
import string
import json

from config import *
from graph import Vertex, Edge, get_vertex_at_pos, get_edge_at_pos, edge_exists, rebuild_edge_lookup
from physics import PhysicsSystem
from np_problems import get_all_problems, mark_all_problems_dirty

def save_graph(vertices, edges, filename="graph.json"):
    with open(filename, "w") as f:
        json.dump({
            "vertices": [{"name": v.name, "pos": v.pos} for v in vertices],
            "edges": [{"start": e.start.name, "end": e.end.name, "value": e.value} for e in edges]
        }, f)

def load_graph(filename, vertices, edges):
    with open(filename, "r") as f:
        data = json.load(f)
    name_map = {v["name"]: Vertex(v["pos"], v["name"]) for v in data["vertices"]}
    vertices.clear()
    vertices.extend(name_map.values())
    edges.clear()
    edges.extend(Edge(name_map[e["start"]], name_map[e["end"]], e.get("value")) for e in data["edges"])
    return iter(name for name in string.ascii_uppercase if name not in name_map)

def draw_button(screen, rect, text, hovered):
    pygame.draw.rect(screen, BUTTON_HOVER_COLOR if hovered else BUTTON_COLOR, rect, border_radius=8)
    label = FONT.render(text, True, BUTTON_TEXT_COLOR)
    screen.blit(label, label.get_rect(center=rect.center))

def update_k_value_from_input(input_text):
    try:
        return max(1, int(input_text))
    except ValueError:
        return None

def main():
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Graph Theory Drawer")
    clock = pygame.time.Clock()

    vertices, edges = [], []
    vertex_names = iter(string.ascii_uppercase)
    edge_lookup = set()
    selected_vertex = None
    moving_vertex = None
    dragging = False
    input_mode, input_target, input_text = None, None, ""
    click_times = []
    k_input_active = False
    k_value = 5
    hovered_problem = None
    np_problems = get_all_problems(vertices, edges)
    physics = PhysicsSystem(vertices, edges)

    while True:
        screen.fill(BACKGROUND_COLOR)
        pos = pygame.mouse.get_pos()
        hovered_vertex = get_vertex_at_pos(vertices, pos)
        hovered_edge = get_edge_at_pos(edges, pos)
        for e in edges:
            e.highlight = (e == hovered_edge)

        save_hovered = SAVE_BUTTON_RECT.collidepoint(pos)
        load_hovered = LOAD_BUTTON_RECT.collidepoint(pos)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            elif event.type == pygame.KEYDOWN:
                if k_input_active:
                    if event.key == pygame.K_RETURN:
                        new_k = update_k_value_from_input(input_text)
                        if new_k is not None:
                            k_value = new_k
                            mark_all_problems_dirty(np_problems)
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
                    elif event.key == pygame.K_BACKSPACE:
                        input_text = input_text[:-1]
                    elif event.key == pygame.K_ESCAPE:
                        input_mode = None
                        input_text = ""
                    else:
                        input_text += event.unicode

            elif event.type == pygame.MOUSEBUTTONDOWN and not input_mode:
                if SAVE_BUTTON_RECT.collidepoint(pos):
                    save_graph(vertices, edges)
                    continue
                elif LOAD_BUTTON_RECT.collidepoint(pos):
                    vertex_names = load_graph("graph.json", vertices, edges)
                    edge_lookup = rebuild_edge_lookup(edges)
                    mark_all_problems_dirty(np_problems)
                    continue
                elif K_INPUT_BOX_RECT.collidepoint(pos):
                    k_input_active = True
                    input_text = str(k_value)
                    continue

                clicked_vertex = hovered_vertex
                clicked_edge = hovered_edge

                def is_double_click():
                    now = pygame.time.get_ticks()
                    click_times.append(now)
                    if len(click_times) > 2:
                        click_times.pop(0)
                    return len(click_times) == 2 and (click_times[1] - click_times[0]) < DOUBLE_CLICK_TIME

                if event.button == 3:
                    if clicked_vertex:
                        input_mode = 'vertex'
                        input_target = clicked_vertex
                        input_text = clicked_vertex.name
                    elif clicked_edge:
                        input_mode = 'edge'
                        input_target = clicked_edge
                        input_text = clicked_edge.value or ""
                    continue

                if is_double_click():
                    if clicked_vertex:
                        edges[:] = [e for e in edges if e.start != clicked_vertex and e.end != clicked_vertex]
                        vertices.remove(clicked_vertex)
                        edge_lookup = rebuild_edge_lookup(edges)
                        selected_vertex = None
                    elif clicked_edge:
                        edges.remove(clicked_edge)
                        edge_lookup = rebuild_edge_lookup(edges)
                    mark_all_problems_dirty(np_problems)
                    continue

                if clicked_vertex:
                    if selected_vertex and selected_vertex != clicked_vertex and not edge_exists(selected_vertex, clicked_vertex, edge_lookup):
                        edges.append(Edge(selected_vertex, clicked_vertex))
                        edge_lookup = rebuild_edge_lookup(edges)
                        selected_vertex = None
                    else:
                        selected_vertex = clicked_vertex
                        moving_vertex = clicked_vertex
                        dragging = True
                    mark_all_problems_dirty(np_problems)
                elif not clicked_edge:
                    try:
                        name = next(vertex_names)
                        vertices.append(Vertex(pos, name))
                        mark_all_problems_dirty(np_problems)
                    except StopIteration:
                        print("No more vertex names available.")

            elif event.type == pygame.MOUSEBUTTONUP:
                dragging = False
                moving_vertex = None

            elif event.type == pygame.MOUSEMOTION and dragging and moving_vertex:
                old_pos = moving_vertex.pos[:]
                moving_vertex.pos = list(pos)
                physics.nudge_neighbors(moving_vertex, moving_vertex.pos, old_pos)

        hovered_problem = None
        y = 60
        for solver in np_problems:
            y, hovered, members = solver.render_debug(screen, DEBUG_FONT, k_value, y, pos)
            if hovered:
                hovered_problem = solver

        for v in vertices:
            v.highlight = False
        if hovered_problem:
            found, members = hovered_problem.result
            member_set = set(members)
            for v in vertices:
                v.highlight = v.name in member_set

        for edge in edges:
            edge.draw(screen)
        for vertex in vertices:
            vertex.draw(screen, selected=(vertex == selected_vertex), hovered=(vertex == hovered_vertex))

        draw_button(screen, SAVE_BUTTON_RECT, "Save", save_hovered)
        draw_button(screen, LOAD_BUTTON_RECT, "Load", load_hovered)

        pygame.draw.rect(screen, (100, 100, 100), K_INPUT_BOX_RECT, border_radius=6)
        k_label = FONT.render(f"k: {input_text if k_input_active else k_value}", True, BUTTON_TEXT_COLOR)
        screen.blit(k_label, (K_INPUT_BOX_RECT.x + 8, K_INPUT_BOX_RECT.y + 8))

        if input_mode:
            pygame.draw.rect(screen, INPUT_BOX_COLOR, (10, 550, 780, 40), border_radius=6)
            label = "Editing Vertex Name:" if input_mode == 'vertex' else "Editing Edge Value:"
            prompt = INPUT_FONT.render(f"{label} {input_text}", True, INPUT_TEXT_COLOR)
            screen.blit(prompt, (20, 558))

        physics.update()

        pygame.display.flip()
        clock.tick(60)

if __name__ == '__main__':
    main()
