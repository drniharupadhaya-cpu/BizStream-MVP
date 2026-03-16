import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

# --- 1. SECURE CONNECTION ---
# This assumes you have your streamlit secrets set up
try:
    # Replace 'BizStream-MVP' with the exact name of your Google Sheet
    # Ensure the Google Service Account email is shared with the sheet!
    sheet_name = "BizStream-MVP"
    
    # We use gspread logic similar to your RBSK app
    from google.oauth2.service_account import Credentials
    import gspread

    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    client = gspread.authorize(creds)
    spreadsheet = client.open(sheet_name)
    
    ws_bookings = spreadsheet.worksheet("salon_bookings")
    ws_services = spreadsheet.worksheet("salon_services")
    
except Exception as e:
    st.error(f"⚠️ Connection Error: {e}")

# --- 2. SIDEBAR NAVIGATION ---
app_mode = st.sidebar.selectbox("Choose Mode", ["📅 Client Booking", "💇‍♂️ Salon Dashboard"])

# --- TAB 1: CLIENT BOOKING ---
if app_mode == "📅 Client Booking":
    st.title("✂️ Style & Shine Salon")
    st.markdown("### Book Your Transformation")

    with st.form("booking_form", clear_on_submit=True):
        name = st.text_input("Full Name")
        phone = st.text_input("Mobile Number")
        service = st.selectbox("Service Desired", ["Haircut", "Hair Color", "Facial", "Shaving/Beard"])
        date = st.date_input("Preferred Date", min_value=datetime.today())
        time_slot = st.selectbox("Preferred Time", ["10 AM", "11 AM", "12 PM", "1 PM", "3 PM", "4 PM", "5 PM", "6 PM"])
        
        submit = st.form_submit_button("Request Appointment")

        if submit:
            if name and phone:
                # Add to 'salon_bookings' tab
                # Column structure: Date, Name, Phone, Service, Time, Status
                new_row = [str(date), name, phone, service, time_slot, "Requested"]
                ws_bookings.append_row(new_row)
                st.balloons()
                st.success(f"Perfect, {name}! We've received your request for {time_slot}. Hang tight!")
            else:
                st.warning("Please provide your name and phone number!")

elif app_mode == "💇‍♂️ Salon Dashboard":
    st.title("👑 Salon Management Hub")
    
    try:
        # 1. Fetch the raw headers directly from Row 1
        headers = ws_bookings.row_values(1)
        
        # 2. DEBUG: Show us exactly what Python sees
        st.write("🔍 **Deep Scan Results:**")
        st.write(f"The computer sees these columns: `{headers}`")
        
        # 3. Check for the word 'Status'
        if "Status" in headers:
            st.success("✅ Match Found! 'Status' is present.")
        else:
            st.error("❌ Match Not Found!")
            # Show the "Ghost" - This shows if there are hidden spaces
            for h in headers:
                st.code(f"Column: '{h}' | Length: {len(h)}")

    except Exception as e:
        st.error(f"Error: {e}")
    
    # 4. Service Log (Internal Record Keeping)
    st.subheader("📝 Complete Service Log")
    with st.form("service_log"):
        c_name = st.text_input("Client Name (Searchable later)")
        formula = st.text_area("Color Formula / Notes")
        price = st.number_input("Amount Collected (₹)", min_value=0)
        log_submit = st.form_submit_button("Save Records")
        
        if log_submit:
            ws_services.append_row([str(datetime.now().date()), c_name, formula, price])
            st.success("Record saved safely.")
