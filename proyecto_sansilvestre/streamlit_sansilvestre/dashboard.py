import streamlit as st
import pandas as pd
import plotly.express as px
import mysql.connector
import re
import os
from dotenv import load_dotenv

load_dotenv()
st.set_page_config(page_title="Race Analytics Dashboard", layout="wide")

# DB Config
DB_CONFIG={
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME')
}
@st.cache_data
def load_data():
    conn = mysql.connector.connect(**DB_CONFIG)
    
    # Unify 3 tables in one dataframe
    query = """
    SELECT 
        res.finish_time, 
        res.age_group, 
        r.name as runner_name, 
        r.gender, 
        ra.location, 
        ra.year, 
        ra.distance,
        ra.id as race_id
    FROM race_results res
    JOIN runners r ON res.runner_id = r.id
    JOIN races ra ON res.race_id = ra.id
    """
    df = pd.read_sql(query, conn)
    conn.close()
    
    # Data cleansing and conversing
    df['total_seconds'] = df['finish_time'].dt.total_seconds()
    # Create "minutes" column for graphics
    df['minutes'] = df['total_seconds'] / 60
    
    return df

# Format time to format HH:MM:SS
def format_time(seconds):
    if pd.isna(seconds): return "N/A"
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d}"

# Extract numeric distance
def extract_distance(dist_str):
    try:
        # Busca números (puede tener decimales)
        match = re.search(r"(\d+(\.\d+)?)", str(dist_str))
        return float(match.group(1)) if match else None
    except:
        return None

try:
    df_all = load_data()
except Exception as e:
    st.error(f"❌ Connection to database failed: {e}")
    st.stop()


st.sidebar.title("🏃 Race Analytics")
view_mode = st.sidebar.radio("Select view:", ["Race Analysis", "Runner Analysis"])

if view_mode == "Race Analysis":
    st.title("📊 Race Analysis")

    race_options = df_all[['location', 'year', 'race_id']].drop_duplicates()
    race_options['label'] = race_options['location'] + " (" + race_options['year'].astype(str) + ")"
    
    list_of_races = sorted(race_options['label'].unique().tolist())
    dropdown_options = ["All Races"] + list_of_races
    selected_option = st.selectbox("Select edition:", options=dropdown_options)
    
    if selected_option == "All Races":
        df_race = df_all.copy()
        chart_title = "Time distribution (All Races)"
    else:
        selected_race_id = race_options[race_options['label'] == selected_option]['race_id'].values[0]
        df_race = df_all[df_all['race_id'] == selected_race_id].copy()
        chart_title = f"Time distribution ({selected_option})"

    col1, col2 = st.columns(2)
    with col1:
        gender_options = sorted(df_race['gender'].unique().astype(str))
        gender_filter = st.multiselect("Filter by gender:", options=gender_options, default=gender_options)
    with col2:
        age_options = sorted(df_race['age_group'].unique().astype(str))
        age_filter = st.multiselect("Filter by age group:", options=age_options, default=age_options)

    df_filtered = df_race[
        (df_race['gender'].isin(gender_filter)) & 
        (df_race['age_group'].isin(age_filter))
    ]

    st.markdown("---")

    if not df_filtered.empty:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Participants", len(df_filtered))
        c2.metric("Record time", format_time(df_filtered['total_seconds'].min()))
        c3.metric("Average", format_time(df_filtered['total_seconds'].mean()))
        c4.metric("Worst time", format_time(df_filtered['total_seconds'].max()))

        st.subheader("Time distribution")
        fig = px.histogram(
            df_filtered, 
            x="minutes", 
            nbins=30, 
            title="How many people finished in X minutes?",
            labels={"minutes": "Minutes"},
            color_discrete_sequence=["#ff4b4b"]
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No data found for selected filters.")

elif view_mode == "Runner Analysis":
    st.title("👤 Runner Analysis")

    search_query = st.text_input("Search runner by name:", placeholder="Type name and press Enter")
    selected_runner = None

    if search_query:
        mask = df_all['runner_name'].str.upper().str.startswith(search_query.upper())
        filtered_runners = sorted(df_all[mask]['runner_name'].unique())[:10]

        if len(filtered_runners) > 0:
            selected_runner = st.selectbox(
                f'Results for "{search_query}"', 
                options=filtered_runners,
                index=None,
                placeholder="Click to select runner...")
        else:
            st.warning("No runners found with that name.")
    else:
        st.info("Please type a name to start searching.")

    if selected_runner:
        st.divider()

        runner_history = df_all[df_all['runner_name'] == selected_runner].copy()

        st.subheader(f"{selected_runner.split(' ')[0]}'s history")
        
        history_data = []
        
        for index, row in runner_history.iterrows():
            race_participants = df_all[df_all['race_id'] == row['race_id']]
            
            race_participants = race_participants.sort_values('total_seconds').reset_index(drop=True)
            try:
                position = race_participants[race_participants['runner_name'] == selected_runner].index[0] + 1
            except:
                position = -1
            
            total_runners = len(race_participants)
            
            dist_km = extract_distance(row['distance'])
            if dist_km and dist_km > 0:
                pace_min_km = row['minutes'] / dist_km
                pace_str = f"{pace_min_km:.2f} min/km"
            else:
                pace_str = "N/A"

            history_data.append({
                "Edition": f"{row['location']} ({row['year']})",
                "Time": format_time(row['total_seconds']),
                "Position": f"{position} / {total_runners}",
                "Pace": pace_str,
                "race_id": row['race_id'],
                "my_time_min": row['minutes']
            })

        df_display = pd.DataFrame(history_data)
        st.dataframe(
            df_display[['Edition', 'Time', 'Position', 'Pace']], 
            use_container_width=True,
            hide_index=True
        )

        st.markdown("---")
        st.subheader("Visual comparison")
        
        selected_race_comp = st.selectbox(
            "Select a race to see in which place the runner has finished:", 
            options=history_data, 
            format_func=lambda x: x['Edition']
        )

        if selected_race_comp:
            race_id_comp = selected_race_comp['race_id']
            race_data = df_all[df_all['race_id'] == race_id_comp]
            
            my_time = selected_race_comp['my_time_min']

            fig2 = px.histogram(
                race_data, 
                x="minutes", 
                nbins=40, 
                title=f"Position in '{selected_race_comp['Edition']}'",
                color_discrete_sequence=['lightgray'], 
                opacity=0.6
            )

            fig2.add_vline(x=my_time, line_width=3, line_dash="dash", line_color="red")
            
            # Mejoras visuales en el gráfico
            fig2.update_layout(
                showlegend=False,
                plot_bgcolor="white",
                margin=dict(t=50, l=0, r=0, b=0)
            )

            st.plotly_chart(fig2, use_container_width=True)