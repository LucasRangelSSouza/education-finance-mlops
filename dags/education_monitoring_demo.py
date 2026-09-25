"""Disabled demonstration DAG: resolve the pinned release, train, drift-check, and score.

It has no schedule and starts paused. An operator must trigger it deliberately.
"""

from datetime import datetime
from pathlib import Path

from education_finance_mlops.release import resolve_release
from education_finance_mlops.release_pipeline import run_release_pipeline

try:
    from airflow import DAG
    from airflow.operators.python import PythonOperator
except ImportError:  # The package must remain importable without Airflow.
    DAG = None
    PythonOperator = None


def run_monitoring(train_through_year: int, evaluation_year: int, score_year: int, output_root: str) -> dict:
    result = run_release_pipeline(
        resolve_release(), Path(output_root),
        int(train_through_year), int(evaluation_year), int(score_year),
    )
    return {"status": result["status"], "drift_reasons": result["drift"]["reasons"]}


if DAG is not None:
    with DAG(
        "education_monitoring_demo",
        schedule=None,
        start_date=datetime(2026, 1, 1),
        catchup=False,
        is_paused_upon_creation=True,
        params={"train_through_year": 2020, "evaluation_year": 2021, "score_year": 2022,
                "output_root": "/tmp/education-monitoring"},
        tags=["mlops", "demo"],
    ) as dag:
        PythonOperator(
            task_id="train_monitor_score",
            python_callable=run_monitoring,
            op_kwargs={key: "{{ params.%s }}" % key for key in ("train_through_year", "evaluation_year", "score_year", "output_root")},
        )
