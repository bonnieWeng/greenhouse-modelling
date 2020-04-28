import numpy as np
import pandas as pd
import math

# import all datasets
crop_data = pd.read_csv("datasets/Crop Data.csv", header=0, index_col="Plant")

solar_profiles = {}
for i in range(1, 13):
  solar_profiles[i] = pd.read_excel("datasets/RepresentativeSolarProfiles.xlsx", header=0, sheet_name="{}".format(i))

ambient_conditions = {}
for i in range(1, 13):
  ambient_conditions[i] = pd.read_excel("datasets/AmbientConditions.xlsx", header=0, sheet_name="{}".format(i))


fuel_sheet = pd.read_csv("datasets/virtual_grower_fuel_energy_and_costs.csv", header=0)
material_sheet = pd.read_excel("datasets/virtual_grower_material_u_values.xlsx", header=0)
ival_sheet = pd.read_csv("datasets/virtual_grower_material_air_infiltration.csv", header=0)
TOU = pd.read_excel('datasets/Ontario TOU Pricing.xlsx', index_col = None)

air_density = 1.225 #kg/m3
specific_heat_capacity = 0.718 #kJ/kg
monthday = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

# Helper Functions
def FindU(wind_speed, material_name):
  #inputs are assumed to be datasheet of U_values (presumed uploaded or mounted)
  #wind_speed is integer or float
  #material_name must be a string exactly matching indice, presuming selected from UI
  
  # Material sheet
  U_sheet = material_sheet.copy()
  
  j = 0 #initialize
  for i in U_sheet['Material']: #located index to check at this point of array
    if i == material_name:
      save = j #save the indice to get U_value, checked it works
    j = j+1

  U_val = U_sheet['U-Value'][save]

  #If statements  below to recalibrate U_value, too ackward trying it via pandas
  if wind_speed < 15:
    U_val = U_val * 1
  if 15 <= wind_speed < 20:
    U_val = U_val *1.04
  if 20 <= wind_speed < 25:
    U_val = U_val * 1.08
  if 25 <= wind_speed <30:
    U_val = U_val * 1.12
  if wind_speed >= 30:
    U_val = U_val *1.16
  return U_val

'''
print(FindU(U_sheet, 25, 'Glass')) #seems to work without issue.
U_val = FindU(U_sheet, 25, 'Glass')
'''

#Conduction heat loss
def get_QCond(SA, U_val, T_change):
  #assume inputs are SA in m^2, U in J/hr*C*m^2, T_change in C

  QC = SA*U_val*T_change
  return QC
#get_QC(SA, U_val, T_change = 5)
#seems to work fine, I assume that T_change will require a funciton call of its own
#but that is out of our scope right now I believe.  

#Convection heat loss #BONNIELOOKHERE
def Findi(sheet, material, wind_speed):
  # Link datasheet
  sheet = ival_sheet.copy()

  i_val = sheet['Air Inflitration (J/(hr*C*m3))'][[sheet.loc[sheet['Material'] == material].index[0]]]

  if wind_speed < 15:
    i_val = i_val * 1
  if 15 <= wind_speed < 20:
    i_val = i_val *1.04
  if 20 <= wind_speed < 25:
    i_val = i_val * 1.08
  if 25 <= wind_speed <30:
    i_val = i_val * 1.12
  if wind_speed >= 30:
    i_val = i_val *1.16

  return i_val

def rad_heat(area, days):
  # Link datasheet
  solar_profile = solar_profiles.copy()

  #ASSUMES RADIATION VERTICAL
  for key in days.keys():
    days[key]['Ambient Radiation (W/m2)'] = solar_profile[key]['50th']*area
  return days

def conduction_loss(days, material, surface_area):
    for key in days.keys():
        days[key]['U_val'] = np.zeros(24)
        days[key]['Cond_loss (kWh)'] = np.zeros(24)
        for i in range(len(days[key])):
            days[key]['U_val'][i] = FindU(days[key]['Wind Speed (m/s)'][i], material)
            days[key]['Cond_loss (kWh)'][i] = (days[key]['U_val'][i] * (days[key]['Temperature (C)'][i] - days[key]['Ambient Temperature (C)'][i]) * surface_area)/3600/1000
    return days

def convection_loss(days, material, volume): 
  for key in days.keys():
    days[key]['inf_correction'] = np.zeros(24)
    days[key]['Conv_loss (kWh)'] = np.zeros(24)
    for i in range(len(days[key])):
      days[key]['inf_correction'][i] = Findi(ival_sheet, material, days[key]['Wind Speed (m/s)'][i])
      days[key]['Conv_loss (kWh)'][i] = (days[key]['inf_correction'][i] * (days[key]['Temperature (C)'][i] - days[key]['Ambient Temperature (C)'][i]) * volume)/3600/1000
  return days

def radiation_gain(days, factor, area):
  '''
  solar_profs is a dictionary with the solar radiation spreadsheet read in as data frames  
  this step is needed before the function: #days[key]['Ambient Radiation (W/m2)'] = solar_profs[key]['50th']
  days dictionary doesn't need anything except ambient radiation. this function uses ambient radiation to create rad_gain radiation gain
  '''
  for key in days.keys():
    days[key]['Rad_gain (kWh)'] = days[key]['Ambient Radiation (W/m2)']*factor*area/1000
  return days


