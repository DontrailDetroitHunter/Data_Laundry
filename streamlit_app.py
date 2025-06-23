import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import json
import io
from fpdf import FPDF

from non_profit import (
    clean_donations,
    clean_volunteers,
    generate_hygiene_report,
    generate_donation_summary,
    generate_volunteer_summary,
    merge_donor_volunteer_data,
    create_pdf_report,
)

# === App Setup ===
st.set_page_config(page_title="Data_Laundry: Mission to Clean")

# === Column Aliases ===
COLUMN_ALIASES = {
    "donor_name": ["giver", "supporter", "donator"],
    "method": ["payment_method", "donation_type"],
    "campaign": ["project", "initiative"],
    "amount": ["donation_amount", "gift", "offering"],
    "date": ["donation_date", "gift_date", "timestamp"],
    "name": ["participant", "student", "volunteer_name"],
    "dept": ["department", "division", "area"],
    "phone": ["phone_number", "contact"],
    "hours": ["time_volunteered", "service_hours"],
}


def suggest_column_mapping(df_columns):
    suggested = {}
    for expected, aliases in COLUMN_ALIASES.items():
        for col in df_columns:
            if expected == col:
                suggested[expected] = col
            elif col.lower() in aliases:
                suggested[expected] = col
    return suggested


def show_column_mapping_interface(df, expected_columns):
    st.subheader("🧩 Match Your Column Names")
    mapping = {}
    for col in expected_columns:
        st.write(f"**Expected column:** `{col}`")
        selected = st.selectbox(
            f"Select column for `{col}`:",
            options=["-- None --"] + list(df.columns),
            key=f"map_{col}",
        )
        if selected != "-- None --":
            mapping[col] = selected
    return mapping


# === Sidebar Branding & Roadmap ===
with st.sidebar:
    st.markdown("## 🧼 Supported File Formats")
    st.markdown("- ✅ CSV (.csv)")
    st.markdown("- ✅ Excel (.xlsx)")

    st.markdown("## 🚧 Coming Soon (Beta/Premium)")
    st.markdown(
        "- ⬜ Text file cleanup (.txt)\n"
        "- ⬜ PDF table extraction (.pdf)\n"
        "- ⬜ OCR for scanned spreadsheets\n"
        "- ⬜ Multi-file uploads\n"
        "- ⬜ Database connectors"
    )
    st.caption("💌 Questions or early access?\n📬 cleandatalaundry@gmail.com")

st.title("🧺 Data_Laundry: Mission to Clean")
st.markdown(
    "Upload your messy donation or volunteer file—we'll clean it, summarize it, and give you export-ready insight."
)


# === File Decoder (CSV + Excel) ===
def decode_file(uploaded_file):
    try:
        if uploaded_file.name.endswith(".csv"):
            text = uploaded_file.getvalue().decode("utf-8")
            return pd.read_csv(io.StringIO(text))
        elif uploaded_file.name.endswith((".xls", ".xlsx")):
            return pd.read_excel(uploaded_file)
        else:
            st.error("Unsupported file type. Please upload a CSV or Excel file.")
            return None
    except Exception as e:
        st.error(f"❌ Could not read file: {e}")
        return None


# === Preview Helper ===
def show_preview(df):
    st.subheader("📋 File Preview")
    st.dataframe(df.head())
    st.write("🧠 Columns:", df.columns.tolist())
    with st.expander("📈 Basic Stats"):
        st.json(df.describe(include="all").fillna("").to_dict())


# === File Upload + Mapping Logic ===
uploaded_file = st.file_uploader("📂 Upload a CSV or Excel File", type=["csv", "xlsx"])
donation_summary = None
volunteer_summary = None
cleaned_donations = None
cleaned_volunteers = None

