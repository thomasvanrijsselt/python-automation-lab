import hashlib
from pathlib import Path

from automation_lab.models import DuplicateGroup, FileRecord


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
            discovered_files.append(
                FileRecord(
                    path=path,
                    size_bytes=path.stat().st_size,
                )
            )

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
) -> dict[str, list[FileRecord]]:
    files_by_hash: dict[str, list[FileRecord]] = {}

    for files_with_same_size in files_by_size.values():
        if len(files_with_same_size) == 1:
            continue

        for file_record in files_with_same_size:
            file_hash = calculate_hash(file_record.path)
            files_by_hash.setdefault(file_hash, []).append(file_record)

    return files_by_hash


def create_duplicate_groups(
    files_by_hash: dict[str, list[FileRecord]],
) -> list[DuplicateGroup]:
    duplicate_groups = [
        DuplicateGroup(
            file_hash=file_hash,
            files=tuple(files),
        )
        for file_hash, files in files_by_hash.items()
        if len(files) > 1
    ]

    return duplicate_groups


def find_duplicates(folder: Path) -> list[DuplicateGroup]:
    """Find content-identical files, hashing only equal-size candidates."""
    validate_scan_folder(folder)

    discovered_files = discover_files(folder)
    files_by_size = group_files_by_size(discovered_files)
    files_by_hash = hash_candidate_files(files_by_size)
    duplicate_groups = create_duplicate_groups(files_by_hash)

    return duplicate_groups
