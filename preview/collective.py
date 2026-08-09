from PIL import Image, ImageColor, ImageDraw
import math
from pathlib import Path
from .render import apply_tint, get_affine_coeffs, apply_pbr_visuals

def render_collective_isometric_block(textures_dir: Path, output_path: str, view_type="upper", resolution=1024, bg_color="#101010", pbr=False, pom=False):
    """
    Renders a 3x3 deterministic arrangement of the block for tileability/collective QA testing.
    """
    def get_texture(name):
        path = textures_dir / f"{name}.png"
        img = Image.open(path).convert("RGBA")
        if pbr or pom:
            img = apply_pbr_visuals(img, textures_dir / f"{name}_s.png", textures_dir / f"{name}_n.png")
        return img

    top_img = get_texture("top")
    bottom_img = get_texture("bottom")
    sides_img = get_texture("sides")

    out_img = Image.new("RGBA", (resolution, resolution), ImageColor.getcolor(bg_color, "RGBA"))

    # We define a 3x3 grid.
    # To fit a 3x3 grid, the size of a single block edge must be smaller.
    cx, cy = resolution / 2, resolution / 2

    # Scale down by about 1/3
    s = resolution * 0.12

    angle30 = math.pi / 6
    dx = s * math.cos(angle30)
    dy = s * math.sin(angle30)

    light_top = 1.0
    light_left = 0.8
    light_right = 0.6
    light_bot = 0.5

    # For a 3x3 isometric grid, we iterate over x, y grid coords.
    # Grid goes from -1 to 1 for 3x3.
    # We must draw them back-to-front depending on the view so they overlap correctly.
    # For "upper", things with smaller y and larger x might be further back.
    # Standard isometric sorting: sort by (grid_x - grid_y) or similar depending on axes.
    # Let's define grid offsets.

    # Grid cell offset vectors in screen space
    # One unit in grid X goes right-down.
    # One unit in grid Y goes left-down.
    gx = (dx, dy)
    gy = (-dx, dy)

    # For proper z-sorting:
    # Upper view: we draw back to front. The backmost is grid (-1, -1) -> actually (min_x, min_y) in a specific axis?
    # Actually, if we map grid (ix, iy) from -1 to 1:
    # drawing order is usually iy from -1 to 1, ix from -1 to 1.

    # Let's generate the 9 blocks.
    blocks = []
    for iy in range(-1, 2):
        for ix in range(-1, 2):
            blocks.append((ix, iy))

    # Sort blocks back to front
    if view_type == "upper":
        blocks.sort(key=lambda b: (b[1], b[0]))
    else:
        # Lower view looks up from the bottom.
        # Z-sorting changes.
        blocks.sort(key=lambda b: (-b[1], b[0]))

    for (ix, iy) in blocks:
        # Center of this specific block
        bcx = cx + ix * gx[0] + iy * gy[0]
        bcy = cy + ix * gx[1] + iy * gy[1]

        # If POM, scale inner slightly
        if pom:
            s_inner = s * 0.95
            dx_i = s_inner * math.cos(angle30)
            dy_i = s_inner * math.sin(angle30)
        else:
            dx_i, dy_i, s_inner = dx, dy, s

        if view_type == "upper":
            top_dst = ((bcx - dx_i, bcy - s_inner + dy_i), (bcx, bcy - s_inner), (bcx + dx_i, bcy - s_inner + dy_i), (bcx, bcy))
            left_dst = ((bcx - dx_i, bcy + dy_i), (bcx - dx_i, bcy - s_inner + dy_i), (bcx, bcy), (bcx, bcy + s_inner))
            right_dst = ((bcx, bcy + s_inner), (bcx, bcy), (bcx + dx_i, bcy - s_inner + dy_i), (bcx + dx_i, bcy + dy_i))

            faces = [
                (top_dst, light_top, top_img),
                (left_dst, light_left, sides_img),
                (right_dst, light_right, sides_img)
            ]

        elif view_type == "lower":
            bot_dst = ((bcx, bcy), (bcx + dx_i, bcy + s_inner - dy_i), (bcx, bcy + s_inner), (bcx - dx_i, bcy + s_inner - dy_i))
            left_dst = ((bcx - dx_i, bcy + s_inner - dy_i), (bcx - dx_i, bcy - dy_i), (bcx, bcy - s_inner), (bcx, bcy))
            right_dst = ((bcx, bcy), (bcx, bcy - s_inner), (bcx + dx_i, bcy - dy_i), (bcx + dx_i, bcy + s_inner - dy_i))

            faces = [
                (bot_dst, light_bot, bottom_img),
                (left_dst, light_left, sides_img),
                (right_dst, light_right, sides_img)
            ]

        if pom:
            mask = Image.new("RGBA", (resolution, resolution), (0,0,0,0))
            draw = ImageDraw.Draw(mask)
            if view_type == "upper":
                poly = ((bcx, bcy-s), (bcx+dx, bcy-s+dy), (bcx+dx, bcy+dy), (bcx, bcy+s), (bcx-dx, bcy+dy), (bcx-dx, bcy-s+dy))
            else:
                poly = ((bcx, bcy-s), (bcx+dx, bcy-dy), (bcx+dx, bcy+s-dy), (bcx, bcy+s), (bcx-dx, bcy+s-dy), (bcx-dx, bcy-dy))
            draw.polygon(poly, fill=(20,20,20,255))
            out_img.paste(mask, (0,0), mask)

        for dst, light, img in faces:
            tw, th = img.size
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
