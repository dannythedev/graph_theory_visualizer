import pygame
import sys
import string
import json
import itertools

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Graph Theory Drawer")

# Fonts and clock
font = pygame.font.SysFont("poppins", 18)
input_font = pygame.font.SysFont("poppins", 22, bold=True)
debug_font = pygame.font.SysFont("consolas", 16)
clock = pygame.time.Clock()

# Constants
VERTEX_RADIUS = 20
EDGE_CLICK_RADIUS = 15
VERTEX_OUTLINE_WIDTH = 4
BACKGROUND_COLOR = (30, 30, 30)
VERTEX_COLOR = (100, 149, 237)
VERTEX_HOVER_COLOR = (70, 130, 180)
EDGE_COLOR = (170, 170, 170)
EDGE_HOVER_COLOR = (225, 225, 225)
SELECTED_COLOR = (255, 99, 71)
BUTTON_COLOR = (50, 50, 50)
BUTTON_HOVER_COLOR = (70, 70, 70)
BUTTON_TEXT_COLOR = (255, 255, 255)
INPUT_BOX_COLOR = (40, 40, 40)
INPUT_TEXT_COLOR = (255, 255, 255)
VERTEX_OUTLINE_COLOR = (255, 255, 255)
DOUBLE_CLICK_TIME = 400

# UI State
vertices = []
edges = []
vertex_names = iter(string.ascii_uppercase)
selected_vertex = None
moving_vertex = None
click_times = []
input_mode = None
input_target = None
input_text = ""
k_value = 5
k_input_active = False

save_button = pygame.Rect(10, 10, 100, 36)
load_button = pygame.Rect(120, 10, 100, 36)
k_input_box = pygame.Rect(230, 10, 60, 36)

# Edge lookup cache
edge_lookup = set()

def rebuild_edge_lookup():
    global edge_lookup
    edge_lookup = set((min(e.start.name, e.end.name), max(e.start.name, e.end.name)) for e in edges)

def edge_exists(v1, v2):
    return (min(v1.name, v2.name), max(v1.name, v2.name)) in edge_lookup

def is_double_click():
    now = pygame.time.get_ticks()
    click_times.append(now)
    if len(click_times) > 2:
        click_times.pop(0)
    return len(click_times) == 2 and (click_times[1] - click_times[0]) < DOUBLE_CLICK_TIME

class PhysicsSystem:
    def __init__(self, vertices, edges):
        self.vertices = vertices
        self.edges = edges
        self.velocities = {v: [0.0, 0.0] for v in vertices}

    def rebuild(self):
        self.velocities = {v: [0.0, 0.0] for v in self.vertices}

    def get_connected(self, vertex):
        connected = set()
        for e in self.edges:
            if e.start == vertex:
                connected.add(e.end)
            elif e.end == vertex:
                connected.add(e.start)
        return connected

    def nudge_neighbors(self, moved_vertex, new_pos, old_pos):
        dx = new_pos[0] - old_pos[0]
        dy = new_pos[1] - old_pos[1]
        if dx == 0 and dy == 0:
            return

        follow_strength = 0.02  # Smaller = softer jiggle

        for neighbor in self.get_connected(moved_vertex):
            if neighbor not in self.velocities:
                self.velocities[neighbor] = [0.0, 0.0]

            self.velocities[neighbor][0] += dx * follow_strength
            self.velocities[neighbor][1] += dy * follow_strength

    def update(self):
        damping = 0.75
        for v in self.vertices:
            if v in self.velocities:
                vx, vy = self.velocities[v]
                v.pos[0] += vx
                v.pos[1] += vy
                self.velocities[v][0] *= damping
                self.velocities[v][1] *= damping


