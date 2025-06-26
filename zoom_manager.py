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