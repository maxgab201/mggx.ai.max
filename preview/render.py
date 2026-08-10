from PIL import Image, ImageColor, ImageDraw, ImageEnhance
import math
from pathlib import Path
from typing import List, Dict

def get_affine_coeffs(src_points, dst_points):
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
    if factor >= 1.0:
        return img
    return img.point(lambda p: int(p * factor) if p < 256 else p)

def apply_pbr_visuals(albedo: Image.Image, s_map_path: Path, n_map_path: Path) -> Image.Image:
    img = albedo.copy()
    if s_map_path.exists():
        try:
            s_map = Image.open(s_map_path).convert("RGBA")
            s_map = s_map.resize(img.size, Image.NEAREST)
            img = Image.blend(img, s_map, alpha=0.15)
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.2)
        except Exception:
            pass
    if n_map_path.exists():
        try:
            n_map = Image.open(n_map_path).convert("RGBA")
            n_map = n_map.resize(img.size, Image.NEAREST)
            img = Image.blend(img, n_map, alpha=0.1)
        except Exception:
            pass
    return img

def render_isometric_block(textures_dir: Path, output_path: str, view_type="upper", resolution=1024, bg_color="#101010", pbr=False, pom=False, multi_blocks: List[Dict] = None):
    # For single block render, we just use the first block in the list.
    prefix = ""
    if multi_blocks and len(multi_blocks) > 1:
        prefix = f"{multi_blocks[0]['block']}_"

    def get_texture(name):
        path = textures_dir / f"{prefix}{name}.png"
        img = Image.open(path).convert("RGBA")
        if pbr or pom:
            img = apply_pbr_visuals(img, textures_dir / f"{prefix}{name}_s.png", textures_dir / f"{prefix}{name}_n.png")
        return img

    top_img = get_texture("top")
    bottom_img = get_texture("bottom")
    sides_img = get_texture("sides")

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

    if pom:
        s_inner = s * 0.95
        dx_i = s_inner * math.cos(angle30)
        dy_i = s_inner * math.sin(angle30)
    else:
        dx_i, dy_i, s_inner = dx, dy, s

    if view_type == "upper":
        top_dst = ((cx - dx_i, cy - s_inner + dy_i), (cx, cy - s_inner), (cx + dx_i, cy - s_inner + dy_i), (cx, cy))
        left_dst = ((cx - dx_i, cy + dy_i), (cx - dx_i, cy - s_inner + dy_i), (cx, cy), (cx, cy + s_inner))
        right_dst = ((cx, cy + s_inner), (cx, cy), (cx + dx_i, cy - s_inner + dy_i), (cx + dx_i, cy + dy_i))
        faces = [(top_dst, light_top, top_img), (left_dst, light_left, sides_img), (right_dst, light_right, sides_img)]
    elif view_type == "lower":
        bot_dst = ((cx, cy), (cx + dx_i, cy + s_inner - dy_i), (cx, cy + s_inner), (cx - dx_i, cy + s_inner - dy_i))
        left_dst = ((cx - dx_i, cy + s_inner - dy_i), (cx - dx_i, cy - dy_i), (cx, cy - s_inner), (cx, cy))
        right_dst = ((cx, cy), (cx, cy - s_inner), (cx + dx_i, cy - dy_i), (cx + dx_i, cy + s_inner - dy_i))
        faces = [(bot_dst, light_bot, bottom_img), (left_dst, light_left, sides_img), (right_dst, light_right, sides_img)]
    else:
        raise ValueError(f"Unknown view type {view_type}")

    if pom:
        mask = Image.new("RGBA", (resolution, resolution), (0,0,0,0))
        draw = ImageDraw.Draw(mask)
        if view_type == "upper":
            poly = ((cx, cy-s), (cx+dx, cy-s+dy), (cx+dx, cy+dy), (cx, cy+s), (cx-dx, cy+dy), (cx-dx, cy-s+dy))
        else:
            poly = ((cx, cy-s), (cx+dx, cy-dy), (cx+dx, cy+s-dy), (cx, cy+s), (cx-dx, cy+s-dy), (cx-dx, cy-dy))
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
        face_img = tinted.transform((resolution, resolution), Image.AFFINE, coeffs, resample=Image.BICUBIC)
        mask = Image.new("L", (resolution, resolution), 0)
        draw = ImageDraw.Draw(mask)
        draw.polygon(dst, fill=255)
        face_alpha = face_img.split()[3]
        combined_mask = Image.new("L", (resolution, resolution), 0)
        combined_mask.paste(face_alpha, (0,0), mask)
        out_img.paste(face_img, (0,0), combined_mask)

    out_img.save(output_path)
