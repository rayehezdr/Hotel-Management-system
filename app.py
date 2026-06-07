import streamlit as st
import pandas as pd
from datetime import timedelta
from backend import *

init_db()

st.set_page_config(layout="wide")
st.title("Hotel Reservation System")

# ––––––––––––––––––––––––––––––––––––––––––
# LOGGED-IN VIEW
# ––––––––––––––––––––––––––––––––––––––––––

if st.session_state.get("user"):
    info = st.session_state.get("user_info")
    if info:
        st.sidebar.markdown(f"**{info[0]} {info[1]}**")
        st.sidebar.markdown(f"National ID: `{info[2]}`")
        st.sidebar.markdown(f"Phone: {info[3]}")
        st.sidebar.divider()

    if st.sidebar.button("Logout"):
        for key in ["user", "user_info", "rooms_shown", "avail_rooms", "unavail_rooms"]:
            st.session_state.pop(key, None)
        st.rerun()

    st.subheader("Select Dates")
    enter = st.date_input("Check-in Date")
    exit_date = st.date_input("Check-out Date")
    nights = (exit_date - enter).days if exit_date > enter else 0
    st.info(f"Number of nights: {nights}")
    cap = st.number_input("Number of Guests", 1, 10)

    if st.button("Show Rooms"):
        avail, unavail = list_rooms(str(enter), str(exit_date), cap)
        st.session_state["rooms_shown"] = True
        st.session_state["avail_rooms"] = avail
        st.session_state["unavail_rooms"] = unavail
        st.session_state["nights"] = nights

    if st.session_state.get("rooms_shown"):
        avail = st.session_state["avail_rooms"]
        unavail = st.session_state["unavail_rooms"]
        saved_nights = st.session_state.get("nights", nights)

        def make_df(data):
            rows = [[r[0], r[1], r[2], r[2] * saved_nights, r[4]] for r in data]
            return pd.DataFrame(rows, columns=["Room", "Capacity", "Price/Night", "Total", "Info"])

        st.markdown("### Available Rooms")
        st.dataframe(make_df(avail))
        st.markdown("### Unavailable Rooms")
        st.dataframe(make_df(unavail))

        # ---------------- BOOK ----------------
        st.markdown("### Book")
        room_choice = st.number_input("Room Number", step=1)
        if st.button("Pay and Book"):
            ok, receipt, msg = book(st.session_state["user"], room_choice, str(enter), str(exit_date))
            if ok:
                st.success(msg)
                st.markdown("## Receipt")
                st.write(f"Reservation ID: {receipt['Reservation ID']}")
                st.write(f"Room: {receipt['Room']}")
                st.write(f"Amount: {receipt['Price Paid']}")
                st.write(f"Check-in: {receipt['Check-in']}")
                st.write(f"Check-out: {receipt['Check-out']}")
            else:
                st.error(msg)

        # ---------------- CALENDAR ----------------
        st.markdown("### Room Availability Calendar")
        room_for_calendar = st.number_input("Room Number for Calendar", step=1, key="cal")
        if st.button("Show Calendar"):
            dates = []
            for i in range(10):
                d = enter + timedelta(days=i)
                avail_cal, _ = list_rooms(str(d), str(d + timedelta(days=1)), 1)
                dates.append([str(d), "Available" if any(r[0] == room_for_calendar for r in avail_cal) else "Booked"])
            st.table(pd.DataFrame(dates, columns=["Date", "Status"]))

# ––––––––––––––––––––––––––––––––––––––––––
# LOGGED-OUT VIEW
# ––––––––––––––––––––––––––––––––––––––––––

else:
    menu = st.sidebar.selectbox("Menu", ["Login", "Sign Up", "Admin"])

    # –––––––– SIGN UP ––––––––
    if menu == "Sign Up":
        if st.session_state.get("signup_success"):
            st.session_state.pop("signup_success")
            st.success("Account created! You can now log in.")
        else:
            st.subheader("Sign Up")
            name = st.text_input("First Name")
            last = st.text_input("Last Name")
            nid = st.text_input("National ID")
            phone = st.text_input("Phone Number")
            password = st.text_input("Password", type="password")

            if st.button("Sign Up"):
                ok, msg = sign_up(name, last, nid, phone, password)
                if ok:
                    st.session_state["signup_success"] = True
                    st.rerun()
                else:
                    st.error(msg)

    # –––––––– LOGIN ––––––––
    elif menu == "Login":
        st.subheader("Login")
        nid = st.text_input("National ID")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            ok, user_id, msg = login(nid, password)
            if ok:
                st.session_state["user"] = user_id
                st.session_state["user_info"] = get_user(user_id)
                st.rerun()
            else:
                st.error(msg)

    # –––––––– ADMIN PANEL ––––––––
    elif menu == "Admin":
        st.subheader("Admin Panel")
        admin_pass = st.text_input("Admin Password", type="password")

        if admin_pass == "admin123":
            st.success("Admin login successful")

            st.markdown("### Add Room")
            r = st.number_input("Room Number", step=1)
            c = st.number_input("Capacity", 1, 10)
            p = st.number_input("Price per Night")
            s = st.selectbox("Status", ["available", "out_of_service"])
            i = st.text_input("Info")

            if st.button("Add"):
                ok, msg = add_room(r, c, p, s, i)
                st.success(msg) if ok else st.error(msg)

            st.markdown("### Reservations List")
            data = get_all_reservations()
            df = pd.DataFrame(data, columns=["ID", "Customer", "Room", "ReserveTime", "Enter", "Exit", "Nights"])
            st.dataframe(df)

            rid = st.number_input("Reservation ID to cancel", step=1)
            if st.button("Cancel Reservation"):
                ok, msg = cancel_reservation(rid)
                st.success(msg) if ok else st.error(msg)

        elif admin_pass:
            st.error("Wrong admin password")
