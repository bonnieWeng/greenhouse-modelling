import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import numpy as np
import plotly.graph_objs as go
from dash.dependencies import Input, Output
import base64

# Import backend simulation
from sim_storage import storage_calc
from sim_water_lighting import water_price, greenhouse_transmissivity
from sim_water_lighting import amb_light, deficiency, Light_Sel, TOU_ON, Ambient_Switching
from sim_final_profiles import final_day_profile
"""
Notes:
Current this version uses dummy data to plot monthly energy savings and peaks
"""

app = dash.Dash(external_stylesheets=[dbc.themes.MINTY])

# Insert greenhouse structure picture
GREENHOUSE_PIC = 'figures/footprint_greenhouse.png'
test_base64 = base64.b64encode(open(GREENHOUSE_PIC, 'rb').read()).decode('ascii')

# Control Panel 1: Greenhouse Structure
controls1 = dbc.Card(
    [
        dbc.FormGroup(
            [
                dbc.Label("Greenhouse Structure"),
                dcc.Dropdown(
                    id="structure-dropdown",
                    options=[
                        {'label': 'A-frame', 'value': 'A-frame'},
                        {'label': 'Quonset', 'value': 'Quonset'}
                    ],
                    value="A-frame",
                ),
            ]
        ),

        dbc.FormGroup(
            [
                dbc.Label("Length A"),
                dbc.Input(id="length-A", type="number", placeholder="Enter length"),
            ]
        ),

        dbc.FormGroup(
            [
                dbc.Label("Length B"),
                dbc.Input(id="length-B", type="number", placeholder="Enter length"),
            ]
        ),

        dbc.FormGroup(
            [
                dbc.Label("Length C"),
                dbc.Input(id="length-C", type="number", placeholder="Enter length"),
            ]
        ),

        dbc.FormGroup(
            [
                dbc.Label("Length D"),
                dbc.Input(id="length-D", type="number", placeholder="Enter length"),
            ]
        ),

        dbc.FormGroup(
            [
                dbc.Label("Length E"),
                dbc.Input(id="length-E", type="number", placeholder="Enter length"),
            ]
        ),
    ],
    body=True,
    color='light'
)

# Control Panel 2: crop, lighting, photo period start, end
controls2 = dbc.Card(
    [   
        # Crop Type
        dbc.FormGroup(
            [
                dbc.Label("Crop Type"),
                dcc.Dropdown(
                    id="crop-dropdown",
                    options=[
                        {'label': 'Tomato', 'value': 'Tomato'},
                        {'label': 'Pepper', 'value': 'Pepper'},
                        {'label': 'Cucumber', 'value': 'Cucumber'},
                        {'label': 'Cannabis', 'value': 'Cannabis'}
                    ],
                    value="Tomato",
                ),
            ]
        ),

        # Photoperiod Start Time
        dbc.FormGroup(
            [
                dbc.Label("Photoperiod Start Time"),
                dcc.Dropdown(
                    id="photoperiod-start-dropdown",
                    options=[
                        {'label': '1 AM', 'value': 1},
                        {'label': '2 AM', 'value': 2},
                        {'label': '3 AM', 'value': 3},
                        {'label': '4 AM', 'value': 4},
                        {'label': '5 AM', 'value': 5},
                        {'label': '6 AM', 'value': 6},
                        {'label': '7 AM', 'value': 7},
                        {'label': '8 AM', 'value': 8},
                        {'label': '9 AM', 'value': 9},
                        {'label': '10 AM', 'value': 10},
                        {'label': '11 AM', 'value': 11},
                        {'label': '12 PM', 'value': 12},
                    ],
                    value=6,
                ),
            ]
        ),

        # Photoperiod End Time
        dbc.FormGroup(
            [
                dbc.Label("Photoperiod End Time"),
                dcc.Dropdown(
                    id="photoperiod-end-dropdown",
                    options=[
                        {'label': '1 PM', 'value': 13},
                        {'label': '2 PM', 'value': 14},
                        {'label': '3 PM', 'value': 15},
                        {'label': '4 PM', 'value': 16},
                        {'label': '5 PM', 'value': 17},
                        {'label': '6 PM', 'value': 18},
                        {'label': '7 PM', 'value': 19},
                        {'label': '8 PM', 'value': 20},
                        {'label': '9 PM', 'value': 21},
                        {'label': '10 PM', 'value': 22},
                        {'label': '11 PM', 'value': 23},
                        {'label': '12 AM', 'value': 24},
                    ],
                    value=18,
                ),
            ]
        ),
    ],
    body=True,
    color='light'
)

