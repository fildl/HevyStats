import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from .const import MUSCLE_GROUP_COLORS, PHASE_COLORS, GROUP_MAPPING

class WorkoutVisualizer:
    def __init__(self, df, bodyweight_df=None, phase_df=None):
        self.df = df
        self.bodyweight_df = bodyweight_df
        self.phase_df = phase_df

    def create_monthly_volume_chart(self, year=None):
        """
        Creates a stacked bar chart of monthly volume by muscle group.
        """
        plot_data = self.df.copy()
        if year:
            plot_data = plot_data[plot_data['start_time'].dt.year == year]

        if plot_data.empty:
            return None

        # Prepare data
        plot_data['year_month'] = plot_data['start_time'].dt.to_period('M').astype(str)
        
        # Aggregate
        monthly_vol = plot_data.groupby(['year_month', 'muscle_group'])['volume'].sum().reset_index()
        monthly_vol['volume_k'] = monthly_vol['volume'] / 1000.0
        
        # Sort muscle groups to ensure consistent coloring
        # We want mapped muscle groups (major groups) if using GROUP_MAPPING logic, 
        # but ref1 logic mapped them first. Let's assume input df has 'muscle_group' as the specific one, 
        # but we might want to aggregate by major group for the main chart?
        # Ref1 logic: plot_data['plotted_muscle_group'] = plot_data['muscle_group'].replace(self.GROUP_MAPPING)
        
        monthly_vol['major_group'] = monthly_vol['muscle_group'].replace(GROUP_MAPPING)
        
        # Re-aggregate by major group
        final_df = monthly_vol.groupby(['year_month', 'major_group'])['volume_k'].sum().reset_index()

        fig = px.bar(
            final_df,
            x='year_month',
            y='volume_k',
            color='major_group',
            title='Monthly Training Volume (tonnes)',
            color_discrete_map=MUSCLE_GROUP_COLORS,
            category_orders={'major_group': list(MUSCLE_GROUP_COLORS.keys())}
        )

        fig.update_layout(
            autosize=True,
            xaxis_title=None,
            yaxis_title='Volume (x1000 kg)',
            legend_title_text='Muscle Group',
            hovermode='x unified'
        )

        # Add Bodyweight Trace (Secondary Y-Axis) if available
        if self.bodyweight_df is not None and not self.bodyweight_df.empty:
            # Filter bodyweight for the relevant period
            min_date = plot_data['start_time'].min()
            max_date = plot_data['start_time'].max()
            
            bw_data = self.bodyweight_df[
                (self.bodyweight_df['date'] >= min_date) & 
                (self.bodyweight_df['date'] <= max_date)
            ].sort_values('date')

            if not bw_data.empty:
                # Convert dates to match x-axis period format roughly, or just plot on time axis?
                # Plotly bar charts with categorical x-axis (strings) vs continuous time axis.
                # To mix them perfectly, we should probably stick to real datetime objects for X.
                
                # Let's rebuild the bar chart with datetime objects for X to allow overlay
                # Re-do aggregation with real dates (Start of Month)
                plot_data['month_date'] = plot_data['start_time'].dt.to_period('M').dt.start_time
                monthly_vol_dt = plot_data.groupby(['month_date', 'muscle_group'])['volume'].sum().reset_index()
                monthly_vol_dt['major_group'] = monthly_vol_dt['muscle_group'].replace(GROUP_MAPPING)
                final_df_dt = monthly_vol_dt.groupby(['month_date', 'major_group'])['volume'].sum().reset_index()
                final_df_dt['volume_k'] = final_df_dt['volume'] / 1000.0

                fig = px.bar(
                    final_df_dt,
                    x='month_date',
                    y='volume_k',
                    color='major_group',
                    title='Monthly Training Volume',
                    color_discrete_map=MUSCLE_GROUP_COLORS
                )

                fig.add_trace(
                    go.Scatter(
                        x=bw_data['date'],
                        y=bw_data['weight_kg'],
                        name='Bodyweight',
                        mode='lines+markers',
                        line=dict(color='white', width=2),
                        yaxis='y2'
                    )
                )

                fig.update_layout(
                    yaxis2=dict(
                        title='Bodyweight (kg)',
                        overlaying='y',
                        side='right'
                    )
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
