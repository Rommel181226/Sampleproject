import os
import openai
from dotenv import load_dotenv
import streamlit as st
import pandas as pd
import plotly.express as px

# Load environment variables from .env file
load_dotenv()

# Set up OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")
if openai.api_key is None:
    st.error("Error: OPENAI_API_KEY not found in .env file.")

# Page config
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

def generate_summary(filtered_data):
    try:
        # Generate a summary for the filtered data
        summary_prompt = f"Generate a summary for the following user data:\n\n{filtered_data.head(10)}"
        
        # OpenAI Completion API Call
        response = openai.Completion.create(
            model="text-davinci-003",
            prompt=summary_prompt,
            max_tokens=200
        )
        
        # Return the generated summary text
        return response.choices[0].text.strip()
    except Exception as e:
        st.error(f"Error generating summary: {str(e)}")
        return None

if uploaded_files:
    df = load_all_data(uploaded_files)

    # Sidebar filters
    users = df['user_first_name'].unique()
    locales = df['user_locale'].unique()
    projects = df['project_id'].unique()
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
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📊 Summary", "📈 Visualizations", "📋 Task Records",
        "👤 User Drilldown", "⏰ Hourly Analysis", "📅 Calendar Heatmap", "💬 Summary Comment"
    ])

    # Summary Tab
    with tab1:
        st.subheader("Minutes Uploaded by Each User")
        minute_table = filtered_df.groupby(['user_first_name'])['minutes'].sum().reset_index()
        st.dataframe(minute_table, use_container_width=True)

        total_minutes = filtered_df['minutes'].sum()
        avg_minutes = filtered_df['minutes'].mean()
        total_tasks = filtered_df.shape[0]

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Time Spent (min)", total_minutes)
        col2.metric("Average Time per Task (min)", round(avg_minutes, 2))
        col3.metric("Total Tasks", total_tasks)

    # Visualizations Tab
    with tab2:
        st.markdown("### Time Spent per User")
        time_chart = filtered_df.groupby('user_first_name')['minutes'].sum().reset_index()
        fig_time = px.bar(time_chart, x='user_first_name', y='minutes', title='Total Minutes per User')
        st.plotly_chart(fig_time, use_container_width=True)

    # Task Records Tab
    with tab3:
        st.markdown("### Task Records")
        st.dataframe(filtered_df[['date', 'user_first_name', 'user_last_name', 'task', 'minutes']], use_container_width=True)

    # User Drilldown Tab
    with tab4:
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

    # Hourly Analysis Tab
    with tab5:
        st.subheader("Hourly Time-of-Day Analysis")
        hourly_summary = filtered_df.groupby('hour')['minutes'].sum().reset_index()
        fig_hour = px.bar(hourly_summary, x='hour', y='minutes', title="Minutes Logged by Hour of Day")
        st.plotly_chart(fig_hour, use_container_width=True)

    # Calendar Heatmap Tab
    with tab6:
        st.subheader("Calendar Heatmap")
        heatmap_data = filtered_df.groupby('date')['minutes'].sum().reset_index()
        heatmap_data['date'] = pd.to_datetime(heatmap_data['date'])
        st.write(heatmap_data)

    # Summary Comment Tab
    with tab7:
        st.subheader("Summary Comment Based on User Data")
        
        # Generate summary for selected user
        summary = generate_summary(filtered_df)
        
        if summary:
            st.write("Generated Summary:")
            st.write(summary)
        else:
            st.write("No summary available.")

else:
    st.info("Upload one or more CSV files to begin.")