# Control Panel 3: heating fuel, heater, wall material, window material
controls3 = dbc.Card(
    [   
        # Heating Fuel Type
        dbc.FormGroup(
            [
                dbc.Label("Heating Fuel Type"),
                dcc.Dropdown(
                    id="fuel-dropdown",
                    options=[
                        {'label': 'Natural Gas', 'value': 'Natural Gas'},
                        {'label': 'Oil 2', 'value': 'Oil 2'},
                        {'label': 'Oil 4', 'value': 'Oil 4'},
                        {'label': 'Propane', 'value': 'Propane'},
                        {'label': 'Electricity', 'value': 'Electricity'},
                        {'label': 'Butane', 'value': 'Butane'},
                        {'label': 'Kerosene', 'value': 'Kerosene'},
                    ],
                    value="Natural Gas",
                ),
            ]
        ),

        # Wall Material (The model assumed a fixed wall and window ratio)
        dbc.FormGroup(
            [
                dbc.Label("Material (Conduction)"),
                dcc.Dropdown(
                    id="material-conduction-dropdown",
                    options=[
                        {'label': 'Corrugated Polycarbonate', 'value': 'Corrugated Polycarbonate'},
                        {'label': 'Glass', 'value': 'Glass'},
                        {'label': 'Glass - Double Layer', 'value': 'Glass - Double Layer'},
                        {'label': 'Fiber Glass', 'value': 'Fiber Glass'},
                        {'label': 'Polyethylene', 'value': 'Polyethylene'},
                        {'label': 'Polyethylene - Double Layer', 'value': 'Polyethylene - Double Layer'},
                        {'label': 'Polycarbonate Bi-Wall', 'value': 'Polycarbonate Bi-Wall'},
                        {'label': 'Polycarbonate Tri-Wall', 'value': 'Polycarbonate Tri-Wall'},
                        {'label': 'Acrylic Bi-Wall', 'value': 'Acrylic Bi-Wall'},
                        {'label': 'IR Film', 'value': 'IR Film'},
                        {'label': 'IR Film - Double Layer', 'value': 'IR Film - Double Layer'},
                        {'label': 'Concrete Block', 'value': 'Concrete Block'},
                        {'label': 'Concrete Poured', 'value': 'Concrete Poured'},
                        {'label': 'Concrete Insulated', 'value': 'Concrete Insulated'},
                        {'label': 'Solid Insulation Foam', 'value': 'Solid Insulation Foam'},
                    ],
                    value="Glass",
                ),
            ]
        ),

        # Window Material (The model assumed a fixed wall and window ratio)
        dbc.FormGroup(
            [
                dbc.Label("Material (Convection)"),
                dcc.Dropdown(
                    id="material-convection-dropdown",
                    options=[
                        {'label': 'Mobile Air Curtain', 'value': 'Mobile Air Curtain'},
                        {'label': 'Stationary Air Curtain', 'value': 'Stationary Air Curtain'},
                        {'label': 'White Spun Bonded Polyolefin Film', 'value': 'White Spun Bonded Polyolefin Film'},
                        {'label': 'Grey Spun Bonded Polyolefin Film', 'value': 'Grey Spun Bonded Polyolefin Film'},
                        {'label': 'Clear Polyethylene', 'value': 'Clear Polyethylene'},
                        {'label': 'Black Polyethylene', 'value': 'Black Polyethylene'},
                        {'label': 'Grey Spun Bonded Polyolefin Film (Heavy)', 'value': 'Grey Spun Bonded Polyolefin Film (Heavy)'},
                        {'label': 'Aluminum - Clear Vinyl Fabric', 'value': 'Aluminum - Clear Vinyl Fabric'},
                        {'label': 'Aluminized Fabric', 'value': 'Aluminized Fabric'},
                        {'label': 'Aluminum - Black Vinyl Fabric', 'value': 'Aluminum - Black Vinyl Fabric'},
                        {'label': 'Double Layer Spun Bonded Polyester', 'value': 'Double Layer Spun Bonded Polyester'},

                    ],
                    value="Clear Polyethylene",
                ),
            ]
        ),
    ],
    body=True,
    color='light'
)

