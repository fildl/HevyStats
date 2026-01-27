# HevyStats 🏋️‍♂️

**HevyStats** is a personal analytics dashboard for your [Hevy](https://hevy.com/) workout data. It provides deep insights into your training volume, muscle balance, and progress over time, going beyond the standard analytics.

## Features (Planned)

- 📊 **Interactive Dashboard**: Built with Streamlit and Plotly.
- 📉 **Volume Analysis**: Tracks volume (kg * reps) handling:
    - Standard weights
    - Dumbbells (2x weight)
    - Assisted exercises (Bodyweight - Assistance)
- 💪 **Muscle Group Breakdown**: Visualizes training balance across major muscle groups.
- ⚖️ **Contextual Analysis**: Correlates training volume with body weight and bulking/cutting phases.

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

1.  **Prepare Data**:
    - Export your data from the Hevy app as a CSV.
    - Place `workout_data.csv` in the `data/` directory.
    - Ensure `exercise_database.json` and other auxiliary files are present in `data/`.

2.  **Run the App**:
    ```bash
    streamlit run app.py
    ```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
