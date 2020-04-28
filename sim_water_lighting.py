import numpy as np
import pandas as pd

# This sim_test currently only tests lighting

# Import all datasets
# Water consumption requirements of each plant
We_sheet = pd.read_excel("datasets/Water_Consumption.xlsx", index_col = None)
# Heat loss U values
U_sheet = pd.read_excel('datasets/virtual_grower_material_u_values.xlsx', index_col = None)
# Crop Lighting Requirements spreadsheet
Crop_Light = pd.read_excel('datasets/Crop_Light.xlsx', index_col = None)
# Ambient Lighting Spreadsheet, based upon Detroit Ambient Solar Data spreadsheet
Amb_sheet = pd.read_excel('datasets/Ambient_Light_Read.xlsx', index_col = None)
# Lighting Selection Data
Light_pick = pd.read_excel('datasets/Lighting_Read.xlsx', index_col = None)
# Detroit Ambient Solar Data Spreadsheet, to be used as a Representative Dataset for Leamington Ontario
Detroit = pd.read_excel('datasets/Hourly Profile of Detroit (2010).xlsx', index_col = None)

# Get representative solar profiles
solar_profs = {}
for i in range (1, 13):
    solar_profs[i] = pd.read_excel("datasets/RepresentativeSolarProfiles.xlsx", header=0, sheet_name="{}".format(i))

#Get crop data to provide rough info as to the needs of each plant
crop_data = pd.read_csv("datasets/Crop Data.csv", header=0, index_col="Plant")

# Get spreadsheets concerning GHG emissions for fuel type, grid power, and ON grid energy source respectively
GHG_data_fuel = pd.read_excel("datasets/emissions_factors.xlsx", header=0, sheet_name="Fuel")
GHG_data_grid = pd.read_excel("datasets/emissions_factors.xlsx", header=0, sheet_name="Grid Intensity By Province", index_col ='Province')
GHG_data_source = pd.read_excel("datasets/emissions_factors.xlsx", header=0, sheet_name="ON Grid Energy Source Intensity")

# Get Ontario TOU Pricing Per Kwh (general use)
TOU = pd.read_excel('datasets/Ontario TOU Pricing.xlsx', index_col = None)

# Get TOU Pricing Spreadsheets for more specific uses 
TOU_pricing = pd.read_excel("datasets/Ontario TOU Pricing.xlsx", header=0, sheet_name="Sheet1", index_col='Start Time')
TOU_pricing = TOU_pricing.sort_values(by=['Start Time'])

# Energy Storage Information
storage_sheet = pd.read_excel("datasets/EnergyStorage.xlsx", header=0, sheet_name="MAIN")

# Josh's lighting function
# Helper Functions
def water_price(area, plant_choice):
  """
  Inputs: surface area, plant_choice as a string specified in the dataset, sheet: We_sheet
  Outputs: max # of plants that can fit the greenhouse, water consumption range (L/ day), cost range ($/ day)
  """
  #Assume area of greenhouse (m^2), sheet is uploaded or mounted, plant_choice is a string input into function
  #This function returns the number of plants needed.

  #For Loop, go through column of Water Consumption and see if match is found to plant_choice
  #Save list index and use it to get spacing of plant. Then divide area by spacing to get approximate number.

  # Passing dataset to Josh's code setup
  sheet = We_sheet.copy()
  j = 0 #initialize
  for i in sheet['Plant Type']: #located index to check at this point of array
    if i == plant_choice:
      save = j #save the indice to get water value
      #print(save) Works
    j = j+1
    
  spacing = sheet['Spacing'][save]
  #print(spacing) works

  plant_num = np.int(area/spacing) #calculate number of plants in greenhouse
  
  min_water = sheet['Water Requirements Min'][save] #get minimum water requirement per plant
  max_water = sheet['Water Requirements Max'][save] #get maximum water requirement per plant
  cost_rate = sheet['Cost of Water'][save] #get price of water

  wmin_req = np.int(min_water*plant_num) #get minimum water requirement in L
  wmax_req = np.int(max_water*plant_num) # get maximum water requirement in L

  cost_min = np.around(plant_num* min_water * cost_rate, 3) #get minimum cost in $
  cost_max = np.around(plant_num* max_water * cost_rate, 3) #get maximum cost in $

  #print("Maximum Number of plants that can fit in the greenhouse:", plant_num)
  #print("Water range of", wmin_req, "L to", wmax_req, "L")
  #print("Cost range of $", cost_min, "to $", cost_max)
  return plant_num, cost_min, cost_max, wmin_req, wmax_req


