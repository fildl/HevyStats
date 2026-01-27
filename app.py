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

# Charts
# Charts
st.subheader("Training Volume History")
fig_vol = viz.create_monthly_volume_chart(year=filter_year)
if fig_vol:
    st.plotly_chart(fig_vol, use_container_width=True)
else:
    st.info("No data available for chart.")

st.divider()

st.subheader("Muscle Balance")
fig_pie = viz.create_muscle_group_distribution(year=filter_year)
if fig_pie:
    st.plotly_chart(fig_pie, use_container_width=True)



