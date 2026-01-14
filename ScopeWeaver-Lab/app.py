"""

TODO add back labels to multivariate flows (and add different metrics as well)
TODO reinstate markdown and non markdown render
TODO add export for database

ScopeWeaver Lab - Comparative Analytics Dashboard
=================================================
A modular Streamlit application for analyzing, comparing, and visualizing 
LLM test results. Designed for the ScopeWeaver testing suite.

Author: URAI ScopeWeaver Team
Date: 08-01-2026
Version: 0.0003 (Sankey Swap & Matrix Fixes)

Modules:
1. Configuration & Styling: CSS injection and global constants.
2. DataManager: Handles file I/O, JSON parsing, Ground Truth mapping, and DataFrame construction.
3. Visualizer: Factory for Plotly charts (Sankey, ParCoords, Scatter).
4. UIComponents: Renders Streamlit widgets (Tables, Diffs, Layouts).
5. Main: Application controller.
"""

import streamlit as st
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go
import os
import glob
import re
import difflib
from html import escape

# ==========================================
# 1. CONFIGURATION & STYLING LAYER
# ==========================================
st.set_page_config(
    page_title="ScopeWeaver Lab | Comparative Analytics",
    layout="wide",
    page_icon="🧪",
    initial_sidebar_state="expanded"
)

# --- Global Constants ---
BASE_TEST_DIR = r"ScopeWeaver-Lab\tests" 
TEST_CASES_FILE = r"ScopeWeaver-Lab\v1_test_cases.json" 
CURRENT_API_MODEL = "gemma-3-27b-it" 

# --- Visual Styling ---
FONT_CONFIG = dict(family="Inter, sans-serif", size=14, color="#ffffff") # Global White Text

# --- Semantic Color Palette ---
COLOR_PASS = "#00CC96"  # Teal Green
COLOR_FAIL = "#EF553B"  # Red Orange
RUN_COLORS = px.colors.qualitative.Bold 

