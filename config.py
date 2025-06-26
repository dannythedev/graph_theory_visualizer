import pygame

pygame.font.init()

# Colors
BACKGROUND_COLOR = (30, 30, 30)
VERTEX_COLOR = (100, 149, 237)
VERTEX_HOVER_COLOR = (70, 130, 180)
EDGE_COLOR = (170, 170, 170)
EDGE_HOVER_COLOR = (142, 225, 142)
SELECTED_COLOR = (255, 99, 71)
VERTEX_OUTLINE_COLOR = (255, 255, 255)
BUTTON_COLOR = (50, 50, 50)
BUTTON_HOVER_COLOR = (70, 70, 70)
BUTTON_TEXT_COLOR = (255, 255, 255)
INPUT_BOX_COLOR = (40, 40, 40)
INPUT_TEXT_COLOR = (255, 255, 255)

# Dimensions
VERTEX_RADIUS = 20
EDGE_CLICK_RADIUS = 15
VERTEX_OUTLINE_WIDTH = 4
DOUBLE_CLICK_TIME = 200

# Fonts
FONT = pygame.font.SysFont("Segoe UI", 13, bold=True)
INPUT_FONT = pygame.font.SysFont("consolas", 16, bold=True)
DEBUG_FONT = pygame.font.SysFont("consolas", 16)

def next_button(label, x, y, padding=12, height=32):
    """Create a button rect based on the label, starting at (x, y)."""
    width = FONT.render(label, True, (0, 0, 0)).get_width() + 2 * padding
    rect = pygame.Rect(x, y, width, height)
    return rect, x + width + 10  # Return new rect and next x-position

x = 10
y = 10

SAVE_BUTTON_RECT, x = next_button("Save", x, y)
LOAD_BUTTON_RECT, x = next_button("Load", x, y)
K_INPUT_BOX_RECT, x = next_button("k=3", x, y)
SELECT_ST_BUTTON_RECT, x = next_button("Select S/T", x, y)
TOGGLE_DIRECTED_RECT, x = next_button("Directed: OFF", x, y)
DUPLICATE_BUTTON_RECT, x = next_button("Duplicate", x, y)
COMPLEMENT_BUTTON_RECT, x = next_button("Complement", x, y)
CLEAR_BUTTON_RECT, x = next_button("Clear", x, y)
RANDOM_BUTTON_RECT, x = next_button("Random", x, y)

# Optional: Slider below Duplicate
DUPLICATE_SLIDER_RECT = pygame.Rect(
    DUPLICATE_BUTTON_RECT.x,
    DUPLICATE_BUTTON_RECT.bottom + 4,
    DUPLICATE_BUTTON_RECT.width,
    12
)


VERTEX_LIMIT = 75
EDGE_LIMIT = 150
# Colors to avoid (RGB)
AVOID_COLORS = [
    (100, 149, 237),  # VERTEX_COLOR
    (70, 130, 180),   # VERTEX_HOVER_COLOR
    (255, 99, 71),    # SELECTED_COLOR
]
