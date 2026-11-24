"""python tests/test_evaluation_data.py; no training or private dataset required."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
data = json.loads((ROOT / "assets/evaluation.json").read_text(encoding="utf-8"))
benchmark = json.loads((ROOT / "assets/benchmark.json").read_text(encoding="utf-8"))
matrix = data["sibi_confusion"]
assert matrix["labels"] == list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
assert len(matrix["counts"]) == 26 and all(len(row) == 26 for row in matrix["counts"])
assert all(isinstance(n, int) and n >= 0 for row in matrix["counts"] for n in row)
assert all(sum(row) > 0 for row in matrix["counts"])
assert sum(map(sum, matrix["counts"])) == matrix["test_samples"] == 245
assert sum(row[i] for i, row in enumerate(matrix["counts"])) == matrix["correct"] == 235
assert round(matrix["correct"] / matrix["test_samples"], 6) == benchmark["datasets"][0]["models"][0]["accuracy"]
f1 = sum(2 * row[i] / (sum(row) + sum(r[i] for r in matrix["counts"])) * sum(row)
         for i, row in enumerate(matrix["counts"])) / matrix["test_samples"]
assert round(f1, 6) == benchmark["datasets"][0]["models"][0]["weighted_f1"]
features = data["rf_importance"]["features"]
assert len(features) == len({f["feature"] for f in features}) == 10
assert all(0 <= f["importance"] <= 1 for f in features)
assert [f["importance"] for f in features] == sorted([f["importance"] for f in features], reverse=True)
for distribution in data["class_distributions"]:
    assert sum(distribution["counts"].values()) == distribution["samples"]
    assert list(distribution["counts"]) == matrix["labels"]
    source = ROOT / distribution["source"]
    if source.exists():
        assert hashlib.sha256(source.read_bytes()).hexdigest() == distribution["sha256"]
assert hashlib.sha256((ROOT / "models/best_model_sibi.joblib").read_bytes()).hexdigest() == data["provenance"]["svm_sha256"]
print('PASS: confusion counts/F1, feature ranking, class totals, available source hashes.')
