import streamlit as st
import pandas as pd
import plotly.express as px

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
        df['hour'] = df['started_at'].dt.hour
        combined.append(df)
    return pd.concat(combined, ignore_index=True)

if uploaded_files:
    df = load_all_data(uploaded_files)

    # Sidebar filters
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
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📌 Minutes by User", 
        "👤 User List", 
        "📊 Dashboard", 
        "📈 Task Type Breakdown",
        "🧑‍💻 User Drilldown",
        "⏰ Hourly Analysis"
    ])

    with tab1:
        st.subheader("Minutes Uploaded by Each User")
        minute_table = filtered_df.groupby(['user_first_name'])['minutes'].sum().reset_index()
        st.dataframe(minute_table, use_container_width=True)

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
        st.download_button("📥 Download Filtered Data", data=filtered_df.to_csv(index=False), file_name="filtered_data.csv")

    with tab4:
        st.subheader("📊 Task Type Breakdown (Minutes Spent per Task)")

        # Task summary with sorting by total minutes spent
        task_summary = filtered_df.groupby('task')['minutes'].sum().reset_index().sort_values(by='minutes', ascending=False)
        
        if not task_summary.empty:
            # Bar chart with sorted tasks and intuitive colors
            col1, col2 = st.columns(2)
            with col1:
                # Pie chart
                fig_pie = px.pie(task_summary, 
                                 names='task', 
                                 values='minutes', 
                                 title="Total Minutes Spent per Task",
                                 color='minutes',  # color by minutes spent to make it more intuitive
                                 color_continuous_scale='Viridis')  # using a perceptual color scale
                st.plotly_chart(fig_pie, use_container_width=True)

            with col2:
                # Bar chart
                fig_bar = px.bar(task_summary, 
                                 x='task', 
                                 y='minutes', 
                                 title="Minutes Spent per Task Type", 
                                 text_auto=True,
                                 color='minutes',  # color by minutes spent
                                 color_continuous_scale='Viridis')  # using the same color scale for consistency
                fig_bar.update_layout(xaxis_title="Task Type", yaxis_title="Minutes", xaxis_tickangle=-45)
                st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.warning("No tasks available for the selected filters.")

    with tab5:
        st.subheader("User Drilldown")
        selected_user = st.selectbox("Select User", options=filtered_df['user_first_name'].unique())
        user_df = filtered_df[filtered_df['user_first_name'] == selected_user]

        col1, col2 = st.columns(2)
        col1.metric("Total Minutes", user_df['minutes'].sum())
        col2.metric("Average Task Time", round(user_df['minutes'].mean(), 2))

        user_chart = user_df.groupby('task')['minutes'].sum().reset_index()
        fig_user = px.bar(user_chart, x='task', y='minutes', title=f"Task Breakdown for {selected_user}")
        st.plotly_chart(fig_user, use_container_width=True)

        st.markdown("### Task History")
        st.dataframe(user_df[['date', 'task', 'minutes']], use_container_width=True)

    with tab6:
        st.subheader("Hourly Time-of-Day Analysis")
        hourly_summary = filtered_df.groupby('hour')['minutes'].sum().reset_index()
        fig_hour = px.bar(hourly_summary, x='hour', y='minutes', title="Minutes Logged by Hour of Day")
        st.plotly_chart(fig_hour, use_container_width=True)

else:
    st.info("Upload one or more CSV files to begin.")