# Control Panel 4: Energy Storage Related
controls4 = dbc.Card(
    [
        # Energy Storage Type
        dbc.FormGroup(
            [
                dbc.Label("Energy Storage Type"),
                dcc.Dropdown(
                    id="energy-storage-type-dropdown",
                    options=[
                        {'label': 'Lithium Ion Batteries', 'value': 'Lithium Ion'},
                        {'label': 'Lead Acid Batteries', 'value': 'Lead Acid'},
                        {'label': 'Alkaline Batteries', 'value': 'Alkaline'},
                        {'label': 'Compressed Air', 'value': 'Compressed Air'},
                        {'label': 'Nickel Cadmium Batteries', 'value': 'Nickel Cadmium'},
                    ],
                    value="Lithium Ion",
                ),
            ]
        ),

        # Energy Storage Calculation Method
        dbc.FormGroup(
            [
                dbc.Label("Optimisation Objective for Energy Storage Calculations"),
                dcc.Dropdown(
                    id="optimisation-dropdown",
                    options=[
                        {'label': 'Minimize Cost', 'value': 'cost'},
                        {'label': 'Flatten Electricity Peak', 'value': 'profile'}
                    ],
                    value='cost',
                ),
            ],
        ),

        # Energy Storage Power Specification
        dbc.FormGroup(
            [
                dbc.Label("Power Capacity (kW)"),
                dbc.Input(id="power-capacity", type="number", placeholder="Enter Power Capacity"),
            ]
        ),

        # Energy Storage Energy Specification
        dbc.FormGroup(
            [
                dbc.Label("Energy Capacity (kWh)"),
                dbc.Input(id="energy-capacity", type="number", placeholder="Enter Energy Capacity"),
            ],
        ),
    ],
    body=True,
    color='light',
)

# Display info for lighting, photoperiod and water
lighting_card = dbc.Card(
    dbc.CardBody([
        html.H4("Lighting Recommendation", className="card-title"),
        html.H4(),
        html.H5("None", className="card-subtitle", id = 'light-choice'),
        html.H4(),
        html.H5("None", className="card-subtitle", id = 'light-upfront-cost'),
        html.H4(),
        html.H5("None", className="card-subtitle", id = 'light-fixture-est'),
        html.H4(),
        html.H5("None", className="card-subtitle", id = 'hourly-elec-consumption'),
        html.H4(),
        html.H5("None", className="card-subtitle", id = 'light-annual-cost'),
        html.H4(),
        html.H5("None", className="card-subtitle", id = 'light-energy-savings'),
    ]),
    color="primary",
    inverse=True
    )

water_card = dbc.Card(
    dbc.CardBody([
        html.H4("PPFD", className="card-title"),
        html.H4(),
        html.H5("None", className="card-subtitle", id = 'light-max-PPFD'),
        html.H4(),
        html.H5("None", className="card-subtitle", id = 'light-min-PPFD'),
        html.Br(),
        html.H4("Water Usage", className="card-title"),
        html.H4(),
        html.H5("None", className="card-subtitle", id = 'water-consumption'),
        html.H4(),
        html.H5("None", className="card-subtitle", id = 'water-cost'),
    ]),
    color="primary",
    inverse=True
    )

# Create months for slider
month_array = np.arange(1, 13, 1)

