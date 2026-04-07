from __future__ import annotations

import os
from pathlib import Path

import uvicorn

from .app import create_app


def main() -> None:
    app = create_app(
        telemetry_api_base_url=os.environ.get("TELEMETRY_API_BASE_URL", "http://127.0.0.1:8080"),
        state_root=(
            Path(os.environ["CONTROL_API_STATE_DIR"])
            if os.environ.get("CONTROL_API_STATE_DIR")
            else None
        ),
    )
    uvicorn.run(app, host="127.0.0.1", port=int(os.environ.get("CONTROL_API_PORT", "8090")))


if __name__ == "__main__":
    main()
