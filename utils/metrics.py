import pandas as pd

def portfolio_metrics(df: pd.DataFrame) -> dict:
    metrics = {
        "years": df["Year"].nunique() if "Year" in df.columns else None,
        "total_spend": df["$ Amount"].sum() if "$ Amount" in df.columns else None,
        "total_usage": df["Usage"].sum() if "Usage" in df.columns else None,
        "bills_count": len(df),
    }
    return metrics
