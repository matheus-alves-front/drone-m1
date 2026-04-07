from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys

from fastapi import FastAPI


def _load_canonical_create_app():
    package_root = Path(__file__).resolve().parents[2] / "telemetry_api"
    package_name = "telemetry_api_canonical"

    package_spec = spec_from_file_location(
        package_name,
        package_root / "__init__.py",
        submodule_search_locations=[str(package_root)],
    )
    if package_spec is None or package_spec.loader is None:
        raise RuntimeError(f"unable to load canonical telemetry api package from {package_root}")

    if package_name not in sys.modules:
        package_module = module_from_spec(package_spec)
        sys.modules[package_name] = package_module
        package_spec.loader.exec_module(package_module)

    app_spec = spec_from_file_location(f"{package_name}.app", package_root / "app.py")
    if app_spec is None or app_spec.loader is None:
        raise RuntimeError(f"unable to load canonical telemetry api app from {package_root / 'app.py'}")
    app_module = module_from_spec(app_spec)
    sys.modules[f"{package_name}.app"] = app_module
    app_spec.loader.exec_module(app_module)
    return app_module.create_app


def create_app(*, storage_root: str | Path | None = None) -> FastAPI:
    canonical_create_app = _load_canonical_create_app()
    return canonical_create_app(storage_root=Path(storage_root).resolve() if storage_root is not None else None)


app = create_app()
