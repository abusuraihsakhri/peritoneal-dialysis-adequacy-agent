"""Regression checks for boolean flags read from CSV text."""
import csv

from pd_sentinel import WeeklyKtVPeritonealAgent
from peritoneal_dialysis_adequacy_agent.cli import main as package_main


def test_legacy_string_false_not_critical():
    agent = WeeklyKtVPeritonealAgent()
    assert agent.evaluate({"critical_flag": "False", "metric_secondary": "4.0"}) == []
    assert len(agent.evaluate({"critical_flag": "True", "metric_secondary": "4.0"})) == 1


def test_package_batch_parses_false_and_true(tmp_path):
    source = tmp_path / "input.csv"
    output = tmp_path / "output.csv"
    source.write_text(
        "case_id,patient_synthetic_id,metric_primary,metric_secondary,is_stat,status_flag\n"
        "CASE-A,SYNTH-1,10,4,False,NORMAL\n"
        "CASE-B,SYNTH-2,10,4,True,NORMAL\n",
        encoding="utf-8"
    )
    assert package_main(["batch", "-i", str(source), "-o", str(output)]) == 0
    with output.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 2
    assert rows[0]["stat_critical_alerts"] == "0"
    assert rows[1]["stat_critical_alerts"] == "1"
