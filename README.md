# 🧺 Data_Laundry: Mission to Clean
![R Markdown Supported](https://img.shields.io/badge/RMarkdown-Supported-75AADB?logo=rstudio&logoColor=white)

**Data_Laundry** is an AI-assisted data hygiene and summarization app designed for nonprofits. Upload raw donor or volunteer data (in `.csv` or `.xlsx`) and instantly receive:

---

## ⚡ Features

- ✅ Clean messy donor or volunteer data
- ✅ Adaptive column mapping (handles “donor” = “giver,” “offering,” etc.)
- ✅ Campaign + department-level summaries
- ✅ Date-range and department filtering
- ✅ Dynamic charts (bar, pie, line)
- ✅ Merged donor/volunteer views
- ✅ Downloadable CSVs & professional PDF summary
- ✅ Built on Streamlit, works in-browser

---

## 🗂 Supported File Formats

| Type           | Format       | Status         |
|----------------|--------------|----------------|
| 📄 CSV         | `.csv`       | ✅ Supported   |
| 📊 Excel       | `.xlsx`      | ✅ Supported   |
| 📃 Text        | `.txt`       | 🚧 Coming Soon |
| 📄 PDF Tables  | `.pdf`       | 🚧 Coming Soon |
| 🖼 Scans/OCR    | `.jpg`, `.png` | 🚧 Future Premium |

---

## 🚀 Live Demo

🧼 Stream, summarize, and export instantly  
👉 [Launch on Streamlit Cloud](https://datalaundry.streamlit.app) ← *(replace with your actual link)*

---

## 🛠️ Install Locally

### 🖼 Sample Output

Here’s what the R Markdown report looks like when you click **Knit** in RStudio:

![Sample HTML report](https://rmarkdown.rstudio.com/images/rmarkdown-html.png)


## 📄 Optional R Markdown Report (for R Users)

If you use **R or RStudio** and want to generate a clean, styled HTML report from your cleaned CSV, we’ve got you covered.

➡️ [Download the R Markdown template](https://github.com/DontrailDetroitHunter/Data_Laundry/raw/main/rmd_reports/data_laundry_report.Rmd)

### 🧼 What it does
This template lets you:
- Load a cleaned CSV from Data Laundry
- View a summary of columns, missing values, and basic statistics
- Knit the results into a **sharable HTML report** for stakeholders or teammates

### 🚀 How to use it
1. Open [RStudio](https://posit.co/download/rstudio-desktop/)
2. Download the `.Rmd` file above
3. Update the file path in this line:
   ```r
   data <- read_csv("cleaned_data.csv")
## 📄 Optional R Markdown Report (for R Users)

If you use **R or RStudio** and want to generate a clean, styled HTML report from your cleaned CSV, we’ve got you covered.

➡️ [Download the R Markdown template](https://github.com/DontrailDetroitHunter/Data_Laundry/raw/main/rmd_reports/data_laundry_report.Rmd)

4. Click Knit to generate your HTML report

🔒 No R coding experience needed—plug in your file and click Knit.

```bash
git clone https://github.com/DontrailDetroitHunter/Data_Laundry.git
cd Data_Laundry
pip install -r requirements.txt
streamlit run streamlit_app.py
