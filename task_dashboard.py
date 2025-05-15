import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
from wordcloud import WordCloud
from textblob import TextBlob
import nltk
nltk.download('punkt')
from datetime import datetime
from collections import Counter

st.set_page_config(layout="wide")
st.title("⏱️ Task Time Analysis Dashboard")

uploaded_files = st.sidebar.file_uploader("Upload CSV files", accept_multiple_files=True, type="csv")

if uploaded_files:
    dataframes = [pd.read_csv(file) for file in uploaded_files]
    df = pd.concat(dataframes, ignore_index=True)

    # Convert time columns
    df['start_time'] = pd.to_datetime(df['start_time'], errors='coerce')
    df['end_time'] = pd.to_datetime(df['end_time'], errors='coerce')
    df['duration'] = (df['end_time'] - df['start_time']).dt.total_seconds() / 60

    df['date'] = pd.to_datetime(df['start_time']).dt.date
    df['hour'] = pd.to_datetime(df['start_time']).dt.hour

    # Sidebar filters
    users = st.sidebar.multiselect("Filter by User", options=df['user'].unique(), default=list(df['user'].unique()))
    locales = st.sidebar.multiselect("Filter by Locale", options=df['locale'].unique(), default=list(df['locale'].unique()))
    date_range = st.sidebar.date_input("Filter by Date Range", [df['date'].min(), df['date'].max()])

    filtered_df = df[
        (df['user'].isin(users)) &
        (df['locale'].isin(locales)) &
        (df['date'] >= date_range[0]) &
        (df['date'] <= date_range[1])
    ]

    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
        "📊 Summary", "📈 Visualizations", "⏱️ Task Duration Distribution",
        "👤 User Drilldown", "☁️ Word Cloud", "📅 Calendar Heatmap",
        "📑 All Uploaded Data", "👥 User Comparison", "🧠 NLP Analysis"
    ])

    # Tab 1: Summary
    with tab1:
        st.subheader("Summary Metrics")
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Tasks", len(filtered_df))
        col2.metric("Total Duration (min)", round(filtered_df['duration'].sum(), 2))
        col3.metric("Avg Task Duration (min)", round(filtered_df['duration'].mean(), 2))

    # Tab 2: Visualizations
    with tab2:
        st.subheader("Visualizations")
        fig = px.histogram(filtered_df, x='user', y='duration', color='locale', barmode='group', title='Total Duration per User by Locale')
        st.plotly_chart(fig, use_container_width=True)

    # Tab 3: Task Duration Distribution
    with tab3:
        st.subheader("Task Duration Distribution")
        fig = px.box(filtered_df, x='user', y='duration', color='locale', points='all', title='Task Duration Distribution per User')
        st.plotly_chart(fig, use_container_width=True)

    # Tab 4: User Drilldown
    with tab4:
        st.subheader("User Drilldown")
        for user in users:
            st.markdown(f"### 👤 {user}")
            user_df = filtered_df[filtered_df['user'] == user]
            fig = px.histogram(user_df, x='date', y='duration', title=f'Task Duration Over Time for {user}')
            st.plotly_chart(fig, use_container_width=True)

    # Tab 5: Word Cloud
    with tab5:
        st.subheader("Word Cloud of Task Descriptions")
        text = " ".join(filtered_df['task'].dropna().astype(str))
        wordcloud = WordCloud(width=800, height=400, background_color='white').generate(text)
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.imshow(wordcloud, interpolation='bilinear')
        ax.axis("off")
        st.pyplot(fig)

    # Tab 6: Calendar Heatmap
    with tab6:
        st.subheader("Calendar Heatmap")
        heatmap_df = filtered_df.groupby(['date', 'user'])['duration'].sum().unstack(fill_value=0)
        st.dataframe(heatmap_df)

    # Tab 7: All Uploaded Data
    with tab7:
        st.subheader("Raw Data")
        st.dataframe(filtered_df, use_container_width=True)

    # Tab 8: User Comparison
    with tab8:
        st.subheader("User Comparison Table")
        summary = filtered_df.groupby('user').agg(
            Total_Tasks=('task', 'count'),
            Total_Duration_Min=('duration', 'sum'),
            Average_Duration_Min=('duration', 'mean')
        ).reset_index()
        st.dataframe(summary)

    # Tab 9: NLP Analysis
    with tab9:
        st.subheader("🧠 NLP Analysis of Task Descriptions")

        if 'task' not in filtered_df.columns or filtered_df['task'].dropna().empty:
            st.info("No task descriptions available for NLP analysis.")
        else:
            task_text = filtered_df['task'].dropna().astype(str)

            # --- Keyword Frequency ---
            all_words = " ".join(task_text).lower().split()
            common_words = Counter(all_words).most_common(20)
            keyword_df = pd.DataFrame(common_words, columns=['Keyword', 'Frequency'])

            st.markdown("### 📋 Top Keywords in Task Descriptions")
            st.dataframe(keyword_df)

            # --- Word Cloud ---
            st.markdown("### ☁️ Word Cloud")
            wc = WordCloud(width=800, height=400, background_color="white").generate(" ".join(all_words))
            fig_wc, ax_wc = plt.subplots(figsize=(12, 6))
            ax_wc.imshow(wc, interpolation="bilinear")
            ax_wc.axis("off")
            st.pyplot(fig_wc)

            # --- Sentiment Analysis ---
            st.markdown("### 😄 Sentiment Analysis")
            sentiments = task_text.apply(lambda x: TextBlob(x).sentiment.polarity)
            sentiment_df = pd.DataFrame({'Task': task_text, 'Polarity': sentiments})
            sentiment_df['Sentiment'] = sentiment_df['Polarity'].apply(
                lambda x: 'Positive' if x > 0 else 'Negative' if x < 0 else 'Neutral'
            )

            fig_sent = px.histogram(
                sentiment_df, x='Polarity', nbins=20,
                title='Distribution of Task Sentiment Polarity',
                color='Sentiment'
            )
            st.plotly_chart(fig_sent, use_container_width=True)

            st.markdown("### 📄 Task Sentiment Table")
            st.dataframe(sentiment_df, use_container_width=True)

else:
    st.warning("Please upload at least one CSV file to begin analysis.")
