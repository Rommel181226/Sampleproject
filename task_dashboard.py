import streamlit as st
import pandas as pd
import plotly.express as px
import calplot
import os
import openai
from fpdf import FPDF
import tempfile
import base64
from datetime import datetime

# Streamlit Page Config
st.set_page_config(page_title="Task Dashboard", layout="wide")
st.title("🗂️ Task Time Analysis Dashboard")

# Sidebar - Logo and Title
logo_path = os.path.join("images", "logo.png")
if os.path.exists(logo_path):
    st.sidebar.image(logo_path, width=150)
st.sidebar.markdown("## 📁 Task Dashboard Sidebar")

# Sidebar - Upload CSV files
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

# --- AI Summary Function ---
def generate_summary(filtered_data):
    sample = filtered_data[['user_first_name', 'task', 'minutes', 'date']].head(20).to_csv(index=False)
    prompt = (
        f"Provide a brief, professional summary for task time analytics based on this data:\n\n"
        f"{sample}\n\n"
        "Summarize trends, top users, and task types in a few sentences."
    )

    openai.api_key = os.getenv("OPENAI_API_KEY")

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a data analyst."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150,
            temperature=0.6
        )
        return response.choices[0].message['content'].strip(), "OpenAI"
    except Exception as e:
        return f"(Fallback Summary) Top user: {filtered_data['user_first_name'].mode()[0]}. " \
               f"Most frequent task: {filtered_data['task'].mode()[0]}.", "Fallback"

# --- PDF Report Generator ---
def generate_pdf(summary_text, fig1, fig2):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, "Task Time Analysis Summary", align="C")
    pdf.ln()

    pdf.set_font("Arial", size=11)
    pdf.multi_cell(0, 10, summary_text)
    pdf.ln()

    temp_dir = tempfile.gettempdir()
    path1 = os.path.join(temp_dir, "top_users.png")
    path2 = os.path.join(temp_dir, "top_tasks.png")
    fig1.write_image(path1)
    fig2.write_image(path2)

    pdf.image(path1, x=10, w=180)
    pdf.add_page()
    pdf.image(path2, x=10, w=180)

    output_path = os.path.join(temp_dir, "task_summary_report.pdf")
    pdf.output(output_path)
    return output_path

