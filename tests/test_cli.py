import sys

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
