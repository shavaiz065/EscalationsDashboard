import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
from io import BytesIO
from matplotlib.backends.backend_pdf import PdfPages
import datetime
from PIL import Image
import numpy as np
from plotly.io import write_image
import time
import json
import os
import base64
from html2image import Html2Image
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet


# ✅ Set up page config
st.set_page_config(layout="wide", page_title="DMAT - TA Escalations Dashboard", page_icon="📊")

# File to store credentials
CREDENTIALS_FILE = "credentials.json"


# Load credentials
def load_credentials():
    if os.path.exists(CREDENTIALS_FILE):
        try:
            with open(CREDENTIALS_FILE, "r") as file:
                data = json.load(file)
                if "admin" in data and "DMAT" in data:
                    return data  # ✅ Return existing credentials
        except json.JSONDecodeError:
            pass  # Handle corrupted file

    # ✅ Do not reset existing credentials
    default_creds = {
        "admin": {"username": "admin", "password": "dmat123461"},
        "DMAT": {"username": "DMAT", "password": "payactiv123461"}
    }
    save_credentials(default_creds)
    return default_creds



# Save credentials
def save_credentials(credentials):
    with open(CREDENTIALS_FILE, "w") as file:
        json.dump(credentials, file, indent=4)


# Initialize authentication
credentials = load_credentials()



# Login function
def login():
    st.markdown("""
        <style>
            /* Fullscreen Centering */
            .stApp {
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                background: linear-gradient(135deg, #1e3c72 10%, #2a5298 100%);
            }

            /* Modern Glassmorphism Container */
            .login-container {
                width: 400px;
                padding: 3rem;
                border-radius: 16px;
                background: rgba(255, 255, 255, 0.15);
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.37);
                text-align: center;
                backdrop-filter: blur(10px);
                -webkit-backdrop-filter: blur(10px);
                border: 1px solid rgba(255, 255, 255, 0.18);
                transition: all 0.3s ease-in-out;
                margin: auto;
            }

            .login-container:hover {
                box-shadow: 0 12px 40px rgba(0, 0, 0, 0.5);
            }

            /* Title */
            .title {
                font-size: 28px;
                font-weight: bold;
                color: #ffffff;
                text-shadow: 0 0 10px rgba(255, 255, 255, 0.6);
                margin-bottom: 20px;
            }

            /* Highlighted Labels */
            .stTextInput label {
                font-size: 18px;
                font-weight: bold;
                color: #ffffff;
                text-shadow: 0 0 8px rgba(255, 255, 255, 0.5);
            }

            /* Input Fields */
            .stTextInput>div>div>input {
                font-size: 18px;
                padding: 12px;
                border-radius: 8px;
                border: 1px solid rgba(255, 255, 255, 0.5);
                background: rgba(255, 255, 255, 0.2);
                color: white;
                text-align: center;
                transition: all 0.3s ease-in-out;
            }

            .stTextInput>div>div>input:focus {
                box-shadow: 0 0 12px rgba(255, 255, 255, 0.8);
                border-color: #ffffff;
            }

            .stTextInput>div>div>input::placeholder {
                color: rgba(255, 255, 255, 0.6);
                font-style: italic;
            }

            /* Modern Gradient Button */
            .stButton>button {
                width: 100%;
                border-radius: 8px;
                background: linear-gradient(90deg, #00c6ff, #0072ff);
                color: white;
                font-size: 18px;
                padding: 14px;
                border: none;
                font-weight: bold;
                transition: all 0.3s ease-in-out;
                cursor: pointer;
                text-shadow: 0 0 10px rgba(255, 255, 255, 0.8);
            }

            .stButton>button:hover {
                background: linear-gradient(90deg, #0072ff, #00c6ff);
                transform: scale(1.05);
                box-shadow: 0 0 15px rgba(255, 255, 255, 0.8);
            }

            /* Error Message */
            .error {
                color: #ff4f7b;
                font-size: 16px;
                font-weight: bold;
                margin-top: 15px;
                text-shadow: 0 0 8px red;
            }

        </style>
    """, unsafe_allow_html=True)

    # Use a single st.markdown() to avoid extra empty containers
    login_html = """
    <div class="login-container">
        <p class="title">🔐 DMAT Dashboard Login</p>
    </div>
    """
    st.markdown(login_html, unsafe_allow_html=True)

    username = st.text_input("Username", placeholder="Enter your username").strip().lower()
    password = st.text_input("Password", placeholder="Enter your password", type="password")

    if st.button("Login"):
        for user_type, cred in credentials.items():
            if username == cred["username"].strip().lower() and password == cred["password"]:
                st.session_state["authenticated"] = True
                st.session_state["user_type"] = user_type
                st.rerun()

        st.markdown('<p class="error">❌ Invalid username or password</p>', unsafe_allow_html=True)


# Check authentication state
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    login()
    st.stop()  # Stop execution if not authenticated
else:

    # Sidebar Profile Option (Only for Admin)
    with st.sidebar:
        if st.session_state.get("user_type") == "admin":
            if st.button("View Profile"):
                st.subheader("Admin Profile")
                st.write("Username: admin")
                st.write("Role: Admin")

                # Password Change Option Inside Profile
                with st.expander("🔑 Change Password"):
                    new_password = st.text_input("New Password", type="password")
                    confirm_password = st.text_input("Confirm New Password", type="password")

                    if st.button("Update Password"):
                        if new_password == confirm_password:
                            save_credentials("admin", new_password)  # Save new password
                            st.success("Password updated successfully! Please log in again.")
                            st.session_state["authenticated"] = False
                            st.rerun()  # Logout user after password change
                        else:
                            st.error("Passwords do not match!")

# Dashboard theme settings
THEMES = {
    "Default": {
        "bg_gradient": "linear-gradient(135deg, #7F7FD5, #91EAE4)",
        "sidebar_gradient": "linear-gradient(135deg, #83a4d4, #b6fbff)",
        "text_color": "#003366",
        "accent_color": "#4e54c8",
        "chart_colors": px.colors.qualitative.Plotly
    },
    "Dark": {
        "bg_gradient": "linear-gradient(135deg, #0f2027, #203a43, #2c5364)",
        "sidebar_gradient": "linear-gradient(135deg, #232526, #414345)",
        "text_color": "#ffffff",
        "accent_color": "#00b4d8",
        "chart_colors": px.colors.qualitative.Dark24
    },
    "Corporate": {
        "bg_gradient": "linear-gradient(135deg, #f5f7fa, #c3cfe2)",
        "sidebar_gradient": "linear-gradient(135deg, #e0e0e0, #f5f5f5)",
        "text_color": "#2c3e50",
        "accent_color": "#3498db",
        "chart_colors": px.colors.qualitative.Safe
    }
}


