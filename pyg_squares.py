import pyglet
from pyglet import shapes
from pyglet import gl
from pyglet.window import key
import random
import time
import math



window = pyglet.window.Window(1000, 1000)

# Batches for drawing
batch = pyglet.graphics.Batch()
square_batch = pyglet.graphics.Batch()
rot_square_batch = pyglet.graphics.Batch()

# Lists to hold shape objects
points = []
square_lines = []
rot_square_lines = []

# --- Minimum Area Rotated Bounding Square ---

def convex_hull(pts):
    """Compute the convex hull using Graham scan."""
    pts = sorted(set(pts))
    if len(pts) <= 1:
        return pts
    
    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    
    lower = []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    
    upper = []
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    
    return lower[:-1] + upper[:-1]

def rotate_point(px, py, angle, cx=0, cy=0):
    """Rotate point (px, py) around (cx, cy) by angle radians."""
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)
    dx = px - cx
    dy = py - cy
    return (cx + dx * cos_a - dy * sin_a, cy + dx * sin_a + dy * cos_a)

def minimum_bounding_square(pts):
    """Find the minimum area bounding square for a set of points."""
    if len(pts) < 2:
        return None, 0, float('inf')
    
    hull = convex_hull(pts)
    if len(hull) < 2:
        return None, 0, float('inf')
    
    min_area = float('inf')
    best_angle = 0
    best_corners = None
    
    # Collect candidate angles: each hull edge, plus 45° offsets (for diagonal alignments)
    candidate_angles = []
    for i in range(len(hull)):
        p1 = hull[i]
        p2 = hull[(i + 1) % len(hull)]
        edge_angle = math.atan2(p2[1] - p1[1], p2[0] - p1[0])
        candidate_angles.append(edge_angle)
        # Also test 45° offset - optimal square may have diagonal aligned with hull features
        candidate_angles.append(edge_angle + math.pi / 4)
    
    # Test each candidate angle
    for angle in candidate_angles:
        # Rotate all points by -angle to align with axes
        rotated = [rotate_point(p[0], p[1], -angle) for p in pts]
        
        # Find axis-aligned bounding box in rotated space
        r_min_x = min(p[0] for p in rotated)
        r_max_x = max(p[0] for p in rotated)
        r_min_y = min(p[1] for p in rotated)
        r_max_y = max(p[1] for p in rotated)
        
        width = r_max_x - r_min_x
        height = r_max_y - r_min_y
        side = max(width, height)
        sq_area = side * side
        
        if sq_area < min_area:
            min_area = sq_area
            best_angle = angle
            # Center the square on the bounding box center
            cx = (r_min_x + r_max_x) / 2
            cy = (r_min_y + r_max_y) / 2
            half = side / 2
            # Square corners in rotated (axis-aligned) space
            corners_rot = [
                (cx - half, cy - half),
                (cx + half, cy - half),
                (cx + half, cy + half),
                (cx - half, cy + half)
            ]
            # Rotate corners back to original orientation
            best_corners = [rotate_point(c[0], c[1], best_angle) for c in corners_rot]
    
    return best_corners, best_angle, min_area

def generate_points_and_squares():
    """Generate new random points and calculate bounding squares."""
    global points, square_lines, rot_square_lines
    
    # Clear existing shapes
    points.clear()
    square_lines.clear()
    rot_square_lines.clear()
    num_points = random.randint(2, 5)

    # Generate new random points
    for _ in range(num_points):
        points.append(shapes.Circle(random.randint(100, 500), 
                                    random.randint(100, 500),
                                    2,
                                    color=(255,255,255),
                                    batch=batch))
    
    # Calculate axis-aligned bounding square (red)
    min_x = min(point.x for point in points)
    min_y = min(point.y for point in points)
    max_x = max(point.x for point in points)
    max_y = max(point.y for point in points)
    
    if max_x - min_x > max_y - min_y:  # square is wider than tall
        max_y = max_y + ((max_x - min_x) - (max_y - min_y))
    else:
        max_x = max_x + ((max_y - min_y) - (max_x - min_x))
    
    square_color = (255, 0, 0)
    square_lines.append(shapes.Line(min_x, min_y, max_x, min_y, color=square_color, batch=square_batch))
    square_lines.append(shapes.Line(max_x, min_y, max_x, max_y, color=square_color, batch=square_batch))
    square_lines.append(shapes.Line(max_x, max_y, min_x, max_y, color=square_color, batch=square_batch))
    square_lines.append(shapes.Line(min_x, max_y, min_x, min_y, color=square_color, batch=square_batch))
    
    area = ((max_x - min_x) * (max_y - min_y)) / 100
    print(f"Area 1 (Red): {area}")
    
    # Calculate minimum area rotated bounding square (green)
    point_coords = [(p.x, p.y) for p in points]
    rot_corners, rot_angle, rot_area = minimum_bounding_square(point_coords)
    
    print(f"Area 2 (Green, rotated): {rot_area / 100}")
    print(f"Square/OriginalArea ratio: {rot_area / area}")
    print(f"Rotation angle: {math.degrees(rot_angle):.2f} degrees")
    print("-" * 40)
    
    # Draw the rotated minimum bounding square in green
    rot_square_color = (0, 255, 0)
    if rot_corners:
        rot_square_lines.append(shapes.Line(rot_corners[0][0], rot_corners[0][1], rot_corners[1][0], rot_corners[1][1], color=rot_square_color, batch=rot_square_batch))
        rot_square_lines.append(shapes.Line(rot_corners[1][0], rot_corners[1][1], rot_corners[2][0], rot_corners[2][1], color=rot_square_color, batch=rot_square_batch))
        rot_square_lines.append(shapes.Line(rot_corners[2][0], rot_corners[2][1], rot_corners[3][0], rot_corners[3][1], color=rot_square_color, batch=rot_square_batch))
        rot_square_lines.append(shapes.Line(rot_corners[3][0], rot_corners[3][1], rot_corners[0][0], rot_corners[0][1], color=rot_square_color, batch=rot_square_batch))

# Generate initial points and squares
generate_points_and_squares()

# Auto-generation state
auto_generate_active = False

def auto_generate_callback(dt):
    """Callback for scheduled auto-generation."""
    generate_points_and_squares()

@window.event
def on_key_press(symbol, modifiers):
    global auto_generate_active
    if symbol == key.SPACE:
        generate_points_and_squares()
        if not auto_generate_active:
            auto_generate_active = True
            pyglet.clock.schedule_interval(auto_generate_callback, 0.8)

@window.event
def on_key_release(symbol, modifiers):
    global auto_generate_active
    if symbol == key.SPACE:
        if auto_generate_active:
            auto_generate_active = False
            pyglet.clock.unschedule(auto_generate_callback)

@window.event
def on_draw():
    window.clear()
    square_batch.draw()
    batch.draw()
    rot_square_batch.draw()

pyglet.app.run()
