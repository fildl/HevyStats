from src.data_loader import HevyDataLoader
import pandas as pd

def verify():
    print("Initializing HevyDataLoader...")
    loader = HevyDataLoader()
    
    print("Loading data...")
    try:
        loader.load_all()
    except Exception as e:
        print(f"FAILED to load data: {e}")
        return

    df = loader.workout_data
    
    if df is None or df.empty:
        print("FAILED: DataFrame is empty!")
        return

    print("\n--- Data Summary ---")
    print(f"Total Entries: {len(df)}")
    print(f"Date Range: {df['start_time'].min()} to {df['start_time'].max()}")
    print(f"Total Volume (kg): {df['volume'].sum():,.2f}")
    
    print("\n--- Exercise Types Verification ---")
    
    # Check if we have mapped exercises
    unknown_muscles = df[df['muscle_group'] == 'unknown']['exercise_title'].unique()
    if len(unknown_muscles) > 0:
        print(f"WARNING: {len(unknown_muscles)} exercises have 'unknown' muscle group.")
        print(f"Sample: {unknown_muscles[:5]}")
    else:
        print("SUCCESS: All exercises mapped to a muscle group.")

    # Verify Double Weight (e.g. Dumbbells)
    double_weight_rows = df[df['weight_type'] == 'double_weight']
    if not double_weight_rows.empty:
        row = double_weight_rows.iloc[0]
        expected_vol = row['weight_kg'] * 2 * row['reps']
        print(f"Check Double Weight '{row['exercise_title']}':")
        print(f"  Weight: {row['weight_kg']}, Reps: {row['reps']}")
        print(f"  Calculated Volume: {row['volume']}, Expected: {expected_vol}")
        assert abs(row['volume'] - expected_vol) < 0.01, "Double weight calc mismatch!"
        print("  [OK]")
    else:
        print("No 'double_weight' exercises found to test.")

    # Verify Assisted Weight
    assisted_rows = df[df['weight_type'] == 'assisted']
    if not assisted_rows.empty:
        row = assisted_rows.iloc[0]
        # We need the bodyweight used for this calc
        bw = loader.get_bodyweight_for_date(pd.Timestamp(row['workout_date']))
        expected_vol = (bw - row['weight_kg']) * row['reps']
        print(f"Check Assisted '{row['exercise_title']}':")
        print(f"  Bodyweight (est): {bw}, Assist: {row['weight_kg']}, Reps: {row['reps']}")
        print(f"  Calculated Volume: {row['volume']}, Expected: {expected_vol}")
        assert abs(row['volume'] - expected_vol) < 0.01, "Assisted weight calc mismatch!"
        print("  [OK]")
    else:
        print("No 'assisted' exercises found to test.")

if __name__ == "__main__":
    verify()
