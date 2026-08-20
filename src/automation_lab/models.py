from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class FileRecord:
    path: Path
    size_bytes: int
    modified_ns: int


@dataclass(frozen=True)
class DuplicateGroup:
    file_hash: str
    files: tuple[FileRecord, ...]


@dataclass(frozen=True)
class CachedFile:
    size_bytes: int
    modified_ns: int
    file_hash: str


@dataclass(frozen=True)
class HashedFile:
    file: FileRecord
    file_hash: str
    reused: bool


@dataclass(frozen=True)
class ScanStats:
    discovered_files: int
    hashed_files: int
    skipped_files: int


@dataclass(frozen=True)
class ScanResult:
    duplicate_groups: tuple[DuplicateGroup, ...]
    hashed_files: tuple[HashedFile, ...]
    stats: ScanStats
