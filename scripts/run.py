"""
Run script

"""
import os
import configparser
import glob
import numpy as np
import pandas as pd
from tqdm import tqdm
from random import random, uniform

from costs import calculate_electricity_cost
from emissions import estimate_emissions

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

DATA_RAW = os.path.join(BASE_PATH, 'raw')
DATA_INTERMEDIATE = os.path.join(BASE_PATH, 'intermediate')
RESULTS = os.path.join(BASE_PATH, '..', 'results')


def run_country(country, settlements, strategies, technology_lut, electricity_mix, energy_costs):
    """

    """
    iso3 = country['iso3']

    folder_out = os.path.join(RESULTS, iso3)
    if not os.path.exists(folder_out):
        os.makedirs(folder_out)

    path_out = os.path.join(RESULTS, iso3, 'results.csv')

    # if not os.path.exists(path_out):
    #     os.makedirs(path_out)

    total_unique_subscribers = get_total_unique_subscribers(country)

    output = []
    subscribers_to_allocate = total_unique_subscribers

    for idx, settlement in settlements.iterrows():

        phones = estimate_phone_adoption(settlement, subscribers_to_allocate)

        smartphones = estimate_smartphone_adoption(phones)

        active_users = estimate_active_smarthpone_users(smartphones)

        data_consumption = estimate_data_consumption(active_users)

        for strategy in strategies:

            electricity_consumption = estimate_electricity_consumption(data_consumption, strategy)

            cost = calculate_electricity_cost(electricity_consumption, strategy,
                electricity_mix, energy_costs)

            emissions = estimate_emissions(electricity_consumption, settlement['on_grid'],
                strategy, electricity_mix, technology_lut)

            output.append({
                'GID_0': settlement['GID_0'],
                'GID_level': settlement['GID_level'],
                'lon': settlement['lon'],#.values[0],
                'lat': settlement['lat'],#.values[0],
                'strategy': strategy,
                'on_grid': settlement['on_grid'],#.values[0],
                'type': settlement['type'],
                'population': settlement['population'],
                'phones': phones,
                'phones_perc': round(phones / settlement['population'] * 100),
                'smartphones': smartphones,
                'smartphones_perc': round(smartphones / settlement['population'] * 100),
                'active_users': active_users,
                'data_consumption_GB': data_consumption,
                'electricity_consumption_kWh': electricity_consumption,
                'cost_usd': cost,
                'carbon_kgs': emissions['carbon_kgs'],
                'nitrogen_oxides_kgs': emissions['nitrogen_oxides_kgs'],
                'sulpher_oxides_kgs': emissions['sulpher_oxides_kgs'],
                'pm10_kgs': emissions['pm10_kgs'],
            })

    output = pd.DataFrame(output)
    output.to_csv(path_out, index=False)

    return


def get_country_electricity_mix(country, electricity_mix):
    """
    Get the country electricity mix.

    """
    iso3 = country['iso3']

    return country_elec_mix


def get_total_unique_subscribers(country):
    """
    Estimate the total number of unique subscribers.

    """
    iso3 = country['iso3']

    path = os.path.join(DATA_RAW, 'gsma', 'gsma_unique_subscribers.csv')
    data = pd.read_csv(path, encoding='latin-1')
    data = data.to_dict('records')

    for item in data:
        if item['iso3'] == iso3:
            penetration = item['2020']

    path = os.path.join(DATA_INTERMEDIATE, iso3, 'regions', 'regional_data.csv')
    data = pd.read_csv(path)
    population = data['population'].sum()

    total_unique_subscribers = round(population * penetration)

    return total_unique_subscribers


def process_settlements(settlements):
    """

    """
    settlements = settlements.sort_values(by=['luminosity_mean'], ascending=False)

    bins = [0, 1, 10, 65]
    labels = ['Lower', 'Middle', 'Upper']

    settlements['adoption_tier'] = pd.cut(settlements['luminosity_mean'], bins,
        labels=labels, include_lowest =True)

    return settlements


