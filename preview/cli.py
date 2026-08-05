import argparse
import sys
import json
import subprocess
from pathlib import Path

from .config import init_config, load_config
from .workspace import (
    create_new_version,
    update_current_dir,
    clean_workspace,
    get_status,
    get_block_dir
)
from .render import render_isometric_block
from .compare import generate_comparison

def get_workspace_root(config: dict) -> Path:
    return Path(config["resolved_workspace"])

def main():
    parser = argparse.ArgumentParser(description="Minecraft Resource Pack Texture Preview CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    init_parser = subparsers.add_parser("init", help="Initialize the preview workspace and configuration")

    render_parser = subparsers.add_parser("render", help="Render a block texture into a new version")
    render_parser.add_argument("--block", required=True, help="Name of the block")
    render_parser.add_argument("--top", required=True, help="Path to the top texture")
    render_parser.add_argument("--bottom", required=True, help="Path to the bottom texture")
    render_parser.add_argument("--sides", required=True, help="Path to the sides texture")

    compare_parser = subparsers.add_parser("compare", help="Compare two versions of a block")
    compare_parser.add_argument("--block", required=True, help="Name of the block")
    compare_parser.add_argument("--from", dest="from_version", required=True, help="Version to compare from (e.g. v0001)")
    compare_parser.add_argument("--to", dest="to_version", required=True, help="Version to compare to (e.g. v0002)")

    open_parser = subparsers.add_parser("open", help="Open the block workspace in the file explorer")
    open_parser.add_argument("--block", required=True, help="Name of the block")

    clean_parser = subparsers.add_parser("clean", help="Clean temporary files and comparisons")
    clean_parser.add_argument("--block", required=True, help="Name of the block")

    status_parser = subparsers.add_parser("status", help="Show workspace status for a block")
    status_parser.add_argument("--block", required=True, help="Name of the block")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "init":
        init_config()
        return

    config = load_config()
    workspace_root = get_workspace_root(config)

    if args.command == "render":
        textures = {
            "top": Path(args.top),
            "bottom": Path(args.bottom),
            "sides": Path(args.sides)
        }

        for name, path in textures.items():
            if not path.exists():
                print(f"Error: {name} texture file not found at {path}")
                sys.exit(1)

        print(f"Rendering new version for block '{args.block}'...")
        version_dir = create_new_version(workspace_root, args.block, textures, config)

        preview_dir = version_dir / "preview"
        views = ["upper", "lower"]

        for view in views:
            out_path = preview_dir / f"{view}.png"
            render_isometric_block(
                textures_dir=version_dir,
                output_path=str(out_path),
                view_type=view,
                resolution=config.get("render_resolution", 1024),
                bg_color=config.get("background", "#101010")
            )
            print(f"  Rendered {view}")

        meta_path = version_dir / "metadata.json"
        with open(meta_path, "r") as f:
            meta = json.load(f)
        meta["render_status"] = "success"
        with open(meta_path, "w") as f:
            json.dump(meta, f, indent=2)

        update_current_dir(workspace_root, args.block, version_dir)
        print(f"Successfully created version {version_dir.name} and updated current/")

    elif args.command == "compare":
        print(f"Comparing {args.from_version} to {args.to_version} for block '{args.block}'...")
        success = generate_comparison(
            workspace_root=workspace_root,
            block_name=args.block,
            v1_name=args.from_version,
            v2_name=args.to_version,
            config=config
        )
        if not success:
            sys.exit(1)

    elif args.command == "open":
        block_dir = get_block_dir(workspace_root, args.block)
        if not block_dir.exists():
            print(f"Error: Block directory not found at {block_dir}")
            sys.exit(1)

        print(f"Opening {block_dir}")
        if sys.platform == "win32":
            subprocess.run(["explorer", str(block_dir)])
        elif sys.platform == "darwin":
            subprocess.run(["open", str(block_dir)])
        else:
            subprocess.run(["xdg-open", str(block_dir)])

    elif args.command == "clean":
        print(f"Cleaning workspace for block '{args.block}'...")
        clean_workspace(workspace_root, args.block)
        print("Cleaned.")

    elif args.command == "status":
        status = get_status(workspace_root, args.block)
        print(json.dumps(status, indent=2))

if __name__ == "__main__":
    main()
