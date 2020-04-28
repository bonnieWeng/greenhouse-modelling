import numpy as np
import pandas as pd
import math

# This script currently only consists of energy storage calculations

# Import all datasets
# Energy Storage Information
storage_sheet = pd.read_excel("datasets/EnergyStorage.xlsx", header=0, sheet_name="MAIN")


# Energy storage calculations
def storage_calc(storage_type, optimisation_type, power_capacity, energy_capacity, dummy_days):
    # Notes: took out days (dict of dfs) and storage_sheet as function inputs
    # Assume everything is calculated inside this function
    
    """
    Inputs: storage_type (user-input dropdown), optimisation_type (user-input dropdown),
            power_spec (user-input values), energy_spec (user-input values),
            dummy_days (dummy daily profiles to plot the result)
    Output: monthly electricity savings and monthly electricity peak (numpy arrays)
    
    Units for each variables to be calculated:
    e_capital_cost = # $/kWh
    specific_energy = # Wh/kg
    cost_per_kg = e_capital_cost * specific_energy/1000
    battery_mass = floor(budget/cost_per_kg)
    depth_of_discharge
    battery_energy = depth_of_discharge*energy
    """
    
    #inputs give storage type
    #NEED TO REPLACE THESE TO PULL FROM INPUT DF
    #storage_type = input_df.tail(1)['Energy Storage Choice'][0]
    #storage_goal = input_df.tail(1)['Energy Storage Goal'][0]
    #store_capacity = input_df.tail(1)['Energy Storage Capacity'][0]
    #store_energy = input_df.tail(1)['Energy Storage Energy'][0]
    
    # Pass in dummy days
    days = dummy_days.copy()
    
    # Assign storage index based on chosen storage type
    storage_index = storage_sheet.loc[storage_sheet['Technology']== storage_type].index[0]

    # Days of each month
    monthdays = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    
    # Retrieve from table: 
    store_efficiency = (storage_sheet['Efficiency L'][storage_index] +\
      storage_sheet['Efficiency U'][storage_index])/(2*100)
    store_depth = (storage_sheet['Depth of Discharge L'][storage_index] +\
      storage_sheet['Depth of Discharge U'][storage_index])/(2*100)
    store_cap_cost = (storage_sheet['Power Capital Cost L'][storage_index] +\
      storage_sheet['Power Capital Cost U'][storage_index])/2
    store_lifespan = (storage_sheet['Lifespan L'][storage_index]\
      + storage_sheet['Lifespan U'][storage_index])/2
    
    if (optimisation_type == 'cost'):
        monthly_savings = np.zeros(12)
        monthly_peaks = np.zeros(12)
        for key in days.keys():
            shaved_profile, storage_profile, daily_savings = flatten_cost(days[key]['Total Electricity (kW)'],
                                                                          power_capacity,
                                                                          energy_capacity*store_depth,
                                                                          store_efficiency,
                                                                          days[key]['Electricity Prices ($/kWh)'], 1)
            # Trouble shooting
            #print("1 Shaved profile: {}".format(shaved_profile))
            #print("2 Storage profile: {}".format(storage_profile))
            
            # Modification
            #shaved_profile = days[key]['Total Electricity (kW)'] - storage_profile

            # electricity profile
            days[key]['Final Electricity (kW)'] = shaved_profile
            days[key]['Storage Profile (kW)'] = storage_profile
            # monthdays is array with the lengths of the months 
            monthly_savings[key-1] = daily_savings*monthdays[key-1]
            monthly_peaks[key-1] = days[key]['Final Electricity (kW)'].max()
    
    elif (optimisation_type == 'profile'):
        monthly_savings = np.zeros(12)
        monthly_peaks = np.zeros(12)
        for key in days.keys():
            shaved_profile, storage_profile, daily_savings = flatten_profile(days[key]['Total Electricity (kW)'],
                                                                             power_capacity,
                                                                             energy_capacity*store_depth,
                                                                             store_efficiency,
                                                                             days[key]['Electricity Prices ($/kWh)'],
                                                                             1)
            # Modification
            #shaved_profile = days[key]['Total Electricity (kW)'] - storage_profile

            days[key]['Final Electricity (kW)'] = shaved_profile
            days[key]['Storage Profile (kW)'] = storage_profile
            monthly_savings[key-1] = daily_savings*monthdays[key-1]
            monthly_peaks[key-1] = days[key]['Final Electricity (kW)'].max()
    #FOR PLOTTING
    return monthly_savings, monthly_peaks, days


