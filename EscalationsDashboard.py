import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
from io import BytesIO
from matplotlib.backends.backend_pdf import PdfPages
import datetime
from google.oauth2.service_account import Credentials
import gspread
from PIL import Image
import numpy as np
from plotly.io import write_image

# Configure page layout
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

# Google Sheets API setup
json_key_file = "creds.json"
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_file(json_key_file, scopes=scope)
client = gspread.authorize(creds)

# Google Sheet details
spreadsheet_id = "11FoqJicHt3BGpzAmBnLi1FQFN-oeTxR_WGKszARDcR4"  # Replace with your actual ID
worksheet_name = "Sheet1"  # Update if different

try:
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

    # Fetch data from Google Sheets
    sheet = client.open_by_key(spreadsheet_id).worksheet(worksheet_name)

    # Get all the values as a list of lists
    all_values = sheet.get_all_values()

    # Define your expected headers (use the exact order and names from your sheet)
    expected_headers = [
        "Mode",
        "Type",
        "Escalation Date",  # This is the one in column C that you want to keep
        "Domain",
        "BID",
        "Account name",
        "Subject line (Manual TA Escalation)",
        "Parent Category",
        "Case Category",
        "Escalated To"
    ]

    # The first row contains the actual headers in the sheet
    actual_headers = all_values[0]

    # Create a mapping of indices to get data from the right columns
    header_indices = []
    for header in expected_headers:
        try:
            # For "Escalation Date", specifically use the first occurrence (column C)
            if header == "Escalation Date":
                index = actual_headers.index(header)
            else:
                index = actual_headers.index(header)
            header_indices.append(index)
        except ValueError:
            # If header not found, append None
            header_indices.append(None)

    # Create a list of dictionaries with only the columns we want
    data = []
    for row in all_values[1:]:  # Skip the header row
        row_dict = {}
        for i, header in enumerate(expected_headers):
            if header_indices[i] is not None and header_indices[i] < len(row):
                row_dict[header] = row[header_indices[i]]
            else:
                row_dict[header] = ""  # Default value for missing columns
        data.append(row_dict)

    # Convert to DataFrame
    df = pd.DataFrame(data)

    # Print normalized column names (for debugging)
    print("Selected column names:", df.columns.tolist())

    # Check for and remove duplicate columns by renaming them
    # This fixes the "Duplicate column names found" error
    if len(df.columns) != len(set(df.columns)):
        # Get duplicated column names
        duplicates = set([col for col in df.columns if list(df.columns).count(col) > 1])
        for dup in duplicates:
            # Find all occurrences of the duplicate column
            dup_indices = [i for i, col in enumerate(df.columns) if col == dup]
            # Rename all but the first occurrence
            for i, idx in enumerate(dup_indices[1:], 1):
                # Create new column name
                new_col_name = f"{dup}_{i}"
                # Create a list from df.columns
                cols = df.columns.tolist()
                # Replace the duplicate column name
                cols[idx] = new_col_name
                # Assign new column names to df
                df.columns = cols

    # Define date_col for compatibility with the rest of your code
    date_col = "Escalation Date"

    # Convert the escalation date column to datetime
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")

    # Convert the escalation date column to datetime
    df["Escalation Date"] = pd.to_datetime(df["Escalation Date"], errors="coerce")

    # Map common expected column names to what's in the dataframe
    column_mapping = {
        "mode": next((col for col in df.columns if "mode" in col.lower()), None),
        "type": next((col for col in df.columns if "type" in col.lower()), None),
        "escalation date": date_col,
        "domain": next((col for col in df.columns if "domain" in col.lower()), None),
        "account name": next((col for col in df.columns if "account" in col.lower()), None),
        "case category": next((col for col in df.columns if "category" in col.lower() and "parent" not in col.lower()), None),
        "escalated to": next((col for col in df.columns if "escalated" in col.lower() or "assignee" in col.lower()),
                             None)
    }

    # Filter out columns that weren't found (None values)
    column_mapping = {k: v for k, v in column_mapping.items() if v is not None}

    # Print the mapping (for debugging)
    print("Column mapping:", column_mapping)

    # Rename columns according to the mapping
    df = df.rename(columns={v: k for k, v in column_mapping.items()})

    # Make sure all required columns exist
    required_columns = ["mode", "type", "escalation date", "domain", "account name", "case category", "escalated to"]
    for col in required_columns:
        if col not in df.columns:
            # If column doesn't exist, create it with placeholder values
            df[col] = "Unknown"

    # Standardize column names for consistency in the rest of the code
    df = df.rename(columns={
        "mode": "Mode",
        "type": "Type",
        "escalation date": "Escalation Date",
        "domain": "Domain",
        "account name": "Account name",
        "case category": "Case Category",
        "escalated to": "Escalated To"
    })

    # Convert Domain and other columns to string type to avoid any Series issues
    string_columns = ["Domain", "Mode", "Type", "Account name", "Case Category", "Escalated To"]
    for col in string_columns:
        if col in df.columns:
            df[col] = df[col].astype(str)

    # Sidebar Filters
    st.sidebar.header("Filters")

    # Debug print to see DataFrame structure
    print("DataFrame info:")
    print(f"Shape: {df.shape}")
    print(f"Columns: {df.columns.tolist()}")
    print(f"Data types: {df.dtypes}")

    # Case Category Dropdown
    try:
        # Check if the column exists
        if "Case Category" in df.columns:
            case_categories = df["Case Category"].unique().tolist()
        else:
            print("Available columns:", df.columns.tolist())
            case_categories = []  # Default to empty list if column not found
    except Exception as e:
        print(f"Error getting Case Category unique values: {e}")
        case_categories = []

    selected_category = st.sidebar.selectbox("Search Case Category", ["All"] + case_categories)

    # Account Name Dropdown
    try:
        # Check if the column exists
        if "Account name" in df.columns:
            account_names = df["Account name"].unique().tolist()
        else:
            print("Available columns:", df.columns.tolist())
            account_names = []  # Default to empty list if column not found
    except Exception as e:
        print(f"Error getting Account name unique values: {e}")
        account_names = []

    selected_account = st.sidebar.selectbox("Search Account Name", ["All"] + account_names)

    # Date Range Filter
    start_date = st.sidebar.date_input("Start Date", df["Escalation Date"].min().date() if not pd.isna(
        df["Escalation Date"].min()) else datetime.date.today())
    end_date = st.sidebar.date_input("End Date", df["Escalation Date"].max().date() if not pd.isna(
        df["Escalation Date"].max()) else datetime.date.today())

    # Apply Filters
    df_filtered = df[(df["Escalation Date"] >= pd.to_datetime(start_date)) &
                     (df["Escalation Date"] <= pd.to_datetime(end_date))]

    if selected_category != "All":
        df_filtered = df_filtered[df_filtered["Case Category"] == selected_category]

    if selected_account != "All":
        df_filtered = df_filtered[df_filtered["Account name"] == selected_account]

    # Streamlit Dashboard
    st.markdown("<h1 class='main-title'>📊 DMAT - TA Escalations Dashboard</h1>", unsafe_allow_html=True)

    # Make sure df_filtered contains data
    if df_filtered.empty:
        st.warning("No data matches the selected filters. Please adjust your filter criteria.")

    # KPIs with proper error handling - FIX FOR INTEGER CONVERSION ERROR
    try:
        col1, col2, col3 = st.columns(3)
        with col1:
            # Use len() which returns an int directly
            total_escalations = len(df_filtered)
            st.metric(label="📌 Total Escalations", value=total_escalations)
        with col2:
            # Count unique values directly instead of using nunique()
            total_domains = len(df_filtered["Domain"].unique())
            st.metric(label="🌐 Total Domains", value=total_domains)
        with col3:
            # Count unique values directly
            total_categories = len(df_filtered["Case Category"].unique())
            st.metric(label="📑 Total Escalation Categories", value=total_categories)
    except Exception as e:
        st.error(f"Error displaying metrics: {e}")
        import traceback
        traceback.print_exc()

    # Display Table on Top
    st.markdown("<h2 class='sub-title'>Escalation Data</h2>", unsafe_allow_html=True)
    st.dataframe(df_filtered)


    # Function to safely create and display charts
    def safe_create_chart(chart_function, error_message="Error creating chart"):
        try:
            return chart_function()
        except Exception as e:
            st.error(f"{error_message}: {e}")
            import traceback
            traceback.print_exc()
            return None


    # Graphs in Horizontal Layout
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("<h2 class='sub-title' style='white-space: nowrap;'>📌 Escalations by Case Category</h2>",
                    unsafe_allow_html=True)


        def create_category_chart():
            category_counts = df_filtered["Case Category"].value_counts().reset_index()
            category_counts.columns = ["Case Category", "Count"]
            fig1 = px.bar(category_counts, x="Case Category", y="Count", text="Count", color="Case Category")
            fig1.update_layout(
                autosize=True,
                margin=dict(t=20, b=20, l=20, r=20),
                height=450
            )
            return fig1, category_counts


        result = safe_create_chart(create_category_chart, "Error creating Case Category chart")
        if result:
            fig1, category_counts = result
            st.plotly_chart(fig1, use_container_width=True)

    with col2:
        st.markdown("<h2 class='sub-title'>📈 Escalation Trend Over Time</h2>", unsafe_allow_html=True)


        def create_time_series_chart():
            time_series = df_filtered.groupby("Escalation Date").size().reset_index(name="Count")
            fig2 = px.line(time_series, x="Escalation Date", y="Count", markers=True)
            fig2.update_layout(height=450, margin=dict(t=0, b=0, l=0, r=0))
            return fig2, time_series


        result = safe_create_chart(create_time_series_chart, "Error creating Time Series chart")
        if result:
            fig2, time_series = result
            st.plotly_chart(fig2, use_container_width=True, key="fig2")

    if 'category_counts' in locals():
        col4, col5 = st.columns(2)
        with col4:
            st.markdown("<h2 class='sub-title'>📌 Top 5 Most Escalated Categories</h2>", unsafe_allow_html=True)


            def create_top5_chart():
                top5_categories = category_counts.nlargest(5, "Count")
                fig4 = px.bar(top5_categories, x="Case Category", y="Count", text="Count", color="Case Category")
                fig4.update_layout(height=400, margin=dict(t=0, b=0, l=0, r=0))
                return fig4


            fig4 = safe_create_chart(create_top5_chart, "Error creating Top 5 Categories chart")
            if fig4:
                st.plotly_chart(fig4, use_container_width=True, key="fig4")

        with col5:
            st.markdown("<h2 class='sub-title'>Escalation Trends Across the Week</h2>", unsafe_allow_html=True)


            def create_day_trend_chart():
                df_filtered['Day of Week'] = df_filtered['Escalation Date'].dt.day_name()
                day_counts = df_filtered['Day of Week'].value_counts().reset_index()
                day_counts.columns = ['Day of Week', 'Count']
                # Sort the days in correct order
                days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                day_counts['Day of Week'] = pd.Categorical(day_counts['Day of Week'], categories=days_order, ordered=True)
                day_counts = day_counts.sort_values('Day of Week')
                fig5 = px.line(day_counts, x='Day of Week', y='Count', markers=True)
                fig5.update_layout(height=400, margin=dict(t=0, b=0, l=0, r=0))
                return fig5, day_counts


            result = safe_create_chart(create_day_trend_chart, "Error creating Day Trend chart")
            if result:
                fig5, day_counts = result
                st.plotly_chart(fig5, use_container_width=True, key="fig5")

    col6, col7 = st.columns(2)
    with col6:
        st.markdown("<h2 class='sub-title'>Escalations by Mode</h2>", unsafe_allow_html=True)


        def create_mode_chart():
            mode_counts = df_filtered['Mode'].value_counts().reset_index()
            mode_counts.columns = ['Mode', 'Count']
            mode_counts['Percentage'] = (mode_counts['Count'] / mode_counts['Count'].sum()) * 100
            mode_counts['Label'] = mode_counts['Mode'] + " (" + mode_counts['Count'].astype(str) + ")"
            fig6 = px.pie(mode_counts, names='Mode', values='Count', title='Escalations by Mode')
            fig6.update_traces(textinfo='label+value', hoverinfo='label+value', textposition='inside')
            fig6.update_layout(height=400)
            return fig6, mode_counts


        result = safe_create_chart(create_mode_chart, "Error creating Mode chart")
        if result:
            fig6, mode_counts = result
            st.plotly_chart(fig6, use_container_width=True, key="fig6")

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

    # Escalation Distribution by Assignees
    st.markdown("<h2 class='sub-title'>🔹 Escalation Distribution by Assignees</h2>", unsafe_allow_html=True)


    def create_assignee_chart():
        assigned_counts = df_filtered["Escalated To"].value_counts().reset_index()
        assigned_counts.columns = ["Escalated To", "Count"]
        assigned_counts["Percentage"] = (assigned_counts["Count"] / assigned_counts["Count"].sum()) * 100
        fig3 = px.pie(assigned_counts, names="Escalated To", values="Count", title="Escalation Distribution", hole=0.3)
        fig3.update_traces(textinfo="label+percent+value", hoverinfo="label+value+percent", textposition="inside")
        fig3.update_layout(height=400)
        return fig3, assigned_counts


    result = safe_create_chart(create_assignee_chart, "Error creating Assignee chart")
    if result:
        fig3, assigned_counts = result
        st.plotly_chart(fig3, use_container_width=True, key="fig3")


    # Function to save Plotly figures as images and add them to a PDF
    def generate_pdf(figures):
        try:
            pdf_buffer = BytesIO()

            with PdfPages(pdf_buffer) as pdf:
                for fig in figures:
                    if fig is None:
                        continue

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

            pdf_buffer.seek(0)  # Reset buffer position again for the download button
            return pdf_buffer

        except Exception as e:
            st.error(f"Error generating PDF: {e}")
            import traceback
            traceback.print_exc()
            return None


    # Only create PDF if we have generated all the charts
    if all(var in locals() for var in ['fig1', 'fig2', 'fig3', 'fig5', 'fig6', 'fig7', 'top5_categories']):
        try:
            # Update all figures with proper colors for PDF export
            fig1 = px.bar(category_counts, x="Case Category", y="Count", text="Count", color="Case Category",
                          color_discrete_sequence=px.colors.qualitative.Plotly, title="📌 Escalations by Case Category")

            fig2 = px.line(time_series, x="Escalation Date", y="Count", markers=True,
                           color_discrete_sequence=px.colors.qualitative.Plotly, title="📈 Escalation Trend Over Time")

            fig3 = px.pie(assigned_counts, names="Escalated To", values="Count",
                          color_discrete_sequence=px.colors.qualitative.Plotly, title="Escalation Distribution")

            top5_categories = category_counts.nlargest(5, 'Count')
            fig4 = px.bar(top5_categories, x="Case Category", y="Count", text="Count", color="Case Category",
                          color_discrete_sequence=px.colors.qualitative.Plotly,
                          title="📌 Top 5 Most Escalated Categories")

            fig5 = px.line(day_counts, x='Day of Week', y='Count', markers=True,
                           color_discrete_sequence=px.colors.qualitative.Plotly,
                           title="Escalation Trends Across the Week")

            fig6 = px.pie(mode_counts, names='Mode', values='Count',
                          color_discrete_sequence=px.colors.qualitative.Plotly, title='Escalations by Mode')

            fig7 = px.bar(domain_counts, x='Domain', y='Count', text='Count', color='Domain',
                          color_discrete_sequence=px.colors.qualitative.Plotly, title="Escalations by Domain")

            # Add all 7 figures to a list
            figures = [fig1, fig2, fig3, fig4, fig5, fig6, fig7]

            # Generate and display the PDF
            pdf_file = generate_pdf(figures)

            if pdf_file:
                # Display a download button for the PDF
                st.download_button("Download Escalations Dashboard PDF", pdf_file,
                                   file_name="Escalations_Dashboard.pdf",
                                   mime="application/pdf")
        except Exception as e:
            st.error(f"Error preparing PDF: {e}")
            import traceback

            traceback.print_exc()

except gspread.exceptions.SpreadsheetNotFound:
    st.error("Error: The Google Sheet was not found. Check the spreadsheet ID and permissions.")
except Exception as e:
    st.error(f"An error occurred: {e}")
    # Print the full error traceback for debugging
    import traceback

    traceback.print_exc()

