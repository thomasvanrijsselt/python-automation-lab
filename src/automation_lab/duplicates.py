import argparse
import hashlib
from pathlib import Path


def main():
    folder = parse_folder_argument()
    duplicates_by_hash = find_duplicates(folder)
    print_duplicate_report(duplicates_by_hash)


def parse_folder_argument():
    parser = argparse.ArgumentParser()
    parser.add_argument("folder")
    args = parser.parse_args()
    return Path(args.folder)


def calculate_hash(file_path: Path) -> str:
    hasher = hashlib.sha256()

    with file_path.open("rb") as file:
        while chunk := file.read(8192):
            hasher.update(chunk)

        return hasher.hexdigest()


def find_duplicates(folder: Path) -> dict[str, list[Path]]:
    if not folder.exists():
        raise FileNotFoundError(f"Folder not correct, it doesn't exist {folder}")
    if not folder.is_dir():
        raise NotADirectoryError(f"Folder not correct, it is a file {folder}")
    files_by_hash = {}
    for path in folder.rglob("*"):
        if path.is_file():
            file_hash = calculate_hash(path)
            if file_hash in files_by_hash:
                files_by_hash[file_hash].append(path)
            else:
                files_by_hash[file_hash] = [path]

    duplicate_files_by_hash = {
        key: value for key, value in files_by_hash.items() if len(value) > 1
    }

    return duplicate_files_by_hash


def print_duplicate_report(duplicates_by_hash):
    duplicate_group_count = len(duplicates_by_hash.keys())

    if duplicate_group_count > 1 or duplicate_group_count == 1:
        print(f"Found {duplicate_group_count} duplicate groups.")
    else:
        print("No duplicate file found.")
    if duplicate_group_count > 0:
        i = 1
        for list_of_files in duplicates_by_hash.values():
            print(f"Group {i} has the following duplicated files: ")
            i += 1
            for file in list_of_files:
                print(f"\t{file.name}")


if __name__ == "__main__":
    main()
