from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

import duckdb

from automation_lab.models import CachedFile, ScanResult

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


CREATE_FILE_CACHE_TABLE = """
CREATE TABLE IF NOT EXISTS file_cache (
    root_path VARCHAR NOT NULL,
    file_path VARCHAR NOT NULL,
    size_bytes BIGINT NOT NULL,
    modified_ns BIGINT NOT NULL,
    file_hash VARCHAR NOT NULL,
    last_seen_scan UUID NOT NULL,
    PRIMARY KEY (root_path, file_path)
)
"""


def initialize_database(
    connection: duckdb.DuckDBPyConnection,
) -> None:
    connection.execute(CREATE_SCAN_RUNS_TABLE)
    connection.execute(CREATE_DUPLICATE_FILES_TABLE)
    connection.execute(CREATE_FILE_CACHE_TABLE)


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

    cache_rows = create_cache_rows(
        scan_id=scan_id,
        root_path=root_path,
        scan_result=scan_result,
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
            if cache_rows:
                connection.executemany(
                    """
                    INSERT INTO file_cache (
                        root_path,
                        file_path,
                        size_bytes,
                        modified_ns,
                        file_hash,
                        last_seen_scan
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT (root_path, file_path)
                    DO UPDATE SET
                        size_bytes = excluded.size_bytes,
                        modified_ns = excluded.modified_ns,
                        file_hash = excluded.file_hash,
                        last_seen_scan = excluded.last_seen_scan
                    """,
                    cache_rows,
                )

            connection.execute("COMMIT")
        except Exception:
            connection.execute("ROLLBACK")
            raise

    return scan_id


def load_hash_cache(
    database_path: Path,
    root_path: Path,
) -> dict[str, CachedFile]:
    with duckdb.connect(str(database_path)) as connection:
        initialize_database(connection)

        rows = connection.execute(
            """
            SELECT
                file_path,
                size_bytes,
                modified_ns,
                file_hash
            FROM file_cache
            WHERE root_path = ?
            """,
            [str(root_path.resolve())],
        ).fetchall()

    hash_cache = {
        file_path: CachedFile(
            size_bytes=size_bytes,
            modified_ns=modified_ns,
            file_hash=file_hash,
        )
        for file_path, size_bytes, modified_ns, file_hash in rows
    }

    return hash_cache


def create_cache_rows(
    scan_id: UUID,
    root_path: Path,
    scan_result: ScanResult,
) -> list[tuple]:
    resolved_root = str(root_path.resolve())

    cache_rows = [
        (
            resolved_root,
            str(hashed_file.file.path.resolve()),
            hashed_file.file.size_bytes,
            hashed_file.file.modified_ns,
            hashed_file.file_hash,
            scan_id,
        )
        for hashed_file in scan_result.hashed_files
    ]

    return cache_rows
