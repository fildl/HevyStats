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

        # [MODIFIED] Create Display Column for cleaner legend
        # We need a new color map for the formatted names
        monthly_vol['display_group'] = monthly_vol['major_group'].apply(lambda x: x.replace('_', ' ').title())
        
        display_color_map = {k.replace('_', ' ').title(): v for k, v in MUSCLE_GROUP_COLORS.items()}
        display_orders = [g.replace('_', ' ').title() for g in MUSCLE_GROUP_ORDER]

        # --- 2. Create Stacked Bar Chart ---
        fig = px.bar(
            monthly_vol,
            x='month_date',
            y='volume_k',
            color='display_group',
            title='Monthly Training Volume (tonnes) & Bodyweight (kg)',
            color_discrete_map=display_color_map,
            category_orders={'display_group': display_orders},
            text='volume_k',
            labels={'volume_k': 'Volume', 'display_group': 'Group', 'month_date': 'Date'}
        )

        fig.update_traces(
            texttemplate='%{text:.1f}', 
            textposition='inside', 
            textfont_size=16,
            hovertemplate='%{y:.1f} t'
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
                            yaxis='y2',
                            hovertemplate='%{y:.1f} kg'
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
            height=600,
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

        # [MODIFIED] Create Display Column
        monthly_vol['display_muscle'] = monthly_vol['muscle_group'].apply(lambda x: x.replace('_', ' ').title())
        display_color_map = {k.replace('_', ' ').title(): v for k, v in MUSCLE_GROUP_COLORS.items()}

        # --- 2. Create Stacked Bar Chart ---
        fig = px.bar(
            monthly_vol,
            x='month_date',
            y='volume_k',
            color='display_muscle',
            title='Monthly Volume by Specific Muscle (tonnes)',
            color_discrete_map=display_color_map,
            text='volume_k',
            labels={'volume_k': 'Volume', 'display_muscle': 'Muscle', 'month_date': 'Date'}
            # We don't enforce a strict order here as there are many specific muscles,
            # but Plotly usually sorts by value or name.
        )
        
        fig.update_traces(
            texttemplate='%{text:.1f}', 
            textposition='inside', 
            textfont_size=16,
            hovertemplate='%{y:.1f} t'
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
                        yaxis='y2',
                        hovertemplate='%{y:.1f} kg'
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
            height=600,
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
        # [MODIFIED] Create Display Column
        merged['display_group'] = merged[group_col].apply(lambda x: x.replace('_', ' ').title())
        display_color_map = {k.replace('_', ' ').title(): v for k, v in MUSCLE_GROUP_COLORS.items()}
        
        orders = {}
        if not filter_group:
             display_orders = [g.replace('_', ' ').title() for g in MUSCLE_GROUP_ORDER]
             orders = {'display_group': display_orders}

        fig = px.bar(
            merged,
            x='month_date',
            y='avg_vol_k',
            color='display_group',
            title='Avg Volume per Workout (tonnes) & Bodyweight (kg)',
            color_discrete_map=display_color_map,
            category_orders=orders,
            text='avg_vol_k',
            labels={'avg_vol_k': 'Average Volume', 'display_group': 'Group', 'month_date': 'Date'}
        )
        
        fig.update_traces(
            texttemplate='%{text:.1f}', 
            textposition='inside', 
            textfont_size=16,
            hovertemplate='%{y:.1f} t'
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
                            yaxis='y2',
                            hovertemplate='%{y:.1f} kg'
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
            height=600,
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
            marker=dict(color='#BDADEA', size=8, opacity=0.6),
            hovertemplate='Volume: %{y:.1f} kg<extra></extra>'
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
            xaxis=dict(hoverformat='%d %b %Y'),
            yaxis_title='Volume (kg)',
            hovermode='x unified',
            showlegend=True,
            legend=dict(orientation="h", y=1.1, x=1, xanchor="right")
        )
        
        return fig

    def create_muscle_balance_radar(self, current_df, comparison_dfs=None, title="Muscle Balance"):
        """
        Creates a Radar Chart (Spider Chart) comparing muscle group volume distribution.
        
        Args:
            current_df (pd.DataFrame): The main dataframe to visualize (e.g. Current Routine)
            comparison_dfs (list of dict, optional): List of dicts with keys:
                - 'df': dataframe
                - 'label': str (e.g. "Historical Avg")
                - 'color': str (hex or rgba)
        """
        if current_df is None or current_df.empty:
            return None

        # Helper to calculate % distribution
        def get_distribution(df):
            if df.empty: return pd.Series()
            df = df.copy()
            df['major_group'] = df['muscle_group'].replace(GROUP_MAPPING)
            # Use 'size' to count sets (rows), assuming 1 row = 1 set
            set_count_by_group = df.groupby('major_group').size()
            total_sets = set_count_by_group.sum()
            if total_sets == 0: return pd.Series()
            return (set_count_by_group / total_sets) * 100

        # DATA PREPARATION
        # 1. Current
        current_dist = get_distribution(current_df)
        
        # Ensure all groups exist in order -> MUSCLE_GROUP_ORDER
        # We need a fixed axis for radar
        # [MODIFIED] Exclude 'unknown' from axes
        axes = [g for g in MUSCLE_GROUP_ORDER if g != 'unknown']
        formatted_axes = [g.replace('_', ' ').title() for g in axes]
        
        # [MODIFIED] Pre-calculate current values to track max for scaling
        values_curr = [current_dist.get(g, 0) for g in axes]
        max_val_found = max(values_curr) if values_curr else 0
        
        # Prepare traces
        traces = []
        
        # Add Comparison Traces FIRST (so they are behind the current one if filled)
        if comparison_dfs:
            for item in comparison_dfs:
                comp_df = item['df']
                label = item['label']
                color = item.get('color', 'grey')
                
                dist = get_distribution(comp_df)
                # Reindex to ensure order and fill missing with 0
                values = [dist.get(g, 0) for g in axes]
                if values:
                    max_val_found = max(max_val_found, max(values))
                # Close the loop
                values_closed = values + [values[0]]
                axes_closed = formatted_axes + [formatted_axes[0]]
                
                # Handle color for fill (make it more transparent)
                # If it's already rgba, we want to lower the alpha.
                # If it's rgb, convert to rgba with low alpha.
                # Quick fix: If it starts with rgba, just use a hardcoded low opacity override or try to parse.
                # Safe approach: always use rgba(r,g,b,0.1) if input is hex/rgb, but handling input rgba string is messy.
                # Let's just use the provided color for fill but set opacity in Scatterpolar if possible?
                # Scatterpolar 'opacity' affects line too. 'fillcolor' is separate.
                
                fill_col = color
                if 'rgba' in color:
                     # e.g. rgba(54, 162, 235, 0.6)
                     # We want to replace 0.6 with 0.1
                     # rsplit on comma
                     parts = color.rsplit(',', 1)
                     if len(parts) == 2:
                         fill_col = parts[0] + ', 0.1)'
                elif 'rgb' in color:
                     fill_col = color.replace('rgb', 'rgba').replace(')', ', 0.1)')
                else:
                     # Hex or name
                     # Leave as is or try to convert? Plotly handles hex.
                     # To add opacity to hex, we can't easily do it in string without conversion.
                     # For now, just use the color as is (it might be opaque).
                     pass

                traces.append(go.Scatterpolar(
                    r=values_closed,
                    theta=axes_closed,
                    fill='toself', 
                    fillcolor=fill_col,
                    name=label,
                    line=dict(color=color, dash='dashdot'),
                    hoverinfo='name+r'
                ))

        # Add Current Trace
        # values_curr is already calculated above
        values_curr_closed = values_curr + [values_curr[0]]
        axes_closed = formatted_axes + [formatted_axes[0]]
        
        traces.append(go.Scatterpolar(
            r=values_curr_closed,
            theta=axes_closed,
            fill='toself',
            name="Current",
            line=dict(color='#ef476f', width=3),
            marker=dict(size=5),
        ))

        fig = go.Figure(data=traces)
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, max(max_val_found, 30)], # Dynamic max but at least 30%
                    ticksuffix='%',
                    showticklabels=True
                )
            ),
            showlegend=True,
            title=title,
            height=500,
            margin=dict(l=80, r=80, t=50, b=50),
            legend=dict(orientation="h", y=-0.1) # Legend at bottom
        )
        
        return fig

    def create_consistency_heatmap(self, year=None):
        """
        Creates a GitHub-style consistency heatmap.
        X-axis: Weeks
        Y-axis: Days (Mon-Sun)
        Color: Volume (Intensity)
        """
        plot_data = self.df.copy()
        
        # Date Logic
        if year:
            plot_data = plot_data[plot_data['start_time'].dt.year == year]
        else:
            # Default to last 365 days if All Time is selected, to avoid massive charts
            if not plot_data.empty:
                max_date = plot_data['start_time'].max()
                start_limit = max_date - pd.Timedelta(days=365)
                plot_data = plot_data[plot_data['start_time'] >= start_limit]

        if plot_data.empty:
            return None

        # Aggregate per day - Use SET COUNT instead of Volume
        plot_data['date'] = plot_data['start_time'].dt.date
        daily_metric = plot_data.groupby('date').size().reset_index(name='sets')
        
        # Create full date range to show empty days as grey/empty
        min_date = daily_metric['date'].min()
        max_date = daily_metric['date'].max()
        all_dates = pd.date_range(start=min_date, end=max_date, freq='D').date
        
        # Merge with full range
        full_df = pd.DataFrame({'date': all_dates})
        full_df = pd.merge(full_df, daily_metric, on='date', how='left').fillna(0)
        
        # Prepare Coordinates
        # y: Day of Week (Monday=0, Sunday=6) - We want Mon at top (0) or Sun at top?
        # Usually GitHub has Sun/Mon at top. Let's put Mon (0) at Top.
        # But Plotly Heatmap Y=0 is bottom by default unless reversed.
        
        full_df['datetime'] = pd.to_datetime(full_df['date'])
        full_df['weekday'] = full_df['datetime'].dt.weekday # 0=Mon, 6=Sun
        full_df['week_start'] = full_df['datetime'].apply(lambda d: d - pd.Timedelta(days=d.weekday()))
        
        # Heatmap
        # We need to reshape for specific x,y,z or just pass columns.
        
        # Map weekday numbers to names for hover
        days_map = {0:'Mon', 1:'Tue', 2:'Wed', 3:'Thu', 4:'Fri', 5:'Sat', 6:'Sun'}
        full_df['day_name'] = full_df['weekday'].map(days_map)
        
        # Invert Y for visualization (Mon at top) -> actually with 'autorange="reversed"' in layout
        
        fig = go.Figure(data=go.Heatmap(
            x=full_df['week_start'],
            y=full_df['day_name'], # Or just weekday index
            z=full_df['sets'],
            colorscale='Greens',
            showscale=False, # cleaner look? or True for reference
            xgap=2, # separate cells
            ygap=2,
            hovertemplate='<b>%{y}</b>, %{x}<br>Sets: %{z:.0f}<extra></extra>'
        ))

        fig.update_layout(
            title="Consistency Streak",
            height=200, # Compact height
            yaxis=dict(
                title=None,
                categoryorder='array',
                categoryarray=['Sun', 'Sat', 'Fri', 'Thu', 'Wed', 'Tue', 'Mon'], # Mon at top
                showgrid=False,
                zeroline=False
            ),
            xaxis=dict(
                title=None,
                showgrid=False,
                zeroline=False,
                tickformat='%b %d'
            ),
            margin=dict(l=40, r=40, t=40, b=20)
        )
        
        return fig
