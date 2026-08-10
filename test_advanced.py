import pytest
from PIL import Image
import subprocess
from pathlib import Path

def test_pbr_pom_failure_missing_maps():
    # Trying to render PBR without maps should fail.
    Image.new('RGBA', (16,16), 'red').save('test2_top.png')
    Image.new('RGBA', (16,16), 'blue').save('test2_bottom.png')
    Image.new('RGBA', (16,16), 'green').save('test2_sides.png')

    result = subprocess.run([
        "python", "-m", "preview.cli", "render", "--block", "test2_missing",
        "--top", "test2_top.png", "--bottom", "test2_bottom.png", "--sides", "test2_sides.png",
        "--pbr"
    ], capture_output=True, text=True)

    # We should see the error in the stdout
    assert result.returncode == 1
    assert "Failed to create version due to missing maps for PBR/POM" in result.stdout

def test_successful_render():
    Image.new('RGBA', (16,16), 'red').save('test_top.png')
    Image.new('RGBA', (16,16), 'blue').save('test_bottom.png')
    Image.new('RGBA', (16,16), 'green').save('test_sides.png')

    # Also create fake S and N maps
    Image.new('RGBA', (16,16), 'grey').save('test_top_s.png')
    Image.new('RGBA', (16,16), 'grey').save('test_top_n.png')
    Image.new('RGBA', (16,16), 'grey').save('test_bottom_s.png')
    Image.new('RGBA', (16,16), 'grey').save('test_bottom_n.png')
    Image.new('RGBA', (16,16), 'grey').save('test_sides_s.png')
    Image.new('RGBA', (16,16), 'grey').save('test_sides_n.png')

    result = subprocess.run([
        "python", "-m", "preview.cli", "render", "--block", "test_success",
        "--top", "test_top.png", "--bottom", "test_bottom.png", "--sides", "test_sides.png",
        "--pbr", "--pom"
    ], capture_output=True, text=True)

    assert result.returncode == 0
    p = Path("workspace/test_success/current/preview/upper_pbr_pom.png")
    assert p.exists()

def test_collective_render():
    result = subprocess.run([
        "python", "-m", "preview.cli", "render", "--block", "test_coll",
        "--top", "test_top.png", "--bottom", "test_bottom.png", "--sides", "test_sides.png",
        "--collective"
    ], capture_output=True, text=True)
    assert result.returncode == 0
    p = Path("workspace/test_coll/current/collective/upper.png")
    assert p.exists()
