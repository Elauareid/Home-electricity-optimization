"""
Optimizes a home battery's charge/discharge schedule to minimize electricity
cost, given hourly price, consumption and solar data. Linear program built
with Pyomo and solved with HiGHS.
"""

import pandas as pd
import pyomo.environ as pyo
import matplotlib.pyplot as plt

datafile = "energy_data.csv"

def get_data(file):
    df = pd.read_csv(file)
    price = df["price_nok_per_kwh"].to_list()
    consumption = df["consumption_kwh"].to_list()
    solar = df["solar_kwh"].to_list()
    return price, consumption, solar



def build_model(price, consumption, solar, 
                max_battery=10, charging_rate=5, 
                battery_efficiency=0.9, battery_level=0):

    m = pyo.ConcreteModel()
    hours = range(len(price))

    m.buy = pyo.Var(hours, domain=pyo.NonNegativeReals)
    m.sell = pyo.Var(hours, domain=pyo.NonNegativeReals)
    m.charge = pyo.Var(hours, domain=pyo.NonNegativeReals, bounds=(0,charging_rate))
    m.discharge = pyo.Var(hours, domain=pyo.NonNegativeReals, bounds=(0,charging_rate))
    m.soc = pyo.Var(hours, domain=pyo.NonNegativeReals, bounds=(0, max_battery)) #Battery level


    total_cost = sum(m.buy[t]*price[t] - m.sell[t]*price[t] for t in hours)
    m.objective = pyo.Objective(expr=total_cost, sense=pyo.minimize)


    def electricity_balance(m,t):
        return solar[t] + m.buy[t] + m.discharge[t] == consumption[t] + m.charge[t] + m.sell[t]
    m.balance = pyo.Constraint(hours, rule=electricity_balance)


    def battery_rule(m, t):
        if t == 0:
            return m.soc[t] == (battery_level  
                                + m.charge[t] * battery_efficiency  
                                - m.discharge[t])
        else:
            return m.soc[t] == (m.soc[t-1]
                                + m.charge[t] * battery_efficiency 
                                - m.discharge[t])
    m.battery = pyo.Constraint(hours, rule=battery_rule)

    last_hour = len(price) - 1
    m.cycle = pyo.Constraint(expr=m.soc[last_hour] == battery_level)


    solver = pyo.SolverFactory("appsi_highs")
    solver.solve(m)
    return m

def print_cost(m):  
    print("Total cost (kr):", pyo.value(m.objective))


def print_table(m, price):
    print(f"{'Hour':>4} {'Buy (kr)':>10} {'Sell (kr)':>9} {'Charge (kWh)':>7} {'Discharge (kWh)':>7} {'Battery kWh':>7}")
    for t in range(len(price)):
        print(f"{t:>4} "
            f"{pyo.value(m.buy[t]):>7.2f} "
            f"{pyo.value(m.sell[t]):>7.2f} "
            f"{pyo.value(m.charge[t]):>10.2f} "
            f"{pyo.value(m.discharge[t]):>12.2f} "
            f"{pyo.value(m.soc[t]):>15.2f}")



def plot(m, price, t_start, t_end):
    timeframe = range(t_start, t_end)
    hours_x = list(timeframe)
    soc_values = [pyo.value(m.soc[t]) for t in timeframe]
    buy_values = [pyo.value(m.buy[t]) for t in timeframe]
    sell_values = [pyo.value(m.sell[t]) for t in timeframe]
    charge_values = [pyo.value(m.charge[t]) for t in timeframe]
    discharge_values = [pyo.value(m.discharge[t]) for t in timeframe]

    fig, (ax1, ax2) = plt.subplots(1,2, figsize=(12,5), gridspec_kw={'width_ratios': [2, 1]})
    ax1.plot(hours_x, soc_values, label="Battery level (kWh)")
    ax1.plot(hours_x, buy_values, label="kWh bought")
    ax1.plot(hours_x, sell_values, label="kWh sold")
    ax1.plot(hours_x, charge_values, label="kWh charged")
    ax1.plot(hours_x, discharge_values, label="kWh discharged")
    ax1.set_xlabel("Hour")
    ax1.set_ylabel("kWh")
    ax1.legend()


    ax2.plot(hours_x, price[t_start:t_end], label="kr/kwH")
    ax2.set_xlabel("Hour")
    ax2.set_ylabel("price (kr)")
    ax2.legend()

    plt.tight_layout()
    plt.savefig("result.png", dpi=150)
    return fig
    

if __name__ == "__main__":
    price, consumption, solar = get_data(datafile)
    m = build_model(price, consumption, solar)
    print_cost(m)
    print_table(m, price)
    plot(m, price, 0, 48)
    plt.show()



