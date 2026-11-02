# TheLook eCommerce — BigQuery → Streamlit sample dashboard

A public, interactive retail analytics dashboard built from Google's
[TheLook eCommerce](https://console.cloud.google.com/marketplace/product/bigquery-public-data/thelook-ecommerce)
dataset on BigQuery. It is the live sample linked from
[alvintola.com](https://alvintola.com).

The point is the method: ingest a public source, define the KPIs, find the
driver, and make the next decision obvious. No client data is used.

## Architecture

```
BigQuery public dataset                 This repo                       Streamlit Community Cloud
bigquery-public-data.thelook_ecommerce
        │
        │  sql/*.sql (SELECT only)
        ▼
pipeline/extract.py  ──►  data/*.parquet + manifest.json  ──►  app.py
        ▲                                                         │
        │  weekly (optional)                                       ▼
pipeline/refresh-workflow.yml                             share.streamlit.io
                                                                  │
                                                                  │ raw app path /~/+/
                                                                  ▼
                                                    Cloudflare Worker (dashboard.alvintola.com)
                                                                  │
                                                                  ▼
                                                         https://dashboard.alvintola.com/
```

BigQuery credentials are needed only by `pipeline/extract.py`. The Streamlit
app reads committed Parquet extracts, so it is fast, cheap to host, and does
not expose a service account to the public.

## What the dashboard answers

- **Overview** — revenue, gross profit, margin, orders, AOV and returns, with
  the selected period compared with the preceding window of equal length.
- **Products & margin** — a promote / hold / review / remove matrix based on
  revenue and margin relative to the medians, plus top-product and category
  tables.
- **Customers** — repeat rate, lifetime order distribution, cohort retention
  heatmap and acquisition-source performance.
- **Inventory** — unsold share, tied-up capital and days-to-sell by category.
- **Method** — extract sizes, query costs, definitions and caveats.

## Definitions

| Metric | Definition |
|---|---|
| Revenue | `SUM(order_items.sale_price)`, excluding `Cancelled` line items |
| COGS | `SUM(products.cost)` for the same line items |
| Gross profit | Revenue − COGS |
| Gross margin | Gross profit ÷ revenue |
| AOV | Revenue ÷ distinct orders |
| Return rate | Line items with non-null `returned_at` ÷ all line items |
| Repeat rate | Customers with 2+ lifetime orders ÷ all customers |

Cancelled line items are excluded everywhere. Inventory ageing is measured
against the latest `inventory_items.created_at` in the dataset, not today's
date, so the sample stays stable.

## Local setup

Python 3.13 is recommended (Community Cloud support is reliable; 3.14 is not
guaranteed).

```bash
cd ~/Projects/bigquery-ecommerce-dashboard
uv venv --python 3.13 .venv
uv pip install --python .venv/bin/python -r requirements.txt
uv pip install --python .venv/bin/python -r pipeline/requirements.txt
```

### 1. BigQuery sandbox (free, no credit card)

1. Sign in at <https://console.cloud.google.com/> and create a project (or
   select an existing one).
2. Open **BigQuery Studio** and accept the sandbox prompt. The sandbox grants
   1 TiB of queried data per month and needs no billing account.
3. Install the CLI if needed, then authenticate:

   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   gcloud auth application-default login
   ```

`gcloud` is installed at `~/.local/bin/gcloud`. If it is missing:

```bash
curl -fsSL -o /tmp/gcloud.tar.gz \
  https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-cli-linux-x86_64.tar.gz
mkdir -p ~/.local/share/google-cloud-sdk && tar -xzf /tmp/gcloud.tar.gz -C ~/.local/share/google-cloud-sdk --strip-components=1
ln -sf ~/.local/share/google-cloud-sdk/bin/gcloud ~/.local/bin/gcloud
ln -sf ~/.local/share/google-cloud-sdk/bin/bq ~/.local/bin/bq
```

### 2. Extract and run

```bash
export GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID
.venv/bin/python pipeline/extract.py
.venv/bin/streamlit run app.py
```

If Application Default Credentials are not set up, a short-lived access token
works too (valid for about an hour, enough for one extraction):

```bash
export GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID
export GOOGLE_OAUTH_ACCESS_TOKEN="$(gcloud auth print-access-token)"
.venv/bin/python pipeline/extract.py
```

`pipeline/extract.py` prints rows, file size, seconds and GiB scanned per
query. A per-query guard rail (`MAX_BYTES_BILLED`, default 200 GiB) protects
the sandbox quota.

### 3. Refresh

- **Manual:** rerun `pipeline/extract.py` and commit `data/`.
- **Scheduled:** copy `pipeline/refresh-workflow.yml` to
  `.github/workflows/refresh.yml`, then add repository secrets `GCP_PROJECT_ID`
  and `GCP_SA_KEY` (service-account JSON with `roles/bigquery.jobUser` and
  `roles/bigquery.dataViewer`). The weekly Action then refreshes the extracts.
  The template is kept out of the workflow path because pushing a workflow file
  needs the `workflow` GitHub token scope.

The action is optional; the dataset is historical, so a manual refresh is
enough for a portfolio sample.

## Deploy on Streamlit Community Cloud

1. Push this repo to GitHub (private is fine — Community Cloud connects with a
   read-only deploy key).
2. Go to <https://share.streamlit.io> → **Create app** → select the repo,
   branch `main`, main file `app.py`.
3. Set the app subdomain to **`alvintola-retail-dashboard`**.
4. Deploy. No secrets are required because the app reads `data/*.parquet`.

The app is then available at
`https://alvintola-retail-dashboard.streamlit.app`.

## Custom domain on Cloudflare

Streamlit routes by the `Host` header, so a CNAME to `*.streamlit.app` returns
404. `cloudflare-worker/` is a small reverse proxy that fetches the raw app
path (`/~/+/`) by its real hostname and serves it on
`https://dashboard.alvintola.com/`.

```bash
cd cloudflare-worker
npx --yes wrangler@latest deploy
```

The Worker config sets `APP_ORIGIN` and a `dashboard.alvintola.com` custom
domain. If the Streamlit subdomain changes, update `APP_ORIGIN` in
`cloudflare-worker/wrangler.jsonc` and redeploy.

## Repo layout

```
app.py                     Streamlit entry point
dashboard/data.py          loading, filtering, aggregation, KPI definitions
dashboard/charts.py        Plotly figures
dashboard/theme.py         palette, CSS, formatting
pipeline/extract.py        BigQuery → Parquet
pipeline/refresh-workflow.yml  copy to .github/workflows/ to schedule refreshes
sql/*.sql                  one query per extract
data/*.parquet             published extracts (committed)
data/manifest.json         refresh timestamp, rows, bytes scanned
cloudflare-worker/         reverse proxy for dashboard.alvintola.com
```

## Notes

- TheLook is **synthetic** public data. It demonstrates method; it is not a
  claim about a real retailer.
- The Streamlit app is public even if the repository is private. Do not add
  secrets or client data to it.
- BigQuery costs are zero inside the sandbox limit; Streamlit Community Cloud
  is free for public apps.
