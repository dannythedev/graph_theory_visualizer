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

        follow_strength = 0.02
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
