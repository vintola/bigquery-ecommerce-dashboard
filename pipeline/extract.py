#!/usr/bin/env python3
"""Run the BigQuery extracts and write the dashboard's Parquet files.

The dashboard reads only the files in ``data/``. BigQuery credentials are
therefore needed here, never in the Streamlit app.

Usage:
    export GOOGLE_CLOUD_PROJECT=your-project-id
    python pipeline/extract.py            # all extracts
    python pipeline/extract.py --only monthly_kpis category_monthly

Authentication uses Application Default Credentials locally, the
GOOGLE_APPLICATION_CREDENTIALS file set by the GitHub Action, or a short-lived
token from `gcloud auth print-access-token` via GOOGLE_OAUTH_ACCESS_TOKEN.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from google.cloud import bigquery

ROOT = Path(__file__).resolve().parents[1]
SQL_DIR = ROOT / "sql"
OUT_DIR = ROOT / "data"

SOURCE = "bigquery-public-data.thelook_ecommerce"

# name -> SQL file. Order matters only for console readability.
QUERIES = {
    "monthly_kpis": "monthly_kpis.sql",
    "monthly_customer_mix": "monthly_customer_mix.sql",
    "category_monthly": "category_monthly.sql",
    "product_monthly": "product_monthly.sql",
    "cohort_retention": "cohort_retention.sql",
    "customer_orders": "customer_orders.sql",
    "traffic_sources": "traffic_sources.sql",
    "inventory_risk": "inventory_risk.sql",
}

# A guard rail for the BigQuery sandbox (1 TB of queries per month). Override
# with MAX_BYTES_BILLED when running outside the sandbox.
MAX_BYTES_BILLED = int(os.environ.get("MAX_BYTES_BILLED", 200 * 1024**3))


def fail(message: str) -> None:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(1)


def build_client(project: str) -> bigquery.Client:
    token = os.environ.get("GOOGLE_OAUTH_ACCESS_TOKEN")
    if token:
        from google.oauth2.credentials import Credentials

        return bigquery.Client(project=project, credentials=Credentials(token=token))
    return bigquery.Client(project=project)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--only",
        nargs="+",
        choices=sorted(QUERIES),
        help="run only the named extracts",
    )
    args = parser.parse_args()

    project = os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("GCLOUD_PROJECT")
    if not project:
        fail("set GOOGLE_CLOUD_PROJECT to the GCP project used for BigQuery jobs")

    selected = args.only or list(QUERIES)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    client = build_client(project)
    manifest_path = OUT_DIR / "manifest.json"
    previous = {}
    if manifest_path.exists():
        previous = json.loads(manifest_path.read_text())

    files: dict[str, dict] = previous.get("files", {})

    for name in selected:
        sql = (SQL_DIR / QUERIES[name]).read_text(encoding="utf-8")
        print(f"[{name}] querying BigQuery...")
        started = time.time()
        job_config = bigquery.QueryJobConfig(maximum_bytes_billed=MAX_BYTES_BILLED)
        job = client.query(sql, job_config=job_config)
        frame = job.result().to_dataframe(create_bqstorage_client=False)
        # db-dtypes marks DATE columns with a pandas extension dtype that
        # pyarrow cannot serialise portably. Store plain timestamps instead.
        for column in ("month", "cohort_month"):
            if column in frame.columns:
                frame[column] = pd.to_datetime(frame[column])
        out = OUT_DIR / f"{name}.parquet"
        frame.to_parquet(out, index=False)
        elapsed = time.time() - started
        size_kb = out.stat().st_size / 1024
        files[name] = {
            "sql": QUERIES[name],
            "rows": int(len(frame)),
            "bytes": out.stat().st_size,
            "query_seconds": round(elapsed, 1),
            "bytes_processed": int(job.total_bytes_processed or 0),
        }
        print(
            f"[{name}] {len(frame):,} rows -> {out.relative_to(ROOT)} "
            f"({size_kb:,.0f} KB, {elapsed:.1f}s, "
            f"{(job.total_bytes_processed or 0) / 1024**3:.2f} GB scanned)"
        )

    manifest = {
        "source": SOURCE,
        "project": project,
        "extracted_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "max_bytes_billed": MAX_BYTES_BILLED,
        "notes": [
            "Public synthetic dataset published by Google Cloud.",
            "Revenue is SUM(order_items.sale_price), excluding Cancelled line items.",
            "COGS uses products.cost; gross profit is revenue minus COGS.",
            "Returns are identified by a non-null order_items.returned_at.",
            "The incomplete current month is excluded so trends end on a complete period.",
        ],
        "files": dict(sorted(files.items())),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {manifest_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
