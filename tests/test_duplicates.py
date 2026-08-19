from pathlib import Path

from automation_lab.duplicates import (
    calculate_reclaimable_bytes,
    create_cleanup_plan,
    create_unique_destination,
    format_file_size,
    move_duplicate_files,
)
from automation_lab.models import DuplicateGroup, FileRecord


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
