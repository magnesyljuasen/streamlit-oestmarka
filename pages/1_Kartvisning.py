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
import plotly.graph_objects as go
import plotly.figure_factory as ff
from plotly.subplots import make_subplots
import statsmodels.api as sm
from folium.plugins import Fullscreen, minimap
from energyanalysis import EnergyAnalysis
from streamlit_extras.switch_page_button import switch_page
import time
from streamlit_extras.no_default_selectbox import selectbox

@st.cache_resource(show_spinner=False)
def import_df(filename):
    df = pd.read_csv(filename, low_memory=False)
    return df

@st.cache_resource(show_spinner=False)
def import_temperature_array(filename):
    df = pd.read_excel(filename)
    return df

class Dashboard:
    def __init__(self):
        self.title = "Energianalyse"
        self.icon = "🖥️"
        self.color_sequence = [
            "#c76900", #bergvarme
            "#48a23f", #bergvarmesolfjernvarme
            "#1d3c34", #fjernvarme
            "#b7dc8f", #fremtidssituasjon
            "#2F528F", #luftluft
            "#3Bf81C", #merlokalproduksjon
            "#AfB9AB", #nåsituasjon
            "#254275", #oppgradert
            "#767171", #referansesituasjon
            "#ffc358", #solceller
        ]
        self.set_streamlit_settings()

    def __hour_to_month(self, hourly_array):
        monthly_array = []
        summed = 0
        for i in range(0, len(hourly_array)):
            verdi = hourly_array[i]
            if np.isnan(verdi):
                verdi = 0
            summed = verdi + summed
            if (
                i == 744
                or i == 1416
                or i == 2160
                or i == 2880
                or i == 3624
                or i == 4344
                or i == 5088
                or i == 5832
                or i == 6552
                or i == 7296
                or i == 8016
                or i == 8759
            ):
                monthly_array.append(int(summed))
                summed = 0
        return monthly_array

    def __hour_to_month_max(self, hourly_array):
        monthly_array = []
        maksverdi = 0
        for i in range(0, len(hourly_array)):
            verdi = hourly_array[i]
            if not np.isnan(verdi):
                if maksverdi < verdi:
                    maksverdi = verdi
            if (
                i == 744
                or i == 1416
                or i == 2160
                or i == 2880
                or i == 3624
                or i == 4344
                or i == 5088
                or i == 5832
                or i == 6552
                or i == 7296
                or i == 8016
                or i == 8759
            ):
                monthly_array.append(int(maksverdi))
                maksverdi = 0
        return monthly_array
    
    def set_streamlit_settings(self):
        st.set_page_config(page_title=self.title, page_icon=self.icon, layout="wide",)
        with open("src/styles/main.css") as f:
            st.markdown("<style>{}</style>".format(f.read()), unsafe_allow_html=True)
        st.markdown("""<style>[data-testid="collapsedControl"] svg {height: 3rem;width: 3rem;}</style>""", unsafe_allow_html=True)
        
    def adjust_input_parameters_middle(self):
        with st.sidebar:
            st.header("Kartvisning")
            self.map_scenario_name = self.scenario_picker(key = "kartvisning", default_label = "Velg scenario")
            selected_buildings_option = st.selectbox("Velg bygningsmasse", options = ["Eksisterende bygningsmasse", "Planforslag (inkl. dagens bygg som skal bevares)", "Planforslag (ekskl. helsebygg)", "Planforslag og områdene rundt Østmarka"])
            selected_buildings_option_map = {
                "Eksisterende bygningsmasse" : "E",
                "Planforslag (inkl. dagens bygg som skal bevares)" : "P1",
                "Planforslag (ekskl. helsebygg)" : "P2",
                "Planforslag og områdene rundt Østmarka" : "P3"
            }
            self.selected_buildings_option = selected_buildings_option_map[selected_buildings_option]
            st.markdown("---")
            st.header("Beregninger")
            self.elprice = st.number_input("Velg strømpris (kr/kWh)", min_value = 0.8, step = 0.2, value = 1.0, max_value = 10.0)
            self.co2_kWh = st.number_input("Velg utslippsfaktor", min_value = 1, step = 5, value = 17, max_value = 200) / 1000000
    
    def adjust_input_parameters_before(self):
        pass
#        def __run_energyanalysis(scenario_file):
#            if scenario_file == "Utviklingsscenario 1":
#                selected_scenario_file = "input/scenarier.xlsx"
#            else:
#                selected_scenario_file = "input/scenarier_2.xlsx"
#            energy_analysis = EnergyAnalysis(
#                building_table = "building_table_østmarka.xlsx",
#                energy_area_id = "energiomraadeid",
#                building_area_id = "bygningsomraadeid",
#                scenario_file_name = selected_scenario_file,
#                temperature_array_file_path = "input/utetemperatur.xlsx")
#            energy_analysis.main()
            
#            with st.expander("Simulering"):
                #self.thermal_reduction = st.slider("Justere termisk energibehov (prosentvis reduksjon)", min_value = 0, value = 0, max_value = 100)
                #self.electric_reduction = st.slider("Justere elektrisk energibehov (prosentvis reduksjon)", min_value = 0, value = 0, max_value = 100)
                #selected_scenario_file = st.selectbox("Simulering", options = ["Utviklingsscenario 1", "Utviklingsscenario 2"])
