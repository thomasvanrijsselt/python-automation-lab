import csv
import json

import pytest

from automation_lab.reporting import create_report_rows, write_report


@pytest.fixture
def duplicate_group(tmp_path):
    original = tmp_path / "original.txt"
    duplicate = tmp_path / "duplicate.txt"

    original.write_text("same content")
    duplicate.write_text("same content")

    return {
        "example-hash": [original, duplicate],
    }


def test_create_report_rows_marks_first_file_to_keep(duplicate_group):
    rows = create_report_rows(duplicate_group)

    assert len(rows) == 2
    assert rows[0]["group_id"] == 1
    assert rows[0]["hash"] == "example-hash"
    assert rows[0]["size_bytes"] == 12
    assert rows[0]["action"] == "keep"
    assert rows[1]["action"] == "quarantine"


def test_writes_json_report(tmp_path, duplicate_group):
    report_path = tmp_path / "report.json"

    write_report(duplicate_group, report_path)

    rows = json.loads(report_path.read_text(encoding="utf-8"))

    assert len(rows) == 2
    assert rows[0]["hash"] == "example-hash"
    assert rows[0]["action"] == "keep"
    assert rows[1]["action"] == "quarantine"


def test_writes_csv_report(tmp_path, duplicate_group):
    report_path = tmp_path / "report.csv"

    write_report(duplicate_group, report_path)

    with report_path.open(encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))

    assert len(rows) == 2
    assert rows[0]["group_id"] == "1"
    assert rows[0]["hash"] == "example-hash"
    assert rows[0]["size_bytes"] == "12"
    assert rows[0]["action"] == "keep"
    assert rows[1]["action"] == "quarantine"


def test_empty_json_report_contains_empty_list(tmp_path):
    report_path = tmp_path / "report.json"

    write_report({}, report_path)

    assert json.loads(report_path.read_text(encoding="utf-8")) == []


def test_empty_csv_report_contains_headers(tmp_path):
    report_path = tmp_path / "report.csv"

    write_report({}, report_path)

    with report_path.open(encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))

    assert rows == []


def test_rejects_unsupported_report_format(tmp_path):
    report_path = tmp_path / "report.txt"

    with pytest.raises(
        ValueError,
        match=r"Report file must have a \.json or \.csv extension",
    ):
        write_report({}, report_path)
