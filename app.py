from __future__ import annotations

import pandas as pd
import streamlit as st

from dashboard import charts, data, theme

st.set_page_config(
    page_title="TheLook eCommerce — Retail performance dashboard",
    page_icon="https://alvintola.com/favicon.svg",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(theme.CSS, unsafe_allow_html=True)


def delta_pct(current: float, previous: float) -> str | None:
    if not previous:
        return None
    return f"{(current - previous) / previous * 100:+.1f}% vs prior period"


def delta_pp(current: float, previous: float) -> str | None:
    if previous is None:
        return None
    return f"{current - previous:+.1f} pp vs prior period"


manifest = data.load_manifest()
missing = data.missing_tables()
if missing:
    st.markdown(
        f"""
        <div class="dash-header">
          <p class="dash-eyebrow">Sample dashboard · TheLook eCommerce · BigQuery public data</p>
          <h1 class="dash-title">Retail performance, margin and inventory</h1>
          <p class="dash-sub">The dashboard is wired up but the data extracts are missing.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.warning("Missing data files: " + ", ".join(f"`{name}.parquet`" for name in missing))
    st.markdown("Run the extract once BigQuery credentials are configured:")
    st.code(
        "export GOOGLE_CLOUD_PROJECT=your-project-id\npython pipeline/extract.py",
        language="bash",
    )
    st.stop()

monthly_all = data.load_table("monthly_kpis")
mix_all = data.load_table("monthly_customer_mix")
category_all = data.load_table("category_monthly")
products_all = data.load_table("product_monthly")
cohort_all = data.load_table("cohort_retention")
customer_orders = data.load_table("customer_orders")
traffic = data.load_table("traffic_sources")
inventory = data.load_table("inventory_risk")

refreshed = str(manifest.get("extracted_at", ""))[:10] or "unknown"
st.markdown(
    f"""
    <div class="dash-header">
      <p class="dash-eyebrow">Sample dashboard · TheLook eCommerce · BigQuery public data</p>
      <h1 class="dash-title">Retail performance, margin and inventory</h1>
      <p class="dash-sub">
        A live Streamlit dashboard built from Google's public
        <code>bigquery-public-data.thelook_ecommerce</code> dataset. It runs the
        same loop as client work: define the KPI, ingest the source, find the
        driver, and make the next action obvious. Built by
        <a href="{theme.PORTFOLIO_URL}" target="_blank" rel="noopener">Al Vintola</a>.
      </p>
    </div>
    """,
    unsafe_allow_html=True,
)

months = data.month_options(monthly_all)
month_labels = [pd.Timestamp(month).strftime("%b %Y") for month in months]
category_options = sorted(category_all["category"].dropna().unique())

st.sidebar.markdown("### Filters")
start_index, end_index = st.sidebar.select_slider(
    "Period",
    options=list(range(len(months))),
    value=(max(0, len(months) - 24), len(months) - 1),
    format_func=lambda index: month_labels[index],
)
st.sidebar.caption(
    "The category filter lives in the Products & margin tab. Customer order "
    "distribution, traffic sources and inventory are lifetime/snapshot views."
)
st.sidebar.divider()
st.sidebar.markdown("### Source")
st.sidebar.caption(
    f"Public synthetic dataset. Extracted {refreshed}. "
    f"Revenue excludes cancelled line items."
)
st.sidebar.markdown(
    f'<p class="dash-link"><a href="{theme.PORTFOLIO_URL}" target="_blank" rel="noopener">Portfolio</a>'
    f' &nbsp;·&nbsp; <a href="{theme.REPO_URL}" target="_blank" rel="noopener">Source code</a></p>',
    unsafe_allow_html=True,
)

start, end = months[start_index], months[end_index]
monthly = data.filter_months(monthly_all, start, end)
mix = data.filter_months(mix_all, start, end)
category_period = data.filter_months(category_all, start, end)
categories = data.aggregate_categories(category_period)
products_period = data.filter_months(products_all, start, end)

current = data.kpis(monthly)
previous = data.previous_period_kpis(monthly_all, start, end)
has_previous = bool(previous) and previous.get("revenue", 0) > 0

overview_tab, products_tab, customers_tab, inventory_tab, method_tab = st.tabs(
    ["Overview", "Products & margin", "Customers", "Inventory", "Method"]
)

with overview_tab:
    first = st.columns(3)
    first[0].metric(
        "Revenue", theme.compact_money(current.get("revenue", 0)),
        delta_pct(current.get("revenue", 0), previous.get("revenue", 0))
        if has_previous
        else None,
    )
    first[1].metric(
        "Gross profit", theme.compact_money(current.get("gross_profit", 0)),
        delta_pct(current.get("gross_profit", 0), previous.get("gross_profit", 0))
        if has_previous
        else None,
    )
    first[2].metric(
        "Gross margin", theme.pct(current.get("gross_margin_pct", 0)),
        delta_pp(current.get("gross_margin_pct", 0), previous.get("gross_margin_pct", 0))
        if has_previous
        else None,
    )
    second = st.columns(3)
    second[0].metric(
        "Orders", theme.number(current.get("orders", 0)),
        delta_pct(current.get("orders", 0), previous.get("orders", 0))
        if has_previous
        else None,
    )
    second[1].metric(
        "Average order value", theme.money(current.get("aov", 0)),
        delta_pct(current.get("aov", 0), previous.get("aov", 0)) if has_previous else None,
    )
    second[2].metric(
        "Return rate", theme.pct(current.get("return_rate_pct", 0)),
        delta_pp(current.get("return_rate_pct", 0), previous.get("return_rate_pct", 0))
        if has_previous
        else None,
        delta_color="inverse",
    )

    st.markdown("#### Revenue and margin by month")
    st.plotly_chart(
        charts.revenue_margin(monthly),
        width="stretch",
        config={"displayModeBar": False},
    )

    left, right = st.columns([1.35, 1])
    with left:
        st.markdown("#### Where revenue comes from")
        st.plotly_chart(
            charts.category_bars(categories),
            width="stretch",
            config={"displayModeBar": False},
        )
    with right:
        st.markdown("#### New vs returning customers")
        st.plotly_chart(
            charts.customer_mix(mix),
            width="stretch",
            config={"displayModeBar": False},
        )

    if not categories.empty:
        top_profit = categories.sort_values("gross_profit", ascending=False).iloc[0]
        material = categories[categories["revenue"] >= categories["revenue"].median()]
        weak_margin = material.sort_values("gross_margin_pct").iloc[0]
        weak_returns = categories.sort_values("return_rate_pct", ascending=False).iloc[0]
        st.markdown(
            f"""
            <div class="insight">
              <span class="label">What the period says</span>
              <strong>{top_profit['category']}</strong> contributes the most gross profit
              ({theme.compact_money(top_profit['gross_profit'])}, {top_profit['gross_margin_pct']:.1f}% margin).
              Among categories with material revenue, <strong>{weak_margin['category']}</strong>
              has the thinnest margin at {weak_margin['gross_margin_pct']:.1f}%.
              The highest return rate is <strong>{weak_returns['category']}</strong>
              at {weak_returns['return_rate_pct']:.1f}% — a fulfilment or product-fit question,
              not just a pricing one.
            </div>
            """,
            unsafe_allow_html=True,
        )

with products_tab:
    st.markdown("#### Product decisions, not just product reports")
    st.caption(
        "Each dot is one of the 500 highest-revenue products. The quadrants split at the "
        "median revenue and median gross margin for the selected period. Size is units sold."
    )
    selected_categories = st.multiselect(
        "Filter products by category",
        options=category_options,
        default=[],
        placeholder="All categories",
        key="product_category_filter",
    )
    products = data.aggregate_products(products_period, selected_categories)
    products = data.label_products(products)
    filtered_categories = data.aggregate_categories(category_period, selected_categories)

    decision_counts = products["decision"].value_counts()
    decision_row = st.columns(4)
    for column, label in zip(
        decision_row,
        ["Promote", "Review price or cost", "Niche / hold", "Remove / de-list"],
    ):
        column.metric(label, f"{int(decision_counts.get(label, 0)):,}")

    st.plotly_chart(
        charts.product_matrix(products),
        width="stretch",
        config={"displayModeBar": False},
    )

    table_left, table_right = st.columns([1.35, 1])
    with table_left:
        st.markdown("#### Top products by gross profit")
        top = products.sort_values("gross_profit", ascending=False).head(20)
        display = top[
            [
                "name",
                "brand",
                "category",
                "revenue",
                "gross_margin_pct",
                "units",
                "units_per_month",
                "return_rate_pct",
                "decision",
            ]
        ].rename(
            columns={
                "name": "Product",
                "brand": "Brand",
                "category": "Category",
                "revenue": "Revenue",
                "gross_margin_pct": "Margin %",
                "units": "Units",
                "units_per_month": "Units / month",
                "return_rate_pct": "Returns %",
                "decision": "Decision",
            }
        )
        st.dataframe(
            display,
            hide_index=True,
            width="stretch",
            column_config={
                "Revenue": st.column_config.NumberColumn(format="$%.0f"),
                "Margin %": st.column_config.NumberColumn(format="%.1f"),
                "Units": st.column_config.NumberColumn(format="%d"),
                "Units / month": st.column_config.NumberColumn(format="%.1f"),
                "Returns %": st.column_config.NumberColumn(format="%.1f"),
            },
        )
    with table_right:
        st.markdown("#### Category economics")
        category_display = filtered_categories[
            [
                "category",
                "department",
                "revenue",
                "gross_margin_pct",
                "return_rate_pct",
                "orders",
            ]
        ].rename(
            columns={
                "category": "Category",
                "department": "Department",
                "revenue": "Revenue",
                "gross_margin_pct": "Margin %",
                "return_rate_pct": "Returns %",
                "orders": "Orders",
            }
        )
        st.dataframe(
            category_display,
            hide_index=True,
            width="stretch",
            column_config={
                "Revenue": st.column_config.NumberColumn(format="$%.0f"),
                "Margin %": st.column_config.NumberColumn(format="%.1f"),
                "Returns %": st.column_config.NumberColumn(format="%.1f"),
                "Orders": st.column_config.NumberColumn(format="%d"),
            },
        )

with customers_tab:
    summary = data.customer_summary(customer_orders)
    st.markdown("#### Lifetime customer behaviour")
    st.caption(
        "Computed across the full dataset, not the period filter — repeat behaviour "
        "needs the whole history to be meaningful."
    )
    row = st.columns(4)
    row[0].metric("Repeat rate", theme.pct(summary.get("repeat_rate_pct", 0)))
    row[1].metric("Customers", theme.number(summary.get("customers", 0)))
    row[2].metric("Orders per customer", f"{summary.get('orders_per_customer', 0):.2f}")
    row[3].metric("Spend per customer", theme.money(summary.get("spend_per_customer", 0)))

    left, right = st.columns([1.3, 1])
    with left:
        st.markdown("#### How much of the base repeats?")
        st.plotly_chart(
            charts.customer_orders(customer_orders),
            width="stretch",
            config={"displayModeBar": False},
        )
    with right:
        st.markdown("#### Revenue by acquisition source")
        st.plotly_chart(
            charts.traffic_bars(traffic),
            width="stretch",
            config={"displayModeBar": False},
        )

    st.markdown("#### Cohort retention")
    st.caption(
        "Share of each acquisition cohort that ordered again in months 1–12. "
        "Cohorts smaller than 50 customers are hidden; the last 36 cohorts are shown."
    )
    retention, cohort_sizes = data.cohort_matrices(
        data.filter_months(cohort_all, start, end)
    )
    st.plotly_chart(
        charts.cohort_heatmap(retention, cohort_sizes),
        width="stretch",
        config={"displayModeBar": False},
    )

    st.markdown("#### Acquisition source detail")
    traffic_display = traffic.rename(
        columns={
            "traffic_source": "Source",
            "customers": "Customers",
            "orders": "Orders",
            "revenue": "Revenue",
            "aov": "AOV",
            "orders_per_customer": "Orders / customer",
        }
    )
    st.dataframe(
        traffic_display,
        hide_index=True,
        width="stretch",
        column_config={
            "Revenue": st.column_config.NumberColumn(format="$%.0f"),
            "AOV": st.column_config.NumberColumn(format="$%.2f"),
            "Orders / customer": st.column_config.NumberColumn(format="%.2f"),
        },
    )

with inventory_tab:
    unsold_units = float(inventory["unsold_units"].sum())
    total_units = float(inventory["units"].sum())
    unsold_cost = float(inventory["unsold_cost"].sum())
    sold_units = total_units - unsold_units
    avg_days = (
        float((inventory["avg_days_to_sell"].fillna(0) * (inventory["units"] - inventory["unsold_units"])).sum())
        / sold_units
        if sold_units
        else 0.0
    )
    st.markdown("#### Stock ageing and tied-up capital")
    st.caption(
        "Snapshot of the public inventory table. Ageing is measured against the most "
        "recent inventory record in the dataset, so the sample stays stable."
    )
    row = st.columns(4)
    row[0].metric("Unsold units", theme.number(unsold_units))
    row[1].metric(
        "Unsold share",
        theme.pct((unsold_units / total_units * 100) if total_units else 0),
    )
    row[2].metric("Capital in unsold stock", theme.compact_money(unsold_cost))
    row[3].metric("Avg days to sell", f"{avg_days:,.0f}")

    st.plotly_chart(
        charts.inventory_bars(inventory),
        width="stretch",
        config={"displayModeBar": False},
    )

    inventory_display = inventory.rename(
        columns={
            "category": "Category",
            "units": "Units",
            "unsold_units": "Unsold units",
            "unsold_pct": "Unsold %",
            "unsold_cost": "Unsold cost",
            "avg_days_to_sell": "Avg days to sell",
            "oldest_unsold_days": "Oldest unsold (days)",
        }
    )
    st.dataframe(
        inventory_display,
        hide_index=True,
        width="stretch",
        column_config={
            "Unsold cost": st.column_config.NumberColumn(format="$%.0f"),
            "Unsold %": st.column_config.NumberColumn(format="%.1f"),
            "Avg days to sell": st.column_config.NumberColumn(format="%.1f"),
        },
    )

with method_tab:
    st.markdown("#### How this sample is built")
    st.markdown(
        """
        <div class="method-grid">
          <div class="method-card">
            <p class="step">01 / Ingest</p>
            <h4>BigQuery public data</h4>
            <p>Parameterised SQL runs against <code>bigquery-public-data.thelook_ecommerce</code>
            and writes small Parquet extracts. The app never holds BigQuery credentials.</p>
          </div>
          <div class="method-card">
            <p class="step">02 / Model</p>
            <h4>Business definitions</h4>
            <p>Revenue is sale price, COGS is product cost, and returns use
            <code>returned_at</code>. Every ratio is recomputed after aggregation to avoid
            averaging an average.</p>
          </div>
          <div class="method-card">
            <p class="step">03 / Publish</p>
            <h4>Streamlit Community Cloud</h4>
            <p>The app reads the committed extracts, so load is fast, cheap and
            reproducible. A scheduled GitHub Action can refresh the data.</p>
          </div>
          <div class="method-card">
            <p class="step">04 / Decide</p>
            <h4>Decision layer</h4>
            <p>Products are labelled promote, hold, review or remove from margin and
            revenue relative to the medians — a starting point for a pricing conversation.</p>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("#### Extracts")
    files = manifest.get("files", {})
    rows = []
    for name, meta in files.items():
        rows.append(
            {
                "Extract": name,
                "SQL": meta.get("sql", ""),
                "Rows": meta.get("rows", 0),
                "Size": f"{meta.get('bytes', 0) / 1024:,.0f} KB",
                "Query time": f"{meta.get('query_seconds', 0):,.1f}s",
                "Scanned": f"{meta.get('bytes_processed', 0) / 1024**3:,.2f} GB",
            }
        )
    if rows:
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    st.caption(
        f"Source: {manifest.get('source', 'bigquery-public-data.thelook_ecommerce')} · "
        f"Extracted {refreshed} · GCP project {manifest.get('project', '—')}"
    )

    st.markdown("#### Reproduce it")
    st.code(
        "export GOOGLE_CLOUD_PROJECT=your-project-id\n"
        "python pipeline/extract.py\n"
        "streamlit run app.py",
        language="bash",
    )
    st.markdown(
        f"""
        <div class="insight">
          <span class="label">Read this before quoting a number</span>
          TheLook is a <strong>synthetic</strong> public dataset. It is useful for
          demonstrating method, not for making claims about a real retailer.
          Revenue excludes cancelled line items; COGS uses the product cost table;
          returns are line items with a non-null <code>returned_at</code>.
          See the SQL in <a href="{theme.REPO_URL}/tree/main/sql" target="_blank" rel="noopener">sql/</a>
          for every definition.
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<p class="dash-link">'
        f'<a href="{theme.SOURCE_URL}" target="_blank" rel="noopener">Dataset documentation</a>'
        f' &nbsp;·&nbsp; <a href="{theme.REPO_URL}" target="_blank" rel="noopener">Source code</a>'
        f' &nbsp;·&nbsp; <a href="{theme.PORTFOLIO_URL}" target="_blank" rel="noopener">Portfolio</a>'
        f"</p>",
        unsafe_allow_html=True,
    )

st.divider()
st.caption(
    "Sample dashboard · TheLook eCommerce (BigQuery public data) · "
    "Built by Al Vintola · No client data is used."
)
