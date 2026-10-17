import csv
import io


def normalize_tags(value: str) -> list[str]:
    rows = csv.reader(io.StringIO(value))
    return [field.strip() for row in rows for field in row if field.strip()]
