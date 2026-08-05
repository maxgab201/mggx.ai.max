from PIL import Image, ImageColor, ImageDraw
import math
from pathlib import Path

def get_affine_coeffs(src_points, dst_points):
    """
    Find affine coefficients that map dst_points to src_points (required by Pillow).
    """
    (x0, y0), (x1, y1), (x2, y2) = dst_points
    (u0, v0), (u1, v1), (u2, v2) = src_points

    den = (x0*(y1 - y2) + x1*(y2 - y0) + x2*(y0 - y1))
    if den == 0:
        raise ValueError("Points are collinear")

    a = (u0*(y1 - y2) + u1*(y2 - y0) + u2*(y0 - y1)) / den
    b = (u0*(x2 - x1) + u1*(x0 - x2) + u2*(x1 - x0)) / den
    c = (u0*(x1*y2 - x2*y1) + u1*(x2*y0 - x0*y2) + u2*(x0*y1 - x1*y0)) / den

    d = (v0*(y1 - y2) + v1*(y2 - y0) + v2*(y0 - y1)) / den
    e = (v0*(x2 - x1) + v1*(x0 - x2) + v2*(x1 - x0)) / den
    f = (v0*(x1*y2 - x2*y1) + v1*(x2*y0 - x0*y2) + v2*(x0*y1 - x1*y0)) / den

    return (a, b, c, d, e, f)

def apply_tint(img, factor):
    """Simple tinting by multiplying RGB channels by factor."""
    if factor >= 1.0:
        return img

    return img.point(lambda p: int(p * factor) if p < 256 else p)

def render_isometric_block(textures_dir: Path, output_path: str, view_type="upper", resolution=1024, bg_color="#101010"):
    """
    Renders an isometric view of a block using the distinct top, bottom, and side textures.
    views: 'upper' or 'lower'
    """
    top_img = Image.open(textures_dir / "top.png").convert("RGBA")
    bottom_img = Image.open(textures_dir / "bottom.png").convert("RGBA")
    sides_img = Image.open(textures_dir / "sides.png").convert("RGBA")

    out_img = Image.new("RGBA", (resolution, resolution), ImageColor.getcolor(bg_color, "RGBA"))

    cx, cy = resolution / 2, resolution / 2
    s = resolution * 0.35

    angle30 = math.pi / 6
    dx = s * math.cos(angle30)
    dy = s * math.sin(angle30)

    light_top = 1.0
    light_left = 0.8
    light_right = 0.6
    light_bot = 0.5

    if view_type == "upper":
        top_dst = ((cx - dx, cy - s + dy), (cx, cy - s), (cx + dx, cy - s + dy), (cx, cy))
        left_dst = ((cx - dx, cy + dy), (cx - dx, cy - s + dy), (cx, cy), (cx, cy + s))
        right_dst = ((cx, cy + s), (cx, cy), (cx + dx, cy - s + dy), (cx + dx, cy + dy))

        # Format: (dest_polygon, light_factor, texture_image)
        faces = [
            (top_dst, light_top, top_img),
            (left_dst, light_left, sides_img),
            (right_dst, light_right, sides_img)
        ]

    elif view_type == "lower":
        bot_dst = ((cx, cy), (cx + dx, cy + s - dy), (cx, cy + s), (cx - dx, cy + s - dy))
        left_dst = ((cx - dx, cy + s - dy), (cx - dx, cy - dy), (cx, cy - s), (cx, cy))
        right_dst = ((cx, cy), (cx, cy - s), (cx + dx, cy - dy), (cx + dx, cy + s - dy))

        faces = [
            (bot_dst, light_bot, bottom_img),
            (left_dst, light_left, sides_img),
            (right_dst, light_right, sides_img)
        ]

    else:
        raise ValueError(f"Unknown view type {view_type}")


    for dst, light, img in faces:
        tw, th = img.size
        # Standard source points for mapping (Top-Left, Top-Right, Bottom-Right, Bottom-Left)
        src_rect = [(0,0), (tw,0), (tw,th), (0,th)]

        coeffs = get_affine_coeffs(src_rect[:3], dst[:3])

        r, g, b, a = img.split()
        r = apply_tint(r, light)
        g = apply_tint(g, light)
        b = apply_tint(b, light)
        tinted = Image.merge("RGBA", (r, g, b, a))

        face_img = tinted.transform(
            (resolution, resolution),
            Image.AFFINE,
            coeffs,
            resample=Image.BICUBIC
        )

        mask = Image.new("L", (resolution, resolution), 0)
        draw = ImageDraw.Draw(mask)
        draw.polygon(dst, fill=255)

        face_alpha = face_img.split()[3]
        combined_mask = Image.new("L", (resolution, resolution), 0)
        combined_mask.paste(face_alpha, (0,0), mask)

        out_img.paste(face_img, (0,0), combined_mask)

    out_img.save(output_path)
