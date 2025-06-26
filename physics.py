from utils import dfs_stack


class PhysicsSystem:
    def __init__(self, vertices, edges):
        self.vertices = vertices
        self.edges = edges
        self.velocities = {v: [0.0, 0.0] for v in vertices}

    def rebuild(self):
        self.velocities = {v: [0.0, 0.0] for v in self.vertices}

    def move_component(self, anchor_vertex, new_pos, old_pos, strength=0.25):
        dx = new_pos[0] - old_pos[0]
        dy = new_pos[1] - old_pos[1]
        if dx == 0 and dy == 0:
            return

        connected_vertices = self.get_connected_component(anchor_vertex)
        for v in connected_vertices:
            if v not in self.velocities:
                self.velocities[v] = [0.0, 0.0]
            self.velocities[v][0] += dx * strength
            self.velocities[v][1] += dy * strength

    def get_connected(self, vertex):
        connected = set()
        for e in self.edges:
            if e.start == vertex:
                connected.add(e.end)
            elif e.end == vertex:
                connected.add(e.start)
        return connected

    def get_connected_component(self, start_vertex):
        visited = set()
        adj = {v: self.get_connected(v) for v in self.vertices}
        dfs_stack(adj, start_vertex, visited)
        return visited

    def nudge_neighbors(self, moved_vertex, new_pos, old_pos, strength=0.02):
        dx = new_pos[0] - old_pos[0]
        dy = new_pos[1] - old_pos[1]
        if dx == 0 and dy == 0:
            return

        for neighbor in self.get_connected(moved_vertex):
            if neighbor not in self.velocities:
                self.velocities[neighbor] = [0.0, 0.0]
            self.velocities[neighbor][0] += dx * strength
            self.velocities[neighbor][1] += dy * strength

    def update(self):
        damping = 0.75
        for v in self.vertices:
            if v in self.velocities:
                vx, vy = self.velocities[v]
                if vx == 0.0 and vy == 0.0:
                    continue

                v.pos[0] += vx
                v.pos[1] += vy
                self.velocities[v][0] *= damping
                self.velocities[v][1] *= damping
