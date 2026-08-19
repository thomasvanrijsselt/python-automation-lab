from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class FileRecord:
    path: Path
    size_bytes: int


@dataclass(frozen=True)
class DuplicateGroup:
    file_hash: str
    files: tuple[FileRecord, ...]
