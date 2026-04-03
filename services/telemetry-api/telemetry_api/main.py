from __future__ import annotations

import os
from pathlib import Path

import uvicorn

from .app import create_app


def main() -> None:
    data_root = Path(os.environ.get("TELEMETRY_API_DATA_ROOT", Path(__file__).resolve().parents[1] / "data"))
    app = create_app(data_root)
    uvicorn.run(app, host="127.0.0.1", port=int(os.environ.get("TELEMETRY_API_PORT", "8080")))


if __name__ == "__main__":
    main()
