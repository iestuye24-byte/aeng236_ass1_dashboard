import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import os
import itertools

# =============================================================================
# Load and prepare main dataset
# =============================================================================
file_path = "dataset-for-dashboard (version 3).xlsb.xlsx"
if not os.path.exists(file_path):
    print(f"Warning: {file_path} not found. Ensure the file is in the directory.")

try:
    df = pd.read_excel(file_path, engine="openpyxl")
    df.columns = ["Size Group", "Length", "Diameter", "Thickness", "Weight", "Slenderness", "Sphericity"]
    df["Slenderness"] = df["Length"] / df["Diameter"]
    df["Sphericity"] = ((df["Length"] * df["Diameter"] * df["Thickness"]) ** (1 / 3)) / df["Length"]
    numeric_cols = ["Length", "Diameter", "Thickness", "Weight", "Slenderness", "Sphericity"]
    df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors="coerce")
    df.dropna(subset=numeric_cols + ["Size Group"], inplace=True)
except Exception as e:
    df = pd.DataFrame(columns=["Size Group", "Length", "Diameter", "Thickness", "Weight", "Slenderness", "Sphericity"])
    numeric_cols = ["Length", "Diameter", "Thickness", "Weight", "Slenderness", "Sphericity"]

# =============================================================================
# Load and prepare density data (static, not affected by filter)
# =============================================================================
density_file = "density_data.xlsx"
if os.path.exists(density_file):
    df_density = pd.read_excel(density_file, engine="openpyxl")
    # Rename columns for clarity
    df_density.columns = ["Sample", "Bulk_density", "Apparent_density"]
    # Convert to numeric, coerce errors (like the "Mean" row)
    df_density["Bulk_density"] = pd.to_numeric(df_density["Bulk_density"], errors="coerce")
    df_density["Apparent_density"] = pd.to_numeric(df_density["Apparent_density"], errors="coerce")
    # Use only rows with valid numbers (samples 1-10)
    density_numeric = df_density.dropna(subset=["Bulk_density", "Apparent_density"])
    bulk_mean = density_numeric["Bulk_density"].mean()
    bulk_std = density_numeric["Bulk_density"].std()
    apparent_mean = density_numeric["Apparent_density"].mean()
    apparent_std = density_numeric["Apparent_density"].std()
else:
    bulk_mean = bulk_std = apparent_mean = apparent_std = None
    print("Warning: density_data.xlsx not found. Density cards will not be displayed.")

# =============================================================================
# Styling & Theme Configuration
# =============================================================================
COLORS = {
    'primary': '#1A4D2E',  # Deep Forest Green
    'secondary': '#E8B817',  # Golden Banana Yellow
    'accent': '#FF7D00',  # Warm Orange Accent
    'background': '#F4F7F5',  # Soft green-tinted white
    'card': '#FFFFFF',  # White
    'text': '#2C3E2D',  # Dark green-gray
    'muted': '#7D8F7D',  # Muted sage green
    'small': '#88AB8E',  # Light sage
    'medium': '#E8B817',  # Golden Yellow
    'large': '#FF7D00',  # Warm Orange
    'border': '#EAEFEB',  # Light border
    'header-gradient-start': '#1A4D2E',
    'header-gradient-end': '#4F6F52',
}

size_colors = {'Small': COLORS['small'], 'Medium': COLORS['medium'], 'Large': COLORS['large']}
FONT_FAMILY = "Plus Jakarta Sans"

# =============================================================================
# App Initialization & Custom CSS
# =============================================================================
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.FONT_AWESOME],
                suppress_callback_exceptions=True)
app.title = "Banana Physical Properties"