# Function to apply custom styling based on theme
def apply_theme(theme_name):
    theme = THEMES.get(theme_name, THEMES["Default"])

    st.markdown(
        f"""
        <style>
        .stApp {{
            background: {theme["bg_gradient"]};
            background-attachment: fixed;
            height: 100vh;
        }}
        .stSidebar {{
            background: {theme["sidebar_gradient"]};
            background-attachment: fixed;
            height: 100%;
            padding: 10px;
        }}
        .main-title {{
            color: {theme["text_color"]} !important;
            font-size: 28px;
            font-weight: bold;
            text-align: center;
            margin-top: 30px;
            font-family: 'Poppins', sans-serif;
        }}
        .sub-title {{
            color: {theme["text_color"]} !important;
            font-size: 22px;
            font-weight: bold;
            text-align: center;
            font-family: 'Poppins', sans-serif;
            margin-bottom: 15px;
        }}
        .metric-card {{
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            transition: transform 0.3s ease;
        }}
        .metric-card:hover {{
            transform: translateY(-5px);
        }}
        /* Custom styling for dataframe */
        .dataframe-container {{
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            margin-bottom: 20px;
        }}
        /* Custom styling for tabs */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 10px;
        }}
        .stTabs [data-baseweb="tab"] {{
            height: 50px;
            white-space: pre-wrap;
            background-color: rgba(255, 255, 255, 0.2);
            border-radius: 5px 5px 0px 0px;
            gap: 1px;
            padding-top: 10px;
            padding-bottom: 10px;
        }}
        .stTabs [aria-selected="true"] {{
            background-color: {theme["accent_color"]};
            color: white;
        }}
        /* Loading animation */
        .loading-spinner {{
            text-align: center;
            padding: 20px;
        }}
        /* Action button */
        .floating-button {{
            position: fixed;
            right: 20px;
            bottom: 20px;
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background-color: {theme["accent_color"]};
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
            cursor: pointer;
            z-index: 1000;
        }}
        /* Tooltip styling */
        .tooltip {{
            position: relative;
            display: inline-block;
        }}
        .tooltip .tooltiptext {{
            visibility: hidden;
            width: 120px;
            background-color: rgba(0,0,0,0.8);
            color: #fff;
            text-align: center;
            border-radius: 6px;
            padding: 5px;
            position: absolute;
            z-index: 1;
            bottom: 125%;
            left: 50%;
            margin-left: -60px;
            opacity: 0;
            transition: opacity 0.3s;
        }}
        .tooltip:hover .tooltiptext {{
            visibility: visible;
            opacity: 1;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# Create session state for user preferences
if 'theme' not in st.session_state:
    st.session_state['theme'] = "Default"
if 'show_tutorial' not in st.session_state:
    st.session_state['show_tutorial'] = True
if 'first_visit' not in st.session_state:
    st.session_state['first_visit'] = True
if 'favorite_charts' not in st.session_state:
    st.session_state['favorite_charts'] = []

# Apply the current theme
apply_theme(st.session_state['theme'])


# Function to process the uploaded file
def process_uploaded_file(file):
    try:
        # Add loading animation
        with st.spinner('Processing your data...'):
            # Determine file type and read accordingly
            if file.name.endswith('.csv'):
                df = pd.read_csv(file)
            else:  # Excel file
                df = pd.read_excel(file)

            # Define your expected headers (use the exact order and names from your sheet)
            expected_headers = [
                "Mode",
                "Type",
                "Escalation Date",
                "Domain",
                "BID",
                "Employer Name",
                "Subject line (Manual TA Escalation)",
                "Parent Category",
                "Case Category",
                "Escalated To"
            ]

            # Check if all expected headers exist in the DataFrame
            missing_headers = [header for header in expected_headers if header not in df.columns]
            if missing_headers:
                st.warning(f"Warning: The following expected columns are missing: {', '.join(missing_headers)}")

            # Convert the escalation date column to datetime if it exists
            if "Escalation Date" in df.columns:
                df["Escalation Date"] = pd.to_datetime(df["Escalation Date"], errors="coerce")
            else:
                st.error("Error: 'Escalation Date' column is required but not found in the uploaded file.")
                return None

            # Make sure essential columns exist
            required_columns = ["Mode", "Type", "Escalation Date", "Domain", "Account name", "Case Category",
                                "Escalated To"]
            for col in required_columns:
                if col not in df.columns:
                    # If column doesn't exist, create it with placeholder values
                    df[col] = "Unknown"

            # Convert string columns to string type to avoid any issues
            string_columns = ["Domain", "Mode", "Type", "Account name", "Case Category", "Escalated To"]
            for col in string_columns:
                if col in df.columns:
                    df[col] = df[col].astype(str)

            # Add data quality indicators
            df_stats = {
                "Total Records": len(df),
                "Missing Values": df.isna().sum().sum(),
                "Data Quality Score": round(100 - (df.isna().sum().sum() / (df.shape[0] * df.shape[1]) * 100), 2)
            }

            # Add month and year columns for better filtering
            if "Escalation Date" in df.columns:
                df["Month"] = df["Escalation Date"].dt.month_name()
                df["Year"] = df["Escalation Date"].dt.year

            return df, df_stats

    except Exception as e:
        st.error(f"Error processing file: {e}")
        import traceback
        traceback.print_exc()
        return None, None


# Function to safely create and display charts with tooltips
def safe_create_chart(chart_function, error_message="Error creating chart"):
    try:
        return chart_function()
    except Exception as e:
        st.error(f"{error_message}: {e}")
        import traceback
        traceback.print_exc()
        return None


# Function to detect anomalies in time series data
def detect_anomalies(time_series):
    # Calculate rolling mean and standard deviation
    rolling_mean = time_series["Count"].rolling(window=3, min_periods=1).mean()
    rolling_std = time_series["Count"].rolling(window=3, min_periods=1).std()

    # Define threshold for anomalies (2 standard deviations)
    threshold = 2

    # Identify anomalies
    anomalies = time_series[abs(time_series["Count"] - rolling_mean) > threshold * rolling_std]

    return anomalies


# Function to create a scorecard with KPI
def create_scorecard(title, value, delta=None, delta_color="normal"):
    card_html = f"""
    <div class="metric-card">
        <h3 style="margin-bottom: 10px;">{title}</h3>
        <div style="font-size: 24px; font-weight: bold;">{value}</div>
    """

    if delta is not None:
        arrow = "↑" if delta > 0 else "↓"
        color = "green" if delta_color == "normal" and delta > 0 else "red"
        color = "red" if delta_color == "inverse" and delta > 0 else color

        card_html += f"""
        <div style="color: {color}; font-size: 16px; margin-top: 5px;">
            {arrow} {abs(delta):.1f}%
        </div>
        """

    card_html += "</div>"
    return card_html


# Function to generate insights from the data
def generate_insights(df):
    insights = []

    # Most common escalation category
    top_category = df["Case Category"].value_counts().idxmax()
    insights.append(f"The most common escalation category is '{top_category}'")

    # Day of week with most escalations
    df['Day of Week'] = df['Escalation Date'].dt.day_name()
    top_day = df['Day of Week'].value_counts().idxmax()
    insights.append(f"Most escalations occur on {top_day}")

    # Month with highest escalations
    df['Month'] = df['Escalation Date'].dt.month_name()
    top_month = df['Month'].value_counts().idxmax()
    insights.append(f"The month with most escalations is {top_month}")

    # Account with most escalations
    top_account = df["Account name"].value_counts().idxmax()
    insights.append(f"Account '{top_account}' has the most escalations")

    return insights


# Function to encode image as Base64
def get_base64(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()



# Function to show tutorial
def show_tutorial():
    tutorial_container = st.container()
    with tutorial_container:
        col1, col2, col3 = st.columns([1, 3, 1])
        with col2:


            # Colorful & big-size "D M A T" text
            st.markdown(
                """
                <style>
                    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@800;900&display=swap');

                    .dmat-container {
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 85vh;
                        background: #0d0d0d;
                        position: relative;
                        overflow: hidden;
                        border-radius: 16px;
                        box-shadow: 0 20px 50px rgba(0, 0, 0, 0.4);
                    }

                    .dmat-container::before {
                        content: '';
                        position: absolute;
                        top: -50%;
                        left: -50%;
                        width: 200%;
                        height: 200%;
                        background: linear-gradient(45deg, 
                            rgba(255, 0, 128, 0.15) 0%, 
                            rgba(255, 140, 0, 0.15) 25%, 
                            rgba(0, 128, 255, 0.15) 50%, 
                            rgba(128, 0, 255, 0.15) 75%, 
                            rgba(255, 0, 128, 0.15) 100%);
                        animation: rotate 20s linear infinite;
                        z-index: 1;
                    }

                    .dmat-container::after {
                        content: '';
                        position: absolute;
                        top: 0;
                        left: 0;
                        right: 0;
                        bottom: 0;
                        background: radial-gradient(circle at center, transparent 30%, #0d0d0d 80%);
                        z-index: 2;
                    }

                    @keyframes rotate {
                        0% { transform: rotate(0deg); }
                        100% { transform: rotate(360deg); }
                    }

                    .particles {
                        position: absolute;
                        top: 0;
                        left: 0;
                        width: 100%;
                        height: 100%;
                        z-index: 3;
                        pointer-events: none;
                    }

                    .particle {
                        position: absolute;
                        width: 6px;
                        height: 6px;
                        border-radius: 50%;
                        background: #fff;
                        opacity: 0;
                        z-index: 3;
                    }

                    @keyframes float-up {
                        0% { transform: translateY(100px); opacity: 0; }
                        10% { opacity: 0.8; }
                        90% { opacity: 0.4; }
                        100% { transform: translateY(-100px); opacity: 0; }
                    }

                    .dmat-text-container {
                        position: relative;
                        z-index: 10;
                        background: rgba(13, 13, 13, 0.7);
                        padding: 40px 50px;
                        border-radius: 16px;
                        backdrop-filter: blur(10px);
                        box-shadow: 0 0 40px rgba(0, 0, 0, 0.2), 
                                    inset 0 0 20px rgba(255, 255, 255, 0.05);
                        border: 1px solid rgba(255, 255, 255, 0.1);
                    }

                    .dmat-text {
                        font-size: 200px;
                        font-family: 'Montserrat', sans-serif;
                        font-weight: 900;
                        display: flex;
                        perspective: 1000px;
                    }

                    .dmat-letter {
                        position: relative;
                        display: inline-block;
                        transition: all 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275);
                        transform-style: preserve-3d;
                        animation: letter-float 3s ease-in-out infinite;
                    }

                    @keyframes letter-float {
                        0%, 100% { transform: translateY(0) rotate(0deg); }
                        50% { transform: translateY(-15px) rotate(2deg); }
                    }

                    .dmat-letter:nth-child(1) {
                        color: #FF3CAC;
                        animation-delay: 0s;
                        text-shadow: 0 0 15px #FF3CAC, 0 0 30px rgba(255, 60, 172, 0.4);
                    }

                    .dmat-letter:nth-child(2) {
                        color: #784BA0;
                        animation-delay: 0.2s;
                        text-shadow: 0 0 15px #784BA0, 0 0 30px rgba(120, 75, 160, 0.4);
                    }

                    .dmat-letter:nth-child(3) {
                        color: #2B86C5;
                        animation-delay: 0.4s;
                        text-shadow: 0 0 15px #2B86C5, 0 0 30px rgba(43, 134, 197, 0.4);
                    }

                    .dmat-letter:nth-child(4) {
                        color: #FF9E00;
                        animation-delay: 0.6s;
                        text-shadow: 0 0 15px #FF9E00, 0 0 30px rgba(255, 158, 0, 0.4);
                    }

                    .dmat-letter:hover {
                        transform: translateY(0) scale(1.2) rotate(5deg);
                        text-shadow: 0 0 30px currentColor, 0 0 60px currentColor;
                        cursor: pointer;
                        z-index: 20;
                    }

                    .dmat-letter::before,
                    .dmat-letter::after {
                        content: attr(data-letter);
                        position: absolute;
                        top: 0;
                        left: 0;
                        opacity: 0;
                        transition: all 0.3s ease;
                    }

                    .dmat-letter::before {
                        transform: translateZ(-10px);
                        color: rgba(255, 255, 255, 0.3);
                        filter: blur(5px);
                    }

                    .dmat-letter::after {
                        transform: translateZ(10px);
                        color: inherit;
                        filter: blur(2px);
                    }

                    .dmat-letter:hover::before,
                    .dmat-letter:hover::after {
                        opacity: 0.6;
                    }

                    .glowing-ring {
                        position: absolute;
                        width: 120%;
                        height: 120%;
                        border-radius: 50%;
                        background: transparent;
                        border: 4px solid transparent;
                        z-index: 1;
                        opacity: 0;
                        transition: opacity 0.3s;
                        box-shadow: 0 0 20px currentColor;
                        border-image: linear-gradient(to right, currentColor, transparent) 1;
                        animation: ring-pulse 2s ease-in-out infinite;
                    }

                    @keyframes ring-pulse {
                        0%, 100% { transform: scale(1); opacity: 0.3; }
                        50% { transform: scale(1.2); opacity: 0.6; }
                    }

                    @media (max-width: 768px) {
                        .dmat-text {
                            font-size: 100px;
                        }

                        .dmat-text-container {
                            padding: 20px;
                        }
                    }
                </style>

                <div class="dmat-container">
                    <div class="particles" id="particles"></div>
                    <div class="dmat-text-container">
                        <div class="dmat-text">
                            <span class="dmat-letter" data-letter="D">D</span>
                            <span class="dmat-letter" data-letter="M">M</span>
                            <span class="dmat-letter" data-letter="A">A</span>
                            <span class="dmat-letter" data-letter="T">T</span>
                        </div>
                    </div>
                </div>

                <script>
                document.addEventListener('DOMContentLoaded', function() {
                    // Create floating particles
                    const particlesContainer = document.getElementById('particles');
                    const particleCount = 30;
                    const colors = ['#FF3CAC', '#784BA0', '#2B86C5', '#FF9E00'];

                    for (let i = 0; i < particleCount; i++) {
                        const particle = document.createElement('div');
                        particle.className = 'particle';

                        // Random position
                        const posX = Math.random() * 100;
                        const posY = Math.random() * 100;

                        // Random size
                        const size = Math.random() * 5 + 2;

                        // Random color
                        const color = colors[Math.floor(Math.random() * colors.length)];

                        // Random animation duration
                        const duration = Math.random() * 10 + 5;

                        // Random animation delay
                        const delay = Math.random() * 5;

                        particle.style.left = posX + '%';
                        particle.style.top = posY + '%';
                        particle.style.width = size + 'px';
                        particle.style.height = size + 'px';
                        particle.style.background = color;
                        particle.style.boxShadow = `0 0 ${size * 2}px ${color}`;
                        particle.style.animation = `float-up ${duration}s ease-in-out ${delay}s infinite`;

                        particlesContainer.appendChild(particle);
                    }

                    // Interactive letters
                    const letters = document.querySelectorAll('.dmat-letter');

                    letters.forEach((letter, index) => {
                        // Create glowing ring for each letter
                        const ring = document.createElement('div');
                        ring.className = 'glowing-ring';
                        ring.style.borderColor = getComputedStyle(letter).color;
                        letter.appendChild(ring);

                        // Add interactive events
                        letter.addEventListener('mouseover', function() {
                            this.querySelector('.glowing-ring').style.opacity = '1';
                        });

                        letter.addEventListener('mouseout', function() {
                            this.querySelector('.glowing-ring').style.opacity = '0';
                        });

                        letter.addEventListener('click', function() {
                            this.style.transform = 'translateY(0) scale(1.5) rotate(360deg)';
                            setTimeout(() => {
                                this.style.transform = '';
                            }, 1000);
                        });
                    });
                });
                </script>
                """,
                unsafe_allow_html=True
            )


# Dashboard Header
st.markdown("<h1 class='main-title'>📊 DMAT - TA Escalations Dashboard</h1>", unsafe_allow_html=True)

# Move the file upload section to the sidebar
st.sidebar.header("Dashboard Settings")

# Theme selector in sidebar
theme_options = list(THEMES.keys())

# Initialize theme in session state if it doesn't exist
if 'theme' not in st.session_state:
    st.session_state['theme'] = theme_options[0]  # Default to first theme

# Get current index for default selection
try:
    current_index = theme_options.index(st.session_state['theme'])
except ValueError:
    # Handle case where saved theme is no longer in options
    current_index = 0
    st.session_state['theme'] = theme_options[0]

# Create the theme selector
selected_theme = st.sidebar.selectbox(
    "Select Theme",
    theme_options,
    index=current_index,
    key="theme_selector"  # Add a unique key
)

# Check if theme has changed and update
if selected_theme != st.session_state['theme']:
    st.session_state['theme'] = selected_theme
    # Use the non-experimental rerun (for newer Streamlit versions)
    try:
        st.rerun()
    except AttributeError:
        # Fallback for older Streamlit versions
        st.experimental_rerun()

st.sidebar.header("Data Upload")
st.sidebar.markdown("<h3>Upload your data file</h3>", unsafe_allow_html=True)
uploaded_file = st.sidebar.file_uploader("Choose a CSV or Excel file", type=["csv", "xlsx", "xls"])

# Show tutorial on first visit
if st.session_state['show_tutorial'] and st.session_state['first_visit']:
    show_tutorial()
    st.session_state['first_visit'] = False

# Rest of the sidebar filters (will be shown after file is uploaded)
if uploaded_file is not None:
    # Process the uploaded file
    df, df_stats = process_uploaded_file(uploaded_file)

    if df is not None and not df.empty:
        # Add navigation tabs
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "📈 Detailed Analysis", "🔍 Data Explorer", "💡 Insights"])

        with tab1:
            # Sidebar Filters
            st.sidebar.header("Filters")

            # Advanced filtering options
            filter_container = st.sidebar.expander("Advanced Filters", expanded=False)
            with filter_container:
                # Case Category Dropdown
                try:
                    # Check if the column exists
                    if "Case Category" in df.columns:
                        case_categories = df["Case Category"].unique().tolist()
                    else:
                        case_categories = []  # Default to empty list if column not found
                except Exception as e:
                    print(f"Error getting Case Category unique values: {e}")
                    case_categories = []

                selected_category = st.selectbox("Search Case Category", ["All"] + case_categories)

                # Account Name Dropdown
                try:
                    # Check if the column exists
                    if "Employer Name" in df.columns:
                        # Clean and process account names
                        account_names = df["Employer Name"].dropna().unique().tolist()

                        # Remove 'unknown' and empty entries, convert to strings, and remove duplicates
                        account_names = sorted(set(
                            str(name).strip() for name in account_names
                            if str(name).strip() and
                            str(name).strip().lower() != 'unknown'
                        ))
                    else:
                        account_names = []  # Default to empty list if column not found
                except Exception as e:
                    print(f"Error getting Employer Name unique values: {e}")
                    account_names = []

                # Select Account dropdown with all employer names
                selected_account = st.selectbox("Select Account", ["All"] + account_names)

                # Month and Year filters
                if "Month" in df.columns and "Year" in df.columns:
                    # Convert month values to strings and filter out any non-string values
                    month_values = [str(x) for x in df["Month"].unique() if isinstance(x, str) or not pd.isna(x)]

                    # Only try to sort if there are valid month names
                    try:
                        months = ["All"] + sorted(month_values, key=lambda x: datetime.datetime.strptime(x,
                                                                                                         "%B").month if x.strip() else 0)
                    except ValueError:
                        # If sorting fails, just use the unsorted list
                        months = ["All"] + month_values

                    years = ["All"] + sorted([x for x in df["Year"].unique().tolist() if not pd.isna(x)])

                    selected_month = st.selectbox("Select Month", months)
                    selected_year = st.selectbox("Select Year", years)

            # Date Range Filter
            start_date = st.sidebar.date_input("Start Date", df["Escalation Date"].min().date() if not pd.isna(
                df["Escalation Date"].min()) else datetime.date.today())
            end_date = st.sidebar.date_input("End Date", df["Escalation Date"].max().date() if not pd.isna(
                df["Escalation Date"].max()) else datetime.date.today())

            # Initialize df_filtered with the full dataframe
            df_filtered = df.copy()

            # Apply Date Range Filter
            df_filtered = df_filtered[(df_filtered["Escalation Date"] >= pd.to_datetime(start_date)) &
                                      (df_filtered["Escalation Date"] <= pd.to_datetime(end_date))]

            # Apply Category Filter
            if selected_category != "All":
                df_filtered = df_filtered[df_filtered["Case Category"] == selected_category]

            # Apply Account Filter
            if selected_account != "All":
                df_filtered = df_filtered[df_filtered["Employer Name"] == selected_account]

            # Apply Month and Year filters if they exist
            if "Month" in df.columns and "Year" in df.columns:
                if selected_month != "All":
                    df_filtered = df_filtered[df_filtered["Month"] == selected_month]
                if selected_year != "All":
                    df_filtered = df_filtered[df_filtered["Year"] == selected_year]


            # Make sure df_filtered contains data
            if df_filtered.empty:
                st.warning("No data matches the selected filters. Please adjust your filter criteria.")
            else:
                # Animated loading
                with st.spinner("Loading dashboard..."):
                    time.sleep(0.5)  # Simulate loading for smoother transitions

                    # Calculate period-over-period changes for KPIs
                    # Get previous period data (assuming same length as current filtered period)
                    current_period_start = pd.to_datetime(start_date)
                    current_period_end = pd.to_datetime(end_date)
                    period_length = (current_period_end - current_period_start).days

                    previous_period_end = current_period_start - datetime.timedelta(days=1)
                    previous_period_start = previous_period_end - datetime.timedelta(days=period_length)

                    df_previous = df[(df["Escalation Date"] >= previous_period_start) &
                                     (df["Escalation Date"] <= previous_period_end)]

                    # Calculate change percentages
                    current_total = len(df_filtered)
                    previous_total = len(df_previous) if not df_previous.empty else 0
                    total_change_pct = (
                                (current_total - previous_total) / previous_total * 100) if previous_total > 0 else 0

                    current_domains = len(df_filtered["Domain"].unique())
                    previous_domains = len(df_previous["Domain"].unique()) if not df_previous.empty else 0
                    domains_change_pct = ((
                                                      current_domains - previous_domains) / previous_domains * 100) if previous_domains > 0 else 0

                    current_categories = len(df_filtered["Case Category"].unique())
                    previous_categories = len(df_previous["Case Category"].unique()) if not df_previous.empty else 0
                    categories_change_pct = ((
                                                         current_categories - previous_categories) / previous_categories * 100) if previous_categories > 0 else 0

                    # Data quality score
                    data_quality = df_stats["Data Quality Score"] if df_stats else 98.5

                    # Enhanced KPIs with scorecards
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric(
                            label="📌 Total Escalations",
                            value=current_total,
                            delta=f"{total_change_pct:.1f}%" if total_change_pct != 0 else None,
                            delta_color="inverse" if total_change_pct > 0 else "normal"
                        )
                    with col2:
                        st.metric(
                            label="🌐 Total Domains",
                            value=current_domains,
                            delta=f"{domains_change_pct:.1f}%" if domains_change_pct != 0 else None,
                            delta_color="inverse" if domains_change_pct > 0 else "normal"
                        )
                    with col3:
                        st.metric(
                            label="📑 Escalation Categories",
                            value=current_categories,
                            delta=f"{categories_change_pct:.1f}%" if categories_change_pct != 0 else None,
                            delta_color="inverse" if categories_change_pct > 0 else "normal"
                        )
                    with col4:
                        st.metric(
                            label="💯 Data Quality",
                            value=f"{data_quality:.2f}%",
                            delta=None
                        )

                    # Display Table with enhanced styling
                    st.markdown("<h2 class='sub-title'>Escalation Data</h2>", unsafe_allow_html=True)
                    with st.container():
                        st.markdown('<div class="dataframe-container">', unsafe_allow_html=True)
                        st.dataframe(df_filtered, use_container_width=True)
                        st.markdown('</div>', unsafe_allow_html=True)

                    # Graphs in Horizontal Layout with enhanced interactivity
                    col1, col2 = st.columns(2)

                    with col1:
                        st.markdown(
                            "<h2 class='sub-title' style='white-space: nowrap;'>📌 Escalations by Case Category</h2>",
                            unsafe_allow_html=True)


                        def create_category_chart():
                            category_counts = df_filtered["Case Category"].value_counts().reset_index()
                            category_counts.columns = ["Case Category", "Count"]
                            fig1 = px.bar(category_counts, x="Case Category", y="Count", text="Count",
                                          color="Case Category",
                                          color_discrete_sequence=THEMES[st.session_state['theme']]["chart_colors"])
                            fig1.update_layout(
                                autosize=True,
                                margin=dict(t=20, b=20, l=20, r=20),
                                height=450,
                                hovermode="closest",
                                hoverlabel=dict(bgcolor="white", font_size=12, font_family="Arial"),
                                transition_duration=500  # Animation duration
                            )
                            # Add custom hover template
                            fig1.update_traces(
                                hovertemplate="<b>%{x}</b><br>Count: %{y}<br>Percentage: %{customdata:.1f}%",
                                customdata=[(count / category_counts["Count"].sum()) * 100 for count in
                                            category_counts["Count"]]
                            )
                            return fig1, category_counts


                        result = safe_create_chart(create_category_chart, "Error creating Case Category chart")
                        if result:
                            fig1, category_counts = result
                            st.plotly_chart(fig1, use_container_width=True, config={'displayModeBar': True})

                    with col2:
                        st.markdown("<h2 class='sub-title'>📈 Escalation Trend Over Time</h2>", unsafe_allow_html=True)


                        def create_time_series_chart():
                            time_series = df_filtered.groupby("Escalation Date").size().reset_index(name="Count")

                            # Detect anomalies
                            anomalies = detect_anomalies(time_series)

                            # Create line chart
                            fig2 = px.line(time_series, x="Escalation Date", y="Count", markers=True,
                                           color_discrete_sequence=[THEMES[st.session_state['theme']]["accent_color"]])

                            # Add anomaly points
                            if not anomalies.empty:
                                fig2.add_trace(go.Scatter(
                                    x=anomalies["Escalation Date"],
                                    y=anomalies["Count"],
                                    mode="markers",
                                    marker=dict(color="red", size=10, symbol="circle"),
                                    name="Anomaly",
                                    hovertemplate="<b>Anomaly</b><br>Date: %{x}<br>Count: %{y}<extra></extra>"
                                ))

                            # Add moving average
                            ma = time_series["Count"].rolling(window=3, min_periods=1).mean()
                            fig2.add_trace(go.Scatter(
                                x=time_series["Escalation Date"],
                                y=ma,
                                mode="lines",
                                line=dict(color="rgba(0,0,0,0.3)", width=2, dash="dot"),
                                name="3-day MA",
                                hovertemplate="<b>3-day Moving Avg</b><br>Date: %{x}<br>Value: %{y:.1f}<extra></extra>"
                            ))

                            fig2.update_layout(
                                height=450,
                                margin=dict(t=0, b=0, l=0, r=0),
                                hovermode="x unified",
                                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                                transition_duration=500  # Animation duration
                            )
                            return fig2, time_series, anomalies


                        result = safe_create_chart(create_time_series_chart, "Error creating Time Series chart")
                        if result:
                            fig2, time_series, anomalies = result
                            st.plotly_chart(fig2, use_container_width=True, key="fig2")

                            # Show anomaly alerts if any exist
                            if not anomalies.empty:
                                with st.expander("📊 Anomaly Detection"):
                                    st.warning(f"Detected {len(anomalies)} anomalies in the time series data.")
                                    st.dataframe(anomalies[["Escalation Date", "Count"]])

                    if 'category_counts' in locals():
                        col4, col5 = st.columns(2)
                        with col4:
                            st.markdown("<h2 class='sub-title'>📌 Top 5 Most Escalated Categories</h2>",
                                        unsafe_allow_html=True)


                            def create_top5_chart():
                                top5_categories = category_counts.nlargest(5, "Count")
                                fig4 = px.bar(top5_categories, x="Case Category", y="Count", text="Count",
                                              color="Case Category",
                                              color_discrete_sequence=THEMES[st.session_state['theme']]["chart_colors"])
                                fig4.update_layout(
                                    height=400,
                                    margin=dict(t=0, b=0, l=0, r=0),
                                    hoverlabel=dict(bgcolor="white", font_size=12, font_family="Arial"),
                                    transition_duration=500  # Animation duration
                                )
                                return fig4


                            fig4 = safe_create_chart(create_top5_chart, "Error creating Top 5 Categories chart")
                            if fig4:
                                st.plotly_chart(fig4, use_container_width=True, key="fig4")

                        with col5:
                            st.markdown("<h2 class='sub-title'>Escalation Trends Across the Week</h2>",
                                        unsafe_allow_html=True)


                            def create_day_trend_chart():
                                df_filtered['Day of Week'] = df_filtered['Escalation Date'].dt.day_name()
                                day_counts = df_filtered['Day of Week'].value_counts().reset_index()
                                day_counts.columns = ['Day of Week', 'Count']
                                # Sort the days in correct order
                                days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday',
                                              'Sunday']
                                day_counts['Day of Week'] = pd.Categorical(day_counts['Day of Week'],
                                                                           categories=days_order,
                                                                           ordered=True)
                                day_counts = day_counts.sort_values('Day of Week')

                                # Create toggleable chart type
                                chart_type = "line"  # Default chart type

                                if chart_type == "line":
                                    fig5 = px.line(day_counts, x='Day of Week', y='Count', markers=True,
                                                   color_discrete_sequence=[
                                                       THEMES[st.session_state['theme']]["accent_color"]])
                                else:
                                    fig5 = px.bar(day_counts, x='Day of Week', y='Count', text='Count',
                                                  color_discrete_sequence=[
                                                      THEMES[st.session_state['theme']]["accent_color"]])

                                fig5.update_layout(
                                    height=400,
                                    margin=dict(t=0, b=0, l=0, r=0),
                                    hovermode="x unified",
                                    transition_duration=500  # Animation duration
                                )
                                return fig5, day_counts


                            result = safe_create_chart(create_day_trend_chart, "Error creating Day Trend chart")
                            if result:
                                fig5, day_counts = result
                                # Add chart type selector
                                chart_type = st.selectbox("Chart Type", ["Line Chart", "Bar Chart"],
                                                          key="day_chart_type")
                                if chart_type == "Bar Chart":
                                    fig5 = px.bar(day_counts, x='Day of Week', y='Count', text='Count',
                                                  color_discrete_sequence=[
                                                      THEMES[st.session_state['theme']]["accent_color"]])
                                st.plotly_chart(fig5, use_container_width=True, key="fig5")

                    col6, col7 = st.columns(2)
                    with col6:
                        st.markdown("<h2 class='sub-title'>Escalations by Mode</h2>", unsafe_allow_html=True)


                        def create_mode_chart():
                            mode_counts = df_filtered["Mode"].value_counts().reset_index()
                            mode_counts.columns = ["Mode", "Count"]
                            fig6 = px.pie(mode_counts, values="Count", names="Mode", hole=0.4,
                                          color_discrete_sequence=THEMES[st.session_state['theme']]["chart_colors"])
                            fig6.update_layout(
                                height=400,
                                margin=dict(t=0, b=0, l=0, r=0),
                                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
                                transition_duration=500  # Animation duration
                            )
                            # Add percentage and count to hover info
                            fig6.update_traces(
                                hovertemplate="<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent:.1%}<extra></extra>"
                            )
                            return fig6, mode_counts


                        fig6, mode_counts = safe_create_chart(create_mode_chart, "Error creating Mode chart")
                        if fig6:
                            st.plotly_chart(fig6, use_container_width=True, key="fig6")

                            # Escalation Distribution by Assignees
                            st.markdown("<h2 class='sub-title'>🔹 Escalation Distribution by Assignees</h2>",
                                        unsafe_allow_html=True)


                            def create_assignee_chart():
                                assigned_counts = df_filtered["Escalated To"].value_counts().reset_index()
                                assigned_counts.columns = ["Escalated To", "Count"]
                                assigned_counts["Percentage"] = (assigned_counts["Count"] / assigned_counts[
                                    "Count"].sum()) * 100
                                fig6 = px.pie(assigned_counts, names="Escalated To", values="Count",
                                              title="Escalation Distribution", hole=0.3)
                                fig6.update_traces(textinfo="label+percent+value", hoverinfo="label+value+percent",
                                                   textposition="inside")
                                fig6.update_layout(height=400)
                                return fig6, assigned_counts


                            result = safe_create_chart(create_assignee_chart, "Error creating Assignee chart")
                            if result:
                                fig3, assigned_counts = result
                                st.plotly_chart(fig3, use_container_width=True, key="fig3")

                            with col7:
                                st.markdown("<h2 class='sub-title'>Escalations by Domain</h2>", unsafe_allow_html=True)


                                def create_domain_chart():
                                    # Print for debugging
                                    print("Domain column data type:", df_filtered['Domain'].dtype)
                                    print("Domain column head:", df_filtered['Domain'].head())

                                    # Ensure Domain is string type
                                    df_filtered['Domain'] = df_filtered['Domain'].astype(str)

                                    domain_counts = df_filtered['Domain'].value_counts().reset_index()
                                    domain_counts.columns = ['Domain', 'Count']

                                    # For debugging
                                    print("Domain counts:", domain_counts.head())

                                    fig7 = px.bar(domain_counts, x='Domain', y='Count', text='Count', color='Domain')
                                    fig7.update_layout(height=400)
                                    return fig7, domain_counts


                                result = safe_create_chart(create_domain_chart, "Error creating Domain chart")
                                if result:
                                    fig7, domain_counts = result
                                    st.plotly_chart(fig7, use_container_width=True, key="fig7")

        # After your existing tab1 code
        with tab2:  # Detailed Analysis Tab
            st.markdown("<h2 class='sub-title'>Detailed Analysis</h2>", unsafe_allow_html=True)

            # Create sub-tabs for different types of analysis
            analysis_tab1, analysis_tab2 = st.tabs(
                ["Trend Analysis", "Category Deep Dive"])

            with analysis_tab1:
                st.markdown("### Trend Analysis")

                # Monthly trend
                st.markdown("#### Monthly Trend")

                if not df_filtered.empty:
                    # Group by month
                    df_filtered['Month-Year'] = df_filtered['Escalation Date'].dt.strftime('%b %Y')
                    monthly_trend = df_filtered.groupby('Month-Year').size().reset_index(name='Count')

                    # Create a line chart
                    fig_monthly = px.line(monthly_trend, x='Month-Year', y='Count', markers=True,
                                          title="Monthly Escalation Trend",
                                          color_discrete_sequence=[THEMES[st.session_state['theme']]["accent_color"]])

                    fig_monthly.update_layout(height=400)
                    st.plotly_chart(fig_monthly, use_container_width=True)

                    # Forecast future trend (simple moving average)
                    st.markdown("#### Forecast (3-month Moving Average)")

                    if len(monthly_trend) > 3:
                        monthly_trend['MA3'] = monthly_trend['Count'].rolling(window=3).mean()

                        # Extend the dataframe with forecast
                        last_3_avg = monthly_trend['Count'].tail(3).mean()
                        forecast_months = pd.date_range(start=df_filtered['Escalation Date'].max(), periods=4, freq='M')
                        forecast_labels = [d.strftime('%b %Y') for d in forecast_months]

                        forecast_df = pd.DataFrame({
                            'Month-Year': monthly_trend['Month-Year'].tolist() + forecast_labels[1:],
                            'Count': monthly_trend['Count'].tolist() + [last_3_avg] * 3,
                            'Type': ['Historical'] * len(monthly_trend) + ['Forecast'] * 3
                        })

                        fig_forecast = px.line(forecast_df, x='Month-Year', y='Count', color='Type',
                                               title="Historical Data with 3-Month Forecast",
                                               color_discrete_sequence=[
                                                   THEMES[st.session_state['theme']]["accent_color"], 'red'])

                        fig_forecast.update_layout(height=400)
                        st.plotly_chart(fig_forecast, use_container_width=True)
                    else:
                        st.info("Need more data points for forecasting.")
                else:
                    st.warning("Insufficient data for trend analysis.")

            with analysis_tab2:
                st.markdown("### Category Deep Dive")

                # Category distribution over time
                st.markdown("#### More Features can be added")


                # Check if we have the necessary data
                if 'Category' not in df_filtered.columns or 'Agent' not in df_filtered.columns:
                    st.info("Workload distribution data not available. Showing sample metrics.")

                    # Create sample data
                    categories = ['Network', 'Hardware', 'Software', 'Access', 'Security', 'Other']
                    agents = ['Smith, J.', 'Johnson, K.', 'Williams, T.', 'Brown, A.', 'Davis, M.']

                    # Create sample workload distribution
                    workload_data = []
                    for agent in agents:
                        total_tickets = np.random.randint(30, 60)
                        # Distribute tickets across categories
                        ticket_distrib = np.random.dirichlet(np.ones(len(categories)), size=1)[0]
                        ticket_counts = (ticket_distrib * total_tickets).astype(int)

                        for i, category in enumerate(categories):
                            workload_data.append({
                                'Agent': agent,
                                'Category': category,
                                'Tickets': ticket_counts[i]
                            })

                    df_workload = pd.DataFrame(workload_data)

                    # Create pivot table
                    pivot_workload = df_workload.pivot_table(
                        index='Agent',
                        columns='Category',
                        values='Tickets',
                        aggfunc='sum',
                        fill_value=0
                    )

                    # Add total column
                    pivot_workload['Total'] = pivot_workload.sum(axis=1)

                    # Calculate team workload breakdown
                    category_totals = df_workload.groupby('Category')['Tickets'].sum().reset_index()
                    total_tickets = category_totals['Tickets'].sum()
                    category_totals['Percentage'] = (category_totals['Tickets'] / total_tickets * 100).round(1)


        with tab3:  # Data Explorer Tab
            st.markdown("<h2 class='sub-title'>Data Explorer</h2>", unsafe_allow_html=True)

            # Advanced filtering
            st.markdown("### Advanced Data Filtering")

            # Create filter columns
            filter_col1, filter_col2, filter_col3 = st.columns(3)

            with filter_col1:
                # Filter by Case Category
                if "Case Category" in df.columns:
                    case_categories = ["All"] + list(df["Case Category"].unique())
                    selected_category_filter = st.selectbox("Filter by Case Category", case_categories,
                                                            key="explorer_category")

                # Filter by Domain
                if "Domain" in df.columns:
                    domains = ["All"] + list(df["Domain"].unique())
                    selected_domain_filter = st.selectbox("Filter by Domain", domains)

            with filter_col2:
                # Filter by Mode
                if "Mode" in df.columns:
                    modes = ["All"] + list(df["Mode"].unique())
                    selected_mode_filter = st.selectbox("Filter by Mode", modes)

                # Filter by Type
                if "Type" in df.columns:
                    types = ["All"] + list(df["Type"].unique())
                    selected_type_filter = st.selectbox("Filter by Type", types)

            with filter_col3:
                # Search by account name
                search_account = st.text_input("Search by Account Name")

                # Search by subject
                if "Subject line (Manual TA Escalation)" in df.columns:
                    search_subject = st.text_input("Search by Subject")

            # Apply filters
            filtered_explorer_df = df.copy()

            if selected_category_filter != "All" and "Case Category" in df.columns:
                filtered_explorer_df = filtered_explorer_df[
                    filtered_explorer_df["Case Category"] == selected_category_filter]

            if selected_domain_filter != "All" and "Domain" in df.columns:
                filtered_explorer_df = filtered_explorer_df[filtered_explorer_df["Domain"] == selected_domain_filter]

            if selected_mode_filter != "All" and "Mode" in df.columns:
                filtered_explorer_df = filtered_explorer_df[filtered_explorer_df["Mode"] == selected_mode_filter]

            if selected_type_filter != "All" and "Type" in df.columns:
                filtered_explorer_df = filtered_explorer_df[filtered_explorer_df["Type"] == selected_type_filter]

            if search_account and "Account name" in df.columns:
                filtered_explorer_df = filtered_explorer_df[
                    filtered_explorer_df["Account name"].str.contains(search_account, case=False, na=False)]

            if search_subject and "Subject line (Manual TA Escalation)" in df.columns:
                filtered_explorer_df = filtered_explorer_df[
                    filtered_explorer_df["Subject line (Manual TA Escalation)"].str.contains(search_subject, case=False,
                                                                                             na=False)]

            # Display the filtered data
            st.markdown("### Filtered Data")
            st.dataframe(filtered_explorer_df, use_container_width=True)

        with tab4:  # Insights Tab
            st.markdown("<h2 class='sub-title'>Insights</h2>", unsafe_allow_html=True)

            # Generate insights
            if not df_filtered.empty:
                insights = generate_insights(df_filtered)

                # Display insights
                st.markdown("### Key Insights")

                for i, insight in enumerate(insights):
                    st.markdown(f"**{i + 1}. {insight}**")

                # Top accounts by escalation
                st.markdown("### Top Accounts by Escalation Count")

                top_accounts = df_filtered["Account name"].value_counts().head(10).reset_index()
                top_accounts.columns = ["Account Name", "Escalation Count"]

                fig_accounts = px.bar(top_accounts, x="Account Name", y="Escalation Count",
                                      title="Top 10 Accounts by Escalation Count",
                                      color_discrete_sequence=[THEMES[st.session_state['theme']]["accent_color"]])

                st.plotly_chart(fig_accounts, use_container_width=True)

                # Daily escalation patterns (alternative to hourly heatmap)
                st.markdown("### Daily Escalation Patterns")

                # Extract just the day of week
                df_filtered['Day of Week'] = pd.to_datetime(df_filtered['Escalation Date']).dt.day_name()

                # Ensure days are ordered correctly
                day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                df_filtered['Day of Week'] = pd.Categorical(df_filtered['Day of Week'], categories=day_order,
                                                            ordered=True)

                # Count escalations by day
                day_counts = df_filtered['Day of Week'].value_counts().sort_index()

                # Create bar chart
                fig_day = px.bar(
                    x=day_counts.index,
                    y=day_counts.values,
                    labels={'x': 'Day of Week', 'y': 'Number of Escalations'},
                    title='Escalations by Day of Week',
                    color=day_counts.values,  # Color by count value
                    color_continuous_scale=px.colors.sequential.Viridis
                )

                # Customize appearance
                fig_day.update_layout(
                    xaxis_title="Day of Week",
                    yaxis_title="Number of Escalations",
                    coloraxis_showscale=True,
                    coloraxis_colorbar=dict(title="Count")
                )

                # Display in Streamlit
                st.plotly_chart(fig_day, use_container_width=True)

                # Recommendations
                st.markdown("### Recommendations")

                recommendations = [
                    "Focus on the most common escalation category to reduce overall volume.",
                    f"Allocate more resources on {df_filtered['Day of Week'].value_counts().idxmax()} when escalation volume is highest.",
                    "Implement proactive measures for accounts with high escalation counts.",
                    "Consider additional training for domains with high escalation rates.",
                    "Review the SLA process for escalations that took longer than the target response time."
                ]

                for i, rec in enumerate(recommendations):
                    st.markdown(f"**{i + 1}. {rec}**")
            else:
                st.warning("Not enough data to generate insights. Please adjust your filters.")
