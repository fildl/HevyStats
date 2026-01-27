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
