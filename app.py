import streamlit as st

from calculations import (
    compare_branches,
    compare_customers,
    compare_products,
    compare_representatives,
    customer_segments,
    dashboard_metrics,
    executive_insights,
    generate_alerts,
    pareto_analysis,
    trend_monthly,
    trend_yearly,
)
from data_manager import DataValidationError, get_available_years, load_excel_file
from excel_export import export_to_excel
from pdf_export import export_to_pdf
from ui import (
    chart_bar,
    chart_line,
    chart_pareto,
    chart_pie,
    chart_treemap,
    render_alerts,
    render_analysis_table,
    render_dashboard,
    render_filters,
    render_header,
    render_insights,
    setup_page,
)


def _render_tab(title: str, frame, chart_title: str, key: str):
    st.subheader(title)
    render_analysis_table(frame, key)
    col1, col2 = st.columns(2)
    col1.plotly_chart(chart_bar(frame, f"{chart_title} - Bar Chart"), use_container_width=True)
    col2.plotly_chart(chart_pie(frame, f"{chart_title} - Pie Chart"), use_container_width=True)
    st.plotly_chart(chart_treemap(frame, f"{chart_title} - Treemap"), use_container_width=True)


def _render_customer_analysis(customers):
    st.subheader("تحليل العملاء")
    segments = customer_segments(customers)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("العملاء الجدد", len(segments["new"]))
    col2.metric("العملاء المفقودون", len(segments["lost"]))
    col3.metric("العملاء المتنامون", len(segments["growing"]))
    col4.metric("العملاء المتراجعون", len(segments["declining"]))

    segment_tabs = st.tabs(["الجدد", "المفقودون", "المتنامون", "المتراجعون"])
    with segment_tabs[0]:
        st.dataframe(segments["new"], use_container_width=True, hide_index=True)
    with segment_tabs[1]:
        st.dataframe(segments["lost"], use_container_width=True, hide_index=True)
    with segment_tabs[2]:
        st.dataframe(segments["growing"], use_container_width=True, hide_index=True)
    with segment_tabs[3]:
        st.dataframe(segments["declining"], use_container_width=True, hide_index=True)


def main():
    setup_page()
    render_header()

    uploaded_file = st.file_uploader("ارفع ملف Excel", type=["xlsx", "xls"])
    if uploaded_file is None:
        st.info("يرجى رفع ملف Excel يحتوي على أعمدة المبيعات المطلوبة للبدء.")
        return

    try:
        df = load_excel_file(uploaded_file)
    except DataValidationError as exc:
        st.error(str(exc))
        return
    except Exception as exc:
        st.error(f"حدث خطأ غير متوقع أثناء معالجة الملف: {exc}")
        return

    years = get_available_years(df)
    if len(years) < 1:
        st.error("لا توجد سنوات صالحة في ملف البيانات.")
        return

    current_year, previous_year, comparison_type, period_value = render_filters(years)

    metrics = dashboard_metrics(df, current_year, previous_year, comparison_type, period_value)
    customers = compare_customers(df, current_year, previous_year, comparison_type, period_value)
    products = compare_products(df, current_year, previous_year, comparison_type, period_value)
    representatives = compare_representatives(df, current_year, previous_year, comparison_type, period_value)
    branches = compare_branches(df, current_year, previous_year, comparison_type, period_value)

    results = {
        "customers": customers,
        "products": products,
        "representatives": representatives,
        "branches": branches,
    }

    #===================تعليق مركز التنبيهات =============================
    #alerts = generate_alerts(results)
    insights = executive_insights(results)

    render_dashboard(metrics)

    export_col1, export_col2 = st.columns(2)
    excel_file = export_to_excel(metrics, customers, products, representatives, branches, insights)
    export_col1.download_button(
        "تصدير Excel",
        excel_file,
        file_name="al_asa_sales_analysis.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    pdf_file = export_to_pdf(metrics, customers, products, representatives, branches, insights)
    export_col2.download_button(
        "تصدير PDF",
        pdf_file,
        file_name="al_asa_sales_analysis.pdf",
        mime="application/pdf",
    )

    render_insights(insights)
    #render_alerts(alerts)

    #=======================================================================

    tabs = st.tabs(["العملاء", "المنتجات", "المناديب", "الفروع", "Pareto", "Trend Analysis"])
    with tabs[0]:
        _render_tab("العملاء", customers, "تحليل العملاء", "customers")
        _render_customer_analysis(customers)
    with tabs[1]:
        _render_tab("المنتجات", products, "تحليل المنتجات", "products")
    with tabs[2]:
        _render_tab("المناديب", representatives, "تحليل المناديب", "representatives")
    with tabs[3]:
        _render_tab("الفروع", branches, "تحليل الفروع", "branches")
    with tabs[4]:
        st.subheader("تحليل Pareto")
        pareto_customers = pareto_analysis(df, "الاسم", current_year, comparison_type, period_value)
        pareto_products = pareto_analysis(df, "الصنف", current_year, comparison_type, period_value)
        col1, col2 = st.columns(2)
        col1.plotly_chart(chart_pareto(pareto_customers, "Pareto - العملاء"), use_container_width=True)
        col2.plotly_chart(chart_pareto(pareto_products, "Pareto - المنتجات"), use_container_width=True)
        st.write("أفضل العملاء المساهمين في 80% من المبيعات")
        st.dataframe(pareto_customers[pareto_customers["ضمن_80"]], use_container_width=True, hide_index=True)
        st.write("أفضل المنتجات المساهمة في 80% من المبيعات")
        st.dataframe(pareto_products[pareto_products["ضمن_80"]], use_container_width=True, hide_index=True)
    with tabs[5]:
        st.subheader("Trend Analysis")
        monthly = trend_monthly(df)
        yearly = trend_yearly(df)
        st.plotly_chart(chart_line(monthly), use_container_width=True)
        st.line_chart(yearly, x="السنة", y="المبيعات")


if __name__ == "__main__":
    main()

#====================كود التذييل=======================
st.markdown(
    """
    <div style='text-align:center; color:#AAAAAA; font-size:12px;'>
        المهندس المالي : عزت العصعص | أتمتة الأعمال بالذكاء الاصطناعي<br>
        للتواصل : 777884468
    </div>
    """,
    unsafe_allow_html=True
)
#==================================================

# python -m streamlit run app.py
