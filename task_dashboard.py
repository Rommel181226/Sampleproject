import streamlit as st
import pandas as pd
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt

# Function to load CSV data
@st.cache
def load_all_data(uploaded_files):
    df_list = []
    for file in uploaded_files:
        df = pd.read_csv(file)
        df_list.append(df)
    return pd.concat(df_list, ignore_index=True)

# Main logic
if uploaded_files:
    df = load_all_data(uploaded_files)

    # Sidebar filters
    users = df['user_first_name'].dropna().unique()
    locales = df['user_locale'].dropna().unique()
    projects = df['project_id'].dropna().unique()
    min_date, max_date = df['date'].min(), df['date'].max()

    st.sidebar.subheader("Filter Data")
    selected_users = st.sidebar.multiselect("User", options=users, default=list(users))
    selected_locales = st.sidebar.multiselect("Locale", options=locales, default=list(locales))
    selected_projects = st.sidebar.multiselect("Project", options=projects, default=list(projects))
    selected_dates = st.sidebar.date_input("Date Range", [min_date, max_date])

    # Apply filters
    mask = (
        df['user_first_name'].isin(selected_users) &
        df['user_locale'].isin(selected_locales) &
        df['project_id'].isin(selected_projects) &
        (df['date'] >= selected_dates[0]) & (df['date'] <= selected_dates[1])
    )
    filtered_df = df[mask]

    # Tabs for different views
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10, tab11, tab12, tab13 = st.tabs([
        "📊 Summary", "📈 Visualizations", "📋 Task Records",
        "👤 User Drilldown", "⏰ Hourly Analysis", "📅 Calendar Heatmap",
        "📈 Productivity Trends", "📊 Top Tasks", "📊 User Efficiency",
        "⏳ Idle Time Gaps", "📂 Project Comparison", "📅 Weekday/Hour Heatmap",
        "⏳ Task Completion Distribution"
    ])

    with tab1:
        # Existing Summary code here
        st.subheader("Summary of Filtered Data")
        st.write(filtered_df.describe())

    with tab2:
        # Existing Visualizations code here
        st.subheader("Visualizations")
        fig = px.scatter(filtered_df, x='started_at', y='minutes', color='user_first_name', title="Time vs User")
        st.plotly_chart(fig)

    with tab3:
        # Existing Task Records code here
        st.subheader("Task Records")
        st.dataframe(filtered_df)

    with tab4:
        # Existing User Drilldown code here
        st.subheader("User Drilldown")
        selected_user = st.selectbox("Select User", options=selected_users)
        user_data = filtered_df[filtered_df['user_first_name'] == selected_user]
        st.write(f"Data for {selected_user}")
        st.dataframe(user_data)

    with tab5:
        # Existing Hourly Analysis code here
        st.subheader("Hourly Analysis")
        hourly_data = filtered_df.groupby(filtered_df['started_at'].dt.hour)['minutes'].sum().reset_index()
        fig_hourly = px.bar(hourly_data, x='started_at', y='minutes', title="Total Time Spent by Hour")
        st.plotly_chart(fig_hourly)

    with tab6:
        # Existing Calendar Heatmap code here
        st.subheader("Calendar Heatmap")
        df['day'] = df['started_at'].dt.date
        daily_data = df.groupby('day')['minutes'].sum().reset_index()
        fig_calendar = px.density_heatmap(daily_data, x='day', y='minutes', title="Daily Time Heatmap")
        st.plotly_chart(fig_calendar)

    with tab7:
        # 📈 Productivity Trends
        st.subheader("Productivity Trends Over Time")
        df['week'] = df['started_at'].dt.to_period('W').astype(str)
        weekly_trend = df.groupby('week')['minutes'].sum().reset_index()
        fig_weekly = px.line(weekly_trend, x='week', y='minutes', markers=True, title="Weekly Productivity Trend")
        st.plotly_chart(fig_weekly, use_container_width=True)

    with tab8:
        # 📊 Top Tasks
        st.subheader("Top Tasks by Duration & Frequency")
        
        # Top tasks by total time spent
        top_by_time = df.groupby('task')['minutes'].sum().sort_values(ascending=False).head(5)
        st.write("Top 5 Tasks by Total Time Spent")
        st.bar_chart(top_by_time)
        
        # Top tasks by frequency
        top_by_count = df['task'].value_counts().head(5)
        st.write("Top 5 Most Frequent Tasks")
        st.bar_chart(top_by_count)

    with tab9:
        # 📊 User Efficiency Score
        st.subheader("User Efficiency Scores")
        efficiency = df.groupby('user_first_name').agg({'minutes': 'sum', 'task': 'count'})
        efficiency['efficiency_score'] = efficiency['minutes'] / efficiency['task']
        efficiency = efficiency.sort_values(by='efficiency_score', ascending=False)
        st.write("User Efficiency Scores (Minutes per Task)")
        st.bar_chart(efficiency['efficiency_score'])

    with tab10:
        # ⏳ Idle Time Gaps
        st.subheader("Idle Time / Gap Detection")
        df_sorted = df.sort_values(by=['user_first_name', 'started_at'])
        df_sorted['time_diff'] = df_sorted.groupby('user_first_name')['started_at'].diff()
        st.write("Time Gaps Between Tasks (Minutes)")
        st.dataframe(df_sorted[['user_first_name', 'task', 'time_diff']])

    with tab11:
        # 📂 Project Comparison
        st.subheader("Project Comparison (Time Spent)")
        project_summary = df.groupby('project_id')['minutes'].sum().reset_index()
        fig_project = px.bar(project_summary, x='project_id', y='minutes', title="Total Time Spent per Project")
        st.plotly_chart(fig_project, use_container_width=True)

    with tab12:
        # 📅 Weekday/Hour Heatmap
        st.subheader("Heatmap by Weekday and Hour")
        df['weekday'] = df['started_at'].dt.day_name()
        heat_data = df.groupby(['weekday', 'hour'])['minutes'].sum().unstack().fillna(0)
        st.write("Weekday vs Hour Heatmap")
        st.dataframe(heat_data)

    with tab13:
        # ⏳ Task Completion Distribution
        st.subheader("Task Completion Distribution (Time Per Task)")
        sns.histplot(df['minutes'], bins=20)
        st.pyplot()

else:
    st.info("Upload one or more CSV files to begin.")
