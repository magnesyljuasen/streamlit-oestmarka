import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster, Draw
from streamlit_folium import st_folium
import geopandas as gpd
from shapely.geometry import Point
import pyproj
import numpy as np
import os
from functools import reduce
import plotly.express as px
import streamlit.components.v1 as components
import plotly.graph_objects as go
from folium.plugins import Fullscreen, minimap
from energyanalysis import EnergyAnalysis
from streamlit_extras.no_default_selectbox import selectbox
from streamlit_extras.switch_page_button import switch_page

title = "Energiplan Østmarka"
icon = "🖥️"
        
st.set_page_config(page_title=title, page_icon=icon, layout="centered",)
with open("src/styles/main.css") as f:
    st.markdown("<style>{}</style>".format(f.read()), unsafe_allow_html=True)
st.markdown("""<style>[data-testid="collapsedControl"] svg {height: 3rem;width: 3rem;}</style>""", unsafe_allow_html=True)

def import_df(filename):
    df = pd.read_excel(filename)
    return df

def embed_map():
    url = "https://asplanviak.maps.arcgis.com/apps/webappviewer/index.html?id=303ea87e725b400fa655cd85353a5b03"
    components.iframe(url, height = 600)

def run_energyanalysis(scenario_file):
    if scenario_file == "Utviklingsscenario 1":
        selected_scenario_file = "input/scenarier.xlsx"
    else:
        selected_scenario_file = "input/scenarier_2.xlsx"
    energy_analysis = EnergyAnalysis(
        building_table = "building_table_østmarka.xlsx",
        energy_area_id = "energiomraadeid",
        building_area_id = "bygningsomraadeid",
        scenario_file_name = selected_scenario_file,
        temperature_array_file_path = "input/utetemperatur.xlsx")
    energy_analysis.main()
            

def main():
    st.title(title)
    st.header("Hva gjør verktøyet?")
    st.write(
        """ 
        Forklaring
        """)
    st.write("")
    st.header("Kjør simulering")
    #self.thermal_reduction = st.slider("Justere termisk energibehov (prosentvis reduksjon)", min_value = 0, value = 0, max_value = 100)
    #self.electric_reduction = st.slider("Justere elektrisk energibehov (prosentvis reduksjon)", min_value = 0, value = 0, max_value = 100)
    #selected_scenario_file = st.selectbox("Simulering", options = ["Utviklingsscenario 1", "Utviklingsscenario 2"])
    selected_scenario_file = "Utviklingsscenario 1"
    if st.button("Kjør energianalyse"):
        #with st.spinner("Beregner..."):
        run_energyanalysis(scenario_file = selected_scenario_file)
    
    #if st.button("Gå til kartvisning"):
    #    switch_page("Kartvisning")


main()

