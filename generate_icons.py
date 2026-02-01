#!/usr/bin/env python
"""Generate PWA icons for ChoreChamp."""
from PIL import Image, ImageDraw, ImageFont
import os

# Icon sizes needed for PWA
SIZES = [72, 96, 128, 144, 152, 192, 384, 512]

# Colors
PRIMARY = (99, 102, 241)  # #6366F1
SECONDARY = (16, 185, 129)  # #10B981
GOLD = (252, 211, 77)  # #FCD34D
WHITE = (255, 255, 255)


def create_icon(size):
    """Create a single icon at the specified size."""
    # Create image with primary color background
    img = Image.new('RGBA', (size, size), PRIMARY)
    draw = ImageDraw.Draw(img)

    # Draw rounded rectangle background (simulate rounded corners)
    padding = size // 8
    corner_radius = size // 5

    # Draw trophy shape (simplified)
    center_x = size // 2
    center_y = size // 2

    # Trophy cup (gold circle)
    cup_radius = size // 3
    cup_y_offset = -size // 10
    draw.ellipse([
        center_x - cup_radius,
        center_y - cup_radius + cup_y_offset,
        center_x + cup_radius,
        center_y + cup_radius + cup_y_offset
    ], fill=GOLD)

    # Trophy stem
    stem_width = size // 8
    stem_height = size // 6
    stem_top = center_y + cup_radius // 2 + cup_y_offset
    draw.rectangle([
        center_x - stem_width // 2,
        stem_top,
        center_x + stem_width // 2,
        stem_top + stem_height
    ], fill=GOLD)

    # Trophy base
    base_width = size // 3
    base_height = size // 12
    base_top = stem_top + stem_height
    draw.rectangle([
        center_x - base_width // 2,
        base_top,
        center_x + base_width // 2,
        base_top + base_height
    ], fill=GOLD)

    # Star on trophy (white)
    star_size = size // 8
    star_y = center_y - size // 8 + cup_y_offset
    # Simple star using polygon
    points = []
    for i in range(5):
        # Outer points
        import math
        angle = math.radians(i * 72 - 90)
        points.append((
            center_x + star_size * math.cos(angle),
            star_y + star_size * math.sin(angle)
        ))
        # Inner points
        angle = math.radians(i * 72 - 90 + 36)
        points.append((
            center_x + star_size * 0.4 * math.cos(angle),
            star_y + star_size * 0.4 * math.sin(angle)
        ))
    draw.polygon(points, fill=WHITE)

    # Checkmark circle (green) in bottom right
    check_radius = size // 5
    check_x = center_x + size // 4
    check_y = center_y + size // 4
    draw.ellipse([
        check_x - check_radius,
        check_y - check_radius,
        check_x + check_radius,
        check_y + check_radius
    ], fill=SECONDARY)

    # Checkmark (white)
    check_width = max(2, size // 32)
    # Draw checkmark as lines
    p1 = (check_x - check_radius // 2, check_y)
    p2 = (check_x - check_radius // 6, check_y + check_radius // 3)
    p3 = (check_x + check_radius // 2, check_y - check_radius // 3)
    draw.line([p1, p2], fill=WHITE, width=check_width)
    draw.line([p2, p3], fill=WHITE, width=check_width)

    return img


def main():
    """Generate all icon sizes."""
    icons_dir = os.path.join(os.path.dirname(__file__), 'app', 'static', 'icons')
    os.makedirs(icons_dir, exist_ok=True)

    print("Generating PWA icons...")

    for size in SIZES:
        icon = create_icon(size)
        filename = os.path.join(icons_dir, f'icon-{size}.png')
        icon.save(filename, 'PNG')
        print(f"  Created: icon-{size}.png")

    # Also create a favicon
    favicon = create_icon(32)
    favicon.save(os.path.join(icons_dir, 'favicon.png'), 'PNG')
    print("  Created: favicon.png")

    print("\nDone! Icons saved to app/static/icons/")


if __name__ == '__main__':
    main()
