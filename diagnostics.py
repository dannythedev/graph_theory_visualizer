class GraphDiagnostics:
    def __init__(self, vertices, edges):
        self.needs_update = True

        self.vertices = vertices
        self.edges = edges
        self.info = {
            "Cyclic": False,
            "Strongly Connected Components": 0,
            "Components": 0,
        }

    def update(self, directed=False):
        if not self.needs_update:
            return
        self.needs_update = False

        self.adj = self._build_adj(directed)
        self.rev_adj = self._build_adj_reverse() if directed else None

        visited = set()

        self.info["Cyclic"] = self._has_cycle(directed, visited.copy())
        self.info["Components"] = self._component_count(visited.copy())
        self.info["Strongly Connected Components"] = (
            self._strongly_connected_components() if directed else self.info["Components"]
        )

    def _build_adj(self, directed):
        adj = {v.name: set() for v in self.vertices}
        for e in self.edges:
            adj[e.start.name].add(e.end.name)
            if not directed:
                adj[e.end.name].add(e.start.name)
        return adj

    def _build_adj_reverse(self):
        rev_adj = {v.name: set() for v in self.vertices}
        for e in self.edges:
            rev_adj[e.end.name].add(e.start.name)
        return rev_adj

    def _has_cycle(self, directed, visited):
        if directed:
            rec_stack = set()

            def dfs(v):
                visited.add(v)
                rec_stack.add(v)
                for neighbor in self.adj[v]:
                    if neighbor not in visited:
                        if dfs(neighbor):
                            return True
                    elif neighbor in rec_stack:
                        return True
                rec_stack.remove(v)
                return False

        else:
            def dfs(v, parent):
                visited.add(v)
                for neighbor in self.adj[v]:
                    if neighbor not in visited:
                        if dfs(neighbor, v):
                            return True
                    elif neighbor != parent:
                        return True
                return False

        for v in self.adj:
            if v not in visited:
                if directed:
                    if dfs(v):
                        return True
                else:
                    if dfs(v, None):
                        return True
        return False

    def _component_count(self, visited):
        count = 0

        def dfs(v):
            visited.add(v)
            for n in self.adj[v]:
                if n not in visited:
                    dfs(n)

        for v in self.adj:
            if v not in visited:
                count += 1
                dfs(v)
        return count

    def _strongly_connected_components(self):
        visited = set()
        order = []

        def dfs1(v):
            visited.add(v)
            for neighbor in self.adj[v]:
                if neighbor not in visited:
                    dfs1(neighbor)
            order.append(v)

        for v in self.adj:
            if v not in visited:
                dfs1(v)

        visited.clear()
        count = 0

        def dfs2(v):
            visited.add(v)
            for neighbor in self.rev_adj[v]:
                if neighbor not in visited:
                    dfs2(neighbor)

        for v in reversed(order):
            if v not in visited:
                dfs2(v)
                count += 1

        return count

    def mark_dirty(self):
        self.needs_update = True

    def render(self, screen, font, y_start, mouse_pos):
        lines = [
            f"  Cyclic: {self.info['Cyclic']}",
            f"  Strongly Connected Components: {self.info['Strongly Connected Components']}",
            f"  Components: {self.info['Components']}"
        ]

        for line in lines:
            text = font.render(line, True, (180, 180, 255))
            screen.blit(text, (10, y_start))
            y_start += 14  # Slightly taller spacing for legibility
