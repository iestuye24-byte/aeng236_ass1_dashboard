import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import os

# Load and prepare data
file_path = "dataset-for-dashboard (version 3).xlsb.xlsx"
if not os.path.exists(file_path):
    raise FileNotFoundError(f"Excel file not found: {file_path}")

df = pd.read_excel(file_path, engine="openpyxl")

# Rename columns for convenience
df.columns = ["Size Group", "Length", "Diameter", "Thickness", "Weight",
              "Slenderness", "Sphericity"]

# Recompute Slenderness and Sphericity (ensuring they are numeric)
df["Slenderness"] = df["Length"] / df["Diameter"]
df["Sphericity"] = ((df["Length"] * df["Diameter"] * df["Thickness"]) ** (1 / 3)) / df["Length"]

# Ensure numeric types
numeric_cols = ["Length", "Diameter", "Thickness", "Weight", "Slenderness", "Sphericity"]
df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors="coerce")

# Drop any rows with missing critical values
df.dropna(subset=numeric_cols + ["Size Group"], inplace=True)

# Overall sample distribution (static)
size_counts = df["Size Group"].value_counts().reset_index()
size_counts.columns = ["Size Group", "Count"]
size_counts["Percentage"] = (size_counts["Count"] / size_counts["Count"].sum() * 100).round(1)

# Color palette - sophisticated scientific scheme
COLORS = {
    'primary': '#2E4057',  # Deep slate blue
    'secondary': '#048A81',  # Teal
    'accent': '#FF6B35',  # Coral accent
    'background': '#F8F9FA',  # Light gray
    'card': '#FFFFFF',  # White
    'text': '#2C3E50',  # Dark blue-gray
    'muted': '#6C757D',  # Gray
    'small': '#54C6EB',  # Light blue
    'medium': '#048A81',  # Teal
    'large': '#FF6B35',  # Coral
    'border': '#E9ECEF'  # Light border
}

# Size group colors
size_colors = {
    'Small': COLORS['small'],
    'Medium': COLORS['medium'],
    'Large': COLORS['large']
}

# Initialize the Dash app with custom styling
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.FONT_AWESOME],
    suppress_callback_exceptions=True
)
app.title = "Banana Physical Properties Dashboard"

