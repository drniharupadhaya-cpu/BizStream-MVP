import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import urllib.parse

# --- LUXURY STYLING ---
st.markdown("""
    <style>
    /* Main background and text */
    .stApp {
        background-color: #0E1117;
        color: #C5A059;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #161B22;
        border-right: 2px solid #C5A059;
    }
    
    /* Headings */
    h1, h2, h3 {
        color: #D4AF37 !important;
        font-family: 'Playfair Display', serif;
    }
    
    /* Buttons */
    div.stButton > button:first-child {
        background-color: #D4AF37;
        color: #000000;
        border-radius: 20px;
        border: none;
        font-weight: bold;
        transition: 0.3s;
    }
    
    div.stButton > button:hover {
        background-color: #C5A059;
        color: white;
        box-shadow: 0 0 15px #D4AF37;
    }

    /* Input Boxes */
    input, textarea {
        background-color: #1C2128 !important;
        color: #D4AF37 !important;
        border: 1px solid #C5A059 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 1. SECURE CONNECTION ---
try:
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    client = gspread.authorize(creds)
    spreadsheet = client.open("BizStream-MVP")
    ws_bookings = spreadsheet.worksheet("salon_bookings")
    ws_services = spreadsheet.worksheet("salon_services")
except Exception as e:
    st.error(f"⚠️ Connection Error: {e}")

# --- 2. WHATSAPP LOGIC ---
def get_wa_link(phone, name, time, service):
    clean_phone = ''.join(filter(str.isdigit, phone))
    if not clean_phone.startswith('91'): clean_phone = '91' + clean_phone
    msg = f"Hello {name}, this is Style & Shine Salon! ✨ Confirming your {service} for {time}. See you then!"
    return f"https://wa.me/{clean_phone}?text={urllib.parse.quote(msg)}"

# --- 3. NAVIGATION ---
app_mode = st.sidebar.selectbox("Choose Mode", ["📅 Client Booking", "💇‍♂️ Salon Dashboard"])

# --- TAB 1: CLIENT BOOKING ---
if app_mode == "📅 Client Booking":
    st.title("✂️ Style & Shine Salon")
    with st.form("booking_form", clear_on_submit=True):
        name = st.text_input("Full Name")
        phone = st.text_input("Mobile Number")
        service = st.selectbox("Service", ["Haircut", "Hair Color", "Facial", "Beard Trim"])
        date = st.date_input("Date", min_value=datetime.today())
        time = st.selectbox("Time", ["10 AM", "11 AM", "12 PM", "2 PM", "4 PM", "6 PM"])
        if st.form_submit_button("Request Appointment"):
            if name and phone:
                ws_bookings.append_row([str(date), name, phone, service, time, "Requested"])
                st.balloons()
                st.success("Request Sent! We will contact you shortly.")

# --- TAB 2: SALON DASHBOARD ---
elif app_mode == "💇‍♂️ Salon Dashboard":
    st.title("👑 Salon Command Center")
    
    # --- LOAD DATA ---
    all_rows = ws_bookings.get_all_values()
    if len(all_rows) > 1:
        df = pd.DataFrame(all_rows[1:], columns=all_rows[0])
        df.columns = [c.strip() for c in df.columns] # Clean hidden spaces
        
        pending = df[df['Status'] == 'Requested']
        
        col1, col2 = st.columns(2)
        col1.metric("Pending Requests", len(pending))
        
        st.subheader("📥 New Requests")
        if not pending.empty:
            st.dataframe(pending, use_container_width=True)
            
            # --- ACTION AREA ---
            with st.expander("✅ Process Appointment"):
                client_to_fix = st.selectbox("Select Client", pending['Name'].tolist())
                client_data = pending[pending['Name'] == client_to_fix].iloc[0]
                
                # WhatsApp Button
                wa_url = get_wa_link(client_data['Phone'], client_data['Name'], client_data['Time'], client_data['Service'])
                st.link_button(f"💬 WhatsApp {client_to_fix}", wa_url)
                
                if st.button(f"Mark {client_to_fix} as Confirmed"):
                    cell = ws_bookings.find(client_to_fix)
                    ws_bookings.update_cell(cell.row, 6, "Confirmed")
                    st.success("Status Updated!")
                    st.rerun()
        else:
            st.write("No new requests.")
    
    st.divider()
    st.subheader("📝 Service Log (Formulas & Payments)")
    with st.form("service_log", clear_on_submit=True):
        c_name = st.text_input("Client Name")
        formula = st.text_area("Formula/Notes")
        price = st.number_input("Amount (₹)", min_value=0)
        if st.form_submit_button("Save Service Record"):
            ws_services.append_row([str(datetime.now().date()), c_name, formula, price])
            st.success("Record saved!")
