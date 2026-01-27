import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from .const import MUSCLE_GROUP_COLORS, PHASE_COLORS, GROUP_MAPPING, MUSCLE_GROUP_ORDER

class WorkoutVisualizer:
    def __init__(self, df, bodyweight_df=None, phase_df=None):
        self.df = df
        self.bodyweight_df = bodyweight_df
        self.phase_df = phase_df

    def create_monthly_volume_chart(self, year=None):
        """
        Creates a stacked bar chart of monthly volume by muscle group.
        Includes a secondary line for monthly average bodyweight.
        """
        plot_data = self.df.copy()
        if year:
            plot_data = plot_data[plot_data['start_time'].dt.year == year]

        if plot_data.empty:
            return None

        # --- 1. Volume Data Preparation ---
        # Align dates to start of month for consistent grouping
        plot_data['month_date'] = plot_data['start_time'].dt.to_period('M').dt.start_time
        plot_data['major_group'] = plot_data['muscle_group'].replace(GROUP_MAPPING)
        
        # Aggregate Volume
        monthly_vol = plot_data.groupby(['month_date', 'major_group'])['volume'].sum().reset_index()
        monthly_vol['volume_k'] = monthly_vol['volume'] / 1000.0

        # --- 2. Create Stacked Bar Chart ---
        fig = px.bar(
            monthly_vol,
            x='month_date',
            y='volume_k',
            color='major_group',
            title='Monthly Training Volume (tonnes) & Bodyweight (kg)',
            color_discrete_map=MUSCLE_GROUP_COLORS,
            category_orders={'major_group': MUSCLE_GROUP_ORDER}
        )

        # --- 3. Bodyweight Overlay (Monthly Average) ---
        if self.bodyweight_df is not None and not self.bodyweight_df.empty:
            # Filter bodyweight data to relevant range
            min_date = plot_data['start_time'].min()
            max_date = plot_data['start_time'].max()
            
            bw_data = self.bodyweight_df[
                (self.bodyweight_df['date'] >= min_date) & 
                (self.bodyweight_df['date'] <= max_date)
            ].copy()

            if not bw_data.empty:
                # Calculate Monthly Average
                bw_data['month_date'] = bw_data['date'].dt.to_period('M').dt.start_time
                monthly_bw = bw_data.groupby('month_date')['weight_kg'].mean().reset_index()
                
                # Add Line Trace
                fig.add_trace(
                    go.Scatter(
                        x=monthly_bw['month_date'],
                        y=monthly_bw['weight_kg'],
                        name='Avg Bodyweight',
                        mode='lines+markers',
                        line=dict(color='white', width=3),
                        marker=dict(size=6, color='white'),
                        yaxis='y2'
                    )
                )

                # Configure Secondary Y-Axis
                fig.update_layout(
                    yaxis2=dict(
                        title='Bodyweight (kg)',
                        overlaying='y',
                        side='right',
                        showgrid=False
                    )
                )

        # --- 4. Final Layout Polish ---
        tick_format = "%b" if year else "%b %Y"
        
        fig.update_layout(
            autosize=True,
            xaxis=dict(
                title=None,
                tickformat=tick_format,
                dtick="M1"  # Force monthly ticks
            ),
            yaxis_title='Volume (x1000 kg)',
            legend_title_text='Muscle Group',
            hovermode='x unified',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )

        return fig

    def create_monthly_specific_muscle_chart(self, year=None, filter_group=None):
        """
        Creates a stacked bar chart of monthly volume by SPECIFIC muscle group.
        (e.g., Biceps, Triceps, Chest, etc. instead of just Arms, Chest)
        
        Args:
            year (int): Filter by year
            filter_group (str): If provided (e.g. 'arms'), only show muscles in this major group.
        """
        plot_data = self.df.copy()
        if year:
            plot_data = plot_data[plot_data['start_time'].dt.year == year]
            
        if filter_group:
            # Filter specifically for muscles matching this major group
            # We need to map each row's muscle_group to check if it belongs to filter_group
            plot_data['mapped_group'] = plot_data['muscle_group'].replace(GROUP_MAPPING)
            plot_data = plot_data[plot_data['mapped_group'] == filter_group]

        if plot_data.empty:
            return None

        # --- 1. Volume Data Preparation ---
        plot_data['month_date'] = plot_data['start_time'].dt.to_period('M').dt.start_time
        
        # Aggregate Volume by specific 'muscle_group'
        monthly_vol = plot_data.groupby(['month_date', 'muscle_group'])['volume'].sum().reset_index()
        monthly_vol['volume_k'] = monthly_vol['volume'] / 1000.0

        # --- 2. Create Stacked Bar Chart ---
        fig = px.bar(
            monthly_vol,
            x='month_date',
            y='volume_k',
            color='muscle_group',
            title='Monthly Volume by Specific Muscle (tonnes)',
            color_discrete_map=MUSCLE_GROUP_COLORS
            # We don't enforce a strict order here as there are many specific muscles,
            # but Plotly usually sorts by value or name.
        )
        
        # --- 3. Bodyweight Overlay (Optional, consistent with main chart) ---
        # Leaving it out for specific muscles to reduce noise, or keeping it?
        # User requested "graph analogous to Training Volume History", so let's keep it consistent.
        if self.bodyweight_df is not None and not self.bodyweight_df.empty:
             min_date = plot_data['start_time'].min()
             max_date = plot_data['start_time'].max()
             bw_data = self.bodyweight_df[
                (self.bodyweight_df['date'] >= min_date) & 
                (self.bodyweight_df['date'] <= max_date)
            ].copy()
             if not bw_data.empty:
                bw_data['month_date'] = bw_data['date'].dt.to_period('M').dt.start_time
                monthly_bw = bw_data.groupby('month_date')['weight_kg'].mean().reset_index()
                fig.add_trace(
                    go.Scatter(
                        x=monthly_bw['month_date'],
                        y=monthly_bw['weight_kg'],
                        name='Avg Bodyweight',
                        mode='lines+markers',
                        line=dict(color='white', width=3),
                        marker=dict(size=6, color='white'),
                        yaxis='y2'
                    )
                )
                fig.update_layout(
                    yaxis2=dict(
                        title='Bodyweight (kg)',
                        overlaying='y',
                        side='right',
                        showgrid=False
                    )
                )

        # --- 4. Final Layout ---
        tick_format = "%b" if year else "%b %Y"
        fig.update_layout(
            autosize=True,
            xaxis=dict(
                title=None,
                tickformat=tick_format,
                dtick="M1"
            ),
            yaxis_title='Volume (x1000 kg)',
            legend_title_text='Specific Muscle',
            hovermode='x unified',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )

        return fig

    def create_monthly_volume_per_workout_chart(self, year=None, filter_group=None):
        """
        Creates a stacked bar chart of monthly volume per workout (Intensity).
        (Total Volume / Number of Workouts in that month)
        """
        plot_data = self.df.copy()
        if year:
            plot_data = plot_data[plot_data['start_time'].dt.year == year]

        if filter_group:
            plot_data['mapped_group'] = plot_data['muscle_group'].replace(GROUP_MAPPING)
            plot_data = plot_data[plot_data['mapped_group'] == filter_group]
        
        if plot_data.empty:
            return None

        # --- 1. Data Prep ---
        plot_data['month_date'] = plot_data['start_time'].dt.to_period('M').dt.start_time
        
        # Calculate Workouts per Month (denominator)
        # We count unique workout dates per month from the ORIGINAL filtered dataframe (before muscle grouping?)
        # Actually, if we filter by muscle group (e.g. Arms), do we divide by TOTAL workouts that month, 
        # or only workouts that included Arms? Usually TOTAL workouts gives "Volume load contribution to the session".
        # But if I didn't train Arms today, it shouldn't dilute the average of Arm days?
        # Let's stick to: Average Volume *per session where that muscle was trained*? 
        # Or Average Volume *per calendar workout*?
        # The user said "Volume divided by number of workouts". Ref1 likely did Total Volume / Total Workouts.
        # Let's count unique start_times involved in this slice.
        
        workouts_per_month = plot_data.groupby('month_date')['start_time'].nunique().reset_index(name='workout_count')
        
        # Aggregate Volume
        group_col = 'muscle_group' if filter_group else 'major_group'
        if not filter_group:
             plot_data['major_group'] = plot_data['muscle_group'].replace(GROUP_MAPPING)
        
        monthly_vol = plot_data.groupby(['month_date', group_col])['volume'].sum().reset_index()
        
        # Merge to get denominator
        merged = pd.merge(monthly_vol, workouts_per_month, on='month_date')
        merged['avg_vol_k'] = (merged['volume'] / merged['workout_count']) / 1000.0
        
        # --- 2. Plot ---
        color_map = MUSCLE_GROUP_COLORS
        orders = {group_col: MUSCLE_GROUP_ORDER} if not filter_group else {} # Use strict order for Major

        fig = px.bar(
            merged,
            x='month_date',
            y='avg_vol_k',
            color=group_col,
            title='Avg Volume per Workout (tonnes) & Bodyweight (kg)',
            color_discrete_map=color_map,
            category_orders=orders
        )

        # --- 3. Bodyweight Overlay ---
        if self.bodyweight_df is not None and not self.bodyweight_df.empty:
            min_date = plot_data['start_time'].min()
            max_date = plot_data['start_time'].max()
            bw_data = self.bodyweight_df[
                (self.bodyweight_df['date'] >= min_date) & 
                (self.bodyweight_df['date'] <= max_date)
            ].copy()

            if not bw_data.empty:
                bw_data['month_date'] = bw_data['date'].dt.to_period('M').dt.start_time
                monthly_bw = bw_data.groupby('month_date')['weight_kg'].mean().reset_index()
                
                fig.add_trace(
                    go.Scatter(
                        x=monthly_bw['month_date'],
                        y=monthly_bw['weight_kg'],
                        name='Avg Bodyweight',
                        mode='lines+markers',
                        line=dict(color='white', width=3),
                        marker=dict(size=6, color='white'),
                        yaxis='y2'
                    )
                )

                fig.update_layout(
                    yaxis2=dict(
                        title='Bodyweight (kg)',
                        overlaying='y',
                        side='right',
                        showgrid=False
                    )
                )

        # --- 4. Layout ---
        tick_format = "%b" if year else "%b %Y"
        fig.update_layout(
            autosize=True,
            xaxis=dict(title=None, tickformat=tick_format, dtick="M1"),
            yaxis_title='Avg Volume / Workout (tonnes)',
            legend_title_text='Muscle Group',
            hovermode='x unified',
            legend=dict(orientation="h", y=1.15, x=1, xanchor="right")
        )
        
        return fig

    def create_exercise_progression_chart(self, exercise_name):
        """
        Creates a progression chart for a specific exercise.
        Plots:
        1. Scatter points: Total Volume for that exercise in every workout.
        2. Line: Connecting 'Record' points (Cumulative Max Volume).
        """
        if not exercise_name:
            return None
            
        ex_data = self.df[self.df['exercise_title'] == exercise_name].copy()
        if ex_data.empty:
            return None
            
        # Group by workout (start_time) to get session volume for this exercise
        session_vol = ex_data.groupby('start_time')['volume'].sum().reset_index()
        session_vol = session_vol.sort_values('start_time')
        
        # Calculate Cumulative Max (Records)
        session_vol['record_volume'] = session_vol['volume'].cummax()
        
        fig = go.Figure()
        
        # 1. All Workouts (Scatter)
        fig.add_trace(go.Scatter(
            x=session_vol['start_time'],
            y=session_vol['volume'],
            mode='markers',
            name='Session Volume',
            marker=dict(color='#BDADEA', size=8, opacity=0.6)
        ))
        
        # 2. Record Progression (Line)
        # We construct a step line for records
        fig.add_trace(go.Scatter(
            x=session_vol['start_time'],
            y=session_vol['record_volume'],
            mode='lines',
            name='Volume Record',
            line=dict(color='#ef476f', width=2, shape='hv'), # hv shape makes it a step function
            hoverinfo='skip'
        ))

        # Highlights formatting
        fig.update_layout(
            title=f"Volume Progression: {exercise_name}",
            xaxis_title=None,
            yaxis_title='Volume (kg)',
            hovermode='x unified',
            showlegend=True,
            legend=dict(orientation="h", y=1.1, x=1, xanchor="right")
        )
        
        return fig

    def create_muscle_group_distribution(self, year=None):
        """Pie chart of volume by muscle group"""
        plot_data = self.df.copy()
        if year:
            plot_data = plot_data[plot_data['start_time'].dt.year == year]
            
        if plot_data.empty: return None
        
        plot_data['major_group'] = plot_data['muscle_group'].replace(GROUP_MAPPING)
        vol_by_group = plot_data.groupby('major_group')['volume'].sum().reset_index()
        
        fig = px.pie(
            vol_by_group,
            values='volume',
            names='major_group',
            title='Volume Distribution by Muscle Group',
            color='major_group',
            color_discrete_map=MUSCLE_GROUP_COLORS,
            hole=0.4
        )
        return fig
