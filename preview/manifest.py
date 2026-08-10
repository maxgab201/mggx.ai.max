import json
from pathlib import Path
from typing import List, Dict, Optional

def parse_manifest(manifest_path: Path) -> tuple[bool, List[Dict[str, Path]], str]:
    """
    Parses a collective JSON manifest and resolves all paths relative to the manifest location.
    Returns: (success, list_of_blocks, error_message)
    """
    try:
        with open(manifest_path, "r") as f:
            data = json.load(f)
    except Exception as e:
        return False, [], f"Failed to read or parse manifest JSON: {str(e)}"

    if "blocks" not in data or not isinstance(data["blocks"], list):
        return False, [], "Manifest must contain a 'blocks' array."

    blocks = []
    parent_dir = manifest_path.parent.resolve()

    for idx, block_data in enumerate(data["blocks"]):
        if "block" not in block_data:
            return False, [], f"Block entry at index {idx} missing 'block' name."

        required_keys = ["top", "bottom", "sides"]
        for key in required_keys:
            if key not in block_data:
                return False, [], f"Block '{block_data['block']}' missing required '{key}' texture."

        # Resolve all paths relative to the manifest
        block_entry = {
            "block": block_data["block"],
            "top": (parent_dir / block_data["top"]).resolve(),
            "bottom": (parent_dir / block_data["bottom"]).resolve(),
            "sides": (parent_dir / block_data["sides"]).resolve(),
        }

        # Optional maps
        if "normal" in block_data:
            block_entry["normal"] = (parent_dir / block_data["normal"]).resolve()
        if "specular" in block_data:
            block_entry["specular"] = (parent_dir / block_data["specular"]).resolve()

        blocks.append(block_entry)

    return True, blocks, ""