def final_day_profile(crop_type, surface_area, volume, photo_start, photo_end, fuel_type, material, c_material, lighting_val, factor):
    # This where the days profile was created and to be returned
    day_night_array = np.zeros(24)
    day_night_array[photo_start:photo_end] +=1
    days = {}
    days_keys = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]

    feature_list = ['Temperature (C)']
    zero_data = np.zeros(shape=(24,len(feature_list)))

    #crop type is string input to select the right column in crop sheet
    tempn = crop_data[crop_type]['Optimal Temp Night']
    tempd = crop_data[crop_type]['Optimal Temp Day']

    temp_array = np.zeros(24)
    for i in range(24):
        if day_night_array[i]==0:
            temp_array[i] = tempn
        else: 
            temp_array[i] = tempd
    
    for key in days_keys:
        days[key] = pd.DataFrame(zero_data, columns = feature_list)
        days[key]['Temperature (C)'] = temp_array
        days[key]['Light Electricity (kWh)'] = day_night_array*lighting_val
    
    fuel_index = fuel_sheet.loc[fuel_sheet['Fuel Name']== fuel_type].index[0]
    fuel_efficiency = fuel_sheet['Efficiency'][fuel_index]
    fuel_kwh_unit = fuel_sheet['kWh/unit'][fuel_index]
    fuel_unit_cost = fuel_sheet['Estimated cost per unit'][fuel_index]

    #add ambient conditions to days dictionary data frames
    for key in days.keys():
        days[key]['Ambient Temperature (C)'] = ambient_conditions[key]['50thTemp']
        days[key]['Wind Speed (m/s)'] = ambient_conditions[key]['50thWind']*1000/3600
        days[key]['Ambient Radiation (W/m2)'] = solar_profiles[key]['50th']

    days = conduction_loss(days, material, surface_area) #add ['Cond_loss (kWh)']
    days = convection_loss(days, c_material, volume)
    days = radiation_gain(days, factor, surface_area)

    #3 FUNCTIONS ABOVE ADD cond_loss, conv_loss and rad_gain columns to dfs
    for key in days.keys(): #CAPTURE ALL HEAT LOSS AND HEATING ADJUSTMENT REQUIRED FOR INTERNAL TEMPERATURE
        days[key]['Total Heat Loss (kWh)'] = days[key]['Cond_loss (kWh)'] + days[key]['Conv_loss (kWh)'] - days[key]['Rad_gain (kWh)']
        days[key]['Heating Adjustment (kWh)'] = np.zeros(24)
        for i in range(23): #loop through all hours to see what the next hour temp change is
            days[key]['Heating Adjustment (kWh)'][i] = (days[key]['Temperature (C)'][i+1] - days[key]['Temperature (C)'][i])*volume*air_density*specific_heat_capacity/3600
        days[key]['Heating Adjustment (kWh)'][23] = (days[key]['Temperature (C)'][0] - days[key]['Temperature (C)'][23])*volume*air_density*specific_heat_capacity/3600 
        
        days[key]['Heating Needs (kWh)'] = days[key]['Heating Adjustment (kWh)']+days[key]['Total Heat Loss (kWh)']
        days[key]['Heating Needs (kWh)'] = (days[key]['Heating Needs (kWh)'] + days[key]['Heating Needs (kWh)'].abs())/2
    
        if key>4 and key<11:
            days[key]['Electricity Price (c/kWh)'] = TOU['TOU Summer (May - Oct) Mid-Peak Rate (cents/kWh)']
        else: 
            days[key]['Electricity Price (c/kWh)'] = TOU['TOU Winter (Nov - Apr) Mid-Peak Rate (cents/kWh)']
        days[key]['Light Electricity Cost ($)'] = days[key]['Light Electricity (kWh)']*days[key]['Electricity Price (c/kWh)']/100
    
        #Fuel energy factors in efficiency
        days[key]['Fuel Energy (kWh)'] = days[key]['Heating Needs (kWh)']/fuel_efficiency
        days[key]['Fuel Unit Consumption'] = days[key]['Fuel Energy (kWh)']/fuel_kwh_unit

    # Check for electricity
    if (fuel_type == 'Electricity'): #if electrical heating, add heating energy to final fuel needs
        for key in days.keys():
            days[key]['Total Electricity (kWh)'] = days[key]['Fuel Energy (kWh)'] + days[key]['Light Electricity (kWh)']
            days[key]['Fuel Cost ($)'] = days[key]['Fuel Energy (kWh)']*days[key]['Electricity Price (c/kWh)']/100
    #need to run storage on this to get Final Electricity
    else:
        for key in days.keys():
            days[key]['Total Electricity (kWh)'] =  days[key]['Light Electricity (kWh)']
            days[key]['Fuel Cost ($)'] = days[key]['Fuel Unit Consumption']*fuel_unit_cost
    
    # Emissions
    elec_index = fuel_sheet.loc[fuel_sheet['Fuel Name']== 'Electricity'].index[0]
    monthly_emissions = np.zeros(12)
    for key in days.keys():
        days[key]['Lighting Emissions (gCO2e)'] = days[key]['Light Electricity (kWh)']*fuel_sheet['Emissions (gCO2e/kJ)'][elec_index]*3600 #3600 converts from kJ to kWh
        days[key]['Fuel Emissions (gCO2e)'] = days[key]['Fuel Energy (kWh)']*fuel_sheet['Emissions (gCO2e/kJ)'][fuel_index]*3600
        days[key]['Total Emissions (gCO2e)'] = days[key]['Lighting Emissions (gCO2e)'] + days[key]['Fuel Emissions (gCO2e)']
        monthly_emissions[key-1] = days[key]['Total Emissions (gCO2e)'].sum()*monthday[key-1] #monthday is an array where each index returns the # of days in the month
    
    return days, monthly_emissions
