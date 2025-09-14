import importlib.util, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MOD_PATH = ROOT / "generated_module.py"

def _load_module(path: Path, name: str = "generated_module"):
    spec = importlib.util.spec_from_file_location(name, str(path))
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod

def test_handler_ok():
    assert MOD_PATH.exists(), f"missing: {MOD_PATH}"
    mod = _load_module(MOD_PATH)
    assert hasattr(mod, "handler")
    out = mod.handler()
    assert isinstance(out, str)
    assert out in ("OK", "ok", "hi from botfarm")
