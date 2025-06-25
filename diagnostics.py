class GraphDiagnostics:
    def __init__(self, vertices, edges):
        self.needs_update = True
        self.vertices = vertices
        self.edges = edges
        self.info = {}

    def update(self, directed=False):
        if not self.needs_update:
            return
        self.needs_update = False

        self.adj = self._build_adj(directed)
        self.rev_adj = self._build_adj_reverse() if directed else None

        visited = set()

        # Core properties
        self.info["Cyclic"] = self._has_cycle(directed, visited.copy())
        self.info["Components"] = self._component_count(visited.copy())
        self.info["Strongly Connected Components"] = (
            self._strongly_connected_components() if directed else self.info["Components"]
        )

        # Structural properties
        self.info["Is Tree"] = not directed and not self.info["Cyclic"] and self.info["Components"] == 1
        self.info["Is Forest"] = not directed and not self.info["Cyclic"]
        self.info["Is Bipartite"] = self._is_bipartite() if not directed else "N/A"
        self.info["Bridges"] = self._bridge_count()

        # Vertex diagnostics
        degrees = [len(self.adj[v.name]) for v in self.vertices]
        self.info["Max/Min Degree"] = f"{max(degrees, default=0)}, {min(degrees, default=0)}"

    def _bridge_count(self):
        """
        Counts bridges in an undirected graph using Tarjan's algorithm.
        Only works correctly if the graph is undirected.
        """
        time = [0]
        visited = set()
        tin = {}
        low = {}
        bridges = []

        def dfs(v, parent):
            visited.add(v)
            tin[v] = low[v] = time[0]
            time[0] += 1
            for to in self.adj[v]:
                if to == parent:
                    continue
                if to in visited:
                    low[v] = min(low[v], tin[to])
                else:
                    dfs(to, v)
                    low[v] = min(low[v], low[to])
                    if low[to] > tin[v]:
                        bridges.append((v, to))

        for v in self.adj:
            if v not in visited:
                dfs(v, None)

        return len(bridges)

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
                if dfs(v) if directed else dfs(v, None):
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

    def _is_bipartite(self):
        color = {}
        for v in self.adj:
            if v not in color:
                queue = [v]
                color[v] = 0
                while queue:
                    u = queue.pop()
                    for n in self.adj[u]:
                        if n not in color:
                            color[n] = 1 - color[u]
                            queue.append(n)
                        elif color[n] == color[u]:
                            return False
        return True

    def mark_dirty(self):
        self.needs_update = True

    def render(self, screen, font):
        y_start = screen.get_height() - len(self.info.items())*15
        for key, val in self.info.items():
            text = font.render(f"{key}: {val}", True, (180, 180, 255))
            screen.blit(text, (10, y_start))
            y_start += 14
