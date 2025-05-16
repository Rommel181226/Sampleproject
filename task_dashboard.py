import streamlit as st
import pandas as pd
import plotly.express as px
import calplot
import os
from wordcloud import WordCloud
import matplotlib.pyplot as plt

# Page configuration
st.set_page_config(page_title="Task Dashboard", layout="wide")
st.title("🗂️ Task Time Analysis Dashboard")

# Sidebar logo (optional)
logo_path = os.path.join("images", "logo.png")
if os.path.exists(logo_path):
    st.sidebar.image(logo_path, width=150)
st.sidebar.markdown("## 📁 Task Dashboard Sidebar")

# File uploader widget for multiple CSV files
uploaded_files = st.sidebar.file_uploader(
    "Upload CSV files", type=["csv"], accept_multiple_files=True
)

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

    users = df['user_first_name'].dropna().unique()
    min_date, max_date = df['date'].min(), df['date'].max()

    st.sidebar.subheader("Filter Data")
    selected_users = st.sidebar.multiselect("User", options=users, default=list(users))
    selected_dates = st.sidebar.date_input("Date Range", [min_date, max_date])

    mask = (
        df['user_first_name'].isin(selected_users) &
        (df['date'] >= selected_dates[0]) & (df['date'] <= selected_dates[1])
    )
    filtered_df = df[mask]

    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
        "📊 Summary", "📈 Visualizations", "⏱️ Task Duration Distribution",
        "👤 User Drilldown", "☁️ Word Cloud", "📅 Calendar Heatmap",
        "📑 All Uploaded Data", "👥 User Comparison", "🕒 Hourly Heatmap"
    ])

    with tab1:
        st.subheader("User Summary")
        user_summary = (
            filtered_df
            .groupby(['user_first_name', 'user_last_name', 'user_locale'])
            .agg(
                Total_Minutes=('minutes', 'sum'),
                Task_Count=('minutes', 'count'),
                Avg_Minutes_Per_Task=('minutes', 'mean')
            )
            .reset_index()
            .sort_values(by='Total_Minutes', ascending=False)
        )
        user_summary['Avg_Minutes_Per_Task'] = user_summary['Avg_Minutes_Per_Task'].round(2)
        user_summary.columns = ['First Name', 'Last Name', 'Locale', 'Total Minutes', 'Task Count', 'Avg Minutes/Task']
        st.dataframe(user_summary, use_container_width=True)

        st.download_button(
            label="📥 Download User Summary",
            data=user_summary.to_csv(index=False),
            file_name="user_summary.csv"
        )

        total_minutes = filtered_df['minutes'].sum()
        avg_minutes = filtered_df['minutes'].mean()
        total_tasks = filtered_df.shape[0]

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Time Spent (min)", total_minutes)
        col2.metric("Average Time per Task (min)", round(avg_minutes, 2))
        col3.metric("Total Tasks", total_tasks)

        # AI Summary
        st.markdown("### 🧠 AI Summary")
        top_user = user_summary.iloc[0]['First Name']
        top_minutes = user_summary.iloc[0]['Total Minutes']
        top_tasks = user_summary.iloc[0]['Task Count']
        avg_task_time = user_summary['Avg Minutes/Task'].mean()

        summary_text = (
            f"Between **{selected_dates[0]}** and **{selected_dates[1]}**, a total of **{total_minutes} minutes** "
            f"were logged across **{total_tasks} tasks** by **{len(selected_users)} users**. "
            f"The average task duration was **{round(avg_minutes, 2)} minutes**. "
            f"**{top_user}** contributed the most with **{top_minutes} minutes** across **{top_tasks} tasks**. "
            f"Overall, users spent an average of **{round(avg_task_time, 2)} minutes per task**."
        )

        st.info(summary_text)

    with tab2:
        st.markdown("## 📈 Visualizations")

        st.markdown("### Total Time Spent per User")
        st.write("This bar chart shows total minutes logged by each user within the selected filters.")
        time_chart = filtered_df.groupby('user_first_name')['minutes'].sum().reset_index()
        fig_time = px.bar(
            time_chart,
            x='user_first_name',
            y='minutes',
            title='Total Minutes per User',
            labels={'user_first_name': 'User', 'minutes': 'Total Minutes'},
            text='minutes'
        )
        fig_time.update_traces(texttemplate='%{text:.2s}', textposition='outside')
        st.plotly_chart(fig_time, use_container_width=True)

        st.markdown("---")
        st.markdown("### Time Distribution Over Time")
        date_chart = filtered_df.groupby('date')['minutes'].sum().reset_index()
        fig_date = px.line(
            date_chart,
            x='date',
            y='minutes',
            markers=True,
            title='Minutes Logged Over Time',
            labels={'date': 'Date', 'minutes': 'Total Minutes'}
        )
        st.plotly_chart(fig_date, use_container_width=True)

        st.markdown("---")
        st.markdown("### Breakdown by Task Type")
        task_summary = filtered_df.groupby('task')['minutes'].sum().reset_index().sort_values(by='minutes', ascending=False)

        col1, col2 = st.columns(2)
        with col1:
            fig_pie = px.pie(
                task_summary,
                names='task',
                values='minutes',
                title="Total Minutes by Task Type",
                hole=0.3
            )
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_pie, use_container_width=True)

        with col2:
            fig_bar = px.bar(
                task_summary,
                x='task',
                y='minutes',
                title='Total Minutes by Task Type',
                labels={'task': 'Task', 'minutes': 'Total Minutes'},
                text_auto=True
            )
            fig_bar.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_bar, use_container_width=True)

    with tab3:
        st.subheader("Task Duration Distribution")
        fig_hist = px.histogram(
            filtered_df,
            x='minutes',
            nbins=30,
            title="Histogram of Task Durations (minutes)",
            labels={"minutes": "Task Duration (minutes)"}
        )
        st.plotly_chart(fig_hist, use_container_width=True)

        fig_box = px.box(
            filtered_df,
            y='minutes',
            title="Boxplot of Task Durations",
            labels={"minutes": "Task Duration (minutes)"}
        )
        st.plotly_chart(fig_box, use_container_width=True)

        st.subheader("Outlier Detection (Task Duration)")
        Q1 = filtered_df['minutes'].quantile(0.25)
        Q3 = filtered_df['minutes'].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR

        st.write(f"Outlier thresholds: Tasks shorter than {lower_bound:.2f} min or longer than {upper_bound:.2f} min.")
        outliers = filtered_df[(filtered_df['minutes'] < lower_bound) | (filtered_df['minutes'] > upper_bound)]

        if outliers.empty:
            st.success("No outliers detected in task durations.")
        else:
            st.warning(f"Detected {outliers.shape[0]} outlier tasks:")
            st.dataframe(outliers[['date', 'user_first_name', 'task', 'minutes']], use_container_width=True)

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

    with tab5:
        st.subheader("Word Cloud of Tasks")
        text = " ".join(filtered_df['task'].dropna().astype(str).values)
        if not text.strip():
            st.info("No task data available for word cloud.")
        else:
            wc = WordCloud(width=800, height=400, background_color="white").generate(text)
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.imshow(wc, interpolation='bilinear')
            ax.axis("off")
            st.pyplot(fig)

    with tab6:
        st.subheader("Calendar Heatmap")
        heatmap_data = filtered_df.groupby('date')['minutes'].sum().reset_index()
        heatmap_data['date'] = pd.to_datetime(heatmap_data['date'])
        heatmap_series = heatmap_data.set_index('date')['minutes']

        fig, ax = calplot.calplot(
            heatmap_series,
            cmap='YlGn',
            colorbar=True,
            figsize=(16, 6),
            suptitle="Minutes Logged by Date"
        )
        st.pyplot(fig)

    with tab7:
        st.subheader("Raw Uploaded Data")
        st.write(f"Showing {filtered_df.shape[0]} rows.")
        st.dataframe(filtered_df, use_container_width=True)

    with tab8:
        st.subheader("User Comparison")
        comp_users = st.multiselect("Select Users to Compare", options=users, default=users[:2])
        if len(comp_users) < 2:
            st.info("Please select at least two users to compare.")
        else:
            comp_df = filtered_df[filtered_df['user_first_name'].isin(comp_users)]
            comp_summary = (
                comp_df.groupby(['user_first_name', 'task'])['minutes']
                .sum()
                .reset_index()
            )
            fig_comp = px.bar(
                comp_summary,
                x='task',
                y='minutes',
                color='user_first_name',
                barmode='group',
                title="Task Time Comparison Between Users",
                labels={'task': 'Task', 'minutes': 'Total Minutes', 'user_first_name': 'User'}
            )
            fig_comp.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_comp, use_container_width=True)

    with tab9:
        st.subheader("🕒 Hourly Activity Heatmap")

        if 'hour' in filtered_df.columns:
            heatmap_df = filtered_df.copy()
            heatmap_df['day'] = pd.to_datetime(heatmap_df['date']).dt.day_name()

            pivot = heatmap_df.groupby(['hour', 'day'])['minutes'].sum().reset_index()
            pivot_table = pivot.pivot(index='hour', columns='day', values='minutes').fillna(0)

            ordered_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            pivot_table = pivot_table.reindex(columns=ordered_days)

            st.write("This heatmap shows total minutes logged by hour and day of week.")
            fig = px.imshow(
                pivot_table,
                labels=dict(x="Day", y="Hour", color="Total Minutes"),
                x=pivot_table.columns,
                y=pivot_table.index,
                color_continuous_scale='YlOrRd',
                aspect="auto"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No hour data available. Make sure 'started_at' was properly parsed.")

else:
    st.info("Please upload one or more CSV files to get started.")
