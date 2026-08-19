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


@dataclass(frozen=True)
class ScanStats:
    discovered_files: int
    hashed_files: int
    skipped_files: int


@dataclass(frozen=True)
class ScanResult:
    duplicate_groups: tuple[DuplicateGroup, ...]
    stats: ScanStats
