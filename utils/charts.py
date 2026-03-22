import altair as alt
import pandas as pd

# -----------------------------
# YEAR-OVER-YEAR SPEND
# -----------------------------
def cost_trend_chart(df: pd.DataFrame):
    if df.empty:
        return alt.Chart(
            pd.DataFrame({"Month_Num": [], "$ Amount": [], "Year": []})
        ).mark_line()

    chart = (
        alt.Chart(df)
        .mark_line(point=True)
        .encode(
            x=alt.X("Month_Num:O", title="Month"),
            y=alt.Y("$ Amount:Q", title="Spend ($)"),
            color=alt.Color("Year:N", title="Year"),
            tooltip=["Year", "Month", "$ Amount"]
        )
        .properties(height=300)
    )
    return chart


# -----------------------------
# YEAR-OVER-YEAR USAGE
# -----------------------------
def usage_trend_chart(df: pd.DataFrame):
    if df.empty:
        return alt.Chart(
            pd.DataFrame({"Month_Num": [], "Usage": [], "Year": []})
        ).mark_line()

    chart = (
        alt.Chart(df)
        .mark_line(point=True)
        .encode(
            x=alt.X("Month_Num:O", title="Month"),
            y=alt.Y("Usage:Q", title="Usage"),
            color=alt.Color("Year:N", title="Year"),
            tooltip=["Year", "Month", "Usage"]
        )
        .properties(height=300)
    )
    return chart


# -----------------------------
# SPEND BY UTILITY (BY YEAR)
# -----------------------------
def spend_by_utility_chart(df: pd.DataFrame):
    if df.empty:
        return alt.Chart(
            pd.DataFrame({"Utility": [], "$ Amount": [], "Year": []})
        ).mark_bar()

    chart = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X("Utility:N", title="Utility"),
            y=alt.Y("$ Amount:Q", title="Spend ($)"),
            color=alt.Color("Year:N", title="Year"),
            tooltip=["Utility", "Year", "$ Amount"]
        )
        .properties(height=300)
    )
    return chart
