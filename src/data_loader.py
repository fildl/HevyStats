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
        self.routines_data = None

    def load_all(self):
        """Loads all necessary data files."""
        self.load_exercise_database(self.data_dir / 'exercise_database.json')
        self.load_workout_data(self.data_dir / 'workout_data.csv')
        # Optional files - fail gracefully or warn if missing, but for now we expect them
        self.load_bodyweight_data(self.data_dir / 'bodyweight_data.csv')
        self.load_body_composition_phases(self.data_dir / 'body_composition_phases.csv')
        self.load_gym_data(self.data_dir / 'gyms.csv')
        self.load_routine_data(self.data_dir / 'routine.csv')
        
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

    def load_routine_data(self, csv_path):
        if csv_path.exists():
            self.routines_data = pd.read_csv(csv_path)
            # Strip whitespace from column names
            self.routines_data.columns = self.routines_data.columns.str.strip()
            
            self.routines_data['date'] = pd.to_datetime(self.routines_data['date'])
            self.routines_data = self.routines_data.sort_values('date')

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
        self.workout_data['gym_dependent'] = self.workout_data['exercise_title'].apply(
            lambda x: get_meta(x, 'gym_dependent', False)
        )

        # Gym Mapping
        if self.gym_data is not None and not self.gym_data.empty:
            # Sort for safety though loading sorts it
            self.gym_data = self.gym_data.sort_values('date')
            
            def get_gym(dt):
                # dt is the workout timestamp
                # We find the latest gym entry where date <= dt
                candidates = self.gym_data[self.gym_data['date'] <= dt]
                if candidates.empty:
                    return 'Unknown'
                return candidates.iloc[-1]['gym']
            
            self.workout_data['gym'] = self.workout_data['start_time'].apply(get_gym)
        else:
            self.workout_data['gym'] = 'Unknown'

        # Routine Mapping (similar logic to Gym Mapping)
        if self.routines_data is not None and not self.routines_data.empty:
            self.routines_data = self.routines_data.sort_values('date')
            
            def get_routine_info(dt):
                # dt is the workout timestamp
                candidates = self.routines_data[self.routines_data['date'] <= dt]
                if candidates.empty:
                    # Before first routine or no routine data
                    return None
                
                # Get the last matching routine (current one)
                current_routine = candidates.iloc[-1]
                
                # Determine display label
                label = current_routine['routine_label'] if pd.notna(current_routine.get('routine_label')) and str(current_routine.get('routine_label')).strip() != '' else str(current_routine['routine_id'])
                
                return {
                    'routine_id': current_routine['routine_id'],
                    'routine_label': current_routine.get('routine_label'), # Keep raw label too
                    'display_label': label,
                    'start_date': current_routine['date']
                }

            # We can't easily vectorise returning a dict, so we might need a couple of applies or just one that returns the ID/Label, 
            # but we need the date range for the UI filter.
            # Let's assign the routine_id mainly, and we can look up details later or put them in columns.
            
            # Actually, let's just create a 'routine_display' column for easy filtering
            # But the user wants the filter to show the date range too.
            # So best is to have a column 'routine_key' that links to the routine entry, or just put the full string.
            
            # Let's iterate to build a list of results to assign
            routine_displays_list = []
            
            # Pre-calculate routine display strings to avoid doing it per row if possible, 
            # but mapping per row is easier logic.
            
            # Optimisation: `searchsorted` style lookup
            # But let's stick to apply for simplicity given dataset size is small.
            
            def get_fmt_routine(dt):
                cand = self.routines_data[self.routines_data['date'] <= dt]
                if cand.empty:
                    return "Unknown"
                
                curr = cand.iloc[-1]
                
                # Find end date (next routine start date)
                next_routines = self.routines_data[self.routines_data['date'] > curr['date']]
                if next_routines.empty:
                    end_date = "Present"
                else:
                    # End date is day before next routine? Or just next routine date? 
                    # Usually "Until X"
                    end_str = next_routines.iloc[0]['date'].strftime('%Y-%m-%d')
                    end_date = end_str
                
                start_str = curr['date'].strftime('%Y-%m-%d')
                
                label = curr['routine_label'] if pd.notna(curr.get('routine_label')) and str(curr.get('routine_label')).strip() != '' else str(curr['routine_id'])
                
                return f"{label} ({start_str} - {end_date})"

            self.workout_data['routine_name'] = self.workout_data['start_time'].apply(get_fmt_routine)

        else:
            self.workout_data['routine_name'] = 'Unknown'


        # 4. Volume Calculation
        self.workout_data['workout_date'] = self.workout_data['start_time'].dt.date
        self.workout_data['volume'] = 0.0

        # Create masks for different calculation types
        double_weight_mask = self.workout_data['weight_type'] == 'double_weight'
        assisted_mask = self.workout_data['weight_type'] == 'assisted'
        bodyweight_mask = self.workout_data['weight_type'] == 'bodyweight'
        weighted_bodyweight_mask = self.workout_data['weight_type'] == 'weighted_bodyweight'
        
        # Standard: Anything NOT special. (weighted, unknown, etc.)
        standard_mask = (~double_weight_mask) & (~assisted_mask) & (~bodyweight_mask) & (~weighted_bodyweight_mask)

        # A. Standard: Weight * Reps
        self.workout_data.loc[standard_mask, 'volume'] = (
            self.workout_data.loc[standard_mask, 'weight_kg'].fillna(0) * 
            self.workout_data.loc[standard_mask, 'reps']
        )

        # B. Double Weight (Dumbbells): Weight * 2 * Reps
        self.workout_data.loc[double_weight_mask, 'volume'] = (
            self.workout_data.loc[double_weight_mask, 'weight_kg'].fillna(0) * 2 * 
            self.workout_data.loc[double_weight_mask, 'reps']
        )

        # C. Iterative calculations for Bodyweight dependent types
        # (Assisted, Bodyweight, Weighted Bodyweight)
        if assisted_mask.any() or bodyweight_mask.any() or weighted_bodyweight_mask.any():
            
            # Combine masks to iterate efficiently
            bw_dependent_mask = assisted_mask | bodyweight_mask | weighted_bodyweight_mask
            
            for idx, row in self.workout_data[bw_dependent_mask].iterrows():
                bw = self.get_bodyweight_for_date(pd.Timestamp(row['workout_date']))
                weight = row['weight_kg'] if pd.notna(row['weight_kg']) else 0.0
                reps = row['reps'] if pd.notna(row['reps']) else 0
                w_type = row['weight_type']
                
                vol = 0.0
                if w_type == 'assisted':
                    vol = (bw - weight) * reps
                elif w_type == 'bodyweight':
                    vol = bw * reps
                elif w_type == 'weighted_bodyweight':
                    vol = (bw + weight) * reps
                
                self.workout_data.loc[idx, 'volume'] = vol
        
        self.workout_data['volume'] = self.workout_data['volume'].fillna(0)
