import json
import os
from pathlib import Path

DEFAULT_CONFIG_FILE = "preview.config.json"

DEFAULT_CONFIG = {
    "workspace": "./workspace",
    "background": "#101010",
    "render_resolution": 1024
}

def get_config_path() -> Path:
    """Gets the path to the config file, searching upwards or defaulting to current dir."""
    return Path(DEFAULT_CONFIG_FILE).resolve()

def init_config(config_path: Path = None) -> None:
    if config_path is None:
        config_path = get_config_path()

    if config_path.exists():
        print(f"Config file already exists at {config_path}")
        return

    with open(config_path, "w") as f:
        json.dump(DEFAULT_CONFIG, f, indent=2)
    print(f"Created default config at {config_path}")

def load_config(config_path: Path = None) -> dict:
    if config_path is None:
        config_path = get_config_path()

    if not config_path.exists():
        print(f"Warning: {config_path} not found. Using default config.")
        return DEFAULT_CONFIG

    with open(config_path, "r") as f:
        config = json.load(f)

    # Resolve workspace path relative to config file location
    workspace_path = config.get("workspace", DEFAULT_CONFIG["workspace"])
    config["resolved_workspace"] = str((config_path.parent / workspace_path).resolve())

    return config
