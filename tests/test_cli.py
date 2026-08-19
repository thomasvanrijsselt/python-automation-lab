import sys

import duckdb

from automation_lab.duplicates import main


def test_cli_does_not_move_files_without_move_flag(
    tmp_path,
    monkeypatch,
    capsys,
):
    original = tmp_path / "original.txt"
    duplicate = tmp_path / "duplicate.txt"

    original.write_text("same content")
    duplicate.write_text("same content")

    monkeypatch.setattr(
        sys,
        "argv",
        ["find-duplicates", str(tmp_path)],
    )

    main()

    output = capsys.readouterr().out

    assert original.exists()
    assert duplicate.exists()
    assert not (tmp_path / ".duplicates_quarantine").exists()
    assert "Found 1 duplicate groups." in output
    assert "Duplicate files not moved." in output


def test_cli_moves_duplicates_with_move_flag(
    tmp_path,
    monkeypatch,
):
    (tmp_path / "original.txt").write_text("same content")
    (tmp_path / "duplicate.txt").write_text("same content")

    monkeypatch.setattr(
        sys,
        "argv",
        ["find-duplicates", str(tmp_path), "--move"],
    )

    main()

    quarantine = tmp_path / ".duplicates_quarantine"

    assert quarantine.exists()
    assert len(list(quarantine.iterdir())) == 1

    remaining_files = [path for path in tmp_path.iterdir() if path.is_file()]
    assert len(remaining_files) == 1


def test_cli_writes_json_report(tmp_path, monkeypatch):
    (tmp_path / "original.txt").write_text("same content")
    (tmp_path / "duplicate.txt").write_text("same content")

    report_path = tmp_path.parent / "duplicates.json"

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "find-duplicates",
            str(tmp_path),
            "--report",
            str(report_path),
        ],
    )

    main()

    assert report_path.exists()


def test_cli_persists_scan_history(
    tmp_path,
    monkeypatch,
):
    scan_folder = tmp_path / "scan"
    scan_folder.mkdir()

    (scan_folder / "original.txt").write_text("same content")
    (scan_folder / "duplicate.txt").write_text("same content")

    database_path = tmp_path / "history.duckdb"

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "find-duplicates",
            str(scan_folder),
            "--database",
            str(database_path),
        ],
    )

    main()

    assert database_path.exists()

    with duckdb.connect(str(database_path)) as connection:
        scan_count = connection.execute("SELECT COUNT(*) FROM scan_runs").fetchone()[0]

    assert scan_count == 1