# Custom CSS for publication-ready styling (all sans‑serif now)
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <link href="https://fonts.googleapis.com/css2?family=Source+Sans+Pro:wght@300;400;600;700&display=swap" rel="stylesheet">
        <style>
            body {
                font-family: 'Source Sans Pro', sans-serif;
                background-color: #F8F9FA;
                color: #2C3E50;
                line-height: 1.6;
            }
            h1, h2, h3, h4, h5, h6 {
                font-family: 'Source Sans Pro', sans-serif;
                font-weight: 600;
                letter-spacing: -0.02em;
            }
            .dashboard-header {
                background: linear-gradient(135deg, #2E4057 0%, #048A81 100%);
                color: white;
                padding: 2.5rem 0;
                margin-bottom: 2rem;
                box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            }
            .metric-card {
                background: white;
                border-radius: 12px;
                box-shadow: 0 2px 12px rgba(0,0,0,0.06);
                border: 1px solid #E9ECEF;
                transition: transform 0.2s ease, box-shadow 0.2s ease;
                overflow: hidden;
                width: 100%;
                height: 100%;
                padding: 1rem;
                text-align: center;
            }
            .metric-card:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 24px rgba(0,0,0,0.1);
            }
            .metric-card.selected {
                border: 2px solid #048A81;
                box-shadow: 0 0 0 2px rgba(4, 138, 129, 0.2);
            }
            .metric-value {
                font-size: 1.75rem;
                font-weight: 700;
                color: #2E4057;
                font-family: 'Source Sans Pro', sans-serif;
            }
            .metric-label {
                font-size: 0.85rem;
                text-transform: uppercase;
                letter-spacing: 0.05em;
                color: #6C757D;
                font-weight: 600;
            }
            .stat-card {
                background: white;
                border-left: 4px solid #048A81;
                padding: 1.25rem;
                margin-bottom: 1rem;
                border-radius: 0 8px 8px 0;
                box-shadow: 0 2px 8px rgba(0,0,0,0.04);
            }
            .filter-container {
                background: white;
                padding: 1.5rem;
                border-radius: 12px;
                box-shadow: 0 2px 12px rgba(0,0,0,0.06);
                margin-bottom: 2rem;
            }
            .custom-checkbox .form-check-input:checked {
                background-color: #048A81;
                border-color: #048A81;
            }
            .custom-checkbox .form-check-input {
                border: 2px solid #CED4DA;
                width: 1.2em;
                height: 1.2em;
                margin-right: 0.5rem;
            }
            .custom-checkbox .form-check-label {
                font-weight: 500;
                color: #2C3E50;
            }
            .dash-graph {
                border-radius: 12px;
                overflow: hidden;
            }
            .correlation-item {
                padding: 0.75rem;
                background: #F8F9FA;
                border-radius: 8px;
                margin-bottom: 0.5rem;
                border-left: 3px solid #048A81;
            }
            .tab-container {
                background: white;
                border-radius: 12px;
                padding: 1.5rem;
                box-shadow: 0 2px 12px rgba(0,0,0,0.06);
            }
            .dash-tabs {
                border-bottom: 2px solid #E9ECEF;
            }
            .dash-tab {
                padding: 1rem 2rem;
                font-weight: 600;
                color: #6C757D;
                border: none;
                border-bottom: 3px solid transparent;
                transition: all 0.3s ease;
            }
            .dash-tab:hover {
                color: #048A81;
                background: rgba(4, 138, 129, 0.05);
            }
            .dash-tab--selected {
                color: #048A81 !important;
                border-bottom: 3px solid #048A81 !important;
                background: white !important;
            }
            .sample-badge {
                display: inline-block;
                padding: 0.25rem 0.75rem;
                background: rgba(4, 138, 129, 0.1);
                color: #048A81;
                border-radius: 20px;
                font-size: 0.85rem;
                font-weight: 600;
                margin-left: 1rem;
            }
            .section-title {
                position: relative;
                padding-bottom: 0.75rem;
                margin-bottom: 1.5rem;
            }
            .section-title::after {
                content: '';
                position: absolute;
                bottom: 0;
                left: 0;
                width: 60px;
                height: 3px;
                background: linear-gradient(90deg, #048A81, #54C6EB);
                border-radius: 2px;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# App layout
app.layout = dbc.Container([
    # Header Section
    html.Div([
        dbc.Container([
            html.Div([
                html.H1([
                    html.I(className="fas fa-leaf me-3", style={"opacity": "0.8"}),
                    "Saba Banana Physical Properties - Los Baños"
                ], className="display-5 mb-2", style={"fontWeight": "700"}),
                html.P([
                    "Dashboard for Physical Properties of Agricultural Materials"
                ], className="lead mb-0", style={"opacity": "0.5", "fontSize": "1.1rem"})
            ], className="text-center")
        ], fluid=True)
    ], className="dashboard-header"),

    dbc.Container([
        # Row 1: Data Filter and Group Statistics side by side
        dbc.Row([
            dbc.Col([
                # Filter Section (checkboxes)
                html.Div([
                    html.H5([
                        html.I(className="fas fa-filter me-2", style={"color": COLORS['secondary']}),
                        "Data Filter"
                    ], className="section-title"),
                    dbc.Row([
                        dbc.Col([
                            html.Label("Select Size Groups:", className="fw-bold mb-3", style={"color": COLORS['text']}),
                            dcc.Checklist(
                                id="size-filter",
                                options=[
                                    {"label": " All Groups", "value": "All"},
                                    {"label": " Small", "value": "Small"},
                                    {"label": " Medium", "value": "Medium"},
                                    {"label": " Large", "value": "Large"}
                                ],
                                value=["All"],  # default to All
                                inline=True,
                                className="custom-checkbox",
                                labelStyle={
                                    "margin-right": "2rem",
                                    "cursor": "pointer",
                                    "display": "inline-flex",
                                    "align-items": "center"
                                }
                            )
                        ], width=12)
                    ])
                ], className="filter-container h-100")
            ], width=4),

            dbc.Col([
                # Group Statistics (metrics grid) - now buttons
                html.Div([
                    html.H5([
                        html.I(className="fas fa-chart-line me-2", style={"color": COLORS['secondary']}),
                        "Group Statistics"
                    ], className="section-title"),
                    dbc.Row(id="metrics-grid", className="g-4")
                ], className="h-100")
            ], width=8)
        ], className="g-4 mb-4"),

        # Row 2: Three cards side by side
        dbc.Row([
            dbc.Col([
                # Dynamic Property Distribution (replaces Weight Distribution)
                html.Div([
                    html.H5(id="property-stats-title", children="Weight Distribution",
                            className="section-title", style={"border": "none", "marginBottom": "1rem"}),
                    html.Div(id="property-stats-content")
                ], className="metric-card p-4 h-100")
            ], width=4),

            dbc.Col([
                html.Div([
                    html.H5([
                        html.I(className="fas fa-project-diagram me-2", style={"color": COLORS['secondary']}),
                        "Correlation Analysis"
                    ], className="section-title", style={"border": "none", "marginBottom": "1rem"}),
                    html.Div(id="correlation-content")
                ], className="metric-card p-4 h-100")
            ], width=4),

            dbc.Col([
                html.Div([
                    html.H5([
                        html.I(className="fas fa-chart-pie me-2", style={"color": COLORS['secondary']}),
                        "Sample Distribution"
                    ], className="section-title"),
                    dcc.Graph(
                        id="sample-pie",
                        config={'displayModeBar': False},
                        style={"height": "300px"}
                    )
                ], className="metric-card p-4 h-100")
            ], width=4)
        ], className="g-4 mb-4"),

        # Main Content Tabs + Expand Button
        html.Div([
            dbc.Row([
                dbc.Col(
                    dcc.Tabs(
                        id="plot-tabs",
                        value="histograms",
                        className="dash-tabs",
                        parent_className="custom-tabs",
                        children=[
                            dcc.Tab(
                                label="Distribution Analysis",
                                value="histograms",
                                className="dash-tab",
                                selected_className="dash-tab--selected"
                            ),
                            dcc.Tab(
                                label="Correlation Matrix",
                                value="scatter-matrix",
                                className="dash-tab",
                                selected_className="dash-tab--dash-tab--selected"
                            ),
                            dcc.Tab(
                                label="Comparative Box Plots",
                                value="box-plots",
                                className="dash-tab",
                                selected_className="dash-tab--selected"
                            ),
                        ]
                    ),
                    width=11
                ),
                dbc.Col(
                    dbc.Button(
                        [html.I(className="fas fa-expand me-1"), "Expand"],
                        id="expand-plot-btn",
                        color="secondary",
                        outline=True,
                        size="sm",
                        className="mt-2"
                    ),
                    width=1,
                    className="text-end"
                )
            ]),
            html.Div(id="tab-content", className="mt-4")
        ], className="tab-container mb-4"),

        # Footer
        html.Footer([
            html.Hr(style={"margin": "2rem 0 1rem 0", "opacity": "0.1"}),
            html.P([
                "Dashboard generated using Plotly Dash • Data: n=62 banana samples"
            ], className="text-center text-muted", style={"fontSize": "0.9rem"})
        ])

    ], fluid=False, style={"maxWidth": "1400px", "margin": "0 auto", "padding": "0 20px"}),

    # Modal for expanded plot
    dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle(id="modal-title", children="Expanded View")),
            dbc.ModalBody(
                dcc.Graph(
                    id="modal-plot",
                    style={"height": "80vh"},  # large graph
                    config={'displayModeBar': 'hover'}
                )
            ),
            dbc.ModalFooter(
                dbc.Button("Close", id="close-modal-btn", className="ms-auto")
            ),
        ],
        id="plot-modal",
        size="xl",
        backdrop="static",
        keyboard=False,
        is_open=False,
    ),

    # Store for selected property
    dcc.Store(id="selected-property", data="Weight"),
    # Store for previous filter selection (to implement smart "All" behavior)
    dcc.Store(id="prev-size-filter", data=["All"]),

], fluid=True, style={"padding": "0", "backgroundColor": COLORS['background']})


