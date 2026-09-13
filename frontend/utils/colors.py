from PyQt6.QtGui import QColor

def lighten_color(color, factor=1.5):
    """Освітлити колір на factor (>=1.0)"""
    r = min(int(color.red() * factor), 255)
    g = min(int(color.green() * factor), 255)
    b = min(int(color.blue() * factor), 255)
    return QColor(r, g, b)

def darken_color(color, factor=0.5):
    """Затемнити колір на factor (<=1.0)"""
    r = max(int(color.red() * factor), 0)
    g = max(int(color.green() * factor), 0)
    b = max(int(color.blue() * factor), 0)
    return QColor(r, g, b)