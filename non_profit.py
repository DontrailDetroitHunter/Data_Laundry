import streamlit as st
import pandas as pd
from fpdf import FPDF
import difflib


def clean_donations(df):
    df = df.copy()

    # --- Normalize column names ---
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

    print("🧪 Columns after normalization:", df.columns.tolist())

    # --- Dynamic donor name aliasing ---
    name_aliases = ["donor_name", "name", "full_name"]
    for alias in name_aliases:
        if alias in df.columns:
            df = df.rename(columns={alias: "donor_name"})
            break

    # --- Use 'dept' as fallback for campaign if needed ---
    if "campaign" not in df.columns and "dept" in df.columns:
        df["campaign"] = df["dept"]

    # --- Fill missing optional columns ---
    if "campaign" not in df.columns:
        df["campaign"] = "Uncategorized"
    if "method" not in df.columns:
        df["method"] = "unspecified"

    # ✅ Require only essential columns now
    required_columns = ["donor_name", "amount", "date"]
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise ValueError(f"Missing expected column(s): {missing}")

    # --- Standardize text fields ---
    df["donor_name"] = df["donor_name"].astype(str).str.strip().str.title()
    df["method"] = df["method"].astype(str).str.strip().str.lower()
    df["campaign"] = (
        df["campaign"].astype(str).str.strip().str.title().fillna("Uncategorized")
    )

    # --- Clean and convert 'amount' ---
    df["amount"] = (
        df["amount"]
        .astype(str)
        .str.replace("$", "", regex=False)
        .str.replace(",", "", regex=False)
        .str.strip()
    )
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")

    # --- Parse dates ---
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    # --- Drop invalid rows ---
    initial_rows = len(df)
    df = df.dropna(subset=["donor_name", "amount", "date"])
    df = df[df["amount"] > 0]
    dropped = initial_rows - len(df)
    if dropped > 0:
        print(
            f"🧽 Dropped {dropped} row(s) due to missing or zero amounts, donor names, or invalid dates."
        )

    return df


def clean_volunteers(df):
    df = df.copy()
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

    print("🧪 Columns after normalization:", df.columns.tolist())

    # --- Dynamic column alias mapping ---
    col_map = {}

    for col in df.columns:
        col_clean = col.lower().strip()
        if col_clean in ["name", "volunteer_name", "full_name"]:
            col_map[col] = "name"
        elif col_clean in ["dept", "department", "division"]:
            col_map[col] = "dept"
        elif col_clean in ["phone", "phone_number", "contact"]:
            col_map[col] = "phone"
        elif col_clean in ["hours", "volunteer_hours", "time"]:
            col_map[col] = "hours"

    df = df.rename(columns=col_map)

    # ✅ Check for required columns
    required_columns = ["name", "dept", "phone", "hours"]
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise ValueError(f"Missing expected column(s): {missing}")

    # --- Standardize fields ---
    df["name"] = df["name"].astype(str).str.strip().str.title()
    df["dept"] = df["dept"].astype(str).str.strip().str.title()
    df["phone"] = df["phone"].astype(str).str.replace(r"\D", "", regex=True)
    df["hours"] = pd.to_numeric(df["hours"], errors="coerce")

    # ✅ Map department to campaign for charting
    df["campaign"] = df["dept"].fillna("Unassigned").astype(str).str.strip().str.title()

    # --- Drop rows missing key info ---
    initial_rows = len(df)
    df = df.dropna(subset=["name", "hours"])
    dropped = initial_rows - len(df)
    if dropped > 0:
        print(f"🧽 Dropped {dropped} row(s) due to missing volunteer names or hours.")

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


def guess_columns(df):
    if df is None:
        return {}
    expected_fields = {
        "name": ["name", "full_name", "volunteer_name", "donor_name", "supporter"],
        "hours": ["hours", "time", "duration", "volunteer_hours", "logged_hours"],
        "amount": ["amount", "donation", "gift", "contribution", "value"],
        "department": ["department", "program", "ministry", "campaign", "area"],
        "date": ["date", "timestamp", "entry_date", "donation_date", "served_on"],
    }

    mapping = {}
    for field, candidates in expected_fields.items():
        matches = difflib.get_close_matches(field, df.columns, n=1, cutoff=0.6)
        if matches:
            mapping[field] = matches[0]
        else:
            # Try matching from candidate list
            for candidate in candidates:
                if candidate in df.columns:
                    mapping[field] = candidate
                    break
    return mapping


