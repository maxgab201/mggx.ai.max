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
from .collective import render_collective_isometric_block

def get_workspace_root(config: dict) -> Path:
    return Path(config["resolved_workspace"])

def _print_output(data: dict, is_json: bool):
    if is_json:
        print(json.dumps(data, indent=2))
    else:
        if "error" in data:
            print(f"Error: {data['error']}")
        else:
            if "message" in data:
                print(data["message"])
            for k, v in data.items():
                if k not in ("status", "message"):
                    print(f"{k.capitalize()}: {v}")

def main():
    parser = argparse.ArgumentParser(
        description="Minecraft Resource Pack Texture Preview CLI",
        epilog="""
Examples:
  preview render --block stone --top stone_top.png --bottom stone_bottom.png --sides stone_side.png
  preview render --block stone --top stone_top.png --bottom stone_bottom.png --sides stone_side.png --pbr
  preview render --block stone --top stone_top.png --bottom stone_bottom.png --sides stone_side.png --pbr --pom
  preview render --collective --block stone --top stone_top.png --bottom stone_bottom.png --sides stone_side.png
  preview render --collective --manifest collective.json
""",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    init_parser = subparsers.add_parser("init", help="Initialize the preview workspace and configuration")

    render_parser = subparsers.add_parser("render", help="Render a block texture into a new version")
    render_parser.add_argument("--block", help="Name of the block (required unless using --manifest)")
    render_parser.add_argument("--top", help="Path to the top texture")
    render_parser.add_argument("--bottom", help="Path to the bottom texture")
    render_parser.add_argument("--sides", help="Path to the sides texture")
    render_parser.add_argument("--pbr", action="store_true", help="Enable PBR visualization")
    render_parser.add_argument("--pom", action="store_true", help="Enable POM visualization")
    render_parser.add_argument("--collective", action="store_true", help="Render multiple blocks or a 3x3 grid")
    render_parser.add_argument("--manifest", help="Path to JSON manifest for collective rendering of multiple blocks")
    render_parser.add_argument("--json", action="store_true", help="Output results as JSON")

    compare_parser = subparsers.add_parser("compare", help="Compare two versions of a block")
    compare_parser.add_argument("--block", required=True, help="Name of the block")
    compare_parser.add_argument("--from", dest="from_version", required=True, help="Version to compare from (e.g. v0001)")
    compare_parser.add_argument("--to", dest="to_version", required=True, help="Version to compare to (e.g. v0002)")
    compare_parser.add_argument("--json", action="store_true", help="Output results as JSON")

    open_parser = subparsers.add_parser("open", help="Open the block workspace in the file explorer")
    open_parser.add_argument("--block", required=True, help="Name of the block")

    clean_parser = subparsers.add_parser("clean", help="Clean temporary files and comparisons")
    clean_parser.add_argument("--block", required=True, help="Name of the block")
    clean_parser.add_argument("--json", action="store_true", help="Output results as JSON")

    status_parser = subparsers.add_parser("status", help="Show workspace status for a block")
    status_parser.add_argument("--block", required=True, help="Name of the block")
    status_parser.add_argument("--json", action="store_true", help="Output results as JSON")

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
        if args.manifest:
            manifest_path = Path(args.manifest)
            if not manifest_path.exists():
                _print_output({"status": "error", "error": f"Manifest file not found: {args.manifest}"}, args.json)
                sys.exit(1)
            # Manifest parsing logic to follow
            _print_output({"status": "error", "error": "Manifest rendering not yet implemented in main loop"}, args.json)
            sys.exit(1)
        else:
            if not args.block or not args.top or not args.bottom or not args.sides:
                _print_output({"status": "error", "error": "--block, --top, --bottom, and --sides are required unless using --manifest"}, args.json)
                sys.exit(1)

            textures = {
                "top": Path(args.top),
                "bottom": Path(args.bottom),
                "sides": Path(args.sides)
            }

            missing = []
            for name, path in textures.items():
                if not path.exists():
                    missing.append(f"{name} texture at {path}")

            if missing:
                _print_output({"status": "error", "error": f"Missing inputs: {', '.join(missing)}"}, args.json)
                sys.exit(1)

            if not args.json:
                print(f"Rendering new version for block '{args.block}'...")

            version_dir = create_new_version(workspace_root, args.block, textures, config, pbr=args.pbr, pom=args.pom, collective=args.collective)

            if version_dir is None:
                 _print_output({"status": "error", "error": "Failed to create version due to missing maps for PBR/POM"}, args.json)
                 sys.exit(1)

            preview_dir = version_dir / "preview"
            views = ["upper", "lower"]

            output_paths = {}
            for view in views:
                # Add suffix logic based on PBR/POM
                suffix = ""
                if args.pbr and args.pom:
                    suffix = "_pbr_pom"
                elif args.pbr:
                    suffix = "_pbr"
                elif args.pom:
                    suffix = "_pom"

                # If collective, put in a 'collective' folder as per spec
                if args.collective:
                    coll_dir = version_dir / "collective"
                    coll_dir.mkdir(exist_ok=True)
                    out_path = coll_dir / f"{view}{suffix}.png"
                    render_collective_isometric_block(
                        textures_dir=version_dir,
                        output_path=str(out_path),
                        view_type=view,
                        resolution=config.get("render_resolution", 1024),
                        bg_color=config.get("background", "#101010"),
                        pbr=args.pbr,
                        pom=args.pom
                    )
                else:
                    out_path = preview_dir / f"{view}{suffix}.png"
                    render_isometric_block(
                        textures_dir=version_dir,
                        output_path=str(out_path),
                        view_type=view,
                        resolution=config.get("render_resolution", 1024),
                        bg_color=config.get("background", "#101010"),
                        pbr=args.pbr,
                        pom=args.pom
                    )
                output_paths[view] = str(out_path)
                if not args.json:
                    print(f"  Rendered {view}")

            meta_path = version_dir / "metadata.json"
            with open(meta_path, "r") as f:
                meta = json.load(f)
            meta["render_status"] = "success"
            with open(meta_path, "w") as f:
                json.dump(meta, f, indent=2)

            update_current_dir(workspace_root, args.block, version_dir)

            _print_output({
                "status": "success",
                "message": f"Successfully created version {version_dir.name} and updated current/",
                "block": args.block,
                "version": version_dir.name,
                "workspace": str(workspace_root),
                "preview": output_paths,
                "pbr": args.pbr,
                "pom": args.pom,
                "collective": args.collective
            }, args.json)

    elif args.command == "compare":
        if not args.json:
            print(f"Comparing {args.from_version} to {args.to_version} for block '{args.block}'...")
        success = generate_comparison(
            workspace_root=workspace_root,
            block_name=args.block,
            v1_name=args.from_version,
            v2_name=args.to_version,
            config=config
        )
        if not success:
            _print_output({"status": "error", "error": "Comparison failed. Check version paths."}, args.json)
            sys.exit(1)
        else:
            comp_path = workspace_root / args.block / "comparisons" / f"{args.from_version}_vs_{args.to_version}.png"
            _print_output({
                "status": "success",
                "message": f"Comparison saved.",
                "comparison_file": str(comp_path)
            }, args.json)

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
        clean_workspace(workspace_root, args.block)
        _print_output({
            "status": "success",
            "message": f"Workspace cleaned for {args.block}."
        }, args.json)

    elif args.command == "status":
        status = get_status(workspace_root, args.block)
        _print_output(status, args.json)

if __name__ == "__main__":
    main()
