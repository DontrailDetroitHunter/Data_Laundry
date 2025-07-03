import streamlit as st


st.set_page_config(page_title="Mission to Clean", page_icon="🧼")

# --- Header and Mission ---
st.title("🧼 Data Laundry for Nonprofits")
st.markdown(
    "Quickly clean, preview, and download structured donation or volunteer data — no tech skills required."
)

# --- Sample File CTA ---
with st.expander("📂 No file? Try a sample dataset"):
    st.markdown(
        "[⬇ Download Sample CSV](https://docs.google.com/spreadsheets/d/1ReCIEaaa48e-ihJLMsrFFpRE8_UP-ALeYdPDgVVQQ_M/export?format=csv)"
    )

    st.markdown(
        "[⬇ Download Sample Excel](https://docs.google.com/spreadsheets/d/1ReCIEaaa48e-ihJLMsrFFpRE8_UP-ALeYdPDgVVQQ_M/export?format=xlsx)"
    )

# --- Sidebar Info ---
st.sidebar.title("🧭 About This Tool")
st.sidebar.markdown(
    "Built for nonprofits who work with messy spreadsheets. Upload donation or volunteer files — we'll detect, clean, and summarize them automatically."
)

# --- Pro Mode Control ---
if st.sidebar.checkbox("🔓 Dev Override: Unlock Pro", key="dev_override"):
    st.session_state["pro_user"] = True
    st.sidebar.success("✨ Pro access unlocked!")

is_pro_user = st.session_state.get("pro_user", False)
PREVIEW_LIMIT = 10

# --- Core App Variables ---
import pandas as pd
import matplotlib.pyplot as plt
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
    push_to_salesforce,
    safe_clean_dataframe,
    push_to_salesforce,
    safe_clean_dataframe,
    clean_data,
)

df_std = None
is_donation = False
is_volunteer = False
is_fallback = not is_donation and not is_volunteer and df_std is not None


col1, col2 = st.columns([1, 2])

# with col1:
#     if st.checkbox("👨‍💻 Dev Mode (Show Full Data)", key="dev_mode_main"):
#         st.session_state["pro_user"] = True

with col2:
    if st.sidebar.checkbox("🔓 Dev Override: Unlock Pro", key="dev_mode_sidebar"):
        st.session_state["pro_user"] = True
        st.sidebar.success("✨ Pro access unlocked!")

# Always check state AFTER dev toggles
is_pro_user = st.session_state.get("pro_user", False)


# --- Status Display ---
status_col1, status_col2 = st.columns([1, 2])
with status_col1:
    st.write("🔐 Pro Mode:", is_pro_user)
with status_col2:
    if is_pro_user:
        st.success("✅ Pro Access Enabled")
    else:
        st.warning("🔒 Free Mode: 10-Row Preview Only")
# --- CRM Integration Options ---
st.sidebar.markdown("## 🔗 CRM Integration (Optional)")

enable_crm = st.sidebar.checkbox("Enable Salesforce Sync", value=False)

if enable_crm:
    st.sidebar.success("📡 CRM Sync Enabled")
    selected_object = st.sidebar.selectbox(
        "Salesforce Object",
        ["Opportunity", "Volunteer__c", "Donation__c", "Custom_Object__c"],
        index=0,
        key="crm_object",
    )
    st.sidebar.markdown(
        "ℹ️ Add your access token in non_profit.py or connect via OAuth."
    )
    salesforce_token = st.sidebar.text_input(
        "🔐 Enter Salesforce Access Token (Dev Only)",
        type="password",
        placeholder="Paste your token here",
        key="salesforce_token_input",
    )

    if salesforce_token:
        st.session_state["sf_token"] = salesforce_token

# --- Upgrade Call-to-Action (shown only if not Pro) ---
if not is_pro_user:
    st.info(
        "You're viewing the first 10 rows. Want full access? Request Pro access and I’ll unlock it for your org."
    )
    if st.button("🚀 Request Pro Access"):
        st.markdown(
            "[📬 Click here to request access via email](mailto:https://docs.google.com/spreadsheets/d/1gPTMI02oOQBERrMEf4kea9qQqtnr73CEFRZYDr3hwA8/edit?resourcekey=&gid=251280724#gid=251280724)"
        )


