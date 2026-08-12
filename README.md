# Python Automation Lab

A collection of practical Python automation tools built to improve my Python engineering skills.

## Duplicate File Finder

The first tool recursively scans a directory and identifies duplicate files based on their contents.

Files are read as binary data and converted into SHA-256 hashes. Files with the same hash have identical contents, regardless of their filename or location.

### Features

- Recursively scans nested directories
- Detects duplicates by file content
- Reads files in chunks to support large files
- Accepts relative and absolute directory paths
- Handles missing paths and invalid input
- Provides a command-line interface
- Includes automated tests with pytest

## Project Structure

```text
python-automation-lab/
├── src/
│   └── automation_lab/
│       ├── __init__.py
│       └── duplicates.py
├── tests/
│   ├── test_data/
│   └── test_duplicates.py
├── .gitignore
├── pyproject.toml
└── README.md
```

## Requirements

- Python 3.11 or newer

## Installation

Clone the repository and open the project directory:

```bash
git clone <repository-url>
cd python-automation-lab
```

Create and activate a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

Install the project in editable mode:

```bash
python -m pip install -e .
```

Install the development dependencies:

```bash
python -m pip install pytest ruff
```

## Usage

Scan a directory for duplicate files:

```bash
find-duplicates /path/to/directory
```

You can also provide a relative path:

```bash
find-duplicates ./photos
```

Display the help page:

```bash
find-duplicates --help
```

Example output:

```text
Found 2 duplicate groups containing 5 files.

Group 1:
  test1.txt
  test1-copy.txt
  test1-backup.txt

Group 2:
  photo.jpg
  photo-copy.jpg
```

When no duplicates are found:

```text
No duplicate files found.
```

The tool only reports duplicates. It does not delete or modify files.

## Running Tests

Run the complete test suite:

```bash
python -m pytest -v
```

The tests cover:

- Duplicate files across nested directories
- Unique files
- Multiple duplicate groups
- Missing directories
- File paths supplied instead of directories

## Code Quality

Check the project with Ruff:

```bash
python -m ruff check .
```

Check formatting:

```bash
python -m ruff format --check .
```

Automatically format the code:

```bash
python -m ruff format .
```

## Roadmap

Planned automation tools include:

- Directory disk-usage reporter
- File organizer
- Old-file finder
- Directory backup utility
- CSV schema validator
- Data-quality reporter
- API health checker

Future improvements will include structured logging, configuration files, Docker, GitHub Actions and scheduled execution.