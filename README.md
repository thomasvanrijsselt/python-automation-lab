Python Automation Lab

Practical Python automation tools built with production-style testing, CI and command-line interfaces.

Duplicate File Finder

Recursively detects files with identical contents using SHA-256 hashes. By default, it only reports duplicates and does not modify files.

Features
- Scans nested directories
- Hashes files in chunks
- Safely moves duplicates to a quarantine folder
- Exports JSON and CSV reports
- Handles filename collisions in quarantine
- Includes automated tests and GitHub Actions CI
- Skips hashing files with unique sizes
- Scan metrics
- Explicit pipeline stages

Requirements
Python 3.11 or newer
Installation
git clone https://github.com/thomasvanrijsselt/python-automation-lab
cd python-automation-lab

python3 -m venv .venv
source .venv/bin/activate

python -m pip install -e .

For development:

python -m pip install pytest ruff
Usage

Scan a directory without moving files:

find-duplicates /path/to/directory

Export a JSON or CSV report:

find-duplicates /path/to/directory --report duplicates.json
find-duplicates /path/to/directory --report duplicates.csv

Reports include each file’s duplicate group, SHA-256 hash, path, size and recommended action.

Move duplicate files into .duplicates_quarantine:

find-duplicates /path/to/directory --move

The first file in each duplicate group is kept. Other copies are moved only when --move is supplied; files are never deleted.

Options can be combined:

find-duplicates /path/to/directory \
  --report duplicates.csv \
  --move

Display all options:

find-duplicates --help
Development

Run tests and code-quality checks:

python -m pytest
python -m ruff check .
python -m ruff format --check .

These checks also run automatically through GitHub Actions.

Roadmap
- DuckDB-backed incremental scans
- Integration tests and performance benchmarks
- Package publishing