app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;700;800&display=swap" rel="stylesheet">
        <style>
            body {
                font-family: 'Plus Jakarta Sans', sans-serif;
                background-color: ''' + COLORS['background'] + ''';
                color: ''' + COLORS['text'] + ''';
                line-height: 1.6;
            }
            /* Animations */
            @keyframes fadeInUp {
                from { opacity: 0; transform: translateY(20px); }
                to { opacity: 1; transform: translateY(0); }
            }
            .fade-in {
                animation: fadeInUp 0.6s cubic-bezier(0.165, 0.84, 0.44, 1) forwards;
            }
            .delay-1 { animation-delay: 0.1s; }
            .delay-2 { animation-delay: 0.2s; }
            .delay-3 { animation-delay: 0.3s; }

            h1, h2, h3, h4, h5, h6 { font-weight: 700; letter-spacing: -0.03em; }

            .dashboard-header {
                background: linear-gradient(135deg, ''' + COLORS['header-gradient-start'] + ''' 0%, ''' + COLORS[
    'header-gradient-end'] + ''' 100%);
                color: white; padding: 2.5rem 0; margin-bottom: 2rem;
                box-shadow: 0 10px 30px rgba(26, 77, 46, 0.15);
                border-radius: 0 0 2rem 2rem; position: relative; overflow: hidden;
            }
            .dashboard-header::after {
                content: ''; position: absolute; top: 0; left: 0; right: 0; bottom: 0;
                background: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" opacity="0.08"><path d="M20 20 L80 20 L80 80 L20 80 Z" fill="none" stroke="white" stroke-width="2"/><circle cx="50" cy="50" r="20" fill="none" stroke="white" stroke-width="2"/></svg>') repeat;
                pointer-events: none;
            }
            .metric-card {
                background: white; border-radius: 20px; box-shadow: 0 8px 24px rgba(0,0,0,0.04);
                border: 1px solid rgba(255,255,255,0.4); overflow: hidden; width: 100%; height: 100%; padding: 1.5rem;
            }
            .metric-card-btn {
                transition: transform 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275), box-shadow 0.3s ease;
                background: white; border: 1px solid ''' + COLORS['border'] + '''; border-radius: 16px;
                padding: 1.2rem; width: 100%; height: 100%; text-align: center; cursor: pointer;
            }
            .metric-card-btn:hover {
                transform: translateY(-6px); box-shadow: 0 15px 30px rgba(232, 184, 23, 0.15); border-color: ''' + \
                   COLORS['secondary'] + ''';
            }
            .metric-value { font-size: 1.8rem; font-weight: 800; color: ''' + COLORS['primary'] + '''; line-height: 1.2; }
            .metric-label { font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.08em; color: ''' + COLORS[
                       'muted'] + '''; font-weight: 700; }

            .filter-container {
                background: white; padding: 1.25rem 1.75rem; border-radius: 20px;
                box-shadow: 0 8px 24px rgba(0,0,0,0.04); margin-bottom: 2rem;
            }
            .custom-checkbox .form-check-input:checked { background-color: ''' + COLORS[
                       'primary'] + '''; border-color: ''' + COLORS['primary'] + '''; }
            .btn-custom { border-radius: 12px; font-weight: 600; background-color: ''' + COLORS[
                       'background'] + '''; color: ''' + COLORS['text'] + '''; border: 1px solid ''' + COLORS[
                       'border'] + '''; transition: all 0.2s; }
            .btn-custom:hover { background-color: ''' + COLORS['primary'] + '''; color: white; transform: translateY(-2px); }

            .section-title { position: relative; padding-bottom: 0.75rem; margin-bottom: 1.5rem; font-weight: 800; color: ''' + \
                   COLORS['primary'] + '''; }
            .section-title::after {
                content: ''; position: absolute; bottom: 0; left: 0; width: 40px; height: 4px;
                background: linear-gradient(90deg, ''' + COLORS['secondary'] + ''', ''' + COLORS['accent'] + '''); border-radius: 4px;
            }

            /* Custom Tabs Styling */
            .nav-tabs { border-bottom: 2px solid ''' + COLORS['border'] + '''; border-radius: 0; margin-bottom: 2rem; }
            .nav-tabs .nav-link { 
                border: none; color: ''' + COLORS['muted'] + '''; font-weight: 700; font-size: 1.1rem; 
                padding: 1rem 1.5rem; transition: all 0.3s; background: transparent;
            }
            .nav-tabs .nav-link:hover { color: ''' + COLORS['primary'] + '''; background: transparent; }
            .nav-tabs .nav-link.active { 
                color: ''' + COLORS['primary'] + '''; background: transparent; 
                border-bottom: 4px solid ''' + COLORS['secondary'] + '''; 
            }

            .scrollable-correlations { max-height: 380px; overflow-y: auto; padding-right: 5px; }
            .scrollable-correlations::-webkit-scrollbar { width: 6px; }
            .scrollable-correlations::-webkit-scrollbar-track { background: #f1f1f1; border-radius: 10px; }
            .scrollable-correlations::-webkit-scrollbar-thumb { background: ''' + COLORS['muted'] + '''; border-radius: 10px; }
        </style>
    </head>
    <body>{%app_entry%}<footer>{%config%}{%scripts%}{%renderer%}</footer></body>
</html>
'''

# =============================================================================
# App Layout
# =============================================================================
app.layout = dbc.Container([
    # Header
    html.Div([
        dbc.Container([
            html.Div([
                html.H1([html.I(className="fas fa-leaf me-3", style={"color": COLORS['secondary']}),
                         "Saba Banana Analytics"], className="display-5 mb-2"),
                html.P(["Interactive Physical & Morphological Dashboard"], className="lead mb-0",
                       style={"opacity": "0.9", "fontWeight": "400"})
            ], className="text-center fade-in")
        ], fluid=True)
    ], className="dashboard-header"),

    dbc.Container([
        # Global Filter Row
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.Div([
                        html.H5([html.I(className="fas fa-filter me-2", style={"color": COLORS['secondary']}),
                                 "Global Filter"], className="mb-0",
                                style={"fontWeight": "800", "color": COLORS['primary']}),
                        dcc.Checklist(
                            id="size-filter",
                            options=[
                                {"label": " All Groups", "value": "All"},
                                {"label": " Small", "value": "Small"},
                                {"label": " Medium", "value": "Medium"},
                                {"label": " Large", "value": "Large"}
                            ],
                            value=["All"], inline=True, className="custom-checkbox ms-4",
                            labelStyle={"margin-right": "1.5rem", "cursor": "pointer", "display": "inline-flex",
                                        "align-items": "center", "font-weight": "600"}
                        )
                    ], className="d-flex align-items-center flex-wrap")
                ], className="filter-container fade-in delay-1")
            ], width=12)
        ]),

        # Main Tabs Content
        dbc.Tabs([
            # TAB 1: OVERVIEW & DISTRIBUTIONS
            dbc.Tab(label="Overview & Distributions", tab_id="tab-1", children=[
                html.Div([
                    html.P("Select a metric card below to filter the distribution plots.", className="text-muted mb-4",
                           style={"fontWeight": "600"}),
                    dbc.Row(id="metrics-grid", className="g-3 mb-4"),

                    dbc.Row([
                        # Left column: Sample Distribution Pie (narrower)
                        dbc.Col([
                            html.Div([
                                html.H5(
                                    [html.I(className="fas fa-chart-pie me-2", style={"color": COLORS['secondary']}),
                                     "Sample Distribution"], className="section-title"),
                                dcc.Loading(type="dot", color=COLORS['primary'], children=[
                                    dcc.Graph(id="sample-pie", config={'displayModeBar': False},
                                              style={"height": "300px"})
                                ])
                            ], className="metric-card h-100")
                        ], xs=12, lg=4, className="mb-4 mb-lg-0"),

                        # Right column: Histogram and Box Plot side by side (wider)
                        dbc.Col([
                            html.Div([
                                html.H4(id="active-property-display", className="text-center mb-3",
                                        style={"color": COLORS['primary']}),
                                dbc.Row([
                                    dbc.Col([
                                        html.Div([
                                            html.Div([
                                                html.H5("Histogram", className="section-title",
                                                        style={"border": "none", "marginBottom": "0.5rem",
                                                               "display": "inline-block"}),
                                                dbc.Button([html.I(className="fas fa-expand-alt me-1"), " Expand"],
                                                           id="show-all-dist-btn", className="btn-custom float-end",
                                                           style={"marginTop": "0.5rem"})
                                            ], className="d-flex justify-content-between align-items-center"),
                                            dcc.Loading(type="dot", color=COLORS['primary'], children=[
                                                dcc.Graph(id="individual-dist-plot", config={'displayModeBar': 'hover'},
                                                          style={"height": "300px"})
                                            ])
                                        ], className="metric-card h-100")
                                    ], xs=12, md=6, className="mb-3 mb-md-0"),

                                    dbc.Col([
                                        html.Div([
                                            html.Div([
                                                html.H5("Box Plot", className="section-title",
                                                        style={"border": "none", "marginBottom": "0.5rem",
                                                               "display": "inline-block"}),
                                                dbc.Button([html.I(className="fas fa-expand-alt me-1"), " Expand"],
                                                           id="show-all-box-btn", className="btn-custom float-end",
                                                           style={"marginTop": "0.5rem"})
                                            ], className="d-flex justify-content-between align-items-center"),
                                            dcc.Loading(type="dot", color=COLORS['primary'], children=[
                                                dcc.Graph(id="box-plot", config={'displayModeBar': 'hover'},
                                                          style={"height": "300px"})
                                            ])
                                        ], className="metric-card h-100")
                                    ], xs=12, md=6)
                                ])
                            ])
                        ], xs=12, lg=8)
                    ])
                ], className="fade-in delay-2 py-3")
            ]),

            # TAB 2: CORRELATION ANALYSIS
            dbc.Tab(label="Correlation Analysis", tab_id="tab-2", children=[
                html.Div([
                    dbc.Row([
                        dbc.Col([
                            html.Div([
                                html.Div([
                                    html.H5("All Pairs", className="mb-2 d-inline-block",
                                            style={"fontWeight": "700", "color": COLORS['primary']}),
                                    dbc.Button("Show Full Matrix", id="reset-correlation-from-list",
                                               className="btn-custom float-end",
                                               style={"padding": "0.3rem 0.8rem", "fontSize": "0.85rem"})
                                ], className="mb-3"),
                                html.Div(id="correlation-summary-content", className="scrollable-correlations")
                            ], className="metric-card")
                        ], xs=12, md=4, className="mb-4 mb-md-0"),

                        dbc.Col([
                            html.Div([
                                html.H5("Correlation Matrix / Scatter Plot", className="mb-4",
                                        style={"fontWeight": "700", "color": COLORS['primary']}),
                                dcc.Loading(type="dot", color=COLORS['primary'], children=[
                                    dcc.Graph(id="correlation-matrix-plot", config={'displayModeBar': 'hover'},
                                              style={"height": "400px"})
                                ])
                            ], className="metric-card")
                        ], xs=12, md=8)
                    ])
                ], className="fade-in delay-2 py-3")
            ]),
        ], id="tabs", active_tab="tab-1"),

        # Footer
        html.Footer([
            html.Hr(style={"margin": "3rem 0 1rem 0", "opacity": "0.1", "borderColor": COLORS['primary']}),
            html.P(["Dashboard generated using Plotly Dash • Data: n=62 Saba banana samples • Density from 10 samples"],
                   className="text-center",
                   style={"fontSize": "0.9rem", "color": COLORS['muted'], "fontWeight": "600", "paddingBottom": "2rem"})
        ])
    ], fluid=True, style={"padding": "0 2% "}),

    # Modals
    dbc.Modal([
        dbc.ModalHeader(
            dbc.ModalTitle("All Distribution Plots", style={"fontWeight": "700", "color": COLORS['primary']})),
        dbc.ModalBody(dcc.Loading(type="dot", color=COLORS['primary'],
                                  children=dcc.Graph(id="dist-modal-plot", style={"height": "80vh"}))),
        dbc.ModalFooter(dbc.Button("Close", id="close-dist-modal-btn", className="ms-auto btn-custom")),
    ], id="dist-modal", size="xl", fullscreen=True, is_open=False),

    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("All Box Plots", style={"fontWeight": "700", "color": COLORS['primary']})),
        dbc.ModalBody(dcc.Loading(type="dot", color=COLORS['primary'],
                                  children=dcc.Graph(id="box-modal-plot", style={"height": "80vh"}))),
        dbc.ModalFooter(dbc.Button("Close", id="close-box-modal-btn", className="ms-auto btn-custom")),
    ], id="box-modal", size="xl", fullscreen=True, is_open=False),

    # Stores
    dcc.Store(id="selected-property", data="Weight"),
    dcc.Store(id="prev-size-filter", data=["All"]),
    dcc.Store(id="correlation-pair", data=None),
], fluid=True, style={"padding": "0", "backgroundColor": COLORS['background']})


# =============================================================================
# Helper Functions & Callbacks
# =============================================================================
def generate_pair_id(x, y): return f"corr-btn-{x}-{y}"

def get_all_pairs(): return list(itertools.combinations(numeric_cols, 2))

def create_density_card(label, value, std, unit, icon):
    """Create a non‑clickable card for density metrics."""
    if value is None:
        return None
    return dbc.Col([
        html.Div([
            html.Div([html.I(className=f"fas fa-{icon}",
                             style={"fontSize": "1.8rem", "color": COLORS['secondary'],
                                    "marginBottom": "0.5rem"})]),
            html.Div(f"{value:.2f}", className="metric-value"),
            html.Div(f"± {std:.2f} {unit}",
                     style={"fontSize": "0.9rem", "color": COLORS['muted'], "fontWeight": "600"}),
            html.Div(label, className="metric-label mt-2")
        ], className="metric-card-btn", style={
            "background": "white",
            "border": f"1px solid {COLORS['border']}",
            "borderRadius": "16px",
            "padding": "1.2rem",
            "width": "100%",
            "height": "100%",
            "textAlign": "center",
            "cursor": "default",           # non‑clickable
            "transition": "none",           # no hover effect
        })
    ], xs=12, sm=6, md=4, lg=3)  # Responsive widths: 4 cards per row on large


@app.callback(
    [Output("size-filter", "value"), Output("prev-size-filter", "data")],
    [Input("size-filter", "value")], [State("prev-size-filter", "data")],
    prevent_initial_call=True
)
def enforce_all_selection(new_val, old_val):
    new_set = set(new_val) if new_val else set()
    old_set = set(old_val) if old_val else set()
    if "All" in new_set:
        target = ["All"] if "All" not in old_set else list(new_set - {"All"}) or ["All"]
    else:
        target = ["All"] if not new_set else list(new_set)
    return (dash.no_update, target) if set(target) == new_set else (target, target)


@app.callback(
    Output("correlation-pair", "data", allow_duplicate=True),
    Input("size-filter", "value"), prevent_initial_call=True
)
def reset_correlation_on_filter(_): return None


@app.callback(
    [Output("metrics-grid", "children"), Output("individual-dist-plot", "figure"),
     Output("box-plot", "figure"), Output("active-property-display", "children"),
     Output("correlation-summary-content", "children"), Output("sample-pie", "figure")],
    [Input("size-filter", "value"), Input("selected-property", "data")]
)
def update_dashboard(selected_groups, selected_prop):
    filtered_df = df if "All" in selected_groups else pd.DataFrame(columns=df.columns) if not selected_groups else df[
        df["Size Group"].isin(selected_groups)]

    # 1. Sample Pie Chart
    if filtered_df.empty:
        pie_fig = go.Figure().add_annotation(text="No data", showarrow=False).update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    else:
        counts = filtered_df["Size Group"].value_counts().reset_index()
        counts.columns = ["Size Group", "Count"]
        pie_colors = [size_colors.get(sg, COLORS['primary']) for sg in counts["Size Group"]]
        pie_fig = go.Figure(data=[go.Pie(
            labels=counts["Size Group"], values=counts["Count"], hole=0.65,
            marker=dict(colors=pie_colors, line=dict(color='white', width=3)),
            textinfo='label+percent', textfont=dict(size=14, family=FONT_FAMILY, color=COLORS['text']),
            hovertemplate='<b>%{label}</b><br>Count: %{value}<extra></extra>'
        )])
        pie_fig.update_layout(
            showlegend=False, margin=dict(t=10, b=10, l=10, r=10), paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            annotations=[
                dict(text=f'<b>n={counts["Count"].sum()}</b>', x=0.5, y=0.5, font_size=22, font_family=FONT_FAMILY,
                     font_color=COLORS['primary'], showarrow=False)],
            transition={'duration': 500, 'easing': 'cubic-in-out'}
        )

    if filtered_df.empty:
        empty_msg = html.Div("No data available.", className="text-muted text-center py-5")
        empty_fig = go.Figure().add_annotation(text="No data", showarrow=False).update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        return [dbc.Col(empty_msg,
                        width=12)], empty_fig, empty_fig, f"Selected Property: {selected_prop}", empty_msg, pie_fig

    # 2. Metrics Grid (main six properties) - unit moved to std line
    means = filtered_df[numeric_cols].mean()
    stds = filtered_df[numeric_cols].std()
    metric_defs = [
        ("Length", means["Length"], stds["Length"], "mm", "ruler-horizontal", "metric-length"),
        ("Diameter", means["Diameter"], stds["Diameter"], "mm", "circle", "metric-diameter"),
        ("Thickness", means["Thickness"], stds["Thickness"], "mm", "layer-group", "metric-thickness"),
        ("Weight", means["Weight"], stds["Weight"], "g", "weight-hanging", "metric-weight"),
        ("Slenderness", means["Slenderness"], stds["Slenderness"], "", "arrows-alt-h", "metric-slenderness"),
        ("Sphericity", means["Sphericity"], stds["Sphericity"], "", "globe", "metric-sphericity")
    ]
    metrics_cards = []
    for name, mean_val, std_val, unit, icon, btn_id in metric_defs:
        # Build std string with unit if present
        std_str = f"± {std_val:.2f}" + (f" {unit}" if unit else "")
        metrics_cards.append(dbc.Col([
            dbc.Button(
                id=btn_id,
                children=[
                    html.Div([html.I(className=f"fas fa-{icon}",
                                     style={"fontSize": "1.8rem", "color": COLORS['secondary'],
                                            "marginBottom": "0.5rem"})]),
                    html.Div(f"{mean_val:.2f}", className="metric-value"),
                    html.Div(std_str,
                             style={"fontSize": "0.9rem", "color": COLORS['muted'], "fontWeight": "600"}),
                    html.Div(name, className="metric-label mt-2")
                ],
                className="metric-card-btn", n_clicks=0
            )
        ], xs=12, sm=6, md=4, lg=3))  # Responsive widths: 4 per row on large

    # 3. Append density cards (static, if available)
    if bulk_mean is not None:
        bulk_card = create_density_card("Bulk Density", bulk_mean, bulk_std, "kg/m³", "weight-hanging")
        if bulk_card:
            metrics_cards.append(bulk_card)
    if apparent_mean is not None:
        apparent_card = create_density_card("Apparent Density", apparent_mean, apparent_std, "kg/m³", "cube")
        if apparent_card:
            metrics_cards.append(apparent_card)

    # 4. Individual Histogram
    indiv_fig = go.Figure(go.Histogram(
        x=filtered_df[selected_prop], marker_color=COLORS['primary'], opacity=0.8, nbinsx=12,
        marker_line_color='white', marker_line_width=2,
        hovertemplate=f'<b>{selected_prop}</b><br>Value: %{{x:.2f}}<br>Count: %{{y}}<extra></extra>'
    ))
    mean_val = filtered_df[selected_prop].mean()
    indiv_fig.add_vline(x=mean_val, line_dash="dash", line_color=COLORS['accent'], line_width=2.5,
                        annotation_text=f"μ={mean_val:.1f}", annotation_position="top right", annotation_font_size=11,
                        annotation_font_color=COLORS['text'])
    unit = 'g' if selected_prop == 'Weight' else 'mm' if selected_prop in ['Length', 'Diameter', 'Thickness'] else ''
    indiv_fig.update_layout(
        xaxis_title=f"{selected_prop} ({unit})" if unit else selected_prop, yaxis_title="Frequency",
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family=FONT_FAMILY, size=12, color=COLORS['text']),
        margin=dict(t=10, b=40, l=40, r=20), hovermode='closest',
        transition={'duration': 500, 'easing': 'cubic-in-out'}
    )
    indiv_fig.update_xaxes(showgrid=False, zeroline=False)
    indiv_fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor=COLORS['border'], zeroline=False)

    # 5. Box Plot
    box_fig = go.Figure()
    if "All" in selected_groups and len(filtered_df["Size Group"].unique()) > 1:
        for size_group in ["Small", "Medium", "Large"]:
            if size_group in filtered_df["Size Group"].unique():
                data = filtered_df[filtered_df["Size Group"] == size_group][selected_prop]
                box_fig.add_trace(go.Box(
                    y=data, name=size_group, marker_color=size_colors.get(size_group, COLORS['primary']),
                    line=dict(width=2), boxmean=True, boxpoints='outliers', fillcolor=size_colors.get(size_group)
                ))
    else:
        box_fig.add_trace(go.Box(
            y=filtered_df[selected_prop], marker_color=COLORS['primary'],
            line=dict(width=2), boxmean=True, boxpoints='outliers', name=selected_prop
        ))
    box_fig.update_layout(
        yaxis_title=selected_prop, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family=FONT_FAMILY, size=12, color=COLORS['text']), margin=dict(t=10, b=40, l=40, r=20),
        hovermode='closest', showlegend=("All" in selected_groups and len(filtered_df["Size Group"].unique()) > 1),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        transition={'duration': 500, 'easing': 'cubic-in-out'}
    )
    box_fig.update_xaxes(showgrid=False, zeroline=False)
    box_fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor=COLORS['border'], zeroline=False)

    # 6. Correlation Summary
    if len(filtered_df) < 2:
        correlation_summary = html.Div([html.I(className="fas fa-info-circle me-2"), "Insufficient data."],
                                       className="text-muted")
    else:
        corr_matrix = filtered_df[numeric_cols].corr()
        pairs = get_all_pairs()
        pair_data = []
        for x, y in pairs:
            r = corr_matrix.loc[x, y]
            abs_r = abs(r)
            pair_data.append((abs_r, x, y, r))
        pair_data.sort(key=lambda item: item[0], reverse=True)

        corr_items = []
        for abs_r, x, y, r in pair_data:
            if abs_r >= 0.9:
                strength, color, badge = "Very Strong", COLORS['primary'], "bg-success"
            elif abs_r >= 0.7:
                strength, color, badge = "Strong", "#4F6F52", "bg-success"
            elif abs_r >= 0.5:
                strength, color, badge = "Moderate", COLORS['medium'], "bg-warning"
            else:
                strength, color, badge = "Weak", COLORS['muted'], "bg-secondary"

            btn_id = generate_pair_id(x, y)
            corr_items.append(dbc.Button(
                id=btn_id,
                children=[
                    html.Div([
                        html.Span(x, style={"fontWeight": "700", "color": COLORS['text']}),
                        html.Span(" vs ", style={"margin": "0 0.5rem", "color": COLORS['muted']}),
                        html.Span(y, style={"fontWeight": "700", "color": COLORS['text']}),
                    ], style={"display": "flex", "alignItems": "center", "marginBottom": "0.3rem"}),
                    html.Div([
                        html.Span(f"r = {r:.3f}", style={"fontWeight": "800", "color": color, "fontSize": "1.1rem",
                                                         "fontFamily": FONT_FAMILY}),
                        html.Span(strength, className=f"badge {badge} ms-2", style={"fontSize": "0.75rem"})
                    ])
                ],
                style={"width": "100%", "textAlign": "left", "background": "white",
                       "border": f"1px solid {COLORS['border']}", "padding": "0.75rem", "marginBottom": "0.5rem",
                       "borderLeft": f"5px solid {color}", "borderRadius": "10px", "transition": "transform 0.2s"},
                className="correlation-btn"
            ))
        correlation_summary = html.Div(corr_items)

    property_title = html.Span([
        "Currently Viewing Distributions for: ",
        html.Span(selected_prop, style={"textDecoration": "underline", "textDecorationColor": COLORS['secondary'],
                                        "textDecorationThickness": "3px"})
    ])

    return metrics_cards, indiv_fig, box_fig, property_title, correlation_summary, pie_fig


@app.callback(
    Output("selected-property", "data"),
    [Input(f"metric-{p.lower()}", "n_clicks") for p in numeric_cols],
    prevent_initial_call=True
)
def select_property(*args):
    ctx = dash.callback_context
    if not ctx.triggered: return dash.no_update
    btn = ctx.triggered[0]["prop_id"].split(".")[0].split("-")[1].capitalize()
    return btn if btn in numeric_cols else "Weight"


@app.callback(
    [Output(f"metric-{p.lower()}", "style") for p in numeric_cols],
    [Input("selected-property", "data")]
)
def highlight_selected(selected_prop):
    base_style = {"background": "white", "border": "1px solid " + COLORS['border'], "borderRadius": "16px",
                  "padding": "1.2rem", "width": "100%", "height": "100%", "textAlign": "center", "color": "inherit",
                  "transition": "all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275)"}
    selected_style = base_style.copy()
    selected_style["border"] = f"2px solid {COLORS['primary']}"
    selected_style["boxShadow"] = f"0 10px 25px rgba(26, 77, 46, 0.15)"
    selected_style["transform"] = "translateY(-4px)"
    return [selected_style if prop == selected_prop else base_style for prop in numeric_cols]


pair_inputs = [Input(generate_pair_id(x, y), "n_clicks") for x, y in get_all_pairs()]


@app.callback(Output("correlation-pair", "data"), pair_inputs, prevent_initial_call=True)
def select_correlation_pair(*args):
    ctx = dash.callback_context
    if not ctx.triggered: return dash.no_update
    parts = ctx.triggered[0]["prop_id"].split(".")[0].split("-")
    return {"x": parts[2], "y": parts[3]}


@app.callback(Output("correlation-pair", "data", allow_duplicate=True),
              Input("reset-correlation-from-list", "n_clicks"), prevent_initial_call=True)
def reset_correlation_from_list(n_clicks): return None


@app.callback(
    Output("correlation-matrix-plot", "figure"),
    [Input("size-filter", "value"), Input("correlation-pair", "data")]
)
def update_correlation_matrix(selected_groups, pair):
    filtered_df = df if "All" in selected_groups else pd.DataFrame(columns=df.columns) if not selected_groups else df[
        df["Size Group"].isin(selected_groups)]
    if filtered_df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No data available", showarrow=False)
        return fig

    multiple_groups = len(filtered_df["Size Group"].unique()) > 1

    if pair is None:
        # Full scatter matrix
        dimensions = numeric_cols
        n_dim = len(dimensions)
        fig = make_subplots(
            rows=n_dim, cols=n_dim,
            shared_xaxes=False, shared_yaxes=False,
            horizontal_spacing=0.02, vertical_spacing=0.02
        )
        for i, y_dim in enumerate(dimensions):
            for j, x_dim in enumerate(dimensions):
                if i == j:
                    fig.add_trace(
                        go.Histogram(x=filtered_df[x_dim], marker_color=COLORS['secondary'], opacity=0.7,
                                     showlegend=False),
                        row=i + 1, col=j + 1
                    )
                elif i > j:
                    if multiple_groups:
                        for size_group in filtered_df["Size Group"].unique():
                            df_group = filtered_df[filtered_df["Size Group"] == size_group]
                            fig.add_trace(
                                go.Scatter(
                                    x=df_group[x_dim], y=df_group[y_dim],
                                    mode='markers', name=size_group,
                                    marker=dict(size=8, color=size_colors.get(size_group, COLORS['primary']),
                                                opacity=0.7, line=dict(width=0.5, color='white')),
                                    showlegend=(i == 1 and j == 0)  # legend only in top-right subplot
                                ),
                                row=i + 1, col=j + 1
                            )
                    else:
                        fig.add_trace(
                            go.Scatter(
                                x=filtered_df[x_dim], y=filtered_df[y_dim],
                                mode='markers',
                                marker=dict(size=8, color=COLORS['secondary'], opacity=0.7,
                                            line=dict(width=0.5, color='white')),
                                showlegend=False
                            ),
                            row=i + 1, col=j + 1
                        )
                    if len(filtered_df) > 2:
                        z = np.polyfit(filtered_df[x_dim], filtered_df[y_dim], 1)
                        p = np.poly1d(z)
                        x_line = np.linspace(filtered_df[x_dim].min(), filtered_df[x_dim].max(), 100)
                        fig.add_trace(
                            go.Scatter(
                                x=x_line, y=p(x_line), mode='lines',
                                line=dict(color=COLORS['accent'], dash='dash', width=2),
                                showlegend=False, hoverinfo='skip'
                            ),
                            row=i + 1, col=j + 1
                        )
                if i == n_dim - 1:
                    fig.update_xaxes(title_text=x_dim, row=i + 1, col=j + 1)
                if j == 0:
                    fig.update_yaxes(title_text=y_dim, row=i + 1, col=j + 1)
                fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(0,0,0,0.05)', row=i + 1, col=j + 1)
                fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(0,0,0,0.05)', row=i + 1, col=j + 1)
        fig.update_layout(
            height=400,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(family=FONT_FAMILY, size=10, color=COLORS['text']),
            margin=dict(t=30, b=30, l=50, r=30),
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                bgcolor='rgba(255,255,255,0.8)'
            ) if multiple_groups else {}
        )
    else:
        # Individual scatter plot for selected pair
        x, y = pair["x"], pair["y"]
        fig = go.Figure()
        if multiple_groups:
            for size_group in filtered_df["Size Group"].unique():
                df_group = filtered_df[filtered_df["Size Group"] == size_group]
                fig.add_trace(go.Scatter(
                    x=df_group[x], y=df_group[y],
                    mode='markers', name=size_group,
                    marker=dict(size=10, color=size_colors.get(size_group, COLORS['primary']),
                                opacity=0.7, line=dict(width=1, color='white'))
                ))
        else:
            fig.add_trace(go.Scatter(
                x=filtered_df[x], y=filtered_df[y],
                mode='markers',
                marker=dict(size=10, color=COLORS['secondary'], opacity=0.7, line=dict(width=1, color='white')),
                showlegend=False
            ))
        if len(filtered_df) > 2:
            z = np.polyfit(filtered_df[x], filtered_df[y], 1)
            p = np.poly1d(z)
            x_line = np.linspace(filtered_df[x].min(), filtered_df[x].max(), 100)
            fig.add_trace(go.Scatter(
                x=x_line, y=p(x_line), mode='lines',
                line=dict(color=COLORS['accent'], dash='dash', width=2),
                name='Trend', showlegend=False
            ))
        r = filtered_df[[x, y]].corr().loc[x, y]
        fig.add_annotation(
            xref="paper", yref="paper", x=0.98, y=0.98, text=f"r = {r:.3f}", showarrow=False,
            font=dict(size=14, color=COLORS['primary'], family=FONT_FAMILY),
            bgcolor="rgba(255,255,255,0.8)", bordercolor=COLORS['border'], borderwidth=1, borderpad=4
        )
        fig.update_layout(
            title=f"{x} vs {y}", xaxis_title=x, yaxis_title=y, height=400,
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(family=FONT_FAMILY, size=12, color=COLORS['text']),
            margin=dict(t=50, b=40, l=60, r=60), hovermode='closest'
        )
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(0,0,0,0.05)')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(0,0,0,0.05)')
    return fig


# Modals Callbacks
@app.callback([Output("dist-modal", "is_open"), Output("dist-modal-plot", "figure")],
              [Input("show-all-dist-btn", "n_clicks")], [State("size-filter", "value")], prevent_initial_call=True)
def open_dist_modal(n_clicks, selected_groups):
    if n_clicks is None: return False, go.Figure()
    filtered_df = df if "All" in selected_groups else pd.DataFrame(columns=df.columns) if not selected_groups else df[
        df["Size Group"].isin(selected_groups)]
    if filtered_df.empty: return True, go.Figure().add_annotation(text="No data", showarrow=False)

    fig = make_subplots(rows=2, cols=3, subplot_titles=[f"<b>{col}</b>" for col in numeric_cols], vertical_spacing=0.15,
                        horizontal_spacing=0.08)
    for i, col in enumerate(numeric_cols):
        row, col_pos = i // 3 + 1, i % 3 + 1
        fig.add_trace(go.Histogram(x=filtered_df[col], marker_color=COLORS['primary'], opacity=0.85, nbinsx=15,
                                   marker_line_color='white', marker_line_width=1), row=row, col=col_pos)
        fig.update_xaxes(showgrid=False, zeroline=False, row=row, col=col_pos)
        fig.update_yaxes(title_text="Frequency" if col_pos == 1 else "", showgrid=True, gridcolor=COLORS['border'],
                         zeroline=False, row=row, col=col_pos)
    fig.update_layout(showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                      font=dict(family=FONT_FAMILY, size=12, color=COLORS['text']), margin=dict(t=40, b=30, l=40, r=30))
    return True, fig


@app.callback(Output("dist-modal", "is_open", allow_duplicate=True), Input("close-dist-modal-btn", "n_clicks"),
              State("dist-modal", "is_open"), prevent_initial_call=True)
def close_dist_modal(n_clicks, is_open): return False if n_clicks else is_open


@app.callback([Output("box-modal", "is_open"), Output("box-modal-plot", "figure")],
              [Input("show-all-box-btn", "n_clicks")], [State("size-filter", "value")], prevent_initial_call=True)
def open_box_modal(n_clicks, selected_groups):
    if n_clicks is None: return False, go.Figure()
    filtered_df = df if "All" in selected_groups else pd.DataFrame(columns=df.columns) if not selected_groups else df[
        df["Size Group"].isin(selected_groups)]
    if filtered_df.empty: return True, go.Figure().add_annotation(text="No data", showarrow=False)

    fig = make_subplots(rows=2, cols=3, subplot_titles=[f"<b>{col}</b>" for col in numeric_cols], vertical_spacing=0.15,
                        horizontal_spacing=0.08)
    for i, col in enumerate(numeric_cols):
        row, col_pos = i // 3 + 1, i % 3 + 1
        if "All" in selected_groups and len(filtered_df["Size Group"].unique()) > 1:
            for sg in ["Small", "Medium", "Large"]:
                if sg in filtered_df["Size Group"].values:
                    fig.add_trace(go.Box(y=filtered_df[filtered_df["Size Group"] == sg][col], name=sg, legendgroup=sg,
                                         showlegend=(i == 0), marker_color=size_colors[sg],
                                         line=dict(color=size_colors[sg], width=2), boxmean=True), row=row, col=col_pos)
        else:
            fig.add_trace(
                go.Box(y=filtered_df[col], marker_color=COLORS['primary'], line=dict(color=COLORS['primary'], width=2),
                       boxmean=True, name=col), row=row, col=col_pos)
        fig.update_xaxes(showticklabels=False, zeroline=False, row=row, col=col_pos)
        fig.update_yaxes(title_text=col if col_pos == 1 else "", showgrid=True, gridcolor=COLORS['border'],
                         zeroline=False, row=row, col=col_pos)
    fig.update_layout(boxmode="group", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                      font=dict(family=FONT_FAMILY, size=12, color=COLORS['text']), margin=dict(t=40, b=30, l=50, r=30),
                      legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="center", x=0.5))
    return True, fig


@app.callback(Output("box-modal", "is_open", allow_duplicate=True), Input("close-box-modal-btn", "n_clicks"),
              State("box-modal", "is_open"), prevent_initial_call=True)
def close_box_modal(n_clicks, is_open): return False if n_clicks else is_open

server = app.server  # Expose the underlying Flask server for gunicorn

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=8080)