# --- Main App Logic ---
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

    # Tabs
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
        "📊 Summary", "📈 Visualizations", "📋 Task Records",
        "👤 User Drilldown", "⏰ Hourly Analysis", "📅 Calendar Heatmap",
        "🧠 AI Summary", "📑 All Uploaded Data"
    ])

    with tab1:
        st.subheader("Minutes Uploaded by Each User")
        minute_table = filtered_df.groupby('user_first_name')['minutes'].sum().reset_index()
        st.dataframe(minute_table, use_container_width=True)

        st.subheader("User List")
        user_table = df[['user_first_name', 'user_last_name', 'user_locale']].drop_duplicates()
        st.dataframe(user_table, use_container_width=True)

        total_minutes = filtered_df['minutes'].sum()
        avg_minutes = filtered_df['minutes'].mean()
        total_tasks = filtered_df.shape[0]

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Time Spent (min)", total_minutes)
        col2.metric("Avg Time per Task (min)", round(avg_minutes, 2))
        col3.metric("Total Tasks", total_tasks)

    with tab2:
        st.markdown("### Time Spent per User")
        user_chart = filtered_df.groupby('user_first_name')['minutes'].sum().reset_index()
        fig_user = px.bar(user_chart, x='user_first_name', y='minutes', title='Total Minutes per User')
        st.plotly_chart(fig_user, use_container_width=True)

        st.markdown("### Time Distribution by Date")
        date_chart = filtered_df.groupby('date')['minutes'].sum().reset_index()
        fig_date = px.line(date_chart, x='date', y='minutes', markers=True)
        st.plotly_chart(fig_date, use_container_width=True)

        task_summary = filtered_df.groupby('task')['minutes'].sum().reset_index().sort_values(by='minutes', ascending=False)
        col1, col2 = st.columns(2)
        with col1:
            fig_pie = px.pie(task_summary, names='task', values='minutes', title="Minutes by Task Type")
            st.plotly_chart(fig_pie, use_container_width=True)
        with col2:
            fig_bar = px.bar(task_summary, x='task', y='minutes', title='Task Breakdown')
            st.plotly_chart(fig_bar, use_container_width=True)

    with tab3:
        st.markdown("### Task Records")
        st.dataframe(filtered_df[['date', 'user_first_name', 'user_last_name', 'task', 'minutes']], use_container_width=True)
        st.download_button("📥 Download Filtered Data", data=filtered_df.to_csv(index=False), file_name="filtered_data.csv")

    with tab4:
        st.subheader("User Drilldown")
        selected_user = st.selectbox("Select User", options=filtered_df['user_first_name'].unique())
        user_df = filtered_df[filtered_df['user_first_name'] == selected_user]
        col1, col2 = st.columns(2)
        col1.metric("Total Minutes", user_df['minutes'].sum())
        col2.metric("Avg Task Time", round(user_df['minutes'].mean(), 2))

        drill_chart = user_df.groupby('task')['minutes'].sum().reset_index()
        fig_drill = px.bar(drill_chart, x='task', y='minutes', title=f"Task Breakdown for {selected_user}")
        st.plotly_chart(fig_drill, use_container_width=True)
        st.dataframe(user_df[['date', 'task', 'minutes']], use_container_width=True)

    with tab5:
        st.subheader("Hourly Time-of-Day Analysis")
        hourly = filtered_df.groupby('hour')['minutes'].sum().reset_index()
        fig_hour = px.bar(hourly, x='hour', y='minutes', title="Minutes by Hour")
        st.plotly_chart(fig_hour, use_container_width=True)

    with tab6:
        st.subheader("Calendar Heatmap")
        heatmap_data = filtered_df.groupby('date')['minutes'].sum().reset_index()
        heatmap_data['date'] = pd.to_datetime(heatmap_data['date'])
        fig, _ = calplot.calplot(heatmap_data.set_index('date')['minutes'], cmap='YlGn', figsize=(16, 8))
        st.pyplot(fig)

    with tab7:
        st.subheader("🧠 AI-Generated Summary")
        with st.spinner("Generating summary with AI..."):
            summary_text, summary_method = generate_summary(filtered_df)
            st.success("Summary generated using: " + summary_method)
            st.markdown(summary_text)

            # Download options
            st.download_button("💾 Download Summary (TXT)", data=summary_text, file_name="task_summary.txt")
            summary_df = pd.DataFrame({"method": [summary_method], "summary": [summary_text]})
            st.download_button("📄 Download Summary (CSV)", data=summary_df.to_csv(index=False), file_name="task_summary.csv")

            # Generate top user/task charts
            top_users = filtered_df.groupby('user_first_name')['minutes'].sum().nlargest(5).reset_index()
            top_tasks = filtered_df.groupby('task')['minutes'].sum().nlargest(5).reset_index()
            fig1 = px.bar(top_users, x='user_first_name', y='minutes', title="Top 5 Users by Time Spent")
            fig2 = px.pie(top_tasks, names='task', values='minutes', title="Top 5 Tasks by Minutes")
            st.plotly_chart(fig1)
            st.plotly_chart(fig2)

            # Generate PDF
            if st.button("📄 Generate PDF Report"):
                pdf_path = generate_pdf(summary_text, fig1, fig2)
                with open(pdf_path, "rb") as f:
                    base64_pdf = base64.b64encode(f.read()).decode('utf-8')
                href = f'<a href="data:application/octet-stream;base64,{base64_pdf}" download="task_summary_report.pdf">📥 Download PDF Report</a>'
                st.markdown(href, unsafe_allow_html=True)

    with tab8:
        st.subheader("All Uploaded Data (Before Filtering)")
        st.dataframe(df, use_container_width=True)
        st.download_button("📥 Download All Uploaded Data", data=df.to_csv(index=False), file_name="all_uploaded_data.csv")

else:
    st.info("Upload one or more CSV files to begin.")
