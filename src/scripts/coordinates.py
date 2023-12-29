import pandas as pd
import requests
import streamlit as st


df = pd.read_excel("input/building_table_østmarka.xlsx")
x = df["x"].to_numpy()
y = df["y"].to_numpy()

street_list = []
name_list = []
housenumber_list = []
API_KEY = "400f888f4da9461387721ccbd1a0e0db"
for i in range(0, len(x)):
    lon = x[i]
    lat = y[i]


    #url = f"https://api.geoapify.com/v1/geocode/search?text={address}&limit=1&apiKey={API_KEY}"
    url = f"https://api.geoapify.com/v1/geocode/reverse?lat={lat}&lon={lon}&lang=fr&apiKey={API_KEY}"
    response = requests.get(url)
    data = response.json()
    data = data["features"][0]["properties"]

    try:
        street = data["street"]
    except Exception:
        street = 0
    try:
        housenumber = data["housenumber"]
    except Exception:
        housenumber = 0
    try:
        name = data["name"]
    except Exception:
        name = 0
    street_list.append(street)
    housenumber_list.append(housenumber)
    name_list.append(name)

df = pd.DataFrame({
    "Street" : street_list,
    "Housenumber" : housenumber_list,
    "Name" : name_list
})

df.to_csv("df.csv")
st.write(street_list)
st.write(housenumber_list)
st.write(name_list)