#                selected_scenario_file = "Utviklingsscenario 1"
#                if st.button("Kjør energianalyse"):
                    #with st.spinner("Beregner..."):
 #                   __run_energyanalysis(scenario_file = selected_scenario_file)
            
    def import_dataframes(self):
        def __read_csv(folder_path = "output"):
            csv_file_list = []
            scenario_name_list = []
            filename_list = []
            for filename in os.listdir(folder_path):
                if filename.endswith("unfiltered.csv"):
                    filename_list.append(filename)
                    scenario_name_list.append(filename.split(sep = "_")[0])
                    csv_file_list.append(filename)
            return csv_file_list, scenario_name_list
        
        #--
        self.temperature_array = import_temperature_array(filename = "input/utetemperatur.xlsx").to_numpy().ravel()
        #--
        csv_list, scenario_name_list = __read_csv(folder_path = "output")
        df_list = []
        df_hourly_list = []
        for i in range(0, len(csv_list)):
            filename = str(csv_list[i])
            filename_hourly_data = f"output/{scenario_name_list[i]}_timedata.csv"
            df_hourly_data = import_df(filename = rf"{filename_hourly_data}")
            df_hourly_data['scenario_navn'] = f'{scenario_name_list[i]}'
            df_hourly_list.append(df_hourly_data)
            df = import_df(filename = rf"output/{filename}")
            df['scenario_navn'] = f'{scenario_name_list[i]}'
            df_list.append(df)
        self.df = pd.concat(df_list, ignore_index=True)
        self.df_hourly_data = pd.concat(df_hourly_list, ignore_index=True)
        self.scenario_name_list = scenario_name_list

    def get_bounding_box(self, polygon):
        # Extracting coordinates of the polygon vertices
        vertices = polygon['geometry']['coordinates'][0]

        # Calculate bounding box coordinates
        lats = [point[1] for point in vertices]
        longs = [point[0] for point in vertices]

        min_lat, max_lat = min(lats), max(lats)
        min_long, max_long = min(longs), max(longs)

        return {
            'min_lat': min_lat,
            'max_lat': max_lat,
            'min_long': min_long,
            'max_long': max_long
        }
    
    def __map_styling_function(self, row):
        popup_text = ""
        tooltip_text = ""
        if row["grunnvarme"]:
            icon_color = "green"
            tooltip_text = "Grunnvarme"
        elif row["solceller"]:
            icon_color = "orange"
            tooltip_text = "Solceller"
        elif row["fjernvarme"]:
            icon_color = "white"
            tooltip_text = "Fjernvarme"
        else:
            icon_color = "black"
        icon = folium.Icon(color = 'black', icon_color = icon_color)
        return popup_text, tooltip_text, icon
    
    # østmarka 63.4525759196283, 10.447553721163194
    # stjørdal 63.4728849, 10.8886829
    # kringsjå 59.9640811 10.7295653
    def map(self, df, scenario_name):
        df = df.loc[(df['scenario_navn'] == scenario_name) & (df['bygningsomraadeid'] == self.selected_buildings_option)]
        map = folium.Map(
            location = [63.4525759196283, 10.447553721163194], 
            zoom_start = 15, 
            scrollWheelZoom = True, 
            tiles = 'CartoDB positron', 
            max_zoom = 22, 
            control_scale = True,)
        Fullscreen().add_to(map)
        draw_rectangle = folium.plugins.Draw(
            position='topright',
            draw_options={
                'polyline': False,
                #'rectangle': True,
                'circle': False,
                'marker': False,
                'circlemarker': False,
                'polygon' : False
                }
            )
        map.add_child(draw_rectangle)
        #--
        url = "https://geo.ngu.no/mapserver/LosmasserWMS2?request=GetCapabilities&service=WMS"
        layer = "Losmasse_flate"
        layer_name = "Løsmasser"
        folium.WmsTileLayer(
             url = url,
             layers = layer,
             transparent = True, 
             control = True,
             fmt="image/png",
             name = layer_name,
             overlay = True,
             show = True,
             opacity = 0.25
             ).add_to(map)
        #--
        url = "https://geo.ngu.no/mapserver/GranadaWMS5?request=GetCapabilities&service=WMS"
        layer = "Energibronn"
        layer_name = "Energibrønner"
        folium.WmsTileLayer(
             url = url,
             layers = layer,
             transparent = True, 
             control = True,
             fmt="image/png",
             name = layer_name,
             overlay = True,
             show = True,
             opacity = 0.5
             ).add_to(map)
        #--
        url = "https://geo.ngu.no/geoserver/nadag/ows?request=GetCapabilities&service=WMS"
        layer = "GBU_metode"
        layer_name = "NADAG"
        folium.WmsTileLayer(
             url = url,
             layers = layer,
             transparent = True, 
             control = True,
             fmt="image/png",
             name = layer_name,
             overlay = True,
             show = True,
             opacity = 0.5
             ).add_to(map)
        folium.LayerControl(position = "bottomleft").add_to(map)
