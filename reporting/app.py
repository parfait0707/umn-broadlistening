import streamlit as st
import json
import os
import re
import pandas as pd
import plotly.graph_objects as go
import streamlit.components.v1 as components
import uuid
import subprocess


class KouchouVisualizationStreamlit:
    def __init__(self, data_path, comments_path=None):
        """Initialize the visualization with data from a JSON file."""
        with open(data_path, "r", encoding="utf-8") as f:
            self.result = json.load(f)

        self.arguments = self.result.get("arguments", [])
        self.clusters = self.result.get("clusters", [])
        self.overview = self.result.get("overview", "")

        # Load comments data if available
        self.comments_df = None
        if comments_path and os.path.exists(comments_path):
            try:
                self.comments_df = pd.read_csv(comments_path, encoding="utf-8")
            except Exception as e:
                st.warning(f"Could not load comments file: {e}")

        # Define soft colors for clusters
        self.soft_colors = [
            "#7ac943", "#3fa9f5", "#ff7997", "#e0dd02", "#d6410f",
            "#b39647", "#7cccc3", "#a147e6", "#ff6b6b", "#4ecdc4",
            # ... additional colors ...
        ]

        # Create color map for all clusters
        self.cluster_color_map = {}
        level1 = [c for c in self.clusters if c.get("level") == 1]
        for i, cluster in enumerate(level1):
            self.cluster_color_map[cluster["id"]] = self.soft_colors[i % len(self.soft_colors)]
        for cluster in self.clusters:
            if cluster.get("level", 0) > 1 and cluster.get("parent"):
                parent_base = cluster["parent"].split("-")[0]
                if parent_base in self.cluster_color_map:
                    self.cluster_color_map[cluster["id"]] = self.cluster_color_map[parent_base]

    def get_dense_clusters(self, max_density=25, min_value=3):
        """Filter clusters by density and minimum value."""
        if not self.clusters:
            return [], True
        max_level = max(c.get("level", 0) for c in self.clusters)
        dense = [
            c for c in self.clusters
            if c.get("level") == max_level
            and c.get("density_rank_percentile", 100) <= max_density
            and c.get("value", 0) >= min_value
        ]
        return dense, len(dense) == 0

    def create_scatter_chart(self, target_level=1, show_labels=True):
        fig = go.Figure()
        for cluster in [c for c in self.clusters if c.get("level") == target_level]:
            args = [a for a in self.arguments if cluster["id"] in a.get("cluster_ids", [])]
            if not args:
                continue
            x = [a.get("x", 0) for a in args]
            y = [a.get("y", 0) for a in args]
            texts = []
            for a in args:
                text = a.get("argument", "")
                text = re.sub(r"(.{30})", r"\1<br />", text)
                texts.append(f"<b>{cluster['label']}</b><br>{text}")
            color = self.cluster_color_map.get(cluster["id"], "#cccccc")

            fig.add_trace(go.Scatter(
                x=x, y=y,
                mode="markers",
                marker=dict(color=color, size=8),
                text=texts,
                hoverinfo="text",
                name=cluster['label']
            ))

            if show_labels:
                cx = sum(x) / len(x)
                cy = sum(y) / len(y)
                fig.add_annotation(
                    x=cx, y=cy,
                    text=cluster['label'],
                    showarrow=False,
                    font=dict(color="white", size=12, family="Arial"),
                    align="center",
                    bgcolor=color,
                    borderpad=4,
                    opacity=0.9
                )

        fig.update_layout(
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=12)),
            margin=dict(l=20, r=20, t=20, b=20),
            hovermode="closest",
            height=600
        )
        return fig

    def create_scatter_dense(self, max_density=25, min_value=3, show_labels=True):
        dense, empty = self.get_dense_clusters(max_density, min_value)
        if empty:
            fig = go.Figure()
            fig.update_layout(
                annotations=[
                    dict(text="No clusters meet the density and size criteria",
                         showarrow=False, xref="paper", yref="paper", x=0.5, y=0.5)
                ],
                margin=dict(l=20, r=20, t=20, b=20),
                height=600
            )
            return fig, True

        fig = go.Figure()
        for i, cluster in enumerate(dense):
            args = [a for a in self.arguments if cluster["id"] in a.get("cluster_ids", [])]
            if not args:
                continue
            x = [a.get("x", 0) for a in args]
            y = [a.get("y", 0) for a in args]
            text_list = []
            for a in args:
                txt = re.sub(r"(.{30})", r"\1<br />", a.get("argument", ""))
                text_list.append(txt)
            color = self.soft_colors[i % len(self.soft_colors)]

            fig.add_trace(go.Scatter(
                x=x, y=y,
                mode="markers",
                marker=dict(color=color, size=8),
                text=text_list,
                hoverinfo="text",
                name=cluster['label']
            ))

            if show_labels:
                cx = sum(x) / len(x)
                cy = sum(y) / len(y)
                fig.add_annotation(
                    x=cx, y=cy,
                    text=cluster['label'],
                    showarrow=False,
                    font=dict(color="white", size=12, family="Arial"),
                    align="center",
                    bgcolor=color,
                    borderpad=4,
                    opacity=0.9
                )

        fig.update_layout(
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=12)),
            margin=dict(l=20, r=20, t=20, b=20),
            hovermode="closest",
            height=600
        )
        return fig, False

    def create_treemap(self, root_level="0"):
        ids, labels, parents, values, customdata = [], [], [], [], []
        for c in self.clusters:
            ids.append(c['id'])
            lbl = re.sub(r"(.{15})", r"\1<br />", c['label'])
            labels.append(lbl)
            parents.append(c.get('parent', '') if c.get('level', 1) > 1 else '')
            values.append(c.get('value', 0))
            customdata.append(re.sub(r"(.{15})", r"\1<br />", c.get('takeaway', '')))
        if '0' not in ids:
            ids.insert(0, '0')
            labels.insert(0, 'All')
            parents.insert(0, '')
            total = sum(v for c, v in zip(self.clusters, values) if c.get('level') == 1)
            values.insert(0, total)
            customdata.insert(0, 'All Clusters')

        fig = go.Figure(go.Treemap(
            ids=ids,
            labels=labels,
            parents=parents,
            values=values,
            hovertemplate="%{label}<br>%{value:,}件",
            texttemplate="%{label}<br>%{value:,}件",
            textfont=dict(size=14, family="Arial"),
            customdata=customdata,
            branchvalues="total",
            maxdepth=2,
            marker=dict(colors=[self.cluster_color_map.get(i.split('-')[0], '#cccccc') for i in ids])
        ))

        fig.update_layout(
            margin=dict(l=10, r=10, t=20, b=10),
            height=600
        )
        return fig

    def display_comments_table(self, cluster_id=None):
        if self.comments_df is None:
            st.warning("Comments data is not available.")
            return
        df = self.comments_df.copy()
        if cluster_id:
            df = df[df['category_id'] == cluster_id]

        st.subheader("Comments and Arguments")
        column_config = {
            'category': st.column_config.TextColumn('Category'),
            'argument': st.column_config.TextColumn('Extracted Argument'),
            'original-comment': st.column_config.TextColumn('Original Comment', width="large"),
        }
        st.dataframe(df, column_config=column_config, use_container_width=True, height=400, hide_index=True)
        st.caption(f"Showing {len(df)} comments{' for cluster '+cluster_id if cluster_id else ' total'}")


