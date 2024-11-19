# Streamlit live coding script
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
import json
from urllib.request import urlopen
from copy import deepcopy

# Data and geojson cache definition
@st.cache_data
def load_data(path):
    df = pd.read_csv(path)
    return df

@st.cache_data
def load_geojson(path):
    with open(path, 'r') as f:
        geojson = json.load(f)
    return geojson

# Canton Conversion Dictionary Definition and Loading
from canton_dicts import nuts2_regions, nuts3_regions, nuts3_regions_codes

# Data Loading and Base-level Modifications
df_ppCH_raw = load_data(path="./data/raw/renewable_power_plants_CH.csv")
df_ppCH_raw['kan_code'] = df_ppCH_raw['nuts_3_region'].map(nuts3_regions_codes)
df_ppCH_raw['region'] = df_ppCH_raw['nuts_2_region'].map(nuts2_regions)
df_ppCH = deepcopy(df_ppCH_raw)

geojson_CH_raw = load_geojson(path="./data/raw/georef-switzerland-kanton.geojson")
geojson_CH = deepcopy(geojson_CH_raw)

# Title and header(s)
st.title("CH Renewable Energy Production")
st.header("Production Map")

# Selectors
left_column, middle_column, right_column = st.columns([3, 1, 1])
natural_ps = st.checkbox('Show production from natural persons only')

renewables = left_column.selectbox(
    label = "Choose Renewable Type", 
    options = ["All"] + sorted(pd.unique(df_ppCH['energy_source_level_2'])))

map_level = right_column.radio(
    label = 'Select Map Level', 
    options = ['Cantonal', 'Regional'])

# Plotly Map Dataframe Configurator w.r.t. Selectors
df_ppCH_slct = deepcopy(df_ppCH)
nuts_level = 0
nuts_dict = dict()
nuts_text = ""

if "All" not in renewables:
    df_ppCH_slct = df_ppCH_slct[df_ppCH_slct['energy_source_level_2']==renewables]

if natural_ps :
    df_ppCH_slct = df_ppCH_slct[df_ppCH_slct['company']=="Natural person"]
    nuts_text = "  -  NOTE: natural persons only"

if map_level == 'Cantonal' :
    nuts_level = "nuts_3_region"
    nuts_dict = nuts3_regions
    nuts_text = ("Canton: " + df_ppCH_slct[nuts_level].map(nuts_dict) + " (" + df_ppCH_slct['canton'] + ")") + nuts_text
else :
    nuts_level = "nuts_2_region"
    nuts_dict = nuts2_regions
    nuts_text = ("Region: " + df_ppCH_slct[nuts_level].map(nuts_dict)) + nuts_text

df_ppCH_slct[map_level.lower()+'_prod'] = df_ppCH_slct[nuts_level].map(df_ppCH_slct.groupby(by=nuts_level)['production'].sum())

# Generation of Percentage Production for Each Renewable Type by Map Level
# TODO: -Fix bug so that each row is populated with cantonal level percentage or regional level percentage depending on selector
# df_ppCH_cat_nat_perc = (df_ppCH_slct.groupby(by='energy_source_level_2')['production'].sum() / sum(df_ppCH_slct.groupby(by='energy_source_level_2')['production'].sum())) * 100

# for renewable in df_ppCH_cat_nat_perc.index :
#     prefix = renewable.lower()
#     df_ppCH_slct[prefix+'_perc'] = df_ppCH_cat_nat_perc[renewable]

# Plotly Map
# TODO: -Introduce percentage by category for each canton/region with customdata
#       -Mean Tariff
fig_CH = go.Figure(go.Choroplethmapbox(geojson=geojson_CH, 
                                       featureidkey = "properties.kan_code", 
                                       locations = df_ppCH_slct['kan_code'],

                                       z = df_ppCH_slct[map_level.lower()+'_prod'], 
                                       zmin = df_ppCH_slct[map_level.lower()+'_prod'].min(), 
                                       zmax = df_ppCH_slct[map_level.lower()+'_prod'].max(),
                                                 
                                       colorscale="Viridis",
                                       colorbar = {"title" : {"text" : ("Yearly " + map_level + " Production (MWh)"),
                                                              "side" : "right"}},
                                       marker_opacity=0.75, marker_line_width=1.5,
                                       
                                    #    customdata = df_ppCH_slct[['bioenergy_perc','hydro_perc','solar_perc','wind_perc']],

                                       text = nuts_text,
                                       hovertemplate=
                                          "<b>%{text}</b><br>" +
                                          "Yearly " + map_level + " Production (MWh): %{z:,.0f}<br>" +
                                        #   "Production Percentage by Renewable:<br>" +
                                        #   "  -Bioenergy %{customdata[0]:,.0f}%<br>" +
                                        #   "  -Hydro %{customdata[1]:,.0f}%<br>" +
                                        #   "  -Solar %{customdata[2]:,.0f}%<br>" +
                                        #   "  -Wind %{customdata[3]:,.0f}%<br>" +
                                          "<extra></extra>",
                                       ))

fig_CH.update_layout(mapbox_style="carto-positron", 
                     mapbox_zoom=6.25, 
                     mapbox_center = {"lat": 46.787, "lon": 8.047},
                     margin={"r":0,"t":0,"l":0,"b":0})

# Plotly Chart Output
st.plotly_chart(fig_CH)