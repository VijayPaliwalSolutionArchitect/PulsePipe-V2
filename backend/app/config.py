"""Runtime configuration for PulsePipe.

All values are read from environment variables (an optional ``.env`` file is
loaded if present) and fall back to sensible defaults suited to local
development.  Everything here is overridable at deploy time so the same image
can back dev, staging and production.
"""

from __future__ import annotations

import os
from pathlib import Path

# Project root is backend/app -> backend -> project root.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = Path(__file__).resolve().parents[1]


def _load_dotenv() -> None:
    """Best-effort load of a ``.env`` file if appdirs' dotenv exists.

    We deliberately avoid a hard dependency: if python-dotenv is not
    installed we simply read the process environment.
    """
    dotenv_path = BACKEND_DIR / ".env"
    if not dotenv_path.is_file():
        return
    for line in dotenv_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


_load_dotenv()


def _as_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


class Settings:
    """Typed accessor over environment variables."""

    def __init__(self) -> None:
        self.app_name: str = os.environ.get("PULSEPIPE_NAME", "PulsePipe")
        self.version: str = os.environ.get("PULSEPIPE_VERSION", "1.0.0")
        self.host: str = os.environ.get("PULSEPIPE_HOST", "0.0.0.0")
        self.port: int = int(os.environ.get("PULSEPIPE_PORT", "8000"))
        self.debug: bool = _as_bool("PULSEPIPE_DEBUG", False)

        # Database file; default to the project's data/ directory so the
        # seeded SQLite DB is easy to find and inspect.
        db_env = os.environ.get("PULSEPIPE_DB_PATH")
        self.database_path: Path = (
            Path(db_env) if db_env else PROJECT_ROOT / "data" / "pulsepipe.db"
        )
        self.database_path.parent.mkdir(parents=True, exist_ok=True)

        # Seed sample pipelines / events / rules on first boot.
        self.seed_on_start: bool = _as_bool("PULSEPIPE_SEED_ON_START", True)

        # How subscribed endpoints receive emitted events.
        #   sync : emit inline within the ingest request (deterministic).
        #   async: emit on a background worker thread (non-blocking ingest).
        self.dispatch_mode: str = os.environ.get(
            "PULSEPIPE_DISPATCH_MODE", "sync"
        )
        # Seconds to wait for a subscriber to accept an event before moving on.
        self.dispatch_timeout: float = float(
            os.environ.get("PULSEPIPE_DISPATCH_TIMEOUT", "2.0")
        )

        # Dashboard serves the pre-built frontend from the project frontend/.
        self.frontend_dir: Path = PROJECT_ROOT / "frontend"

    @property
    def is_async_dispatch(self) -> bool:
        """True when emission should happen off the request thread."""
        return self.dispatch_mode.lower() in {"async", "background"}


settings = Settings()