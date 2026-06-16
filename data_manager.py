import os
from typing import BinaryIO

import pandas as pd


REQUIRED_COLUMNS = ["التاريخ", "الاسم", "المندوب", "الصنف", "الفرع", "المبيعات"]

COLUMN_ALIASES = {
    "date": "التاريخ",
    "customer": "الاسم",
    "representative": "المندوب",
    "product": "الصنف",
    "branch": "الفرع",
    "sales_amount": "المبيعات",
    "sales": "المبيعات",
    "amount": "المبيعات",
    "التاريخ": "التاريخ",
    "تاريخ": "التاريخ",
    "العميل": "الاسم",
    "الاسم": "الاسم",
    "اسم_العميل": "الاسم",
    "اسم العميل": "الاسم",
    "المندوب": "المندوب",
    "مندوب": "المندوب",
    "الصنف": "الصنف",
    "المنتج": "الصنف",
    "الفرع": "الفرع",
    "المبيعات": "المبيعات",
    "قيمة_المبيعات": "المبيعات",
    "قيمة المبيعات": "المبيعات",
}


class DataValidationError(ValueError):
    """خطأ واضح يظهر للمستخدم عند وجود مشكلة في ملف البيانات."""


def _normalize_column_name(column: object) -> str:
    return str(column).strip().lower().replace(" ", "_")


def _rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    renamed = {}
    for column in df.columns:
        raw = str(column).strip()
        normalized = _normalize_column_name(column)
        renamed[column] = COLUMN_ALIASES.get(normalized, COLUMN_ALIASES.get(raw, raw))
    return df.rename(columns=renamed)


def load_excel_file(file: BinaryIO) -> pd.DataFrame:
    """تحميل ملف Excel بصيغتي xlsx و xls ثم تنظيفه وتجهيزه للتحليل."""
    filename = getattr(file, "name", "")
    extension = os.path.splitext(filename)[1].lower()

    if extension not in [".xlsx", ".xls"]:
        raise DataValidationError("صيغة الملف غير مدعومة. يرجى رفع ملف Excel بصيغة xlsx أو xls.")

    try:
        engine = "openpyxl" if extension == ".xlsx" else "xlrd"
        df = pd.read_excel(file, engine=engine)
    except Exception as exc:
        raise DataValidationError(f"تعذر قراءة ملف Excel: {exc}") from exc

    return clean_sales_data(df)


def clean_sales_data(df: pd.DataFrame) -> pd.DataFrame:
    """تنظيف أسماء الأعمدة وتوحيد التاريخ وإنشاء أعمدة الفترة الزمنية."""
    if df.empty:
        raise DataValidationError("ملف Excel فارغ ولا يحتوي على بيانات.")

    df = df.copy()
    df.columns = [str(column).strip() for column in df.columns]
    df = _rename_columns(df)

    missing = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing:
        raise DataValidationError("الأعمدة المطلوبة غير موجودة: " + "، ".join(missing))

    df = df[REQUIRED_COLUMNS].copy()

    for column in ["الاسم", "المندوب", "الصنف", "الفرع"]:
        df[column] = df[column].astype(str).str.strip()
        df[column] = df[column].replace({"": "غير محدد", "nan": "غير محدد", "None": "غير محدد"})

    df["التاريخ"] = pd.to_datetime(df["التاريخ"], errors="coerce")
    invalid_dates = int(df["التاريخ"].isna().sum())
    if invalid_dates:
        raise DataValidationError(f"يوجد {invalid_dates} صف يحتوي على تاريخ غير صالح.")

    df["المبيعات"] = pd.to_numeric(df["المبيعات"], errors="coerce")
    invalid_sales = int(df["المبيعات"].isna().sum())
    if invalid_sales:
        raise DataValidationError(f"يوجد {invalid_sales} صف يحتوي على قيمة مبيعات غير صالحة.")

    df = df.dropna(subset=["التاريخ", "المبيعات"])
    df = df[df["المبيعات"] >= 0]
    if df.empty:
        raise DataValidationError("لا توجد بيانات صالحة بعد التنظيف.")

    df["السنة"] = df["التاريخ"].dt.year.astype(int)
    df["الشهر"] = df["التاريخ"].dt.month.astype(int)
    df["الربع"] = df["التاريخ"].dt.quarter.astype(int)
    df["النصف"] = ((df["الشهر"] - 1) // 6 + 1).astype(int)
    df["شهر_نصي"] = df["التاريخ"].dt.strftime("%Y-%m")

    return df


def get_available_years(df: pd.DataFrame) -> list[int]:
    return sorted(df["السنة"].dropna().astype(int).unique().tolist(), reverse=True)
