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

# --- TAB 2: SALON DASHBOARD ---
# --- TAB 2: SALON DASHBOARD ---
elif app_mode == "💇‍♂️ Salon Dashboard":
    st.title("👑 Salon Management Hub")
    
    # --- SAFE DATA LOADER ---
    try:
        # Get all data from the sheet
        all_data = ws_bookings.get_all_values()
        
        if len(all_data) > 1:  # Check if there is more than just the header row
            df = pd.DataFrame(all_data[1:], columns=all_data[0])
            
            # --- 2. Metrics ---
            # Make sure 'Status' column exists before filtering
            if 'Status' in df.columns:
                pending_count = len(df[df['Status'] == 'Requested'])
                st.metric("New Requests", pending_count)
                
                # --- 3. Booking Queue ---
                st.subheader("📥 Incoming Requests")
                pending_df = df[df['Status'] == 'Requested']
                
                if not pending_df.empty:
                    st.dataframe(pending_df, use_container_width=True)
                    # ... (rest of your confirmation button logic)
                else:
                    st.success("✅ All caught up! No pending requests.")
            else:
                st.error("❌ Column 'Status' not found in Google Sheet!")
        else:
            st.info("📭 The booking queue is currently empty. Try booking an appointment in Client Mode!")
            
    except Exception as e:
        st.error(f"⚠️ Error reading records: {e}")
    
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
