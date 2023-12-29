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

def main():
    st.title(title)
    st.header("Hva gjør verktøyet?")
    st.write(
        """ 
        Forklaring
        """)
    st.write("")
    
    if st.button("Gå til kartvisning"):
        switch_page("Kartvisning")


main()

