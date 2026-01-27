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

# Routine Filter
# Get unique routines sorted by most recent first
# We group by routine_name and take the min start_time to find the routine's start, then sort descending
routine_order = df.groupby('routine_name')['start_time'].min().sort_values(ascending=False).index.tolist()
available_routines = ["All Splits"] + routine_order

# Default index logic: Select the most recent split (index 1) if available
default_idx = 1 if len(available_routines) > 1 else 0
selected_routine = st.sidebar.selectbox("Select Split", available_routines, index=default_idx)

filter_year = None if selected_year == "All Time" else selected_year
filter_routine = None if selected_routine == "All Splits" else selected_routine

# Filter dataset for calculations
# Start with full dataset
filtered_df = df.copy()

# Apply Year Filter
if filter_year:
    filtered_df = filtered_df[filtered_df['start_time'].dt.year == filter_year]

# Apply Routine Filter
if filter_routine:
    filtered_df = filtered_df[filtered_df['routine_name'] == filter_routine] 


# Visualizer
viz = WorkoutVisualizer(filtered_df, bw_df, phases_df)

# Main Dashboard
st.title("Hevy Stats")

# Show active filters
active_filters = []
if filter_year:
    active_filters.append(f"**Year:** {filter_year}")
if filter_routine:
    active_filters.append(f"**Split:** {filter_routine}")

if active_filters:
    st.markdown(f"#### {' • '.join(active_filters)}")

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

st.subheader("Muscle Balance")
fig_pie = viz.create_muscle_group_distribution(year=filter_year)
if fig_pie:
    st.plotly_chart(fig_pie, use_container_width=True)

st.divider()

# Exercise Progression Analysis
st.subheader("Exercise Analysis 📈")

# Filter exercises: Must have at least 12 sessions in the selected period
# We first get valid exercises, then enrich with muscle group for hierarchical selection
ex_counts = filtered_df.groupby('exercise_title')['start_time'].nunique()
valid_exercises_list = ex_counts[ex_counts >= 12].index.tolist()

if not valid_exercises_list:
    st.info("No exercises found with at least 12 sessions in this period.")
    selected_exercise = None
else:
    # Create a subset DF for valid exercises
    valid_df = filtered_df[filtered_df['exercise_title'].isin(valid_exercises_list)][['exercise_title', 'muscle_group']].drop_duplicates()
    
    # 1. Select Group (Use specific muscle group directly)
    available_groups = sorted(valid_df['muscle_group'].unique())
    selected_group = st.selectbox("Select Muscle Group", available_groups)
    
    # 2. Select Exercise (Filtered by Group)
    exercises_in_group = valid_df[valid_df['muscle_group'] == selected_group]['exercise_title'].sort_values().tolist()
    
    # Initialize or Validate Session State for Navigation
    if 'selected_exercise_nav' not in st.session_state:
        st.session_state.selected_exercise_nav = exercises_in_group[0]
    elif st.session_state.selected_exercise_nav not in exercises_in_group:
        # If group changed or filtered list changed, reset to first item
        st.session_state.selected_exercise_nav = exercises_in_group[0]
        
    # Navigation Callbacks
    def prev_ex():
        current = st.session_state.selected_exercise_nav
        if current in exercises_in_group:
            curr_idx = exercises_in_group.index(current)
            new_idx = (curr_idx - 1) % len(exercises_in_group)
            st.session_state.selected_exercise_nav = exercises_in_group[new_idx]
            
    def next_ex():
        current = st.session_state.selected_exercise_nav
        if current in exercises_in_group:
            curr_idx = exercises_in_group.index(current)
            new_idx = (curr_idx + 1) % len(exercises_in_group)
            st.session_state.selected_exercise_nav = exercises_in_group[new_idx]

    # Layout: [ < ] [ Selectbox ] [ > ]
    c1, c2, c3 = st.columns([1, 10, 1])
    with c1:
        st.write("") # Spacer to align with label? 
        st.write("") 
        st.button("⬅️", on_click=prev_ex, help="Previous Exercise")
    with c2:
        selected_exercise = st.selectbox("Select Exercise", exercises_in_group, key='selected_exercise_nav')
    with c3:
        st.write("") 
        st.write("") 
        st.button("➡️", on_click=next_ex, help="Next Exercise")

if selected_exercise:
    fig_prog = viz.create_exercise_progression_chart(selected_exercise)
    if fig_prog:
        st.plotly_chart(fig_prog, use_container_width=True)
    else:
        st.info("No data for this exercise in the selected period.")



