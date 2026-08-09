import pytest
from PIL import Image, ImageDraw
import os
from pathlib import Path
import subprocess

def test_face_color_correctness():
    # We will generate a red top, a blue bottom, and a green side
    # Then render, and check center pixels of where the faces roughly map.
    Image.new('RGBA', (64,64), (255, 0, 0, 255)).save('chk_top.png')
    Image.new('RGBA', (64,64), (0, 0, 255, 255)).save('chk_bot.png')
    Image.new('RGBA', (64,64), (0, 255, 0, 255)).save('chk_sides.png')

    # We enforce a clean resolution so coords are exact
    with open('preview.config.json', 'w') as f:
        f.write('{"workspace": "./workspace", "background": "#101010", "render_resolution": 512}')

    subprocess.run([
        "python", "-m", "preview.cli", "render", "--block", "test_colors",
        "--top", "chk_top.png", "--bottom", "chk_bot.png", "--sides", "chk_sides.png"
    ])

    # Check upper view
    upper_path = Path("workspace/test_colors/current/preview/upper.png")
    assert upper_path.exists()
    u_img = Image.open(upper_path)

    # Center is 256, 256.
    # For Upper:
    # Top face is roughly above center: (256, 200)
    top_color = u_img.getpixel((256, 200))
    # It might be tinted by light_top=1.0. It should be red.
    assert top_color[0] > 200 and top_color[1] == 0 and top_color[2] == 0

    # Left side is down-left: (200, 300)
    left_color = u_img.getpixel((200, 300))
    # Green, tinted to 0.8
    assert left_color[0] == 0 and left_color[1] > 150 and left_color[2] == 0

    # Right side is down-right: (312, 300)
    right_color = u_img.getpixel((312, 300))
    # Green, tinted to 0.6
    assert right_color[0] == 0 and right_color[1] > 100 and right_color[2] == 0

    # Check lower view
    lower_path = Path("workspace/test_colors/current/preview/lower.png")
    assert lower_path.exists()
    l_img = Image.open(lower_path)

    # Bottom face is exactly at (256, 300)
    bot_color = l_img.getpixel((256, 300))
    # Blue, tinted to 0.5
    assert bot_color[0] == 0 and bot_color[1] == 0 and bot_color[2] > 100

    # Left side is up-left: (200, 200)
    l_left_color = l_img.getpixel((200, 200))
    # Green, tinted to 0.8
    assert l_left_color[0] == 0 and l_left_color[1] > 150 and l_left_color[2] == 0
