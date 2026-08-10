import pytest
import os
import json
from pathlib import Path
import subprocess
from PIL import Image

def test_manifest_collective_rendering():
    # Setup multiple dummy blocks in a temp manifest
    Image.new('RGBA', (16,16), 'red').save('chk_m1_top.png')
    Image.new('RGBA', (16,16), 'red').save('chk_m1_bot.png')
    Image.new('RGBA', (16,16), 'red').save('chk_m1_sides.png')

    Image.new('RGBA', (16,16), 'blue').save('chk_m2_top.png')
    Image.new('RGBA', (16,16), 'blue').save('chk_m2_bot.png')
    Image.new('RGBA', (16,16), 'blue').save('chk_m2_sides.png')

    manifest_data = {
        "blocks": [
            {
                "block": "red_block",
                "top": "chk_m1_top.png",
                "bottom": "chk_m1_bot.png",
                "sides": "chk_m1_sides.png"
            },
            {
                "block": "blue_block",
                "top": "chk_m2_top.png",
                "bottom": "chk_m2_bot.png",
                "sides": "chk_m2_sides.png"
            }
        ]
    }

    manifest_path = Path("test_manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest_data, f)

    result = subprocess.run([
        "python", "-m", "preview.cli", "render", "--collective", "--manifest", str(manifest_path)
    ], capture_output=True, text=True)

    assert result.returncode == 0

    output_path = Path("workspace/collective_manifest/current/collective/upper.png")
    assert output_path.exists()

    # Optional metadata inspection
    meta_path = Path("workspace/collective_manifest/current/metadata.json")
    assert meta_path.exists()
    with open(meta_path, "r") as f:
        meta = json.load(f)
    assert meta["is_manifest"] is True
    assert len(meta["inputs"]) == 2

def test_manifest_missing_file():
    manifest_data = {
        "blocks": [
            {
                "block": "red_block",
                "top": "chk_MISSING.png",
                "bottom": "chk_m1_bot.png",
                "sides": "chk_m1_sides.png"
            }
        ]
    }
    manifest_path = Path("test_manifest_missing.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest_data, f)

    result = subprocess.run([
        "python", "-m", "preview.cli", "render", "--collective", "--manifest", str(manifest_path)
    ], capture_output=True, text=True)

    assert result.returncode == 1
    assert "Missing files in manifest" in result.stdout
