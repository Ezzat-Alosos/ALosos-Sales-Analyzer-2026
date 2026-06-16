# نظام العصعص لتحليل المبيعات

## Al-osos Professional Sales Analyzer 2026

تطبيق Streamlit احترافي لتحليل ملفات Excel الخاصة بالمبيعات، مع لوحات مؤشرات تنفيذية، مقارنات زمنية، رسوم Plotly، تحليل Pareto، تنبيهات تشغيلية، وتصدير تقارير Excel و PDF.

## التشغيل

```bash
pip install -r requirements.txt
streamlit run app.py
```

## أعمدة ملف Excel المطلوبة

يدعم النظام الأعمدة العربية التالية:

- التاريخ
- الاسم
- المندوب
- الصنف
- الفرع
- المبيعات

ويدعم تحويل الأعمدة الإنجليزية التالية تلقائياً:

- date -> التاريخ
- customer -> الاسم
- representative -> المندوب
- product -> الصنف
- branch -> الفرع
- sales_amount -> المبيعات

## الملفات

- `app.py`: نقطة التشغيل الرئيسية للتطبيق.
- `data_manager.py`: تحميل وتنظيف والتحقق من بيانات Excel.
- `calculations.py`: جميع الحسابات والتحليلات.
- `ui.py`: واجهة Streamlit والرسوم البيانية.
- `excel_export.py`: تصدير تقرير Excel متعدد الأوراق.
- `pdf_export.py`: إنشاء تقرير PDF عربي باستخدام ReportLab.
- `requirements.txt`: حزم التشغيل المطلوبة.

## ملاحظات

- التطبيق مبني بالكامل بواسطة Streamlit.
- لا يستخدم Tkinter أو CustomTkinter أو PyQt.
- لا يحتوي على بيانات تجريبية داخل التطبيق؛ يعمل مباشرة على الملف الذي يرفعه المستخدم.