def load_and_clean_structured_sales(uploaded_file):
    if uploaded_file is None:
        return None

    try:
        # Read Excel file with no headers
        full_df = pd.read_excel(uploaded_file, header=None)

        # Find the row where the clean data starts
        # Look for the row that contains the actual headers
        header_row_index = (
            full_df[0].astype(str).str.contains("Ship Mode", case=False).idxmax()
        )

        # Extract headers and data
        headers = full_df.iloc[header_row_index].tolist()
        df = full_df.iloc[header_row_index + 1 :].copy()
        df.columns = [str(col).strip().lower().replace(" ", "_") for col in headers]

        # Drop any unnamed or empty columns
        df = df.loc[:, ~df.columns.str.contains("^unnamed", case=False)]
        df = df.dropna(how="all")  # Drop empty rows

        return safe_clean_dataframe(df)

    except Exception as e:
        st.error(f"Failed to load structured sales data: {e}")
        return None


def load_and_clean_dataframe(uploaded_file):
    import pandas as pd
    import streamlit as st

    if uploaded_file is None:
        return None

    try:
        # Try loading as comma CSV
        df = pd.read_csv(uploaded_file, encoding="utf-8")
        if df.shape[1] == 1:
            sample = df.iloc[:, 0].dropna().astype(str)
            if sample.str.contains(r"\|").sum() >= 3:
                uploaded_file.seek(0)
                fallback_df = pd.read_csv(
                    uploaded_file,
                    sep="|",
                    engine="python",
                    header=None,
                    encoding="utf-8",
                )

                # ⛏️ Grab first row as headers
                new_header = fallback_df.iloc[0].tolist()
                df = fallback_df.iloc[1:].copy()
                df.columns = [
                    str(col).strip().lower().replace(" ", "_") for col in new_header
                ]

    except Exception:
        try:
            uploaded_file.seek(0)
            df = pd.read_excel(uploaded_file, engine="openpyxl")
        except Exception as e:
            st.error(f"⚠️ Failed to load file: {e}")
            return None

    if df is None or df.empty:
        st.warning("⚠️ File was loaded but contains no usable rows.")
        return None

    st.write("🔍 Columns after load:", df.columns.tolist())
    st.dataframe(df.head(3))

    try:
        df_clean = safe_clean_dataframe(df)
        if df_clean is None or df_clean.empty:
            st.warning("⚠️ Cleaning completed, but no usable data remained.")
            return None
        return df_clean
    except Exception as e:
        st.error(f"❌ Cleaning error: {e}")
        return None


def safe_clean_dataframe(df):
    import pandas as pd
    import streamlit as st

    if df is None:
        raise ValueError("No data to clean.")

    df_clean = df.copy()

    # ✅ Normalize column names
    df_clean.columns = [
        col.strip().lower().replace(" ", "_") for col in df_clean.columns
    ]

    # 🧹 Drop fully empty columns
    df_clean.dropna(axis=1, how="all", inplace=True)

    # 🧾 Clean 'amount' values

    if "amount" in df_clean.columns and "category" in df_clean.columns:
        contains_pipe = df_clean["amount"].astype(str).str.contains(r"\|").any()

        if contains_pipe:
            df_clean = df_clean.assign(
                amount=df_clean["amount"].astype(str).str.split("|"),
                category=df_clean["category"].astype(str).str.split("|"),
            ).explode(["amount", "category"])

        # 🧼 Now clean up the amount column
        df_clean["amount"] = (
            df_clean["amount"]
            .astype(str)
            .str.extract(r"([0-9]+(?:\.[0-9]+)?)")[0]
            .replace("", None)
        )
        df_clean["amount"] = pd.to_numeric(df_clean["amount"], errors="coerce")

    # 📆 Clean 'date' if present
    if "date" in df_clean.columns:
        df_clean["date"] = pd.to_datetime(df_clean["date"], errors="coerce")

    # ⏱️ Clean 'hours' if present
    if "hours" in df_clean.columns:
        df_clean["hours"] = pd.to_numeric(df_clean["hours"], errors="coerce")

    # 🪪 Map 'dept' to 'campaign' if needed
    if "dept" in df_clean.columns and "campaign" not in df_clean.columns:
        df_clean["campaign"] = df_clean["dept"]

    # 🧼 Standardize 'campaign' values
    if "campaign" in df_clean.columns:
        df_clean["campaign"] = (
            df_clean["campaign"]
            .astype(str)
            .str.strip()
            .str.title()
            .replace("", "Uncategorized")
            .fillna("Uncategorized")
        )
    df_clean.insert(0, "row", range(1, len(df_clean) + 1))
    df_clean.reset_index(drop=True, inplace=True)
    return df_clean


