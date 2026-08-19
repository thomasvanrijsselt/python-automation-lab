from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

import duckdb

from automation_lab.models import ScanResult

CREATE_SCAN_RUNS_TABLE = """
CREATE TABLE IF NOT EXISTS scan_runs (
    scan_id UUID PRIMARY KEY,
    root_path VARCHAR NOT NULL,
    scanned_at TIMESTAMPTZ NOT NULL,
    discovered_files BIGINT NOT NULL,
    hashed_files BIGINT NOT NULL,
    skipped_files BIGINT NOT NULL,
    duplicate_groups BIGINT NOT NULL
)
"""


CREATE_DUPLICATE_FILES_TABLE = """
CREATE TABLE IF NOT EXISTS duplicate_files (
    scan_id UUID NOT NULL,
    group_hash VARCHAR NOT NULL,
    file_path VARCHAR NOT NULL,
    size_bytes BIGINT NOT NULL,
    action VARCHAR NOT NULL,
    PRIMARY KEY (scan_id, file_path)
)
"""


def initialize_database(
    connection: duckdb.DuckDBPyConnection,
) -> None:
    connection.execute(CREATE_SCAN_RUNS_TABLE)
    connection.execute(CREATE_DUPLICATE_FILES_TABLE)


def create_duplicate_file_rows(
    scan_id: UUID,
    scan_result: ScanResult,
) -> list[tuple]:
    rows = []

    for group in scan_result.duplicate_groups:
        for position, file_record in enumerate(group.files):
            action = "keep" if position == 0 else "quarantine"

            rows.append(
                (
                    scan_id,
                    group.file_hash,
                    str(file_record.path.resolve()),
                    file_record.size_bytes,
                    action,
                )
            )

    return rows


def persist_scan_result(
    database_path: Path,
    root_path: Path,
    scan_result: ScanResult,
) -> UUID:
    scan_id = uuid4()
    scanned_at = datetime.now(UTC)

    scan_run_row = (
        scan_id,
        str(root_path.resolve()),
        scanned_at,
        scan_result.stats.discovered_files,
        scan_result.stats.hashed_files,
        scan_result.stats.skipped_files,
        len(scan_result.duplicate_groups),
    )

    duplicate_file_rows = create_duplicate_file_rows(
        scan_id,
        scan_result,
    )

    with duckdb.connect(str(database_path)) as connection:
        initialize_database(connection)
        connection.execute("BEGIN TRANSACTION")

        try:
            connection.execute(
                """
                INSERT INTO scan_runs (
                    scan_id,
                    root_path,
                    scanned_at,
                    discovered_files,
                    hashed_files,
                    skipped_files,
                    duplicate_groups
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                scan_run_row,
            )

            if duplicate_file_rows:
                connection.executemany(
                    """
                    INSERT INTO duplicate_files (
                        scan_id,
                        group_hash,
                        file_path,
                        size_bytes,
                        action
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    duplicate_file_rows,
                )

            connection.execute("COMMIT")
        except Exception:
            connection.execute("ROLLBACK")
            raise

    return scan_id