def estimate_phone_adoption(settlement, subscribers_to_allocate):
    """
    Estimate total phone users for this settlement.

    Parameters
    ----------
    settlement : pandas series array
        Contains all information about the settlement being modeled.
    subscribers_to_allocate : int
        The number of subscribers to allocate.

    Returns
    -------
    phones : int
        The total number of estimated phones for the settlement.

    """
    population = settlement['population']
    adoption_tier = settlement['adoption_tier']

    if adoption_tier == 'Upper':
        phone_adoption_rate = 0.8
    elif adoption_tier == 'Middle':
        phone_adoption_rate = 0.4
    elif adoption_tier == 'Lower':
        phone_adoption_rate = 0.2
    else:
        print('Did not recognize adoption_tier')

    phones = round(population * phone_adoption_rate)

    return phones


def estimate_smartphone_adoption(phones):
    """
    Estimate total smartphone users for this settlement.

    Parameters
    ----------
    phones : int
        The total number of estimated phones for the settlement.

    Returns
    -------
    smartphones : int
        The total number of estimated smartphones for the settlement.

    """
    smartphone_adoption_rate = uniform(0.05, 0.6)

    smartphones = round(phones * smartphone_adoption_rate)

    return smartphones


def estimate_active_smarthpone_users(smartphones):
    """
    Estimate active smartphone users for this settlement.

    Parameters
    ----------
    smartphones : int
        The total number of estimated smartphones for the settlement.

    Returns
    -------
    active_users : int
        The total number of estimated active_users for the settlement.

    """
    active_user_rate = 0.1

    active_users = smartphones * active_user_rate

    return active_users


def estimate_data_consumption(active_users):
    """
    Estimate annual data consumption for this settlement.

    Parameters
    ----------
    active_users : int
        The total number of estimated active_users for the settlement.

    Returns
    -------
    data_consumption : int
        The quantity of annual data consumption estimated for the settlement.

    """
    months = 12
    monthly_data_consumption = 12

    data_consumption = round(active_users * monthly_data_consumption * months)

    return data_consumption


def estimate_electricity_consumption(data_consumption, strategy):
    """
    Estimate annual electricity consumption for this settlement.

    Parameters
    ----------
    data_consumption : int
        The quantity of annual data consumption estimated for the settlement.
    strategy : string
        The strategy being implemented.

    Returns
    -------
    electricity_consumption : int
        The quantity of electricity consumption estimated for the settlement.

    """
    kWh_per_GB = 0.25

    electricity_consumption = round(data_consumption * kWh_per_GB)

    return electricity_consumption


def load_electricity_mix(path):
    """

    """
    electricity_mix = pd.read_csv(path)
    unique_iso3_ids = electricity_mix['iso3'].unique()
    electricity_mix = electricity_mix.to_dict('records')

    output = {}

    for unique_iso3_id in unique_iso3_ids:
        for item in electricity_mix:
            if unique_iso3_id == item['iso3']:
                output[unique_iso3_id] = item

    return output


