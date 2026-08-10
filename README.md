# mc-preview

A standalone CLI for generating local, versioned, and comparable 3D previews of Minecraft block textures.

This tool acts as a deterministic infrastructure pipeline—ideal for Claude Code and automated visual QA testing. It is strictly for visual inspection and does **not** handle asset generation, PBR generation, or heavy rendering.

## Target Environment Constraints
- Minecraft Java Edition 1.21+
- Fabric Loader & Iris Shaders
- **NO Optifine.**

## Features

- **No Heavy Native Dependencies**: Uses lightweight isometric software rendering via Python's `Pillow`. No WebGL, Blender, OptiFine, or GPU required.
- **Deterministic Two-View Logic**: Generates strictly 2 perspectives (`upper` and `lower`) keeping QA simple and fully comparable.
- **Strict Face Mapping**: Enforces assigning independent textures to `--top`, `--bottom`, and `--sides` to prevent duplicate mappings across faces.
- **PBR & POM Visualization**: Given existing maps associated with the textures, `--pbr` visually simulates specular shading and normal mapped highlights, while `--pom` simulates a parallax void for height displacement approximation.
- **Collective Mode & Manifests**: A `--collective` flag generates a deterministic 3x3 array layout of the block. Support for passing a JSON `--manifest` allows rendering distinct *multiple materials* within this grid to verify seamless tiling and block-to-block rhythmic correctness.
- **Automated Versioning**: Successive renders do not override history. A `vXXXX` directory handles incremental changes alongside a convenient physical `current/` alias folder mapping to the latest approved preview.
- **JSON Stdout Compatibility**: Support for a `--json` parameter to easily pass structured parsing context into pipelines or LLM wrappers.

## Installation

This requires **Python 3.9+** and `Pillow`. This functions gracefully inside typical Windows/macOS/Linux systems including WSL and PowerShell.

```powershell
git clone <repository>
cd mc-preview
python -m pip install .
```

## Setup Config

Launch workspace layout and initialization settings with defaults.
```powershell
python -m preview.cli init
```

*(This constructs a `preview.config.json` that roots workspace outputs relative to the json configuration file, guaranteeing portability).*

## Examples & Usage

### 1. Single Block Preview
Generates an upper and lower view of a basic block material.
```powershell
python -m preview.cli render --block grass_block --top "textures\grass_top.png" --bottom "textures\dirt.png" --sides "textures\grass_side.png"
```

### 2. PBR / POM Visualization
If your material possesses roughness/specular (`_s`) or normal (`_n`) maps next to your inputs, this simulates physical based highlights.
```powershell
python -m preview.cli render --block stone --top "stone_top.png" --bottom "stone_bottom.png" --sides "stone_side.png" --pbr --pom
```

### 3. Collective Array Rendering
Checks tiling by populating a 3x3 repeating structural grid format with a single material.
```powershell
python -m preview.cli render --collective --block stone --top "stone_top.png" --bottom "stone_bottom.png" --sides "stone_side.png"
```

### 4. Collective Rendering via Manifest (Multi-Block)
Allows checking multiple completely distinct materials tiled next to one another in the grid.
Provide a manifest JSON file containing paths:
```json
{
  "blocks": [
    {
      "block": "stone",
      "top": "textures/stone_top.png",
      "bottom": "textures/stone_bottom.png",
      "sides": "textures/stone_side.png"
    },
    {
      "block": "dirt",
      "top": "textures/dirt.png",
      "bottom": "textures/dirt.png",
      "sides": "textures/dirt.png"
    }
  ]
}
```
Run using:
```powershell
python -m preview.cli render --collective --manifest collective.json --pbr
```

## Management Commands

### Status
Get tracking states of history. Use `--json` for machine readability.
```powershell
python -m preview.cli status --block stone
```

### Compare
Puts two historical iterations side-by-side on an image grid for easy visual review.
```powershell
python -m preview.cli compare --block stone --from v0001 --to v0002
```

### Open
Opens your native file explorer exactly to the workspace location containing your `current` and versioned iterations.
```powershell
python -m preview.cli open --block stone
```

### Clean
Purges temporary collages or loose cached artifacts without touching version iterations.
```powershell
python -m preview.cli clean --block stone
```