if uploaded_file:
    df = decode_file(uploaded_file)
    if df is not None:
        df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
        show_preview(df)

        # Define expected column sets
        expected_donation_cols = {"donor_name", "method", "campaign", "amount", "date"}
        expected_volunteer_cols = {"name", "dept", "phone", "hours"}
        is_donation = expected_donation_cols.issubset(df.columns)
        is_volunteer = expected_volunteer_cols.issubset(df.columns)

        # Allow column remapping if mismatch
        if not is_donation and not is_volunteer:
            st.warning(
                "Columns don’t fully match known donation or volunteer templates."
            )
            remap_type = st.radio("Attempt remapping as:", ["Donations", "Volunteers"])
            suggested = suggest_column_mapping(df.columns)

            if remap_type == "Donations":
                remapped = show_column_mapping_interface(df, expected_donation_cols)
                if remapped:
                    df = df.rename(columns=remapped)
                    is_donation = expected_donation_cols.issubset(df.columns)
            else:
                remapped = show_column_mapping_interface(df, expected_volunteer_cols)
                if remapped:
                    df = df.rename(columns=remapped)
                    is_volunteer = expected_volunteer_cols.issubset(df.columns)
        if is_donation:
            action = st.radio(
                "Detected donation dataset. Next step:",
                ["Preview Only", "Clean & Summarize"],
                key="donate_action",
            )

            if action == "Clean & Summarize":
                try:
                    cleaned_donations = clean_donations(df)
                    st.subheader("📊 Cleaned Donations Preview")
                    st.dataframe(cleaned_donations.head())

                    # Date range filter
                    st.markdown("### 📅 Filter Donations by Date")
                    min_date, max_date = (
                        cleaned_donations["date"].min(),
                        cleaned_donations["date"].max(),
                    )
                    start_date, end_date = st.date_input(
                        "Select date range",
                        [min_date, max_date],
                        min_value=min_date,
                        max_value=max_date,
                    )
                    filtered = cleaned_donations[
                        (cleaned_donations["date"] >= pd.to_datetime(start_date))
                        & (cleaned_donations["date"] <= pd.to_datetime(end_date))
                    ]

                    st.metric("💵 Total Donations", f"${filtered['amount'].sum():,.2f}")
                    st.metric("🙋 Unique Donors", filtered["donor_name"].nunique())
                    st.metric("📅 Filtered Range", f"{start_date} → {end_date}")

                    # Chart style toggle
                    chart_type = st.selectbox(
                        "Select chart type", ["Bar", "Line", "Pie"]
                    )
                    fig, ax = plt.subplots()
                    chart_data = (
                        filtered.groupby("campaign")["amount"].sum().sort_values()
                    )

                    if chart_type == "Bar":
                        chart_data.plot(kind="barh", ax=ax, color="#4da6ff")
                    elif chart_type == "Line":
                        chart_data.plot(kind="line", ax=ax, marker="o", color="#4da6ff")
                    else:
                        chart_data.plot(kind="pie", autopct="%1.1f%%", ax=ax)
                        ax.set_ylabel("")

                    ax.set_title("Donations by Campaign")
                    st.pyplot(fig)

                    st.download_button(
                        "⬇ Download Filtered Donations",
                        filtered.to_csv(index=False),
                        file_name="filtered_donations.csv",
                    )

                    hygiene = generate_hygiene_report(df, filtered, "Donations")
                    donation_summary = generate_donation_summary(filtered)

                    st.subheader("🧽 Hygiene Report")
                    st.json(hygiene)
                    st.subheader("📦 Donation Summary")
                    st.json(donation_summary)

                except Exception as e:
                    st.error(f"❌ Donation cleaning failed: {e}")
        elif is_volunteer:
            action = st.radio(
                "Detected volunteer dataset. Next step:",
                ["Preview Only", "Clean & Summarize"],
                key="vol_action",
            )

            if action == "Clean & Summarize":
                try:
                    cleaned_volunteers = clean_volunteers(df)
                    st.subheader("📊 Cleaned Volunteers Preview")
                    st.dataframe(cleaned_volunteers.head())

                    # Department filter
                    st.markdown("### 🏢 Filter by Department")
                    depts = ["All"] + sorted(
                        cleaned_volunteers["dept"].dropna().unique()
                    )
                    selected_dept = st.selectbox("Choose department", depts)
                    filtered = (
                        cleaned_volunteers
                        if selected_dept == "All"
                        else cleaned_volunteers[
                            cleaned_volunteers["dept"] == selected_dept
                        ]
                    )

                    st.metric("🙋 Volunteers", filtered["name"].nunique())
                    st.metric("⏱️ Total Hours", filtered["hours"].sum())
                    st.metric("🏢 Departments", cleaned_volunteers["dept"].nunique())

                    chart_type = st.selectbox("Chart Type", ["Bar", "Line", "Pie"])
                    fig, ax = plt.subplots()
                    chart_data = filtered.groupby("dept")["hours"].sum().sort_values()

                    if chart_type == "Bar":
                        chart_data.plot(kind="barh", ax=ax, color="#82d18e")
                    elif chart_type == "Line":
                        chart_data.plot(kind="line", ax=ax, marker="o", color="#82d18e")
                    else:
                        chart_data.plot(kind="pie", autopct="%1.1f%%", ax=ax)
                        ax.set_ylabel("")

                    ax.set_title("Volunteer Hours by Department")
                    st.pyplot(fig)

                    st.download_button(
                        "⬇ Download Filtered Volunteers",
                        filtered.to_csv(index=False),
                        file_name="filtered_volunteers.csv",
                    )

                    hygiene = generate_hygiene_report(df, filtered, "Volunteers")
                    volunteer_summary = generate_volunteer_summary(filtered)

                    st.subheader("🧽 Hygiene Report")
                    st.json(hygiene)
                    st.subheader("📦 Volunteer Summary")
                    st.json(volunteer_summary)

                except Exception as e:
                    st.error(f"❌ Volunteer cleaning failed: {e}")

# === Merged View & PDF Download ===
if cleaned_donations is not None and cleaned_volunteers is not None:
    st.subheader("🔁 Merged Donor & Volunteer View")
    merged_df = merge_donor_volunteer_data(cleaned_donations, cleaned_volunteers)
    st.dataframe(merged_df.head())

    st.download_button(
        "⬇ Download Merged Dataset",
        merged_df.to_csv(index=False),
        file_name="merged_donor_volunteer.csv",
    )

    pdf_bytes = create_pdf_report(donation_summary, volunteer_summary)
    st.download_button(
        label="📥 Download PDF Summary",
        data=pdf_bytes,
        file_name="nonprofit_summary_report.pdf",
        mime="application/pdf",
    )

# === Footer Branding ===
st.markdown("---")
st.caption("Built by **Dontrail Detroit Hunter** · Powered by Data_Laundry 🧺")
