# Python Automation Lab

Practical Python automation tools built with testing, CI and command-line interfaces.

## Duplicate File Finder

Detects files with identical contents using SHA-256. Files with unique sizes are not hashed, and files are only moved when `--move` is supplied.

### Features

* Scans nested directories
* Hashes equal-size candidates in chunks
* Reuses unchanged hashes through a DuckDB cache
* Exports JSON and CSV reports
* Persists scan history and metrics
* Safely moves duplicates to quarantine
* Includes pytest tests and GitHub Actions CI

## Installation

Requires Python 3.11 or newer.

```bash
git clone https://github.com/thomasvanrijsselt/python-automation-lab.git
cd python-automation-lab
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

For development:

```bash
python -m pip install pytest ruff
```

## Usage

```bash
# Scan without modifying files
find-duplicates /path/to/directory

# Export a report
find-duplicates /path/to/directory --report duplicates.json
find-duplicates /path/to/directory --report duplicates.csv

# Persist history and reuse unchanged hashes
find-duplicates ~/Downloads --database ~/download-scans.duckdb

# Move duplicates to quarantine
find-duplicates /path/to/directory --move

# Display all options
find-duplicates --help
```

> **Important:** Store the DuckDB database outside the scanned directory. Otherwise, it may be included as an input file and change while the scan is running.

Reports contain each duplicate group, hash, file path, size and recommended action.

DuckDB stores scan metrics in `scan_runs`, duplicate results in `duplicate_files` and reusable hashes in `file_cache`. A hash is reused when the file path, size and modification time are unchanged.

The first file in each duplicate group is kept. Other copies are moved to `.duplicates_quarantine`; files are never deleted.

Options can be combined:

```bash
find-duplicates ~/Downloads \
  --report ~/Desktop/download-duplicates.csv \
  --database ~/download-scans.duckdb
```

## Development

```bash
python -m pytest
python -m ruff check .
python -m ruff format --check .
```

These checks also run through GitHub Actions.

## Roadmap

* Compare scan history
* Add performance benchmarks
* Publish the package
