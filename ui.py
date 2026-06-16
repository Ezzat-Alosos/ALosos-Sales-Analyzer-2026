import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


def setup_page():
    st.set_page_config(page_title="نظام العصعص لتحليل المبيعات", page_icon="📊", layout="wide")
    st.markdown(
        """
        <style>
        html, body, [class*="css"] { direction: rtl; text-align: right; font-family: "Segoe UI", Tahoma, sans-serif; }
        .stMetric { background: #f8fafc; border: 1px solid #e2e8f0; padding: 14px; border-radius: 8px; }
        .danger { color: #b91c1c; font-weight: 700; }
        .success { color: #15803d; font-weight: 700; }
        </style>
        """,
        unsafe_allow_html=True,
    )

#==============================================================

def render_header():
    st.markdown(
        """
        <style>
        html, body, [class*="css"] {
            direction: rtl;
            text-align: right;
            font-family: "Segoe UI", Tahoma, sans-serif;
            background-color: #f8fafc;
        }

        .stApp {
            background: #f8fafc;
        }

        .stMetric {
            background: #ffffff;
            border: 1px solid #e5e7eb;
            padding: 14px;
            border-radius: 10px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }

        .success { color: #16a34a; font-weight: 700; }
        .danger  { color: #dc2626; font-weight: 700; }

        section[data-testid="stSidebar"] {
            background-color: #f1f5f9;
        }

        h1, h2, h3 {
            color: #0f172a;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # 👇 هذا هو المهم (العنوان نفسه)
    st.markdown(
        """
        <div style="text-align:center; margin-top:20px;">
            <h1 style="margin:0;">
                نظام العصعص لتحليل المبيعات
            </h1>
            <p style="color:#64748b; margin-top:5px;">
                Al-osos Professional Sales Analyzer 2026
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )



#================================================================
def render_filters(years):
    col1, col2, col3, col4 = st.columns(4)
    current_year = col1.selectbox("السنة الحالية", years, index=0)
    previous_default = 1 if len(years) > 1 else 0
    previous_year = col2.selectbox("السنة السابقة", years, index=previous_default)
    comparison_type = col3.selectbox("نوع المقارنة", ["شهر", "ربع سنوي", "نصف سنوي", "سنة كاملة"], index=3)
    period_value = None
    if comparison_type == "شهر":
        period_value = col4.selectbox("الشهر", list(range(1, 13)))
    elif comparison_type == "ربع سنوي":
        period_value = col4.selectbox("الربع", [1, 2, 3, 4])
    elif comparison_type == "نصف سنوي":
        period_value = col4.selectbox("النصف", [1, 2])
    else:
        col4.info("سنة كاملة")
    return current_year, previous_year, comparison_type, period_value


def render_dashboard(metrics):
    cols = st.columns(4)
    cols[0].metric("إجمالي المبيعات الحالية", f"{metrics['current_total']:,.2f}")
    cols[1].metric("إجمالي المبيعات السابقة", f"{metrics['previous_total']:,.2f}")
    cols[2].metric("إجمالي الفرق", f"{metrics['difference']:,.2f}")
    cols[3].metric("نسبة النمو", f"{metrics['growth']:,.2f}%")
    cols = st.columns(4)
    cols[0].metric("عدد العملاء", metrics["customers_count"])
    cols[1].metric("عدد المنتجات", metrics["products_count"])
    cols[2].metric("عدد المناديب", metrics["representatives_count"])
    cols[3].metric("عدد الفروع", metrics["branches_count"])


def render_analysis_table(df, key):
    search = st.text_input("بحث", key=f"search_{key}")
    shown = df.copy()
    if search:
        shown = shown[shown["الاسم"].astype(str).str.contains(search, case=False, na=False)]
    st.dataframe(shown, use_container_width=True, hide_index=True)
    st.download_button(
        "تنزيل CSV",
        shown.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"{key}.csv",
        mime="text/csv",
        key=f"download_{key}",
    )


def chart_bar(df, title):
    data = df.head(15)
    return px.bar(data, x="الاسم", y="الحالي", title=title, text_auto=".2s")


def chart_line(monthly_df):
    return px.line(monthly_df, x="شهر_نصي", y="المبيعات", markers=True, title="اتجاه المبيعات الشهري")


def chart_pie(df, title):
    return px.pie(df.head(10), names="الاسم", values="الحالي", title=title, hole=0.35)


def chart_treemap(df, title):
    return px.treemap(df.head(30), path=["الاسم"], values="الحالي", title=title)


def chart_pareto(pareto_df, title):
    fig = go.Figure()
    fig.add_bar(x=pareto_df["الاسم"], y=pareto_df["الحالي"], name="المبيعات")
    fig.add_scatter(x=pareto_df["الاسم"], y=pareto_df["النسبة_التراكمية"], name="النسبة التراكمية", yaxis="y2")
    fig.update_layout(
        title=title,
        yaxis=dict(title="المبيعات"),
        yaxis2=dict(title="النسبة التراكمية", overlaying="y", side="right", range=[0, 100]),
    )
    return fig


def render_alerts(alerts_df):
    st.subheader("مركز التنبيهات")
    if alerts_df.empty:
        st.success("لا توجد تنبيهات حرجة أو فرص نمو كبيرة حالياً.")
        return
    for _, row in alerts_df.iterrows():
        if row["النوع"] == "خطر":
            st.error(f"{row['الرسالة']}: {row['الاسم']} ({row['النسبة']:.2f}%)")
        else:
            st.success(f"{row['الرسالة']}: {row['الاسم']} ({row['النسبة']:.2f}%)")


def render_insights(insights_df):
    st.subheader("Executive Insights")
    if insights_df.empty:
        st.info("لا توجد مؤشرات كافية.")
        return
    cols = st.columns(4)
    for idx, (_, row) in enumerate(insights_df.iterrows()):
        cols[idx % 4].metric(row["المؤشر"], row["الاسم"], f"{row['النسبة']:.2f}%")
