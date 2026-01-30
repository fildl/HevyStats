# HevyStats

**HevyStats** is a personal analytics dashboard for [Hevy](https://hevy.com/) workout data. It converts your export data into actionable insights, focusing on training consistency, volume progression, and muscle balance.

## Key Features

### 📊 Dashboard & KPIs
- **Smart KPIs**: Tracks Total Volume, Workouts, Total Sets, Reps, and Training Duration.
- **🔥Dynamic Streak Tracking**: 
    - Shows **Weekly Streak** for active periods.
    - Shows **Max Streak** for historical splits or past years.

### 📅 Consistency & Trends
- **Workout Consistency Heatmap**: An heatmap displaying daily activity (intensity based on Set Count).
- **Bodyweight & Phases Overlay**: Correlates training volume with bodyweight trends and bulking/cutting phases.

### 🕸️ Muscle Balance Strategy
- **Radar Chart Analysis**: Replaces traditional pie charts to show set distribution across muscle groups.
- **Historical Comparison**: Compares your current routine's focus against your historical average or previous routine.

### 📈 Deep Dive Analysis
- **Exercise Analysis**: Drill down into specific exercises with "Volume Progression" charts.
    - Gym-dependent tracking for machine exercises.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/fildl/HevyStats.git
    cd HevyStats
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

1.  **Data Preparation**:
    - Export your data from Hevy (`workouts.csv`) and place it in the `data/` folder.
    - Maintain `exercise_database.json` for mapping exercises to muscle groups.

2.  **Run the Dashboard**:
    ```bash
    streamlit run app.py
    ```

## License

This project is licensed under the MIT License.