if __name__ == '__main__':

    technology_lut = {
        'oil': {
            'carbon_per_kWh': 0.5, #kgs of carbon per kWh
            'nitrogen_oxide_per_kWh':0.00009, #kgs of nitrogen oxide (NOx) per kWh
            'sulpher_dioxide_per_kWh': 0.007, #kgs of sulpher dioxide (SO2) per kWh
            'pm10_per_kWh': 0.002, #kgs of PM10 per kWh
        },
        'gas': {
            'carbon_per_kWh': 0.5, #kgs of carbon per kWh
            'nitrogen_oxide_per_kWh':0.00009, #kgs of nitrogen oxide (NOx) per kWh
            'sulpher_dioxide_per_kWh': 0.007, #kgs of sulpher dioxide (SO2) per kWh
            'pm10_per_kWh': 0.002, #kgs of PM10 per kWh
        },
        'coal': {
            'carbon_per_kWh': 1, #kgs of carbon per kWh
            'nitrogen_oxide_per_kWh':0.0001, #kgs of nitrogen oxide (NOx) per kWh
            'sulpher_dioxide_per_kWh': 0.01, #kgs of sulpher dioxide (SO2) per kWh
            'pm10_per_kWh': 0.01, #kgs of PM10 per kWh
        },
        'nuclear': {
            'carbon_per_kWh': 0.5, #kgs of carbon per kWh
            'nitrogen_oxide_per_kWh':0.00009, #kgs of nitrogen oxide (NOx) per kWh
            'sulpher_dioxide_per_kWh': 0.007, #kgs of sulpher dioxide (SO2) per kWh
            'pm10_per_kWh': 0.002, #kgs of PM10 per kWh
        },
        'hydro': {
            'carbon_per_kWh': 0.01, #kgs of carbon per kWh
            'nitrogen_oxide_per_kWh':0.0000009, #kgs of nitrogen oxide (NOx) per kWh
            'sulpher_dioxide_per_kWh': 0.00007, #kgs of sulpher dioxide (SO2) per kWh
            'pm10_per_kWh': 0.00002, #kgs of PM10 per kWh
        },
        'diesel': {
            'carbon_per_kWh': 0.5, #kgs of carbon per kWh
            'nitrogen_oxide_per_kWh':0.00009, #kgs of nitrogen oxide (NOx) per kWh
            'sulpher_dioxide_per_kWh': 0.007, #kgs of sulpher dioxide (SO2) per kWh
            'pm10_per_kWh': 0.002, #kgs of PM10 per kWh
        },
        'renewables': {
            'carbon_per_kWh': 0.1, #kgs of carbon per kWh
            'nitrogen_oxide_per_kWh':0.000001, #kgs of nitrogen oxide (NOx) per kWh
            'sulpher_dioxide_per_kWh': 0.0001, #kgs of sulpher dioxide (SO2) per kWh
            'pm10_per_kWh': 0.00001, #kgs of PM10 per kWh
        }
    }

    energy_costs = {
        'oil_usd_kwh': 0.1,
        'gas_usd_kwh': 0.1,
        'coal_usd_kwh': 0.1,
        'nuclear_usd_kwh': 0.1,
        'hydro_usd_kwh': 0.1,
        'renewables_usd_kwh': 0.1,
    }

    # countries = find_country_list(['Africa'])

    countries = [
        {'iso3': 'PER', 'iso2': 'PE', 'regional_level': 2, #'regional_nodes_level': 3,
            'region': 'SSA', 'pop_density_km2': 25, 'settlement_size': 500,
            'subs_growth': 3.5, 'smartphone_growth': 5, 'cluster': 'C1', 'coverage_4G': 16
        },
        {'iso3': 'IDN', 'iso2': 'ID', 'regional_level': 2, #'regional_nodes_level': 3,
            'region': 'SEA', 'pop_density_km2': 100, 'settlement_size': 100,
            'subs_growth': 3.5, 'smartphone_growth': 5, 'cluster': 'C1', 'coverage_4G': 16
        },
    ]

    strategies = [
        'baseline',
        'smart_diesel_generators',
        'solar'
    ]

    filename = 'electricity_mix.csv'
    path = os.path.join(DATA_RAW, 'bp_statistical_review', filename)

    global_electricity_mix = load_electricity_mix(path)

    for country in countries:

        print('Working on {}'.format(country['iso3']))

        filename = 'settlement_data.csv'
        path = os.path.join(DATA_INTERMEDIATE, country['iso3'], 'settlements', filename)
        settlements = pd.read_csv(path)#[:50]
        settlements = process_settlements(settlements)

        electricity_mix = global_electricity_mix[country['iso3']]

        run_country(country, settlements, strategies, technology_lut, electricity_mix, energy_costs)
