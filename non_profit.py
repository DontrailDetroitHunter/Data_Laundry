import pandas as pd
from fpdf import FPDF


def clean_donations(df):
    df = df.copy()
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

    print("🧪 Columns after normalization:", df.columns.tolist())

    # ✅ Safety check for required columns
    required_columns = ["donor_name", "method", "campaign", "amount", "date"]
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise ValueError(f"Missing expected column(s): {missing}")

    # Standardize text fields
    df["donor_name"] = df["donor_name"].astype(str).str.strip().str.title()
    df["method"] = df["method"].astype(str).str.strip().str.lower()
    df["campaign"] = (
        df["campaign"].astype(str).str.strip().str.title().fillna("Uncategorized")
    )

    # Fix currency symbols and convert amount to float
    df["amount"] = df["amount"].replace(r"[\$,]", "", regex=True).astype(float)

    # Parse and standardize dates
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    # Drop rows with missing or zero donation amounts or donor names
    df = df.dropna(subset=["donor_name", "amount", "date"])
    df = df[df["amount"] > 0]

    return df


def clean_volunteers(df):
    df = df.copy()
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

    print("🧪 Columns after normalization:", df.columns.tolist())

    # ✅ Check for required columns
    required_columns = ["name", "dept", "phone", "hours"]
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise ValueError(f"Missing expected column(s): {missing}")

    # Standardize text fields
    df["name"] = df["name"].astype(str).str.strip().str.title()
    df["dept"] = df["dept"].astype(str).str.strip().str.title()
    df["phone"] = df["phone"].astype(str).str.replace(r"\D", "", regex=True)

    # Drop rows missing key info
    df = df.dropna(subset=["name", "hours"])

    return df


def generate_hygiene_report(original_df, cleaned_df, name):
    original_rows = len(original_df)
    cleaned_rows = len(cleaned_df)
    removed_rows = original_rows - cleaned_rows
    null_counts = original_df.isnull().sum()

    report = {
        "Dataset": name,
        "Original Rows": original_rows,
        "Cleaned Rows": cleaned_rows,
        "Rows Removed": removed_rows,
        "Missing Values (by column)": null_counts[null_counts > 0].to_dict(),
    }
    return report


def generate_donation_summary(df):
    df = df.copy()
    summary = {
        "total_donations": df["amount"].sum(),
        "unique_donors": df["donor_name"].nunique(),
        "campaign_totals": df.groupby("campaign")["amount"]
        .sum()
        .sort_values(ascending=False)
        .to_dict(),
        "donations_by_method": df["method"].value_counts().to_dict(),
        "donations_by_month": {
            str(k): v
            for k, v in (
                df["date"].dt.to_period("M").value_counts().sort_index().items()
            )
        },
    }
    return summary


def generate_volunteer_summary(df):
    df = df.copy()
    summary = {
        "total_hours": df["hours"].sum(),
        "volunteers_count": df["name"].nunique(),
        "departments_involved": df["dept"].nunique(),
        "hours_by_department": df.groupby("dept")["hours"]
        .sum()
        .sort_values(ascending=False)
        .to_dict(),
        "volunteers_by_phone_length": df["phone"]
        .str.len()
        .value_counts()
        .sort_index()
        .to_dict(),
    }
    return summary


def merge_donor_volunteer_data(donors_df, volunteers_df):
    donors = donors_df.copy()
    volunteers = volunteers_df.copy()

    donors["donor_name"] = donors["donor_name"].astype(str).str.strip().str.lower()
    volunteers["name"] = volunteers["name"].astype(str).str.strip().str.lower()

    return pd.merge(
        donors,
        volunteers,
        left_on="donor_name",
        right_on="name",
        how="inner",  # use "left" if you want all donors with volunteer info where available
        suffixes=("_donor", "_volunteer"),
    )


def create_pdf_report(donation_summary, volunteer_summary):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 10, "Nonprofit Data Summary", ln=True)
    pdf.ln(5)

    if donation_summary:
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, "Donation Summary", ln=True)
        pdf.set_font("Arial", size=11)
        for key, value in donation_summary.items():
            pdf.multi_cell(0, 10, f"{key}: {value}")
        pdf.ln(5)

    if volunteer_summary:
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, "Volunteer Summary", ln=True)
        pdf.set_font("Arial", size=11)
        for key, value in volunteer_summary.items():
            pdf.multi_cell(0, 10, f"{key}: {value}")

    return pdf.output(dest="S").encode("latin1")
