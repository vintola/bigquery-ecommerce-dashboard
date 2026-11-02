"""Data loading, filtering and aggregation for the dashboard.

All values come from the Parquet extracts in ``data/``; the app never talks to
BigQuery directly.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"

TABLES = (
    "monthly_kpis",
    "monthly_customer_mix",
    "category_monthly",
    "product_monthly",
    "cohort_retention",
    "customer_orders",
    "traffic_sources",
    "inventory_risk",
)


class MissingData(RuntimeError):
    """Raised when the Parquet extracts have not been generated yet."""


@st.cache_data(show_spinner=False)
def load_table(name: str) -> pd.DataFrame:
    path = DATA_DIR / f"{name}.parquet"
    if not path.exists():
        raise MissingData(
            f"{path.name} is missing. Run `python pipeline/extract.py` "
            "after authenticating with BigQuery."
        )
    frame = pd.read_parquet(path)
    for column in ("month", "cohort_month"):
        if column in frame.columns:
            frame[column] = pd.to_datetime(frame[column])
    return frame


@st.cache_data(show_spinner=False)
def load_manifest() -> dict:
    path = DATA_DIR / "manifest.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def missing_tables() -> list[str]:
    return [name for name in TABLES if not (DATA_DIR / f"{name}.parquet").exists()]


def filter_months(frame: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    if frame.empty:
        return frame
    column = "month" if "month" in frame.columns else "cohort_month"
    return frame[(frame[column] >= start) & (frame[column] <= end)].copy()


def month_options(monthly: pd.DataFrame) -> list[pd.Timestamp]:
    return sorted(monthly["month"].dropna().unique())


def _metrics(frame: pd.DataFrame) -> dict[str, float]:
    if frame.empty:
        return {}
    revenue = float(frame["revenue"].sum())
    cogs = float(frame["cogs"].sum())
    profit = float(frame["gross_profit"].sum()) if "gross_profit" in frame else revenue - cogs
    orders = float(frame["orders"].sum())
    units = float(frame["units"].sum())
    returned = float(frame["returned_units"].sum()) if "returned_units" in frame else 0.0
    return {
        "revenue": revenue,
        "cogs": cogs,
        "gross_profit": profit,
        "gross_margin_pct": (profit / revenue * 100) if revenue else 0.0,
        "orders": orders,
        "units": units,
        "aov": (revenue / orders) if orders else 0.0,
        "return_rate_pct": (returned / units * 100) if units else 0.0,
    }


def kpis(monthly: pd.DataFrame) -> dict[str, float]:
    return _metrics(monthly)


def previous_period_kpis(
    monthly: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp
) -> dict[str, float]:
    """Metrics for the equally long window immediately before ``start``."""
    months = pd.date_range(start, end, freq="MS")
    length = len(months)
    previous_end = start - pd.offsets.MonthBegin(1)
    previous_start = previous_end - pd.DateOffset(months=length - 1)
    window = monthly[(monthly["month"] >= previous_start) & (monthly["month"] <= previous_end)]
    return _metrics(window)


def monthly_from_categories(
    frame: pd.DataFrame,
    start: pd.Timestamp,
    end: pd.Timestamp,
    categories: list[str] | None = None,
) -> pd.DataFrame:
    """Rebuild monthly KPIs from the category extract so the category filter
    also drives the overview. Distinct customer counts are not additive, so
    they are omitted here; the overview does not use them.
    """
    data = filter_months(frame, start, end)
    if categories:
        data = data[data["category"].isin(categories)]
    if data.empty:
        return pd.DataFrame(
            columns=[
                "month",
                "orders",
                "units",
                "returned_units",
                "revenue",
                "cogs",
                "gross_profit",
                "gross_margin_pct",
                "aov",
                "return_rate_pct",
            ]
        )
    grouped = (
        data.groupby("month", as_index=False)
        .agg(
            orders=("orders", "sum"),
            units=("units", "sum"),
            returned_units=("returned_units", "sum"),
            revenue=("revenue", "sum"),
            cogs=("cogs", "sum"),
            gross_profit=("gross_profit", "sum"),
        )
        .sort_values("month")
    )
    grouped["gross_margin_pct"] = (
        grouped["gross_profit"] / grouped["revenue"].replace(0, pd.NA) * 100
    ).fillna(0.0)
    grouped["aov"] = (
        grouped["revenue"] / grouped["orders"].replace(0, pd.NA)
    ).fillna(0.0)
    grouped["return_rate_pct"] = (
        grouped["returned_units"] / grouped["units"].replace(0, pd.NA) * 100
    ).fillna(0.0)
    return grouped


def aggregate_categories(
    frame: pd.DataFrame, categories: list[str] | None = None
) -> pd.DataFrame:
    if frame.empty:
        return frame
    data = frame
    if categories:
        data = data[data["category"].isin(categories)]
    grouped = (
        data.groupby(["category", "department"], as_index=False)
        .agg(
            orders=("orders", "sum"),
            units=("units", "sum"),
            returned_units=("returned_units", "sum"),
            revenue=("revenue", "sum"),
            cogs=("cogs", "sum"),
            gross_profit=("gross_profit", "sum"),
        )
        .sort_values("revenue", ascending=False)
    )
    grouped["gross_margin_pct"] = (
        grouped["gross_profit"] / grouped["revenue"].replace(0, pd.NA) * 100
    ).fillna(0.0)
    grouped["return_rate_pct"] = (
        grouped["returned_units"] / grouped["units"].replace(0, pd.NA) * 100
    ).fillna(0.0)
    grouped["aov"] = (
        grouped["revenue"] / grouped["orders"].replace(0, pd.NA)
    ).fillna(0.0)
    return grouped


def aggregate_products(
    frame: pd.DataFrame, categories: list[str] | None = None
) -> pd.DataFrame:
    if frame.empty:
        return frame
    data = frame
    if categories:
        data = data[data["category"].isin(categories)]
    grouped = (
        data.groupby(
            ["product_id", "name", "brand", "category", "department"], as_index=False
        )
        .agg(
            orders=("orders", "sum"),
            units=("units", "sum"),
            returned_units=("returned_units", "sum"),
            revenue=("revenue", "sum"),
            cogs=("cogs", "sum"),
            gross_profit=("gross_profit", "sum"),
            retail_price=("retail_price", "mean"),
            cost=("cost", "mean"),
            avg_sale_price=("avg_sale_price", "mean"),
            months_active=("month", "nunique"),
        )
    )
    grouped["gross_margin_pct"] = (
        grouped["gross_profit"] / grouped["revenue"].replace(0, pd.NA) * 100
    ).fillna(0.0)
    grouped["return_rate_pct"] = (
        grouped["returned_units"] / grouped["units"].replace(0, pd.NA) * 100
    ).fillna(0.0)
    grouped["units_per_month"] = (
        grouped["units"] / grouped["months_active"].replace(0, pd.NA)
    ).fillna(0.0)
    return grouped


def label_products(frame: pd.DataFrame) -> pd.DataFrame:
    """Assign a decision label from margin and revenue relative to medians."""
    if frame.empty:
        return frame
    data = frame.copy()
    revenue_cut = data["revenue"].median()
    margin_cut = data["gross_margin_pct"].median()
    high_revenue = data["revenue"] >= revenue_cut
    high_margin = data["gross_margin_pct"] >= margin_cut

    labels = []
    for revenue_high, margin_high in zip(high_revenue, high_margin):
        if revenue_high and margin_high:
            labels.append("Promote")
        elif revenue_high and not margin_high:
            labels.append("Review price or cost")
        elif not revenue_high and margin_high:
            labels.append("Niche / hold")
        else:
            labels.append("Remove / de-list")
    data["decision"] = labels
    data.attrs["revenue_cut"] = float(revenue_cut)
    data.attrs["margin_cut"] = float(margin_cut)
    return data


def customer_summary(frame: pd.DataFrame) -> dict[str, float]:
    if frame.empty:
        return {}
    customers = float(frame["customers"].sum())
    repeat = float(frame.loc[frame["orders"] >= 2, "customers"].sum())
    revenue = float(frame["revenue"].sum())
    orders = float((frame["orders"] * frame["customers"]).sum())
    return {
        "customers": customers,
        "repeat_customers": repeat,
        "repeat_rate_pct": (repeat / customers * 100) if customers else 0.0,
        "orders_per_customer": (orders / customers) if customers else 0.0,
        "spend_per_customer": (revenue / customers) if customers else 0.0,
        "revenue": revenue,
    }


def cohort_matrices(frame: pd.DataFrame, max_periods: int = 12) -> tuple[pd.DataFrame, pd.Series]:
    """Return retention (%) by cohort/month and cohort sizes.

    Cohorts smaller than 50 customers are dropped so the heatmap is not noisy.
    """
    if frame.empty:
        return pd.DataFrame(), pd.Series(dtype=float)
    data = frame[frame["period"] <= max_periods].copy()
    pivot = data.pivot_table(
        index="cohort_month", columns="period", values="customers", aggfunc="sum"
    ).fillna(0.0)
    pivot = pivot.sort_index()
    sizes = pivot.get(0, pd.Series(0.0, index=pivot.index))
    keep = sizes[sizes >= 50].index
    pivot = pivot.loc[keep]
    sizes = sizes.loc[keep]
    pct = pivot.div(sizes.replace(0, pd.NA), axis=0) * 100
    return pct.fillna(0.0), sizes