# =============================================================================
# Callbacks
# =============================================================================

# 1. Enforce smart "All" vs specific groups behavior
@app.callback(
    [Output("size-filter", "value"),
     Output("prev-size-filter", "data")],
    [Input("size-filter", "value")],
    [State("prev-size-filter", "data")],
    prevent_initial_call=True
)
def enforce_all_selection(new_val, old_val):
    # Convert to sets for easier manipulation
    new_set = set(new_val) if new_val else set()
    old_set = set(old_val) if old_val else set()

    # Compute target selection based on change
    if "All" in new_set:
        if "All" not in old_set:
            # User just clicked "All" -> set to only "All"
            target = ["All"]
        else:
            # "All" was already selected, user clicked something else
            # Remove "All" and keep the rest (specifics)
            target = list(new_set - {"All"})
            if not target:
                target = ["All"]  # should not happen, but safety
    else:
        # "All" not in new set
        if not new_set:
            # No groups selected -> default to "All"
            target = ["All"]
        else:
            # Only specifics selected
            target = list(new_set)

    # If the target is the same as input, avoid infinite loop
    if set(target) == new_set:
        return dash.no_update, target
    else:
        return target, target


# 2. Main callback to update metrics grid, correlation, pie, and plots
@app.callback(
    [Output("metrics-grid", "children"),
     Output("correlation-content", "children"),
     Output("tab-content", "children"),
     Output("sample-pie", "figure")],
    [Input("size-filter", "value"),
     Input("plot-tabs", "value")]
)
def update_dashboard(selected_groups, active_tab):
    # Filter data
    if "All" in selected_groups:
        filtered_df = df
    else:
        if not selected_groups:
            filtered_df = pd.DataFrame(columns=df.columns)
        else:
            filtered_df = df[df["Size Group"].isin(selected_groups)]

    # Prepare pie chart (static overall distribution but with highlight)
    pie_colors = [size_colors.get(sg, COLORS['primary']) for sg in size_counts["Size Group"]]
    if "All" not in selected_groups and len(selected_groups) == 1:
        highlight = selected_groups[0]
        pie_colors = [
            size_colors.get(sg, COLORS['primary']) if sg == highlight else '#E9ECEF'
            for sg in size_counts["Size Group"]
        ]
    else:
        pie_colors = [size_colors.get(sg, COLORS['primary']) for sg in size_counts["Size Group"]]

    pie_fig = go.Figure(data=[go.Pie(
        labels=size_counts["Size Group"],
        values=size_counts["Count"],
        hole=0.55,
        marker=dict(colors=pie_colors, line=dict(color='white', width=2)),
        textinfo='label+percent',
        textfont=dict(size=12, family='Source Sans Pro'),
        hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>'
    )])

    if "All" in selected_groups:
        ann_text = f'<b>Total</b><br>n=62'
    elif len(selected_groups) == 1:
        ann_text = f'<b>{selected_groups[0]}</b><br>n={len(filtered_df)}'
    else:
        ann_text = f'<b>Selected</b><br>n={len(filtered_df)}'

    pie_fig.update_layout(
        showlegend=False,
        margin=dict(t=20, b=20, l=20, r=20),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        annotations=[dict(
            text=ann_text,
            x=0.5, y=0.5,
            font_size=16,
            font_family='Source Sans Pro',
            showarrow=False
        )]
    )

    # If empty after filtering, show placeholder for all outputs
    if filtered_df.empty:
        empty_msg = html.Div([
            html.I(className="fas fa-exclamation-circle me-2"),
            "No data available for selected groups."
        ], className="text-muted text-center py-5")
        empty_cards = [dbc.Col(empty_msg, width=12)]
        return empty_cards, empty_msg, empty_msg, pie_fig

    # Calculate metrics for grid
    means = filtered_df[numeric_cols].mean()
    stds = filtered_df[numeric_cols].std()

    # Create metric cards as clickable buttons
    metric_definitions = [
        ("Length", means["Length"], stds["Length"], "mm", "ruler-horizontal", "metric-length"),
        ("Diameter", means["Diameter"], stds["Diameter"], "mm", "circle", "metric-diameter"),
        ("Thickness", means["Thickness"], stds["Thickness"], "mm", "layer-group", "metric-thickness"),
        ("Weight", means["Weight"], stds["Weight"], "g", "weight-hanging", "metric-weight"),
        ("Slenderness", means["Slenderness"], stds["Slenderness"], "", "arrows-alt-h", "metric-slenderness"),
        ("Sphericity", means["Sphericity"], stds["Sphericity"], "", "globe", "metric-sphericity")
    ]

    metrics_cards = []
    for name, mean_val, std_val, unit, icon, btn_id in metric_definitions:
        card = dbc.Col([
            dbc.Button(
                id=btn_id,
                children=[
                    html.Div([
                        html.I(className=f"fas fa-{icon}", style={
                            "fontSize": "1.5rem",
                            "color": COLORS['secondary'],
                            "marginBottom": "0.5rem"
                        })
                    ]),
                    html.Div(f"{mean_val:.2f} {unit}", className="metric-value"),
                    html.Div(f"± {std_val:.2f}", style={
                        "fontSize": "0.9rem",
                        "color": COLORS['muted'],
                        "fontWeight": "500"
                    }),
                    html.Div(name, className="metric-label mt-2")
                ],
                style={
                    "background": "white",
                    "border": "1px solid #E9ECEF",
                    "borderRadius": "12px",
                    "padding": "0.75rem",
                    "width": "100%",
                    "height": "100%",
                    "textAlign": "center",
                    "color": "inherit",
                    "boxShadow": "0 2px 12px rgba(0,0,0,0.06)",
                    "transition": "transform 0.2s ease, box-shadow 0.2s ease",
                },
                className="metric-card-btn",
                n_clicks=0
            )
        ], width=4, lg=2, className="mb-3")
        metrics_cards.append(card)

    # Correlation content (unchanged)
    corr_cols = ["Length", "Diameter", "Thickness", "Weight"]
    if len(filtered_df) < 2:
        correlation_content = html.Div([
            html.I(className="fas fa-info-circle me-2", style={"color": COLORS['muted']}),
            "Insufficient data points for correlation analysis."
        ], className="text-muted")
    else:
        corr_matrix = filtered_df[corr_cols].corr()
        pairs = [
            ("Weight", "Length"),
            ("Weight", "Diameter"),
            ("Weight", "Thickness"),
            ("Length", "Diameter")
        ]
        corr_items = []
        for x, y in pairs:
            r = corr_matrix.loc[x, y]
            abs_r = abs(r)
            if abs_r >= 0.9:
                strength = "Very Strong"
                color = COLORS['secondary']
                badge_class = "bg-success"
            elif abs_r >= 0.7:
                strength = "Strong"
                color = "#28a745"
                badge_class = "bg-success"
            elif abs_r >= 0.5:
                strength = "Moderate"
                color = "#ffc107"
                badge_class = "bg-warning"
            else:
                strength = "Weak"
                color = COLORS['muted']
                badge_class = "bg-secondary"

            corr_item = html.Div([
                html.Div([
                    html.Div([
                        html.Span(x, style={"fontWeight": "600", "color": COLORS['text']}),
                        html.Span(" vs ", style={"margin": "0 0.5rem", "color": COLORS['muted']}),
                        html.Span(y, style={"fontWeight": "600", "color": COLORS['text']}),
                    ], style={"display": "flex", "alignItems": "center", "marginBottom": "0.25rem"}),
                    html.Div([
                        html.Span(f"r = {r:.3f}", style={
                            "fontWeight": "700",
                            "color": color,
                            "fontSize": "1.1rem",
                            "fontFamily": "Source Sans Pro"
                        }),
                        html.Span(strength, className=f"badge {badge_class} ms-2",
                                  style={"fontSize": "0.75rem", "padding": "0.4em 0.8em"})
                    ])
                ])
            ], className="correlation-item")
            corr_items.append(corr_item)
        correlation_content = html.Div(corr_items)

    # Plot content based on active tab
    if active_tab == "histograms":
        fig = make_subplots(
            rows=2, cols=3,
            subplot_titles=[f"<b>{col}</b>" for col in numeric_cols],
            vertical_spacing=0.12, horizontal_spacing=0.08
        )
        for i, col in enumerate(numeric_cols):
            row = i // 3 + 1
            col_pos = i % 3 + 1
            fig.add_trace(
                go.Histogram(
                    x=filtered_df[col],
                    name=col,
                    marker_color=COLORS['secondary'],
                    opacity=0.85, nbinsx=12,
                    marker_line_color='white', marker_line_width=1,
                    hovertemplate=f'<b>{col}</b><br>Value: %{{x:.2f}}<br>Count: %{{y}}<extra></extra>'
                ),
                row=row, col=col_pos
            )
            mean_val = filtered_df[col].mean()
            # Changed annotation_position from "top" to "top right" to avoid overlapping with subplot title
            fig.add_vline(
                x=mean_val, line_dash="dash", line_color=COLORS['accent'],
                line_width=2, annotation_text=f"μ={mean_val:.1f}",
                annotation_position="top right", annotation_font_size=10,
                row=row, col=col_pos
            )
            fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(0,0,0,0.05)', row=row, col=col_pos)
            fig.update_yaxes(title_text="Frequency" if col_pos == 1 else "",
                             showgrid=True, gridwidth=1, gridcolor='rgba(0,0,0,0.05)', row=row, col=col_pos)
        fig.update_layout(
            height=550, showlegend=False, title_text="",
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(family="Source Sans Pro", size=11), margin=dict(t=40, b=30, l=40, r=30)
        )
        tab_content = dcc.Graph(figure=fig, config={'displayModeBar': 'hover'})

    elif active_tab == "scatter-matrix":
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
                        go.Histogram(x=filtered_df[x_dim], marker_color=COLORS['secondary'], opacity=0.7, showlegend=False),
                        row=i+1, col=j+1
                    )
                elif i > j:
                    if "All" in selected_groups:
                        for size_group in filtered_df["Size Group"].unique():
                            df_group = filtered_df[filtered_df["Size Group"] == size_group]
                            fig.add_trace(
                                go.Scatter(
                                    x=df_group[x_dim], y=df_group[y_dim],
                                    mode='markers', name=size_group,
                                    marker=dict(size=8, color=size_colors.get(size_group, COLORS['primary']),
                                                opacity=0.7, line=dict(width=0.5, color='white')),
                                    showlegend=(i==1 and j==0)
                                ),
                                row=i+1, col=j+1
                            )
                    else:
                        fig.add_trace(
                            go.Scatter(
                                x=filtered_df[x_dim], y=filtered_df[y_dim],
                                mode='markers',
                                marker=dict(size=8, color=COLORS['secondary'],
                                            opacity=0.7, line=dict(width=0.5, color='white')),
                                showlegend=False
                            ),
                            row=i+1, col=j+1
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
                            row=i+1, col=j+1
                        )
                if i == n_dim - 1:
                    fig.update_xaxes(title_text=x_dim, row=i+1, col=j+1)
                if j == 0:
                    fig.update_yaxes(title_text=y_dim, row=i+1, col=j+1)
                fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(0,0,0,0.05)', row=i+1, col=j+1)
                fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(0,0,0,0.05)', row=i+1, col=j+1)
        fig.update_layout(
            height=700,
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(family="Source Sans Pro", size=10), margin=dict(t=30, b=30, l=50, r=30),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                        bgcolor='rgba(255,255,255,0.8)') if "All" in selected_groups else {}
        )
        tab_content = dcc.Graph(figure=fig, config={'displayModeBar': 'hover'})

    else:  # box-plots
        if "All" in selected_groups and len(filtered_df["Size Group"].unique()) > 1:
            fig = make_subplots(
                rows=2, cols=3,
                subplot_titles=[f"<b>{col}</b>" for col in numeric_cols],
                vertical_spacing=0.12, horizontal_spacing=0.08
            )
            for i, col in enumerate(numeric_cols):
                row = i // 3 + 1
                col_pos = i % 3 + 1
                for size_group in ["Small", "Medium", "Large"]:
                    if size_group in filtered_df["Size Group"].values:
                        data = filtered_df[filtered_df["Size Group"] == size_group][col]
                        fig.add_trace(
                            go.Box(
                                y=data, name=size_group, legendgroup=size_group,
                                showlegend=(i == 0),
                                marker_color=size_colors[size_group],
                                line=dict(color=size_colors[size_group]),
                                boxmean=True, boxpoints='outliers'
                            ),
                            row=row, col=col_pos
                        )
                fig.update_xaxes(showticklabels=False, row=row, col=col_pos)
                fig.update_yaxes(title_text=col if col_pos == 1 else "",
                                 showgrid=True, gridcolor='rgba(0,0,0,0.05)', row=row, col=col_pos)
            fig.update_layout(
                height=600, boxmode="group",
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font=dict(family="Source Sans Pro", size=11), margin=dict(t=40, b=30, l=50, r=30),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
                boxgap=0.1, boxgroupgap=0.1
            )
        else:
            fig = make_subplots(
                rows=2, cols=3,
                subplot_titles=[f"<b>{col}</b>" for col in numeric_cols],
                vertical_spacing=0.12, horizontal_spacing=0.08
            )
            for i, col in enumerate(numeric_cols):
                row = i // 3 + 1
                col_pos = i % 3 + 1
                fig.add_trace(
                    go.Box(
                        y=filtered_df[col], marker_color=COLORS['secondary'],
                        line=dict(color=COLORS['secondary']),
                        boxmean=True, boxpoints='outliers', name=col
                    ),
                    row=row, col=col_pos
                )
                fig.update_xaxes(showticklabels=False, row=row, col=col_pos)
                fig.update_yaxes(title_text=col if col_pos == 1 else "",
                                 showgrid=True, gridcolor='rgba(0,0,0,0.05)', row=row, col=col_pos)
            fig.update_layout(
                height=600, showlegend=False,
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font=dict(family="Source Sans Pro", size=11), margin=dict(t=40, b=30, l=50, r=30),
                boxgap=0.2
            )
        tab_content = dcc.Graph(figure=fig, config={'displayModeBar': 'hover'})

    return metrics_cards, correlation_content, tab_content, pie_fig


