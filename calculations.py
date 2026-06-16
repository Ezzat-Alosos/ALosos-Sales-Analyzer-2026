from __future__ import annotations

from typing import Optional

import pandas as pd


DIMENSION_COLUMNS = {
    "customers": "الاسم",
    "products": "الصنف",
    "representatives": "المندوب",
    "branches": "الفرع",
}


def _period_column(comparison_type: str) -> Optional[str]:
    mapping = {
        "شهر": "الشهر",
        "ربع سنوي": "الربع",
        "نصف سنوي": "النصف",
        "سنة كاملة": None,
    }
    return mapping.get(comparison_type)


def _filter_period(df: pd.DataFrame, year: int, comparison_type: str, period_value: Optional[int]) -> pd.DataFrame:
    filtered = df[df["السنة"] == int(year)]
    column = _period_column(comparison_type)
    if column and period_value is not None:
        filtered = filtered[filtered[column] == int(period_value)]
    return filtered


def _growth_percentage(current: pd.Series, previous: pd.Series) -> pd.Series:
    # عند السابق = 0 والحالي أكبر من 0 نعرض 100% لتجنب القسمة على صفر.
    result = ((current - previous) / previous.replace(0, pd.NA)) * 100
    result = result.fillna(0)
    result = result.mask((previous == 0) & (current > 0), 100)
    return result.astype(float)


def compare_dimension(
    df: pd.DataFrame,
    dimension_column: str,
    current_year: int,
    previous_year: int,
    comparison_type: str = "سنة كاملة",
    period_value: Optional[int] = None,
) -> pd.DataFrame:
    current_df = _filter_period(df, current_year, comparison_type, period_value)
    previous_df = _filter_period(df, previous_year, comparison_type, period_value)

    current = current_df.groupby(dimension_column, dropna=False)["المبيعات"].sum()
    previous = previous_df.groupby(dimension_column, dropna=False)["المبيعات"].sum()

    result = pd.DataFrame({"الحالي": current, "السابق": previous}).fillna(0)
    result["الفرق"] = result["الحالي"] - result["السابق"]
    result["النسبة"] = _growth_percentage(result["الحالي"], result["السابق"])
    result = result.reset_index().rename(columns={dimension_column: "الاسم"})
    return result.sort_values("الحالي", ascending=False).reset_index(drop=True)


def compare_customers(df, current_year, previous_year, comparison_type="سنة كاملة", period_value=None):
    return compare_dimension(df, "الاسم", current_year, previous_year, comparison_type, period_value)


def compare_products(df, current_year, previous_year, comparison_type="سنة كاملة", period_value=None):
    return compare_dimension(df, "الصنف", current_year, previous_year, comparison_type, period_value)


def compare_representatives(df, current_year, previous_year, comparison_type="سنة كاملة", period_value=None):
    return compare_dimension(df, "المندوب", current_year, previous_year, comparison_type, period_value)


def compare_branches(df, current_year, previous_year, comparison_type="سنة كاملة", period_value=None):
    return compare_dimension(df, "الفرع", current_year, previous_year, comparison_type, period_value)


def dashboard_metrics(df: pd.DataFrame, current_year: int, previous_year: int, comparison_type: str, period_value=None) -> dict:
    current_df = _filter_period(df, current_year, comparison_type, period_value)
    previous_df = _filter_period(df, previous_year, comparison_type, period_value)
    current_total = float(current_df["المبيعات"].sum())
    previous_total = float(previous_df["المبيعات"].sum())
    difference = current_total - previous_total
    growth = 0 if previous_total == 0 else (difference / previous_total) * 100
    if previous_total == 0 and current_total > 0:
        growth = 100
    return {
        "current_total": current_total,
        "previous_total": previous_total,
        "difference": difference,
        "growth": growth,
        "customers_count": int(current_df["الاسم"].nunique()),
        "products_count": int(current_df["الصنف"].nunique()),
        "representatives_count": int(current_df["المندوب"].nunique()),
        "branches_count": int(current_df["الفرع"].nunique()),
    }


def pareto_analysis(df: pd.DataFrame, dimension_column: str, current_year: int, comparison_type: str, period_value=None) -> pd.DataFrame:
    current_df = _filter_period(df, current_year, comparison_type, period_value)
    grouped = current_df.groupby(dimension_column)["المبيعات"].sum().sort_values(ascending=False).reset_index()
    grouped = grouped.rename(columns={dimension_column: "الاسم", "المبيعات": "الحالي"})
    total = grouped["الحالي"].sum()
    grouped["النسبة"] = 0 if total == 0 else grouped["الحالي"] / total * 100
    grouped["النسبة_التراكمية"] = grouped["النسبة"].cumsum()
    grouped["ضمن_80"] = grouped["النسبة_التراكمية"] <= 80
    return grouped


def customer_segments(customers_df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    return {
        "new": customers_df[(customers_df["السابق"] == 0) & (customers_df["الحالي"] > 0)],
        "lost": customers_df[(customers_df["السابق"] > 0) & (customers_df["الحالي"] == 0)],
        "growing": customers_df[customers_df["النسبة"] > 0],
        "declining": customers_df[customers_df["النسبة"] < 0],
    }


def trend_monthly(df: pd.DataFrame) -> pd.DataFrame:
    return df.groupby("شهر_نصي", as_index=False)["المبيعات"].sum().sort_values("شهر_نصي")


def trend_yearly(df: pd.DataFrame) -> pd.DataFrame:
    return df.groupby("السنة", as_index=False)["المبيعات"].sum().sort_values("السنة")


def generate_alerts(results: dict[str, pd.DataFrame], threshold: float = 30) -> pd.DataFrame:
    labels = {
        "customers": "عميل",
        "products": "منتج",
        "representatives": "مندوب",
        "branches": "فرع",
    }
    rows = []
    for key, frame in results.items():
        label = labels.get(key, key)
        for _, row in frame.iterrows():
            if row["النسبة"] <= -threshold:
                rows.append({"النوع": "خطر", "الفئة": label, "الاسم": row["الاسم"], "الرسالة": f"{label} انخفض أكثر من {threshold:.0f}%", "النسبة": row["النسبة"]})
            elif row["النسبة"] >= threshold:
                rows.append({"النوع": "فرصة", "الفئة": label, "الاسم": row["الاسم"], "الرسالة": f"{label} حقق نمو أكثر من {threshold:.0f}%", "النسبة": row["النسبة"]})
    return pd.DataFrame(rows, columns=["النوع", "الفئة", "الاسم", "الرسالة", "النسبة"])


def executive_insights(results: dict[str, pd.DataFrame]) -> pd.DataFrame:
    labels = {
        "customers": "عميل",
        "products": "منتج",
        "representatives": "مندوب",
        "branches": "فرع",
    }
    rows = []
    for key, frame in results.items():
        if frame.empty:
            continue
        best = frame.sort_values("الفرق", ascending=False).iloc[0]
        worst = frame.sort_values("الفرق", ascending=True).iloc[0]
        rows.append({"المؤشر": f"أفضل {labels[key]}", "الاسم": best["الاسم"], "القيمة": best["الحالي"], "النسبة": best["النسبة"]})
        rows.append({"المؤشر": f"أسوأ {labels[key]}", "الاسم": worst["الاسم"], "القيمة": worst["الحالي"], "النسبة": worst["النسبة"]})
    return pd.DataFrame(rows, columns=["المؤشر", "الاسم", "القيمة", "النسبة"])
