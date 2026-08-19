import argparse
import hashlib
import shutil
from pathlib import Path

from automation_lab.models import DuplicateGroup, FileRecord
from automation_lab.reporting import write_report


def main() -> None:
    args = parse_argument()

    scan_folder = args.folder.resolve()
    quarantine_folder = scan_folder / ".duplicates_quarantine"

    duplicates = find_duplicates(scan_folder)
    cleanup_plan = create_cleanup_plan(duplicates)
    reclaimable_bytes = calculate_reclaimable_bytes(cleanup_plan)

    print_duplicate_report(duplicates)

    if args.report:
        write_report(duplicates, args.report)
        print(f"Report written to: {args.report}")

    print(f"Total reclaimable space: {format_file_size(reclaimable_bytes)}")

    if args.move:
        move_duplicate_files(cleanup_plan, quarantine_folder)
        print(f"Duplicate files moved to: {quarantine_folder}")
    else:
        print("Duplicate files not moved. Use --move to move them to quarantine.")


def parse_argument() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Find and safely quarantine duplicate files."
    )
    parser.add_argument(
        "folder",
        type=Path,
        help="Folder to scan for duplicate files.",
    )
    parser.add_argument(
        "--move",
        action="store_true",
        help="Move duplicate files to a quarantine folder.",
    )
    parser.add_argument(
        "--report",
        type=Path,
        help="Write the duplicate report to a .json or .csv file.",
    )
    return parser.parse_args()


def calculate_hash(file_path: Path) -> str:
    hasher = hashlib.sha256()

    with file_path.open("rb") as file:
        while chunk := file.read(8192):
            hasher.update(chunk)

        return hasher.hexdigest()


def find_duplicates(folder: Path) -> list[DuplicateGroup]:
    """Find content-identical files, hashing only equal-size candidates."""
    if not folder.exists():
        raise FileNotFoundError(f"Folder not correct, it doesn't exist {folder}")
    if not folder.is_dir():
        raise NotADirectoryError(f"Folder not correct, it is a file {folder}")

    quarantine_folder = folder / ".duplicates_quarantine"
    files_by_size: dict[int, list[FileRecord]] = {}

    for path in folder.rglob("*"):
        if quarantine_folder in path.parents:
            continue

        if path.is_file():
            file_record = FileRecord(
                path=path,
                size_bytes=path.stat().st_size,
            )
            files_by_size.setdefault(file_record.size_bytes, []).append(file_record)

    files_by_hash: dict[str, list[FileRecord]] = {}

    for files_with_same_size in files_by_size.values():
        if len(files_with_same_size) == 1:
            continue

        for file_record in files_with_same_size:
            file_hash = calculate_hash(file_record.path)
            files_by_hash.setdefault(file_hash, []).append(file_record)

    duplicate_groups = [
        DuplicateGroup(
            file_hash=file_hash,
            files=tuple(files),
        )
        for file_hash, files in files_by_hash.items()
        if len(files) > 1
    ]

    return duplicate_groups


def create_cleanup_plan(
    duplicate_groups: list[DuplicateGroup],
) -> dict[Path, list[Path]]:
    cleanup_plan = {}

    for group in duplicate_groups:
        if len(group.files) < 2:
            continue

        file_to_keep = group.files[0].path
        files_to_remove = [file_record.path for file_record in group.files[1:]]

        cleanup_plan[file_to_keep] = files_to_remove

    return cleanup_plan


def calculate_reclaimable_bytes(cleanup_plan: dict[Path, list[Path]]) -> int:
    total_bytes = 0
    for files_to_remove in cleanup_plan.values():
        for file in files_to_remove:
            total_bytes += file.stat().st_size
    return total_bytes


def format_file_size(size_in_bytes: int) -> str:
    if size_in_bytes < 1024:
        return f"{size_in_bytes} B"
    elif size_in_bytes < 1024**2:
        return f"{size_in_bytes / 1024:.2f} KB"
    elif size_in_bytes < 1024**3:
        return f"{size_in_bytes / (1024**2):.2f} MB"
    else:
        return f"{size_in_bytes / (1024**3):.2f} GB"


def move_duplicate_files(
    cleanup_plan: dict[Path, list[DuplicateGroup]],
    quarantine_folder: Path,
) -> list[Path]:
    quarantine_folder.mkdir(parents=True, exist_ok=True)
    moved_files = []

    for files_to_remove in cleanup_plan.values():
        for file in files_to_remove:
            destination = create_unique_destination(quarantine_folder, file)

            shutil.move(file, destination)
            moved_files.append(destination)
            print(f"Moved {file} to {destination}")

    return moved_files


def create_unique_destination(quarantine_folder: Path, source_file: Path) -> Path:
    """Return an available quarantine path without overwriting existing files."""
    destination = quarantine_folder / source_file.name
    counter = 1
    while destination.exists():
        destination = quarantine_folder / (
            f"{source_file.stem}-{counter}{source_file.suffix}"
        )
        counter += 1

    return destination


def print_duplicate_report(
    duplicate_groups: list[DuplicateGroup],
) -> None:
    duplicate_group_count = len(duplicate_groups)

    if duplicate_group_count == 0:
        print("No duplicate files found.")
        return

    print(f"Found {duplicate_group_count} duplicate groups.")

    for group_number, group in enumerate(duplicate_groups, start=1):
        print(f"Group {group_number} has the following duplicate files:")

        for file_record in group.files:
            print(f"\t{file_record.path.name}")


if __name__ == "__main__":
    main()