# --- Custom CSS ---
st.markdown("""
<style>
    /* Diff Container Styling */
    .diff-container {
        font-family: 'Consolas', 'Monaco', monospace;
        font-size: 14px;
        border: 1px solid #444;
        border-radius: 8px;
        background-color: #2b2b2b;
        color: #eee;
        padding: 15px;
        overflow-x: auto;
    }
    .diff-line { display: block; white-space: pre-wrap; margin-bottom: 2px; }
    .diff-add { background-color: #064e3b; color: #a7f3d0; } 
    .diff-del { background-color: #7f1d1d; color: #fecaca; text-decoration: line-through; opacity: 0.8; }
    .diff-header { font-weight: bold; color: #aaa; margin-bottom: 10px; border-bottom: 1px solid #555; padding-bottom: 5px; }
    
    /* API Badge Styling */
    .api-badge {
        background-color: #7c3aed;
        color: white;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 0.8em;
        font-weight: bold;
        font-family: 'Inter', sans-serif;
        border: 1px solid #8b5cf6;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATA MANAGER (Model Layer)
# ==========================================
class DataManager:
    """Handles all data ingestion and transformation logic."""

    @staticmethod
    def load_ground_truth(filepath):
        """Loads v1_test_cases.json for accurate Expected Tool mapping."""
        mapping = {}
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    raw = json.load(f)
                    for item in raw:
                        if 'id' in item:
                            exp_json = item.get('expected_json', {})
                            sys_call = exp_json.get('systemCall', {})
                            func = sys_call.get('Function used', None)
                            
                            # R3: Catch explicit error expectations
                            if not func and 'error_id' in exp_json:
                                func = "ErrorExpected"
                            
                            mapping[item['id']] = func or "Unknown"
            except Exception as e:
                st.error(f"Error loading Ground Truth ({filepath}): {e}")
        return mapping

    @staticmethod
    def get_available_tests(base_dir):
        if not os.path.exists(base_dir): return []
        subdirs = [f.path for f in os.scandir(base_dir) if f.is_dir()]
        subdirs.sort(key=lambda x: os.path.basename(x))
        return subdirs

    @staticmethod
    def load_single_run(folder_path):
        run_id = os.path.basename(folder_path)
        json_files = glob.glob(os.path.join(folder_path, "*.json"))
        md_files = glob.glob(os.path.join(folder_path, "*.md"))
        
        data = []
        prompt = "No system prompt found."
        
        if json_files:
            try:
                with open(json_files[0], "r", encoding='utf-8') as f:
                    data = json.load(f)
            except Exception as e:
                st.error(f"Critical: Error reading JSON in {run_id}: {e}")

        if md_files:
            try:
                with open(md_files[0], "r", encoding='utf-8') as f:
                    prompt = f.read()
            except Exception: pass
                
        return {"run_id": run_id, "data": data, "prompt": prompt}

    @staticmethod
    def process_run_data(run_payload, ground_truth_map):
        """Transforms raw JSON into a flat Pandas DataFrame with Ground Truth."""
        raw_data = run_payload['data']
        run_id = run_payload['run_id']
        
        if not raw_data: return pd.DataFrame()

        rows = []
        for d in raw_data:
            errs = d.get('errors', {})
            checks = errs.get('checks', {})
            perf = d.get('perf', {})
            in_met = d.get('input_metrics', {})
            out_met = d.get('output_metrics', {})
            cost = d.get('cost', {})

            actual_tool = DataManager._extract_actual_tool(d)
            test_id = d.get("id")
            expected_tool = ground_truth_map.get(test_id, "Unknown")
            primary_err = DataManager._determine_primary_error(d)

            row = {
                "run_id": run_id,
                "id": test_id,
                "category": d.get("category", "Unknown"),
                "type": d.get("type", "N/A"),
                "rank": d.get("rank", "N/A"),
                "status": "PASS" if d.get("passed") else "FAIL",
                
                "actual_tool": actual_tool,
                "expected_tool": expected_tool,
                "primary_error": primary_err,

                # Sankey Logic Flags
                "check_json": 1 if errs.get('is_valid_json') else 0,
                "check_schema": 1 if errs.get('is_valid_schema') else 0,
                "check_hallucination": 1 if checks.get('no_hallucination') else 0,
                "check_function": 1 if checks.get('function_match') else 0,
                "check_param": 1 if checks.get('param_match') else 0,

                # Metrics
                "latency_ms": perf.get("latency", 0),
                "total_tokens": perf.get("total_tokens", 0),
                "total_cost": cost.get("total_cost", 0.0),
                "input_chars": in_met.get("char_count", 0),
                "input_words": in_met.get("word_count", 0),
                "input_complexity_pct": in_met.get("special_char_percent", 0),
                "input_tokens": in_met.get("token_count", 0),
                "output_tokens": out_met.get("token_count", 0),
                "full_record": d 
            }
            rows.append(row)
        return pd.DataFrame(rows)

    @staticmethod
    def _extract_actual_tool(d):
        try:
            raw = d.get('raw_output', '')
            match = re.search(r'\{.*\}', raw, re.DOTALL)
            if match:
                obj = json.loads(match.group(0))
                return obj.get('systemCall', {}).get('Function used', 'Schema Error')
            else:
                return "No JSON"
        except: 
            return "Crash"

    @staticmethod
    def _determine_primary_error(d):
        errs = d.get('errors', {})
        checks = errs.get('checks', {})
        if d.get('passed'): return "None"
        if not errs.get('is_valid_json'): return "Invalid JSON"
        if not checks.get('no_hallucination'): return "Hallucination"
        if not checks.get('function_match'): return "Wrong Tool"
        if not checks.get('param_match'): return "Wrong Param"
        return "Unknown Fail"

# ==========================================
# 3. VISUALIZATION ENGINE
# ==========================================
class Visualizer:
    
    # --------------------------------------------------------
    # HELPER: CSS Text Styling (Restored for White + Border)
    # --------------------------------------------------------
    @staticmethod
    def _style_label(text):
        """
        Applies HTML styling to create white text with a black outline (shadow).
        This ensures text is white even on light background nodes.
        """
        style = (
            "color: white; "
            "font-weight: bold; "
            "text-shadow: "
            "-1px -1px 0 #000, "
            "1px -1px 0 #000, "
            "-1px 1px 0 #000, "
            "1px 1px 0 #000;"
        )
        return f'<span style="{style}">{text}</span>'

    # --------------------------------------------------------
    # [R2] COMPARATIVE VIZ: Small Multiples of DETAILED PIPELINE
    # --------------------------------------------------------
    @staticmethod
    def plot_pipeline_sankey_small_multiples(df):
        runs = df['run_id'].unique()
        cols = st.columns(len(runs))
        
        for i, run_id in enumerate(runs):
            run_df = df[df['run_id'] == run_id]
            with cols[i]:
                st.markdown(f"**{run_id}** Failure Pipeline")
                if run_df.empty:
                    st.warning("No data")
                    continue
                # Note: We apply the styling here too for consistency
                Visualizer._render_pipeline_sankey_logic(
                    run_df, height=350, unique_key=f"pipe_sm_{run_id}_{i}"
                )

    # --------------------------------------------------------
    # [R2] SINGLE INSPECTOR: Hierarchical Sankey
    # --------------------------------------------------------
    @staticmethod
    def plot_hierarchical_sankey_single(df, unique_key="hier_single"):
        st.markdown("##### ☀️ Hierarchical Flow")
        Visualizer._render_hierarchical_sankey_logic(df, unique_key=unique_key, height=500)

    # --------------------------------------------------------
    # [R1.5 + R3] CONFUSION MATRIX SMALL MULTIPLES
    # --------------------------------------------------------
    @staticmethod
    def plot_confusion_matrix_small_multiples(df):
        runs = df['run_id'].unique()
        cols = st.columns(len(runs))
        
        all_actual = set(df['actual_tool'].unique())
        all_expected = set(df['expected_tool'].unique())
        global_labels = sorted(list(all_actual.union(all_expected)))

        for i, run_id in enumerate(runs):
            run_df = df[df['run_id'] == run_id]
            with cols[i]:
                st.markdown(f"**{run_id}** Confusion")
                if run_df.empty:
                    st.caption("No data.")
                    continue
                
                pivot = pd.crosstab(run_df['actual_tool'], run_df['expected_tool'])
                pivot = pivot.reindex(index=global_labels, columns=global_labels, fill_value=0)
                
                fig = px.imshow(
                    pivot, text_auto=True, color_continuous_scale="Blues",
                    labels=dict(x="Expected Tool", y="Actual Tool", color="Count")
                )
                fig.update_layout(
                    font=FONT_CONFIG, width=400, height=400,
                    margin=dict(l=0, r=0, t=0, b=0),
                    coloraxis_showscale=False
                )
                st.plotly_chart(fig, use_container_width=True, key=f"conf_mat_{run_id}_{i}")

    # --------------------------------------------------------
    # HELPER: Detailed Pipeline Logic
    # --------------------------------------------------------
    @staticmethod
    def _render_pipeline_sankey_logic(df, height=500, unique_key="pipeline"):
        if df.empty: return

        total_c = len(df)
        valid_json = df['check_json'].sum(); inv_json = total_c - valid_json
        df_j = df[df['check_json']==1]
        valid_sch = df_j['check_schema'].sum(); inv_sch = len(df_j) - valid_sch
        df_s = df_j[df_j['check_schema']==1]
        no_hal = df_s['check_hallucination'].sum(); hal = len(df_s) - no_hal
        df_h = df_s[df_s['check_hallucination']==1]
        val_func = df_h['check_function'].sum(); inv_func = len(df_h) - val_func
        df_f = df_h[df_h['check_function']==1]
        val_p = df_f['check_param'].sum(); inv_p = len(df_f) - val_p
        
        raw_labels = ["Start", "Bad JSON", "JSON OK", "Bad Schema", "Schema OK", "Hallucination", "Tool Valid", "Wrong Tool", "Tool OK", "Wrong Param", "PERFECT"]
        # Apply CSS Styling
        styled_labels = [Visualizer._style_label(l) for l in raw_labels]

        n_colors = ["#333", COLOR_FAIL, COLOR_PASS, COLOR_FAIL, COLOR_PASS, COLOR_FAIL, COLOR_PASS, COLOR_FAIL, COLOR_PASS, COLOR_FAIL, COLOR_PASS]
        l_colors = ["rgba(239, 85, 59, 0.4)", "rgba(0, 204, 150, 0.4)"] * 5

        fig = go.Figure(data=[go.Sankey(
            node = dict(
                pad=15, thickness=20, 
                line=dict(color="black", width=0.5), 
                label=styled_labels, # <--- Styled
                color=n_colors
            ),
            link = dict(
                source = [0, 0, 2, 2, 4, 4, 6, 6, 8, 8],
                target = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                value  = [inv_json, valid_json, inv_sch, valid_sch, hal, no_hal, inv_func, val_func, inv_p, val_p],
                color  = l_colors
            )
        )])
        fig.update_layout(height=height, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True, key=unique_key)

    # --------------------------------------------------------
    # HELPER: Hierarchical Logic (FIXED for White Text)
    # --------------------------------------------------------
    @staticmethod
    def _render_hierarchical_sankey_logic(df, unique_key, height=500):
        s_labels_raw = []
        node_colors = [] 
        label_map = {}
        
        def get_idx(name):
            if name not in label_map:
                label_map[name] = len(label_map)
                s_labels_raw.append(name)
                # Assign colors based on node name content
                if "PASS" in name: node_colors.append(COLOR_PASS)
                elif "FAIL" in name: node_colors.append(COLOR_FAIL)
                else: node_colors.append("#636EFA") 
            return label_map[name]

        s_src, s_tgt, s_val, s_col = [], [], [], []
        
        flow_df = df.groupby(['category', 'type', 'rank', 'status']).size().reset_index(name='count')
        
        for _, row in flow_df.iterrows():
            c = row['count']
            status = row['status']
            l_col = "rgba(152, 251, 152, 0.4)" if status == "PASS" else "rgba(239, 85, 59, 0.4)"
            
            i_cat = get_idx(f"{row['category']}")
            i_typ = get_idx(f"{row['type']}")
            i_rnk = get_idx(f"{row['rank']}")
            i_sts = get_idx(f"{status}")
            
            s_src.extend([i_cat, i_typ, i_rnk])
            s_tgt.extend([i_typ, i_rnk, i_sts])
            s_val.extend([c, c, c])
            s_col.extend([l_col, l_col, l_col])
        
        # FIX: Apply CSS Styling to Hierarchical labels
        styled_labels = [Visualizer._style_label(l) for l in s_labels_raw]

        fig = go.Figure(data=[go.Sankey(
            node=dict(
                pad=15, thickness=20, 
                line=dict(color="black", width=0.5), 
                label=styled_labels, # <--- Using styled labels with border
                color=node_colors    
            ),
            link=dict(source=s_src, target=s_tgt, value=s_val, color=s_col)
        )])
        fig.update_layout(height=height, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True, key=unique_key)

    @staticmethod
    def plot_input_explorer(df):
        st.markdown("##### 🔬 Input Feature Correlation")
        c1, c2, c3 = st.columns(3)
        with c1: x_axis = st.selectbox("X Axis", ["input_complexity_pct", "input_chars", "input_words", "input_tokens"], index=0)
        with c2: y_axis = st.selectbox("Y Axis", ["latency_ms", "total_tokens", "total_cost"], index=0)
        with c3: color_by = st.selectbox("Color By", ["run_id", "status", "category"], index=0)

        fig = px.scatter(
            df, x=x_axis, y=y_axis, color=color_by,
            symbol="status", opacity=0.8, size_max=15,
            hover_data=["id", "primary_error"],
            title=f"Correlation: {y_axis} vs {x_axis}",
            color_discrete_sequence=RUN_COLORS,
        )
        fig.update_layout(font=FONT_CONFIG, height=450)
        st.plotly_chart(fig, use_container_width=True, key="input_scatter_interactive")

    @staticmethod
    def plot_multivariate_flow(df):
        st.markdown("##### 🌊 Multivariate Metric Flow")
        runs = sorted(df['run_id'].unique())
        col_ctrl, col_info = st.columns([1, 2])
        
        with col_ctrl:
            focus_run = st.selectbox("🎯 Highlight Run (Focus Mode)", ["All"] + list(runs), index=0)
            
        df_plot = df.copy()
        if focus_run == "All":
            run_map = {rid: i+1 for i, rid in enumerate(runs)}
            df_plot['color_val'] = df_plot['run_id'].map(run_map)
            colorscale = 'Viridis'
            show_colorbar = True
        else:
            df_plot['color_val'] = df_plot['run_id'].apply(lambda x: 1 if x == focus_run else 0)
            colorscale = [[0.0, 'rgba(100,100,100,0.1)'], [1.0, '#00CC96']]
            show_colorbar = False

        dimensions = [
            dict(range=[0, df_plot['input_complexity_pct'].max()], label='Special Char %', values=df_plot['input_complexity_pct']),
            dict(range=[0, df_plot['input_tokens'].max()], label='Input Toks', values=df_plot['input_tokens']),
            dict(range=[0, df_plot['latency_ms'].max()], label='Latency (ms)', values=df_plot['latency_ms']),
            dict(range=[0, df_plot['total_cost'].max()], label='Cost ($)', values=df_plot['total_cost']),
        ]

        fig = go.Figure(data=go.Parcoords(
            line=dict(color=df_plot['color_val'], colorscale=colorscale, showscale=show_colorbar),
            dimensions=dimensions
        ))
        fig.update_layout(font=FONT_CONFIG, height=500, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True, key="input_parcoords_refined")

# ==========================================
# 4. UI COMPONENT LAYER
# ==========================================
class UIComponents:
    @staticmethod
    def render_rich_kpi_table(df):
        st.subheader("Comparison Summary")
        stats = df.groupby("run_id").agg(
            Total_Tests=('id', 'count'),
            Passed=('status', lambda x: (x == 'PASS').sum()),
            Avg_Latency=('latency_ms', 'mean'),
            Total_Cost=('total_cost', 'sum')
        ).reset_index()

        stats['Pass_Rate'] = stats['Passed'] / stats['Total_Tests']
        
        st.dataframe(
            stats,
            column_config={
                "Pass_Rate": st.column_config.ProgressColumn("Success Rate", min_value=0, max_value=1, format="%.1f%%"),
            },
            hide_index=True, width="stretch"
        )

        # [R1] Restored the Heatmap Breakdown Table
        with st.expander("🔻 Expand Detailed Breakdown (Category & Type)", expanded=True):
            cat_stats = df.groupby(["run_id", "category", "type"]).agg(
                Pass_Rate=('status', lambda x: (x == 'PASS').mean())
            ).reset_index()
            
            pivot = cat_stats.pivot(index=["category", "type"], columns="run_id", values="Pass_Rate")
            
            def discrete_style(row):
                styles = []
                max_val = row.max()
                winner_col = row[row == max_val].index[-1]
                colors = ["#8B0000", "#A52A2A", "#CD5C5C", "#F08080", "#E9967A", "#DAA520", "#BDB76B", "#9ACD32", "#32CD32", "#006400"]
                for col, val in row.items():
                    if pd.isna(val):
                        styles.append("")
                        continue
                    idx = int(val * 10) 
                    if idx >= 10: idx = 9
                    if idx < 0: idx = 0
                    bg = colors[idx]
                    text_col = "white" if idx < 5 or idx > 8 else "black"
                    style = f"background-color: {bg}; color: {text_col};"
                    if col == winner_col: style += "border: 2px solid #fff; font-weight: bold;"
                    styles.append(style)
                return styles

            st.dataframe(pivot.style.apply(discrete_style, axis=1).format("{:.1%}"), width="stretch")

    @staticmethod
    def render_error_artifact_inspector(df):
        st.markdown("### 🐞 Error Artifact Inspector")
        fails = df[df['status'] == "FAIL"]
        if fails.empty:
            st.success("🎉 No failures detected!")
            return

        run_ids = fails['run_id'].unique()
        for run_id in run_ids:
            with st.expander(f"🔴 Failures in {run_id}", expanded=True):
                run_fails = fails[fails['run_id'] == run_id]
                for idx, row in run_fails.iterrows():
                    label = f"**{row['id']}** ({row['category']}): {row['primary_error']} | Expected: `{row['expected_tool']}` vs Actual: `{row['actual_tool']}`"
                    st.markdown(label)
                    st.code(json.dumps(row['full_record'], indent=2), language='json')
                    st.markdown("---")

    @staticmethod
    def render_original_deep_dive(df):
        for idx, row in df.iterrows():
            rec = row['full_record']
            s_icon = "✅" if row['status'] == "PASS" else "❌"
            with st.expander(f"{s_icon} {row['id']} | {row['category']} | Latency: {row['latency_ms']:.2f}s", expanded=False):
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("**Output JSON:**")
                    st.code(rec.get('raw_output', ''), language='json')
                with c2:
                    st.markdown("**Error Log:**")
                    st.json(rec.get('errors', {}))
                    st.markdown("**Performance:**")
                    st.json(rec.get('perf', {}))

    @staticmethod
    def render_global_database(df):
        st.markdown("### 🗄️ Global Error Database")
        c1, c2, c3 = st.columns(3)
        with c1: f_runs = st.multiselect("Filter Run ID", df['run_id'].unique())
        with c2: f_status = st.multiselect("Filter Status", ["PASS", "FAIL"])
        with c3: f_error = st.multiselect("Filter Error Type", df['primary_error'].unique())

        dff = df.copy()
        if f_runs: dff = dff[dff['run_id'].isin(f_runs)]
        if f_status: dff = dff[dff['status'].isin(f_status)]
        if f_error: dff = dff[dff['primary_error'].isin(f_error)]
        
        # [R4] Restored Color Filtering Logic
        st.markdown("#### 🎨 Color Heatmap")
        color_mode = st.radio("Color Rows By:", ["None", "Status (Pass/Fail)", "Category", "Run ID"], horizontal=True)

        def color_logic(row):
            if color_mode == "Status (Pass/Fail)":
                return ['background-color: #450a0a; color: #fecaca'] * len(row) if row['status'] == "FAIL" else ['background-color: #064e3b; color: #a7f3d0'] * len(row)
            elif color_mode == "Category":
                val = hash(row['category']) % 360
                return [f'background-color: hsl({val}, 40%, 20%); color: white'] * len(row)
            elif color_mode == "Run ID":
                val = hash(row['run_id']) % 360
                return [f'background-color: hsl({val}, 60%, 25%); color: white'] * len(row)
            return [''] * len(row)

        disp_cols = ["run_id", "id", "status", "category", "type", "primary_error", "actual_tool", "expected_tool", "latency_ms"]
        st.dataframe(dff[disp_cols].style.apply(color_logic, axis=1).format({"latency_ms": "{:.2f}"}), height=600, width="stretch")

    @staticmethod
    def render_diff_view(prompts_dict):
        st.subheader("System Prompts & Configuration")
        runs = list(prompts_dict.keys())
        if len(runs) < 2:
            st.warning("Select 2+ runs to compare prompts.")
            if len(runs) == 1: st.code(prompts_dict[runs[0]])
            return

        diff_mode = st.radio("Diff Mode", ["Unified", "Side-by-Side"], horizontal=True)
        if diff_mode == "Side-by-Side":
            cols = st.columns(len(runs))
            for i, r in enumerate(runs):
                with cols[i]:
                    st.subheader(r)
                    st.code(prompts_dict[r])
        else:
            base, target = runs[0], runs[-1]
            a_lines = prompts_dict[base].splitlines()
            b_lines = prompts_dict[target].splitlines()
            matcher = difflib.SequenceMatcher(None, a_lines, b_lines)
            html = [f"<div class='diff-header'>Comparing: {base} ➝ {target}</div>"]
            for tag, i1, i2, j1, j2 in matcher.get_opcodes():
                if tag == 'replace':
                    for l in a_lines[i1:i2]: html.append(f"<span class='diff-line diff-del'>- {escape(l)}</span>")
                    for l in b_lines[j1:j2]: html.append(f"<span class='diff-line diff-add'>+ {escape(l)}</span>")
                elif tag == 'delete':
                    for l in a_lines[i1:i2]: html.append(f"<span class='diff-line diff-del'>- {escape(l)}</span>")
                elif tag == 'insert':
                    for l in b_lines[j1:j2]: html.append(f"<span class='diff-line diff-add'>+ {escape(l)}</span>")
                elif tag == 'equal':
                    for l in a_lines[i1:i2]: html.append(f"<span class='diff-line'>  {escape(l)}</span>")
            st.markdown(f"<div class='diff-container'>{''.join(html)}</div>", unsafe_allow_html=True)

# ==========================================
# 5. MAIN CONTROLLER
# ==========================================
def main():
    st.sidebar.title("🧪 ScopeWeaver Lab")
    
    # 1. Load Ground Truth
    # Tries to load v1_test_cases.json to accurately map IDs to Expected Tools
    ground_truth = DataManager.load_ground_truth(TEST_CASES_FILE)
    if not ground_truth:
        st.sidebar.warning(f"⚠️ {TEST_CASES_FILE} not found. 'Expected Tool' will be unknown.")

    # 2. Load Available Test Runs
    target_dir = BASE_TEST_DIR if os.path.exists(BASE_TEST_DIR) else "tests"
    available_tests = DataManager.get_available_tests(target_dir)

    if not available_tests:
        st.error(f"Tests folder `{target_dir}` not found.")
        st.info("Ensure your directory structure matches the documentation.")
        return

    name_map = {os.path.basename(p): p for p in available_tests}
    all_names = list(name_map.keys())

    # 3. Sidebar Selection
    st.sidebar.subheader("📂 Comparison Scope")
    selected_runs = st.sidebar.multiselect(
        "Select Runs:", 
        all_names, 
        default=all_names[-2:] if len(all_names)>=2 else all_names
    )
    
    if not selected_runs:
        st.warning("Select a run to begin.")
        return

    st.sidebar.markdown("---")
    # Single Run Inspector Focus
    primary_run = st.sidebar.selectbox("🔎 Focus Run (Deep Dive)", selected_runs, index=len(selected_runs)-1)

    # 4. Process Data
    all_dfs = []
    prompts_map = {}
    
    for name in selected_runs:
        payload = DataManager.load_single_run(name_map[name])
        # Pass Ground Truth to DataManager
        df = DataManager.process_run_data(payload, ground_truth)
        if not df.empty: all_dfs.append(df)
        prompts_map[name] = payload['prompt']

    master_df = pd.concat(all_dfs, ignore_index=True) if all_dfs else pd.DataFrame()

    # 5. Render Layout
    tabs = st.tabs(["📈 KPIs", "📊 Comparative Viz", "🧬 Input Analysis", "🔎 Single Inspector", "🗄️ Error DB", "🐞 Error Artifacts", "📝 Prompts"])

    with tabs[0]:
        UIComponents.render_rich_kpi_table(master_df)

    with tabs[1]:
        # --- Comparative Visualization Tab ---
        st.markdown("### 📊 Comparative Analysis")
        
        # [R1.5 + R3] Confusion Matrix Small Multiples
        st.markdown("#### 😵 Tool Selection Confusion (Small Multiples)")
        Visualizer.plot_confusion_matrix_small_multiples(master_df)
        
        st.markdown("---")
        
        # [R2 Swap] Pipeline Sankey is now here
        st.markdown("#### 🌊 Failure Pipeline Comparison (Small Multiples)")
        Visualizer.plot_pipeline_sankey_small_multiples(master_df)

    with tabs[2]:
        Visualizer.plot_input_explorer(master_df)
        st.markdown("---")
        Visualizer.plot_multivariate_flow(master_df)

    with tabs[3]:
        # --- Single Inspector Tab ---
        st.markdown(f"### 🔎 Deep Dive: {primary_run}")
        primary_df = master_df[master_df['run_id'] == primary_run]
        
        if not primary_df.empty:
            c1, c2 = st.columns([2, 1])
            with c1: 
                # [R2 Swap] Hierarchical Sankey is now here with Styling
                Visualizer.plot_hierarchical_sankey_single(primary_df, unique_key="hier_single_main")
            with c2: 
                # Sunburst Chart
                fig_sun = px.sunburst(primary_df, path=['category', 'type', 'status'], 
                                      color='status', color_discrete_map={"PASS":COLOR_PASS, "FAIL":COLOR_FAIL})
                
                fig_sun.update_layout(font=FONT_CONFIG)
                
                # FIX: FORCE WHITE TEXT ON SUNBURST
                fig_sun.update_traces(
                    textfont=dict(color='white', size=14),
                    insidetextorientation='radial'
                )
                
                st.plotly_chart(fig_sun, use_container_width=True, key="sun_single")
            
            st.markdown("---")
            UIComponents.render_original_deep_dive(primary_df)

    with tabs[4]:
        UIComponents.render_global_database(master_df)

    with tabs[5]:
        UIComponents.render_error_artifact_inspector(master_df)

    with tabs[6]:
        UIComponents.render_diff_view(prompts_map)

if __name__ == "__main__":
    main()