# Helper functions for energy storage calculations
def flatten_profile(profile, store_peak, store_energy, efficiency, prices, increment):
    """
    Function: creates a new load profile that deploys storage to flatten the initial profile
    inputs: 
        profile: electricity profile to be optimized (array of values, 24)
        store_peak (power rating of storage, should be same units as profile)
        store_energy (enrgy rating of storage, should be same units as profile over time)
        efficiency: round-trip efficiency of unit (0-1)
        prices: array of hourly prices (24
        increment: 

    returns: 
        shaved_profile: new overall load profile      
        battery_profile: electricity profile of storage unit (positive discharge, negative charge)                    
        daily_savings: single value of savings for the day, in units of prices
    """
    battery_profile = np.zeros(24)
    shaved_profile = profile.copy()
    tots = {}
    p = pd.DataFrame(columns =  ['Hour', 'Load (kW)'])
    for i in range(len(profile)):
        a_row = [i, profile[i]]
        row_df = pd.DataFrame([a_row],  columns =  ['Hour', 'Load (kW)'])
        p = pd.concat([row_df, p], ignore_index=True)
    
    order = create_order_flatten(p)
    #print(order)
    j=0
    k=1

    while j < 24: 
        hour = order[j]
        while j+k<24:
            charge_hour = order[-k]
            hour = order[j]
            #print(j, k)
            if feasible_charge(increment, hour, charge_hour, battery_profile, store_peak, store_energy, efficiency) and ((shaved_profile[hour]- shaved_profile[charge_hour])>1/efficiency):
                battery_profile[hour] += increment*efficiency
                battery_profile[charge_hour] -= increment
                
                shaved_profile[hour] -= increment*efficiency
                shaved_profile[charge_hour] += increment #CHARGING
                
                #Update the profile dictionary with shaving
                p['Load (kW)'][[p.loc[p['Hour'] == hour].index[0]]] -= increment*efficiency
                p['Load (kW)'][[p.loc[p['Hour'] == charge_hour].index[0]]] += increment #CHARGING
                
                order = create_order_flatten(p)
                j = 0  
                k = 1  
                #print("Dischaged at {}, charged at {}".format(hour, charge_hour))
            else:
                k +=1
        k = 0
        j += 1
    verify = battery_profile + shaved_profile 
    #if (profile-verify).sum() != 0:
        # print('Error')
    
    daily_saving = (np.asarray(battery_profile)*np.asarray(prices)).sum()
    #print(daily_saving)
    return shaved_profile, battery_profile, daily_saving