# Define website layout
app.layout = dbc.Container(
    [
        html.H1("OK Bloomer"),
        html.H2("A Decision Support Tool for Greenhouse Design"),
        html.Hr(),
        html.H2("User Inputs:"),
        dbc.Row(
            [
                dbc.Col(controls2, md=2),
                dbc.Col(controls3, md=2),
                dbc.Col(controls4, md=3),
                dbc.Col(controls1, md=2),
                dbc.Col(html.Img(src='data:image/png;base64,{}'.format(test_base64)), md=2),
            ],
        ),

        html.Hr(),
        html.H2("Simulation Outputs:"),
        dbc.Row(
            [
                dbc.Col(id='lighting_card', children=[lighting_card], md=6),
                dbc.Col(id='water_card', children=[water_card], md=6)
            ]
        ),

        html.H2(),
        #html.H3("Energy Storage"),

        # Output graphs
        # Electricity and energy profiles
        dbc.Row(
            [
                dbc.Col([dcc.Graph(id="daily-energy-demand"),
                         dcc.Slider(
                            id='month-slider',
                            min=month_array.min(),
                            max=month_array.max(),
                            value=month_array.min(),
                            marks={str(month): str(month) for month in month_array},
                            step=None)
                        ], md=6),
                dbc.Col(dcc.Graph(id="monthly-electricity-peaks"), md=6),
            ],
            align="center",
        ),

        # Energy storage calculations
        dbc.Row(
            [
                dbc.Col(dcc.Graph(id="monthly-electricity-savings"), md=6),
                dbc.Col(dcc.Graph(id="monthly-GHG-emission"), md=6)
            ],
            align="center",
        ),
    ],
    fluid=True,
)

# Callback functions
@app.callback(
    [Output('hourly-elec-consumption', 'children'),
     Output('light-annual-cost', 'children'),
     Output('light-energy-savings', 'children'),
     Output('light-choice', 'children'),
     Output('light-upfront-cost', 'children'),
     Output('light-fixture-est', 'children'),
     Output('light-max-PPFD', 'children'),
     Output('light-min-PPFD', 'children'),
     Output('water-consumption', 'children'),
     Output('water-cost', 'children')],
    [Input('structure-dropdown', 'value'),
     Input('length-A', 'value'),
     Input('length-B', 'value'),
     Input('length-C', 'value'),
     Input('length-D', 'value'),
     Input('length-E', 'value'),
     Input('crop-dropdown', 'value'),
     Input('photoperiod-start-dropdown', 'value'),
     Input('photoperiod-end-dropdown', 'value'),
     Input('material-conduction-dropdown', 'value'),
     ])
def display_single_values(structure_type, a, b, c, d, e, crop_type, photo_start, photo_end, window_material):
    # Wait for users to reach
    if structure_type is None:
        structure_type = 'A-frame'
    if a is None:
        a = 10
    if b is None:
        b = 10
    if c is None:
        c = 10
    if d is None:
        d = 10
    if e is None:
        e = 10
    if crop_type is None:
        crop_type = 'Tomato'
    if photo_start is None:
        photo_start = 6
    if photo_end is None:
        photo_end = 19
    if window_material is None:
        window_material = 'Glass'
    
    # Calculate surface area
    if structure_type == 'A-frame':
        area = np.round(2*(a*c + b*c + e*b + a*d), 2)
    elif structure_type == 'Quonset':
        area = np.round((a*b)*np.pi/2 + (np.power(a,2))*np.pi/4, 2)

    # Function calls to backend
    plant_num, cost_min, cost_max, wmin_req, wmax_req = water_price(area, crop_type)
    water_consumption = 'Daily water requirement:  {} - {}L'.format(wmin_req, wmax_req)  # return water_consumption
    water_cost = water_cost = 'Daily water cost:  ${} - ${}'.format(cost_min, cost_max)

    trans = greenhouse_transmissivity(window_material)
    array, PPFD_max, PPFD_avg = amb_light(trans)
    photo = photo_end - photo_start
    crop_PPFDmin, crop_PPFDmax = deficiency(array, crop_type, photo)
    max_PPFD = 'Maximum PPFD Requirement:  {} Micromols/m\u00b2/s'.format(crop_PPFDmax)
    min_PPFD = 'Minimum PPFD Requirement:  {} Micromols/m\u00b2/s'.format(crop_PPFDmin)

    final_pick, light_num, upfront_cost, consumption_kwh = Light_Sel(crop_PPFDmin, crop_PPFDmax, photo, plant_num)
    light_choice = 'Recommended light choice: {}'.format(final_pick)
    light_upfront_cost = "Estmated upfront cost:  ${}".format(int(upfront_cost))
    fixtures_est = 'Estimated fixtures:  {}'.format(int(light_num))
    hourly_elec_consumption = 'Total hourly electricity consumption: {} kWh'.format(np.round(consumption_kwh, 2))

    sum_year, win_year, total_annualcost, kwh_year = TOU_ON(photo_start, photo_end, consumption_kwh, photo)
    light_annual_cost = 'Annual lighting electricity cost: ${}'.format(np.round(total_annualcost, 2))

    energy_savings = Ambient_Switching(crop_PPFDmin, trans, consumption_kwh)
    light_energy_savings = 'Energy savings if light are stragically shut off: {} kWh'.format(np.round(energy_savings, 2))
    
    return hourly_elec_consumption, light_annual_cost, light_energy_savings, light_choice, light_upfront_cost, fixtures_est, max_PPFD, min_PPFD, water_consumption, water_cost