# 3. Callback to update selected property based on metric button clicks
@app.callback(
    Output("selected-property", "data"),
    [Input("metric-length", "n_clicks"),
     Input("metric-diameter", "n_clicks"),
     Input("metric-thickness", "n_clicks"),
     Input("metric-weight", "n_clicks"),
     Input("metric-slenderness", "n_clicks"),
     Input("metric-sphericity", "n_clicks")],
    prevent_initial_call=True
)
def select_property(length_clicks, diameter_clicks, thickness_clicks, weight_clicks, slenderness_clicks, sphericity_clicks):
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    mapping = {
        "metric-length": "Length",
        "metric-diameter": "Diameter",
        "metric-thickness": "Thickness",
        "metric-weight": "Weight",
        "metric-slenderness": "Slenderness",
        "metric-sphericity": "Sphericity"
    }
    return mapping.get(button_id, "Weight")


# 4. Callback to update property stats content and title
@app.callback(
    [Output("property-stats-content", "children"),
     Output("property-stats-title", "children")],
    [Input("size-filter", "value"),
     Input("selected-property", "data")]
)
def update_property_stats(selected_groups, prop):
    # Filter data
    if "All" in selected_groups:
        filtered_df = df
    else:
        if not selected_groups:
            filtered_df = pd.DataFrame(columns=df.columns)
        else:
            filtered_df = df[df["Size Group"].isin(selected_groups)]

    if filtered_df.empty:
        return html.Div("No data available", className="text-muted"), f"{prop} Distribution"

    # Compute stats for the selected property
    data = filtered_df[prop]
    mean_val = data.mean()
    std_val = data.std()
    cv = (std_val / mean_val * 100) if mean_val != 0 else 0
    min_val = data.min()
    max_val = data.max()
    range_val = max_val - min_val

    stats_content = html.Div([
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.Div("Mean ± SD", className="metric-label"),
                    html.Div(f"{mean_val:.2f} ± {std_val:.2f} {('g' if prop=='Weight' else 'mm' if prop in ['Length','Diameter','Thickness'] else '')}",
                             className="metric-value", style={"fontSize": "1.4rem", "color": COLORS['primary']})
                ], className="mb-3")
            ], width=6),
            dbc.Col([
                html.Div([
                    html.Div("Coefficient of Variation", className="metric-label"),
                    html.Div(f"{cv:.1f}%", className="metric-value",
                             style={"fontSize": "1.4rem", "color": COLORS['accent']})
                ], className="mb-3")
            ], width=6),
        ]),
        html.Hr(style={"margin": "1rem 0"}),
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.Div("Range", className="metric-label"),
                    html.Div(f"{min_val:.2f} - {max_val:.2f} {('g' if prop=='Weight' else 'mm' if prop in ['Length','Diameter','Thickness'] else '')}",
                             style={"fontSize": "1.1rem", "fontWeight": "600", "color": COLORS['text']})
                ])
            ], width=6),
            dbc.Col([
                html.Div([
                    html.Div("Span", className="metric-label"),
                    html.Div(f"{range_val:.2f} {('g' if prop=='Weight' else 'mm' if prop in ['Length','Diameter','Thickness'] else '')}",
                             style={"fontSize": "1.1rem", "fontWeight": "600", "color": COLORS['text']})
                ])
            ], width=6),
        ])
    ])

    title = f"{prop} Distribution"
    return stats_content, title