#    bounding_box = self.get_bounding_box(drawn_polygon.data)
        marker_cluster = MarkerCluster(
            name = 'Cluster',
            control = False,  
            overlay = True,  
            options = {
                'disableClusteringAtZoom': 13
            }).add_to(map)
        for index, row in df.iterrows():
            thermal_demand = int(np.sum(row['_termisk_energibehov_sum']))
            electric_demand = int(np.sum(row['_elektrisk_energibehov_sum']))
            total_demand = thermal_demand + electric_demand
            if total_demand <= 100000:
                icon_color = '#48a23f'
            elif total_demand > 100000 and total_demand < 500000:
                icon_color = '#b7dc8f'
            elif total_demand > 500000 and total_demand < 1000000:
                icon_color = '#1d3c34'
            else:
                icon_color = 'black'
            popup_text = f"Termisk: {int(np.sum(row['_termisk_energibehov_sum'])):,} kWh/år<br>Elspesifikt: {int(np.sum(row['_elektrisk_energibehov_sum'])):,} kWh/år<br>".replace(",", "")
            tooltip_text = f"Adresse: {row['har_adresse']}"
            popup_text, tooltip_text, icon = self.__map_styling_function(row) 
            folium.Marker(
                [row['y'], row['x']], 
                popup = popup_text, 
                tooltip = tooltip_text, 
                icon = icon).add_to(marker_cluster)
        self.st_map = st_folium(
            map,
            use_container_width=True,
            height=400,
            returned_objects=["last_active_drawing"]
            )

        #st.info("Zoom inn og ut på kartet med scrollehjulet. Diagrammene på høyre side følger kartutsnittet.", icon = "ℹ️")
    
    def dataframe_to_geodataframe(self, df):
        geometry = [Point(lon, lat) for lon, lat in zip(df['x'], df['y'])]
        gdf = gpd.GeoDataFrame(df, geometry=geometry, crs = "25832")
        gdf = gdf.loc[gdf['bygningsomraadeid'] == self.selected_buildings_option]
        self.gdf = gdf
    
    def filter_geodataframe(self):
        original_crs = pyproj.CRS("EPSG:4326")
        target_crs = pyproj.CRS("EPSG:4326")
        #bounding_box = self.st_map["bounds"]
        #transformer = pyproj.Transformer.from_crs(original_crs, target_crs, always_xy=True)
        #min_lon, min_lat = transformer.transform(bounding_box["_southWest"]["lng"], bounding_box["_southWest"]["lat"])
        #max_lon, max_lat = transformer.transform(bounding_box["_northEast"]["lng"], bounding_box["_northEast"]["lat"])
        #--
        if self.st_map["last_active_drawing"] == None:
            st.info("Tegn polygon...")
            self.progress_bar.progress(100)
            st.stop()
        else:
            bounding_box = self.st_map["last_active_drawing"]["geometry"]["coordinates"][0]
            sw, nw = bounding_box[0], bounding_box[2]
            sw_long, sw_lat = sw[0], sw[1]
            nw_long, nw_lat = nw[0], nw[1]
            transformer = pyproj.Transformer.from_crs(original_crs, target_crs, always_xy=True)
            min_lon, min_lat = transformer.transform(sw_long, sw_lat)
            max_lon, max_lat = transformer.transform(nw_long, nw_lat)
            filtered_gdf = self.gdf.cx[min_lon:max_lon, min_lat:max_lat]
            
            self.filtered_gdf = filtered_gdf
            self.filtered_df = pd.DataFrame(filtered_gdf.drop(columns='geometry'))
        
    def get_unique_series_ids(self):
        self.unique_series_ids = self.df_hourly_data["ID"].unique().tolist()
        self.unique_objectids = list(map(str, self.filtered_gdf["objectid"].unique().tolist()))
        self.unique_objectids.append("scenario_navn")
        self.unique_objectids.append("ID")

    def filter_hourly_data(self, scenario_name):
        df_results = pd.DataFrame()
        #--
        df = self.df_hourly_data[self.unique_objectids]
        df = df[df["scenario_navn"] == scenario_name]
        for id in self.unique_series_ids:
            df_id = df[df["ID"] == id]
            df_id = df_id.drop(columns=["scenario_navn", "ID"])
            df_id = df_id.reset_index(drop = True)
            df_results[id] = df_id.sum(axis = 1)
        return df_results
                
            
    def __cleanup_df(self, df):
        df = df.reset_index(drop = True)
        df = df.drop(columns = "Unnamed: 0")
        df.columns = df.columns.str.replace('_', '')
        df.columns = df.columns.str.replace('energibehov', '')
        return df
        
    def __rounding_to_int(self, number):
        number = int(round(number,0))
        return number
    
    def __rounding_to_int_fixed(self, number, rounding):
        number = int(round(number, rounding))
        return number
    
    def __show_map_results(self, key, default_option):
        scenario_name = "Referansesituasjon"
        df_buildings = self.filtered_df.loc[self.filtered_df['scenario_navn'] == scenario_name].reset_index()
        #--
        df_results = self.filter_hourly_data(scenario_name)
        thermal_array_delivered = df_results["_termisk_energibehov"]
        electric_array_delivered = df_results["_elektrisk_energibehov"]
        spaceheating_array = df_results["_romoppvarming_energibehov"]
        dhw_array  = df_results["_tappevann_energibehov"]
        electric_array = df_results["_elspesifikt_energibehov"]
        grid_array = df_results["_nettutveksling_energi_liste"]
        #--
        spaceheating_color = "#ff9966"
        dhw_color = "#b39200"
        thermal_color_delivered = "red"
        electricty_color_delivered = "blue"
        electricty_color = "#3399ff"
        grid_color = "#7f7f7f"
        stand_out_color = "#48a23f"
        base_color = "#1d3c34"
        #--
        tab1, tab2, tab3 = st.tabs(["Levert energi", "Behov", "Bygningsmassen"])
        with tab1:
            #with st.expander("Dagens energi- og effektbehov"):
            with st.container():
                st.markdown(f"<span style='color:black'><small>**{self.__rounding_to_int_fixed(np.sum(electric_array_delivered + thermal_array_delivered), -3):,}** kWh/år | **{self.__rounding_to_int_fixed(np.max(electric_array_delivered + thermal_array_delivered), -1):,}** kW</span>".replace(",", " "), unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"<span style='color:{thermal_color_delivered}'><small>Termisk:<br>**{self.__rounding_to_int_fixed(np.sum(thermal_array_delivered), -3):,}** kWh/år<br>**{self.__rounding_to_int_fixed(np.max(thermal_array_delivered), -1):,}** kW</span>".replace(",", " "), unsafe_allow_html=True)
            with c2:
                st.markdown(f"<span style='color:{electricty_color_delivered}'><small>Elektrisk<br>**{self.__rounding_to_int_fixed(np.sum(electric_array_delivered), -3):,}** kWh/år<br>**{self.__rounding_to_int_fixed(np.max(electric_array_delivered), -1):,}** kW</span>".replace(",", " "), unsafe_allow_html=True)
            
            df_demands = pd.DataFrame(
                {"Måneder" : ["jan", "feb", "mar", "apr", "mai", "jun", "jul", "aug", "sep", "okt", "nov", "des"],
                "Termisk (kWh/år)" : self.__hour_to_month(thermal_array_delivered),
                "Elektrisk  (kWh/år)" : self.__hour_to_month(electric_array),
                "Termisk (kW)" : self.__hour_to_month_max(thermal_array_delivered),
                "Elektrisk (kW)" : self.__hour_to_month_max(electric_array),
                #"Maksimal effekt (kW)" : self.__hour_to_month_max(electric_array + spaceheating_array + dhw_array)
                #"Nett" : grid_array,
                })
            df_demands['Total'] = df_demands.iloc[:, 1:].sum(axis=1)
            fig = go.Figure()
            kWh_colors = [electricty_color_delivered, thermal_color_delivered]
            kWh_labels = ['Elektrisk  (kWh/år)', 'Termisk (kWh/år)']
            for col in kWh_labels:
                df_demands[col + '_percentage'] = (df_demands[col] / df_demands['Total']) * 100
            for i, col in enumerate(kWh_labels):
                bar = go.Bar(x=df_demands['Måneder'], y=df_demands[col], name=col, yaxis='y', marker=dict(color=kWh_colors[i]))
                #text_labels = [f'{val:.0f}%' for val in df_demands[col + '_percentage']]
                #bar.update(text=text_labels, textposition='auto')
                fig.add_trace(bar)
            kW_colors = [electricty_color_delivered, thermal_color_delivered]
            for i, col in enumerate(['Elektrisk (kW)', 'Termisk (kW)']):
                fig.add_trace(go.Scatter(x=df_demands['Måneder'], y=df_demands[col], name=col, yaxis='y2', mode='markers', marker=dict(color=kW_colors[i], symbol="diamond", line=dict(width=1, color = "black"))))
            fig.update_layout(
                showlegend=False,
                margin=dict(b=0, t=0),
                yaxis=dict(title='Energi (kWh/år)', side='left', showgrid=True, tickformat=",.0f"),
                yaxis2=dict(title='Effekt (kW)', side='right', overlaying='y', showgrid=True),
                barmode='relative',
                height = 200
                #fig.update_yaxes()
            )
            st.plotly_chart(fig, use_container_width=True, config = {'displayModeBar': True, 'staticPlot': True})
            #--
        with tab2:
            #with st.expander("Energi- og effektbehov"):
            with st.container():
                st.markdown(f"<span style='color:black'><small>**{self.__rounding_to_int_fixed(np.sum(spaceheating_array + dhw_array + electric_array), -3):,}** kWh/år | **{self.__rounding_to_int_fixed(np.max(spaceheating_array + dhw_array + electric_array), -1):,}** kW</span>".replace(",", " "), unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f"<span style='color:{spaceheating_color}'><small>Oppvarming<br>**{self.__rounding_to_int_fixed(np.sum(spaceheating_array), -3):,}** kWh/år<br>**{self.__rounding_to_int_fixed(np.max(spaceheating_array), -1):,}** kW</span>".replace(",", " "), unsafe_allow_html=True)
            with c2:
                st.markdown(f"<span style='color:{dhw_color}'><small>Tappevann<br>**{self.__rounding_to_int_fixed(np.sum(dhw_array), -3):,}** kWh/år<br>**{self.__rounding_to_int_fixed(np.max(dhw_array), -1):,}** kW</span>".replace(",", " "), unsafe_allow_html=True)
            with c3:
                st.markdown(f"<span style='color:{electricty_color}'><small>Elspesifikt<br>**{self.__rounding_to_int_fixed(np.sum(electric_array), -3):,}** kWh/år<br>**{self.__rounding_to_int_fixed(np.max(electric_array), -1):,}** kW</span>".replace(",", " "), unsafe_allow_html=True)
            df_demands = pd.DataFrame(
                {"Måneder" : ["jan", "feb", "mar", "apr", "mai", "jun", "jul", "aug", "sep", "okt", "nov", "des"],
                "Romoppvarmingsbehov (kWh/år)" : self.__hour_to_month(spaceheating_array),
                "Tappevann  (kWh/år)" : self.__hour_to_month(dhw_array),
                "Elspesifikt  (kWh/år)" : self.__hour_to_month(electric_array),
                "Romoppvarming (kW)" : self.__hour_to_month_max(spaceheating_array),
                "Tappevann (kW)" : self.__hour_to_month_max(dhw_array),
                "Elspesifikt (kW)" : self.__hour_to_month_max(electric_array),
                #"Maksimal effekt (kW)" : self.__hour_to_month_max(electric_array + spaceheating_array + dhw_array)
                #"Nett" : grid_array,
                })
            df_demands['Total'] = df_demands.iloc[:, 1:].sum(axis=1)
            fig = go.Figure()
            kWh_colors = [dhw_color, electricty_color, spaceheating_color]
            kWh_labels = ['Tappevann  (kWh/år)', 'Elspesifikt  (kWh/år)', 'Romoppvarmingsbehov (kWh/år)']
            for col in kWh_labels:
                df_demands[col + '_percentage'] = (df_demands[col] / df_demands['Total']) * 100
            for i, col in enumerate(kWh_labels):
                bar = go.Bar(x=df_demands['Måneder'], y=df_demands[col], name=col, yaxis='y', marker=dict(color=kWh_colors[i]))
                #text_labels = [f'{val:.0f}%' for val in df_demands[col + '_percentage']]
                #bar.update(text=text_labels, textposition='auto')
                fig.add_trace(bar)
            kW_colors = [dhw_color, electricty_color, spaceheating_color]
            for i, col in enumerate(['Tappevann (kW)', 'Elspesifikt (kW)', 'Romoppvarming (kW)']):
                fig.add_trace(go.Scatter(x=df_demands['Måneder'], y=df_demands[col], name=col, yaxis='y2', mode='markers', marker=dict(color=kW_colors[i], symbol="diamond", line=dict(width=1, color = "black"))))
            fig.update_layout(
                #title='Energi- og effektbehov',
                #legend=dict(orientation="h", yanchor="top", y=1.0, x=0.5),
                showlegend=False,
                margin=dict(b=0, t=0),
                yaxis=dict(title='Energi (kWh/år)', side='left', showgrid=True, tickformat=",.0f"),
                yaxis2=dict(title='Effekt (kW)', side='right', overlaying='y', showgrid=True),
                barmode='relative',
                height = 200
                #fig.update_yaxes()
            )
            st.plotly_chart(fig, use_container_width=True, config = {'displayModeBar': True, 'staticPlot': True})
            #--
               
        #--
        with tab3:
            #with st.expander("Om bygningsmassen"):
            fig = px.pie(
                df_buildings, 
                values='bruksareal_totalt', 
                names='har_adresse',
                color_discrete_sequence=px.colors.qualitative.Set3,
                labels={'Category': 'Categories', 'Values': 'Percentage'}, 
                hole=0.4,
            )
            fig.update_traces(textposition='inside', textinfo='label+percent')
            fig.update_layout(
                showlegend=False,
                margin=dict(b=0, t=0),
                height = 350
            )
            st.plotly_chart(fig, use_container_width=True, config = {'displayModeBar': False, 'staticPlot': True})
            #--
        #--            
        
    def __show_scenario_results(self, key, default_option):
        scenario_name = self.scenario_picker(key, default_option = default_option)
        selected_visual = self.selected_visual
        df_buildings = self.filtered_df.loc[self.filtered_df['scenario_navn'] == scenario_name].reset_index()
        #--
        
        df_results = self.filter_hourly_data(scenario_name)
        thermal_array_delivered = df_results["_termisk_energibehov"]
        electric_array_delivered = df_results["_elektrisk_energibehov"]
        spaceheating_array = df_results["_romoppvarming_energibehov"]
        dhw_array  = df_results["_tappevann_energibehov"]
        electric_array = df_results["_elspesifikt_energibehov"]
        grid_array = df_results["_nettutveksling_energi_liste"]
        
        #--
        spaceheating_color = "#ff9966"
        dhw_color = "#b39200"
        thermal_color_delivered = "red"
        electricty_color_delivered = "blue"
        electricty_color = "#3399ff"
        grid_color = "#7f7f7f"
        stand_out_color = "#48a23f"
        base_color = "#1d3c34"
        #--
        if selected_visual == "Om scenarioet":
            #with st.expander("Om scenarioet"):
            df_scenarios = df_buildings[["har_adresse", "grunnvarme", "fjernvarme", "solceller", "luft_luft_varmepumpe", "oppgraderes"]]
            df_scenarios = df_scenarios.rename(columns={
                'har_adresse': 'Adresse',
                'grunnvarme': 'Grunnvarme',
                'fjernvarme': 'Fjernvarme',
                'luft_luft_varmepumpe': 'Luft luft varmepumpe',
                'solceller': 'Solceller',
                'oppgraderes': 'Oppgradert bygningsmasse'
            })
            df_scenarios['Ingen tiltak'] = ~df_scenarios.iloc[:, 1:].any(axis=1)
            counts = df_scenarios.iloc[:, 1:].sum()
            plot_data = {
                'Categories': counts.index,
                'Counts': counts.values
            }
            plot_df = pd.DataFrame(plot_data)
            fig = px.pie(
                plot_df, 
                values='Counts', 
                names='Categories',
                color_discrete_sequence=px.colors.qualitative.Set3,
                labels={'Category': 'Categories', 'Values': 'Percentage'}, 
                hole=0.4,
            )
            fig.update_traces(textposition='inside', textinfo='label+value')
            #fig = px.bar(plot_df, x='Categories', y='Counts',
            #            labels={'Categories': '', 'Counts': 'Antall bygg med tiltak'},
            #            color='Categories')
            fig.update_layout(
                showlegend=False,
                margin=dict(b=0, t=0),
                height = 200
            )
            st.plotly_chart(fig, use_container_width=True, config = {'displayModeBar': False, 'staticPlot': True})
            #--
        if selected_visual == "Måned":
            grid_array_sorted = grid_array
            grid_before_sorted = thermal_array_delivered + electric_array_delivered
            before_color = "#1d3c34"
            after_color = "#48a23f"
            #with st.expander("Dagens energi- og effektbehov"):
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"<span style='color:{before_color}'><small>Før:<br>**{self.__rounding_to_int_fixed(np.sum(thermal_array_delivered + electric_array_delivered), -3):,}** kWh/år<br>**{self.__rounding_to_int_fixed(np.max(thermal_array_delivered), -1):,}** kW</span>".replace(",", " "), unsafe_allow_html=True)
            with c2:
                st.markdown(f"<span style='color:{after_color}'><small>Etter<br>**{self.__rounding_to_int_fixed(np.sum(grid_array), -3):,}** kWh/år<br>**{self.__rounding_to_int_fixed(np.max(electric_array_delivered), -1):,}** kW</span>".replace(",", " "), unsafe_allow_html=True)
            
            df_demands = pd.DataFrame(
                {"Måneder" : ["jan", "feb", "mar", "apr", "mai", "jun", "jul", "aug", "sep", "okt", "nov", "des"],
                "Etter (kWh/år)" : self.__hour_to_month(grid_array),
                "Før (kWh/år)" : self.__hour_to_month(thermal_array_delivered + electric_array_delivered),
                "Etter (kW)" : self.__hour_to_month_max(grid_array),
                "Før (kW)" : self.__hour_to_month_max(thermal_array_delivered + electric_array_delivered),
                })
            df_demands['Total'] = df_demands.iloc[:, 1:].sum(axis=1)
            fig = go.Figure()
            kWh_colors = [before_color, after_color]
            kWh_labels = ['Før (kWh/år)', 'Etter (kWh/år)']
            for col in kWh_labels:
                df_demands[col + '_percentage'] = (df_demands[col] / df_demands['Total']) * 100
            for i, col in enumerate(kWh_labels):
                bar = go.Bar(x=df_demands['Måneder'], y=df_demands[col], name=col, yaxis='y', marker=dict(color=kWh_colors[i]))
                #text_labels = [f'{val:.0f}%' for val in df_demands[col + '_percentage']]
                #bar.update(text=text_labels, textposition='auto')
                fig.add_trace(bar)
            kW_colors = [before_color, after_color]
            for i, col in enumerate(['Før (kW)', 'Etter (kW)']):
                fig.add_trace(go.Scatter(x=df_demands['Måneder'], y=df_demands[col], name=col, yaxis='y2', mode='markers', marker=dict(color=kW_colors[i], symbol="diamond", line=dict(width=1, color = "black"))))
            fig.update_layout(
                showlegend=False,
                margin=dict(b=0, t=0),
                yaxis=dict(title='Energi (kWh/år)', side='left', showgrid=True, tickformat=",.0f"),
                yaxis2=dict(title='Effekt (kW)', side='right', overlaying='y', showgrid=True),
                #barmode='relative',
                height = 200
                #fig.update_yaxes()
            )
            st.plotly_chart(fig, use_container_width=True, config = {'displayModeBar': True, 'staticPlot': True})
        #--
        if selected_visual == "Time for time":
            #with st.expander("Time for time"):
            varighetskurve = st.toggle("Varighetskurve", value = False, key = f"{key}_varighetskurve")
            if varighetskurve == True:
                grid_array_sorted = np.sort(grid_array)[::-1]
                grid_before_sorted = np.sort(thermal_array_delivered + electric_array_delivered)[::-1]
            else:
                grid_array_sorted = grid_array
                grid_before_sorted = thermal_array_delivered + electric_array_delivered
            #spaceheating_array_sorted = np.sort(spaceheating_array)[::-1]
            #dhw_array_sorted = np.sort(dhw_array)[::-1]
            #electric_array_sorted = np.sort(electric_array)[::-1]
            
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"<span style='color:{grid_color}'><small>Utgangspunkt<br>**{self.__rounding_to_int_fixed(np.sum(grid_before_sorted), -3):,}** kWh/år<br>**{self.__rounding_to_int_fixed(np.max(grid_before_sorted), -1):,}** kW</span>".replace(",", " "), unsafe_allow_html=True)
            with c2:
                st.markdown(f"<span style='color:{stand_out_color}'><small>{scenario_name}<br>**{self.__rounding_to_int_fixed(np.sum(grid_array_sorted), -3):,}** kWh/år (-{100 - self.__rounding_to_int((np.sum(grid_array_sorted)/np.sum(grid_before_sorted))*100)}%)<br>**{self.__rounding_to_int_fixed(np.max(grid_array_sorted), -1):,}** kW (-{100 - self.__rounding_to_int((np.max(grid_array_sorted)/np.max(grid_before_sorted))*100)}%)</span>".replace(",", " "), unsafe_allow_html=True)
            
            #trace1 = go.Scatter(x=np.arange(len(spaceheating_array_sorted)), y=spaceheating_array_sorted, mode='lines', name='Oppvarming', visible='legendonly', line=dict(color=spaceheating_color))
            #trace2 = go.Scatter(x=np.arange(len(dhw_array_sorted)), y=dhw_array_sorted, mode='lines', name='Tappevann', visible='legendonly', line=dict(color=dhw_color))
            #trace3 = go.Scatter(x=np.arange(len(electric_array_sorted)), y=electric_array_sorted, mode='lines', name='Elspesifikt', visible='legendonly', line=dict(color=electricty_color))
            if varighetskurve == True:
                trace4 = go.Scatter(x=np.arange(len(grid_array_sorted)), y=grid_array_sorted, mode='lines', name=f'{scenario_name}', line=dict(color=stand_out_color))
                trace5 = go.Scatter(x=np.arange(len(grid_before_sorted)), y=grid_before_sorted, mode='lines', name=f'Oppvarming + Tappevann + Elspesifikt', line=dict(color=grid_color, dash = "dash"))
                layout = go.Layout(
                xaxis=dict(title='Varighet (timer)'),
                yaxis=dict(title='Effekt (kW)'),
                showlegend=False,
                margin=dict(b=0, t=0),
                height = 200
                #legend=dict(x=0.5, y=1.0, bgcolor='rgba(255, 255, 255, 0.5)', bordercolor='rgba(0, 0, 0, 0.5)', borderwidth=1)
                )
            else:
                trace4 = go.Scatter(x=np.arange(len(grid_array_sorted)), y=grid_array_sorted, mode='lines', name=f'{scenario_name}', line=dict(color=stand_out_color, width = 0.5))
                trace5 = go.Scatter(x=np.arange(len(grid_before_sorted)), y=grid_before_sorted, mode='lines', name=f'Oppvarming + Tappevann + Elspesifikt', line=dict(color=grid_color, width = 0.5))
                layout = go.Layout(
                xaxis=dict(title='Timer i ett år'),
                yaxis=dict(title='Effekt (kW)'),
                showlegend=False,
                margin=dict(b=0, t=0),
                height = 200
                #legend=dict(x=0.5, y=1.0, bgcolor='rgba(255, 255, 255, 0.5)', bordercolor='rgba(0, 0, 0, 0.5)', borderwidth=1)
                )
            fig = go.Figure(data=[
                #trace1, trace2, trace3, 
                trace4, trace5], layout=layout)
            st.plotly_chart(fig, use_container_width=True, config = {'displayModeBar': False, 'staticPlot': True})
        #--
        if selected_visual == "ET-kurve":
            #with st.expander("ET-kurve"):
            df = pd.DataFrame(
                {"Utetemperatur" : self.temperature_array,
                "Effekt" : grid_array
                })
            X = sm.add_constant(df['Utetemperatur'])
            model = sm.OLS(df['Effekt'], X).fit()
            st.markdown(f"$$ P = {model.params[0]:.1f} {model.params[1]:.1f} \cdot T $$".replace(".", ","), unsafe_allow_html=True)
            fig = px.scatter(df, x="Utetemperatur", y="Effekt", trendline="ols")
            fig.update_traces(line=dict(color=base_color, dash = 'dash'))
            fig.update_traces(marker=dict(color=stand_out_color))
            fig.update_layout(
                showlegend=False,
                margin=dict(b=0, t=0),
                yaxis=dict(title='Effekt (kW)', side='left', showgrid=True, tickformat=",.0f"),
                xaxis=dict(title='Utetemperatur (°C)', showgrid=True),
                height = 200
            )
            st.plotly_chart(fig, use_container_width=True, config = {'displayModeBar': False, 'staticPlot': True})
        if selected_visual == "Økonomi":
            #with st.expander("Økonomi"):
            reference_array = thermal_array_delivered + electric_array
            scenario_array = grid_array
            #--
            reference_array = reference_array * self.elprice
            scenario_array = scenario_array * self.elprice
            #--
            st.write("**Strømkostnader**")
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"<span style='color:{grid_color}'><small>Utgangspunkt<br>**{self.__rounding_to_int_fixed(np.sum(reference_array), -3):,}** kr/år".replace(",", " "), unsafe_allow_html=True)
            with c2:
                st.markdown(f"<span style='color:{stand_out_color}'><small>{scenario_name}<br>**{self.__rounding_to_int_fixed(np.sum(scenario_array), -3):,}** kr (-{100 - self.__rounding_to_int((np.sum(scenario_array)/np.sum(reference_array))*100)}%)".replace(",", " "), unsafe_allow_html=True)
            st.write("**Investeringskostnader**")
            well_meter = np.sum(df_buildings["grunnvarme_meter"].to_numpy())
            number_of_wells = int(well_meter/300)
            st.write(f"• Ca. {number_of_wells} brønner á 300 m brønndybde.")
            gshp_investment_cost = int(well_meter * 600)
            st.write(f"• Investeringskostnad brønner: {gshp_investment_cost:,} kr".replace(",", " "))
            solar_panels_produced = int(np.sum(df_buildings["_solcelleproduksjon_sum"].to_numpy()))
            st.write(f"• Investeringskostnad solceller: {solar_panels_produced:,} kr".replace(",", " "))
            solar_panels_cost = int(solar_panels_produced * 14)
            st.write(f"• Investeringskostnad solceller: {solar_panels_cost:,} kr".replace(",", " "))
        if selected_visual == "Utslipp":    
            #with st.expander("Utslipp"):
            reference_array = thermal_array_delivered + electric_array
            scenario_array = grid_array
            #--
            reference_array = reference_array * self.co2_kWh
            scenario_array = scenario_array * self.co2_kWh
            #--
            st.write("**Utslipp ved strøm**")
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"<span style='color:{grid_color}'><small>Utgangspunkt<br>**{self.__rounding_to_int(np.sum(reference_array)):,}** tonn CO2".replace(",", " "), unsafe_allow_html=True)
            with c2:
                st.markdown(f"<span style='color:{stand_out_color}'><small>{scenario_name}<br>**{self.__rounding_to_int(np.sum(scenario_array)):,}** tonn CO2 (-{100 - self.__rounding_to_int((np.sum(scenario_array)/np.sum(reference_array))*100)}%)".replace(",", " "), unsafe_allow_html=True)
            
    def display_scenario_results(self, df, key, default_option):
        if (len(df)) == 0:
            st.warning('Du er utenfor kartutsnittet', icon="⚠️")
            st.stop()
        else:
            df = self.__cleanup_df(df = df) # wierd
            self.__show_scenario_results(key = key, default_option = default_option)
            
    def display_map_results(self, df, key, default_option):
        if (len(df)) == 0:
            st.warning('Du er utenfor kartutsnittet', icon="⚠️")
            st.stop()
        else:
            df = self.__cleanup_df(df = df)
            self.__show_map_results(key = key, default_option = default_option)

    def scenario_picker(self, key, default_label = "Velg scenario", default_option = 0):
        scenario_name = st.selectbox(
            label = default_label, 
            options = [item for item in self.scenario_name_list if item != "Referansesituasjon"],
            index = default_option,
            key = f"{key}_scenario"
            )
        return scenario_name
                           
    def app(self):
        self.progress_bar = st.progress(0, text = "Laster inn...")
        self.adjust_input_parameters_before()
        #st.info("TODO: Symbolisering på kart, muligheter for ulike valg? [som prosent 0 - 100% av maksimal verdi] 1) Høyest effekt 2) Høyest energibruk 3) Høyest oppvarming 4) Høyest elspesifikt. Også mulighet til å filterer på ulike scenarier?")
        self.import_dataframes()
        self.progress_bar.progress(33)
        self.adjust_input_parameters_middle()
        c1, c2 = st.columns([1, 1])
        with c1:
            self.dataframe_to_geodataframe(df = self.df)
            self.map(df = self.df, scenario_name = self.map_scenario_name)
            self.progress_bar.progress(66)
        with c2:
            #if self.st_map["zoom"] > 24:
            #    st.warning("Du må zoome lenger ut")
            #else:
            self.filter_geodataframe() # returns a pandas dataframe -> self.filtered_df
            self.get_unique_series_ids()
        with c2:
            self.display_map_results(df = self.filtered_df, key = "map_results", default_option = 0)
        #--
        option_list = [
            "Måned",
            "Time for time",
            "Om scenarioet", 
            "ET-kurve",
            "Utslipp", 
            "Økonomi",
            ]
        self.selected_visual = st.selectbox(label = "", options = option_list, label_visibility="collapsed", key = "selectmode")
        c1, c2 = st.columns([1, 1])
        with c1:
            self.display_scenario_results(df = self.filtered_df, key = "topleft", default_option = 0)
        with c2:
            self.display_scenario_results(df = self.filtered_df, key = "topright", default_option = 1)
        #c1, c2 = st.columns([1, 1])
        #with c1:
        #    self.display_scenario_results(df = self.filtered_df, key = "bottomleft", default_option = 2)
        #with c2:
        #    self.display_scenario_results(df = self.filtered_df, key = "bottomright", default_option = 3)
        self.progress_bar.progress(100)
if __name__ == "__main__":
    dashboard = Dashboard()
    dashboard.app()
    if st.button("Hjem"):
        switch_page("Hjem")