def render_volunteer_view(cleaned_volunteers, is_pro_user, preview_limit=10):
    if cleaned_volunteers.empty:
        st.warning("⚠️ No valid volunteer data available for preview.")
        return

    st.subheader("🧼 Cleaned Volunteer Data Preview")
    if is_pro_user:
        st.dataframe(cleaned_volunteers)
    else:
        st.dataframe(cleaned_volunteers.head(preview_limit))


def guess_columns(df):
    expected = {
        "id": [
            "id",
            "identifier",
            "unique_id",
            "case_number",
            "client_id",
            "volunteer_id",
            "donor_id",
            "supporter_id",
            "client_identifier",
        ],
        "name": [
            "name",
            "person" "volunteer",
            "full_name",
            "identity",
            "donor_name",
            "supporter",
            "id",
            "unique_id",
            "volunteer_name",
            "volunteer_full_name",
            "volunteer_identity",
            "volunteer_person",
            "volunteer_full_name",
            "volunteer_identity",
            "volunteer_person",
        ],
        "donor_name": [
            "donor",
            "supporter",
            "giver",
            "contributor",
            "donation_name",
        ],
        "amount": [
            "amount",
            "donation",
            "gift",
            "contribution",
            "value",
            "price",
            "donation_amount",
            "donation_value",
            "donation_total",
            "totals",
        ],
        "hours": [
            "hours",
            "time",
            "duration",
            "logged",
            "length",
            "volunteer_hours",
            "time_spent",
            "volunteer_time",
            "volunteer_duration",
        ],
        "department": [
            "department",
            "program",
            "campaign",
            "ministry",
            "area",
            "track",
            "initiative",
            "project",
            "service_area",
            "service_department",
            "service_program",
            "church",
            "organization",
            "nonprofit",
            "nonprofit_name",
            "organization_name",
            "nonprofit_department",
            "nonprofit_program",
            "nonprofit_campaign",
            "nonprofit_ministry",
            "nonprofit_area",
            "nonprofit_track",
            "nonprofit_initiative",
            "nonprofit_project",
            "nonprofit_service_area",
            "nonprofit_service_department",
            "nonprofit_service_program",
            "nonprofit_service_campaign",
        ],
        "campaign": [
            "campaign",
            "initiative",
            "project",
            "program",
            "funding_program",
            "funding_initiative",
            "fundraiser",
            "event",
            "funding",
            "funding_campaign",
            "funding_initiative",
            "funding_project",
            "funding_event",
            "funding_fundraiser",
            "funding_source",
            "category",
            "subcategory",
            "fund",
            "funding_source",
            "funding_source_name",
            "funding_source_type",
            "funding_source_category",
            "funding_source_subcategory",
            "funding_source_project",
            "funding_source_initiative",
            "funding_source_event",
        ],
        "date": ["date", "timestamp", "donation_date", "served"],
        "client_id": ["id", "case_number", "client_identifier"],
        "service_type": ["program", "track", "service"],
        "contact": ["email", "phone", "contact_info"],
        "gender": [
            "gender",
            "sex",
            "identity",
            "gender_identity",
            "prefix",
            "pronouns",
            "Mr",
            "Mrs",
            "Ms",
            "Mx",
            "Dr",
            "male",
            "female",
            "non_binary",
            "genderqueer",
            "genderfluid",
            "agender",
            "bigender",
            "two_spirit",
        ],
        "ethnicity": ["race", "ethnicity", "background"],
        "notes": ["notes", "remarks", "comments"],
        "location": ["location", "address", "site"],
        "age": ["age", "years", "birth_year"],
        "status": ["status", "case_status", "volunteer_status"],
        "volunteer_status": ["volunteer_status", "engagement", "participation"],
        "service_date": [
            "service_date",
            "visit_date",
            "appointment_date",
            "project_date",
        ],
    }
    result = {}
    for key, aliases in expected.items():
        for col in df.columns:
            if any(alias in col.lower() for alias in aliases):
                result[key] = col
                break
    return result


def decode_file(uploaded_file):
    try:
        if uploaded_file.name.endswith(".csv"):
            return pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith((".xls", ".xlsx")):
            return pd.read_excel(uploaded_file)
        else:
            st.error("Unsupported file type.")
            return None
    except Exception as e:
        st.error(f"Could not load file: {e}")
        return None


