import streamlit as st
import pandas as pd
import datetime
from src.data_loader import HevyDataLoader
from src.visualizations import WorkoutVisualizer
from src.const import GROUP_MAPPING

# Page Config
st.set_page_config(page_title="HevyStats", page_icon="🏋️‍♂️", layout="wide")

@st.cache_data
def load_data():
    loader = HevyDataLoader()
    try:
        loader.load_all()
        return loader
    except Exception as e:
        return None

loader = load_data()

if not loader or loader.workout_data is None:
    st.error("Failed to load data. Please check `data/` folder.")
    st.stop()

df = loader.workout_data
bw_df = loader.bodyweight_data
phases_df = loader.phases_data

# Sidebar
st.sidebar.title("HevyStats")
st.sidebar.markdown("Advanced analytics for your Hevy workouts.")

# Filters
available_years = sorted(df['start_time'].dt.year.unique(), reverse=True)
selected_year = st.sidebar.selectbox("Select Year", ["All Time"] + available_years)

filter_year = None if selected_year == "All Time" else selected_year

# Filter dataset for calculations
if filter_year:
    filtered_df = df[df['start_time'].dt.year == filter_year].copy()
else:
    filtered_df = df.copy()

# Visualizer
viz = WorkoutVisualizer(filtered_df, bw_df, phases_df)

# Main Dashboard
st.title("Dashboard")

# KPI Row
col1, col2, col3, col4, col5, col6 = st.columns(6)
total_vol = filtered_df['volume'].sum() / 1000 # tonnes
total_workouts = filtered_df['start_time'].dt.date.nunique()
total_sets = len(filtered_df)
total_reps = int(filtered_df['reps'].sum())

# Calculate Duration
# We use start_time to identify unique workouts and calculate duration for each
unique_workouts = filtered_df[['start_time', 'end_time']].drop_duplicates()
total_seconds = (unique_workouts['end_time'] - unique_workouts['start_time']).dt.total_seconds().sum()
total_hours = total_seconds / 3600

avg_sets_workout = total_sets / total_workouts if total_workouts > 0 else 0

col1.metric("Total Volume", f"{total_vol:.1f} t")
col2.metric("Workouts", total_workouts)
col3.metric("Hours", f"{total_hours:.1f} h")
col4.metric("Total Sets", f"{total_sets}")
col5.metric("Total Reps", f"{total_reps}")
col6.metric("Avg Sets/Workout", f"{avg_sets_workout:.1f}")

st.divider()

# Check for unknown exercises
unknown_exercises = filtered_df[filtered_df['muscle_group'] == 'unknown']['exercise_title'].unique()
if len(unknown_exercises) > 0:
    st.warning(
        f"⚠️ Found {len(unknown_exercises)} exercises with unknown muscle group: "
        f"{', '.join(unknown_exercises)}. Please update `exercise_database.json`."
    )

# Charts
st.subheader("Training Volume History")

# Metric Selection
metric = st.radio(
    "Metric", 
    ["Total Volume", "Avg Volume per Workout"], 
    horizontal=True,
    label_visibility="collapsed"
)

# Define tabs: Overall + specific major groups that have sub-muscles
tabs = st.tabs(["Overall", "Arms", "Legs", "Back", "Chest", "Shoulders", "Core"])

def get_chart(viz_obj, metric_name, year, group=None):
    if metric_name == "Total Volume":
        if group:
            return viz_obj.create_monthly_specific_muscle_chart(year, filter_group=group)
        else:
            return viz_obj.create_monthly_volume_chart(year)
    else:
        # Avg per Workout
        return viz_obj.create_monthly_volume_per_workout_chart(year, filter_group=group)

with tabs[0]: # Overall
    fig_vol = get_chart(viz, metric, filter_year)
    if fig_vol:
        st.plotly_chart(fig_vol, use_container_width=True)
    else:
        st.info("No data available.")

# Helper to render specific group tabs
def render_group_tab(tab_idx, group_name):
    with tabs[tab_idx]:
        fig = get_chart(viz, metric, filter_year, group=group_name)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(f"No data available for {group_name}.")

# Specific Groups
render_group_tab(1, 'arms')
render_group_tab(2, 'legs')
render_group_tab(3, 'back')
render_group_tab(4, 'chest')
render_group_tab(5, 'shoulders')
render_group_tab(6, 'core')



st.divider()

# Exercise Progression Analysis
st.subheader("Exercise Analysis 📈")

# Get list of Top 50 exercises by frequency (to avoid clutter)
# Ensure we define filtered_df or use the one from state? filtered_df is defined in app.py's flow
# In app.py line 48: filtered_df = df.copy() (with year filter)
# Re-filter for unique exercises available in the selected year
top_exercises = filtered_df['exercise_title'].value_counts().head(50).index.tolist()
selected_exercise = st.selectbox("Select Exercise", top_exercises)

if selected_exercise:
    fig_prog = viz.create_exercise_progression_chart(selected_exercise)
    if fig_prog:
        st.plotly_chart(fig_prog, use_container_width=True)
    else:
        st.info("No data for this exercise in the selected period.")

st.divider()

st.subheader("Muscle Balance")
fig_pie = viz.create_muscle_group_distribution(year=filter_year)
if fig_pie:
    st.plotly_chart(fig_pie, use_container_width=True)



