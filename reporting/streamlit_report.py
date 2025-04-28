import streamlit as st
import json
import os
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots


class KouchouVisualizationStreamlit:
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
                f"<b>{cluster['label']}</b><br>{arg['argument'].replace(r'(.{30})', r'$1<br />')}"
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
            title=f"Cluster Visualization (Level {target_level})",
            xaxis=dict(title="", showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(title="", showgrid=False, zeroline=False, showticklabels=False),
            showlegend=True,
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
            ),
            margin=dict(l=20, r=20, t=60, b=20),
            hovermode="closest",
            height=600,
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
                height=600,
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
                f"<b>{cluster['label']}</b><br>{arg['argument'].replace(r'(.{30})', r'$1<br />')}"
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
            title=f"Dense Clusters Visualization (Density ≤ {max_density}%, Size ≥ {min_value})",
            xaxis=dict(title="", showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(title="", showgrid=False, zeroline=False, showticklabels=False),
            showlegend=True,
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
            ),
            margin=dict(l=20, r=20, t=60, b=20),
            hovermode="closest",
            height=600,
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
            height=600,
        )

        return fig


def main():
    st.set_page_config(
        page_title="Kouchou AI Visualization", page_icon="📊", layout="wide"
    )

    # Sidebar for file upload
    st.sidebar.title("Kouchou AI Visualization")

    # File upload
    uploaded_file = st.sidebar.file_uploader("Upload JSON data file", type=["json"])

    if uploaded_file is not None:
        # Save the uploaded file temporarily
        with open("temp_data.json", "wb") as f:
            f.write(uploaded_file.getvalue())

        # Create visualization object
        viz = KouchouVisualizationStreamlit("temp_data.json")

        # Display overview
        st.header("Report Overview")
        st.text_area("Overview", viz.overview, height=200)

        # Visualization type selection
        st.sidebar.header("Visualization Settings")
        viz_type = st.sidebar.radio(
            "Visualization Type", ["Scatter (All)", "Scatter (Dense Groups)", "Treemap"]
        )

        # Show cluster labels option
        show_labels = st.sidebar.checkbox("Show Cluster Labels", value=True)

        # Dense cluster settings
        if viz_type == "Scatter (Dense Groups)":
            st.sidebar.subheader("Dense Cluster Settings")
            max_density = st.sidebar.slider(
                "Max Density Percentile",
                min_value=5,
                max_value=100,
                value=25,
                step=5,
                help="Show only clusters with density rank percentile below this value",
            )
            min_value = st.sidebar.slider(
                "Min Cluster Size",
                min_value=1,
                max_value=10,
                value=3,
                step=1,
                help="Show only clusters with at least this many arguments",
            )

        # Treemap settings
        if viz_type == "Treemap":
            st.sidebar.subheader("Treemap Settings")

            # Store current treemap level in session state
            if "treemap_level" not in st.session_state:
                st.session_state.treemap_level = "all"
                st.session_state.treemap_history = ["all"]

            # Back button
            if len(st.session_state.treemap_history) > 1:
                if st.sidebar.button("Back to Parent"):
                    # Remove current level from history
                    st.session_state.treemap_history.pop()
                    # Set current level to the last item in history
                    st.session_state.treemap_level = st.session_state.treemap_history[
                        -1
                    ]

            # Show current level
            current_level_display = "All Clusters"
            if st.session_state.treemap_level != "all":
                for cluster in viz.clusters:
                    if cluster["id"] == st.session_state.treemap_level:
                        current_level_display = (
                            f"{cluster['label']} (ID: {st.session_state.treemap_level})"
                        )
                        break

            st.sidebar.text(f"Current Level: {current_level_display}")

        # Display the selected visualization
        st.header("Visualization")

        if viz_type == "Scatter (All)":
            fig = viz.create_scatter_chart(target_level=1, show_labels=show_labels)
            st.plotly_chart(fig, use_container_width=True)

        elif viz_type == "Scatter (Dense Groups)":
            fig = viz.create_scatter_dense(
                max_density=max_density, min_value=min_value, show_labels=show_labels
            )
            st.plotly_chart(fig, use_container_width=True)

        elif viz_type == "Treemap":
            fig = viz.create_treemap(root_level=st.session_state.treemap_level)

            # Handle treemap clicks for navigation
            selected_points = plotly_events(fig, click_event=True, override_height=600)
            if selected_points:
                clicked_id = selected_points[0].get("pointNumber")
                if clicked_id is not None:
                    # Get the ID of the clicked node
                    clicked_label = fig.data[0].labels[clicked_id]

                    # Only navigate if it's a cluster (not 'All')
                    if clicked_label != "All":
                        # Add to history and update current level
                        st.session_state.treemap_level = clicked_label
                        if clicked_label not in st.session_state.treemap_history:
                            st.session_state.treemap_history.append(clicked_label)

                        # Force a rerun to update the visualization
                        st.experimental_rerun()

            st.plotly_chart(fig, use_container_width=True)

        # Export functionality
        st.sidebar.header("Export")
        if st.sidebar.button("Export All Visualizations"):
            # Create output directory
            output_dir = "kouchou_output"
            os.makedirs(output_dir, exist_ok=True)

            # Export all visualizations
            scatter_fig = viz.create_scatter_chart(target_level=1)
            scatter_fig.write_html(os.path.join(output_dir, "scatter_all.html"))

            dense_fig = viz.create_scatter_dense()
            dense_fig.write_html(os.path.join(output_dir, "scatter_dense.html"))

            treemap_fig = viz.create_treemap()
            treemap_fig.write_html(os.path.join(output_dir, "treemap.html"))

            # Create overview HTML
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
                        <div class="overview">{viz.overview}</div>  
                    </div>  
                </body>  
                </html>  
                """
                )

            st.sidebar.success(f"Visualizations exported to {output_dir}/")
    else:
        # Display instructions when no file is uploaded
        st.info("Please upload a JSON data file to begin visualization.")
        st.markdown(
            """  
        ### Expected JSON Format  
          
        The uploaded JSON file should contain:  
          
        - `arguments`: Array of opinion arguments with coordinates  
        - `clusters`: Array of hierarchical clusters  
        - `overview`: Text summary of the analysis  
          
        This visualization tool replicates the functionality of the original Next.js visualization component in the Kouchou AI project.  
        """
        )


# Add the plotly_events function for handling treemap clicks
def plotly_events(
    fig, click_event=True, hover_event=False, select_event=False, override_height=None
):
    """
    Custom implementation of streamlit-plotly-events for handling treemap clicks.
    Returns selected points when user interacts with the plot.
    """
    import uuid
    import json
    from streamlit.components.v1 import html

    # Generate a unique ID for this chart
    chart_id = f"chart_{uuid.uuid4().hex}"

    # Create the JavaScript to handle events
    js_code = f"""  
    <script type="text/javascript">  
        var chart = document.getElementById('{chart_id}');  
        chart.on('plotly_click', function(data) {{  
            var points = data.points.map(function(point) {{  
                return {{  
                    'pointNumber': point.pointNumber,  
                    'curveNumber': point.curveNumber,  
                    'customdata': point.customdata  
                }};  
            }});  
            window.parent.postMessage({{  
                'type': 'streamlit:plotly_click',  
                'points': points  
            }}, "*");  
        }});  
    </script>  
    """

    # Set the height of the chart
    height = override_height if override_height else fig.layout.height

    # Render the chart and JavaScript
    html_str = f"""  
    <div id="{chart_id}" style="height: {height}px;"></div>  
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>  
    <script type="text/javascript">  
        var data = {json.dumps(fig.data, cls=plotly.utils.PlotlyJSONEncoder)};  
        var layout = {json.dumps(fig.layout, cls=plotly.utils.PlotlyJSONEncoder)};  
        Plotly.newPlot('{chart_id}', data, layout, {{responsive: true}});  
        {js_code}  
    </script>  
    """

    # Use streamlit's html component to render
    html(html_str, height=height)

    # Create a placeholder for the selected points
    result = st.empty()

    # Return any selected points from session state
    if "plotly_selected_points" in st.session_state:
        selected_points = st.session_state.plotly_selected_points
        # Clear the selection after retrieving it
        del st.session_state.plotly_selected_points
        return selected_points

    return []


if __name__ == "__main__":
    main()
