import duckdb

from automation_lab.models import (
    DuplicateGroup,
    FileRecord,
    ScanResult,
    ScanStats,
)
from automation_lab.storage import persist_scan_result


def test_persists_scan_run_and_duplicate_files(tmp_path):
    original = tmp_path / "original.txt"
    duplicate = tmp_path / "duplicate.txt"

    original.write_text("same content")
    duplicate.write_text("same content")

    scan_result = ScanResult(
        duplicate_groups=(
            DuplicateGroup(
                file_hash="example-hash",
                files=(
                    FileRecord(
                        path=original,
                        size_bytes=12,
                    ),
                    FileRecord(
                        path=duplicate,
                        size_bytes=12,
                    ),
                ),
            ),
        ),
        stats=ScanStats(
            discovered_files=3,
            hashed_files=2,
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
            ORDER BY action
            """,
            [scan_id],
        ).fetchall()

    assert scan_run == (3, 2, 1, 1)
    assert len(duplicate_files) == 2
    assert {row[1] for row in duplicate_files} == {
        "keep",
        "quarantine",
    }


def test_persists_scan_without_duplicates(tmp_path):
    scan_result = ScanResult(
        duplicate_groups=(),
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
        scan_run_count = connection.execute(
            "SELECT COUNT(*) FROM scan_runs WHERE scan_id = ?",
            [scan_id],
        ).fetchone()[0]

        duplicate_file_count = connection.execute(
            "SELECT COUNT(*) FROM duplicate_files",
        ).fetchone()[0]

    assert scan_run_count == 1
    assert duplicate_file_count == 0
