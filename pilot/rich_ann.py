from pathlib import Path
def find_annotations(names, row):
    """All annotation files for a spreadsheet row: exact name, else names containing the catalog number."""
    base = {Path(n).name: n for n in names}
    if row["annotated_image_filename"] in base: return [base[row["annotated_image_filename"]]]
    cat = row["catalog_number"]; keys = {cat, cat.replace("-", "")}
    stem = Path(row["original_image_filename"]).stem
    hits = [n for b, n in base.items() if b.startswith(stem)]
    return hits or [n for b, n in base.items() if any(b.startswith(k + "-") or b.startswith(k + "_") for k in keys)]
