import pandas as pd
from non_profit import clean_donations, clean_volunteers


def test_clean_donations():
    raw_data = pd.DataFrame(
        {
            "Donor Name": ["  jane doe", "JOHN smith", None, "Amy"],
            "Method": ["CREDIT", "paypal", "CASH", "credit"],
            "Campaign": ["Holiday Fund", None, "Health", "Health"],
            "Amount": ["$100", "$0", "$25.00", "$75.5"],
            "Date": ["2024-01-01", "2024-02-10", "not_a_date", "2024-03-15"],
        }
    )

    cleaned = clean_donations(raw_data)

    assert "donor_name" in cleaned.columns
    assert cleaned.shape[0] == 2  # drops None name and $0 donation
    assert cleaned["amount"].dtype == float
    assert cleaned["donor_name"].tolist() == ["Jane Doe", "Amy"]


def test_clean_volunteers():
    raw_data = pd.DataFrame(
        {
            " Name ": [" alice ", "BOB", None],
            "Dept": ["health", "Education", "Food"],
            "Phone": ["(555)-123-4567", "+1-555-789-4321", "NaN"],
            "Hours": [2, 4, None],
        }
    )

    cleaned = clean_volunteers(raw_data)

    assert "name" in cleaned.columns
    assert cleaned.shape[0] == 2  # drops row with missing name or hours
    assert cleaned["phone"].iloc[0] == "5551234567"
    assert cleaned["name"].tolist() == ["Alice", "Bob"]


if __name__ == "__main__":
    test_clean_donations()
    test_clean_volunteers()
    print("✅ All cleaning tests passed!")
