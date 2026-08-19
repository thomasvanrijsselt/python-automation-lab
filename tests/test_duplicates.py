from pathlib import Path

import pytest

import automation_lab.duplicates as duplicates_module
from automation_lab.duplicates import (
    calculate_reclaimable_bytes,
    create_cleanup_plan,
    create_unique_destination,
    find_duplicates,
    format_file_size,
    move_duplicate_files,
)
from automation_lab.models import DuplicateGroup, FileRecord


def test_finds_duplicate_files_across_nested_directories(tmp_path):
    nested_folder = tmp_path / "nested"
    nested_folder.mkdir()

    original = tmp_path / "test1.txt"
    copy_1 = tmp_path / "test1 copy.txt"
    copy_2 = nested_folder / "test2.txt"

    original.write_text("same content")
    copy_1.write_text("same content")
    copy_2.write_text("same content")

    result = find_duplicates(tmp_path)

    assert len(result) == 1

    duplicate_records = result[0].files
    duplicate_names = {file_record.path.name for file_record in duplicate_records}

    assert duplicate_names == {
        "test1 copy.txt",
        "test1.txt",
        "test2.txt",
    }


def test_ignores_unique_files(tmp_path):
    (tmp_path / "first.txt").write_text("first")
    (tmp_path / "second.txt").write_text("second")

    result = find_duplicates(tmp_path)

    assert result == []


def test_finds_multiple_duplicate_groups(tmp_path):
    (tmp_path / "group-a-original.txt").write_text("content A")
    (tmp_path / "group-a-copy.txt").write_text("content A")

    (tmp_path / "group-b-original.txt").write_text("content B")
    (tmp_path / "group-b-copy.txt").write_text("content B")

    result = find_duplicates(tmp_path)

    assert len(result) == 2


def test_missing_directory_raises_file_not_found_error(tmp_path):
    missing_folder = tmp_path / "does_not_exist"

    with pytest.raises(FileNotFoundError):
        find_duplicates(missing_folder)


def test_file_path_raises_not_a_directory_error(tmp_path):
    file = tmp_path / "file.txt"
    file.write_text("content")

    with pytest.raises(NotADirectoryError):
        find_duplicates(file)


def test_create_cleanup_plan_keeps_first_file():
    file_1 = FileRecord(
        path=Path("original.txt"),
        size_bytes=100,
    )
    file_2 = FileRecord(
        path=Path("copy-1.txt"),
        size_bytes=100,
    )
    file_3 = FileRecord(
        path=Path("copy-2.txt"),
        size_bytes=100,
    )

    duplicate_groups = [
        DuplicateGroup(
            file_hash="some-hash",
            files=(file_1, file_2, file_3),
        )
    ]

    result = create_cleanup_plan(duplicate_groups)

    assert result == {
        file_1.path: [
            file_2.path,
            file_3.path,
        ]
    }


def test_calculate_reclaimable_bytes(tmp_path):
    original = tmp_path / "original.txt"
    copy_1 = tmp_path / "copy-1.txt"
    copy_2 = tmp_path / "copy-2.txt"

    original.write_text("hello")
    copy_1.write_text("hello")
    copy_2.write_text("hello")

    cleanup_plan = {
        original: [copy_1, copy_2],
    }

    assert calculate_reclaimable_bytes(cleanup_plan) == 10


def test_format_file_size():
    assert format_file_size(500) == "500 B"
    assert format_file_size(1024) == "1.00 KB"
    assert format_file_size(1024**2) == "1.00 MB"
    assert format_file_size(1024**3) == "1.00 GB"


def test_find_duplicates_ignores_quarantine(tmp_path):
    original = tmp_path / "original.txt"
    quarantine_folder = tmp_path / ".duplicates_quarantine"
    quarantined_copy = quarantine_folder / "copy.txt"

    quarantine_folder.mkdir()
    original.write_text("same content")
    quarantined_copy.write_text("same content")

    duplicates = find_duplicates(tmp_path)

    assert duplicates == []


def test_move_duplicate_files_to_quarantine(tmp_path):
    original = tmp_path / "original.txt"
    duplicate = tmp_path / "duplicate.txt"
    quarantine = tmp_path / ".duplicates_quarantine"

    original.write_text("same content")
    duplicate.write_text("same content")

    cleanup_plan = {
        original: [duplicate],
    }

    moved_files = move_duplicate_files(cleanup_plan, quarantine)

    assert original.exists()
    assert not duplicate.exists()
    assert (quarantine / "duplicate.txt").exists()
    assert moved_files == [quarantine / "duplicate.txt"]


def test_create_unique_destination_uses_original_name(tmp_path):
    source = Path("duplicate.txt")

    result = create_unique_destination(tmp_path, source)

    assert result == tmp_path / "duplicate.txt"


def test_create_unique_destination_adds_counter(tmp_path):
    (tmp_path / "duplicate.txt").write_text("existing")
    (tmp_path / "duplicate-1.txt").write_text("existing")

    source = Path("duplicate.txt")

    result = create_unique_destination(tmp_path, source)

    assert result == tmp_path / "duplicate-2.txt"


def test_unique_size_files_are_not_hashed(tmp_path, monkeypatch):
    (tmp_path / "one-byte.txt").write_text("a")
    (tmp_path / "two-bytes.txt").write_text("bb")
    (tmp_path / "three-bytes.txt").write_text("ccc")

    hashed_files = []

    def record_hash_call(file_path):
        hashed_files.append(file_path)
        return "unused-hash"

    monkeypatch.setattr(
        duplicates_module,
        "calculate_hash",
        record_hash_call,
    )

    result = find_duplicates(tmp_path)

    assert result == []
    assert hashed_files == []


def test_same_size_files_with_different_contents_are_not_duplicates(tmp_path):
    (tmp_path / "first.txt").write_text("abcd")
    (tmp_path / "second.txt").write_text("wxyz")

    result = find_duplicates(tmp_path)

    assert result == []
