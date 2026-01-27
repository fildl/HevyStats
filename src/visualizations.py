import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from .const import MUSCLE_GROUP_COLORS, PHASE_COLORS, GROUP_MAPPING, MUSCLE_GROUP_ORDER

class WorkoutVisualizer:
    def __init__(self, df, bodyweight_df=None, phase_df=None):
        self.df = df
        self.bodyweight_df = bodyweight_df
        self.phases_data = phase_df

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
                
                # Phase Lookup
                def get_phase(dt):
                    if self.phases_data is not None:
                        past_phases = self.phases_data[self.phases_data['date'] <= dt]
                        if not past_phases.empty: return past_phases.iloc[-1]['phase']
                    return 'unknown'

                monthly_bw['phase'] = monthly_bw['month_date'].apply(get_phase)

                # 1. Background line
                fig.add_trace(
                    go.Scatter(
                        x=monthly_bw['month_date'],
                        y=monthly_bw['weight_kg'],
                        mode='lines',
                        line=dict(color='rgba(255,255,255,0.4)', width=3),
                        showlegend=False,
                        hoverinfo='skip',
                        yaxis='y2'
                    )
                )

                # 2. Phase Markers
                for phase_name in monthly_bw['phase'].unique():
                    phase_subset = monthly_bw[monthly_bw['phase'] == phase_name]
                    color = PHASE_COLORS.get(phase_name, '#ffffff')
                    fig.add_trace(
                        go.Scatter(
                            x=phase_subset['month_date'],
                            y=phase_subset['weight_kg'],
                            name=f"BW ({phase_name})",
                            mode='markers',
                            marker=dict(color=color, size=8, line=dict(width=1, color='white')),
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
        
        # --- 3. Bodyweight Overlay (Phase Colored) ---
        if self.bodyweight_df is not None and not self.bodyweight_df.empty and self.phases_data is not None:
             min_date = plot_data['start_time'].min()
             max_date = plot_data['start_time'].max()
             bw_data = self.bodyweight_df[
                (self.bodyweight_df['date'] >= min_date) & 
                (self.bodyweight_df['date'] <= max_date)
            ].copy()
             if not bw_data.empty:
                bw_data['month_date'] = bw_data['date'].dt.to_period('M').dt.start_time
                monthly_bw = bw_data.groupby('month_date')['weight_kg'].mean().reset_index()
                
                def get_phase(dt):
                    past_phases = self.phases_data[self.phases_data['date'] <= dt]
                    if not past_phases.empty: return past_phases.iloc[-1]['phase']
                    return 'unknown'

                monthly_bw['phase'] = monthly_bw['month_date'].apply(get_phase)
                
                fig.add_trace(go.Scatter(
                    x=monthly_bw['month_date'],
                    y=monthly_bw['weight_kg'],
                    mode='lines',
                    line=dict(color='rgba(255,255,255,0.4)', width=3),
                    showlegend=False,
                    yaxis='y2',
                    hoverinfo='skip'
                ))
                
                for phase_name in monthly_bw['phase'].unique():
                    phase_subset = monthly_bw[monthly_bw['phase'] == phase_name]
                    color = PHASE_COLORS.get(phase_name, '#ffffff')
                    fig.add_trace(go.Scatter(
                        x=phase_subset['month_date'],
                        y=phase_subset['weight_kg'],
                        name=f"BW ({phase_name})",
                        mode='markers',
                        marker=dict(color=color, size=8, line=dict(width=1, color='white')),
                        yaxis='y2'
                    ))

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

        # --- 3. Bodyweight Overlay (Phase Colored) ---
        if self.bodyweight_df is not None and not self.bodyweight_df.empty and self.phases_data is not None:
            min_date = plot_data['start_time'].min()
            max_date = plot_data['start_time'].max()
            bw_data = self.bodyweight_df[
                (self.bodyweight_df['date'] >= min_date) & 
                (self.bodyweight_df['date'] <= max_date)
            ].copy()

            if not bw_data.empty:
                bw_data['month_date'] = bw_data['date'].dt.to_period('M').dt.start_time
                # Group by month to get avg weight
                monthly_bw = bw_data.groupby('month_date')['weight_kg'].mean().reset_index()
                
                # Assign Phase to each month
                # Logic: Find the phase that started before or on this month
                def get_phase(dt):
                    # dt is Timestamp (start of month). 
                    # We want the phase active at this time.
                    past_phases = self.phases_data[self.phases_data['date'] <= dt]
                    if not past_phases.empty:
                        return past_phases.iloc[-1]['phase']
                    # If no phase starts before, maybe take the first one? or 'unknown'
                    return 'unknown'

                monthly_bw['phase'] = monthly_bw['month_date'].apply(get_phase)

                # Generate coloured traces using px.line logic
                # We need to ensure connectivity. px.line with color breaks the line.
                # To look good, we often plot a faint background line + colored markers/segments
                
                # 1. Background connection line (neutral)
                fig.add_trace(
                    go.Scatter(
                        x=monthly_bw['month_date'],
                        y=monthly_bw['weight_kg'],
                        mode='lines',
                        line=dict(color='rgba(255,255,255,0.4)', width=3),
                        showlegend=False,
                        hoverinfo='skip',
                        yaxis='y2'
                    )
                )

                # 2. Colored Markers + Lines (Segments)
                # We use px to handle the grouping colors easily
                # Warning: px.line creates gaps between different groups. The background line handles the visual flow.
                
                # Ensure colors are mapped
                for phase_name in monthly_bw['phase'].unique():
                    phase_subset = monthly_bw[monthly_bw['phase'] == phase_name]
                    color = PHASE_COLORS.get(phase_name, '#ffffff')
                    
                    fig.add_trace(
                        go.Scatter(
                            x=phase_subset['month_date'],
                            y=phase_subset['weight_kg'],
                            name=f"BW ({phase_name})",
                            mode='markers', # Just markers to avoid confusing gaps, or lines+markers?
                            # If we use lines, it connects disjoint months of same phase (e.g. Bulk in Jan, Bulk in Dec -> Line across).
                            # So strictly speaking, we should just use Markers for the phase indicator on top of the generic line.
                            marker=dict(color=color, size=8, line=dict(width=1, color='white')),
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
        # Include 'gym' and 'gym_dependent' in aggregation
        agg_dict = {'volume': 'sum'}
        if 'gym' in ex_data.columns:
            agg_dict['gym'] = 'first'
        if 'gym_dependent' in ex_data.columns:
            agg_dict['gym_dependent'] = 'first'
            
        session_vol = ex_data.groupby('start_time').agg(agg_dict).reset_index()
        session_vol = session_vol.sort_values('start_time')
        
        # Calculate Cumulative Max (Records)
        # Check if gym dependent
        is_dependent = False
        if 'gym_dependent' in session_vol.columns and not session_vol.empty:
            # It's a boolean column, assume True if any is True (should be consistent per exercise)
            is_dependent = bool(session_vol.iloc[0]['gym_dependent'])

        if not is_dependent:
             session_vol['record_volume'] = session_vol['volume'].cummax()
        else:
             records = []
             gym_maxes = {} # gym -> current record
             
             for _, row in session_vol.iterrows():
                 gym = row.get('gym', 'Unknown')
                 current_vol = row['volume']
                 
                 existing_max = gym_maxes.get(gym, 0.0)
                 new_max = max(existing_max, current_vol)
                 gym_maxes[gym] = new_max
                 
                 records.append(new_max)
             
             session_vol['record_volume'] = records
        
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
        if not is_dependent:
            fig.add_trace(go.Scatter(
                x=session_vol['start_time'],
                y=session_vol['record_volume'],
                mode='lines',
                name='Volume Record',
                line=dict(color='#ef476f', width=2, shape='hv'), # hv shape makes it a step function
                hoverinfo='skip'
            ))
        else:
            # For dependent records, we need to break the line when the gym changes.
            # We identify segments where the gym is continuous.
            session_vol['gym'] = session_vol['gym'].fillna('Unknown')
            # Create a group id that increments every time gym changes
            session_vol['gym_group'] = (session_vol['gym'] != session_vol['gym'].shift()).cumsum()
            
            # Using legendgroup to have one legend item toggle all segments
            show_legend = True
            
            for _, group_data in session_vol.groupby('gym_group'):
                fig.add_trace(go.Scatter(
                    x=group_data['start_time'],
                    y=group_data['record_volume'],
                    mode='lines',
                    name='Volume Record',
                    legendgroup='records',
                    showlegend=show_legend,
                    line=dict(color='#ef476f', width=2, shape='hv'),
                    hoverinfo='skip'
                ))
                show_legend = False # Only show first segment in legend

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
