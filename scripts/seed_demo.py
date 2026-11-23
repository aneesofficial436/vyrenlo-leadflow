"""Wrapper — run the API seed script from the leadflow repo root."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

API_DIR = Path(__file__).resolve().parents[1] / "apps" / "api"
script = API_DIR / "scripts" / "seed_demo.py"
raise SystemExit(subprocess.call([sys.executable, str(script)], cwd=str(API_DIR)))