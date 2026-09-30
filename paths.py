from __future__ import annotations

import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any


APP_ID = "SimpleHVACKE"
PACKAGE_ROOT = Path(__file__).resolve().parent.parent
RESOURCE_ROOT = PACKAGE_ROOT / "scada_app" / "resources"


def app_data_dir() -> Path:
    override = os.environ.get("SIMPLE_HVAC_DATA_DIR")
    if override:
        root = Path(override).expanduser()
    elif os.name == "nt":
        root = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / APP_ID
    else:
        root = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")) / APP_ID
    root.mkdir(parents=True, exist_ok=True)
    return root


def resource_path(*parts: str) -> Path:
    return RESOURCE_ROOT.joinpath(*parts)


def data_path(*parts: str) -> Path:
    path = app_data_dir().joinpath(*parts)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def ensure_user_file(relative: str, default_relative: str | None = None) -> Path:
    target = data_path(relative)
    if not target.exists() and default_relative:
        source = resource_path(default_relative)
        if source.is_file():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
    return target


def atomic_write_text(path: Path, text: str, encoding: str = "utf-8") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    candidate: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding=encoding, dir=path.parent, prefix=f".{path.name}-",
            suffix=".tmp", delete=False,
        ) as stream:
            candidate = Path(stream.name)
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        candidate.replace(path)
    finally:
        if candidate is not None:
            candidate.unlink(missing_ok=True)


def atomic_write_json(path: Path, value: Any) -> None:
    atomic_write_text(path, json.dumps(value, ensure_ascii=False, indent=2))
