import pygame
import matplotlib.pyplot as plt
import matplotlib as mpl
import io
from config import FONT

# Reset to safe mathtext rendering (built-in math engine)
mpl.rcParams.update({
    "text.usetex": False,         # Don't use external LaTeX
    "font.family": "serif",
    "mathtext.fontset": "cm",     # Use Computer Modern (LaTeX-style font)
    "mathtext.rm": "serif",
})

_surface_cache = {}

def get_math_surface(text, color=(255, 255, 255), dpi=200, fontsize=8):
    if not text:
        return FONT.render("", True, color)

    key = (text, color)
    if key in _surface_cache:
        return _surface_cache[key]

    try:
        fig = plt.figure(figsize=(0.01, 0.01))
        ax = fig.add_axes([0, 0, 1, 1])
        ax.axis("off")

        ax.text(0, 0, f"${text}$", fontsize=fontsize, color=_mpl_color(color))

        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=dpi, transparent=True, bbox_inches='tight', pad_inches=0)
        buf.seek(0)
        plt.close(fig)

        surface = pygame.image.load(buf).convert_alpha()
        _surface_cache[key] = surface
        return surface
    except Exception as e:
        print("[Math render fallback]", e)
        fallback = FONT.render(text, True, color)
        _surface_cache[key] = fallback
        return fallback

def _mpl_color(rgb):
    return tuple(c / 255 for c in rgb)
