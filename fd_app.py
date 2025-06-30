import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import gspread
from google.oauth2.service_account import Credentials
import os
import json
from io import StringIO
from PIL import Image
import hmac
import time

# Page config for better display on all devices
st.set_page_config(
    page_title="Fixed Deposit Repository",
    layout="centered",  # changed from "wide" to "centered"
    initial_sidebar_state="collapsed"
)

# Add password protection mechanism
def check_password():
    """Returns `True` if the user had the correct password."""
    
    import time
    import os  # Add this import
    
    # Initialize session state variables
    if "login_attempts" not in st.session_state:
        st.session_state["login_attempts"] = 0
    if "last_attempt_time" not in st.session_state:
        st.session_state["last_attempt_time"] = time.time()
    
    # Password is correct - allow access
    if st.session_state.get("password_correct", False):
        return True
    
    # Try to get credentials from secrets
    try:
        correct_username = st.secrets["admin_username"]
        correct_password = st.secrets["admin_password"]
    except Exception:
        # For local development, fallback to environment variables or defaults
        import os
        correct_username = os.environ.get("ADMIN_USERNAME", "admin")
        correct_password = os.environ.get("ADMIN_PASSWORD", "default_local_password")
    
    # If too many failed attempts, add a time delay
    if st.session_state["login_attempts"] >= 3:
        # Check if enough time has passed since last attempt (30 seconds cooldown)
        if time.time() - st.session_state["last_attempt_time"] < 30:
            remaining = int(30 - (time.time() - st.session_state["last_attempt_time"]))
            st.error(f"Too many failed attempts. Please try again in {remaining} seconds.")
            return False
        else:
            # Reset attempts after cooldown period
            st.session_state["login_attempts"] = 0
    
    # Display a clean login form with matching styling
    st.markdown("""
    <style>
    .login-container {
        max-width: 500px;
        margin: 0 auto;
        padding: 30px;
        background-color: #f8f9fa;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .login-header {
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 25px;
    }
    .login-logo {
        margin-right: 15px;
    }
    .login-title {
        color: #692B30;
        font-size: 1.8rem;
        font-weight: 700;
        display: inline-block;
        vertical-align: middle;
        border-bottom: 2px solid #692B30;
        padding-bottom: 5px;
    }
    .login-input-label {
        font-weight: 500 !important;
        color: #692B30 !important;
        font-size: 1.1rem !important;
        margin-bottom: 0.5rem !important;
    }
    .login-button {
        background-color: #f0f0f0;
        color: #692B30 !important;
        font-weight: bold;
        border-radius: 5px;
        border: 1px solid #ddd;
        padding: 10px 20px;
        margin-top: 20px;
        width: 100%;
        cursor: pointer;
    }
    .login-button:hover {
        background-color: #e0e0e0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("<div class='login-container'>", unsafe_allow_html=True)
    
    # Create header with logo and title, similar to main app
    st.markdown("<div class='login-header'>", unsafe_allow_html=True)
    
    # Check if logo exists and display it
    if os.path.exists('emblem2.png'):
        from PIL import Image  # Add this import too
        image = Image.open('emblem2.png')
        col1, col2 = st.columns([1, 5])
        
        with col1:
            st.image(image, width=60)
        
        with col2:
            st.markdown("<div class='login-title'>Fixed Deposit Repository</div>", unsafe_allow_html=True)
    else:
        # If logo not found, just display the title
        st.markdown("<div class='login-title' style='text-align: center;'>Fixed Deposit Repository</div>", unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Create login form
    st.markdown("<p class='login-input-label'>Username</p>", unsafe_allow_html=True)
    username = st.text_input("Username", key="username_input", label_visibility="collapsed")
    
    st.markdown("<p class='login-input-label'>Password</p>", unsafe_allow_html=True)
    password = st.text_input("Password", type="password", key="password_input", label_visibility="collapsed")
    
    if st.button("Login"):
        st.session_state["last_attempt_time"] = time.time()
        
        if username == correct_username and password == correct_password:
            st.session_state["password_correct"] = True
            st.session_state["username"] = username
            st.session_state["login_attempts"] = 0
            st.rerun()  # Force a rerun to update the page
        else:
            st.session_state["login_attempts"] += 1
            remaining_attempts = max(0, 3 - st.session_state["login_attempts"])
            st.error(f"Incorrect username or password. {remaining_attempts} attempts remaining.")
    
    st.markdown("</div>", unsafe_allow_html=True)
    return False

# Check password before showing the actual app
if not check_password():
    st.stop()  # This will halt the app from continuing if password is incorrect

# Custom CSS for better styling with increased font sizes and improved readability
# Extra CSS specificity to ensure the main title is burgundy
st.markdown("""
<style>
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* More specific selectors for the main title with burgundy color */
    .main h1, h1, .st-emotion-cache-1egp7eo h1, div.st-emotion-cache-zt5igj h1, header h1 {
        color: #692B30 !important;
        text-align: center;
        margin-bottom: 1.5rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #692B30;
        font-size: 2.5rem !important;
        font-weight: 700 !important;
    }
    
    /* Additional styles for main title - more specificity */
    [data-testid="stAppViewContainer"] h1, 
    .stApp h1, 
    .element-container h1,
    .st-emotion-cache-10trblm {
        color: #692B30 !important;
    }
    
    /* Style for inline title */
    .inline-title {
        color: #692B30;
        font-size: 2.5rem;
        font-weight: 700;
        margin-top: 0.5rem;
        margin-bottom: 1.5rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #692B30;
        display: inline-block;
        vertical-align: middle;
    }
    
    /* Align logo vertically */
    .logo-img {
        vertical-align: middle;
        margin-right: 15px;
    }
    
    /* Increase subheader font size and change to burgundy */
    h2, .subheader, h3, h4, h5, h6 {
        color: #692B30 !important;
        font-size: 1.8rem !important;
        font-weight: 600 !important;
        margin-top: 1rem;
        margin-bottom: 1.5rem;
    }
    
    /* Tab styling with larger font and burgundy color */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    
    .stTabs [data-baseweb="tab"] {
        font-size: 1.2rem !important;
        font-weight: 600 !important;
        color: #692B30 !important;
    }
    
    /* Make buttons more appealing with burgundy text */
    .stButton > button {
        width: 100%;
        font-weight: bold;
        border-radius: 5px;
        height: 3rem;
        font-size: 1.1rem !important;
        color: #692B30 !important;
    }
    
    /* Button inner text color */
    .stButton > button span {
        color: #692B30 !important;
    }
    
    /* More visible result section with burgundy header */
    .result-box {
        padding: 1.2rem;
        background-color: #f0f9ff;
        border-radius: 5px;
        margin: 1.2rem 0;
        border-left: 4px solid #692B30;
        font-size: 1.1rem !important;
    }
    
    .result-box strong {
        color: #692B30;
    }
    
    /* Dataframe styling with burgundy headers */
    .dataframe {
        border-collapse: collapse;
        width: 100%;
        font-size: 1.1rem !important;
    }
    .dataframe th {
        border: 1px solid #ddd;
        padding: 10px;
        text-align: left !important;
        background-color: #f2f2f2;
        color: #692B30 !important;
        font-weight: 600 !important;
        font-size: 1.1rem !important;
    }
    .dataframe td {
        border: 1px solid #ddd;
        padding: 10px;
        text-align: center !important;
        font-size: 1.1rem !important;
    }
    .dataframe tr:nth-child(even) {
        background-color: #f9f9f9;
    }
    .dataframe tr:hover {
        background-color: #f1f1f1;
    }
    
    /* Input field labels in burgundy */
    label, .stSelectbox label, .stNumberInput label, .stDateInput label, p, .stTextInput label {
        font-weight: 500 !important;
        color: #692B30 !important;
        font-size: 1.1rem !important;
        margin-bottom: 0.5rem !important;
    }
    
    /* Selectbox and input text */
    .stSelectbox, .stNumberInput, .stDateInput, .stTextInput {
        font-size: 1.1rem !important;
    }
    
    /* About section text */
    .st-expander p, .st-expander li {
        font-size: 1.1rem !important;
    }
    
    /* Success/info/error messages headers */
    .stSuccess div:first-child, .stInfo div:first-child, .stError div:first-child, .stWarning div:first-child {
        color: #692B30 !important;
        font-weight: 600 !important;
    }
    
    /* Expander header in burgundy */
    .st-expander details summary {
        color: #692B30 !important;
        font-weight: 600 !important;
    }
    
    /* Download button text color */
    .stDownloadButton button span {
        color: #692B30 !important;
        font-weight: 600 !important;
    }
    
    /* Strong and bold text in burgundy */
    strong, b {
        color: #692B30 !important;
    }
    
    /* Remove horizontal padding to allow better alignment */
    .css-1n76uvr, .css-18e3th9, .stMarkdown {
        padding-left: 0 !important;
        padding-right: 0 !important;
    }
    
    /* Responsive design adjustments */
    @media (max-width: 768px) {
        .main .block-container {
            padding: 1rem;
        }
        h1 {
            font-size: 2rem !important;
        }
        h2, .subheader, h3 {
            font-size: 1.5rem !important;
        }
        .inline-title {
            font-size: 1.8rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# Create a container for the logo and title side by side
col1, col2 = st.columns([1, 6])  # First column for logo, second for title

# Display logo in first column
with col1:
    try:
        # Check if the image file exists
        if os.path.exists('emblem2.png'):
            image = Image.open('emblem2.png')
            # Display the image with a specific width
            st.image(image, width=70)  # Adjust width as needed
        else:
            st.warning("Logo image 'emblem2.png' not found in the current directory")
    except Exception as e:
        st.warning(f"Error loading logo image: {e}")

# Display title in second column
with col2:
    st.markdown("<div class='inline-title'>Fixed Deposit Repository</div>", unsafe_allow_html=True)

# Function to authenticate with Google Sheets
def authenticate_google_sheets():
    # Check if credentials.json exists in the current directory
    if os.path.exists('credentials.json'):
        try:
            # Local development - load from file
            credentials = Credentials.from_service_account_file(
                'credentials.json',
                scopes=['https://www.googleapis.com/auth/spreadsheets']
            )
            return gspread.authorize(credentials)
        except Exception as e:
            st.error(f"Error loading credentials.json: {e}")
    
    # Try using Streamlit secrets as fallback
    try:
        credentials_dict = st.secrets["gcp_service_account"]
        credentials = Credentials.from_service_account_info(
            credentials_dict,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        return gspread.authorize(credentials)
    except Exception as e:
        # If both methods fail, use mock data for testing
        st.warning("No valid Google credentials found. Using local storage for testing.")
        return None

# Function to load data from Google Sheets
def load_fd_data():
    try:
        # Get sheet ID from secrets or use a default for local testing
        sheet_id = ""
        
        # Try to get from secrets if available
        try:
            sheet_id = st.secrets["spreadsheet_id"]
        except Exception:
            # For local development without secrets
            if os.path.exists('.local_config'):
                with open('.local_config', 'r') as f:
                    sheet_id = f.read().strip()
            else:
                # No sheet ID available - will use local storage
                pass
        
        client = authenticate_google_sheets()
        
        # If client is None, we're using local storage for testing
        if client is None:
            # Check if we have a local CSV file
            if os.path.exists('fd_data.csv'):
                df = pd.read_csv('fd_data.csv')
                # Convert date strings to datetime objects
                try:
                    df["StartDate"] = pd.to_datetime(df["StartDate"])
                    df["MaturityDate"] = pd.to_datetime(df["MaturityDate"])
                except:
                    pass
                return df
            else:
                return create_empty_dataframe()
        
        # Otherwise, proceed with Google Sheets
        sheet = client.open_by_key(sheet_id).worksheet("Sheet1")
        data = sheet.get_all_records()
        
        # Convert to DataFrame
        df = pd.DataFrame(data) if data else create_empty_dataframe()
        
        # Ensure all expected columns exist
        expected_columns = ["Bank", "FD_Number", "Principal", "Rate", "StartDate", 
                           "Duration", "Compounding", "MaturityAmount", "MaturityDate"]
        
        for col in expected_columns:
            if col not in df.columns:
                if col in ["Principal", "Rate", "MaturityAmount"]:
                    df[col] = 0.0
                elif col in ["StartDate", "MaturityDate"]:
                    df[col] = pd.Timestamp.now().strftime("%Y-%m-%d")
                else:
                    df[col] = ""
        
        # Convert date strings to datetime objects
        try:
            df["StartDate"] = pd.to_datetime(df["StartDate"])
            df["MaturityDate"] = pd.to_datetime(df["MaturityDate"])
        except:
            # If conversion fails, keep as strings
            pass
            
        return df
    
    except Exception as e:
        st.warning(f"Error loading data from Google Sheets: {e}. Using local storage instead.")
        # Try to load from local CSV as fallback
        if os.path.exists('fd_data.csv'):
            df = pd.read_csv('fd_data.csv')
            # Convert date strings to datetime objects
            try:
                df["StartDate"] = pd.to_datetime(df["StartDate"])
                df["MaturityDate"] = pd.to_datetime(df["MaturityDate"])
            except:
                pass
            return df
        else:
            return create_empty_dataframe()

# Helper function to create empty dataframe with correct structure
def create_empty_dataframe():
    return pd.DataFrame({
        "Bank": pd.Series(dtype='str'),
        "FD_Number": pd.Series(dtype='str'),
        "Principal": pd.Series(dtype='float'),
        "Rate": pd.Series(dtype='float'),
        "StartDate": pd.Series(dtype='datetime64[ns]'),
        "Duration": pd.Series(dtype='str'),
        "Compounding": pd.Series(dtype='str'),
        "MaturityAmount": pd.Series(dtype='float'),
        "MaturityDate": pd.Series(dtype='datetime64[ns]')
    })

# Function to save data to Google Sheets
def save_fd_data(data):
    try:
        # Get sheet ID from secrets or use a default for local testing
        sheet_id = ""
        
        # Try to get from secrets if available
        try:
            sheet_id = st.secrets["spreadsheet_id"]
        except Exception:
            # For local development without secrets
            if os.path.exists('.local_config'):
                with open('.local_config', 'r') as f:
                    sheet_id = f.read().strip()
            else:
                # No sheet ID available - will use local storage
                pass
        
        # Create a copy of the dataframe to avoid modifying the original
        data_copy = data.copy()
        
        # Convert numeric columns to strings with quotes to prevent date interpretation
        for col in ["Rate", "MaturityAmount", "Principal"]:
            if col in data_copy.columns:
                data_copy[col] = data_copy[col].astype(str)
        
        # Convert datetime columns to strings safely
        for col in ["StartDate", "MaturityDate"]:
            if col in data_copy.columns:
                # Check if the column contains datetime objects
                if pd.api.types.is_datetime64_any_dtype(data_copy[col]):
                    data_copy[col] = data_copy[col].dt.strftime("%Y-%m-%d")
                elif len(data_copy) > 0 and isinstance(data_copy[col].iloc[0], (datetime, pd.Timestamp)):
                    data_copy[col] = data_copy[col].apply(lambda x: x.strftime("%Y-%m-%d") if isinstance(x, (datetime, pd.Timestamp)) else str(x))
                else:
                    # If it's already a string or another type, convert to string
                    data_copy[col] = data_copy[col].astype(str)
        
        client = authenticate_google_sheets()
        
        # If client is None, we're using local storage for testing
        if client is None:
            # Save to CSV file
            data_copy.to_csv('fd_data.csv', index=False)
            st.success("Data saved to local CSV file for testing")
            return True
        
        # Otherwise proceed with Google Sheets
        sheet = client.open_by_key(sheet_id).worksheet("Sheet1")
        
        # Convert DataFrame to list of dictionaries
        data_dict = data_copy.to_dict('records')
        
        # Clear existing data
        sheet.clear()
        
        # Write headers and data
        if data_dict:
            headers = list(data_dict[0].keys())
            sheet.append_row(headers)
            
            # Prepare values to append
            values = []
            for row in data_dict:
                values.append([row.get(header, "") for header in headers])
            
            # Append all rows at once
            if values:
                sheet.append_rows(values)
                
            # Format numeric columns as numbers to prevent date interpretation
            if len(values) > 0:
                try:
                    # Get column indices for numeric columns
                    col_indices = {}
                    for col in ["Rate", "MaturityAmount", "Principal"]:
                        if col in headers:
                            col_indices[col] = headers.index(col) + 1  # 1-based indexing in sheets API
                    
                    # Apply number formatting to each numeric column
                    for col, idx in col_indices.items():
                        sheet.format(f"{chr(64 + idx)}2:{chr(64 + idx)}{len(values) + 1}", {
                            "numberFormat": {"type": "NUMBER", "pattern": "0.00"}
                        })
                except Exception as format_error:
                    st.warning(f"Warning: Could not apply number formatting: {format_error}")
        
        return True
    
    except Exception as e:
        st.warning(f"Error saving to Google Sheets: {e}. Saving to local file instead.")
        
        # Save to CSV file as fallback
        try:
            # Create a copy of the dataframe
            data_copy = data.copy()
            
            # Convert all columns to strings safely
            for col in data_copy.columns:
                if col in ["Rate", "MaturityAmount", "Principal"]:
                    data_copy[col] = data_copy[col].astype(str)
                elif col in ["StartDate", "MaturityDate"]:
                    data_copy[col] = data_copy[col].astype(str)
                
            data_copy.to_csv('fd_data.csv', index=False)
            st.success("Data saved to local CSV file as fallback")
            return True
        except Exception as csv_e:
            st.error(f"Also failed to save to CSV: {csv_e}")
            return False

# Function to calculate FD maturity
def calc_maturity(principal, rate, start_date, duration, compounding):
    rate = rate / 100
    
    # Determine compounding frequency
    n = {"Yearly": 1, "Half Yearly": 2, "Quarterly": 4, "Monthly": 12}[compounding]
    
    # Calculate duration in years - MODIFIED to match Shiny logic
    years = duration.get('years', 0)
    months = duration.get('months', 0)
    days = duration.get('days', 0)
    
    # Calculate fractional duration in years directly (matching Shiny logic)
    duration_years = years + (months / 12) + (days / 365)
    
    # Calculate maturity amount
    maturity_amount = principal * (1 + rate / n) ** (n * duration_years)
    
    # Calculate maturity date using duration_years * 365 (matching Shiny logic)
    maturity_date = start_date + timedelta(days=int(duration_years * 365))
    
    return {
        'maturity_amount': round(maturity_amount, 2),
        'maturity_date': maturity_date
    }

# Initialize session state for storing data
if 'fd_data' not in st.session_state:
    st.session_state.fd_data = load_fd_data()

if 'calculation_result' not in st.session_state:
    st.session_state.calculation_result = None

if 'show_calculator' not in st.session_state:
    st.session_state.show_calculator = True

# Add tabs for different sections
tab1, tab2 = st.tabs(["Add/Calculate FD", "View/Manage FDs"])

with tab1:
    # FD Calculator and Add FD Form
    with st.container():
        st.subheader("Fixed Deposit Calculator")
        
        # Bank selection with conditional other bank input
        col1, col2 = st.columns(2)
        
        with col1:
            bank = st.selectbox(
                "Bank Name",
                options=["SBI", "HDFC", "ICICI", "Axis", "Kotak", 
                        "Punjab National Bank", "Bank of Baroda", "Canara Bank", 
                        "IDBI Bank", "Indian Bank", "Central Bank of India", 
                        "Union Bank", "Others"]
            )
        
        with col2:
            if bank == "Others":
                other_bank = st.text_input("Enter Bank Name")
            else:
                other_bank = ""
            
            # Modified: Changed "FD Number" to "FD Account Number"
            fd_number = st.text_input("FD Account Number")
        
        # Principal amount and interest rate
        col1, col2 = st.columns(2)
        
        with col1:
            principal = st.number_input("Principal Amount (₹)", min_value=0.0, value=10000.0, step=1000.0, format="%.2f")
        
        with col2:
            rate = st.number_input("Interest Rate (%)", min_value=0.0, max_value=20.0, value=5.5, step=0.1, format="%.2f")
        
        # Start date and duration
        col1, col2 = st.columns(2)
        
        with col1:
            start_date = st.date_input("Start Date", value=datetime.now())
        
        with col2:
            compounding = st.selectbox(
                "Compounding",
                options=["Yearly", "Half Yearly", "Quarterly", "Monthly"]
            )
        
        # Duration
        col1, col2, col3 = st.columns(3)
        
        with col1:
            duration_years = st.number_input("Duration (Years)", min_value=0, value=1)
        
        with col2:
            duration_months = st.number_input("Duration (Months)", min_value=0, value=0)
        
        with col3:
            duration_days = st.number_input("Duration (Days)", min_value=0, value=0)
        
        # Calculate button
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown('<div class="calculate-btn">', unsafe_allow_html=True)
            calculate_button = st.button("Calculate Maturity", use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="add-btn">', unsafe_allow_html=True)
            add_fd_button = st.button("Add Fixed Deposit", use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Calculate maturity if button is clicked
        if calculate_button:
            if duration_years == 0 and duration_months == 0 and duration_days == 0:
                st.error("Duration must be greater than 0")
            else:
                duration = {"years": duration_years, "months": duration_months, "days": duration_days}
                result = calc_maturity(principal, rate, start_date, duration, compounding)
                st.session_state.calculation_result = result
        
        # Display calculation result if available
        if st.session_state.calculation_result:
            st.markdown('<div class="result-box">', unsafe_allow_html=True)
            st.markdown(f"""
            **Calculation Result:**  
            Maturity Amount: ₹{st.session_state.calculation_result['maturity_amount']:,.2f}  
            Maturity Date: {st.session_state.calculation_result['maturity_date'].strftime('%Y-%m-%d')}
            """)
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Add FD to the list if button is clicked
        if add_fd_button:
            if duration_years == 0 and duration_months == 0 and duration_days == 0:
                st.error("Duration must be greater than 0")
            elif not fd_number:
                st.error("Please enter an FD Account Number")
            else:
                # Calculate maturity if not already calculated
                if not st.session_state.calculation_result:
                    duration = {"years": duration_years, "months": duration_months, "days": duration_days}
                    result = calc_maturity(principal, rate, start_date, duration, compounding)
                else:
                    result = st.session_state.calculation_result
                
                # Create a new row
                new_row = pd.DataFrame({
                    "Bank": [other_bank if bank == "Others" else bank],
                    "FD_Number": [fd_number],
                    "Principal": [principal],
                    "Rate": [rate],
                    "StartDate": [start_date],
                    "Duration": [f"{duration_years} years {duration_months} months {duration_days} days"],
                    "Compounding": [compounding],
                    "MaturityAmount": [result['maturity_amount']],
                    "MaturityDate": [result['maturity_date']]
                })
                
                # Add the new row to existing data
                st.session_state.fd_data = pd.concat([st.session_state.fd_data, new_row], ignore_index=True)
                
                # Reset calculation result
                st.session_state.calculation_result = None
                
                # Show success message
                st.success("Fixed Deposit added successfully!")
                
                # Switch to the second tab
                st.query_params.tab='View/Manage FDs'

with tab2:
    # View and manage FDs
    with st.container():
        st.subheader("Manage Fixed Deposits")
        
        # Display FD table
        if not st.session_state.fd_data.empty:
            # Add a Row ID column starting from 1 (instead of 0)
            display_df = st.session_state.fd_data.copy()
            
            # Add the Row ID column with values starting from 1
            display_df.reset_index(inplace=True)
            display_df['index'] = display_df['index'] + 1
            display_df.rename(columns={'index': 'Row ID'}, inplace=True)
            
            # Rename columns as requested
            display_df.rename(columns={
                'FD_Number': 'FD Number',
                'Rate': 'Rate (%)',
                'StartDate': 'Start Date',
                'MaturityAmount': 'Maturity Amount',
                'MaturityDate': 'Maturity Date'
            }, inplace=True)

            # Ensure FD Number is treated as string to avoid Arrow serialization warnings
            display_df['FD Number'] = display_df['FD Number'].astype(str)
            
            # Reorder columns - keep Row ID first, then Bank, FD Number
            cols = display_df.columns.tolist()
            cols.remove('Bank')
            cols.remove('FD Number')
            cols.remove('Row ID')
            cols = ['Row ID', 'Bank', 'FD Number'] + cols
            display_df = display_df[cols]
            
            # Format the DataFrame for display
            display_df['Principal'] = display_df['Principal'].apply(lambda x: f"₹{x:,.2f}")
            display_df['Maturity Amount'] = display_df['Maturity Amount'].apply(lambda x: f"₹{x:,.2f}")
            
            if 'Start Date' in display_df.columns:
                display_df['Start Date'] = pd.to_datetime(display_df['Start Date']).dt.strftime('%Y-%m-%d')
            
            if 'Maturity Date' in display_df.columns:
                display_df['Maturity Date'] = pd.to_datetime(display_df['Maturity Date']).dt.strftime('%Y-%m-%d')
            
            # Display the formatted DataFrame without the index column
            st.dataframe(display_df, use_container_width=True, hide_index=True)
            
            # Delete row functionality
            col1, col2 = st.columns([3, 1])
            
            with col1:
                # Create options with 1-based indexing for display
                options = list(range(len(st.session_state.fd_data)))
                
                row_to_delete = st.selectbox(
                    "Select Row to Delete",
                    options=options,
                    format_func=lambda x: f"Row {x+1}: {st.session_state.fd_data.iloc[x]['Bank']} - {st.session_state.fd_data.iloc[x]['FD_Number']}"
                )
            
            with col2:
                st.markdown('<div class="delete-btn">', unsafe_allow_html=True)
                delete_button = st.button("Delete Selected Row", use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            if delete_button:
                # Note: We need to delete from the original dataframe, not the display one
                st.session_state.fd_data = st.session_state.fd_data.drop(index=row_to_delete)
                st.session_state.fd_data.reset_index(drop=True, inplace=True)
                st.success(f"Row {row_to_delete+1} deleted successfully!")
                st.rerun()
            
            # Save and Download buttons in separate columns
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown('<div class="save-btn">', unsafe_allow_html=True)
                save_button = st.button("Save Data to Google Sheets", use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col2:
                # Create a CSV download button
                st.markdown('<div class="save-btn">', unsafe_allow_html=True)
                
                # Prepare the data for download (convert to CSV)
                csv_data = st.session_state.fd_data.copy()
                
                # Convert dates to strings safely
                for col in ["StartDate", "MaturityDate"]:
                    if col in csv_data.columns:
                        # Check if the column contains datetime objects
                        if pd.api.types.is_datetime64_any_dtype(csv_data[col]):
                            csv_data[col] = csv_data[col].dt.strftime('%Y-%m-%d')
                        elif len(csv_data) > 0 and (isinstance(csv_data[col].iloc[0], datetime) or 
                                                    isinstance(csv_data[col].iloc[0], pd.Timestamp)):
                            csv_data[col] = csv_data[col].apply(lambda x: x.strftime("%Y-%m-%d") if isinstance(x, (datetime, pd.Timestamp)) else str(x))
                        else:
                            # If it's already a string or another type, convert to string
                            csv_data[col] = csv_data[col].astype(str)
                
                csv = csv_data.to_csv(index=False)
                st.download_button(
                    label="Download as CSV",
                    data=csv,
                    file_name="fixed_deposits.csv",
                    mime="text/csv",
                    use_container_width=True
                )
                st.markdown('</div>', unsafe_allow_html=True)
            
            if save_button:
                if save_fd_data(st.session_state.fd_data):
                    st.success("Data saved to Google Sheets successfully!")
                else:
                    st.error("Failed to save data to Google Sheets.")
        
        else:
            st.info("No Fixed Deposits added yet. Use the Add/Calculate FD tab to add a new Fixed Deposit.")
