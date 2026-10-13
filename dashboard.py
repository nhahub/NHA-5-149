import pandas as pd
from pathlib import Path
from dash import Dash, dcc, html, Input, Output
import plotly.express as px

# ----------------------------------
# 1. Load and prepare the data
# ----------------------------------

BASE_DIR = Path(__file__).resolve().parent
DATASET_DIR = BASE_DIR / "dataset"

train = pd.read_csv(DATASET_DIR / "train.csv", low_memory=False)
store = pd.read_csv(DATASET_DIR / "store.csv")

train["Date"] = pd.to_datetime(train["Date"])

df = train.merge(
    store[["Store", "StoreType"]],
    on="Store",
    how="left"
)

df["Month"] = df["Date"].dt.to_period("M").astype(str)

day_names = {
    1: "Monday",
    2: "Tuesday",
    3: "Wednesday",
    4: "Thursday",
    5: "Friday",
    6: "Saturday",
    7: "Sunday"
}

df["DayName"] = df["DayOfWeek"].map(day_names)

days_order = [
    "Monday", "Tuesday", "Wednesday", "Thursday",
    "Friday", "Saturday", "Sunday"
]

months = sorted(df["Month"].unique())
stores = sorted(df["Store"].unique())
store_types = sorted(df["StoreType"].dropna().unique())

# ----------------------------------
# 2. Create the Dash application
# ----------------------------------

app = Dash(__name__)

app.layout = html.Div(
    style={
        "fontFamily": "Arial",
        "backgroundColor": "#f4f6f9",
        "padding": "25px"
    },
    children=[
        html.H1(
            "Rossmann Store Sales Dashboard",
            style={"textAlign": "center", "color": "#17365D"}
        ),

        html.P(
            "Explore sales trends, promotions, customers, and store types.",
            style={"textAlign": "center", "fontSize": "16px"}
        ),

        # Filters
        html.Div(
            style={
                "display": "grid",
                "gridTemplateColumns": "repeat(5, minmax(150px, 1fr))",
                "gap": "15px",
                "backgroundColor": "white",
                "padding": "20px",
                "borderRadius": "10px"
            },
            children=[
                html.Div([
                    html.Label("Store"),
                    dcc.Dropdown(
                        id="store-filter",
                        options=[
                            {"label": str(s), "value": s}
                            for s in stores
                        ],
                        multi=True,
                        placeholder="All stores"
                    )
                ]),

                html.Div([
                    html.Label("Month"),
                    dcc.Dropdown(
                        id="month-filter",
                        options=[
                            {"label": m, "value": m}
                            for m in months
                        ],
                        multi=True,
                        placeholder="All months"
                    )
                ]),

                html.Div([
                    html.Label("Store Type"),
                    dcc.Dropdown(
                        id="type-filter",
                        options=[
                            {"label": t, "value": t}
                            for t in store_types
                        ],
                        multi=True,
                        placeholder="All store types"
                    )
                ]),

                html.Div([
                    html.Label("Promotion"),
                    dcc.Dropdown(
                        id="promo-filter",
                        options=[
                            {"label": "With promotion", "value": 1},
                            {"label": "Without promotion", "value": 0}
                        ],
                        multi=False,
                        placeholder="All promotions"
                    )
                ]),

                html.Div([
                    html.Label("Day of Week"),
                    dcc.Dropdown(
                        id="day-filter",
                        options=[
                            {"label": day, "value": day}
                            for day in days_order
                        ],
                        multi=True,
                        placeholder="All days"
                    )
                ])
            ]
        ),

        # Six charts
        html.Div(
            style={
                "display": "grid",
                "gridTemplateColumns": "repeat(2, minmax(0, 1fr))",
                "gap": "20px",
                "marginTop": "25px"
            },
            children=[
                dcc.Graph(id="sales-over-time"),
                dcc.Graph(id="sales-by-month"),
                dcc.Graph(id="sales-by-day"),
                dcc.Graph(id="sales-by-promo"),
                dcc.Graph(id="customers-vs-sales"),
                dcc.Graph(id="sales-by-type")
            ]
        )
    ]
)

# ----------------------------------
# 3. Update charts when filters change
# ----------------------------------

