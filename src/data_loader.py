import pandas as pd
import json
from pathlib import Path

class HevyDataLoader:
    def __init__(self, data_dir='data'):
        self.data_dir = Path(data_dir)
        self.workout_data = None
        self.exercise_database = None
        self.excluded_exercises = None
        self.bodyweight_data = None
        self.phases_data = None
        self.gym_data = None

    def load_all(self):
        """Loads all necessary data files."""
        self.load_exercise_database(self.data_dir / 'exercise_database.json')
        self.load_workout_data(self.data_dir / 'workout_data.csv')
        # Optional files - fail gracefully or warn if missing, but for now we expect them
        self.load_bodyweight_data(self.data_dir / 'bodyweight_data.csv')
        self.load_body_composition_phases(self.data_dir / 'body_composition_phases.csv')
        self.load_gym_data(self.data_dir / 'gyms.csv')
        
        self.process_data()

    def load_workout_data(self, csv_path):
        if not csv_path.exists():
            raise FileNotFoundError(f"Workout data not found at {csv_path}")
            
        self.workout_data = pd.read_csv(csv_path)
        
        # Convert datetime columns
        # Hevy export format: "10 Oct 2023, 12:00"
        self.workout_data['start_time'] = pd.to_datetime(self.workout_data['start_time'], format='%d %b %Y, %H:%M')
        self.workout_data['end_time'] = pd.to_datetime(self.workout_data['end_time'], format='%d %b %Y, %H:%M')
        
        # Clean numeric columns
        numeric_columns = ['weight_kg', 'reps', 'distance_km', 'duration_seconds', 'rpe']
        for col in numeric_columns:
            if col in self.workout_data.columns:
                self.workout_data[col] = pd.to_numeric(self.workout_data[col], errors='coerce')

    def load_exercise_database(self, json_path):
        if not json_path.exists():
            print(f"Warning: Exercise database not found at {json_path}")
            self.exercise_database = {}
            self.excluded_exercises = set()
            return

        with open(json_path, 'r') as f:
            data = json.load(f)
        
        self.exercise_database = data.get('exercises', {})
        self.excluded_exercises = set(data.get('excluded_exercises', []))

    def load_bodyweight_data(self, csv_path):
        if csv_path.exists():
            self.bodyweight_data = pd.read_csv(csv_path)
            self.bodyweight_data['date'] = pd.to_datetime(self.bodyweight_data['date'])

    def load_body_composition_phases(self, csv_path):
        if csv_path.exists():
            self.phases_data = pd.read_csv(csv_path)
            self.phases_data['date'] = pd.to_datetime(self.phases_data['date'])
            self.phases_data = self.phases_data.sort_values('date')

    def load_gym_data(self, csv_path):
        if csv_path.exists():
            self.gym_data = pd.read_csv(csv_path)
            self.gym_data['date'] = pd.to_datetime(self.gym_data['date'])
            self.gym_data = self.gym_data.sort_values('date')

    def get_bodyweight_for_date(self, workout_date):
        """Get bodyweight for a given workout date (uses most recent available)"""
        if self.bodyweight_data is None:
            return 70.0  # Default bodyweight
        
        valid_entries = self.bodyweight_data[self.bodyweight_data['date'] <= workout_date]
        if valid_entries.empty:
            return self.bodyweight_data.iloc[0]['weight_kg'] if not self.bodyweight_data.empty else 70.0
        
        return valid_entries.iloc[-1]['weight_kg']

    def process_data(self):
        """Clean and calculate derived metrics like Volume."""
        if self.workout_data is None:
            return

        # 1. Filter excluded exercises
        if self.excluded_exercises:
            self.workout_data = self.workout_data[
                ~self.workout_data['exercise_title'].isin(self.excluded_exercises)
            ].copy()

        # 2. Filter warmup sets
        if 'set_type' in self.workout_data.columns:
            self.workout_data = self.workout_data[
                self.workout_data['set_type'] != 'warmup'
            ].copy()

        # 3. Enrich with Exercise Database Metadata
        def get_meta(exercise, field, default):
            return self.exercise_database.get(exercise, {}).get(field, default)

        self.workout_data['muscle_group'] = self.workout_data['exercise_title'].apply(
            lambda x: get_meta(x, 'muscle_group', 'unknown')
        )
        self.workout_data['weight_type'] = self.workout_data['exercise_title'].apply(
            lambda x: get_meta(x, 'weight_type', 'unknown')
        )

        # 4. Volume Calculation
        self.workout_data['workout_date'] = self.workout_data['start_time'].dt.date
        self.workout_data['volume'] = 0.0

        # Create masks for different calculation types
        double_weight_mask = self.workout_data['weight_type'] == 'double_weight'
        assisted_mask = self.workout_data['weight_type'] == 'assisted'
        # Standard is anything that is NOT double_weight AND NOT assisted (and is not None/Nan)
        standard_mask = (~double_weight_mask) & (~assisted_mask)

        # A. Standard: Weight * Reps
        self.workout_data.loc[standard_mask, 'volume'] = (
            self.workout_data.loc[standard_mask, 'weight_kg'] * 
            self.workout_data.loc[standard_mask, 'reps']
        )

        # B. Double Weight (Dumbbells): Weight * 2 * Reps
        self.workout_data.loc[double_weight_mask, 'volume'] = (
            self.workout_data.loc[double_weight_mask, 'weight_kg'] * 2 * 
            self.workout_data.loc[double_weight_mask, 'reps']
        )

        # C. Assisted: (Bodyweight - Weight) * Reps
        # This is iterative because it depends on the date for bodyweight
        # Optimization: Group by date? For now, iterative is safe and clear enough for this scale.
        if assisted_mask.any():
            # Create a lookup series map for Bodyweights to avoid N lookups
            # Or just iterate the assisted rows
            for idx, row in self.workout_data[assisted_mask].iterrows():
                bw = self.get_bodyweight_for_date(pd.Timestamp(row['workout_date']))
                assist_weight = row['weight_kg']
                reps = row['reps']
                if pd.notna(assist_weight) and pd.notna(reps):
                    effective_weight = bw - assist_weight
                    self.workout_data.loc[idx, 'volume'] = effective_weight * reps
        
        self.workout_data['volume'] = self.workout_data['volume'].fillna(0)
