import pandas as pd
import numpy as np
from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import BackendApplicationClient
import time
import random
import swifter
import streamlit as st
from sklearn.linear_model import LinearRegression

class EnergyAnalysis:
    PROFET_BUILDINGSTANDARD = "profet_bygningsstandard"
    PROFET_BUILDINGTYPE = "profet_bygningstype"
    PROFET_DATE = "profet_date"
    BUILDING_TYPE = "bygningstype_navn"
    BUILDING_YEAR = "tatt_i_bruk"
    BUILDING_AREA = "bruksareal_totalt"
    OBJECT_ID = "objectid"
    STORIES = "antall_etasjer"
    BUILDING_ID = "bygning_id"
    BEBYGD_AREA = "bebygd_areal"
    LATITUDE = "x"
    LONGITUDE = "y"
    
    BUILDING_STANDARDS = {
            "Eldre": "Reg", 
            "TEK10/TEK17": "Eff-E", 
            "Passivhus": "Vef"
            }
    
    PROFET_DATA = pd.read_csv('src/profet_data.csv', sep = ";")

    GSHP = 'grunnvarme'
    SOLAR_PANELS = 'solceller'
    ASHP = 'luft_luft_varmepumpe'
    DISTRICT_HEATING = 'fjernvarme'
    BUILDING_STANDARD_UPGRADED = 'oppgraderes'
    HEATING_EXISTS = 'varme_finnes'
    REDUCE_THERMAL_DEMAND = 'reduksjon_termiskbehov'
    REDUCE_ELECTRIC_DEMAND = 'reduksjon_elektriskbehov'
    
    SCENARIO_NAME = "scenario_navn"
    THERMAL_DEMAND_FOR_CALCULATION = '_termisk_energibehov'
    SPACEHEATING_DEMAND = '_romoppvarming_energibehov'
    DHW_DEMAND = '_tappevann_energibehov'
    ELECTRIC_DEMAND = '_elspesifikt_energibehov'
    ELECTRIC_DEMAND_FOR_CALCULATION = '_elektrisk_energibehov'
    COMPRESSOR = '_kompressor'
    PEAK = '_spisslast'
    FROM_SOURCE = '_levert_fra_kilde'
    DISTRICT_HEATING_PRODUCED = '_fjernvarmeproduksjon'
    SOLAR_PANELS_PRODUCED = '_solcelleproduksjon'
    GRID = '_nettutveksling'
    
    HAS_WELL = 'har_grunnvarme'
    HAS_DISTRICTHEATING = 'har_fjernvarme'
    HAS_ADDRESS = 'har_adresse'
    HAS_EXISTING_DATA = 'har_eksisterende_data'
    
    SOLARPANEL_DATA = pd.read_csv('src/solenergi_antakelser.csv', sep = ";")
    
    BUILDING_TYPES = {
            "Hus": "Hou",
            "Leilighet": "Apt",
            "Kontor": "Off",
            "Butikk": "Shp",
            "Hotell": "Htl",
            "Barnehage": "Kdg",
            "Skole": "Sch",
            "Universitet": "Uni",
            "Kultur": "CuS",
            "Sykehjem": "Nsh",
            "Sykehus": "Other",
            "Andre": "Other"
        }
    
    DEKNINGSGRADER_GSHP = {
            'Hus' : 100, 
            'Leilighet' : 95,
            "Kontor" : 95,
            "Butikk" : 95,
            "Hotell" : 95,
            "Barnehage" : 95,
            "Skole" : 95,
            "Universitet" : 95,
            "Kultur" : 95,
            "Sykehjem" : 95,
            "Sykehus" : 95,
            "Andre" : 95,
            }
    
    COEFFICIENT_OF_PERFORMANCES_GSHP = {
        'Hus' : 3.5, 
        'Leilighet' : 3.5,
        "Kontor" : 3.5,
        "Butikk" : 3.5,
        "Hotell" : 3.5,
        "Barnehage" : 3.5,
        "Skole" : 3.5,
        "Universitet" : 3.5,
        "Kultur" : 3.5,
        "Sykehjem" : 3.5,
        "Sykehus" : 3.5,
        "Andre" : 3.5,
        }
    
    SOLARPANEL_BUILDINGS = {
            'Hus' : 'Småhus', 
            'Leilighet' : 'Boligblokk',
            'Kontor' : 'Næringsbygg_mindre',
            'Butikk' : 'Næringsbygg_større',
            'Hotell' : 'Småhus', 
            'Barnehage' : 'Boligblokk',
            'Skole' : 'Næringsbygg_mindre',
            'Universitet' : 'Næringsbygg_mindre',
            'Kultur' : 'Næringsbygg_større',
            'Sykehjem' : 'Småhus', 
            'Sykehus' : 'Boligblokk',
            'Andre' : 'Næringsbygg_mindre',
        }
    
    def __init__(self, building_table, energy_area_id, building_area_id, scenario_file_name, temperature_array_file_path):
        self.BUILDING_TABLE = building_table
        self.ENERGY_AREA_ID = energy_area_id
        self.BUILDING_AREA_ID = building_area_id
        self.SCENARIO_FILE_NAME = scenario_file_name
        self.TEMPERATURE_ARRAY_FILE_NAME = temperature_array_file_path
                
    def __lower_column_names(self, df):
        df.rename(columns=lambda x: x.lower(), inplace=True)
        return df
    
    def __replace_null(self, df):
        df.replace('<Null>', 0, inplace=True)
        return df
        
    def __populate_profet_columns(self, df):
        def assign_buildingstandard(row):
            if row[self.PROFET_DATE].year <= 2007:
                return "Eldre"
            elif row[self.PROFET_DATE].year > 2022:
                return "Passivhus"
            elif row[self.PROFET_DATE].year > 2007 and row[self.PROFET_DATE].year <= 2022:
                return "TEK10/TEK17"
            
        def map_values(input_string):
            for key, value in mapping_dict.items():
                if key in input_string:
                    return value
            return None
        
        unique_buildings = df[self.BUILDING_TYPE].unique()
        unique_buildings = [unique_building for unique_building in unique_buildings if isinstance(unique_building, str)]
        mapping_dict = {
            "sykehus" : "Sykehus",
            "helse" : "Sykehus",
            "hotell" : "Hotell",
            "barnehage" : "Barnehage",
            "sykehjem" : "Sykehjem",
            "behandling" : "Sykehjem",
            "skole" : "Skole",
            "kontor" : "Kontor",
            "fritidsbygg" : "Hus",
            "bofellesskap" : "Sykehjem",
            "bolig": "Hus",
            "hus": "Hus",
        }
        unique_buildings = [string.lower() for string in unique_buildings] # list 2
        mapped_values = [map_values(string) for string in unique_buildings] # list 1
        building_map = {}
        for item1, item2 in zip(unique_buildings, mapped_values):
            if item1 is not None:
                if item1 in building_map:
                    building_map[item1].append(item2)
                else:
                    building_map[item1] = [item2]
        building_map = {key: value[0].strip('[]') if value and isinstance(value[0], str) else value[0] for key, value in building_map.items()}
        capitalized_map = {key.capitalize(): value for key, value in building_map.items()}
        df[self.PROFET_BUILDINGTYPE] = df[self.BUILDING_TYPE].map(capitalized_map)
        df[self.PROFET_DATE] = pd.to_datetime(df[self.BUILDING_YEAR], format='%Y%m%d', errors='coerce', exact=False)
        df[self.PROFET_BUILDINGSTANDARD] = df.apply(assign_buildingstandard, axis=1)
        return df
    
    def __drop_null_rows(self, df):
        df = df[df[self.BUILDING_AREA] != 0]
        return df
    
    def __if_not_profet_categories(self, df):
        df[self.PROFET_BUILDINGTYPE].fillna('Andre', inplace=True)
        df[self.PROFET_BUILDINGSTANDARD].fillna('Eldre', inplace=True)
        return df
    
    def __cleanup_columns(self, df):
        df = df[[
            self.OBJECT_ID,
            self.ENERGY_AREA_ID,
            self.BUILDING_AREA_ID,
            self.HAS_WELL,
            self.HAS_DISTRICTHEATING,
            self.HAS_ADDRESS,
            self.BUILDING_ID, 
            self.BUILDING_TYPE, 
            self.PROFET_BUILDINGTYPE, 
            self.PROFET_BUILDINGSTANDARD, 
            self.BUILDING_AREA, 
            self.BEBYGD_AREA, 
            self.STORIES, 
            self.LATITUDE, 
            self.LONGITUDE, 
            ]]
        return df
    
    def __area_sort(self, df):
        df = df.sort_values(by=[self.BUILDING_AREA], ascending=[False])
        df = df.reset_index(drop = True)
        return df
     
    def __read_xlsx(self):
        df = pd.read_excel(f"input/{self.BUILDING_TABLE}")
        return df
    
    def __read_xlsx_sheets(self):
        df = pd.read_excel(f"input/{self.BUILDING_TABLE}", sheet_name=None)
        self.address_dict = df 
        keys = list(df.keys())
        keys.pop(0)
        self.address_keys = keys
        #for key in keys:
        #    st.write(key)
        #    st.write(df[key])
        #return sheet  
    
    def import_xlsx(self):
        self.__read_xlsx_sheets()
        df = self.__read_xlsx()
        df = self.__lower_column_names(df)
        df = self.__replace_null(df)
        df = self.__populate_profet_columns(df)
        df = self.__drop_null_rows(df)
        df = self.__if_not_profet_categories(df)
        df = self.__cleanup_columns(df)
        df = self.__area_sort(df)            
        return df
    
    def __read_scenario_file_excel(self):
        variable_dict = {}
        xls_keys = list(pd.read_excel(self.SCENARIO_FILE_NAME, sheet_name = None).keys())
        for key in xls_keys:
            df = pd.read_excel(self.SCENARIO_FILE_NAME, sheet_name = key, index_col=0)
            df = df.T
            energy_dicts = df.to_dict()
            variable_dict[key] = energy_dicts
        energy_dicts_of_dicts = []
        for i in range(0, len(variable_dict)):
            energy_dicts_of_dicts.append(variable_dict[xls_keys[i]])
        return energy_dicts_of_dicts, xls_keys
          
    def __get_secret(self, filename):
        with open(filename) as file:
            secret = file.readline()
        return secret
        
    def __profet_api(self, building_standard, building_type, area, temperature_array):
        oauth = OAuth2Session(client=BackendApplicationClient(client_id="profet_2023"))
        predict = OAuth2Session(
            token=oauth.fetch_token(
                token_url="https://identity.byggforsk.no/connect/token",
                client_id="profet_2023",
                client_secret=self.__get_secret("src/secret.txt"),
            )
        )
        selected_standard = self.BUILDING_STANDARDS[building_standard]
        if selected_standard == "Reg":
            regular_area, efficient_area, veryefficient_area = area, 0, 0
        if selected_standard == "Eff-E":
            regular_area, efficient_area, veryefficient_area = 0, area, 0
        if selected_standard == "Vef":
            regular_area, efficient_area, veryefficient_area = 0, 0, area
        # --
        if len(temperature_array) == 0:
            request_data = {
                "StartDate": "2022-01-01", 
                "Areas": {f"{self.BUILDING_TYPES[building_type]}": {"Reg": regular_area, "Eff-E": efficient_area, "Eff-N": 0, "Vef": veryefficient_area}},
                "RetInd": False,  # Boolean, if True, individual profiles for each category and efficiency level are returned
                "Country": "Norway"}
        else:
            request_data = {
            "StartDate": "2022-01-01", 
            "Areas": {f"{self.BUILDING_TYPES[building_type]}": {"Reg": regular_area, "Eff-E": efficient_area, "Eff-N": 0, "Vef": veryefficient_area}},
            "RetInd": False,  # Boolean, if True, individual profiles for each category and efficiency level are returned
            "Country": "Norway",  # Optional, possiblity to get automatic holiday flags from the python holiday library.
            "TimeSeries": {"Tout": temperature_array}}
            
        r = predict.post(
            "https://flexibilitysuite.byggforsk.no/api/Profet", json=request_data
        )
        if r.status_code == 200:
            df = pd.DataFrame.from_dict(r.json())
            df.reset_index(drop=True, inplace=True)
            profet_df = df[["Electric", "DHW", "SpaceHeating"]]
            dhw_demand = profet_df['DHW'].to_numpy()
            spaceheating_demand = profet_df['SpaceHeating'].to_numpy()
            electric_demand = profet_df['Electric'].to_numpy()
            return dhw_demand, spaceheating_demand, electric_demand
        else:
            raise TypeError("PROFet virker ikke")
        
    def preprocess_profet_data(self, temperature_array):
        result_df = pd.DataFrame()
        for building_type in self.BUILDING_TYPES:
            for building_standard in self.BUILDING_STANDARDS:
                dhw_demand, spaceheating_demand, electric_demand = self.__profet_api(building_standard = building_standard, building_type = building_type, area = 1, temperature_array = temperature_array)
                dhw_col_name = f"{building_type}_{building_standard}_DHW"
                spaceheating_col_name = f"{building_type}_{building_standard}_SPACEHEATING"
                electric_col_name = f"{building_type}_{building_standard}_ELECTRIC"
                result_df[dhw_col_name] = dhw_demand.flatten()
                result_df[spaceheating_col_name] = spaceheating_demand.flatten()
                result_df[electric_col_name] = electric_demand.flatten()
        result_df.to_csv("src/profet_data.csv", sep = ";")
        return result_df
    
    def preprocess_luft_luft_varmepumpe(self, temperature_array):
        COP_NOMINAL = 5  # Nominell COP
        temperature_datapoints = [-15, 2, 7] # SN- NSPEK 3031:2023 - tabell K.13
        P_3031 = np.array([
            [0.46, 0.72, 1],
            [0.23, 0.36, 0.5],
            [0.09, 0.14, 0.2]
            ])
        COP_3031 = np.array([
            [0.44, 0.53, 0.64],
            [0.61, 0.82, 0.9],
            [0.55, 0.68, 0.82]
            ])
        P_3031_list = []
        COP_3031_list = []
        for i in range(0, len(temperature_datapoints)):
            P_3031_list.append(np.polyfit(x = temperature_datapoints, y = P_3031[i], deg = 1))
            COP_3031_list.append(np.polyfit(x = temperature_datapoints, y = COP_3031[i], deg = 1))

        self.P_HP_DICT = []
        self.COP_HP_DICT = []
        self.INTERPOLATE_HP_DICT = []
        for index, outdoor_temperature in enumerate(temperature_array):
            p_hp_list = np.array([np.polyval(P_3031_list[0], outdoor_temperature), np.polyval(P_3031_list[1], outdoor_temperature), np.polyval(P_3031_list[2], outdoor_temperature)])
            cop_hp_list = np.array([np.polyval(COP_3031_list[0], outdoor_temperature), np.polyval(COP_3031_list[1], outdoor_temperature), np.polyval(COP_3031_list[2], outdoor_temperature)]) * COP_NOMINAL
            interpolate_hp_list = np.polyfit(x = p_hp_list, y = cop_hp_list, deg = 0)[0]
            #--
            self.P_HP_DICT.append(p_hp_list)
            self.COP_HP_DICT.append(cop_hp_list)
            self.INTERPOLATE_HP_DICT.append(interpolate_hp_list)
            
    def __load_temperature_array(self):
        array = pd.read_excel(self.TEMPERATURE_ARRAY_FILE_NAME).to_numpy()
        array = array.flatten().tolist()
        self.temperature_array = array
        self.WINTER_MAX = np.argmax(array)
        self.SUMMER_MAX = 5000
        return array
    
    def __string_percentage(self, string):
        if len(string) == 2:
            number = int(f"{string[1]}")
        elif len(string) == 3:
            number = int(f"{string[1]}{string[2]}")
        elif len(string) == 4:
            number = int(f"{string[1]}{string[2]}{string[3]}")
            if number > 100:
                raise TypeError("Prosent kan ikke være over 100%")
        return number
    
    def modify_scenario(self, df, energy_dicts):
        table_no_entries = df.loc[(df[self.GSHP] == 0) & (df[self.DISTRICT_HEATING] == 0) & (df[self.ASHP] == 0) & (df[self.SOLAR_PANELS] == 0)]
        new_df = self.create_scenario(df = table_no_entries, energy_dicts = energy_dicts)
        df = pd.concat([new_df, df])
        df = df.drop_duplicates(subset=self.OBJECT_ID, keep="first")
        df = df.sort_values(self.OBJECT_ID).reset_index(drop=True)
        return df
    
    def __rounding_effect(self, number):
        return number
        #return round((number / 1000), 10)
    
    def __rounding_energy(self, number):
        return number
        #return round((number / (1000 * 1000)), 10)
        
    def __predict_heating_demand(self, demand, temperature):
        #data = pd.DataFrame({'Demand': demand, 'Temperature': temperature})
        #filtered_data = data[data['Temperature'] < 10]
        #model = LinearRegression()
        #model.fit(filtered_data[['Temperature']], filtered_data['Demand'])
        #predicted_demand = model.predict(data[['Temperature']])
        #data['Predicted_Demand'] = predicted_demand
        #data['Heating_Demand'] = data['Demand'] - data['Predicted_Demand']
        #data['Heating_Demand'] = np.where(data['Heating_Demand'] < 0, 0, data['Heating_Demand'])
        #heating_related_demand = data['Heating_Demand']
        electric_related_demand = self.__dekningsgrad_calculation(dekningsgrad = 50, timeserie = demand)
        if np.sum(demand - electric_related_demand) < 100:
            electric_related_demand = demand * 0.5
        heating_related_demand = demand - electric_related_demand
        return heating_related_demand, electric_related_demand

    def demand_calculation_simplified(self, row):
        try:
            if row[self.HAS_EXISTING_DATA] == True:
                #--
                existing_data_df = self.address_dict[row[self.HAS_ADDRESS]]
                heat_production = existing_data_df["Varmeproduksjon"].to_numpy()
                power_production = existing_data_df["Strømproduksjon"].to_numpy()
                # ml
                grid_array = existing_data_df["Levert energi til bygg (strømmåler)"].to_numpy()
                heating_related_demand, electric_related_demand = self.__predict_heating_demand(demand = grid_array, temperature = self.temperature_array)
                #--
                thermal_demand_for_calculation = heating_related_demand #+ heat_production
                electric_demand_for_calculation = electric_related_demand
                electric_demand = electric_related_demand + power_production
                spaceheating_demand = heating_related_demand
                dhw_demand = heat_production
            else:
                spaceheating_series = self.PROFET_DATA[f"{row[self.PROFET_BUILDINGTYPE]}_{row[self.PROFET_BUILDINGSTANDARD]}_SPACEHEATING"]
                spaceheating_demand = row[self.BUILDING_AREA] * np.array(spaceheating_series)
                dhw_demand_series = self.PROFET_DATA[f"{row[self.PROFET_BUILDINGTYPE]}_{row[self.PROFET_BUILDINGSTANDARD]}_DHW"]
                dhw_demand = row[self.BUILDING_AREA] * np.array(dhw_demand_series)
                electric_demand_series = self.PROFET_DATA[f"{row[self.PROFET_BUILDINGTYPE]}_{row[self.PROFET_BUILDINGSTANDARD]}_ELECTRIC"]
                electric_demand = row[self.BUILDING_AREA] * np.array(electric_demand_series)
                #--
                thermal_demand_for_calculation = dhw_demand + spaceheating_demand
                electric_demand_for_calculation = electric_demand
            #--
            thermal_demand_for_calculation = thermal_demand_for_calculation - (thermal_demand_for_calculation/100)*row[self.REDUCE_THERMAL_DEMAND]
            electric_demand_for_calculation = electric_demand_for_calculation - (electric_demand_for_calculation/100)*row[self.REDUCE_ELECTRIC_DEMAND]
        except Exception as e:
            thermal_demand_for_calculation, electric_demand_for_calculation, spaceheating_demand, dhw_demand, electric_demand = [0], [0], [0], [0], [0]
        
        return thermal_demand_for_calculation, electric_demand_for_calculation, spaceheating_demand, dhw_demand, electric_demand
    
    def __dekningsgrad_calculation(self, dekningsgrad, timeserie):
        if dekningsgrad == 100:
            return timeserie
        timeserie_sortert = np.sort(timeserie)
        timeserie_sum = np.sum(timeserie)
        timeserie_N = len(timeserie)
        startpunkt = timeserie_N // 2
        i = 0
        avvik = 0.0001
        pm = 2 + avvik
        while abs(pm - 1) > avvik:
            cutoff = timeserie_sortert[startpunkt]
            timeserie_tmp = np.where(timeserie > cutoff, cutoff, timeserie)
            beregnet_dekningsgrad = (np.sum(timeserie_tmp) / timeserie_sum) * 100
            pm = beregnet_dekningsgrad / dekningsgrad
            gammelt_startpunkt = startpunkt
            if pm < 1:
                startpunkt = startpunkt + timeserie_N // 2 ** (i + 2) - 1
            else:
                startpunkt = startpunkt - timeserie_N // 2 ** (i + 2) - 1
            if startpunkt == gammelt_startpunkt:
                break
            i += 1
            if i > 13:
                break
        return timeserie_tmp
    
    def varmepumpe_calculation(self, row):
        VIRKNINGSGRAD = 1
        kompressor, levert_fra_kilde, spisslast = 0, 0, 0
        try:
            if (row[self.GSHP] == 1) | (row[self.ASHP] == 1):
                varmebehov = row[self.THERMAL_DEMAND_FOR_CALCULATION] * VIRKNINGSGRAD
                if row[self.GSHP] == 1:
                    levert_fra_varmepumpe = self.__dekningsgrad_calculation(self.DEKNINGSGRADER_GSHP[row[self.PROFET_BUILDINGTYPE]], varmebehov * VIRKNINGSGRAD)
                    levert_fra_kilde = levert_fra_varmepumpe - (levert_fra_varmepumpe/self.COEFFICIENT_OF_PERFORMANCES_GSHP[row[self.PROFET_BUILDINGTYPE]])
                    kompressor = levert_fra_varmepumpe - levert_fra_kilde
                    levert_fra_kilde = levert_fra_varmepumpe - kompressor
                    spisslast = varmebehov - levert_fra_varmepumpe
                else:
                    temperature = self.temperature_array # kan utbedres
                    varmepumpe = np.zeros(8760)
                    cop = np.zeros(8760)
                    P_NOMINAL = np.max(varmebehov) * 0.4 # 40% effektdekningsgrad
                    if P_NOMINAL > 10: # ikke større varmepumpe enn 10 kW?
                        P_NOMINAL = 10
                    for i, outdoor_temperature in enumerate(temperature):
                        effekt = varmebehov[i]
                        if outdoor_temperature < -15:
                            cop[i] = 1
                            varmepumpe[i] = 0
                        else:
                            varmepumpe_effekt_verdi = effekt
                            p_hp_list = self.P_HP_DICT[i] * P_NOMINAL
                            cop_hp_list = self.COP_HP_DICT[i]
                            if effekt >= p_hp_list[0]:
                                varmepumpe_effekt_verdi = p_hp_list[0]
                                cop_verdi = cop_hp_list[0]
                            elif effekt <= p_hp_list[2]:
                                cop_verdi = cop_hp_list[2]
                            else:
                                cop_verdi = self.INTERPOLATE_HP_DICT[i]
                            varmepumpe[i] = varmepumpe_effekt_verdi
                            cop[i] = cop_verdi
                    levert_fra_kilde = varmepumpe - varmepumpe / np.array(cop_verdi)
                    kompressor = varmepumpe - levert_fra_kilde
                    spisslast = varmebehov - varmepumpe
        except Exception:
            pass
            #logger.info('Varmepumpeberegning feilet')
        return kompressor, -levert_fra_kilde, spisslast

    def fjernvarme_calculation(self, row):
        VIRKNINGSGRAD = 1
        DEKNINGSGRAD = 100
        fjernvarme = 0
        try:
            if row[self.DISTRICT_HEATING] == 1:
                fjernvarme = self.__dekningsgrad_calculation(DEKNINGSGRAD, row[self.THERMAL_DEMAND_FOR_CALCULATION] * VIRKNINGSGRAD)
        except Exception:
            pass
            #logger.info("Fjernvarmeberegning feilet")
        return -fjernvarme

    def solcelle_calculation(self, row):
        solceller = 0
        try:
            if row[self.BUILDING_AREA] != 0:
                area = row[self.BEBYGD_AREA]
                if area == 0:
                    try:
                        number_of_floors = row[self.STORIES]
                        scale_factor = number_of_floors
                    except:
                        scale_factor = 5
                    area = row[self.BUILDING_AREA] / scale_factor
                if row[self.SOLAR_PANELS] == 1:
                    solceller = area * self.SOLARPANEL_DATA[self.SOLARPANEL_BUILDINGS[row[self.PROFET_BUILDINGTYPE]]].to_numpy()
        except Exception:
            pass
            #logger.info("Solcelleberegning feilet")
        return -solceller
    
    def grunnvarme_meter_and_cost_calculation(self, row):
        well_meter, gshp_cost = 0, 0
        try:
            if row[self.GSHP] == True:
                cost_per_well_meter = 600
                well_meter = round(np.sum(abs(row[self.FROM_SOURCE])) / 80,0)
                gshp_cost = round(well_meter * cost_per_well_meter,0)
        except Exception:
            pass
            #logger.info("Kostnadsberegning grunnvarme feilet")
        return well_meter, gshp_cost
        
    def compile_data(self, row):
        if (len(row[self.THERMAL_DEMAND_FOR_CALCULATION]) == 1) or (len(row[self.ELECTRIC_DEMAND_FOR_CALCULATION]) == 1):
            total_balance, year_sum, winter_max, summer_max = 0, 0, 0, 0 
        else:
            thermal_balance = row[self.THERMAL_DEMAND_FOR_CALCULATION] + row[self.FROM_SOURCE] - row[self.COMPRESSOR] - row[self.PEAK] + row[self.DISTRICT_HEATING_PRODUCED]
            electric_balance = row[self.ELECTRIC_DEMAND_FOR_CALCULATION] + row[self.COMPRESSOR] + row[self.PEAK] + row[self.SOLAR_PANELS_PRODUCED]
            total_balance = thermal_balance + electric_balance
            year_sum = round(np.sum(total_balance),-2)
            winter_max = round((total_balance[self.WINTER_MAX]),0)
            summer_max = round((total_balance[self.SUMMER_MAX]),0)
        return total_balance, self.__rounding_energy(year_sum), self.__rounding_effect(winter_max), self.__rounding_effect(summer_max)
    
    def sumify(self, row):
        thermal_demand = self.__rounding_energy(np.sum(row[self.THERMAL_DEMAND_FOR_CALCULATION]))
        from_source = self.__rounding_energy(np.sum(row[self.FROM_SOURCE]))
        district_heating_produced = self.__rounding_energy(np.sum(row[self.DISTRICT_HEATING_PRODUCED]))
        electric_demand = self.__rounding_energy(np.sum(row[self.ELECTRIC_DEMAND_FOR_CALCULATION]))
        compressor = self.__rounding_energy(np.sum(row[self.COMPRESSOR]))
        peak = self.__rounding_energy(np.sum(row[self.PEAK]))
        solar_panels_produced = self.__rounding_energy(np.sum(row[self.SOLAR_PANELS_PRODUCED]))
        return abs(thermal_demand), abs(from_source), abs(district_heating_produced), abs(electric_demand), abs(compressor), abs(peak), abs(solar_panels_produced)
    
    def maxify_winter(self, row):
        max_index = self.WINTER_MAX
        try:
            thermal_demand = self.__rounding_effect((row[self.THERMAL_DEMAND_FOR_CALCULATION])[max_index])
        except Exception:
            thermal_demand = 0
        try:
            from_source = self.__rounding_effect((row[self.FROM_SOURCE])[max_index])
        except Exception:
            from_source = 0
        try:
            district_heating_produced = self.__rounding_effect((row[self.DISTRICT_HEATING_PRODUCED])[max_index])
        except Exception:
            district_heating_produced = 0
        try:
            electric_demand = self.__rounding_effect((row[self.ELECTRIC_DEMAND_FOR_CALCULATION])[max_index])
        except Exception:
            electric_demand = 0
        try:
            compressor = self.__rounding_effect((row[self.COMPRESSOR])[max_index])
        except Exception:
            compressor = 0
        try:
            peak = self.__rounding_effect((row[self.PEAK])[max_index])
        except Exception:
            peak = 0
        try:
            solar_panels_produced = self.__rounding_effect((row[self.SOLAR_PANELS_PRODUCED])[max_index])
        except Exception:
            solar_panels_produced = 0
        return abs(thermal_demand), abs(from_source), abs(district_heating_produced), abs(electric_demand), abs(compressor), abs(peak), abs(solar_panels_produced)     
    
    def maxify_summer(self, row):
        max_index = self.SUMMER_MAX
        try:
            thermal_demand = self.__rounding_effect((row[self.THERMAL_DEMAND_FOR_CALCULATION])[max_index])
        except Exception:
            thermal_demand = 0
        try:
            from_source = self.__rounding_effect((row[self.FROM_SOURCE])[max_index])
        except Exception:
            from_source = 0
        try:
            district_heating_produced = self.__rounding_effect((row[self.DISTRICT_HEATING_PRODUCED])[max_index])
        except Exception:
            district_heating_produced = 0
        try:
            electric_demand = self.__rounding_effect((row[self.ELECTRIC_DEMAND_FOR_CALCULATION])[max_index])
        except Exception:
            electric_demand = 0
        try:
            compressor = self.__rounding_effect((row[self.COMPRESSOR])[max_index])
        except Exception:
            compressor = 0
        try:
            peak = self.__rounding_effect((row[self.PEAK])[max_index])
        except Exception:
            peak = 0
        try:
            solar_panels_produced = self.__rounding_effect((row[self.SOLAR_PANELS_PRODUCED])[max_index])
        except Exception:
            solar_panels_produced = 0
        return abs(thermal_demand), abs(from_source), abs(district_heating_produced), abs(electric_demand), abs(compressor), abs(peak), abs(solar_panels_produced) 
    
    def run_simulation(self, df, scenario_name, chunk_size = 1000, test = True):
        def __chunkify(df, chunk_size):
            list_df = [df[i:i+chunk_size] for i in range(0,df.shape[0],chunk_size)]
            return list_df
    
        def __merge_dataframe_list(df_chunked_list):
            df_results = pd.concat(df_chunked_list).reset_index(drop=True)
            df_results = df_results.sort_values(self.OBJECT_ID).reset_index(drop=True)
            return df_results
        
        def __export_hourly_data(df):
            hourly_data_fiels = [f'{self.GRID}_energi_liste', self.DHW_DEMAND, self.SPACEHEATING_DEMAND, self.ELECTRIC_DEMAND_FOR_CALCULATION, self.ELECTRIC_DEMAND, self.THERMAL_DEMAND_FOR_CALCULATION]
            new_df = pd.DataFrame()
            for datafield in hourly_data_fiels:
                old_df = pd.DataFrame()
                for count, row in df.iterrows():
                    object_id = row[self.OBJECT_ID]
                    array = np.zeros(8760)
                    try:
                        array = row[datafield].flatten()
                    except Exception:
                        pass
                    old_df[f"{object_id}"] = array
                old_df["ID"] = datafield
                new_df = pd.concat([old_df, new_df]).reset_index(drop=True)
            new_df["scenario"] = scenario_name
            new_df.to_csv(f"output/{scenario_name}_timedata.csv")
        
        def __clean_dataframe_and_export_to_csv(df, scenario_name):
            __export_hourly_data(df = df)
            df["scenario"] = scenario_name
            df.to_csv(f"output/{scenario_name}_unfiltered.csv")
            #df.drop([self.THERMAL_DEMAND, self.ELECTRIC_DEMAND, self.COMPRESSOR, self.FROM_SOURCE, self.PEAK, self.DISTRICT_HEATING_PRODUCED, self.SOLAR_PANELS_PRODUCED, f'_nettutveksling_energi_liste'], axis=1, inplace=True)
            df[self.SCENARIO_NAME] = scenario_name
            #df.to_csv(f"output/{scenario_name}_filtered.csv")
            return df

        df_chunked_list = []
        chunked = __chunkify(df = df, chunk_size = chunk_size)
        for index, df_chunked in enumerate(chunked):
            df_chunked[self.THERMAL_DEMAND_FOR_CALCULATION], df_chunked[self.ELECTRIC_DEMAND_FOR_CALCULATION], df_chunked[self.SPACEHEATING_DEMAND], df_chunked[self.DHW_DEMAND], df_chunked[self.ELECTRIC_DEMAND] = zip(*df_chunked.apply(self.demand_calculation_simplified, axis=1))
            # supply
            df_chunked[self.COMPRESSOR], df_chunked[self.FROM_SOURCE], df_chunked[self.PEAK] = zip(*df_chunked.apply(self.varmepumpe_calculation, axis=1))
            df_chunked[self.DISTRICT_HEATING_PRODUCED] = df_chunked.apply(self.fjernvarme_calculation, axis=1)
            df_chunked[self.SOLAR_PANELS_PRODUCED] = df_chunked.apply(self.solcelle_calculation, axis=1)
            # costs
            df_chunked[f"{self.GSHP}_meter"], df_chunked[f"{self.GSHP}_kostnad"] = zip(*df_chunked.apply(self.grunnvarme_meter_and_cost_calculation, axis=1))
            # conclusion
            df_chunked[f'{self.GRID}_energi_liste'], df_chunked[f'{self.GRID}_energi'], df_chunked[f'{self.GRID}_vintereffekt'], df_chunked[f'{self.GRID}_sommereffekt'] = zip(*df_chunked.apply(self.compile_data, axis=1))
            df_chunked[f'{self.THERMAL_DEMAND_FOR_CALCULATION}_sum'], df_chunked[f'{self.FROM_SOURCE}_sum'], df_chunked[f'{self.DISTRICT_HEATING_PRODUCED}_sum'], df_chunked[f'{self.ELECTRIC_DEMAND_FOR_CALCULATION}_sum'], df_chunked[f'{self.COMPRESSOR}_sum'], df_chunked[f'{self.PEAK}_sum'], df_chunked[f'{self.SOLAR_PANELS_PRODUCED}_sum']  = zip(*df_chunked.apply(self.sumify, axis=1))   
            df_chunked[f'{self.THERMAL_DEMAND_FOR_CALCULATION}_vintereffekt'], df_chunked[f'{self.FROM_SOURCE}_vintereffekt'], df_chunked[f'{self.DISTRICT_HEATING_PRODUCED}_vintereffekt'], df_chunked[f'{self.ELECTRIC_DEMAND_FOR_CALCULATION}_vintereffekt'], df_chunked[f'{self.COMPRESSOR}_vintereffekt'], df_chunked[f'{self.PEAK}_vintereffekt'], df_chunked[f'{self.SOLAR_PANELS_PRODUCED}_vintereffekt']  = zip(*df_chunked.apply(self.maxify_winter, axis=1))   
            df_chunked[f'{self.THERMAL_DEMAND_FOR_CALCULATION}_sommereffekt'], df_chunked[f'{self.FROM_SOURCE}_sommereffekt'], df_chunked[f'{self.DISTRICT_HEATING_PRODUCED}_sommereffekt'], df_chunked[f'{self.ELECTRIC_DEMAND_FOR_CALCULATION}_sommereffekt'], df_chunked[f'{self.COMPRESSOR}_sommereffekt'], df_chunked[f'{self.PEAK}_sommereffekt'], df_chunked[f'{self.SOLAR_PANELS_PRODUCED}_sommereffekt']  = zip(*df_chunked.apply(self.maxify_summer, axis=1))   
            # append to
            df_chunked_list.append(df_chunked)
            if index == 2 and test == True:
                break 
        df = __merge_dataframe_list(df_chunked_list)
        # df logikk for å summere alt
        df = __clean_dataframe_and_export_to_csv(df, scenario_name)
        return df
    
    def add_random_values(self, df, energy_id, building_type, percentage, column):
        fill_value = True
        if (column == self.GSHP) or (column == self.ASHP) or (column == self.DISTRICT_HEATING):
            unselected_df = df[~((df[self.ENERGY_AREA_ID] == energy_id) & (df[self.PROFET_BUILDINGTYPE] == building_type) & (df[self.HEATING_EXISTS] != fill_value))]
            selected_df = df[(df[self.ENERGY_AREA_ID] == energy_id) & (df[self.PROFET_BUILDINGTYPE] == building_type) & (df[self.HEATING_EXISTS] != fill_value)]
        else:
            unselected_df = df[~((df[self.ENERGY_AREA_ID] == energy_id) & (df[self.PROFET_BUILDINGTYPE] == building_type))]
            selected_df = df[(df[self.ENERGY_AREA_ID] == energy_id) & (df[self.PROFET_BUILDINGTYPE] == building_type)]
        number_of_rows = len(selected_df)
        n_values = int((percentage / 100) * number_of_rows)
        random_indices = random.sample(range(number_of_rows), n_values)
        random_values = [fill_value for _ in range(n_values)]
        selected_df = selected_df.sort_values(self.OBJECT_ID).reset_index(drop=True)
        selected_df.loc[random_indices, column] = random_values
        if (column == self.GSHP) or (column == self.ASHP) or (column == self.DISTRICT_HEATING):
            selected_df.loc[random_indices, self.HEATING_EXISTS] = random_values
        df = pd.concat([selected_df, unselected_df], ignore_index = True)
        return df
    
    def fill_reduction_values(self, df, energy_id, building_type, percentage, column):
        unselected_df = df[~((df[self.ENERGY_AREA_ID] == energy_id) & (df[self.PROFET_BUILDINGTYPE] == building_type))]
        selected_df = df[(df[self.ENERGY_AREA_ID] == energy_id) & (df[self.PROFET_BUILDINGTYPE] == building_type)]
        selected_df[column] = percentage
        df = pd.concat([selected_df, unselected_df], ignore_index = True)
        return df
    
    def create_scenario(self, df, energy_dicts):
        PERCENTAGE_CODE_MAP = {
            "G" : self.GSHP,
            "S" : self.SOLAR_PANELS,
            "V" : self.ASHP,
            "F" : self.DISTRICT_HEATING,
            "O" : self.BUILDING_STANDARD_UPGRADED,
            "T" : self.REDUCE_THERMAL_DEMAND,
            "E" : self.REDUCE_ELECTRIC_DEMAND
        }
        for supply_technology in [self.GSHP, self.SOLAR_PANELS, self.ASHP, self.DISTRICT_HEATING, self.BUILDING_STANDARD_UPGRADED, self.HEATING_EXISTS]:
            df[supply_technology] = False
            
        df[self.REDUCE_THERMAL_DEMAND] = 0
        df[self.REDUCE_ELECTRIC_DEMAND] = 0
        #--
        unique_energy_ids = df[self.ENERGY_AREA_ID].unique()
        for i in range(0, len(unique_energy_ids)): # energiområdeid
            energy_id = unique_energy_ids[i]
            #df_energy_id = df[df[self.ENERGY_AREA_ID] == energy_id]
            percentage_codes = energy_dicts[energy_id]
            building_types = list(percentage_codes.keys())
            for j in range(0, len(percentage_codes)): # bygningstype i energiområde
                building_type = building_types[j]
                percentage_code = percentage_codes[building_type]
                #st.write(energy_id, building_type, percentage_code)
                individual_percentage_codes = percentage_code.split("_")
                #st.write(individual_percentage_codes)
                for k in range(0, len(individual_percentage_codes)):
                    individual_percentage_code = individual_percentage_codes[k]
                    tiltak = PERCENTAGE_CODE_MAP[individual_percentage_code[0]]
                    tiltak_percentage = self.__string_percentage(individual_percentage_code)
                    #st.write(tiltak, tiltak_percentage)
                    df = self.add_random_values(df = df, energy_id = energy_id, building_type = building_type, percentage = tiltak_percentage, column = tiltak)
                    #df = self.fill_reduction_values(df = df, energy_id = energy_id, building_type = building_type, percentage = tiltak_percentage, column = tiltak)
        #--
        df[self.HAS_EXISTING_DATA] = False
        for index, row in df.iterrows():
            address = str(row[self.HAS_ADDRESS])
            if address in self.address_keys:
                df.at[index, self.HAS_EXISTING_DATA] = True
        return df
    
    def __default_simulation(self, df, energy_dicts, scenario_name):
        start_time = time.time()
        df = self.create_scenario(df = df, energy_dicts = energy_dicts)
        df = self.run_simulation(df = df, scenario_name = scenario_name)
        end_time = time.time()
        #logger.info(f"Simulering {scenario_name}: {round((end_time - start_time),0)} sekunder")
        #self.export_to_arcgis(df = df, gdb = gdb, scenario_name = scenario_name)   
        #logger.info(f"Eksportert til ArcGIS")
        return df
    
    def __modified_simulation(self, df, energy_dicts, scenario_name):
        start_time = time.time()
        df = self.modify_scenario(df = df, energy_dicts = energy_dicts)
        df = self.run_simulation(df = df, scenario_name = scenario_name)
        end_time = time.time()
        #logger.info(f"Simulering {scenario_name}: {round((end_time - start_time),0)} sekunder")
        #self.export_to_arcgis(df = df, gdb = gdb, scenario_name = scenario_name)  
        #logger.info(f"Eksportert til ArcGIS")
    
    def run_simulations(self, df):
        energy_dicts_of_dicts, scenario_names = self.__read_scenario_file_excel()
        
        df = self.__default_simulation(df = df, energy_dicts = energy_dicts_of_dicts[0], scenario_name = scenario_names[0])
        original_df = df.copy()
        
        for i in range(1, len(scenario_names)):
            self.__modified_simulation(df = original_df, energy_dicts = energy_dicts_of_dicts[i], scenario_name = scenario_names[i])
    
    def main(self):
        df = self.import_xlsx() # en df for alle planforslag
        temperature_array = self.__load_temperature_array()
        #self.preprocess_profet_data(temperature_array = temperature_array) # preprocess profet data
        self.preprocess_luft_luft_varmepumpe(temperature_array = temperature_array) # preprocess ashp
        self.run_simulations(df)