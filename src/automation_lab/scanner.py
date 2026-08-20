import hashlib
from pathlib import Path

from automation_lab.models import (
    DuplicateGroup,
    FileRecord,
    HashedFile,
    ScanResult,
    ScanStats,
)


def calculate_hash(file_path: Path) -> str:
    hasher = hashlib.sha256()

    with file_path.open("rb") as file:
        while chunk := file.read(8192):
            hasher.update(chunk)

    return hasher.hexdigest()


def validate_scan_folder(folder: Path) -> None:
    if not folder.exists():
        raise FileNotFoundError(f"Folder not correct, it doesn't exist {folder}")
    if not folder.is_dir():
        raise NotADirectoryError(f"Folder not correct, it is a file {folder}")


def discover_files(folder: Path) -> list[FileRecord]:
    quarantine_folder = folder / ".duplicates_quarantine"
    discovered_files: list[FileRecord] = []

    for path in folder.rglob("*"):
        if quarantine_folder in path.parents:
            continue

        if path.is_file():
            file_stat = path.stat()

            file_record = FileRecord(
                path=path,
                size_bytes=file_stat.st_size,
                modified_ns=file_stat.st_mtime_ns,
            )

            discovered_files.append(file_record)

    return discovered_files


def group_files_by_size(
    files: list[FileRecord],
) -> dict[int, list[FileRecord]]:
    files_by_size: dict[int, list[FileRecord]] = {}

    for file_record in files:
        files_by_size.setdefault(file_record.size_bytes, []).append(file_record)

    return files_by_size


def hash_candidate_files(
    files_by_size: dict[int, list[FileRecord]],
) -> tuple[HashedFile, ...]:
    hashed_files: list[HashedFile] = []

    for files_with_same_size in files_by_size.values():
        if len(files_with_same_size) == 1:
            continue

        for file_record in files_with_same_size:
            file_hash = calculate_hash(file_record.path)

            hashed_files.append(
                HashedFile(
                    file=file_record,
                    file_hash=file_hash,
                    reused=False,
                )
            )

    return tuple(hashed_files)


def create_duplicate_groups(
    hashed_files: tuple[HashedFile, ...],
) -> list[DuplicateGroup]:
    files_by_hash: dict[str, list[FileRecord]] = {}

    for hashed_file in hashed_files:
        files_by_hash.setdefault(
            hashed_file.file_hash,
            [],
        ).append(hashed_file.file)

    duplicate_groups = [
        DuplicateGroup(
            file_hash=file_hash,
            files=tuple(files),
        )
        for file_hash, files in files_by_hash.items()
        if len(files) > 1
    ]

    return duplicate_groups


def find_duplicates(folder: Path) -> ScanResult:
    """Find duplicate files and return groups with scan statistics."""
    validate_scan_folder(folder)

    discovered_files = discover_files(folder)
    files_by_size = group_files_by_size(discovered_files)
    hashed_files = hash_candidate_files(files_by_size)
    duplicate_groups = create_duplicate_groups(hashed_files)

    scan_stats = ScanStats(
        discovered_files=len(discovered_files),
        hashed_files=len(hashed_files),
        skipped_files=len(discovered_files) - len(hashed_files),
    )

    scan_result = ScanResult(
        duplicate_groups=tuple(duplicate_groups),
        hashed_files=hashed_files,
        stats=scan_stats,
    )
    return scan_result