def find_project_folders():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    outputs = os.path.join(root, "outputs")
    if not os.path.exists(outputs):
        return []
    return [
        d for d in os.listdir(outputs)
        if os.path.isdir(os.path.join(outputs, d))
        and os.path.exists(os.path.join(outputs, d, 'hierarchical_result.json'))
    ]


def load_project_data(project_name):
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    proj = os.path.join(root, 'outputs', project_name)
    res = os.path.join(proj, 'hierarchical_result.json')
    com = os.path.join(proj, 'final_result_with_comments.csv')
    if not os.path.exists(res):
        st.error(f"hierarchical_result.json not found for {project_name}")
        return None, None
    if not os.path.exists(com):
        st.warning(f"comments CSV not found for {project_name}")
        com = None
    return res, com


def main():
    st.set_page_config(page_title="Kouchou AI Visualization", page_icon="📊", layout="wide")
    st.sidebar.title("Kouchou AI Visualization")
    projects = find_project_folders()
    mode = 'Upload New Data' if not projects else st.sidebar.radio(
        'Choose a mode', ['Select Existing Project', 'Upload New Data'])
    viz = None

    if mode == 'Select Existing Project':
        sel = st.sidebar.selectbox('Select a project', projects)
        if sel:
            res, com = load_project_data(sel)
            if res:
                viz = KouchouVisualizationStreamlit(res, com)
                st.sidebar.success(f"Loaded project: {sel}")
    else:
        st.sidebar.header("Upload Data")
        raw_file = st.sidebar.file_uploader("Upload Preprocessing CSV (UTF-8)", type=['csv'])
        
        # --- Configuration File Upload & Selection ---
        # Ensure configs folder exists at root/configs
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        configs_dir = os.path.join(root_dir, "configs")
        if not os.path.exists(configs_dir):
            os.makedirs(configs_dir)
        
        # Allow user to upload a config file manually
        uploaded_config = st.sidebar.file_uploader("Upload Configuration File (JSON) if the configuration file you want to use isn’t available under Select Configuration File.", type=["json"])
        if uploaded_config is not None:
            config_save_path = os.path.join(configs_dir, uploaded_config.name)
            with open(config_save_path, "wb") as f:
                f.write(uploaded_config.getbuffer())
            st.sidebar.success(f"Configuration file '{uploaded_config.name}' uploaded and saved.")
        
        # List available config files from configs folder
        config_files = [f for f in os.listdir(configs_dir) if f.endswith(".json")]
        if config_files:
            selected_config = st.sidebar.selectbox("Select Configuration File", config_files)
            config_path = os.path.join("configs", selected_config)
        else:
            st.sidebar.error("No configuration files found in 'configs' folder.")
            config_path = None
        # --- End Configuration ---

        if raw_file and config_path:
            try:
                df = pd.read_csv(raw_file, encoding="utf-8")
            except Exception as e:
                st.error(f"Failed to read CSV: {e}")
            else:
                # ユーザーにCSVの列名一覧から解析対象カラムを選択させる
                selected_col = st.sidebar.selectbox(
                    "Select Analysis Target Column", 
                    df.columns.tolist(), 
                    index=(df.columns.get_loc("comment-body") if "comment-body" in df.columns else 0)
                )
                # 「実行」ボタン押下後に後続の処理を実行
                if st.sidebar.button("Run"):
                    # 指定された解析対象カラムが "comment-body" でなければリネームする
                    if selected_col != "comment-body":
                        df = df.rename(columns={selected_col: "comment-body"})
                    # "comment-id"カラムが存在しなければ連番を作成する
                    if "comment-id" not in df.columns:
                        df["comment-id"] = range(1, len(df) + 1)
                    # 前処理用のCSVとしてroot直下に保存
                    df.to_csv("raw_data.csv", index=False, encoding="utf-8")
                    st.info("Raw CSV processed and saved as 'raw_data.csv'. Running preprocessing...")
                    cmd = ["python", "hierarchical_main.py", config_path]
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    if result.returncode != 0:
                        st.error(f"Preprocessing failed:\n{result.stderr}")
                    else:
                        st.success("Preprocessing completed successfully.")
                        projects = find_project_folders()
                        if projects:
                            outputs_dir = os.path.join(root_dir, "outputs")
                            latest_project = max(projects, key=lambda proj: os.path.getmtime(os.path.join(outputs_dir, proj)))
                            res, com = load_project_data(latest_project)
                            if res:
                                viz = KouchouVisualizationStreamlit(res, com)
                                st.sidebar.success(f"Loaded project: {latest_project}")

    if viz:
        # Report Overview
        st.header("Report Overview")
        st.text_area("Overview", viz.overview, height=200)

        # Visualization Settings
        st.sidebar.header("Visualization Settings")
        choice = st.sidebar.radio('Visualization Type',
                                   ['Scatter (All)', 'Scatter (Dense Groups)', 'Treemap', 'Comments Table'])
        show_labels = st.sidebar.checkbox('Show Cluster Labels', True)

        if choice == 'Scatter (Dense Groups)':
            max_d = st.sidebar.slider('Max Density Percentile', 5, 100, 25, 5)
            min_v = st.sidebar.slider('Min Cluster Size', 1, 10, 3, 1)
            st.sidebar.markdown("**Max Density Percentile:**  \n"
                                "This parameter filters clusters by selecting those whose density percentile is less than or equal to the specified value. Lower values will display only the densest clusters.")
            st.sidebar.markdown("**Min Cluster Size:**  \n"
                                "This parameter sets the minimum number of elements required for a cluster to be included. Higher values will exclude smaller clusters.")

        if choice == 'Treemap':
            if 'treemap_level' not in st.session_state:
                st.session_state.treemap_level = '0'
                st.session_state.treemap_history = ['0']
            if len(st.session_state.treemap_history) > 1:
                if st.sidebar.button('Back to Parent'):
                    st.session_state.treemap_history.pop()
                    st.session_state.treemap_level = st.session_state.treemap_history[-1]
            lvl = 'All Clusters'
            if st.session_state.treemap_level != '0':
                for c in viz.clusters:
                    if c['id'] == st.session_state.treemap_level:
                        lvl = f"{c['label']} (ID:{c['id']})"
                        break
            st.sidebar.text(f"Current Level: {lvl}")

        if choice == 'Comments Table':
            opts = [('All Clusters', None)] + [
                (f"{c['label']} (ID:{c['id']})", c['id'])
                for c in viz.clusters if c.get('level') == 1
            ]
            idx = st.sidebar.selectbox('Filter by Cluster', range(len(opts)), format_func=lambda i: opts[i][0])
            selected_id = opts[idx][1]

        # Render visualization with dynamic headers
        if choice == 'Scatter (All)':
            st.header("Cluster Visualization (Level 1)")
            fig = viz.create_scatter_chart(show_labels=show_labels)
            st.plotly_chart(fig, use_container_width=True)

        elif choice == 'Scatter (Dense Groups)':
            st.header(f"Dense Clusters Visualization (Density ≤ {max_d}%, Size ≥ {min_v})")
            fig, _ = viz.create_scatter_dense(max_d, min_v, show_labels)
            st.plotly_chart(fig, use_container_width=True)

        elif choice == 'Treemap':
            st.header("Hierarchical Cluster Visualization")
            fig = viz.create_treemap(st.session_state.treemap_level)
            st.plotly_chart(fig, use_container_width=True)

        elif choice == 'Comments Table':
            st.header("Comments and Arguments")
            viz.display_comments_table(selected_id)

        # Export
        st.sidebar.header("Export")
        if st.sidebar.button("Export All Visualizations"):
            out = 'kouchou_output'
            os.makedirs(out, exist_ok=True)
            viz.create_scatter_chart().write_html(f"{out}/scatter_all.html")
            viz.create_scatter_dense()[0].write_html(f"{out}/scatter_dense.html")
            viz.create_treemap().write_html(f"{out}/treemap.html")
            with open(f"{out}/overview.html", "w", encoding="utf-8") as f:
                f.write(f"<h1>Overview</h1><p>{viz.overview}</p>")
            if viz.comments_df is not None:
                viz.comments_df.to_csv(f"{out}/comments.csv", index=False)
            st.sidebar.success(f"Exported to {out}/")
    else:
        st.info("Please select or upload data to begin.")
        st.markdown(
            """
### Expected Data Format
- `arguments`: list of args with x,y coordinates
- `clusters`: hierarchical cluster info
- `overview`: text summary

Optional CSV (UTF-8 encoded):
- `category_id`, `argument`, `original-comment`
"""
        )


def plotly_events(fig, **kwargs):
    # Simplified placeholder; full interactive click handling requires custom components
    st.warning("Interactive treemap clicks are not supported in this simplified version.")
    return []


if __name__ == "__main__":
    main()