# Sidebar branding
with st.sidebar:
    st.markdown("## 🧼 File Types")
    st.markdown("- CSV (.csv)\n- Excel (.xlsx)")
    st.sidebar.markdown("## 🧪 Coming Soon")

    st.sidebar.markdown(
        "- PDF/Scanner cleanup\n- Multi-file merge\n- Saved org profiles"
    )

    st.sidebar.markdown("## 🏢 Who Uses This?")
    st.sidebar.markdown(
        "- Nonprofit admins\n"
        "- Volunteer coordinators\n"
        "- Grant writers & CRM assistants\n"
        "- Shelters, food banks, clinics, ministries"
    )
    st.sidebar.markdown("## 💌 Need custom cleanup help?")
    st.sidebar.markdown("📬 Email:")
    st.caption("🔧 cleandataaundry@gmail.com")
    st.sidebar.markdown(
        "📋 [Fill out this quick form to request Pro access](https://forms.gle/vJ55VwzP9DudWNCG8)"
    )
    st.sidebar.markdown("## 📄 R Markdown Report")
    st.sidebar.markdown(
        "Use R? Download our R Markdown template to generate a clean HTML report from your cleaned CSV."
    )

    st.sidebar.markdown(
        "[Download R template](https://github.com/DontrailDetroitHunter/your-repo-name/raw/main/rmd_reports/data_laundry_report.Rmd)"
    )


st.title("🧺 Data_Laundry: Mission to Clean")


def run_column_mapper(df):
    import streamlit as st

    if df is None or df.empty:
        return None

    # Remove duplicate columns
    if df.columns.duplicated().any():
        df = df.loc[:, ~df.columns.duplicated()]
        st.warning("⚠️ Duplicate columns removed.")

    st.subheader("📈 Data Preview")
    st.dataframe(df.head())

    # Column guessing
    try:
        column_map = guess_columns(df)
    except Exception as e:
        st.error(f"❌ Column guessing failed: {e}")
        return None

    def safe_index(col):
        return df.columns.get_loc(col) if col in df.columns else 0

    st.sidebar.markdown("### 🧭 Match Your Columns")
    confirmed = {}

    for key, guess in column_map.items():
        confirmed[key] = st.sidebar.selectbox(
            f"Column for `{key}`", df.columns, index=safe_index(guess), key=f"map_{key}"
        )

    if confirmed:
        df_std = df.rename(columns={v: k for k, v in confirmed.items()})
        st.success("✅ Column mapping applied.")
        st.subheader("🧼 Standardized Preview")
        st.dataframe(df_std.head())
        return df_std
    else:
        st.warning("⚠️ Mapping skipped — no columns were matched.")
        return None


def detect_workflow(df_std):
    donation_required = {"amount", "date"}
    donation_optional = {"campaign", "donor_name", "method"}
    donation_matches = donation_required.intersection(df_std.columns)
    is_donation = len(donation_matches) == len(donation_required)

    volunteer_required = {"name", "hours", "department"}
    volunteer_optional = {"contact", "phone", "email"}
    volunteer_matches = volunteer_required.intersection(df_std.columns)
    is_volunteer = len(volunteer_matches) == len(volunteer_required)

    return is_donation, is_volunteer, donation_matches, volunteer_matches


def missing_value_report(df, key_fields=None):
    total = len(df)
    missing_report = {}

    for col in df.columns:
        missing = df[col].isna().sum()
        if missing > 0:
            pct = (missing / total) * 100
            critical = col in key_fields if key_fields else False
            missing_report[col] = {
                "missing_rows": missing,
                "percent_missing": f"{pct:.1f}%",
                "important": critical,
            }

    return missing_report


# --- Upload & Safeguard ---
# --- Upload & Safeguard ---
# --- File Upload and Column Mapping ---
uploaded_file = st.file_uploader("Upload your CSV or Excel file", type=["csv", "xlsx"])
df = None
df_std = None
cleaned_df = None
is_donation = False
is_volunteer = False

