import streamlit as st
import pyomo.environ as pyo
import model

price, consumption, solar = model.get_data("energy_data.csv")

st.title("Home battery optimization")

start, end = st.slider("Hour range", 0, 168, (0,48))
battery_capacity = st.slider("Battery capacity kWH", 1, 100, 10)
battery_charging_rate = st.slider("Charging rate kWh", 1, 10, 5)
battery_percent = st.slider("Battery efficiency %", 0, 100, 90)
battery_efficiency = battery_percent / 100 #90 -> 0.9

m = model.build_model(price, consumption, solar, battery_capacity, battery_charging_rate, battery_efficiency)

st.write(f"Total weekly cost: {pyo.value(m.objective):.2f} kr")




fig = model.plot(m, price, start,end)
st.pyplot(fig)

