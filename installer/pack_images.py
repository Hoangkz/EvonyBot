"""pack_images.py <Images dir> <images.dat> — pack Images/ for the installer (see bot/context/image_store.py)."""
import importlib.util
import sys
from pathlib import Path

store_file = Path(__file__).resolve().parent.parent / "bot" / "context" / "image_store.py"
spec = importlib.util.spec_from_file_location("image_store", store_file)
store = importlib.util.module_from_spec(spec)
spec.loader.exec_module(store)

count = store.pack(Path(sys.argv[1]), Path(sys.argv[2]))
print(f"Packed {count} images -> {sys.argv[2]}")