def greenhouse_transmissivity(material_name):
  """
  This functions return the transmissivity of a material given the material name (as string)
  Inputs: U_sheet (global variable), material_name as string
  Assumptions: This function will only apply to windows
  """
  #here I approiximate the greenhouse materials transmissivity as one average transmissivity.
  #this function will need to be updated to incorporate multiple materials, right now it is stuck at just one
  j = 0 #initialize
  for i in U_sheet['Material']: #located index to check at this point of array
    if i == material_name:
      save = j #save the indice to get U_value, checked it works
    j = j+1
  Trans = U_sheet['Light Transmittance'][save]
  return Trans


def amb_light(Trans):
  """
  This functions returns an array of ambient light reaching plants.
  Inputs: transimissivity, Amb_sheet (global variable)
  Outputs: (1) An list of ambient light reaching plants (size of 12x24, 12 represents the month, 
            and 24 represents the hours in each representative day in a month), 
           (2) PPFD_max, max. photon requirements for plants 
           (3) PPFD_avg, avg. 
  """
  #create 1-D array of Ambinent light reaching plants in greenhouse accounting for transmissivity
  #rows, cols = (12, 24) 
  array = [] #going to make array of all PPFDs for hours of each month that reach greenhouse
  j = 0
  for i in range(len(Amb_sheet)):
    array.append(np.around(Amb_sheet['PPFD'][i] * Trans, 2)) #multiply by transmissivity, round to two decimal places
  PPFD_max = np.max(array)
  PPFD_avg = np.mean(array)
  return array, PPFD_max, PPFD_avg


def deficiency(array, plant_choice, photo):
  """
  Inputs: Crop_Light (data for Crop_Light), array (the array returned from amb_light_),
          plant_choice (user input string), photo (photoperiod in hours, from user input end-start)
  Outputs: crop_PPFDmin, crop_PPFDmax
  """
  j = 0
  for i in Crop_Light['Plant Type']:
    if i == plant_choice:
      save = j
    j = j+1
    #same algorithm as before

  photoperiod_min = Crop_Light['Photoperiod Min'][save] #get minimum photoperiod for plant
  photoperiod_max = Crop_Light['Photoperiod Max'][save] #get max recommended photoperiod for plant
  #print("It is recommended that",plant_choice, "have a photoperiod between", photoperiod_min, "h -", photoperiod_max, "h")
  #print("You have chosen a photoperiod of", photo, "h")

  #Get PPFD Requirements
  crop_PPFDmin = np.around(((Crop_Light['DLI - Min'][save])/photo/3600)*pow(10,6),2) #get minimum DLI requirement for plant
  crop_PPFDmax = np.around((Crop_Light['DLI - Max'][save]/photo/3600)*pow(10,6),2) #get maximum DLI recommended for plant
  
  #print("At this photoperiod:", plant_choice, "will require a minimum PPFD of", crop_PPFDmin, "Micromols/m^2/s")
  #print(plant_choice, "is not recommended to receive a PPFD higher than", crop_PPFDmax, "Micromols/m^2/s")
  
  #Deficiency is how far behind the ambient is from PPFD requirements of plants reaching greenhouse
  #defic = []
  #for i in range(len(array)):
  #  defic.append(crop_PPFDmin - array[i])
  #deficiency = np.around(np.max(defic),2)

  #It is assumed that the deficiency is the crop_PPFDmin, since the sun is not always up.

  return crop_PPFDmin, crop_PPFDmax

