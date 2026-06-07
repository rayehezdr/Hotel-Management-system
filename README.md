# Hotel-Management-system

A simple hotel reservation app built with Streamlit and SQLite. Customers can sign up, search rooms by date, and book them. Admins can add rooms and manage reservations.

## Tech Stack

Python, Streamlit, SQLite, pandas.

## Project Structure

├── app.py          # Streamlit frontend  
├── backend.py      # Database logic  
└── database.sql    # Schema

## Setup
pip install streamlit pandas
streamlit run app.py

The app opens at http://localhost:8501.

## Usage

- Customer: Sign up, log in, pick dates and capacity, then book a room.
- Admin: Select “Admin” from the sidebar and enter the password (default: admin123) to add rooms or cancel reservations.

## Database

Four tables: Rooms, Customers, Reservations, Payments. A trigger sets payment_time automatically on insert.

## Known Limitations

- Passwords stored in plaintext — add hashing before deployment.
- Admin password hardcoded in app.py — move to an env variable for production.

##Author

Zahra Zolghadriha     
email: rayehezdr@gmail.com
