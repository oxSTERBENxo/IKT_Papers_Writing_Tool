import os
import sys
from pathlib import Path

os.environ["STARRY_BACKEND"] = "tfidf"  # deterministic, no model download
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