# Big Boi
@app.callback(
    [Output('daily-energy-demand', 'figure'),
     Output('monthly-electricity-savings', 'figure'),
     Output('monthly-electricity-peaks', 'figure'),
     Output('monthly-GHG-emission', 'figure')],
    [Input('month-slider', 'value'),
     Input('structure-dropdown', 'value'),
     Input('length-A', 'value'),
     Input('length-B', 'value'),
     Input('length-C', 'value'),
     Input('length-D', 'value'),
     Input('length-E', 'value'),
     Input('crop-dropdown', 'value'),
     Input('photoperiod-start-dropdown', 'value'),
     Input('photoperiod-end-dropdown', 'value'),
     Input('fuel-dropdown', 'value'),
     Input('material-conduction-dropdown', 'value'),
     Input('material-convection-dropdown', 'value'),
     Input('energy-storage-type-dropdown', 'value'),
     Input('optimisation-dropdown', 'value'),
     Input('power-capacity', 'value'),
     Input('energy-capacity', 'value')
     ])
def update_graph(month_slider, structure_type, a, b, c, d, e, crop_type, photo_start, photo_end, fuel_type, material_cond, material_conv, storage_type, optimisation_type, power_capacity, energy_capacity):
    # Wait for users to input values
    if structure_type is None:
        structure_type = 'A-frame'
    if a is None:
        a = 10
    if b is None:
        b = 10
    if c is None:
        c = 10
    if d is None:
        d = 10
    if e is None:
        e = 10
    
    if crop_type is None:
        crop_type = 'Tomato'
    
    if photo_start is None:
        photo_start = 6
    
    if photo_end is None:
        photo_end = 19
    
    if fuel_type is None:
        fuel_type = 'Natural Gas'

    if material_cond is None:
        material_cond = 'Glass'

    if material_conv is None:
        material_conv = 'Clear Polyethylene'

    if (storage_type is None):
        storage_type = 'Lithium Ion'

    if (optimisation_type is None):
        optimisation_type = 'cost'
    
    if (power_capacity is None):
        power_capacity = 100.
    
    if (energy_capacity is None):
        energy_capacity = 300.

    # Calculate surface area
    if structure_type == 'A-frame':
        area = np.round(2*(a*c + b*c + e*b + a*d), 2)
        volume = a*b*c + a*d/2*b
    elif structure_type == 'Quonset':
        area = np.round((a*b)*np.pi/2 + (np.power(a,2))*np.pi/4, 2)
        volume = (np.pi*np.power((a/2), 2)*b)/2

    photo = photo_end - photo_start
    # Repeat Josh's calculation section to get lighting
    plant_num, cost_min, cost_max, wmin_req, wmax_req = water_price(area, crop_type)
    trans = greenhouse_transmissivity(material_cond)
    array, PPFD_max, PPFD_avg = amb_light(trans)
    crop_PPFDmin, crop_PPFDmax = deficiency(array, crop_type, photo)
    final_pick, light_num, upfront_cost, consumption_kwh = Light_Sel(crop_PPFDmin, crop_PPFDmax, photo, plant_num)
    # Need the consumption_kwh to plug into big boi

    # Now call the big boi!
    # Assume a factor
    factor = 0.3
    days, monthly_emissions = final_day_profile(crop_type, area, volume, photo_start, photo_end,
        fuel_type, material_cond, material_conv, consumption_kwh, factor)
    
    # Use days and monthly_emissions to plot!
    # Get data from days to plot!
    monthly_peak_without_storage = np.zeros(12)
    for month in days.keys():
        monthly_peak_without_storage[month-1] = days[month]['Total Electricity (kWh)'].max()

    # Pass the big boi to storage calculations
    dummy_days = dict()
    
    # Append dummy data to dictionary
    for month in days.keys():
        dummy_days[month] = pd.DataFrame(np.asarray(days[month]['Total Electricity (kWh)']), columns=['Total Electricity (kW)'])
        dummy_days[month]['Electricity Prices ($/kWh)'] = days[month]['Electricity Price (c/kWh)']/100
        dummy_days[month] = dummy_days[month].fillna(0)  # Fill nan with zeros
 
    monthly_savings, monthly_peaks, days_storage = storage_calc(storage_type, optimisation_type,
        power_capacity, energy_capacity, dummy_days)
    
    # Get electricity peaks per month for storage option
    monthly_peak_with_storage = np.zeros(12)
    for month in days_storage.keys():
        monthly_peak_with_storage[month-1] = days_storage[month]['Final Electricity (kW)'].max()
    
    # Create numpy arrays to plot the months
    month_array = np.arange(1, 13, 1)
    day_array = np.arange(1, 25, 1)

    # Convert cents to $
    monthly_savings = monthly_savings/100

    # return graphs

    daily_energy_demand_graph = {
        'data': [
            dict(
                x=day_array,
                y=days[int(month_slider)]['Total Electricity (kWh)'],
                mode='lines+markers',
                marker={
                    'size': 15,
                    'opacity': 0.5,
                    'line': {'width': 0.5, 'color': 'white'},
                    'color': 'blue'
            },
                name='without energy storage'),
            
            dict(
                x=day_array,
                y=days_storage[int(month_slider)]['Final Electricity (kW)'],
                mode='lines+markers',
                marker={
                    'size': 15,
                    'opacity': 0.5,
                    'line': {'width': 0.5, 'color': 'white'},
                    'color': 'green'
            },
                name='with energy storage')
        ],
        'layout': dict(
            xaxis={
                'title': "Hour"
            },
            yaxis={
                'title': 'Energy Demand (kWh)'
            },
            title='Daily Energy Demand Profile',
            hovermode='closest'
        )
    }

    monthly_saving_graph = {
        'data': [dict(
            x=month_array,
            y=monthly_savings,
            mode='lines+markers',
            marker={
                'size': 15,
                'opacity': 0.5,
                'line': {'width': 0.5, 'color': 'white'},
                'color': 'green'
            }
        )],
        'layout': dict(
            xaxis={
                'title': "Month"
            },
            yaxis={
                'title': 'Electricity Savings ($)'
            },
            title='Monthly Electricity Cost Savings with Energy Storage',
            hovermode='closest'
        )
    }

    # monthly_peak_without_storage
    # monthly_peaks not used here for storage
    monthly_peak_graph = {
        'data': [
            dict(
                x=month_array,
                y=monthly_peak_with_storage,
                mode='lines+markers',
                marker={
                    'size': 15,
                    'opacity': 0.5,
                    'line': {'width': 0.5, 'color': 'white'},
                    'color': 'green'
                },
                name='with storage'),
            
            dict(
                x=month_array,
                y=monthly_peak_without_storage,
                mode='lines+markers',
                marker={
                    'size': 15,
                    'opacity': 0.5,
                    'line': {'width': 0.5, 'color': 'white'},
                    'color': 'blue'
                },
                name='without storage')

            ],
        'layout': dict(
            xaxis={
                'title': "Month"
            },
            yaxis={
                'title': 'Electricity Peaks (kW)'
            },
            title='Monthly Electricity Peaks',
            hovermode='closest'
        )
    }

    # Monthly GHG Emission graph
    monthly_GHG_graph = {
        'data': [dict(
            x=month_array,
            y=monthly_emissions,
            mode='lines+markers',
            marker={
                'size': 15,
                'opacity': 0.5,
                'line': {'width': 0.5, 'color': 'white'},
                'color': 'green'
            }
        )],
        'layout': dict(
            xaxis={
                'title': "Month"
            },
            yaxis={
                'title': 'GHG Emissions (gCO2e)'
            },
            title='Monthly GHG Emissions',
            hovermode='closest'
        )
    }


    return daily_energy_demand_graph, monthly_saving_graph, monthly_peak_graph, monthly_GHG_graph

if __name__ == "__main__":
    app.run_server(debug=True)
