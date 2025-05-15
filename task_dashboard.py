import streamlit as st
import pandas as pd
import plotly.express as px
import calendar
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

    df['date'] = pd.to_datetime(df['date'])
    df['hour'] = df['date'].dt.hour
    df['day'] = df['date'].dt.day_name()
    df['month'] = df['date'].dt.month_name()
    df['day_num'] = df['date'].dt.day

    users = st.sidebar.multiselect("Filter by user", options=df['user'].unique(), default=df['user'].unique())
    locales = st.sidebar.multiselect("Filter by locale", options=df['locale'].unique(), default=df['locale'].unique())
    start_date = st.sidebar.date_input("Start date", df['date'].min().date())
    end_date = st.sidebar.date_input("End date", df['date'].max().date())

    filtered_df = df[
        (df['user'].isin(users)) &
        (df['locale'].isin(locales)) &
        (df['date'] >= pd.to_datetime(start_date)) &
        (df['date'] <= pd.to_datetime(end_date))
    ]

    tabs = ["Summary", "Dashboard", "Task Types", "User View", "Hourly Analysis", "Calendar View", "Raw Data", "AI Summary"]
    selected_tab = st.sidebar.radio("Select Tab", tabs)

    if selected_tab == "Summary":
        st.subheader("📊 Summary Metrics")
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Tasks", len(filtered_df))
        col2.metric("Total Minutes", filtered_df['minutes'].sum())
        col3.metric("Avg. Minutes/Task", round(filtered_df['minutes'].mean(), 2))

    elif selected_tab == "Dashboard":
        st.subheader("📈 Time Spent by Task")
        fig = px.bar(filtered_df.groupby('task')['minutes'].sum().reset_index().sort_values(by='minutes', ascending=False),
                     x='task', y='minutes', title='Minutes by Task')
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("📍 Time by Locale")
        fig2 = px.pie(filtered_df, names='locale', values='minutes', title='Time Distribution by Locale')
        st.plotly_chart(fig2, use_container_width=True)

    elif selected_tab == "Task Types":
        st.subheader("🗂️ Task Type Breakdown")
        task_df = filtered_df.groupby(['task', 'user'])['minutes'].sum().reset_index()
        fig = px.bar(task_df, x='task', y='minutes', color='user', barmode='group', title='Task Types by User')
        st.plotly_chart(fig, use_container_width=True)

    elif selected_tab == "User View":
        st.subheader("👤 User Drilldown")
        user_df = filtered_df.groupby(['user', 'task'])['minutes'].sum().reset_index()
        fig = px.sunburst(user_df, path=['user', 'task'], values='minutes', title='User > Task Drilldown')
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

    elif selected_tab == "AI Summary":
        st.header("🧠 AI Summary & Reports")

        total_minutes = filtered_df['minutes'].sum()
        avg_minutes = filtered_df['minutes'].mean()
        most_common_task = filtered_df['task'].mode()[0] if not filtered_df.empty else 'N/A'
        top_user = filtered_df['user'].value_counts().idxmax() if not filtered_df.empty else 'N/A'

        summary_text = f"""
        ✅ Total time tracked: **{total_minutes:.2f} minutes**
        📌 Average task time: **{avg_minutes:.2f} minutes**
        ⭐ Most frequent task: **{most_common_task}**
        🧑 Top user: **{top_user}**
        """

        st.markdown(summary_text)

        st.download_button("💾 Download Summary (TXT)", data=summary_text, file_name="task_summary.txt", mime="text/plain")

        summary_df = pd.DataFrame([{
            "Total Minutes": total_minutes,
            "Average Minutes": avg_minutes,
            "Most Common Task": most_common_task,
            "Top User": top_user
        }])

        st.download_button("📥 Download Summary (CSV)", data=summary_df.to_csv(index=False), file_name="summary.csv", mime="text/csv")

        if st.button("📄 Generate PDF Report"):
            buffer = BytesIO()
            c = canvas.Canvas(buffer, pagesize=letter)
            c.setFont("Helvetica", 12)
            c.drawString(40, 750, "🧠 Task Time Summary Report")
            c.drawString(40, 730, f"Total Time: {total_minutes:.2f} mins")
            c.drawString(40, 710, f"Average Time: {avg_minutes:.2f} mins")
            c.drawString(40, 690, f"Most Common Task: {most_common_task}")
            c.drawString(40, 670, f"Top User: {top_user}")
            c.drawString(40, 640, "📈 Minutes by Task Chart:")

            fig, ax = plt.subplots()
            task_chart = filtered_df.groupby('task')['minutes'].sum().nlargest(5)
            task_chart.plot(kind='bar', ax=ax)
            ax.set_title('Top 5 Tasks by Time')
            ax.set_ylabel('Minutes')
            plt.tight_layout()

            chart_buffer = BytesIO()
            plt.savefig(chart_buffer, format='PNG')
            plt.close()
            chart_buffer.seek(0)
            c.drawInlineImage(chart_buffer, 40, 400, width=500, height=200)

            c.save()
            buffer.seek(0)

            st.download_button("📥 Download PDF Report", buffer, file_name="task_summary_report.pdf")

else:
    st.info("👈 Upload one or more CSV files to begin.")