if uploaded_file:
    try:
        df = (
            pd.read_csv(uploaded_file)
            if uploaded_file.name.endswith(".csv")
            else pd.read_excel(uploaded_file)
        )
    except Exception as e:
        st.error(f"❌ Error reading file: {e}")
    else:
        df_std = run_column_mapper(df)

        # ✅ Auto-clean after mapping
        cleaned_df = clean_data(df_std)
        st.success("✅ File uploaded and auto-cleaned.")
        st.dataframe(cleaned_df.head())

        # ✅ Use the cleaned output throughout the app
        filtered = cleaned_df

        # --- Detect Workflow Type ---
        is_donation, is_volunteer, donation_matches, volunteer_matches = (
            detect_workflow(df_std)
        )

        # 🧪 Optional Debug Output
        st.write("🧠 Matched donation fields:", donation_matches)
        st.write("🧠 Matched volunteer fields:", volunteer_matches)
        st.write("🔍 is_donation:", is_donation, " | is_volunteer:", is_volunteer)

        # --- Donation Detection (Refined) ---
        donation_required = {"amount", "date"}
        donation_optional = {"campaign", "donor_name", "method"}
        donation_matches = donation_required.intersection(df_std.columns)
        is_donation = len(donation_matches) == len(donation_required)

        # --- Volunteer Detection (Refined) ---
        volunteer_required = {"name", "hours", "department"}
        volunteer_optional = {"contact", "phone", "email"}
        volunteer_matches = volunteer_required.intersection(df_std.columns)
        is_volunteer = len(volunteer_matches) == len(volunteer_required)

        # 🧪 Debug display (optional — remove in production)
        st.write("🧠 Matched donation fields:", donation_matches)
        st.write("🧠 Matched volunteer fields:", volunteer_matches)
        st.write("🔍 is_donation:", is_donation, " | is_volunteer:", is_volunteer)

else:
    st.info("📂 Please upload a file to begin.")


# --- Donation View ---
if is_donation:
    st.header("💵 Donation Data")

    if (
        st.radio("Step:", ["Preview Only", "Clean & Summarize"], key="donation_step")
        == "Clean & Summarize"
    ):
        try:
            cleaned_donations = clean_donations(df_std)

            # Filter by selected date range
            if (
                "date" in cleaned_donations.columns
                and not cleaned_donations["date"].isna().all()
            ):
                s, e = st.date_input(
                    "Date Range",
                    [cleaned_donations["date"].min(), cleaned_donations["date"].max()],
                    min_value=cleaned_donations["date"].min(),
                    max_value=cleaned_donations["date"].max(),
                )
                filtered = cleaned_donations[
                    (cleaned_donations["date"] >= pd.to_datetime(s))
                    & (cleaned_donations["date"] <= pd.to_datetime(e))
                ]
            else:
                st.warning("⚠️ Missing or invalid date column — skipping filter.")
                filtered = cleaned_donations

            preview = filtered if is_pro_user else filtered.head(PREVIEW_LIMIT)
            st.subheader("📋 Donation Preview")
            st.dataframe(preview)

            st.metric("💵 Total Donations", f"${filtered['amount'].sum():,.2f}")
            st.metric("🙋 Donors", filtered["donor_name"].nunique())

            if not is_pro_user:
                st.info(f"You're viewing the first {PREVIEW_LIMIT} rows.")
                if st.button("🚀 Request Pro Access (Donations)"):
                    st.markdown(
                        "[📬 Click to request Pro access](mailto:cleandatalaundry@gmail.com?subject=Pro%20Access%20Request)"
                    )

            st.subheader("📊 Donations by Campaign")

            # Fallback if campaign column is missing
            if "campaign" not in filtered.columns and "dept" in filtered.columns:
                filtered["campaign"] = filtered["dept"]

            if (
                "campaign" in filtered.columns
                and "amount" in filtered.columns
                and filtered["amount"].notna().sum() > 0
            ):
                chart_type = st.selectbox(
                    "Chart Type", ["Bar", "Line", "Pie"], key="donation_chart"
                )
                chart_data = filtered.groupby("campaign")["amount"].sum().sort_values()
                fig, ax = plt.subplots()

                if chart_type == "Bar":
                    chart_data.plot(kind="barh", ax=ax, color="#4d4dff")
                elif chart_type == "Line":
                    chart_data.plot(kind="line", ax=ax, marker="o", color="#4d4dff")
                elif chart_type == "Pie":
                    chart_data.plot(kind="pie", ax=ax, autopct="%.1f%%", startangle=90)
                    ax.set_ylabel("")

                ax.set_title("Donations by Campaign")
                st.pyplot(fig)
            else:
                st.info(
                    "📉 Chart skipped — missing or empty 'amount' or 'campaign' data."
                )

            st.subheader("⬇️ Download Cleaned Donations")
            if is_pro_user:

                st.download_button(
                    label="⬇ Download Full Cleaned File",
                    data=filtered.to_csv(index=False),
                    file_name="cleaned_donations.csv",
                    mime="text/csv",
                    key="download_donations_full",
                )
            if is_pro_user and st.button("🔗 Push to Salesforce (Donations)"):
                success, message = push_to_salesforce(
                    filtered, object_type="Opportunity"
                )
                if success:
                    st.success(f"✅ {message}")
                else:
                    st.error(f"❌ {message}")

                st.download_button(
                    label="⬇ Download Sample (Pro Only)",
                    data=filtered.head(PREVIEW_LIMIT).to_csv(index=False),
                    file_name="donations_sample.csv",
                    mime="text/csv",
                    disabled=True,
                    help="Unlock Pro to download full dataset",
                )

            try:
                donation_summary = generate_donation_summary(cleaned_donations)
                st.subheader("📦 Donation Summary")
                st.json(donation_summary)
            except Exception as e:
                st.error(f"❌ Donation summary failed: {e}")

        except Exception as e:
            st.error(f"❌ Donations failed: {e}")


