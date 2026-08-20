import os

import duckdb

from automation_lab.models import (
    CachedFile,
    DuplicateGroup,
    FileRecord,
    HashedFile,
    ScanResult,
    ScanStats,
)
from automation_lab.scanner import find_duplicates
from automation_lab.storage import (
    load_hash_cache,
    persist_scan_result,
)


def create_file_record(file_path):
    file_stat = file_path.stat()

    return FileRecord(
        path=file_path,
        size_bytes=file_stat.st_size,
        modified_ns=file_stat.st_mtime_ns,
    )


def test_persists_scan_run_and_duplicate_files(tmp_path):
    scan_folder = tmp_path / "scan"
    scan_folder.mkdir()

    original = scan_folder / "original.txt"
    duplicate = scan_folder / "duplicate.txt"

    original.write_text("same content")
    duplicate.write_text("same content")

    original_record = create_file_record(original)
    duplicate_record = create_file_record(duplicate)

    scan_result = ScanResult(
        duplicate_groups=(
            DuplicateGroup(
                file_hash="example-hash",
                files=(original_record, duplicate_record),
            ),
        ),
        hashed_files=(
            HashedFile(
                file=original_record,
                file_hash="example-hash",
                reused=False,
            ),
            HashedFile(
                file=duplicate_record,
                file_hash="example-hash",
                reused=False,
            ),
        ),
        stats=ScanStats(
            discovered_files=2,
            hashed_files=2,
            skipped_files=0,
        ),
    )

    database_path = tmp_path / "history.duckdb"

    scan_id = persist_scan_result(
        database_path=database_path,
        root_path=scan_folder,
        scan_result=scan_result,
    )

    with duckdb.connect(str(database_path)) as connection:
        scan_run = connection.execute(
            """
            SELECT
                discovered_files,
                hashed_files,
                skipped_files,
                duplicate_groups
            FROM scan_runs
            WHERE scan_id = ?
            """,
            [scan_id],
        ).fetchone()

        duplicate_files = connection.execute(
            """
            SELECT file_path, action
            FROM duplicate_files
            WHERE scan_id = ?
            """,
            [scan_id],
        ).fetchall()

    assert scan_run == (2, 2, 0, 1)
    assert len(duplicate_files) == 2
    assert {row[1] for row in duplicate_files} == {
        "keep",
        "quarantine",
    }


def test_persists_scan_without_duplicates(tmp_path):
    scan_result = ScanResult(
        duplicate_groups=(),
        hashed_files=(),
        stats=ScanStats(
            discovered_files=1,
            hashed_files=0,
            skipped_files=1,
        ),
    )

    database_path = tmp_path / "history.duckdb"

    scan_id = persist_scan_result(
        database_path=database_path,
        root_path=tmp_path,
        scan_result=scan_result,
    )

    with duckdb.connect(str(database_path)) as connection:
        scan_run_count_row = connection.execute(
            "SELECT COUNT(*) FROM scan_runs WHERE scan_id = ?",
            [scan_id],
        ).fetchone()

        duplicate_file_count_row = connection.execute(
            "SELECT COUNT(*) FROM duplicate_files",
        ).fetchone()

    assert scan_run_count_row is not None
    assert duplicate_file_count_row is not None

    scan_run_count = scan_run_count_row[0]
    duplicate_file_count = duplicate_file_count_row[0]

    assert scan_run_count == 1
    assert duplicate_file_count == 0


def test_load_hash_cache_returns_empty_dictionary_for_new_database(tmp_path):
    database_path = tmp_path / "history.duckdb"
    scan_folder = tmp_path / "scan"
    scan_folder.mkdir()

    result = load_hash_cache(
        database_path=database_path,
        root_path=scan_folder,
    )

    assert result == {}
    assert database_path.exists()


