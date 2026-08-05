import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

def generate_comparison(workspace_root: Path, block_name: str, v1_name: str, v2_name: str, config: dict) -> bool:
    block_dir = workspace_root / block_name
    v1_dir = block_dir / v1_name
    v2_dir = block_dir / v2_name

    if not v1_dir.exists():
        print(f"Error: Version {v1_name} does not exist for block {block_name}")
        return False

    if not v2_dir.exists():
        print(f"Error: Version {v2_name} does not exist for block {block_name}")
        return False

    comparisons_dir = block_dir / "comparisons"
    comparisons_dir.mkdir(exist_ok=True)

    out_path = comparisons_dir / f"{v1_name}_vs_{v2_name}.png"

    views = ["upper_a", "upper_b", "lower_a", "lower_b"]

    res = config.get("render_resolution", 1024)

    header_height = 100
    total_width = res * 2
    total_height = header_height + (res * 4)

    bg_color = config.get("background", "#101010")

    collage = Image.new("RGBA", (total_width, total_height), bg_color)
    draw = ImageDraw.Draw(collage)

    try:
        font = ImageFont.load_default(size=40)
    except:
        font = ImageFont.load_default()

    draw.text((res // 2, header_height // 2), v1_name, fill="white", font=font, anchor="mm")
    draw.text((res + res // 2, header_height // 2), v2_name, fill="white", font=font, anchor="mm")

    for i, view in enumerate(views):
        y_offset = header_height + (i * res)

        v1_img_path = v1_dir / "preview" / f"{view}.png"
        if v1_img_path.exists():
            img1 = Image.open(v1_img_path)
            collage.paste(img1, (0, y_offset))

        v2_img_path = v2_dir / "preview" / f"{view}.png"
        if v2_img_path.exists():
            img2 = Image.open(v2_img_path)
            collage.paste(img2, (res, y_offset))

        draw.text((res, y_offset + res // 2), view.replace("_", " ").title(), fill="white", font=font, anchor="mm")

    collage.save(out_path)
    print(f"Comparison saved to {out_path}")

    for v_dir in [v1_dir, v2_dir]:
        meta_path = v_dir / "metadata.json"
        if meta_path.exists():
            try:
                with open(meta_path, "r") as f:
                    meta = json.load(f)
                meta["has_comparison"] = True
                with open(meta_path, "w") as f:
                    json.dump(meta, f, indent=2)
            except Exception:
                pass

    return True