# def flatten_invoice_dataset(uploaded_file):
#     import pandas as pd
#     import streamlit as st

#     try:
#         df_raw = pd.read_excel(uploaded_file, header=None, usecols=[0])
#         records = []

#         for i in range(2, len(df_raw), 3):  # Skip "Dirty 8" and "Order ID"
#             try:
#                 order_id = str(df_raw.iloc[i, 0]).strip()
#                 raw_categories = str(df_raw.iloc[i + 1, 0])
#                 raw_amounts = str(df_raw.iloc[i + 2, 0])

#                 if not order_id or not raw_categories or not raw_amounts:
#                     continue

#                 categories = [c.strip() for c in raw_categories.split("|")]
#                 amounts = [a.strip() for a in raw_amounts.split("|")]

#                 for cat, amt in zip(categories, amounts):
#                     try:
#                         amt_float = float(amt.replace(",", ""))
#                     except ValueError:
#                         amt_float = None

#                     records.append(
#                         {"order_id": order_id, "category": cat, "amount": amt_float}
#                     )

#             except Exception as e:
#                 st.warning(f"⚠️ Skipped block at row {i}: {e}")
#                 continue

#         return pd.DataFrame(records)

#     except Exception as e:
#         st.error(f"❌ Failed to flatten invoice file: {e}")
#         return None


def debug_invoice_file(uploaded_file):
    df = pd.read_excel(uploaded_file, header=None)
    st.write("🧾 Raw Excel Preview (first 15 rows):")
    st.dataframe(df.head(15))


# --- Salesforce Push (Beta Stub) ---
def push_to_salesforce(df, object_type="Opportunity"):
    import requests
    import json
    import streamlit as st
    from datetime import datetime
    import pandas as pd  # If you plan to return/display/export the log

    token = st.session_state.get("sf_token")
    if not token:
        return (
            False,
            "No Salesforce token provided. Please enter one in the sidebar.",
            [],
        )

    instance_url = "https://your_instance.salesforce.com"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    try:
        synced = 0
        errors = []
        log = []

        for _, row in df.iterrows():
            payload = {
                "Name": row.get("name"),
                "Amount__c": row.get("amount"),
                "Campaign__c": row.get("campaign"),
                "Hours__c": row.get("hours"),
                "Email__c": row.get("contact"),
            }

            response = requests.post(
                f"{instance_url}/services/data/v52.0/sobjects/{object_type}/",
                headers=headers,
                data=json.dumps(payload),
            )

            timestamp = datetime.now().isoformat()

            if response.ok:
                synced += 1
                log.append(
                    {
                        "name": row.get("name", "Unknown"),
                        "status": "Synced",
                        "message": "Success",
                        "timestamp": timestamp,
                    }
                )
            else:
                errors.append(row.get("name", "Unknown"))
                log.append(
                    {
                        "name": row.get("name", "Unknown"),
                        "status": "Failed",
                        "message": response.text,
                        "timestamp": timestamp,
                    }
                )

        summary = f"✅ Pushed {synced} rows. 🚧 {len(errors)} errors."
        return True, summary, log

    except Exception as e:
        return False, f"Sync error: {e}", []


def run_column_mapper(df):
    return df.copy()  # Placeholder for any mapping logic you'd like


def clean_data(df):
    df_std = run_column_mapper(df)
    if "amount" in df_std.columns and "date" in df_std.columns:
        return clean_donations(df_std)
    elif "hours" in df_std.columns and "name" in df_std.columns:
        return clean_volunteers(df_std)
    else:
        return safe_clean_dataframe(df_std)
