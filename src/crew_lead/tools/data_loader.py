import csv
from pathlib import Path


# Find the project root
PROJECT_ROOT = Path(__file__).resolve().parents[3]

DATA_DIR = PROJECT_ROOT / "data"


def load_csv(filename):
    """Load a CSV file and return its rows as dictionaries."""

    file_path = DATA_DIR / filename

    with open(file_path, "r", newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def load_flights():
    return load_csv("flights.csv")


def load_crew():
    return load_csv("crew.csv")


def load_assignments():
    return load_csv("assignments.csv")