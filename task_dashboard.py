import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import matplotlib.pyplot as plt

st.set_page_config(page_title="Task Time Dashboard", layout="wide")
st.title("⏱️ Task Time Dashboard")

uploaded_files = st.sidebar.file_uploader("Upload CSV", type="csv", accept_multiple_files=True)

if uploaded_files:
    df_list = [pd.read_csv(file) for file in uploaded_files]
    df = pd.concat(df_list, ignore_index=True)

    # Convert 'started_at' to datetime
    df['started_at'] = pd.to_datetime(df['started_at'])

    # Extract date/time components
    df['hour'] = df['started_at'].dt.hour
    df['day'] = df['started_at'].dt.day_name()
    df['month'] = df['started_at'].dt.month_name()
    df['day_num'] = df['started_at'].dt.day

    # Sidebar filters
    users = st.sidebar.multiselect("Filter by user", options=df['user_first_name'].unique(), default=df['user_first_name'].unique())
    locales = st.sidebar.multiselect("Filter by locale", options=df['user_locale'].unique(), default=df['user_locale'].unique())

    # Date inputs with correct range handling
    start_date = pd.Timestamp(st.sidebar.date_input("Start date", df['started_at'].min().date()))
    end_date = pd.Timestamp(st.sidebar.date_input("End date", df['started_at'].max().date())) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)

    # Filter dataframe
    filtered_df = df[
        (df['user_first_name'].isin(users)) &
        (df['user_locale'].isin(locales)) &
        (df['started_at'] >= start_date) &
        (df['started_at'] <= end_date)
    ]

    tabs = ["Summary", "Dashboard", "Task Types", "User View", "Hourly Analysis", "Calendar View", "Raw Data"]
    selected_tab = st.sidebar.radio("Select Tab", tabs)

    if selected_tab == "Summary":
        st.subheader("📊 Summary Metrics")
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Tasks", len(filtered_df))
        col2.metric("Total Minutes", filtered_df['minutes'].sum())
        col3.metric("Avg. Minutes/Task", round(filtered_df['minutes'].mean(), 2))

    elif selected_tab == "Dashboard":
        st.subheader("📈 Time Spent by Task")
        task_sum = filtered_df.groupby('task')['minutes'].sum().reset_index().sort_values(by='minutes', ascending=False)
        fig = px.bar(task_sum, x='task', y='minutes', title='Minutes by Task')
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("📍 Time by Locale")
        fig2 = px.pie(filtered_df, names='user_locale', values='minutes', title='Time Distribution by Locale')
        st.plotly_chart(fig2, use_container_width=True)

    elif selected_tab == "Task Types":
        st.subheader("🗂️ Task Type Breakdown")
        task_user_df = filtered_df.groupby(['task', 'user_first_name'])['minutes'].sum().reset_index()
        fig = px.bar(task_user_df, x='task', y='minutes', color='user_first_name', barmode='group', title='Task Types by User')
        st.plotly_chart(fig, use_container_width=True)

    elif selected_tab == "User View":
        st.subheader("👤 User Drilldown")
        user_task_df = filtered_df.groupby(['user_first_name', 'task'])['minutes'].sum().reset_index()
        fig = px.sunburst(user_task_df, path=['user_first_name', 'task'], values='minutes', title='User > Task Drilldown')
        st.plotly_chart(fig, use_container_width=True)

    elif selected_tab == "Hourly Analysis":
        st.subheader("🕒 Time of Day Analysis")
        fig = px.histogram(filtered_df, x='hour', y='minutes', histfunc='sum', nbins=24, title='Time Spent by Hour')
        st.plotly_chart(fig, use_container_width=True)

    elif selected_tab == "Calendar View":
        st.subheader("📅 Calendar Heatmap")
        calendar_df = filtered_df.groupby(['day_num', 'day'])['minutes'].sum().reset_index()
        fig = px.density_heatmap(calendar_df, x='day', y='day_num', z='minutes', title='Heatmap of Time Spent per Day')
        st.plotly_chart(fig, use_container_width=True)

    elif selected_tab == "Raw Data":
        st.subheader("🧾 Raw Data")
        st.dataframe(filtered_df)

else:
    st.info("👈 Upload one or more CSV files to begin.")
