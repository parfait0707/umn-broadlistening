import json
import os
import argparse
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc


class KouchouVisualization:
    def __init__(self, data_path):
        """Initialize the visualization with data from a JSON file."""
        with open(data_path, "r", encoding="utf-8") as f:
            self.result = json.load(f)

        self.arguments = self.result.get("arguments", [])
        self.clusters = self.result.get("clusters", [])
        self.overview = self.result.get("overview", "")

        # Define soft colors for clusters (same as in the original)
        self.soft_colors = [
            "#7ac943",
            "#3fa9f5",
            "#ff7997",
            "#e0dd02",
            "#d6410f",
            "#b39647",
            "#7cccc3",
            "#a147e6",
            "#ff6b6b",
            "#4ecdc4",
            "#ffbe0b",
            "#fb5607",
            "#8338ec",
            "#3a86ff",
            "#ff006e",
            "#8ac926",
            "#1982c4",
            "#6a4c93",
            "#f72585",
            "#7209b7",
            "#00b4d8",
            "#e76f51",
            "#606c38",
            "#9d4edd",
            "#457b9d",
            "#bc6c25",
            "#2a9d8f",
            "#e07a5f",
            "#5e548e",
            "#81b29a",
            "#f4a261",
            "#9b5de5",
            "#f15bb5",
            "#00bbf9",
            "#98c1d9",
            "#84a59d",
            "#f28482",
            "#00afb9",
            "#cdb4db",
            "#fcbf49",
        ]

        # Create color map for clusters
        self.cluster_color_map = {}
        for i, cluster in enumerate([c for c in self.clusters if c["level"] == 1]):
            self.cluster_color_map[cluster["id"]] = self.soft_colors[
                i % len(self.soft_colors)
            ]

    def get_dense_clusters(self, max_density=25, min_value=3):
        """Filter clusters by density and minimum value."""
        # Get the deepest level
        max_level = max([c["level"] for c in self.clusters]) if self.clusters else 0

        # Filter clusters by density and minimum value
        dense_clusters = [
            c
            for c in self.clusters
            if c["level"] == max_level
            and c.get("density_rank_percentile", 100) <= max_density
            and c.get("value", 0) >= min_value
        ]

        return dense_clusters

    def create_scatter_chart(self, target_level=1, show_labels=True):
        """Create a scatter chart for the specified level."""
        # Filter clusters by level
        target_clusters = [c for c in self.clusters if c["level"] == target_level]

        # Create figure
        fig = go.Figure()

        # Add scatter traces for each cluster
        for cluster in target_clusters:
            # Get arguments for this cluster
            cluster_args = [
                arg
                for arg in self.arguments
                if cluster["id"] in arg.get("cluster_ids", [])
            ]

            if not cluster_args:
                continue

            # Extract coordinates and texts
            x_values = [arg.get("x", 0) for arg in cluster_args]
            y_values = [arg.get("y", 0) for arg in cluster_args]
            texts = [
                f"<b>{cluster['label']}</b><br>{arg['argument'].replace('.{30}', '$1<br />')}"
                for arg in cluster_args
            ]

            # Calculate cluster center
            center_x = sum(x_values) / len(x_values) if x_values else 0
            center_y = sum(y_values) / len(y_values) if y_values else 0

            # Add scatter plot for this cluster
            fig.add_trace(
                go.Scatter(
                    x=x_values,
                    y=y_values,
                    mode="markers",
                    marker=dict(
                        color=self.cluster_color_map.get(cluster["id"], "#cccccc"),
                        size=10,
                    ),
                    text=texts,
                    hoverinfo="text",
                    name=cluster["label"],
                )
            )

            # Add cluster label if requested
            if show_labels:
                fig.add_trace(
                    go.Scatter(
                        x=[center_x],
                        y=[center_y],
                        mode="text",
                        text=[cluster["label"]],
                        textfont=dict(size=14, color="black"),
                        hoverinfo="none",
                        showlegend=False,
                    )
                )

        # Update layout
        fig.update_layout(
            title=dict(
                text=f"Cluster Visualization (Level {target_level})",
                y=0.98,
                x=0.5,
                xanchor='center',
                yanchor='top'
            ),
            xaxis=dict(title="", showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(title="", showgrid=False, zeroline=False, showticklabels=False),
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.15,           # <<< scatterの下に配置
                xanchor="center",
                x=0.5,
                bgcolor='rgba(255,255,255,0)'  # <<< 安全のため透明背景
            ),
            margin=dict(l=20, r=20, t=60, b=60),  # <<< 上下マージンでバランス調整
            height=700,                           # <<< 任意。プロット領域の見やすさ向上
            hovermode="closest",
        )

        return fig

    def create_scatter_dense(self, max_density=25, min_value=3, show_labels=True):
        """Create a scatter chart showing only the densest clusters."""
        # Get dense clusters
        dense_clusters = self.get_dense_clusters(max_density, min_value)

        if not dense_clusters:
            # Return empty figure if no dense clusters
            fig = go.Figure()
            fig.update_layout(
                title="No Dense Clusters Found",
                annotations=[
                    dict(
                        text="No clusters meet the density and size criteria",
                        showarrow=False,
                        xref="paper",
                        yref="paper",
                        x=0.5,
                        y=0.5,
                    )
                ],
            )
            return fig

        # Create figure
        fig = go.Figure()

        # Add scatter traces for each dense cluster
        for cluster in dense_clusters:
            # Get arguments for this cluster
            cluster_args = [
                arg
                for arg in self.arguments
                if cluster["id"] in arg.get("cluster_ids", [])
            ]

            if not cluster_args:
                continue

            # Extract coordinates and texts
            x_values = [arg.get("x", 0) for arg in cluster_args]
            y_values = [arg.get("y", 0) for arg in cluster_args]
            texts = [
                f"<b>{cluster['label']}</b><br>{arg['argument'].replace('.{30}', '$1<br />')}"
                for arg in cluster_args
            ]

            # Calculate cluster center
            center_x = sum(x_values) / len(x_values) if x_values else 0
            center_y = sum(y_values) / len(y_values) if y_values else 0

            # Add scatter plot for this cluster
            fig.add_trace(
                go.Scatter(
                    x=x_values,
                    y=y_values,
                    mode="markers",
                    marker=dict(
                        color=self.cluster_color_map.get(
                            cluster["id"].split("-")[0], "#cccccc"
                        ),
                        size=10,
                    ),
                    text=texts,
                    hoverinfo="text",
                    name=cluster["label"],
                )
            )

            # Add cluster label if requested
            if show_labels:
                fig.add_trace(
                    go.Scatter(
                        x=[center_x],
                        y=[center_y],
                        mode="text",
                        text=[cluster["label"]],
                        textfont=dict(size=14, color="black"),
                        hoverinfo="none",
                        showlegend=False,
                    )
                )

        # Update layout
        fig.update_layout(
            title=dict(
                text=f"Dense Clusters Visualization (Density ≤ {max_density}%, Size ≥ {min_value})",
                y=0.97,
                x=0.5,
                xanchor='center',
                yanchor='top'
            ),
            xaxis=dict(title="", showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(title="", showgrid=False, zeroline=False, showticklabels=False),
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.15,       # <<< プロットエリアの**外**にlegendを配置
                xanchor="center",
                x=0.5,
                bgcolor='rgba(255,255,255,0)'  # <<< 背景透明に（安全対策）
            ),
            margin=dict(l=20, r=20, t=60, b=40),  # <<< 下側marginも広げる
            height=700,
            hovermode="closest",
        )
        
        return fig

    def create_treemap(self, root_level="all"):
        """Create a treemap visualization of the hierarchical clusters."""
        # Prepare data for treemap
        labels = []
        parents = []
        values = []
        hover_texts = []

        # Add root
        labels.append("All")
        parents.append("")
        values.append(
            sum([c.get("value", 0) for c in self.clusters if c["level"] == 1])
        )
        hover_texts.append("All Clusters")

        # Add clusters
        for cluster in self.clusters:
            # Skip if this is beyond our current view
            if (
                root_level != "all"
                and not cluster["id"].startswith(root_level)
                and cluster["id"] != root_level
            ):
                continue

            labels.append(cluster["id"])

            # Set parent
            if cluster["level"] == 1:
                parents.append("All")
            else:
                parents.append(cluster.get("parent", ""))

            values.append(cluster.get("value", 0))
            hover_texts.append(
                f"<b>{cluster['label']}</b><br>{cluster.get('takeaway', '')}"
            )

        # Create figure
        fig = go.Figure(
            go.Treemap(
                labels=labels,
                parents=parents,
                values=values,
                text=[
                    l if i > 0 else "" for i, l in enumerate(labels)
                ],  # Don't show 'All' text
                hovertext=hover_texts,
                hoverinfo="text",
                textinfo="label",
                marker=dict(
                    colors=[
                        (
                            self.cluster_color_map.get(l.split("-")[0], "#cccccc")
                            if l != "All"
                            else "#ffffff"
                        )
                        for l in labels
                    ]
                ),
                branchvalues="total",
            )
        )

        # Update layout
        fig.update_layout(
            title="Hierarchical Cluster Visualization",
            margin=dict(l=20, r=20, t=60, b=20),
        )

        return fig

    def export_html(self, output_dir="output"):
        """Export all visualizations as HTML files."""
        os.makedirs(output_dir, exist_ok=True)

        # Create and save scatter chart
        scatter_fig = self.create_scatter_chart(target_level=1)
        scatter_fig.write_html(os.path.join(output_dir, "scatter_all.html"))

        # Create and save dense scatter chart
        dense_fig = self.create_scatter_dense()
        dense_fig.write_html(os.path.join(output_dir, "scatter_dense.html"))

        # Create and save treemap
        treemap_fig = self.create_treemap()
        treemap_fig.write_html(os.path.join(output_dir, "treemap.html"))

        # Create and save overview
        with open(
            os.path.join(output_dir, "overview.html"), "w", encoding="utf-8"
        ) as f:
            f.write(
                f"""  
            <!DOCTYPE html>  
            <html>  
            <head>  
                <title>Kouchou AI Report Overview</title>  
                <style>  
                    body {{ font-family: 'Roboto', 'Noto Sans JP', sans-serif; margin: 0; padding: 20px; }}  
                    .container {{ max-width: 800px; margin: 0 auto; }}  
                    h1 {{ color: #2577b1; }}  
                    .overview {{ white-space: pre-wrap; }}  
                </style>  
            </head>  
            <body>  
                <div class="container">  
                    <h1>Report Overview</h1>  
                    <div class="overview">{self.overview}</div>  
                </div>  
            </body>  
            </html>  
            """
            )

        print(f"Visualizations exported to {output_dir}/")

    def run_dashboard(self, port=8050):
        """Run an interactive Dash dashboard."""
        app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

        app.layout = html.Div(
            [
                dbc.Container(
                    [
                        html.H1("Voice AI Visualization", className="my-4"),
                        # Overview
                        dbc.Card(
                            [
                                dbc.CardHeader("Overview"),
                                dbc.CardBody(
                                    html.Pre(
                                        self.overview, style={"white-space": "pre-wrap"}
                                    )
                                ),
                            ],
                            className="mb-4",
                        ),
                        # Chart selection
                        dbc.Card(
                            [
                                dbc.CardHeader("Visualization Type"),
                                dbc.CardBody(
                                    [
                                        dbc.RadioItems(
                                            id="chart-type",
                                            options=[
                                                {
                                                    "label": "Scatter (All)",
                                                    "value": "scatter-all",
                                                },
                                                {
                                                    "label": "Scatter (Dense Groups)",
                                                    "value": "scatter-dense",
                                                },
                                                {
                                                    "label": "Treemap",
                                                    "value": "treemap",
                                                },
                                            ],
                                            value="scatter-all",
                                            className="mb-3",
                                        ),
                                        # Settings for dense clusters
                                        html.Div(
                                            [
                                                html.H5(
                                                    "Dense Cluster Settings",
                                                    className="mb-2",
                                                ),
                                                dbc.Row(
                                                    [
                                                        dbc.Col(
                                                            [
                                                                html.Label(
                                                                    "Max Density Percentile"
                                                                ),
                                                                dcc.Slider(
                                                                    id="density-slider",
                                                                    min=5,
                                                                    max=100,
                                                                    step=5,
                                                                    value=25,
                                                                    marks={
                                                                        i: f"{i}%"
                                                                        for i in range(
                                                                            5, 101, 15
                                                                        )
                                                                    },
                                                                    className="mb-3",
                                                                ),
                                                            ],
                                                            width=6,
                                                        ),
                                                        dbc.Col(
                                                            [
                                                                html.Label(
                                                                    "Min Cluster Size"
                                                                ),
                                                                dcc.Slider(
                                                                    id="min-value-slider",
                                                                    min=1,
                                                                    max=10,
                                                                    step=1,
                                                                    value=3,
                                                                    marks={
                                                                        i: f"{i}"
                                                                        for i in range(
                                                                            1, 11
                                                                        )
                                                                    },
                                                                    className="mb-3",
                                                                ),
                                                            ],
                                                            width=6,
                                                        ),
                                                    ]
                                                ),
                                                dbc.Checkbox(
                                                    id="show-labels",
                                                    label="Show Cluster Labels",
                                                    value=True,
                                                    className="mb-3",
                                                ),
                                            ],
                                            id="dense-settings",
                                            style={"display": "none"},
                                        ),
                                        # Settings for treemap
                                        html.Div(
                                            [
                                                html.H5(
                                                    "Treemap Settings", className="mb-2"
                                                ),
                                                html.Div(
                                                    [
                                                        html.Label("Current Level"),
                                                        html.Div(
                                                            id="current-level",
                                                            className="mb-2",
                                                        ),
                                                        dbc.Button(
                                                            "Back to Parent",
                                                            id="back-button",
                                                            className="mb-3",
                                                            disabled=True,
                                                        ),
                                                    ]
                                                ),
                                            ],
                                            id="treemap-settings",
                                            style={"display": "none"},
                                        ),
                                    ]
                                ),
                            ],
                            className="mb-4",
                        ),
                        # Chart display
                        dbc.Card(
                            [
                                dbc.CardHeader(
                                    [
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    html.H4(
                                                        "Visualization", className="m-0"
                                                    ),
                                                    width="auto",
                                                ),
                                                dbc.Col(
                                                    dbc.Button(
                                                        "Fullscreen",
                                                        id="fullscreen-button",
                                                        size="sm",
                                                        className="float-end",
                                                    ),
                                                    width="auto",
                                                    className="ms-auto",
                                                ),
                                            ]
                                        )
                                    ]
                                ),
                                dbc.CardBody(
                                    [
                                        html.Div(
                                            id="chart-container",
                                            style={"height": "700px"},
                                        )
                                    ]
                                ),
                            ]
                        ),
                    ]
                )
            ]
        )

        # Store the current treemap level
        app.current_treemap_level = "all"

        @app.callback(  
            [  
                Output("chart-container", "children"),  
                Output("dense-settings", "style"),  
                Output("treemap-settings", "style"),  
                Output("current-level", "children"),  
                Output("back-button", "disabled"),  
            ],  
            [  
                Input("chart-type", "value"),  
                Input("density-slider", "value"),  
                Input("min-value-slider", "value"),  
                Input("show-labels", "value"),  
                Input("back-button", "n_clicks"),  
            ],  
            [  
                State("back-button", "disabled"),  
                State("chart-type", "value"),  # Add this to track the current chart type  
            ],  
        )  
        def update_chart(  
            chart_type, density, min_value, show_labels, back_clicks, back_disabled, current_chart_type  
        ):  
            ctx = dash.callback_context  
            triggered_id = ctx.triggered[0]["prop_id"].split(".")[0] if ctx.triggered else None  
            
            # Handle treemap navigation  
            if triggered_id == "back-button" and not back_disabled and chart_type == "treemap":  
                if app.current_treemap_level != "all":  
                    # Go up one level  
                    parts = app.current_treemap_level.split("-")  
                    if len(parts) > 1:  
                        app.current_treemap_level = "-".join(parts[:-1])  
                    else:  
                        app.current_treemap_level = "all" 

            # Create the appropriate chart
            if chart_type == "scatter-all":
                fig = self.create_scatter_chart(target_level=1, show_labels=show_labels)
                chart = dcc.Graph(figure=fig, style={"height": "100%"})
                dense_style = {"display": "none"}
                treemap_style = {"display": "none"}
                current_level = ""
                back_disabled = True

            elif chart_type == "scatter-dense":
                fig = self.create_scatter_dense(
                    max_density=density, min_value=min_value, show_labels=show_labels
                )
                chart = dcc.Graph(figure=fig, style={"height": "100%"})
                dense_style = {"display": "block"}
                treemap_style = {"display": "none"}
                current_level = ""
                back_disabled = True

            elif chart_type == "treemap":
                fig = self.create_treemap(root_level=app.current_treemap_level)
                chart = dcc.Graph(
                    figure=fig,
                    style={"height": "100%"},
                    id="treemap-graph",
                    config={"displayModeBar": False},
                )
                dense_style = {"display": "none"}
                treemap_style = {"display": "block"}

                # Format current level for display
                if app.current_treemap_level == "all":
                    current_level = "All Clusters"
                    back_disabled = True
                else:
                    # Find the cluster label
                    for cluster in self.clusters:
                        if cluster["id"] == app.current_treemap_level:
                            current_level = (
                                f"{cluster['label']} (ID: {app.current_treemap_level})"
                            )
                            break
                    else:
                        current_level = f"ID: {app.current_treemap_level}"
                    back_disabled = False

            return chart, dense_style, treemap_style, current_level, back_disabled

        # Handle treemap clicks
        @app.callback(
            Output("treemap-graph", "figure", allow_duplicate=True),
            [Input("treemap-graph", "clickData")],
            [State("chart-type", "value")],
            prevent_initial_call=True,
        )
        def handle_treemap_click(click_data, chart_type):  
            try:  
                if chart_type != "treemap" or not click_data:  
                    raise dash.exceptions.PreventUpdate  
                
                print("Click data structure:", click_data)  
                
                # Extract the clicked node ID safely  
                if "points" not in click_data or len(click_data["points"]) == 0:  
                    print("No points data in click event")  
                    raise dash.exceptions.PreventUpdate  
                    
                point = click_data["points"][0]  
                
                # Try different properties that might contain the ID  
                if "label" in point:  
                    clicked_id = point["label"]  
                elif "curveNumber" in point and "pointNumber" in point:  
                    # Get the label from the treemap data  
                    point_number = point["pointNumber"]  
                    # Use the labels from the treemap  
                    clicked_id = self.create_treemap().data[0].labels[point_number]  
                else:  
                    print("Could not find ID in click data:", point)  
                    raise dash.exceptions.PreventUpdate  
                
                print(f"Clicked ID: {clicked_id}")  
                
                # Update current level  
                app.current_treemap_level = clicked_id  
                
                # Create new treemap with the clicked node as root  
                fig = self.create_treemap(root_level=clicked_id)  
                return fig  
            except Exception as e:  
                print(f"Error in treemap click handler: {e}")  
                print(f"Click data: {click_data if 'click_data' in locals() else 'Not available'}")  
                raise dash.exceptions.PreventUpdate

        # Handle fullscreen button
        @app.callback(
            [
                Output("chart-container", "style"),
                Output("fullscreen-button", "children"),
            ],
            [Input("fullscreen-button", "n_clicks")],
            [State("chart-container", "style")],
        )
        def toggle_fullscreen(n_clicks, current_style):
            if n_clicks is None:
                raise dash.exceptions.PreventUpdate

            if n_clicks % 2 == 1:
                # Enter fullscreen
                return {
                    "position": "fixed",
                    "top": "0",
                    "left": "0",
                    "width": "100vw",
                    "height": "100vh",
                    "z-index": "1000",
                    "background-color": "white",
                    "padding": "20px",
                }, "Exit Fullscreen"
            else:
                # Exit fullscreen
                return {"height": "600px"}, "Fullscreen"

        # Run the app
        app.run(debug=False, host="0.0.0.0", port=port)


def main():
    """Main function to run the visualization program."""
    parser = argparse.ArgumentParser(description="Kouchou AI Visualization")
    parser.add_argument(
        "--data", type=str, required=True, help="Path to the JSON data file"
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["dashboard", "export"],
        default="dashboard",
        help="Run mode: dashboard (interactive) or export (static HTML)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="output",
        help="Output directory for exported HTML files",
    )
    parser.add_argument(
        "--port", type=int, default=8050, help="Port for the dashboard server"
    )

    args = parser.parse_args()

    # Create visualization object
    viz = KouchouVisualization(args.data)

    # Run in the specified mode
    if args.mode == "dashboard":
        print(f"Starting dashboard on http://localhost:{args.port}")
        viz.run_dashboard(port=args.port)
    else:
        viz.export_html(output_dir=args.output)


if __name__ == "__main__":
    main()
