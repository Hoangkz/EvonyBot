"""
image_store.py — Images/ packed into one scrambled file (images.dat) for the installed build.

The installer does not ship the Images/ folder; build packs it into images.dat. At run time
`PackedDir` stands in for the Images/ Path: same `/`, exists(), is_dir(), glob(), parent, name, stem,
read_bytes() the code already uses, served from memory. From source (no images.dat) the real folder is used.

Standard library only: installer/pack_images.py loads this file on its own to build images.dat.
"""
import hashlib
import json
import os
import struct
from fnmatch import fnmatchcase
from pathlib import Path, PurePosixPath

_MAGIC = b"EVIMG1"
_KEY = b"\x5a\xc3\x19\xe7EvonyBot-images\x8d\x42\xb0\x71"
_NONCE_SIZE = 16


def _xor(data: bytes, nonce: bytes) -> bytes:
    stream = hashlib.shake_256(_KEY + nonce).digest(len(data))
    return (int.from_bytes(data, "little") ^ int.from_bytes(stream, "little")).to_bytes(len(data), "little")


def pack(source: Path, target: Path, skip: tuple[str, ...] = ("test",)) -> int:
    """Write every file under `source` (except top-level folders in `skip`) to `target`. Returns file count."""
    index, chunks, offset = {}, [], 0
    for path in sorted(p for p in Path(source).rglob("*") if p.is_file()):
        rel = path.relative_to(source).as_posix()
        if rel.split("/")[0] in skip:
            continue
        data = path.read_bytes()
        index[rel] = (offset, len(data))
        chunks.append(data)
        offset += len(data)
    header = json.dumps(index, separators=(",", ":")).encode()
    body = struct.pack("<I", len(header)) + header + b"".join(chunks)
    nonce = os.urandom(_NONCE_SIZE)
    Path(target).write_bytes(_MAGIC + nonce + _xor(body, nonce))
    return len(index)


class _Store:
    def __init__(self, dat: Path):
        raw = Path(dat).read_bytes()
        if raw[:len(_MAGIC)] != _MAGIC:
            raise ValueError(f"{dat} is not an image pack")
        nonce = raw[len(_MAGIC):len(_MAGIC) + _NONCE_SIZE]
        body = _xor(raw[len(_MAGIC) + _NONCE_SIZE:], nonce)
        size = struct.unpack("<I", body[:4])[0]
        self.files = {k: tuple(v) for k, v in json.loads(body[4:4 + size]).items()}
        self.data = memoryview(body)[4 + size:]
        self.dirs = {""}
        for rel in self.files:
            parts = PurePosixPath(rel).parts
            self.dirs.update("/".join(parts[:i]) for i in range(1, len(parts)))


class PackedDir:
    """A file or folder inside the pack, addressed like a Path."""

    def __init__(self, store: _Store, rel: str = ""):
        self._store = store
        self._rel = rel

    def __truediv__(self, other):
        other = str(other).replace("\\", "/")
        if Path(other).is_absolute():          # a real file (e.g. learned images) overrides the pack
            return Path(other)
        rel = PurePosixPath(self._rel, other).as_posix().strip("/")
        return PackedDir(self._store, "" if rel == "." else rel)

    def exists(self) -> bool:
        return self.is_file() or self.is_dir()

    def is_file(self) -> bool:
        return self._rel in self._store.files

    def is_dir(self) -> bool:
        return self._rel in self._store.dirs

    def read_bytes(self) -> bytes:
        if not self.is_file():
            raise FileNotFoundError(str(self))
        start, size = self._store.files[self._rel]
        return bytes(self._store.data[start:start + size])

    def glob(self, pattern: str):
        """Direct match of a relative pattern like "*.png" or "*/Done.png" (no "**")."""
        want = pattern.split("/")
        base = self._rel.split("/") if self._rel else []
        found = set()
        for rel in (*self._store.files, *self._store.dirs):
            if not rel:
                continue
            parts = rel.split("/")
            if len(parts) != len(base) + len(want) or parts[:len(base)] != base:
                continue
            if all(fnmatchcase(p, w) for p, w in zip(parts[len(base):], want)):
                found.add(rel)
        return [PackedDir(self._store, rel) for rel in sorted(found)]

    @property
    def name(self) -> str:
        return PurePosixPath(self._rel).name

    @property
    def stem(self) -> str:
        return PurePosixPath(self._rel).stem

    @property
    def parent(self) -> "PackedDir":
        parent = PurePosixPath(self._rel).parent.as_posix()
        return PackedDir(self._store, "" if parent == "." else parent)

    def __lt__(self, other):
        return self._rel < other._rel

    def __eq__(self, other):
        return isinstance(other, PackedDir) and other._store is self._store and other._rel == self._rel

    def __hash__(self):
        return hash(self._rel)

    def __str__(self):
        return f"images.dat:{self._rel}"

    __repr__ = __str__


def open_pack(dat: Path) -> PackedDir:
    return PackedDir(_Store(dat))
