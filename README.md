# Python Automation Lab

Practical Python automation tools built with testing, CI and command-line interfaces.

## Duplicate File Finder

Detects files with identical contents using SHA-256. Files with unique sizes are not hashed, reducing unnecessary work. Files are only moved when `--move` is supplied.

### Features

* Scans nested directories
* Hashes equal-size candidates in chunks
* Exports JSON and CSV reports
* Persists scan history in DuckDB
* Shows discovered, hashed and skipped file counts
* Safely moves duplicates to quarantine
* Includes pytest tests and GitHub Actions CI

## Requirements

* Python 3.11 or newer

## Installation

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

# Persist scan history
find-duplicates ~/Downloads --database ~/download-scans.duckdb
> **Important:** Store the DuckDB database outside the scanned directory. Otherwise, the database may be scanned as an input file and change while the scan is running.

# Move duplicates to quarantine
find-duplicates /path/to/directory --move

# Display all options
find-duplicates --help
```

Reports contain each duplicate group, hash, file path, size and recommended action.

The DuckDB database stores scan metrics in `scan_runs` and detected duplicate files in `duplicate_files`. Store it outside the scanned directory so it is not included in later scans.

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

* Reuse unchanged hashes during incremental scans
* Compare scan history
* Add performance benchmarks
* Publish the package
