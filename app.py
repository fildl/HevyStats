import streamlit as st
import pandas as pd
import datetime
from src.data_loader import HevyDataLoader
from src.visualizations import WorkoutVisualizer
from src.const import GROUP_MAPPING

def calculate_current_streak(df):
    if df is None or df.empty:
        return 0
    
    current_date = datetime.date.today()
    current_year, current_week, _ = current_date.isocalendar()
    
    # Get unique (year, week) pairs from data
    # We use a set for O(1) lookups during traversal, but we need sorted list for gap check
    iso = df['start_time'].dt.isocalendar()
    # Create valid (year, week) tuples unique
    unique_weeks = sorted(list(set(zip(iso.year, iso.week))), reverse=True)
    
    if not unique_weeks:
        return 0
    
    last_year, last_week = unique_weeks[0]
    
    # Helper to calc week difference
    def weeks_diff(y1, w1, y2, w2):
        d1 = datetime.datetime.fromisocalendar(y1, w1, 1)
        d2 = datetime.datetime.fromisocalendar(y2, w2, 1)
        return abs((d1 - d2).days) // 7
        
    diff_from_now = weeks_diff(current_year, current_week, last_year, last_week)
    
    # If the last workout was > 1 week ago (i.e. 2+ weeks gap), streak is 0
    # Note: If diff is 0 (this week) or 1 (last week), streak is active.
    if diff_from_now > 1:
        return 0
        
    streak = 1
    curr_y, curr_w = last_year, last_week
    
    # Iterate backwards to find consecutive weeks
    for i in range(1, len(unique_weeks)):
        prev_y, prev_w = unique_weeks[i]
        if weeks_diff(curr_y, curr_w, prev_y, prev_w) == 1:
            streak += 1
            curr_y, curr_w = prev_y, prev_w
        else:
            break
            
    return streak

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

# Calculate Streak (using full original dataframe to ignore filters)
streak = calculate_current_streak(df)

# Main Dashboard
# Main Dashboard
# st.title("Hevy Stats")
st.markdown("""
<style>
@keyframes gradient {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}
.header {
    background: linear-gradient(-45deg, #ee7752, #e73c7e, #23a6d5, #23d5ab);
    background-size: 400% 400%;
    animation: gradient 15s ease infinite;
    padding: 30px;
    border-radius: 15px;
    text-align: center;
    color: white;
    margin-bottom: 30px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.2);
}
.header h1 {
    margin: 0;
    font-size: 3.5rem;
    font-weight: 700;
    color: white;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    font-family: sans-serif;
}
.header p {
    font-size: 1.2rem;
    opacity: 0.9;
    margin-top: 5px;
}
</style>
<div class="header">
    <h1>Hevy Stats</h1>
</div>
""", unsafe_allow_html=True)


# Show active filters
active_filters = []
if filter_year:
    active_filters.append(f"**Year:** {filter_year}")
if filter_routine:
    active_filters.append(f"**Split:** {filter_routine}")

if active_filters:
    st.markdown(f"#### {' • '.join(active_filters)}")

# Metric Calculations
total_vol = filtered_df['volume'].sum() / 1000 # tonnes
total_workouts = filtered_df['start_time'].dt.date.nunique()
total_sets = len(filtered_df)
total_reps = int(filtered_df['reps'].sum())

# Calculate Duration
unique_workouts = filtered_df[['start_time', 'end_time']].drop_duplicates()
total_seconds = (unique_workouts['end_time'] - unique_workouts['start_time']).dt.total_seconds().sum()
total_hours = total_seconds / 3600

avg_sets_workout = total_sets / total_workouts if total_workouts > 0 else 0
avg_duration_mins = (total_seconds / 60) / total_workouts if total_workouts > 0 else 0

# KPI Row 1
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Volume", f"{total_vol:.1f} t")
col2.metric("Workouts", total_workouts)
col3.metric("Hours", f"{total_hours:.1f} h")
col4.metric("Total Sets", f"{total_sets}")

# KPI Row 2
col5, col6, col7, col8 = st.columns(4)
col5.metric("Total Reps", f"{total_reps}")
col6.metric("Avg Sets/Workout", f"{avg_sets_workout:.1f}")
col7.metric("Avg Duration", f"{avg_duration_mins:.0f} min")
col8.metric("Weekly Streak", f"{streak} 🔥")

# Check for unknown exercises
unknown_exercises = filtered_df[filtered_df['muscle_group'] == 'unknown']['exercise_title'].unique()
if len(unknown_exercises) > 0:
    st.warning(
        f"⚠️ Found {len(unknown_exercises)} exercises with unknown muscle group: "
        f"{', '.join(unknown_exercises)}. Please update `exercise_database.json`."
    )

st.divider()

# Consistency Heatmap
heatmap_title = f"Workout Consistency ({filter_routine if filter_routine else 'All Splits'})"
st.subheader(heatmap_title)
fig_heatmap = viz.create_consistency_heatmap(year=filter_year)
if fig_heatmap:
    st.plotly_chart(fig_heatmap, use_container_width=True)
else:
    st.info("No data available for consistency heatmap.")

st.divider()

# Charts
st.subheader("Training Volume History")

# Metric Selection
metric = st.radio(
    "Metric", 
    ["Avg Volume per Workout", "Total Volume"], 
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

# Filter exercises: Must have at least a dynamic number of sessions
# Logic: approx once every 2 weeks, min 2, max 10
if filtered_df.empty:
    days_range = 0
else:
    days_range = (filtered_df['start_time'].max() - filtered_df['start_time'].min()).days

# Calculate threshold: 1 session per 14 days, min 2, capped at 10
calculated_threshold = max(2, int(days_range // 14))
min_sessions = min(10, calculated_threshold)

# We first get valid exercises, then enrich with muscle group for hierarchical selection
ex_counts = filtered_df.groupby('exercise_title')['start_time'].nunique()
valid_exercises_list = ex_counts[ex_counts >= min_sessions].index.tolist()

if not valid_exercises_list:
    st.info(f"No exercises found with at least {min_sessions} sessions in this period.")
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