# 5. Callback to highlight the selected metric card
@app.callback(
    [Output("metric-length", "style"),
     Output("metric-diameter", "style"),
     Output("metric-thickness", "style"),
     Output("metric-weight", "style"),
     Output("metric-slenderness", "style"),
     Output("metric-sphericity", "style")],
    [Input("selected-property", "data")]
)
def highlight_selected(selected_prop):
    base_style = {
        "background": "white",
        "border": "1px solid #E9ECEF",
        "borderRadius": "12px",
        "padding": "0.75rem",
        "width": "100%",
        "height": "100%",
        "textAlign": "center",
        "color": "inherit",
        "boxShadow": "0 2px 12px rgba(0,0,0,0.06)",
        "transition": "transform 0.2s ease, box-shadow 0.2s ease",
    }
    selected_style = base_style.copy()
    selected_style["border"] = "2px solid #048A81"
    selected_style["boxShadow"] = "0 0 0 2px rgba(4, 138, 129, 0.2)"

    styles = []
    for prop in ["Length", "Diameter", "Thickness", "Weight", "Slenderness", "Sphericity"]:
        if prop == selected_prop:
            styles.append(selected_style)
        else:
            styles.append(base_style)
    return styles


# 6. Callback to open modal
@app.callback(
    [Output("plot-modal", "is_open"),
     Output("modal-plot", "figure"),
     Output("modal-title", "children")],
    [Input("expand-plot-btn", "n_clicks")],
    [State("size-filter", "value"),
     State("plot-tabs", "value")],
    prevent_initial_call=True
)
def open_modal(n_clicks, selected_groups, active_tab):
    if n_clicks is None:
        return False, go.Figure(), "Expanded View"

    # Filter data
    if "All" in selected_groups:
        filtered_df = df
    else:
        if not selected_groups:
            filtered_df = pd.DataFrame(columns=df.columns)
        else:
            filtered_df = df[df["Size Group"].isin(selected_groups)]

    if filtered_df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No data available", showarrow=False)
    else:
        if active_tab == "histograms":
            fig = make_subplots(
                rows=2, cols=3,
                subplot_titles=[f"<b>{col}</b>" for col in numeric_cols],
                vertical_spacing=0.12, horizontal_spacing=0.08
            )
            for i, col in enumerate(numeric_cols):
                row = i // 3 + 1
                col_pos = i % 3 + 1
                fig.add_trace(
                    go.Histogram(
                        x=filtered_df[col],
                        marker_color=COLORS['secondary'],
                        opacity=0.85, nbinsx=12,
                        marker_line_color='white', marker_line_width=1,
                        hovertemplate=f'<b>{col}</b><br>Value: %{{x:.2f}}<br>Count: %{{y}}<extra></extra>'
                    ),
                    row=row, col=col_pos
                )
                mean_val = filtered_df[col].mean()
                # Changed annotation_position to "top right" here as well
                fig.add_vline(
                    x=mean_val, line_dash="dash", line_color=COLORS['accent'],
                    line_width=2, annotation_text=f"μ={mean_val:.1f}",
                    annotation_position="top right", annotation_font_size=10,
                    row=row, col=col_pos
                )
                fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(0,0,0,0.05)', row=row, col=col_pos)
                fig.update_yaxes(title_text="Frequency" if col_pos == 1 else "",
                                 showgrid=True, gridwidth=1, gridcolor='rgba(0,0,0,0.05)', row=row, col=col_pos)
            fig.update_layout(
                showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font=dict(family="Source Sans Pro", size=11), margin=dict(t=40, b=30, l=40, r=30)
            )
        elif active_tab == "scatter-matrix":
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
                            go.Histogram(x=filtered_df[x_dim], marker_color=COLORS['secondary'], opacity=0.7, showlegend=False),
                            row=i+1, col=j+1
                        )
                    elif i > j:
                        if "All" in selected_groups:
                            for size_group in filtered_df["Size Group"].unique():
                                df_group = filtered_df[filtered_df["Size Group"] == size_group]
                                fig.add_trace(
                                    go.Scatter(
                                        x=df_group[x_dim], y=df_group[y_dim],
                                        mode='markers', name=size_group,
                                        marker=dict(size=8, color=size_colors.get(size_group, COLORS['primary']),
                                                    opacity=0.7, line=dict(width=0.5, color='white')),
                                        showlegend=(i==1 and j==0)
                                    ),
                                    row=i+1, col=j+1
                                )
                        else:
                            fig.add_trace(
                                go.Scatter(
                                    x=filtered_df[x_dim], y=filtered_df[y_dim],
                                    mode='markers',
                                    marker=dict(size=8, color=COLORS['secondary'],
                                                opacity=0.7, line=dict(width=0.5, color='white')),
                                    showlegend=False
                                ),
                                row=i+1, col=j+1
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
                                row=i+1, col=j+1
                            )
                    if i == n_dim - 1:
                        fig.update_xaxes(title_text=x_dim, row=i+1, col=j+1)
                    if j == 0:
                        fig.update_yaxes(title_text=y_dim, row=i+1, col=j+1)
                    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(0,0,0,0.05)', row=i+1, col=j+1)
                    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(0,0,0,0.05)', row=i+1, col=j+1)
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font=dict(family="Source Sans Pro", size=10), margin=dict(t=30, b=30, l=50, r=30),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                            bgcolor='rgba(255,255,255,0.8)') if "All" in selected_groups else {}
            )
        else:  # box-plots
            if "All" in selected_groups and len(filtered_df["Size Group"].unique()) > 1:
                fig = make_subplots(
                    rows=2, cols=3,
                    subplot_titles=[f"<b>{col}</b>" for col in numeric_cols],
                    vertical_spacing=0.12, horizontal_spacing=0.08
                )
                for i, col in enumerate(numeric_cols):
                    row = i // 3 + 1
                    col_pos = i % 3 + 1
                    for size_group in ["Small", "Medium", "Large"]:
                        if size_group in filtered_df["Size Group"].values:
                            data = filtered_df[filtered_df["Size Group"] == size_group][col]
                            fig.add_trace(
                                go.Box(
                                    y=data, name=size_group, legendgroup=size_group,
                                    showlegend=(i == 0),
                                    marker_color=size_colors[size_group],
                                    line=dict(color=size_colors[size_group]),
                                    boxmean=True, boxpoints='outliers'
                                ),
                                row=row, col=col_pos
                            )
                    fig.update_xaxes(showticklabels=False, row=row, col=col_pos)
                    fig.update_yaxes(title_text=col if col_pos == 1 else "",
                                     showgrid=True, gridcolor='rgba(0,0,0,0.05)', row=row, col=col_pos)
                fig.update_layout(
                    boxmode="group",
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(family="Source Sans Pro", size=11), margin=dict(t=40, b=30, l=50, r=30),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
                    boxgap=0.1, boxgroupgap=0.1
                )
            else:
                fig = make_subplots(
                    rows=2, cols=3,
                    subplot_titles=[f"<b>{col}</b>" for col in numeric_cols],
                    vertical_spacing=0.12, horizontal_spacing=0.08
                )
                for i, col in enumerate(numeric_cols):
                    row = i // 3 + 1
                    col_pos = i % 3 + 1
                    fig.add_trace(
                        go.Box(
                            y=filtered_df[col], marker_color=COLORS['secondary'],
                            line=dict(color=COLORS['secondary']),
                            boxmean=True, boxpoints='outliers', name=col
                        ),
                        row=row, col=col_pos
                    )
                    fig.update_xaxes(showticklabels=False, row=row, col=col_pos)
                    fig.update_yaxes(title_text=col if col_pos == 1 else "",
                                     showgrid=True, gridcolor='rgba(0,0,0,0.05)', row=row, col=col_pos)
                fig.update_layout(
                    showlegend=False,
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(family="Source Sans Pro", size=11), margin=dict(t=40, b=30, l=50, r=30),
                    boxgap=0.2
                )

    tab_names = {
        "histograms": "Distribution Analysis",
        "scatter-matrix": "Correlation Matrix",
        "box-plots": "Comparative Box Plots"
    }
    title = f"Expanded View: {tab_names.get(active_tab, 'Plot')}"
    return True, fig, title


# 7. Callback to close modal
@app.callback(
    Output("plot-modal", "is_open", allow_duplicate=True),
    Input("close-modal-btn", "n_clicks"),
    State("plot-modal", "is_open"),
    prevent_initial_call=True
)
def close_modal(n_clicks, is_open):
    if n_clicks:
        return False
    return is_open


if __name__ == "__main__":
    app.run(debug=True)