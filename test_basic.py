import pytest
import os
from pathlib import Path
from preview.config import DEFAULT_CONFIG

def test_config_import():
    import preview.config
    assert preview.config.DEFAULT_CONFIG_FILE == "preview.config.json"

def test_workspace_names():
    from preview.workspace import get_next_version_name
    assert callable(get_next_version_name)

def test_render_math():
    from preview.render import get_affine_coeffs
    src = ((0,0), (1,0), (1,1))
    dst = ((1,1), (2,1), (2,2))
    coeffs = get_affine_coeffs(src, dst)
    a, b, c, d, e, f = coeffs
    assert abs((a*1 + b*1 + c) - 0) < 1e-6
    assert abs((d*1 + e*1 + f) - 0) < 1e-6
