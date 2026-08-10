import os
import json
import shutil
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

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

def find_auxiliary_maps(base_path: Path, pbr: bool, pom: bool, explicit_normal=None, explicit_specular=None) -> dict:
    """Finds associated PBR (_s for specular/roughness) and POM (_n for normal/height) maps."""
    found = {}
    base_name = base_path.stem
    parent = base_path.parent

    if pbr:
        if explicit_specular and explicit_specular.exists():
             found["s"] = explicit_specular
        else:
             s_map = parent / f"{base_name}_s.png"
             if s_map.exists():
                 found["s"] = s_map
             else:
                 return None

    if pom or pbr:
        if explicit_normal and explicit_normal.exists():
             found["n"] = explicit_normal
        else:
             n_map = parent / f"{base_name}_n.png"
             if n_map.exists():
                 found["n"] = n_map
             elif pom:
                 return None

    return found

def create_new_version(workspace_root: Path, primary_block_name: str, multi_blocks: List[Dict[str, Path]], config: dict, pbr: bool = False, pom: bool = False, collective: bool = False, is_manifest: bool = False) -> Optional[Path]:
    block_dir = get_block_dir(workspace_root, primary_block_name)
    block_dir.mkdir(parents=True, exist_ok=True)

    version_name = get_next_version_name(workspace_root, primary_block_name)
    version_dir = block_dir / version_name

    # Validation step
    aux_maps_per_block = []
    for b in multi_blocks:
        aux_maps = {}
        for face in ["top", "bottom", "sides"]:
            if pbr or pom:
                exp_n = b.get("normal")
                exp_s = b.get("specular")
                aux = find_auxiliary_maps(b[face], pbr, pom, explicit_normal=exp_n, explicit_specular=exp_s)
                if aux is None:
                    return None
                aux_maps[face] = aux
            else:
                aux_maps[face] = {}
        aux_maps_per_block.append(aux_maps)

    version_dir.mkdir(exist_ok=True)
    preview_dir = version_dir / "preview"
    preview_dir.mkdir(exist_ok=True)

    inputs_meta = []

    from PIL import Image

    for idx, b in enumerate(multi_blocks):
        b_name = b["block"]
        b_meta = {
            "block": b_name,
            "paths": {},
            "hashes": {},
            "dimensions": {}
        }

        # We store copies namespaced by the block name if there are multiple blocks
        prefix = f"{b_name}_" if len(multi_blocks) > 1 else ""

        for face in ["top", "bottom", "sides"]:
            source_path = b[face]
            dest_path = version_dir / f"{prefix}{face}.png"
            shutil.copy2(source_path, dest_path)

            b_meta["paths"][face] = str(source_path)
            b_meta["hashes"][face] = calculate_hash(dest_path)
            try:
                with Image.open(dest_path) as img:
                    b_meta["dimensions"][face] = list(img.size)
            except Exception:
                b_meta["dimensions"][face] = [0, 0]

            # Copy aux maps
            for aux_type, aux_path in aux_maps_per_block[idx][face].items():
                dest_aux = version_dir / f"{prefix}{face}_{aux_type}.png"
                shutil.copy2(aux_path, dest_aux)
                b_meta["paths"][f"{face}_{aux_type}"] = str(aux_path)
                b_meta["hashes"][f"{face}_{aux_type}"] = calculate_hash(dest_aux)

        inputs_meta.append(b_meta)

    metadata = {
        "block": primary_block_name,
        "version": version_name,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "status": "candidate",
        "render_mode": "collective" if collective else "single",
        "is_manifest": is_manifest,
        "pbr": pbr,
        "pom": pom,
        "views": ["upper", "lower"],
        "inputs": inputs_meta,
        "render_status": "pending",
        "renderer": "pillow_isometric_v4",
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

    block_dir = get_block_dir(workspace_root, block_name)
    if block_dir.exists():
        for item in block_dir.iterdir():
            if item.is_file():
                item.unlink()

def get_status(workspace_root: Path, block_name: str) -> dict:
    versions = get_versions_dirs(workspace_root, block_name)
    current_dir = get_current_dir(workspace_root, block_name)

    status = {
        "status": "success",
        "block": block_name,
        "total_versions": len(versions),
        "versions": [v.name for v in versions],
        "has_current": current_dir.exists(),
        "latest_version": versions[-1].name if versions else None,
        "workspace": str(get_block_dir(workspace_root, block_name))
    }

    if current_dir.exists():
        meta_path = current_dir / "metadata.json"
        if meta_path.exists():
            with open(meta_path, "r") as f:
                meta = json.load(f)
                status["current_version_name"] = meta.get("version")

    return status
