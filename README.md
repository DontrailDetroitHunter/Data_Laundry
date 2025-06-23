# 🧺 Data_Laundry: Mission to Clean

**Data_Laundry** is an AI-assisted data hygiene and summarization app designed for nonprofits. Upload raw donor or volunteer data (in `.csv` or `.xlsx`) and instantly receive:

- Cleaned, analysis-ready datasets
- Summary insights with visual charts
- Exportable hygiene reports (JSON + PDF)
- Donor-volunteer merge analysis

Whether you're a nonprofit analyst, volunteer coordinator, or development director juggling spreadsheet chaos—**Data_Laundry helps you clean smarter, not harder.**

---

## ⚡ Features

✅ Clean messy donor or volunteer data  
✅ Adaptive column mapping (handles “donor” = “giver,” “offering,” etc.)  
✅ Campaign + department-level summaries  
✅ Date-range and department filtering  
✅ Dynamic charts (bar, pie, line)  
✅ Merged donor/volunteer views  
✅ Downloadable CSVs & professional PDF summary  
✅ Built on Streamlit, works in-browser  

---

## 🗂 Supported File Formats

| Type        | Format        | Status      |
|-------------|---------------|-------------|
| 📄 CSV       | `.csv`         | ✅ Supported |
| 📊 Excel     | `.xlsx`        | ✅ Supported |
| 📃 Text      | `.txt`         | 🚧 Coming Soon |
| 📄 PDF Tables | `.pdf`        | 🚧 Coming Soon |
| 🖼 Scans/OCR | `.jpg`, `.png` | 🚧 Future Premium |

---

## 🚀 Live Demo

> 🧼 Stream, summarize, and export instantly  
> [Launch on Streamlit Cloud](https://data-laundry.streamlit.app)

---

## 🛠️ Install Locally

```bash
git clone https://github.com/YOUR_USERNAME/data_laundry.git
cd data_laundry
pip install -r requirements.txt
streamlit run streamlit_app.py