def test_persist_scan_result_updates_hash_cache(tmp_path):
    scan_folder = tmp_path / "scan"
    scan_folder.mkdir()

    original = scan_folder / "original.txt"
    duplicate = scan_folder / "duplicate.txt"

    original.write_text("same content")
    duplicate.write_text("same content")

    original_record = create_file_record(original)
    duplicate_record = create_file_record(duplicate)

    scan_result = ScanResult(
        duplicate_groups=(
            DuplicateGroup(
                file_hash="example-hash",
                files=(original_record, duplicate_record),
            ),
        ),
        hashed_files=(
            HashedFile(
                file=original_record,
                file_hash="example-hash",
                reused=False,
            ),
            HashedFile(
                file=duplicate_record,
                file_hash="example-hash",
                reused=False,
            ),
        ),
        stats=ScanStats(
            discovered_files=2,
            hashed_files=2,
            skipped_files=0,
        ),
    )

    database_path = tmp_path / "history.duckdb"

    persist_scan_result(
        database_path=database_path,
        root_path=scan_folder,
        scan_result=scan_result,
    )

    cache = load_hash_cache(
        database_path=database_path,
        root_path=scan_folder,
    )

    assert cache[str(original.resolve())] == CachedFile(
        size_bytes=original_record.size_bytes,
        modified_ns=original_record.modified_ns,
        file_hash="example-hash",
    )
    assert cache[str(duplicate.resolve())] == CachedFile(
        size_bytes=duplicate_record.size_bytes,
        modified_ns=duplicate_record.modified_ns,
        file_hash="example-hash",
    )


def test_persisted_hashes_are_reused_during_next_scan(tmp_path):
    scan_folder = tmp_path / "scan"
    scan_folder.mkdir()

    (scan_folder / "original.txt").write_text("same content")
    (scan_folder / "duplicate.txt").write_text("same content")

    database_path = tmp_path / "history.duckdb"

    first_result = find_duplicates(scan_folder)

    persist_scan_result(
        database_path=database_path,
        root_path=scan_folder,
        scan_result=first_result,
    )

    hash_cache = load_hash_cache(
        database_path=database_path,
        root_path=scan_folder,
    )

    second_result = find_duplicates(
        scan_folder,
        hash_cache=hash_cache,
    )

    assert len(second_result.duplicate_groups) == 1
    assert all(hashed_file.reused for hashed_file in second_result.hashed_files)
    assert second_result.stats == ScanStats(
        discovered_files=2,
        hashed_files=0,
        skipped_files=2,
    )


def test_changed_file_is_rehashed_instead_of_reused(tmp_path):
    scan_folder = tmp_path / "scan"
    scan_folder.mkdir()

    unchanged_file = scan_folder / "unchanged.txt"
    changed_file = scan_folder / "changed.txt"

    unchanged_file.write_text("same content")
    changed_file.write_text("same content")

    database_path = tmp_path / "history.duckdb"

    first_result = find_duplicates(scan_folder)

    persist_scan_result(
        database_path=database_path,
        root_path=scan_folder,
        scan_result=first_result,
    )

    original_stat = changed_file.stat()

    # Keep the same file size so both files remain hashing candidates.
    changed_file.write_text("new! content")
    os.utime(
        changed_file,
        ns=(
            original_stat.st_atime_ns,
            original_stat.st_mtime_ns + 1_000_000_000,
        ),
    )

    hash_cache = load_hash_cache(
        database_path=database_path,
        root_path=scan_folder,
    )

    second_result = find_duplicates(
        scan_folder,
        hash_cache=hash_cache,
    )

    hashed_files_by_name = {
        hashed_file.file.path.name: hashed_file
        for hashed_file in second_result.hashed_files
    }

    assert hashed_files_by_name["unchanged.txt"].reused is True
    assert hashed_files_by_name["changed.txt"].reused is False

    assert second_result.duplicate_groups == ()
    assert second_result.stats == ScanStats(
        discovered_files=2,
        hashed_files=1,
        skipped_files=1,
    )