class Vertex:
    def __init__(self, pos, name):
        self.pos = list(pos)
        self.name = name
        self.highlight = False

    def draw(self, screen, selected=False, hovered=False):
        color = SELECTED_COLOR if self.highlight or selected else VERTEX_HOVER_COLOR if hovered else VERTEX_COLOR
        pygame.draw.circle(screen, VERTEX_OUTLINE_COLOR, self.pos, VERTEX_RADIUS + VERTEX_OUTLINE_WIDTH)
        pygame.draw.circle(screen, color, self.pos, VERTEX_RADIUS)
        text = font.render(self.name, True, (255, 255, 255))
        screen.blit(text, text.get_rect(center=self.pos))

    def is_clicked(self, pos):
        dx, dy = self.pos[0] - pos[0], self.pos[1] - pos[1]
        return dx * dx + dy * dy <= VERTEX_RADIUS ** 2

class Edge:
    def __init__(self, start, end, value=None):
        self.start = start
        self.end = end
        self.value = value
        self.highlight = False

    def draw(self, screen):
        color = EDGE_HOVER_COLOR if self.highlight else EDGE_COLOR
        pygame.draw.line(screen, color, self.start.pos, self.end.pos, 2)
        if self.value:
            mid = [(s + e) // 2 for s, e in zip(self.start.pos, self.end.pos)]
            screen.blit(font.render(str(self.value), True, color), mid)

    def is_clicked(self, pos):
        x1, y1 = self.start.pos
        x2, y2 = self.end.pos
        px, py = pos
        dx, dy = x2 - x1, y2 - y1
        if dx == dy == 0:
            return False
        length_sq = dx * dx + dy * dy
        t = ((px - x1) * dx + (py - y1) * dy) / length_sq
        if not (0 <= t <= 1):
            return False
        closest = (x1 + t * dx, y1 + t * dy)
        dist_sq = (closest[0] - px) ** 2 + (closest[1] - py) ** 2
        return dist_sq <= EDGE_CLICK_RADIUS ** 2

def get_vertex_at_pos(pos):
    return next((v for v in vertices if v.is_clicked(pos)), None)

def get_edge_at_pos(pos):
    return next((e for e in edges if e.is_clicked(pos)), None)

def save_graph(filename="graph.json"):
    with open(filename, "w") as f:
        json.dump({
            "vertices": [{"name": v.name, "pos": v.pos} for v in vertices],
            "edges": [{"start": e.start.name, "end": e.end.name, "value": e.value} for e in edges]
        }, f)

def load_graph(filename="graph.json"):
    global vertex_names
    with open(filename, "r") as f:
        data = json.load(f)
    name_map = {v["name"]: Vertex(v["pos"], v["name"]) for v in data["vertices"]}
    vertices.clear()
    vertices.extend(name_map.values())
    edges.clear()
    edges.extend(Edge(name_map[e["start"]], name_map[e["end"]], e.get("value")) for e in data["edges"])
    vertex_names = iter(name for name in string.ascii_uppercase if name not in name_map)
    rebuild_edge_lookup()
    mark_all_problems_dirty()

def mark_all_problems_dirty():
    for s in np_problems:
        s.needs_update = True

def draw_button(rect, text, hovered):
    pygame.draw.rect(screen, BUTTON_HOVER_COLOR if hovered else BUTTON_COLOR, rect, border_radius=8)
    label = font.render(text, True, BUTTON_TEXT_COLOR)
    label_rect = label.get_rect(center=rect.center)
    screen.blit(label, label_rect)
def update_k_value_from_input():
    global k_value, input_text
    try:
        k_value = max(1, int(input_text))
        mark_all_problems_dirty()
    except ValueError:
        pass

# NP Problems
class NPProblem:
    def __init__(self, name, vertices, edges):
        self.name = name
        self.vertices = vertices
        self.edges = edges
        self.k = None
        self.result = (False, [])
        self.needs_update = True

    def compute(self, k): pass

    def update(self, k):
        if self.needs_update or self.k != k:
            self.k = k
            self.result = self.compute(k)
            self.needs_update = False

    def render_debug(self, screen, font, k, y, mouse_pos):
        self.update(k)
        found, members = self.result
        lines = [f"{self.name} <G,{k}> = {found}", f"Set: {', '.join(members) if found else 'None'}"]
        area = pygame.Rect(10, y, 300, len(lines) * 20)
        global hovered_problem
        if area.collidepoint(mouse_pos):
            hovered_problem = self
        for line in lines:
            text = font.render(line, True, (255, 255, 100) if area.collidepoint(mouse_pos) else (200, 200, 200))
            screen.blit(text, (10, y))
            y += 20
        return y

class IndependentSetSolver(NPProblem):
    def __init__(self, v, e): super().__init__("INDEPENDENT-SET", v, e)
    def compute(self, k):
        adj = {v.name: set() for v in self.vertices}
        for e in self.edges:
            adj[e.start.name].add(e.end.name)
            adj[e.end.name].add(e.start.name)
        for combo in itertools.combinations(self.vertices, k):
            names = [v.name for v in combo]
            if all(n2 not in adj[n1] for i, n1 in enumerate(names) for n2 in names[i+1:]):
                return True, names
        return False, []

class CliqueSolver(NPProblem):
    def __init__(self, v, e): super().__init__("CLIQUE", v, e)
    def compute(self, k):
        adj = {v.name: set() for v in self.vertices}
        for e in self.edges:
            adj[e.start.name].add(e.end.name)
            adj[e.end.name].add(e.start.name)
        for combo in itertools.combinations(self.vertices, k):
            names = [v.name for v in combo]
            if all(n2 in adj[n1] for i, n1 in enumerate(names) for n2 in names[i+1:]):
                return True, names
        return False, []

class VertexCoverSolver(NPProblem):
    def __init__(self, v, e): super().__init__("VERTEX-COVER", v, e)
    def compute(self, k):
        edge_set = {(e.start.name, e.end.name) for e in self.edges}
        for combo in itertools.combinations(self.vertices, k):
            cover = {v.name for v in combo}
            if all(e[0] in cover or e[1] in cover for e in edge_set):
                return True, list(cover)
        return False, []

class HamiltonianPathSolver(NPProblem):
    def __init__(self, v, e): super().__init__("HAMPATH", v, e)
    def compute(self, k):
        if len(self.vertices) < 2: return False, []
        adj = {v.name: set() for v in self.vertices}
        for e in self.edges:
            adj[e.start.name].add(e.end.name)
            adj[e.end.name].add(e.start.name)
        for path in itertools.permutations([v.name for v in self.vertices]):
            if all(path[i+1] in adj[path[i]] for i in range(len(path)-1)):
                return True, list(path)
        return False, []

np_problems = [
    IndependentSetSolver(vertices, edges),
    CliqueSolver(vertices, edges),
    VertexCoverSolver(vertices, edges),
    HamiltonianPathSolver(vertices, edges)
]

def main():
    global selected_vertex, moving_vertex, input_mode, input_target, input_text, k_value, k_input_active, hovered_problem
    dragging = False
    physics = PhysicsSystem(vertices, edges)

    while True:
        screen.fill(BACKGROUND_COLOR)
        pos = pygame.mouse.get_pos()

        hovered_vertex = get_vertex_at_pos(pos)
        hovered_edge = get_edge_at_pos(pos)
        for e in edges: e.highlight = (e == hovered_edge)

        save_hovered = save_button.collidepoint(pos)
        load_hovered = load_button.collidepoint(pos)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            elif event.type == pygame.KEYDOWN:
                if k_input_active:
                    if event.key == pygame.K_RETURN: update_k_value_from_input(); k_input_active = False; input_text = ""
                    elif event.key == pygame.K_BACKSPACE: input_text = input_text[:-1]
                    elif event.key == pygame.K_ESCAPE: k_input_active = False; input_text = ""
                    elif event.unicode.isdigit(): input_text += event.unicode
                elif input_mode:
                    if event.key == pygame.K_RETURN:
                        if input_mode == 'vertex' and input_text and all(v.name != input_text for v in vertices):
                            input_target.name = input_text
                        elif input_mode == 'edge': input_target.value = input_text or None
                        input_mode = None; input_text = ""; mark_all_problems_dirty()
                    elif event.key == pygame.K_BACKSPACE: input_text = input_text[:-1]
                    elif event.key == pygame.K_ESCAPE: input_mode = None; input_text = ""
                    else: input_text += event.unicode

            elif event.type == pygame.MOUSEBUTTONDOWN and not input_mode:
                if save_button.collidepoint(pos): save_graph(); continue
                elif load_button.collidepoint(pos): load_graph(); continue
                elif k_input_box.collidepoint(pos): k_input_active = True; input_text = str(k_value); continue

                clicked_vertex = hovered_vertex
                clicked_edge = hovered_edge

                if event.button == 3:
                    if clicked_vertex: input_mode = 'vertex'; input_target = clicked_vertex; input_text = clicked_vertex.name
                    elif clicked_edge: input_mode = 'edge'; input_target = clicked_edge; input_text = clicked_edge.value or ""
                    continue

                if is_double_click():
                    if clicked_vertex:
                        edges[:] = [e for e in edges if e.start != clicked_vertex and e.end != clicked_vertex]
                        vertices.remove(clicked_vertex); rebuild_edge_lookup(); selected_vertex = None
                    elif clicked_edge: edges.remove(clicked_edge); rebuild_edge_lookup()
                    mark_all_problems_dirty(); continue

                if clicked_vertex:
                    if selected_vertex and selected_vertex != clicked_vertex and not edge_exists(selected_vertex, clicked_vertex):
                        edges.append(Edge(selected_vertex, clicked_vertex)); rebuild_edge_lookup(); selected_vertex = None
                    else:
                        selected_vertex = clicked_vertex
                        moving_vertex = clicked_vertex
                        dragging = True
                    mark_all_problems_dirty()
                elif not clicked_edge:
                    try:
                        name = next(vertex_names)
                        vertices.append(Vertex(pos, name)); mark_all_problems_dirty()
                    except StopIteration: print("No more vertex names available.")

            elif event.type == pygame.MOUSEBUTTONUP: dragging = False; moving_vertex = None
            elif event.type == pygame.MOUSEMOTION and dragging and moving_vertex:
                old_pos = moving_vertex.pos[:]
                moving_vertex.pos = list(pos)
                physics.nudge_neighbors(moving_vertex, moving_vertex.pos, old_pos)

        hovered_problem = None
        y = 60
        for solver in np_problems:
            y = solver.render_debug(screen, debug_font, k_value, y, pos)

        for v in vertices: v.highlight = False
        if hovered_problem:
            found, members = hovered_problem.result
            member_set = set(members)
            for v in vertices: v.highlight = v.name in member_set

        for edge in edges: edge.draw(screen)
        for vertex in vertices: vertex.draw(screen, selected=(vertex == selected_vertex), hovered=(vertex == hovered_vertex))

        draw_button(save_button, "Save", save_hovered)
        draw_button(load_button, "Load", load_hovered)

        pygame.draw.rect(screen, (100, 100, 100), k_input_box, border_radius=6)
        k_label = font.render(f"k: {input_text if k_input_active else k_value}", True, BUTTON_TEXT_COLOR)
        screen.blit(k_label, (k_input_box.x + 8, k_input_box.y + 8))

        if input_mode:
            pygame.draw.rect(screen, INPUT_BOX_COLOR, (10, 550, 780, 40), border_radius=6)
            label = "Editing Vertex Name:" if input_mode == 'vertex' else "Editing Edge Value:"
            prompt = input_font.render(f"{label} {input_text}", True, INPUT_TEXT_COLOR)
            screen.blit(prompt, (20, 558))

        physics.update()

        pygame.display.flip()
        clock.tick(60)

if __name__ == '__main__':
    main()
