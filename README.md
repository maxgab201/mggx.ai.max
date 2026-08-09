# mc-preview

A standalone CLI for generating local, versioned, and comparable 3D previews of Minecraft block textures.

This tool acts as a deterministic infrastructure pipeline—ideal for Claude Code and automated visual QA testing. It is strictly for visual inspection and does **not** handle asset generation, PBR generation, or heavy rendering.

## Features

- **No Heavy Native Dependencies**: Uses lightweight isometric software rendering via Python's `Pillow`. No WebGL, Blender, OptiFine, or GPU required.
- **Deterministic Two-View Logic**: Generates strictly 2 perspectives (`upper` and `lower`) keeping QA simple and fully comparable.
- **Strict Face Mapping**: Enforces assigning independent textures to `--top`, `--bottom`, and `--sides` to prevent duplicate mappings across faces.
- **PBR & POM Visualization**: Given existing `_s` and `_n` maps associated with the textures, `--pbr` visually simulates specular shading and normal mapped highlights, while `--pom` simulates a parallax void for height displacement approximation.
- **Collective Mode**: A `--collective` flag generates a deterministic 3x3 array layout of the block specifically designed for checking tiling, repetition seams, and rhythmic correctness.
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

### 2. PBR Visualization
If your material possesses roughness/specular (`_s`) or normal (`_n`) maps next to your inputs, this simulates physical based highlights.
```powershell
python -m preview.cli render --block stone --top "stone_top.png" --bottom "stone_bottom.png" --sides "stone_side.png" --pbr
```

### 3. POM Visualization
Combines depth voiding approximations to test POM extrusions and seams.
```powershell
python -m preview.cli render --block stone --top "stone_top.png" --bottom "stone_bottom.png" --sides "stone_side.png" --pbr --pom
```

### 4. Collective Array Rendering
Checks tiling by populating a 3x3 repeating structural grid format.
```powershell
python -m preview.cli render --collective --block stone --top "stone_top.png" --bottom "stone_bottom.png" --sides "stone_side.png"
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

## Architecture Map

- `preview/cli.py`: Core CLI router.
- `preview/workspace.py`: Versioning/IO engine logic mapping inputs and copying resources.
- `preview/render.py`: Math-based isometric projection scaling textures to specific cube faces with PBR logic.
- `preview/collective.py`: Sub-renderer specifically for overlapping Z-space mapping across a 3x3 block array logic.
- `preview/compare.py`: Pillow collage construction logic.
