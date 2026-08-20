import pytest

import automation_lab.scanner as scanner_module
from automation_lab.models import CachedFile, ScanStats
from automation_lab.scanner import find_duplicates


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

    assert len(result.duplicate_groups) == 1

    duplicate_records = result.duplicate_groups[0].files
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

    assert result.duplicate_groups == ()


def test_finds_multiple_duplicate_groups(tmp_path):
    (tmp_path / "group-a-original.txt").write_text("content A")
    (tmp_path / "group-a-copy.txt").write_text("content A")

    (tmp_path / "group-b-original.txt").write_text("content B")
    (tmp_path / "group-b-copy.txt").write_text("content B")

    result = find_duplicates(tmp_path)

    assert len(result.duplicate_groups) == 2


def test_missing_directory_raises_file_not_found_error(tmp_path):
    missing_folder = tmp_path / "does_not_exist"

    with pytest.raises(FileNotFoundError):
        find_duplicates(missing_folder)


def test_file_path_raises_not_a_directory_error(tmp_path):
    file = tmp_path / "file.txt"
    file.write_text("content")

    with pytest.raises(NotADirectoryError):
        find_duplicates(file)


def test_find_duplicates_ignores_quarantine(tmp_path):
    original = tmp_path / "original.txt"
    quarantine_folder = tmp_path / ".duplicates_quarantine"
    quarantined_copy = quarantine_folder / "copy.txt"

    quarantine_folder.mkdir()
    original.write_text("same content")
    quarantined_copy.write_text("same content")

    result = find_duplicates(tmp_path)

    assert result.duplicate_groups == ()
    assert result.stats == ScanStats(
        discovered_files=1,
        hashed_files=0,
        skipped_files=1,
    )


def test_unique_size_files_are_not_hashed(tmp_path, monkeypatch):
    (tmp_path / "one-byte.txt").write_text("a")
    (tmp_path / "two-bytes.txt").write_text("bb")
    (tmp_path / "three-bytes.txt").write_text("ccc")

    hashed_files = []

    def record_hash_call(file_path):
        hashed_files.append(file_path)
        return "unused-hash"

    monkeypatch.setattr(
        scanner_module,
        "calculate_hash",
        record_hash_call,
    )

    result = find_duplicates(tmp_path)

    assert result.duplicate_groups == ()
    assert result.stats == ScanStats(
        discovered_files=3,
        hashed_files=0,
        skipped_files=3,
    )
    assert hashed_files == []


def test_same_size_files_with_different_contents_are_not_duplicates(tmp_path):
    (tmp_path / "first.txt").write_text("abcd")
    (tmp_path / "second.txt").write_text("wxyz")

    result = find_duplicates(tmp_path)

    assert result.duplicate_groups == ()
    assert result.stats == ScanStats(
        discovered_files=2,
        hashed_files=2,
        skipped_files=0,
    )


def test_scan_stats_count_discovered_hashed_and_skipped_files(tmp_path):
    (tmp_path / "original.txt").write_text("same")
    (tmp_path / "duplicate.txt").write_text("same")
    (tmp_path / "unique.txt").write_text("different size")

    result = find_duplicates(tmp_path)

    assert len(result.duplicate_groups) == 1
    assert result.stats == ScanStats(
        discovered_files=3,
        hashed_files=2,
        skipped_files=1,
    )


def test_reuses_valid_cached_hashes(tmp_path, monkeypatch):
    original = tmp_path / "original.txt"
    duplicate = tmp_path / "duplicate.txt"

    original.write_text("same content")
    duplicate.write_text("same content")

    hash_cache = {}

    for file_path in (original, duplicate):
        file_stat = file_path.stat()
        hash_cache[str(file_path.resolve())] = CachedFile(
            size_bytes=file_stat.st_size,
            modified_ns=file_stat.st_mtime_ns,
            file_hash="cached-hash",
        )

    def fail_if_hash_is_calculated(file_path):
        pytest.fail(f"Unexpected hash calculation for {file_path}")

    monkeypatch.setattr(
        scanner_module,
        "calculate_hash",
        fail_if_hash_is_calculated,
    )

    result = find_duplicates(
        tmp_path,
        hash_cache=hash_cache,
    )

    assert len(result.duplicate_groups) == 1
    assert all(hashed_file.reused for hashed_file in result.hashed_files)
    assert result.stats == ScanStats(
        discovered_files=2,
        hashed_files=0,
        skipped_files=2,
    )
