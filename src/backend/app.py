"""Entry point — run with: python app.py  (or via flask/gunicorn)."""
import sys
from pathlib import Path

# Ensure the 'src/' directory is on the path so 'backend' is importable
# regardless of where the script is invoked from.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend import create_app
from backend.config import PORT

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=True, threaded=True)
