import streamlit as st

st.set_page_config(layout="wide")  # This will enable full page width layout
# Custom Background Color for Live Dashboard
st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(135deg, #7F7FD5, #91EAE4);
        background-attachment: fixed; /* This makes the gradient fixed while scrolling */
        height: 100vh; /* Optional: Makes sure gradient covers the full page height */
    }
    </style>
    """,
    unsafe_allow_html=True
)

import matplotlib
print(matplotlib.__version__)
import gspread
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt  # Yeh line yahan add kar di hai 🔥
from io import BytesIO
from matplotlib.backends.backend_pdf import PdfPages
import datetime
from google.oauth2 import service_account
import PIL.Image  # Yeh bhi zaroori hai PDF ka format theek karne ke liye
# Access secrets
gcp_creds = st.secrets["gcp_service_account"]

# Use creds from Streamlit secrets
creds = service_account.Credentials.from_service_account_info(gcp_creds)


# Google Sheets API setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_file("creds.json", scopes=scope)
client = gspread.authorize(creds)

# Google Sheet details
spreadsheet_id = "11FoqJicHt3BGpzAmBnLi1FQFN-oeTxR_WGKszARDcR4"  # Replace with your actual ID
worksheet_name = "Sheet1"  # Update if different

try:
    sheet = client.open_by_key(spreadsheet_id).worksheet(worksheet_name)
    data = sheet.get_all_values()

    # Convert to DataFrame
    df = pd.DataFrame(data)

    # Rename first row as column headers
    df.columns = df.iloc[0]
    df = df[1:].reset_index(drop=True)

    # Remove duplicate 'Escalation Date' column (keep first occurrence - Column C)
    df = df.loc[:, ~df.columns.duplicated()]

    # Selecting required columns
    selected_columns = ["Mode", "Type", "Escalation Date", "Domain", "Account name", "Case Category", "Escalated To"]
    df = df[selected_columns]

    # Convert 'Escalation Date' to datetime
    df["Escalation Date"] = pd.to_datetime(df["Escalation Date"], errors="coerce")

    # Apply Custom Styling to Utilize Full Page
    st.markdown(
        """
        <style>
        .main-title {
            color: #003366 !important;
            font-size: 28px;
            font-weight: bold;
            text-align: center;
            margin-top: 30px; /* Add some top margin */
            font-family: 'Poppins', sans-serif;
        }
        .sub-title {
            color: black !important;
            font-size: 22px;
            font-weight: bold;
            text-align: center;
            font-family: 'Poppins', sans-serif;
        }
        /* Keep the rest of your styles the same or remove them if needed */
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <style>
        .stSidebar {
            background: linear-gradient(135deg, #83a4d4, #b6fbff); /* Gradient color */
            background-attachment: fixed; /* Keeps gradient fixed while scrolling */
            height: 100%; /* Full sidebar coverage */
            padding: 10px; /* Optional: Add padding */
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Sidebar Filters
    st.sidebar.header("Filters")

    # Case Category Dropdown
    case_categories = df["Case Category"].unique().tolist()
    selected_category = st.sidebar.selectbox("Search Case Category", ["All"] + case_categories)

    # Account Name Dropdown
    account_names = df["Account name"].unique().tolist()
    selected_account = st.sidebar.selectbox("Search Account Name", ["All"] + account_names)

    # Date Range Filter
    start_date = st.sidebar.date_input("Start Date", df["Escalation Date"].min())
    end_date = st.sidebar.date_input("End Date", df["Escalation Date"].max())

    # Apply Filters
    df_filtered = df[(df["Escalation Date"] >= pd.to_datetime(start_date)) &
                     (df["Escalation Date"] <= pd.to_datetime(end_date))]

    if selected_category != "All":
        df_filtered = df_filtered[df_filtered["Case Category"] == selected_category]

    if selected_account != "All":
        df_filtered = df_filtered[df_filtered["Account name"] == selected_account]

    # Streamlit Dashboard
    st.markdown("<h1 class='main-title'>📊 DMAT - TA Escalations Dashboard</h1>", unsafe_allow_html=True)

    # KPIs
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="📌 Total Escalations", value=len(df_filtered))
    with col2:
        st.metric(label="🌐 Total Domains", value=df_filtered["Domain"].nunique())
    with col3:
        st.metric(label="📑 Total Escalation Categories", value=df_filtered["Case Category"].nunique())

    # Display Table on Top
    st.markdown("<h2 class='sub-title'>Escalation Data</h2>", unsafe_allow_html=True)
    st.dataframe(df_filtered)

    # Graphs in Horizontal Layout
    col1, col2 = st.columns(2)

    with col1:
        with col1:
            st.markdown("<h2 class='sub-title' style='white-space: nowrap;'>📌 Escalations by Case Category</h2>",
                        unsafe_allow_html=True)
            category_counts = df_filtered["Case Category"].value_counts().reset_index()
            category_counts.columns = ["Case Category", "Count"]
            fig1 = px.bar(category_counts, x="Case Category", y="Count", text="Count", color="Case Category")

            fig1.update_layout(
                autosize=True,  # Graph ko automatic container ke size ke mutabiq set karega
                margin=dict(t=20, b=20, l=20, r=20),  # Margins ko kam karega
                height=450  # Height ko thoda zyada set karega
            )

            st.plotly_chart(fig1, use_container_width=True)  # Container width ko enable karega

    with col2:
        st.markdown("<h2 class='sub-title'>📈 Escalation Trend Over Time</h2>", unsafe_allow_html=True)
        time_series = df_filtered.groupby("Escalation Date").size().reset_index(name="Count")
        fig2 = px.line(time_series, x="Escalation Date", y="Count", markers=True)
        fig2.update_layout(height=450, margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(fig2, use_container_width=True, key="fig2")

    col4, col5 = st.columns(2)
    with col4:
        st.markdown("<h2 class='sub-title'>📌 Top 5 Most Escalated Categories</h2>", unsafe_allow_html=True)
        top5_categories = category_counts.nlargest(5, "Count")
        fig4 = px.bar(top5_categories, x="Case Category", y="Count", text="Count", color="Case Category")
        fig4.update_layout(height=400, margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(fig4, use_container_width=True, key="fig4")

    with col5:
        st.markdown("<h2 class='sub-title'>Escalation Trends Across the Week</h2>", unsafe_allow_html=True)
        df_filtered['Day of Week'] = df_filtered['Escalation Date'].dt.day_name()
        day_counts = df_filtered['Day of Week'].value_counts().reset_index()
        day_counts.columns = ['Day of Week', 'Count']
        fig5 = px.line(day_counts, x='Day of Week', y='Count', markers=True)
        fig5.update_layout(height=400, margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(fig5, use_container_width=True, key="fig5")

    col6, col7 = st.columns(2)
    with col6:
        st.markdown("<h2 class='sub-title'>Escalations by Mode</h2>", unsafe_allow_html=True)
        mode_counts = df_filtered['Mode'].value_counts().reset_index()
        mode_counts.columns = ['Mode', 'Count']
        mode_counts['Percentage'] = (mode_counts['Count'] / mode_counts['Count'].sum()) * 100
        mode_counts['Label'] = mode_counts['Mode'] + " (" + mode_counts['Count'].astype(str) + ")"
        fig6 = px.pie(mode_counts, names='Mode', values='Count', title='Escalations by Mode')
        fig6.update_traces(textinfo='label+value', hoverinfo='label+value', textposition='inside')
        fig6.update_layout(height=400)
        st.plotly_chart(fig6, use_container_width=True, key="fig6")

    with col7:
        st.markdown("<h2 class='sub-title'>Escalations by Domain</h2>", unsafe_allow_html=True)
        domain_counts = df_filtered['Domain'].value_counts().reset_index()
        domain_counts.columns = ['Domain', 'Count']
        fig7 = px.bar(domain_counts, x='Domain', y='Count', text='Count', color='Domain')
        fig7.update_layout(height=400)
        st.plotly_chart(fig7, use_container_width=True, key="fig7")

    # Escalation Distribution by Assignees
    st.markdown("<h2 class='sub-title'>🔹 Escalation Distribution by Assignees</h2>", unsafe_allow_html=True)
    assigned_counts = df_filtered["Escalated To"].value_counts().reset_index()
    assigned_counts.columns = ["Escalated To", "Count"]
    assigned_counts["Percentage"] = (assigned_counts["Count"] / assigned_counts["Count"].sum()) * 100
    fig3 = px.pie(assigned_counts, names="Escalated To", values="Count", title="Escalation Distribution", hole=0.3)
    fig3.update_traces(textinfo="label+percent+value", hoverinfo="label+value+percent", textposition="inside")
    fig3.update_layout(height=400)
    st.plotly_chart(fig3, use_container_width=True, key="fig3")



except gspread.exceptions.SpreadsheetNotFound:
    st.error("Error: The Google Sheet was not found. Check the spreadsheet ID and permissions.")
except Exception as e:
    st.error(f"An error occurred: {e}")
import streamlit as st
import gspread
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
from io import BytesIO
from matplotlib.backends.backend_pdf import PdfPages
import plotly.express as px
from plotly.io import write_image
from PIL import Image  # This import is necessary
import numpy as np

# Function to save Plotly figures as images and add them to a PDF
def generate_pdf(figures):
    pdf_buffer = BytesIO()

    with PdfPages(pdf_buffer) as pdf:
        for fig in figures:
            # Set the figure background to white to avoid black background
            fig.update_layout(plot_bgcolor='white', paper_bgcolor='white')

            # Save the Plotly figure as a PNG image to a BytesIO buffer
            img_buf = BytesIO()
            write_image(fig, img_buf, format="png", scale=3)  # Increase scale for better resolution
            img_buf.seek(0)  # Reset buffer position to the beginning

            # Open the image using PIL (Pillow)
            img = Image.open(img_buf)
            img = img.convert("RGB")  # Convert image to RGB (to avoid transparency issues)

            # Convert image to an array that can be used by matplotlib
            img_array = np.array(img)

            # Use matplotlib to read the image and add it to the PDF
            fig_matplotlib, ax = plt.subplots()
            ax.imshow(img_array)
            ax.axis('off')  # Hide axes
            pdf.savefig(fig_matplotlib, bbox_inches='tight', dpi=300)
            plt.close(fig_matplotlib)  # Close the matplotlib figure to avoid display issues

    pdf_buffer.seek(0)  # Reset buffer position to the beginning

    # Save the PDF to a file for verification
    with open('escalations_dashboard.pdf', 'wb') as f:
        f.write(pdf_buffer.read())

    return pdf_buffer

# Collecting all the figures (from your original Streamlit app)
category_counts = df_filtered["Case Category"].value_counts().reset_index()
category_counts.columns = ["Case Category", "Count"]
fig1 = px.bar(category_counts, x="Case Category", y="Count", text="Count", color="Case Category", color_discrete_sequence=px.colors.qualitative.Plotly, title="📌 Escalations by Case Category")

time_series = df_filtered.groupby("Escalation Date").size().reset_index(name="Count")
fig2 = px.line(time_series, x="Escalation Date", y="Count", markers=True,
    color_discrete_sequence=px.colors.qualitative.Plotly, title="📈 Escalation Trend Over Time")

assigned_counts = df_filtered["Escalated To"].value_counts().reset_index()
assigned_counts.columns = ["Escalated To", "Count"]
fig3 = px.pie(assigned_counts, names="Escalated To", values="Count", color_discrete_sequence=px.colors.qualitative.Plotly, title="Escalation Distribution")

top5_categories = category_counts.nlargest(5, "Count")
fig4 = px.bar(top5_categories, x="Case Category", y="Count", text="Count", color="Case Category", color_discrete_sequence=px.colors.qualitative.Plotly, title="📌 Top 5 Most Escalated Categories")

df_filtered['Day of Week'] = df_filtered['Escalation Date'].dt.day_name()
day_counts = df_filtered['Day of Week'].value_counts().reset_index()
day_counts.columns = ['Day of Week', 'Count']
fig5 = px.line(day_counts, x='Day of Week', y='Count', markers=True, color_discrete_sequence=px.colors.qualitative.Plotly, title="Escalation Trends Across the Week")

mode_counts = df_filtered['Mode'].value_counts().reset_index()
mode_counts.columns = ['Mode', 'Count']
fig6 = px.pie(mode_counts, names='Mode', values='Count', color_discrete_sequence=px.colors.qualitative.Plotly, title='Escalations by Mode')

domain_counts = df_filtered['Domain'].value_counts().reset_index()
domain_counts.columns = ['Domain', 'Count']
fig7 = px.bar(domain_counts, x='Domain', y='Count', text='Count', color='Domain', color_discrete_sequence=px.colors.qualitative.Plotly, title="Escalations by Domain")

# Add all 7 figures to a list
figures = [fig1, fig2, fig3, fig4, fig5, fig6, fig7]

# Generate and display the PDF
pdf_file = generate_pdf(figures)

# Display a download button for the PDF
import streamlit as st
st.download_button("Download Escalations Dashboard PDF", pdf_file, file_name="Escalations_Dashboard.pdf", mime="application/pdf")

