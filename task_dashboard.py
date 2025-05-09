
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Task Dashboard", layout="wide")

st.title("🗂️ Task Time Analysis Dashboard")

# File uploader
uploaded_file = st.sidebar.file_uploader("Upload your CSV file", type=["csv"])

@st.cache_data
def load_data(file):
    df = pd.read_csv(file)
    df['started_at'] = pd.to_datetime(df['started_at'], errors='coerce')
    df['date'] = df['started_at'].dt.date
    return df

if uploaded_file:
    df = load_data(uploaded_file)

    # Sidebar filters
    users = df['user_first_name'].unique()
    locales = df['user_locale'].unique()
    min_date, max_date = df['date'].min(), df['date'].max()

    st.sidebar.subheader("Filter Data")
    selected_users = st.sidebar.multiselect("User", options=users, default=users)
    selected_locales = st.sidebar.multiselect("Locale", options=locales, default=locales)
    selected_dates = st.sidebar.date_input("Date Range", [min_date, max_date])

    # Filter dataset
    mask = (
        df['user_first_name'].isin(selected_users) &
        df['user_locale'].isin(selected_locales) &
        (df['date'] >= selected_dates[0]) & (df['date'] <= selected_dates[1])
    )
    filtered_df = df[mask]

    # Metrics
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
else:
    st.info("Upload a CSV file to begin.")
