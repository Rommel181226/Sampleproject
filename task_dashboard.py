import streamlit as st
import pandas as pd
import plotly.express as px
import calplot
import matplotlib.pyplot as plt
from io import BytesIO

st.set_page_config(page_title="Task Dashboard", layout="wide")
st.title("🗂️ Task Time Analysis Dashboard")

# Sidebar - Upload multiple CSV files
uploaded_files = st.sidebar.file_uploader("Upload CSV files", type=["csv"], accept_multiple_files=True)

@st.cache_data

def load_all_data(files):
    combined = []
    for file in files:
        df = pd.read_csv(file)
        df['started_at'] = pd.to_datetime(df['started_at'], errors='coerce')
        df['date'] = df['started_at'].dt.date
        combined.append(df)
    return pd.concat(combined, ignore_index=True)

if uploaded_files:
    df = load_all_data(uploaded_files)

    # Sidebar - Project ID Filter
    if 'project_id' in df.columns:
        selected_project = st.sidebar.selectbox("Select Project ID", df['project_id'].dropna().unique())
        df = df[df['project_id'] == selected_project]

    # Sidebar Filters
    users = df['user_first_name'].unique()
    locales = df['user_locale'].unique()
    min_date, max_date = df['date'].min(), df['date'].max()

    st.sidebar.subheader("Filter Data")
    selected_users = st.sidebar.multiselect("User", options=users, default=users)
    selected_locales = st.sidebar.multiselect("Locale", options=locales, default=locales)
    selected_dates = st.sidebar.date_input("Date Range", [min_date, max_date])

    # Apply filters
    mask = (
        df['user_first_name'].isin(selected_users) &
        df['user_locale'].isin(selected_locales) &
        (df['date'] >= selected_dates[0]) & (df['date'] <= selected_dates[1])
    )
    filtered_df = df[mask]

    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📌 Minutes by User", "👤 User List", "📊 Dashboard", "📅 Calendar Heatmap"])

    with tab1:
        st.subheader("Minutes Uploaded by Each User")
        minute_table = filtered_df.groupby('user_first_name')['minutes'].sum().reset_index()
        st.dataframe(minute_table, use_container_width=True)

        # Download Button for Summary
        csv = minute_table.to_csv(index=False).encode('utf-8')
        st.download_button("Download Per-User Summary", csv, "user_summary.csv", "text/csv")

    with tab2:
        st.subheader("User List")
        user_table = df[['user_first_name', 'user_last_name', 'user_locale']].drop_duplicates().sort_values(by='user_first_name')
        st.dataframe(user_table, use_container_width=True)

    with tab3:
        total_minutes = filtered_df['minutes'].sum()
        avg_minutes = filtered_df['minutes'].mean()
        total_tasks = filtered_df.shape[0]

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Time Spent (min)", total_minutes)
        col2.metric("Average Time per Task (min)", round(avg_minutes, 2))
        col3.metric("Total Tasks", total_tasks)

        st.markdown("### 📊 Time Spent per User")
        time_chart = filtered_df.groupby('user_first_name')['minutes'].sum().reset_index()
        fig_time = px.bar(time_chart, x='user_first_name', y='minutes', title='Total Minutes per User')
        st.plotly_chart(fig_time, use_container_width=True)

        st.markdown("### 🗓️ Time Distribution by Date")
        date_chart = filtered_df.groupby('date')['minutes'].sum().reset_index()
        fig_date = px.line(date_chart, x='date', y='minutes', markers=True, title='Minutes Logged Over Time')
        st.plotly_chart(fig_date, use_container_width=True)

        st.markdown("### 📋 Task Records")
        st.dataframe(filtered_df[['date', 'user_first_name', 'user_last_name', 'task', 'minutes']], use_container_width=True)

    with tab4:
        st.subheader("Calendar Heatmap of Time Spent")
        cal_df = filtered_df.groupby('date')['minutes'].sum()
        fig, ax = calplot.calplot(cal_df, cmap='YlGn', fillcolor='lightgray', colorbar=True)
        buf = BytesIO()
        plt.savefig(buf, format="png")
        st.image(buf)

else:
    st.info("Upload one or more CSV files to begin.")
