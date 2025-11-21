import streamlit as st
import pandas as pd
from datetime import date
from pathlib import Path
import time  # module, not datetime.time

from db.db_functions_users_KT import edit_own_profile
from db.db_functions_usertrips_KT import get_user_trips
from db.db_functions_trips import create_trip_table, create_trip_users_table
from db.db_functions_expenses import (
    create_expenses_table,
    add_expense,
    get_expenses_for_trip,
)
from db.db_functions_API_SBB import get_sbb_connections, extract_simple_connection_list

# --- Page setup ---
st.set_page_config(page_title="Employee Dashboard", layout="wide")
st.title("Employee Dashboard")

# --- Access control ---
if "role" not in st.session_state or st.session_state["role"] != "User":
    st.error("Access denied. Please log in as User.")
    st.stop()

# Make sure all required tables exist
create_trip_table()
create_trip_users_table()
create_expenses_table()

# --- Layout ---
left, right = st.columns([4, 2], gap="large")

# -----------------------------
# LEFT: TRIP OVERVIEW
# -----------------------------
with left:
    st.subheader("Your Trips")

    user_id = st.session_state.get("user_ID", None)
    if user_id is None:
        st.warning("No user logged in. Please log in again.")
        st.stop()

    trips = get_user_trips(user_id)

    if trips is None or trips.empty:
        st.info("You have no trips assigned yet.")
    else:
        # Normalize date columns
        # Prefer departure/arrival dates; keep legacy start/end for safety.
        trips["departure_date"] = pd.to_datetime(trips["departure_date"])
        trips["arrival_date"] = pd.to_datetime(trips["arrival_date"])

        st.markdown("### 📅 Filter by date range")
        date_range = st.date_input(
            "Select a date or range",
            value=(date.today(), date.today()),
            help="Pick one day or a range to filter your trips",
        )

        if isinstance(date_range, tuple):
            start, end = date_range
        else:
            start = end = date_range

        mask = (trips["departure_date"] <= end) & (trips["arrival_date"] >= start)
        filtered = trips.loc[mask].sort_values("departure_date", ascending=True)

        if filtered.empty:
            st.warning("No trips found for the selected date range.")
        else:
            st.markdown("### ✈️ Your trips")
            for _, row in filtered.iterrows():
                dep_city = row["departure_city"] or "?"
                arr_city = row["arrival_city"] or row["destination"]
                dep_date = row["departure_date"].date()
                arr_date = row["arrival_date"].date()

                trip_title = f"{dep_city} → {arr_city} ({dep_date} → {arr_date})"
                with st.expander(trip_title, expanded=False):
                    st.markdown(f"**Destination label:** {row['destination']}")
                    st.markdown(f"**Cities:** {dep_city} → {arr_city}")
                    st.markdown(f"**Dates:** {dep_date} → {arr_date}")
                    st.markdown(f"**Occasion:** {row['occasion'] or '—'}")

                    # --- SBB map + train times section ---
                    st.markdown("#### 🗺️ Journey & Train Info")

                    if row["sbb_api_token"]:
                        api_token = row["sbb_api_token"]
                        sbb_data = get_sbb_connections(
                            departure_city=dep_city,
                            arrival_city=arr_city,
                            departure_date=str(dep_date),
                            api_token=api_token,
                        )
                        connections = extract_simple_connection_list(sbb_data)
                        if connections:
                            st.markdown("**Sample connections (simplified):**")
                            st.dataframe(connections, use_container_width=True)
                        else:
                            st.info("No connections could be parsed from SBB response (template).")
                    else:
                        st.info(
                            "No SBB API token stored for this trip yet. "
                            "Ask your manager to add it if you need live train data."
                        )

                    # --- Receipt upload form ---
                    st.markdown("#### 📄 Upload a receipt")
                    with st.form(f"upload_receipt_form_{row['trip_ID']}"):
                        uploaded_file = st.file_uploader(
                            "Choose a receipt file (image or PDF)",
                            type=["png", "jpg", "jpeg", "pdf"],
                            key=f"receipt_{row['trip_ID']}",
                        )

                        col1, col2 = st.columns(2)
                        with col1:
                            category = st.selectbox(
                                "Category",
                                ["Meal", "Transport", "Hotel", "Other"],
                                index=0,
                            )
                            amount = st.number_input(
                                "Amount",
                                min_value=0.0,
                                step=1.0,
                                format="%.2f",
                            )
                        with col2:
                            currency = st.text_input("Currency", value="CHF")
                            note = st.text_input("Note (optional)", value="")

                        submit_receipt = st.form_submit_button("Save receipt")

                    if submit_receipt:
                        if uploaded_file is None:
                            st.error("Please upload a file first.")
                        else:
                            # Save file to disk
                            receipts_dir = Path("uploads") / "receipts" / str(row["trip_ID"])
                            receipts_dir.mkdir(parents=True, exist_ok=True)

                            ext = Path(uploaded_file.name).suffix
                            filename = f"user{user_id}_{int(time.time())}{ext}"
                            file_path = receipts_dir / filename

                            with open(file_path, "wb") as f:
                                f.write(uploaded_file.getbuffer())

                            # Store in expenses.db
                            add_expense(
                                trip_ID=int(row["trip_ID"]),
                                user_ID=int(user_id),
                                file_path=str(file_path),
                                amount=float(amount) if amount else None,
                                currency=currency or None,
                                category=category or None,
                                note=note or None,
                            )

                            st.success("Receipt saved.")
                            st.experimental_rerun()

                    # --- Show existing receipts for this trip ---
                    st.markdown("#### 💰 Your receipts for this trip")
                    receipts_df = get_expenses_for_trip(int(row["trip_ID"]), user_ID=user_id)
                    if receipts_df.empty:
                        st.info("No receipts uploaded yet.")
                    else:
                        display_cols = [
                            "created_at",
                            "category",
                            "amount",
                            "currency",
                            "note",
                            "status",
                        ]
                        receipts_display = receipts_df[display_cols]
                        st.dataframe(
                            receipts_display,
                            use_container_width=True,
                            hide_index=True,
                        )
                        st.caption("Status will be used later for manager approval.")
# -----------------------------
# RIGHT: PROFILE
# -----------------------------
with right:
    st.subheader("My Profile")
    edit_own_profile()
