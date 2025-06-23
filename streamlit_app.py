import streamlit as st
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
)

st.set_page_config(page_title="Data_Laundry: Mission to Clean")


def guess_columns(df):
    expected = {
        "name": ["name", "volunteer", "full_name"],
        "donor_name": ["donor", "supporter", "giver"],
        "amount": ["amount", "donation", "gift", "contribution", "value"],
        "hours": ["hours", "time", "duration", "logged"],
        "department": ["department", "program", "campaign"],
        "campaign": ["campaign", "initiative", "project"],
        "date": ["date", "timestamp", "donation_date", "served"],
        "client_id": ["id", "case_number", "client_identifier"],
        "service_type": ["program", "track", "service"],
        "contact": ["email", "phone", "contact_info"],
        "gender": ["gender", "sex", "identity"],
        "ethnicity": ["race", "ethnicity", "background"],
        "notes": ["notes", "remarks", "comments"],
        "location": ["location", "address", "site"],
        "age": ["age", "years", "birth_year"],
        "status": ["status", "case_status", "volunteer_status"],
        "volunteer_status": ["volunteer_status", "engagement", "participation"],
        "service_date": ["service_date", "visit_date", "appointment_date"],
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
    st.markdown("## 🧪 Coming Soon")
    st.markdown("- PDF/Scanner cleanup\n- Multi-file merge\n- Saved org profiles")

    st.sidebar.markdown("## 🏢 Who Uses This?")
    st.sidebar.markdown(
        "- Nonprofit admins\n"
        "- Volunteer coordinators\n"
        "- Grant writers & CRM assistants\n"
        "- Shelters, food banks, clinics, ministries"
    )
    st.sidebar.markdown("## 💌 Need custom cleanup help?")
    st.sidebar.markdown("📬 Email:")
    st.caption("🔧 cleandatalaundry@gmail.com")
st.title("🧺 Data_Laundry: Mission to Clean")


uploaded = st.file_uploader("Upload your CSV or Excel file", type=["csv", "xlsx"])

if uploaded:
    df = decode_file(uploaded)
    if df is not None:
        if df.columns.duplicated().any():
            df = df.loc[:, ~df.columns.duplicated()]
            st.warning("Duplicate columns found and removed.")

        st.subheader("📋 Preview")
        st.dataframe(df.head())

        column_map = guess_columns(df)

        def safe_index(col):
            return df.columns.get_loc(col) if col in df.columns else 0

        st.sidebar.markdown("### 🧭 Match Your Columns")
        column_map = guess_columns(df)

        confirmed = {}
        for key, guess in column_map.items():
            confirmed[key] = st.sidebar.selectbox(
                f"Column for `{key}`",
                df.columns,
                index=df.columns.get_loc(guess) if guess in df.columns else 0,
            )

        df_std = df.rename(columns={v: k for k, v in confirmed.items()})

        is_donation = "amount" in df_std.columns and "donor_name" in df_std.columns
        is_volunteer = "hours" in df_std.columns and "name" in df_std.columns

        cleaned_donations = None
        cleaned_volunteers = None
        donation_summary = None
        volunteer_summary = None

        if is_donation:
            st.header("💵 Donation Data")
            if (
                st.radio("Step:", ["Preview Only", "Clean & Summarize"], key="donate")
                == "Clean & Summarize"
            ):
                try:
                    cleaned_donations = clean_donations(df_std)
                    st.dataframe(cleaned_donations.head())

                    # Filter by selected date range
                    s, e = st.date_input(
                        "Date Range",
                        [
                            cleaned_donations["date"].min(),
                            cleaned_donations["date"].max(),
                        ],
                        min_value=cleaned_donations["date"].min(),
                        max_value=cleaned_donations["date"].max(),
                    )

                    # Apply date filtering
                    filtered = cleaned_donations[
                        (cleaned_donations["date"] >= pd.to_datetime(s))
                        & (cleaned_donations["date"] <= pd.to_datetime(e))
                    ]

                    # Pro user preview logic
                    PREVIEW_LIMIT = 10
                    is_pro_user = st.session_state.get("pro_user", False)
                    filtered_preview = (
                        filtered if is_pro_user else filtered.head(PREVIEW_LIMIT)
                    )

                    st.subheader("📋 Cleaned Donation Preview")
                    st.dataframe(filtered_preview)

                    # Upgrade option
                    if not is_pro_user:
                        st.info(
                            f"You're viewing the first {PREVIEW_LIMIT} rows. Upgrade to unlock full access and downloads."
                        )
                        if st.button("🚀 Upgrade to Pro"):
                            st.session_state["pro_user"] = True
                            st.success("✨ Pro unlocked! You now have full access.")

                    st.metric("💵 Total", f"${filtered['amount'].sum():,.2f}")
                    st.metric("🙋 Donors", filtered["donor_name"].nunique())

                    if "campaign" in filtered.columns:
                        ct = st.selectbox("Chart", ["Bar", "Line", "Pie"])
                        fig, ax = plt.subplots()
                        cd = filtered.groupby("campaign")["amount"].sum().sort_values()

                    if ct == "Bar":
                        cd.plot(kind="barh", ax=ax, color="#4d4dff")
                    elif ct == "Line":
                        cd.plot(kind="line", ax=ax, marker="o", color="#4d4dff")
                    elif ct == "Pie":
                        cd.plot(kind="pie", ax=ax, autopct="%.1f%%", startangle=90)
                        ax.set_ylabel("")

                    ax.set_title("Donations by Campaign")
                    st.pyplot(fig)

                    st.download_button(
                        "⬇ Download",
                        filtered.to_csv(index=False),
                        file_name="filtered_donations.csv",
                    )

                    donation_summary = generate_donation_summary(filtered)
                    hygiene = generate_hygiene_report(df_std, filtered, "Donations")
                    st.subheader("🧽 Hygiene Report")
                    st.json(hygiene)
                    st.subheader("📦 Summary")
                    st.json(donation_summary)

                except Exception as e:
                    st.error(f"❌ Donations failed: {e}")

        if is_volunteer:
            st.header("🙋 Volunteer Data")
            if (
                st.radio("Step:", ["Preview Only", "Clean & Summarize"], key="vol")
                == "Clean & Summarize"
            ):
                try:
                    cleaned_volunteers = clean_volunteers(df_std)
                    st.dataframe(cleaned_volunteers.head())

                    depts = ["All"] + sorted(
                        cleaned_volunteers["department"].dropna().unique()
                    )
                    selected = st.selectbox("Department", depts)
                    filtered = (
                        cleaned_volunteers
                        if selected == "All"
                        else cleaned_volunteers[
                            cleaned_volunteers["department"] == selected
                        ]
                    )

                    st.metric("🙋 Volunteers", filtered["name"].nunique())
                    st.metric("⏱️ Total Hours", filtered["hours"].sum())

                    chart_type = st.selectbox("Chart", ["Bar", "Line", "Pie"])
                    chart = filtered.groupby("department")["hours"].sum().sort_values()
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
                        ax.set_ylabel("")  # hide y-label for pie

                    ax.set_title("Volunteer Hours by Department")
                    st.pyplot(fig)

                    if chart_type == "Pie":
                        ax.set_ylabel("")
                    ax.set_title("Hours by Department")
                    st.pyplot(fig)

                    st.download_button(
                        "⬇ Download",
                        filtered.to_csv(index=False),
                        file_name="filtered_volunteers.csv",
                    )

                    volunteer_summary = generate_volunteer_summary(filtered)
                    hygiene = generate_hygiene_report(df_std, filtered, "Volunteers")
                    st.subheader("🧽 Hygiene Report")
                    st.json(hygiene)
                    st.subheader("📦 Summary")
                    st.json(volunteer_summary)

                except Exception as e:
                    st.error(f"❌ Volunteers failed: {e}")

        if cleaned_donations is not None and cleaned_volunteers is not None:
            st.header("🔁 Merged Donor & Volunteer View")
            merged = merge_donor_volunteer_data(cleaned_donations, cleaned_volunteers)
            st.dataframe(merged.head())

            st.download_button(
                "⬇ Download Merged",
                merged.to_csv(index=False),
                file_name="merged_donor_volunteer.csv",
            )

            try:
                pdf = create_pdf_report(donation_summary, volunteer_summary)
                st.download_button(
                    "📥 Download PDF",
                    data=pdf,
                    file_name="nonprofit_summary.pdf",
                    mime="application/pdf",
                )
            except Exception as e:
                st.error(f"PDF generation failed: {e}")
                PREVIEW_LIMIT = 10
    is_pro_user = st.session_state.get("pro_user", False)


st.markdown("---")
st.markdown("### What Makes Data_Laundry Different")
st.markdown(
    "- ✅ Works with any column names\n"
    "- 🚀 No templates or rigid formats\n"
    "- 📊 Built for nonprofits, not spreadsheets\n"
    "- 🧠 Smart insights, not just row cleanup"
)
st.caption("Built by **Dontrail Detroit Hunter** · Powered by Data_Laundry 🧼")
st.markdown("### 🧼 Data_Laundry: Mission to Clean")
st.caption(
    "🔒 Built with care by Data_Laundry · Used by outreach teams, food banks, and missions nationwide"
)