if is_volunteer:
    st.header("🙋 Volunteer Data")

    if (
        st.radio("Step:", ["Preview Only", "Clean & Summarize"], key="volunteer_step")
        == "Clean & Summarize"
    ):
        try:
            cleaned_volunteers = clean_volunteers(df_std)
            st.subheader("📋 Cleaned Volunteer Preview")
            st.dataframe(cleaned_volunteers.head())

            # 🧼 Fallback: If 'campaign' is missing but 'dept' exists
            if (
                "campaign" not in cleaned_volunteers.columns
                and "dept" in cleaned_volunteers.columns
            ):
                cleaned_volunteers["campaign"] = cleaned_volunteers["dept"]

            # 🧪 Build campaign filter dynamically
            if "campaign" in cleaned_volunteers.columns:
                campaigns = ["All"] + sorted(
                    cleaned_volunteers["campaign"].dropna().unique()
                )
                selected = st.selectbox("Campaign", campaigns, key="vol_dept")

                filtered = (
                    cleaned_volunteers
                    if selected == "All"
                    else cleaned_volunteers[cleaned_volunteers["campaign"] == selected]
                )
            else:
                filtered = cleaned_volunteers
                st.warning("⚠️ No 'campaign' column found — skipping campaign filter.")

            preview = filtered if is_pro_user else filtered.head(PREVIEW_LIMIT)
            st.subheader("📋 Volunteer Preview")
            st.dataframe(preview)

            st.metric("🙋 Volunteers", filtered["name"].nunique())
            st.metric("⏱️ Total Hours", filtered["hours"].sum())

            if not is_pro_user:
                st.info(f"You're viewing the first {PREVIEW_LIMIT} rows.")
                if st.button("🚀 Request Pro Access (Volunteers)"):
                    st.markdown(
                        "[📬 Click to request access](mailto:cleandatalaundry@gmail.com?subject=Pro%20Access%20Request)"
                    )

            st.subheader("📊 Volunteer Hours by Campaign")

            if (
                "campaign" in filtered.columns
                and "hours" in filtered.columns
                and filtered["hours"].notna().sum() > 0
            ):
                chart = filtered.groupby("campaign")["hours"].sum().sort_values()
                chart_type = st.selectbox(
                    "Chart Type", ["Bar", "Line", "Pie"], key="vol_chart"
                )
                fig, ax = plt.subplots()

                if chart_type == "Bar":
                    chart.plot(kind="barh", ax=ax, color="#82d18e")
                elif chart_type == "Line":
                    chart.plot(kind="line", ax=ax, marker="o", color="#82d18e")
                elif chart_type == "Pie":
                    chart.plot(
                        kind="pie",
                        ax=ax,
                        autopct="%1.1f%%",
                        startangle=90,
                        colors=plt.cm.Pastel1.colors,
                    )
                    ax.set_ylabel("")

                ax.set_title("Volunteer Hours by Campaign")
                st.pyplot(fig)
            else:
                st.info(
                    "📉 Chart skipped — missing or empty 'hours' or 'campaign' data."
                )
            if is_pro_user and enable_crm:
                st.caption(f"🎯 Target CRM Object: `{selected_object}`")

                if st.button("🔄 Push to Salesforce (Volunteers)"):
                    success, message, sync_log = push_to_salesforce(
                        filtered, object_type=selected_object
                    )

                    if success:
                        st.success(f"✅ {message}")
                    else:
                        st.error(f"❌ {message}")

                    if sync_log and isinstance(sync_log, list) and len(sync_log) > 0:
                        log_df = pd.DataFrame(sync_log)
                        with st.expander("📋 View Sync Log"):
                            st.caption(f"📋 Sync Log: {len(log_df)} rows processed")
                            st.dataframe(log_df)
                            st.download_button(
                                "📄 Download Sync Log",
                                log_df.to_csv(index=False),
                                file_name="sync_log.csv",
                            )

            st.subheader("⬇️ Download Cleaned Volunteers")
            if is_pro_user:
                st.download_button(
                    "📁 Download Full Cleaned File",
                    filtered.to_csv(index=False),
                    file_name="cleaned_volunteers.csv",
                    mime="text/csv",
                    key="download_volunteers_full",
                )
            else:
                st.download_button(
                    "📁 Download Sample (Pro Only)",
                    filtered.head(10).to_csv(index=False),
                    file_name="volunteers_sample.csv",
                    mime="text/csv",
                    disabled=True,
                    help="Unlock Pro to download the full file and sync to Salesforce",
                )

            if st.button("🔄 Push to Salesforce (Volunteers)"):
                success, message, sync_log = push_to_salesforce(
                    filtered, object_type=selected_object
                )

                if success:
                    st.success(f"✅ {message}")
                else:
                    st.error(f"❌ {message}")

                # 👇 Drop your improved sync_log check right here
                if sync_log and isinstance(sync_log, list) and len(sync_log) > 0:
                    log_df = pd.DataFrame(sync_log)
                    st.caption(f"📋 Sync Log: {len(log_df)} rows processed")
                    st.dataframe(log_df)
                    st.download_button(
                        "📄 Download Sync Log",
                        log_df.to_csv(index=False),
                        file_name="sync_log.csv",
                    )

                    if success:
                        st.success(f"✅ {message}")
                    else:
                        st.error(f"❌ {message}")
            else:
                st.download_button(
                    "📁 Download Sample (Pro Only)",
                    filtered.head(10).to_csv(index=False),
                    file_name="volunteers_sample.csv",
                    mime="text/csv",
                    disabled=True,
                    help="Unlock Pro to download the full file and sync to Salesforce",
                )

            try:
                volunteer_summary = generate_volunteer_summary(filtered)
                hygiene = generate_hygiene_report(df_std, filtered, "Volunteers")

                st.subheader("🧽 Hygiene Report")
                st.json(hygiene)

                st.subheader("📦 Volunteer Summary")
                st.json(volunteer_summary)

            except Exception as e:
                st.error(f"❌ Volunteer summary or hygiene failed: {e}")

        except Exception as e:
            st.error(f"❌ Volunteers failed: {e}")


