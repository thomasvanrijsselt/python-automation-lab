import csv
import json
from pathlib import Path

ReportRow = dict[str, str | int]


def write_report(
    duplicates: dict[str, list[Path]],
    report_path: Path,
) -> None:
    """Write duplicate-file information to a JSON or CSV report."""
    rows = create_report_rows(duplicates)
    suffix = report_path.suffix.lower()

    if suffix == ".json":
        write_json_report(rows, report_path)
    elif suffix == ".csv":
        write_csv_report(rows, report_path)
    else:
        raise ValueError("Report file must have a .json or .csv extension.")


def create_report_rows(
    duplicates: dict[str, list[Path]],
) -> list[ReportRow]:
    """Convert duplicate groups into records suitable for reporting."""
    rows = []

    for group_id, (file_hash, files) in enumerate(
        duplicates.items(),
        start=1,
    ):
        for position, file_path in enumerate(files):
            rows.append(
                {
                    "group_id": group_id,
                    "hash": file_hash,
                    "file_path": str(file_path.resolve()),
                    "size_bytes": file_path.stat().st_size,
                    "action": "keep" if position == 0 else "quarantine",
                }
            )

    return rows


def write_json_report(
    rows: list[ReportRow],
    report_path: Path,
) -> None:
    """Write report rows as JSON."""
    with report_path.open("w", encoding="utf-8") as file:
        json.dump(rows, file, indent=2)
        file.write("\n")


def write_csv_report(
    rows: list[ReportRow],
    report_path: Path,
) -> None:
    """Write report rows as CSV."""
    fieldnames = [
        "group_id",
        "hash",
        "file_path",
        "size_bytes",
        "action",
    ]

    with report_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
