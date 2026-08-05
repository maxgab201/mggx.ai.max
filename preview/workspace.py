import os
import json
import shutil
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict

def get_block_dir(workspace_root: Path, block_name: str) -> Path:
    return workspace_root / block_name

def get_current_dir(workspace_root: Path, block_name: str) -> Path:
    return get_block_dir(workspace_root, block_name) / "current"

def get_comparisons_dir(workspace_root: Path, block_name: str) -> Path:
    return get_block_dir(workspace_root, block_name) / "comparisons"

def get_versions_dirs(workspace_root: Path, block_name: str) -> list[Path]:
    block_dir = get_block_dir(workspace_root, block_name)
    if not block_dir.exists():
        return []
    versions = []
    for entry in block_dir.iterdir():
        if entry.is_dir() and entry.name.startswith("v") and entry.name[1:].isdigit():
            versions.append(entry)
    versions.sort(key=lambda x: int(x.name[1:]))
    return versions

def get_next_version_name(workspace_root: Path, block_name: str) -> str:
    versions = get_versions_dirs(workspace_root, block_name)
    if not versions:
        return "v0001"
    last_version = versions[-1].name
    next_num = int(last_version[1:]) + 1
    return f"v{next_num:04d}"

def calculate_hash(file_path: Path) -> str:
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def create_new_version(workspace_root: Path, block_name: str, textures: Dict[str, Path], config: dict) -> Path:
    block_dir = get_block_dir(workspace_root, block_name)
    block_dir.mkdir(parents=True, exist_ok=True)

    version_name = get_next_version_name(workspace_root, block_name)
    version_dir = block_dir / version_name
    version_dir.mkdir(exist_ok=True)

    preview_dir = version_dir / "preview"
    preview_dir.mkdir(exist_ok=True)

    input_hashes = {}
    texture_dimensions = {}

    from PIL import Image

    for name, source_path in textures.items():
        dest_path = version_dir / f"{name}.png"
        shutil.copy2(source_path, dest_path)
        input_hashes[name] = calculate_hash(dest_path)

        try:
            with Image.open(dest_path) as img:
                texture_dimensions[name] = list(img.size)
        except Exception:
            texture_dimensions[name] = [0, 0]

    metadata = {
        "block_name": block_name,
        "version": version_name,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "inputs": {
            "top": str(textures["top"]),
            "bottom": str(textures["bottom"]),
            "sides": str(textures["sides"])
        },
        "input_hashes": input_hashes,
        "texture_dimensions": texture_dimensions,
        "render_status": "pending",
        "engine": "pillow_isometric_v2",
        "camera_parameters": "fixed_isometric_2_views",
        "lighting_parameters": "fixed_tinting",
        "has_comparison": False
    }

    metadata_path = version_dir / "metadata.json"
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

    return version_dir

def update_current_dir(workspace_root: Path, block_name: str, version_dir: Path):
    current_dir = get_current_dir(workspace_root, block_name)
    if current_dir.exists():
        shutil.rmtree(current_dir)

    shutil.copytree(version_dir, current_dir)

def clean_workspace(workspace_root: Path, block_name: str):
    comparisons_dir = get_comparisons_dir(workspace_root, block_name)
    if comparisons_dir.exists():
        shutil.rmtree(comparisons_dir)
        print(f"Removed {comparisons_dir}")

    block_dir = get_block_dir(workspace_root, block_name)
    if block_dir.exists():
        for item in block_dir.iterdir():
            if item.is_file():
                item.unlink()
                print(f"Removed orphan file {item}")

def get_status(workspace_root: Path, block_name: str) -> dict:
    versions = get_versions_dirs(workspace_root, block_name)
    current_dir = get_current_dir(workspace_root, block_name)

    status = {
        "block": block_name,
        "total_versions": len(versions),
        "versions": [v.name for v in versions],
        "has_current": current_dir.exists(),
        "latest_version": versions[-1].name if versions else None,
    }

    if current_dir.exists():
        meta_path = current_dir / "metadata.json"
        if meta_path.exists():
            with open(meta_path, "r") as f:
                meta = json.load(f)
                status["current_version_name"] = meta.get("version")

    return status