# if not is_donation and not is_volunteer:
#     st.warning(
#         "⚠️ Your file didn't match donation or volunteer templates exactly, but we've cleaned and preserved what we could."
#     )
if df_std is not None and not is_donation and not is_volunteer:
    st.warning(
        "⚠️ Your file didn't match donation or volunteer templates exactly, but we've cleaned and preserved what we could."
    )

    try:
        fallback = safe_clean_dataframe(df_std)

        if fallback.empty:
            st.warning("⚠️ Fallback cleaning returned no usable data.")
        else:
            st.subheader("🧼 Fallback Cleaned Preview")
            st.dataframe(fallback.head(PREVIEW_LIMIT))

            st.subheader("🧼 Missing Value Overview")
            hygiene = missing_value_report(
                fallback, key_fields=["name", "hours", "amount", "date"]
            )
            st.json(hygiene)

            st.download_button(
                "⬇ Download Cleaned Fallback File",
                fallback.to_csv(index=False),
                file_name="cleaned_fallback.csv",
                mime="text/csv",
                key="fallback_download",
            )

    except Exception as e:
        st.error(f"❌ Fallback cleaning failed: {e}")


# --- Combined View ---

st.markdown("---")
st.markdown("### What Makes Data_Laundry Different")
st.markdown(
    "- ✅ Adapts to column names—no rigid templates required\n"
    "- 🚀 Flexible column matching, even with messy files\n"
    "- 📊 Built for nonprofits, not spreadsheets\n"
    "- 🧠 Smart insights, not just row cleanup, Smart mapping for real-world nonprofit data"
)
st.caption("Built by **Dontrail Detroit Hunter** · Powered by Data_Laundry 🧼")
st.markdown("### 🧼 Data_Laundry: Mission to Clean")
st.caption(
    "🔒 Built with care by Data_Laundry · Used by outreach teams, food banks, and missions nationwide"
)
