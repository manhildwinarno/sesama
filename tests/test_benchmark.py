"""python tests/test_benchmark.py; also checks notebook outputs when available locally."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
report = json.loads((ROOT / "assets/benchmark.json").read_text(encoding="utf-8"))
assert report["selection_metric"] == "weighted_f1"
assert [d["name"] for d in report["datasets"]] == ["SIBI", "BISINDO"]
notebook = ROOT / report["source"]
outputs = []
if notebook.exists():
    for cell in json.loads(notebook.read_text(encoding="utf-8"))["cells"]:
        text = ''.join(''.join(o.get("text", [])) + ''.join(o.get("data", {}).get("text/plain", []))
                       for o in cell.get("outputs", []))
        rows = re.findall(r'^\s*\d+\s+(SVM \(RBF Kernel\)|Random Forest|XGBoost)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s*$', text, re.M)
        if rows:
            outputs.append(rows)
    assert len(outputs) == 2
for i, dataset in enumerate(report["datasets"]):
    assert len(dataset["models"]) == 3
    assert max(dataset["models"], key=lambda m: m["weighted_f1"])["name"] == "SVM (RBF)"
    assert dataset["train_samples"] > dataset["test_samples"] > 0
    for j, model in enumerate(dataset["models"]):
        values = [model[key] for key in ("accuracy", "precision", "recall", "weighted_f1")]
        assert all(0 <= value <= 1 for value in values)
        if outputs:
            row = outputs[i][j]
            assert row[0].replace("RBF Kernel", "RBF") == model["name"]
            assert values == [float(value) for value in row[1:]]
print('PASS: benchmark values, F1 selection, and available notebook output provenance.')
