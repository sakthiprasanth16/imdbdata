import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np

#tidb_database
host = "gateway01.eu-central-1.prod.aws.tidbcloud.com"
port = 4000
user = "42aq8sKC2dkkKnC.root"
password = "YOUR PASSWORD"
database = "grab"
ssl_ca_path = "YOUY PATH"
ssl_args = f"?ssl_ca={ssl_ca_path}"

engine = create_engine(
    f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}{ssl_args}"
)

#load_data
@st.cache_data
def load_data():
    query = "SELECT * FROM movies"
    return pd.read_sql(query, engine)

df = load_data()

#front_page
st.title("IMDb Movie Analytics")
if st.button("Go to Dashboard"):
    st.session_state['dashboard'] = True

if 'dashboard' in st.session_state:

    #menu
    selected_tab = st.radio(
        "Please Select",
        ["Top 10 Movies", "Movie Analysis", "All Movies Data", "Data Analytics"]
    )

    #tab1_top10_movies
    if selected_tab == "Top 10 Movies":
        genre_list = list(df["genre"].unique())
        genre_select_mode = st.radio("Genre Filter", ["All Genres", "Custom Selection"])

        if genre_select_mode == "All Genres":
            selected_top_genre = genre_list
            st.info("Showing Top 10 Movies In All Genres")
        else:
            selected_top_genre = st.multiselect("Select Genres for Top 10 Movies", genre_list)
            if not selected_top_genre:
                st.warning("Select at least one genre to show")
                st.stop()

        top_df = df[df["genre"].isin(selected_top_genre)].copy()

        name_col = None
        for col in ["title", "name", "movie_name"]:
            if col in top_df.columns:
                name_col = col
                break
        if not name_col:
            st.error("No valid movie name")
            st.stop()

        sort_option = st.radio("Sort Top 10 By", ["Rating", "Votes", "Rating & Votes"])

        if sort_option == "Rating":
            sorted_df = top_df.sort_values(by="rating", ascending=False)
        elif sort_option == "Votes":
            sorted_df = top_df.sort_values(by="votes", ascending=False)
        else:
            top_df["score"] = top_df["rating"] * np.log(top_df["votes"] + 1)
            sorted_df = top_df.sort_values(by="score", ascending=False)

        st.subheader("Top 10 Movies Here")
        top_movies = sorted_df.drop_duplicates(subset=name_col).head(10)

        display_columns = [name_col, "genre","duration","rating", "votes"]
        st.dataframe(top_movies[display_columns])


    #tab2_Movie Analysis
    elif selected_tab == "Movie Analysis":
        st.subheader("Genre Distribution")

        genre_counts = df["genre"].value_counts().reset_index()
        genre_counts.columns = ["Genre", "Count"]

        f1, ax1 = plt.subplots(figsize=(10, 6))
        sns.barplot(data=genre_counts, x="Genre", y="Count", palette="viridis", ax=ax1)
        ax1.set_title("Number of Movies per Genre")
        ax1.set_xlabel("Genre")
        ax1.set_ylabel("Number of Movies")
        ax1.tick_params(axis='x', rotation=45)
        st.pyplot(f1)

        #movie_duration
        st.subheader("Average Duration by Genre")
        avg_duration = df.groupby("genre")["duration_minutes"].mean().sort_values(ascending=True).reset_index()

        f2, ax2 = plt.subplots(figsize=(10, 6))
        sns.barplot(data=avg_duration, x="duration_minutes", y="genre", palette="mako", ax=ax2)
        ax2.set_title("Average Movie Duration per Genre")
        ax2.set_xlabel("Average Duration (In Minutes)")
        ax2.set_ylabel("Genre")
        st.pyplot(f2)

        #vote_trends
        st.subheader("Voting Trends by Genre")
        avg_votes = df.groupby("genre")["votes"].mean().sort_values(ascending=True).reset_index()

        f3, ax3 = plt.subplots(figsize=(10, 6))
        sns.barplot(data=avg_votes, x="votes", y="genre", palette="cubehelix", ax=ax3)
        ax3.set_title("Average Voting Count per Genre")
        ax3.set_xlabel("Average Votes")
        ax3.set_ylabel("Genre")
        st.pyplot(f3)

        #rating_distribution
        st.subheader("Rating Distribution")
        f4, ax4 = plt.subplots(figsize=(10, 6))
        sns.boxplot(data=df, x="rating", color="lightcoral", ax=ax4)
        ax4.set_title("Movie Ratings in Box plot")
        ax4.set_xlabel("Rating")
        st.pyplot(f4)

        #rating_leaders
        st.subheader("Genre-Based Rating Leaders")
        title_col = None
        for col in ["title", "name", "movie_name"]:
            if col in df.columns:
                title_col = col
                break

        if title_col:
            top_rated_per_genre = df.sort_values(by="rating", ascending=False).drop_duplicates(subset=["genre"])
            top_rated_per_genre = top_rated_per_genre[["genre", title_col, "rating", "votes"]].sort_values(by="genre")
            top_rated_per_genre.columns = ["Genre", "Top Movie", "Rating", "Votes"]
            st.dataframe(top_rated_per_genre, use_container_width=True)
        else:
            st.warning("Nothing")

        #popular_genre
        st.subheader("Most Popular Genres by Voting")
        total_votes_per_genre = df.groupby("genre")["votes"].sum().sort_values(ascending=False)
        f5, ax5 = plt.subplots(figsize=(8, 8))
        ax5.pie(total_votes_per_genre, labels=total_votes_per_genre.index, autopct="%1.1f%%", startangle=140, colors=sns.color_palette("pastel"))
        ax5.set_title("Most Popular Genres by Total Voting Counts")
        ax5.axis("equal")
        st.pyplot(f5)

        #duration_distribution
        st.subheader("Movie Duration Distribution")
        f6, ax8 = plt.subplots(figsize=(10, 6))
        sns.boxplot(data=df, x="duration_minutes", color="skyblue", ax=ax8)
        ax8.set_title("Movie Durations in Box plot")
        ax8.set_xlabel("Duration (In Minutes)")
        st.pyplot(f6)

        #duration_extremes
        st.subheader("Duration Extremes")
        if title_col:
            valid_durations = df[df["duration_minutes"] > 0]

            if not valid_durations.empty:
                shortest = valid_durations.loc[valid_durations["duration_minutes"].idxmin()]
                longest = df.loc[df["duration_minutes"].idxmax()]

                def minutes_to_text(minutes):
                    h = minutes // 60
                    m = minutes % 60
                    return f"{int(h)}h {int(m)}m"

                extremes_df = pd.DataFrame([
                    {
                        "Type": "Shortest",
                        "Title": shortest[title_col],
                        "Genre": shortest["genre"],
                        "Duration": minutes_to_text(shortest["duration_minutes"])
                    },
                    {
                        "Type": "Longest",
                        "Title": longest[title_col],
                        "Genre": longest["genre"],
                        "Duration": minutes_to_text(longest["duration_minutes"])
                    }
                ])

                st.table(extremes_df)
            else:
                st.warning("No movie durations > 0")
        else:
            st.warning("Movie titles not found")

        #heatmap
        st.subheader("Ratings by Genre")
        avg_rating_genre = df.groupby("genre")["rating"].mean().reset_index()
        avg_rating_genre_pivot = avg_rating_genre.pivot_table(index="genre", values="rating")

        f7, ax6 = plt.subplots(figsize=(8, len(avg_rating_genre_pivot) * 0.5 + 2))
        sns.heatmap(avg_rating_genre_pivot, annot=True, fmt=".2f", cmap="coolwarm", linewidths=0.5, ax=ax6)
        ax6.set_title("Average Rating by Genre")
        #ax6.set_xlabel("Rating")
        ax6.set_ylabel("Genre")
        st.pyplot(f7)

        #correlation
        st.subheader("Correlation Analysis")
        f8, ax7 = plt.subplots(figsize=(10, 6))
        sns.scatterplot(data=df, x="votes", y="rating", hue="genre", alpha=0.7, palette="husl", ax=ax7)
        ax7.set_title("Relationship Between Votes and Ratings")
        ax7.set_xlabel("Votes")
        ax7.set_ylabel("Rating")
        ax7.legend(bbox_to_anchor=(1.05, 1), loc='upper left', title="Genre")
        st.pyplot(f8)

    #tab3_allmovie_data
    elif selected_tab == "All Movies Data":
        st.subheader("All Movies Data")

        title_col = None
        for col in ["movie_name", "duration", "rating", "votes"]:
            if col in df.columns:
                title_col = col
                break

        if not title_col:
            st.error("No movie titles")
        else:
            display_cols = [title_col, "duration", "rating", "votes"]

            selected_all_genre = st.selectbox(
                "Select Genre to View All Movies",
                ["All Genres"] + list(df["genre"].unique())
            )

            if selected_all_genre == "All Genres":
                total_count = len(df)
                st.markdown(f"Total Movies : {total_count}")
                st.dataframe(df[display_cols])
            else:
                filtered_df = df[df["genre"] == selected_all_genre]
                total_count = len(filtered_df)
                st.markdown(f"Total Movies : {total_count}")
                st.dataframe(filtered_df[display_cols])

    #tab4_data_analytics
    elif selected_tab == "Data Analytics":
        st.sidebar.header("Custom Filters")
        genre_filter_mode = st.sidebar.radio("Genre Filter Mode", ["All Genres", "Custom Selection"])

        if genre_filter_mode == "All Genres":
            selected_genre = df["genre"].unique().tolist()
        else:
            selected_genre = st.sidebar.multiselect("Select Genre(s)", df["genre"].unique().tolist())
            if not selected_genre:
                st.sidebar.warning("Please select at least one genre to apply filters")


        duration_filter = st.sidebar.slider("Select Movie Duration (Minutes)", 0, 300, (90, 180))
        rating_filter = st.sidebar.slider("Select Minimum Rating", 0.0, 10.0, 7.0)
        votes_filter = st.sidebar.slider("Select Minimum Votes", 0, 500000, 10000)

        #filters
        filtered_df = df[
            (df["duration_minutes"].between(duration_filter[0], duration_filter[1])) &
            (df["rating"] >= rating_filter) &
            (df["votes"] >= votes_filter) &
            (df["genre"].isin(selected_genre))
        ]

        #filter_view
        st.subheader("Filtered Movies")
        st.write(f"Showing {len(filtered_df)} movies matching your filters")
        st.dataframe(filtered_df)
    else:
        filtered_df = df.copy()