def flatten_cost(profile, store_peak, store_energy, efficiency, prices, increment):
  """
  Function: creates a new load profile that deploys storage minimize costs
    inputs: 
        profile: electricity profile to be optimized (array of values, 24)
        store_peak (power rating of storage, should be same units as profile)
        store_energy (enrgy rating of storage, should be same units as profile over time)
        efficiency: round-trip efficiency of unit (0-1)
        prices: array of hourly prices (24
        increment: 

    returns: 
        shaved_profile: new overall load profile      
        battery_profile: electricity profile of storage unit (positive discharge, negative charge)                    
        daily_savings: single value of savings for the day, in units of prices
  """
  #shaved_peak = np.zeros(24)
  battery_profile = np.zeros(24)
  #charged_peak = np.zeros(24)
  #shaved_energy = 0 
  shaved_profile = profile.copy()
  unique_vals = np.unique(prices)
  p = {}
  tots = {}
  for i in unique_vals:
    p[i] = pd.DataFrame(columns = ['Hour', 'Load (kW)'])
  for i in range(len(profile)):
    a_row = [i, profile[i]]
    row_df = pd.DataFrame([a_row],  columns =  ['Hour', 'Load (kW)'])
    p[prices[i]] = pd.concat([row_df, p[prices[i]]], ignore_index=True)
    tots[prices[i]] = p[prices[i]]['Load (kW)'].sum()


  order = create_order(p)
  #print(order)
  j=0
  k=1

  while j < 24: 
    hour = order[j]
    price = prices[order[j]]
    while j+k<24:
      charge_hour = order[-k]
      hour = order[j]
      price = prices[order[j]]
      if feasible_charge(increment, hour, charge_hour, battery_profile, store_peak, store_energy, efficiency) and (prices[hour]*efficiency>prices[charge_hour]):
        battery_profile[hour] += increment*efficiency
        battery_profile[charge_hour] -= increment

        #shaved_peak[hour] += increment
        #shaved_energy = shaved_peak.sum()
        shaved_profile[hour] -= increment*efficiency
        shaved_profile[charge_hour] += increment #CHARGING


        #Update the profile dictionary with shaving
        p[price]['Load (kW)'][[p[price].loc[p[price]['Hour'] == hour].index[0]]] -= increment*efficiency
        p[prices[charge_hour]]['Load (kW)'][[p[prices[charge_hour]].loc[p[prices[charge_hour]]['Hour']\
          == charge_hour].index[0]]] += increment #CHARGING
        
        order = create_order(p)
        j = 0  
        k = 1  
        #print("Dischaged at {}, charged at {}".format(hour, charge_hour))
      else:
        k +=1
    k = 0
    j += 1

  verify = battery_profile + shaved_profile 
  #if (profile-verify).sum() != 0:
    # print('Error')

  daily_saving = (np.asarray(battery_profile)*np.asarray(prices)).sum()
  #print(daily_saving)
  return shaved_profile, battery_profile, daily_saving

def feasible_charge(increment, discharge_hour, charge_hour, current_battery_profile, battery_peak, battery_energy, efficiency):
  #function to evaluate whether a certain charge/discharge hour pairing is feasible,
  #given the limitations of the storage unit and the current storage profile
  #returns True if feasible, False if infeasible
  battery_profile = current_battery_profile.copy()
  battery_profile[discharge_hour] += increment*efficiency
  battery_profile[charge_hour] -= increment

  battery_progress = np.zeros(24)
  battery_progress[0] = battery_profile[0]

  for i in range(1,24):
    battery_progress[i] = battery_progress[i-1]+battery_profile[i]
  #print(battery_progress)
  if (abs(battery_profile[discharge_hour]) > battery_peak) or (abs(battery_profile[charge_hour])>battery_peak) or (battery_progress.max()-battery_progress.min())>battery_energy:
    return False
  return True
  
def energies(profile):
  #NOT USED IN SIMULATION
  #Function takes in a profile, and returns an array of same length where each 
  #entry of the array corresponds to the energy of the current charge/discharge period.
  zeros = []
  energies = np.zeros(24)
  if (profile[23]*profile[0])<=0:
    zeros.append(0)
  for i in range(23):
    if (profile[i]*profile[i+1])<=0:
      zeros.append(i+1)


  #print("Zeros are:", zeros)
  for i in range(1, len(zeros)):
    #print(i)
    energies[zeros[i-1]:zeros[i]] = profile[zeros[i-1]:zeros[i]].sum()
  energies[:zeros[0]] = profile[:zeros[0]].sum() + profile[zeros[len(zeros)-1]:].sum()
  energies[zeros[len(zeros)-1]:] = profile[:zeros[0]].sum() + profile[zeros[len(zeros)-1]:].sum()
  return energies

def create_order(p):
  #Function to create the order of priority for charging/discharging hours to reduce cost
  #input is a dictionary, where keys are the int prices values possible for the profile,
  #and each key gives a data frame of hours (and loads) that have that price
  #outputs an array sorting the hours 0-23 in terms of favourability based on 
  #price first, then load
  d = p.copy()
  key_array =list(d.keys())
  order = []
  sort_prices = np.sort(key_array)[::-1]
  for i in sort_prices:
    df = d[i].sort_values(by=['Load (kW)'])
    sorted_hours = df['Hour'][::-1]
    order = np.concatenate((order, np.asarray(sorted_hours)),axis=0)
  return order

def create_order_flatten(profile_df):
  #function to create order of priority for charging/discharging to flatten profile
  #input is a profile array
  #output is an order of hours (0-23)
  order_df = profile_df.sort_values(by = ['Load (kW)'])

  order = np.asarray(order_df['Hour'])
  order = order[::-1]
  return order