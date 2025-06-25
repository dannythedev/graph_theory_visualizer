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

# Buttons
SAVE_BUTTON_RECT = pygame.Rect(10, 10, 100, 36)
LOAD_BUTTON_RECT = pygame.Rect(120, 10, 100, 36)
K_INPUT_BOX_RECT = pygame.Rect(230, 10, 60, 36)
TOGGLE_DIRECTED_RECT = pygame.Rect(300, 10, 120, 36)
CLEAR_BUTTON_RECT = pygame.Rect(590, 10, 100, 36)
DUPLICATE_BUTTON_RECT = pygame.Rect(440, 10, 140, 18)
DUPLICATE_SLIDER_RECT = pygame.Rect(440, 33, 140, 12)  # Adjusted height and aligned with button

VERTEX_LIMIT = 50