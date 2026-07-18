"""Project-root entry point — run with: python run.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from backend import create_app
from backend.config import PORT

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=True, threaded=True)