# Simulation Functions
def Light_Sel(crop_PPFDmin, crop_PPFDmax, photo, plant_num):
  """
  Input: Light_pick (data), crop_PPFDmin, crop_PPFDmax (returned from function deficiency),
         photo (end-start, from user input), plant_num (returned from water_price)
  Outputs: final_pick (the light choice), light_num (units/ per-all-plants of a chosen crop),
           upfront_cost (total purchase cost), hourly_consumption_kwh (kWh)
  """
  j = 0
  #for comparison, can light meet peak requirement?
  choices = [] #for lighting choices
  choices_ind = [] #for indices of lighting choices
  prices = [] #for cost of one fixture
  electric = [] #for electricity input
  inst_num = []

  for i in Light_pick['PPFD - Best']: #Using worst case scenario for PPFD, ie 32 degrees of light is absorbed, make selection of PPFD.
    installation_num = round(crop_PPFDmin/i)
    inst_num.append(installation_num)
    choices.append(i) #if PPFD meets crop peak PPFD needs, add it to choices.
    choices_ind.append(j) #add index too
    prices.append(Light_pick['Cost of One Fixture'][j])
    electric.append(Light_pick['Electrical Input'][j]) 
    j = j+1
  
  #Now I have an array full of PPFD and their corresponding indices and costs, select here for minimum cost

  #Recall that number of installations affects electrical input
  for i in range(len(electric)):
    electric[i] = electric[i] * inst_num[i]

  sel = electric.index(min(electric)) #get minimum value index
  key = choices_ind[sel] #take minimum value index from choices index list
  final_pick = Light_pick['Lamp Type'][key] + " " + Light_pick['Ballast'][key] + " " + Light_pick['Fixture Producer'][key] #add three strings together
  
  #Get upfront cost and lighting fixture numbers
  area_e = Light_pick['Area of Emittance'][0]
  light_num = int((plant_num)/area_e) #number of lights needed to radiate over each plant
  light_num = inst_num[key]*light_num #minimum number of lights needed to satisfy plant lighting requirements

  upfront_cost = light_num*(Light_pick['Cost of One Fixture'][key])
  
  #Get electricity consumption rate
  consumption = (Light_pick['Electrical Input'][key] * light_num) #Recall that this is hourly consumption for each light
  #consumption_kwh = np.around(consumption/3600000, 4)
  consumption_kwh = np.around(consumption/1000, 4)

  #print("For lowest overall electricity consumption, recommend", final_pick)
  #print("Upfront cost of $", upfront_cost, "and fixtures estimated are", light_num)
  #print("Total Hourly Electricity Consumption:", consumption, "J" , "or", consumption_kwh , "kWh")

  return final_pick, light_num, upfront_cost, consumption_kwh


def TOU_ON(start, end, consumption_kwh, photo):
  """
  Inputs: start and end time (user input), TOU (data), consumption_kwh (returned from Light_Sel), photo (end-start)
  Outputs: sum_year (May-Oct, summer cost $), win_year (Nov.-April, winter cost $),
           total_annualcost ($) , kwh_year (electricity consumption per year)
  """
  #inputs are start time, end time, Time of Use spreadsheet (not yet uploaded to Colab), and photoperiod.
  #Consumption is currently entered as kWh, and it is hourly
  #start time is time in morning when lights are turned on (min 1 h)
  #end time is time in night when lights are turned off (max 24 h)

  hours = [] #initialize list of hours
  costs_sum = [] #initialize list of summer rate costs
  costs_win = [] #initialize list of winter rate costs

  if abs((end - start))!= photo:
    #print("Photoperiod does not match input lighting start and end times")
    return None
  else:
    for i in range(len(TOU['Start Time'])):
      if start <= TOU['Start Time'][i] <= end: #Ensure that the indices chosen are within the photoperiod and operating hours
        hours.append(TOU['Start Time'][i]) #start time is the starting hours of the TOU fees, and since they are hourly, each indice is a start time for an hour of electricity.

        costs_sum.append(TOU['TOU Summer (May - Oct) Mid-Peak Rate (cents/kWh)'][i] * consumption_kwh) #checked to ensure rates matched hours
        costs_win.append(TOU['TOU Winter (Nov - Apr) Mid-Peak Rate (cents/kWh)'][i] * consumption_kwh) #each index is now in the unit of cents

    #Get total daily costs
    sum_day = sum(costs_sum)
    win_day = sum(costs_win)

    #Convert to total yearly costs (the list is in cents, so convert to dollars)
    sum_year = np.around((sum_day*183)*0.01,2)
    win_year = np.around((win_day*182)*0.01,2)
    total_annualcost = sum_year + win_year
    kwh_year = consumption_kwh * photo *365
    #print("Respective annual summer and winter costs will respectively be: $", sum_year,"and $", win_year, "and total annual cost will be $", total_annualcost, "and annual energy consumption is ", kwh_year, "(kWh)")
    return sum_year, win_year, total_annualcost, kwh_year


def Ambient_Switching(crop_PPFDmin, Trans, consumption):
  """
  Inputs: consumption (returned from Light_Sel)
  """
  #How much energy can you save if you switch off when ambient lighting is enough for plant needs?
  #Assume that when ambient is higher than max recommended PPFD, that the greenhouse is cloaked, allowing it to still rely on outside light.
  #Assume that peak solar always happens in the afternoons
  #Inputs are Detroit 2010 data for solar insolation, consumption in J, and transmissivity.
  
  count = 0
  for i in Detroit['PPFD (Micromoles/m^2/s)']:
    if (i*Trans) > (crop_PPFDmin):
      count = count + 1

  energy_savings = count *consumption
  #print("If lights are strageically shut off during highly sunny hours, then", energy_savings, "J will be saved")
  return energy_savings