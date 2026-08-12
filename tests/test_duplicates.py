from pathlib import Path

import pytest

from src.automation_lab.duplicates import find_duplicates


def test_finds_duplicate_files_across_nested_directories():
    test_folder = Path(__file__).parent / "test_data" / "duplicate_data"
    result = find_duplicates(test_folder)
    assert len(result) == 1
    duplicate_paths = next(iter(result.values()))
    duplicate_names = {path.name for path in duplicate_paths}
    assert duplicate_names == {"test1 copy.txt", "test1.txt", "test2.txt"}


def test_ignores_unique_files():
    test_folder = Path(__file__).parent / "test_data" / "unique_data"
    result = find_duplicates(test_folder)
    assert len(result) == 0


def test_finds_multiple_duplicate_groups():
    test_folder = Path(__file__).parent / "test_data1" / "duplicate_data"
    result = find_duplicates(test_folder)
    assert len(result) == 2


def test_missing_directory_raise_NotAFileError():
    missing_folder = Path(__file__).parent / "does_not_exist"
    with pytest.raises(FileNotFoundError):
        find_duplicates(missing_folder)


def test_missing_directory_raise_NotADirectoryError():
    missing_folder = (
        Path(__file__).parent / "test_data1" / "duplicate_data" / "test1.txt"
    )
    with pytest.raises(NotADirectoryError):
        find_duplicates(missing_folder)