@app.callback(
    Output("sales-over-time", "figure"),
    Output("sales-by-month", "figure"),
    Output("sales-by-day", "figure"),
    Output("sales-by-promo", "figure"),
    Output("customers-vs-sales", "figure"),
    Output("sales-by-type", "figure"),
    Input("store-filter", "value"),
    Input("month-filter", "value"),
    Input("type-filter", "value"),
    Input("promo-filter", "value"),
    Input("day-filter", "value")
)
def update_dashboard(selected_stores, selected_months,
                     selected_types, selected_promo, selected_days):

    filtered = df

    if selected_stores:
        filtered = filtered[
            filtered["Store"].isin(selected_stores)
        ]

    if selected_months:
        filtered = filtered[
            filtered["Month"].isin(selected_months)
        ]

    if selected_types:
        filtered = filtered[
            filtered["StoreType"].isin(selected_types)
        ]

    if selected_promo is not None:
        filtered = filtered[
            filtered["Promo"] == selected_promo
        ]

    if selected_days:
        filtered = filtered[
            filtered["DayName"].isin(selected_days)
        ]

    # Chart 1: Total sales over time
    time_data = (
        filtered.groupby("Date", as_index=False)["Sales"]
        .sum()
        .sort_values("Date")
    )

    fig1 = px.line(
        time_data,
        x="Date",
        y="Sales",
        title="Sales Over Time",
        labels={"Sales": "Total Sales", "Date": "Date"}
    )

    # Chart 2: Total sales by month
    month_data = (
        filtered.groupby("Month", as_index=False)["Sales"]
        .sum()
        .sort_values("Month")
    )

    fig2 = px.bar(
        month_data,
        x="Month",
        y="Sales",
        title="Sales by Month",
        labels={"Sales": "Total Sales", "Month": "Month"}
    )

    # Chart 3: Total sales by day of week
    day_data = filtered.groupby(
        ["DayOfWeek", "DayName"], as_index=False
    )["Sales"].sum()

    day_data = day_data.sort_values("DayOfWeek")

    fig3 = px.bar(
        day_data,
        x="DayName",
        y="Sales",
        category_orders={"DayName": days_order},
        title="Sales by Day of Week",
        labels={"Sales": "Total Sales", "DayName": "Day"}
    )

    # Chart 4: Sales with and without promotions
    promo_data = filtered.groupby(
        "Promo", as_index=False
    )["Sales"].sum()

    promo_data["Promotion"] = promo_data["Promo"].map({
        0: "Without Promotion",
        1: "With Promotion"
    })

    fig4 = px.bar(
        promo_data,
        x="Promotion",
        y="Sales",
        title="Sales With vs Without Promotion",
        labels={"Sales": "Total Sales", "Promotion": "Promotion Status"}
    )

    # Chart 5: Relationship between customers and sales
    scatter_data = filtered[
        ["Customers", "Sales", "Store", "Date"]
    ].dropna()

    if len(scatter_data) > 4000:
        scatter_data = scatter_data.sample(
            n=4000, random_state=42
        )

    fig5 = px.scatter(
        scatter_data,
        x="Customers",
        y="Sales",
        color="Store",
        title="Customers vs Sales",
        labels={
            "Customers": "Number of Customers",
            "Sales": "Sales"
        },
        hover_data=["Date"]
    )

    # Chart 6: Total sales by store type
    type_data = (
        filtered.groupby("StoreType", as_index=False)["Sales"]
        .sum()
        .sort_values("StoreType")
    )

    fig6 = px.bar(
        type_data,
        x="StoreType",
        y="Sales",
        title="Sales by Store Type",
        labels={"Sales": "Total Sales", "StoreType": "Store Type"}
    )

    # Common chart formatting
    figures = [fig1, fig2, fig3, fig4, fig5, fig6]

    for fig in figures:
        fig.update_layout(
            template="plotly_white",
            title_x=0.5,
            margin=dict(l=40, r=20, t=65, b=45)
        )

    return fig1, fig2, fig3, fig4, fig5, fig6


# ----------------------------------
# 4. Run the application
# ----------------------------------

if __name__ == "__main__":
    app.run(debug=True)