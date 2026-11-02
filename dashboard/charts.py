"""Plotly figures for the dashboard. All figures use the portfolio's palette."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from dashboard import theme

DECISION_COLORS = {
    "Promote": theme.ACCENT,
    "Niche / hold": theme.COOL,
    "Review price or cost": theme.AMBER,
    "Remove / de-list": theme.RED,
}


def _base(fig: go.Figure, height: int = 380, showlegend: bool = True) -> go.Figure:
    fig.update_layout(
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=theme.SANS, color=theme.MUTED_STRONG, size=12),
        margin=dict(l=8, r=8, t=34, b=8),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.03,
            x=0,
            font=dict(size=11, color=theme.MUTED_STRONG),
        ),
        hoverlabel=dict(
            bgcolor=theme.PANEL_2,
            bordercolor=theme.LINE,
            font=dict(color=theme.TEXT, family=theme.SANS),
        ),
        showlegend=showlegend,
        bargap=0.28,
    )
    fig.update_xaxes(
        showgrid=False,
        linecolor=theme.LINE,
        tickfont=dict(color=theme.MUTED),
        zeroline=False,
    )
    fig.update_yaxes(
        gridcolor=theme.GRID,
        linecolor=theme.LINE,
        tickfont=dict(color=theme.MUTED),
        zeroline=False,
    )
    return fig


def empty(message: str = "No data for this selection.") -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        showarrow=False,
        font=dict(color=theme.MUTED, size=13),
        x=0.5,
        y=0.5,
        xref="paper",
        yref="paper",
    )
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return _base(fig, height=260, showlegend=False)


def revenue_margin(monthly: pd.DataFrame) -> go.Figure:
    if monthly.empty:
        return empty()
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_bar(
        x=monthly["month"],
        y=monthly["revenue"],
        name="Revenue",
        marker_color=theme.ACCENT,
        marker_line_width=0,
        opacity=0.9,
        customdata=monthly[["gross_profit", "gross_margin_pct", "orders"]].to_numpy(),
        hovertemplate=(
            "%{x|%b %Y}<br>Revenue $%{y:,.0f}"
            "<br>Gross profit $%{customdata[0]:,.0f}"
            "<br>Margin %{customdata[1]:.1f}%"
            "<br>Orders %{customdata[2]:,.0f}<extra></extra>"
        ),
    )
    fig.add_scatter(
        x=monthly["month"],
        y=monthly["gross_margin_pct"],
        name="Gross margin",
        mode="lines+markers",
        line=dict(color=theme.COOL, width=2.4),
        marker=dict(size=5, color=theme.COOL, line=dict(width=0)),
        hovertemplate="%{x|%b %Y}<br>Gross margin %{y:.1f}%<extra></extra>",
        secondary_y=True,
    )
    fig.update_yaxes(
        title_text="Revenue",
        tickprefix="$",
        tickformat="~s",
        title_font=dict(size=11, color=theme.MUTED),
        secondary_y=False,
    )
    fig.update_yaxes(
        title_text="Gross margin",
        ticksuffix="%",
        title_font=dict(size=11, color=theme.MUTED),
        showgrid=False,
        secondary_y=True,
    )
    return _base(fig, height=390)


def category_bars(categories: pd.DataFrame, limit: int = 10) -> go.Figure:
    if categories.empty:
        return empty()
    data = categories.head(limit).sort_values("revenue")
    fig = go.Figure(
        go.Bar(
            x=data["revenue"],
            y=data["category"],
            orientation="h",
            marker_color=theme.ACCENT,
            marker_line_width=0,
            opacity=0.9,
            customdata=data[["gross_margin_pct", "orders", "return_rate_pct"]].to_numpy(),
            hovertemplate=(
                "%{y}<br>Revenue $%{x:,.0f}"
                "<br>Margin %{customdata[0]:.1f}%"
                "<br>Orders %{customdata[1]:,.0f}"
                "<br>Returns %{customdata[2]:.1f}%<extra></extra>"
            ),
        )
    )
    fig.update_xaxes(tickprefix="$", tickformat="~s")
    fig.update_layout(margin=dict(l=8, r=8, t=18, b=8))
    return _base(fig, height=360, showlegend=False)


def customer_mix(mix: pd.DataFrame) -> go.Figure:
    if mix.empty:
        return empty()
    fig = go.Figure()
    fig.add_bar(
        x=mix["month"],
        y=mix["new_customers"],
        name="New",
        marker_color=theme.ACCENT,
        hovertemplate="%{x|%b %Y}<br>New customers %{y:,.0f}<extra></extra>",
    )
    fig.add_bar(
        x=mix["month"],
        y=mix["returning_customers"],
        name="Returning",
        marker_color=theme.COOL,
        hovertemplate="%{x|%b %Y}<br>Returning customers %{y:,.0f}<extra></extra>",
    )
    fig.update_layout(barmode="stack")
    fig.update_yaxes(title_text="Customers", title_font=dict(size=11, color=theme.MUTED))
    return _base(fig, height=360)


def product_matrix(products: pd.DataFrame) -> go.Figure:
    if products.empty:
        return empty()
    fig = go.Figure()
    max_units = max(float(products["units"].max()), 1.0)
    for label, group in products.groupby("decision"):
        sizes = group["units"].clip(lower=1)
        fig.add_scatter(
            x=group["revenue"],
            y=group["gross_margin_pct"],
            mode="markers",
            name=label,
            marker=dict(
                size=sizes,
                sizemode="area",
                sizeref=2.0 * max_units / (26.0**2),
                sizemin=4,
                color=DECISION_COLORS.get(label, theme.MUTED),
                opacity=0.72,
                line=dict(width=0.8, color=theme.BG),
            ),
            customdata=group[["name", "brand", "units", "units_per_month"]].to_numpy(),
            hovertemplate=(
                "<b>%{customdata[0]}</b>"
                "<br>%{customdata[1]}"
                "<br>Revenue $%{x:,.0f}"
                "<br>Gross margin %{y:.1f}%"
                "<br>Units %{customdata[2]:,.0f}"
                "<br>Units / month %{customdata[3]:.1f}<extra></extra>"
            ),
        )
    revenue_cut = products.attrs.get("revenue_cut")
    margin_cut = products.attrs.get("margin_cut")
    if revenue_cut:
        fig.add_vline(
            x=revenue_cut,
            line=dict(color=theme.LINE, width=1, dash="dot"),
        )
    if margin_cut:
        fig.add_hline(
            y=margin_cut,
            line=dict(color=theme.LINE, width=1, dash="dot"),
        )
    fig.update_xaxes(
        title_text="Revenue over the selected period (log scale)",
        type="log",
        tickprefix="$",
        tickformat="~s",
        title_font=dict(size=11, color=theme.MUTED),
    )
    fig.update_yaxes(
        title_text="Gross margin",
        ticksuffix="%",
        title_font=dict(size=11, color=theme.MUTED),
    )
    return _base(fig, height=470)


def cohort_heatmap(pct: pd.DataFrame, sizes: pd.Series) -> go.Figure:
    if pct.empty:
        return empty("Not enough cohort history for this selection.")
    if 0 in pct.columns:
        pct = pct.drop(columns=[0])
    if pct.empty:
        return empty("Not enough cohort history for this selection.")
    pct = pct.tail(36)
    sizes = sizes.reindex(pct.index)
    z = pct.to_numpy()
    x = [str(int(column)) for column in pct.columns]
    y = [cohort.strftime("%Y-%m") for cohort in pct.index]
    counts = pct.mul(sizes, axis=0).round(0)
    zmax = max(10.0, min(100.0, float(z.max())))
    fig = go.Figure(
        go.Heatmap(
            z=z,
            x=x,
            y=y,
            colorscale=[
                [0.0, "#12151c"],
                [0.2, "#263118"],
                [0.45, "#536f1f"],
                [0.7, "#96bd3a"],
                [1.0, theme.ACCENT_BRIGHT],
            ],
            zmin=0,
            zmax=zmax,
            xgap=2,
            ygap=2,
            customdata=counts.to_numpy(),
            hovertemplate=(
                "Cohort %{y}<br>Month %{x} after first order"
                "<br>Retained %{z:.1f}% (%{customdata:,.0f} customers)<extra></extra>"
            ),
            colorbar=dict(
                title=dict(text="Retained", font=dict(size=10, color=theme.MUTED)),
                ticksuffix="%",
                tickfont=dict(size=10, color=theme.MUTED),
                outlinewidth=0,
                thickness=10,
            ),
        )
    )
    fig.update_xaxes(title_text="Months since first order", title_font=dict(size=11, color=theme.MUTED))
    fig.update_yaxes(title_text="Acquisition cohort", title_font=dict(size=11, color=theme.MUTED))
    height = max(300, min(720, 26 * len(y) + 90))
    return _base(fig, height=height, showlegend=False)


def customer_orders(frame: pd.DataFrame) -> go.Figure:
    if frame.empty:
        return empty()
    data = frame.copy()
    head = data[data["orders"] <= 10].copy()
    tail = data[data["orders"] > 10]
    if not tail.empty:
        head = pd.concat(
            [
                head,
                pd.DataFrame(
                    [
                        {
                            "orders": "11+",
                            "customers": tail["customers"].sum(),
                            "revenue": tail["revenue"].sum(),
                        }
                    ]
                ),
            ],
            ignore_index=True,
        )
    total_revenue = data["revenue"].sum()
    head["revenue_share"] = (head["revenue"].cumsum() / total_revenue * 100) if total_revenue else 0
    x = [str(int(value)) if not isinstance(value, str) else value for value in head["orders"]]
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_bar(
        x=x,
        y=head["customers"],
        name="Customers",
        marker_color=theme.ACCENT,
        opacity=0.9,
        hovertemplate="%{x} order(s)<br>%{y:,.0f} customers<extra></extra>",
    )
    fig.add_scatter(
        x=x,
        y=head["revenue_share"],
        name="Cumulative revenue",
        mode="lines+markers",
        line=dict(color=theme.COOL, width=2),
        marker=dict(size=5, color=theme.COOL),
        hovertemplate="%{x} order(s)<br>%{y:.1f}% of revenue<extra></extra>",
        secondary_y=True,
    )
    fig.update_yaxes(title_text="Customers", title_font=dict(size=11, color=theme.MUTED), secondary_y=False)
    fig.update_yaxes(
        title_text="Cumulative revenue",
        ticksuffix="%",
        showgrid=False,
        range=[0, 105],
        title_font=dict(size=11, color=theme.MUTED),
        secondary_y=True,
    )
    fig.update_xaxes(title_text="Lifetime orders per customer", title_font=dict(size=11, color=theme.MUTED))
    return _base(fig, height=380)


def traffic_bars(frame: pd.DataFrame) -> go.Figure:
    if frame.empty:
        return empty()
    data = frame.sort_values("revenue")
    fig = go.Figure(
        go.Bar(
            x=data["revenue"],
            y=data["traffic_source"],
            orientation="h",
            marker_color=theme.COOL,
            opacity=0.9,
            customdata=data[["customers", "orders", "aov"]].to_numpy(),
            hovertemplate=(
                "%{y}<br>Revenue $%{x:,.0f}"
                "<br>Customers %{customdata[0]:,.0f}"
                "<br>Orders %{customdata[1]:,.0f}"
                "<br>AOV $%{customdata[2]:,.2f}<extra></extra>"
            ),
        )
    )
    fig.update_xaxes(tickprefix="$", tickformat="~s")
    fig.update_layout(margin=dict(l=8, r=8, t=18, b=8))
    return _base(fig, height=320, showlegend=False)


def inventory_bars(frame: pd.DataFrame) -> go.Figure:
    if frame.empty:
        return empty()
    data = frame.sort_values("unsold_cost")
    fig = go.Figure(
        go.Bar(
            x=data["unsold_cost"],
            y=data["category"],
            orientation="h",
            marker=dict(
                color=data["unsold_pct"],
                colorscale=[[0, "#2a3320"], [1, theme.ACCENT]],
                cmin=float(data["unsold_pct"].min()),
                cmax=float(data["unsold_pct"].max()),
                colorbar=dict(
                    title=dict(text="Unsold", font=dict(size=10, color=theme.MUTED)),
                    ticksuffix="%",
                    tickfont=dict(size=10, color=theme.MUTED),
                    outlinewidth=0,
                    thickness=10,
                ),
            ),
            customdata=data[
                ["unsold_pct", "unsold_units", "units", "avg_days_to_sell", "oldest_unsold_days"]
            ].to_numpy(),
            hovertemplate=(
                "<b>%{y}</b>"
                "<br>Unsold cost $%{x:,.0f}"
                "<br>Unsold %{customdata[0]:.1f}% (%{customdata[1]:,.0f} of %{customdata[2]:,.0f} units)"
                "<br>Avg days to sell %{customdata[3]:.1f}"
                "<br>Oldest unsold %{customdata[4]:,.0f} days<extra></extra>"
            ),
        )
    )
    fig.update_xaxes(
        title_text="Capital in unsold stock",
        tickprefix="$",
        tickformat="~s",
        title_font=dict(size=11, color=theme.MUTED),
    )
    fig.update_yaxes(title_text="")
    return _base(fig, height=440, showlegend=False)


def monthly_units(monthly: pd.DataFrame) -> go.Figure:
    if monthly.empty:
        return empty()
    fig = go.Figure(
        go.Scatter(
            x=monthly["month"],
            y=monthly["units"],
            mode="lines",
            line=dict(color=theme.ACCENT, width=2),
            fill="tozeroy",
            fillcolor="rgba(207,244,90,0.10)",
            hovertemplate="%{x|%b %Y}<br>Units %{y:,.0f}<extra></extra>",
        )
    )
    fig.update_yaxes(title_text="Units", title_font=dict(size=11, color=theme.MUTED))
    return _base(fig, height=280, showlegend=False)
