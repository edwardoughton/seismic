"""
Run script

"""
import os
import configparser
import glob
import numpy as np
import pandas as pd
from tqdm import tqdm


CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

DATA_RAW = os.path.join(BASE_PATH, 'raw')
DATA_INTERMEDIATE = os.path.join(BASE_PATH, 'intermediate')
RESULTS = os.path.join(BASE_PATH, '..', 'results')


def run_country(country):
    """

    """
    iso3 = country['iso3']


    folder_out = os.path.join(RESULTS, iso3)
    if not os.path.exists(folder_out):
        os.makedirs(folder_out)

    path_out = os.path.join(RESULTS, iso3, 'results.csv')

    # if not os.path.exists(path_out):
    #     os.makedirs(path_out)

    path = os.path.join(DATA_INTERMEDIATE, iso3, 'settlements', 'settlement_data.csv')
    settlements = pd.read_csv(path)[:5]

    output = []

    for idx, settlement in settlements.iterrows():

        phones = estimate_phone_adoption(settlement['population'])

        smartphones = estimate_smartphone_adoption(phones)

        active_users = estimate_active_smarthpone_users(smartphones)

        data_consumption = estimate_data_consumption(active_users)

        electricity_consumption = estimate_electricity_consumption(data_consumption)

        emissions = estimate_emissions(electricity_consumption)

        output.append({
            'GID_0': settlement['GID_0'],
            'GID_level': settlement['GID_level'],
            'population': settlement['population'],
            'type': settlement['type'],
            'lon': settlements['lon'],
            'lat': settlements['lat'],
            'on_grid': settlements['on_grid'],
            'phones': phones,
            'smartphones': smartphones,
            'active_users': active_users,
            'data_consumption_GB': data_consumption,
            'electricity_consumption_kWh': electricity_consumption,
            'carbon_kgs': emissions['carbon_kgs'],
            'nitrogen_oxides_kgs': emissions['nitrogen_oxides_kgs'],
            'sulpher_oxides_kgs': emissions['sulpher_oxides_kgs'],
            'pm10_kgs': emissions['pm10_kgs'],
        })

    output = pd.DataFrame(output)
    output.to_csv(path_out, index=False)

    return


def estimate_phone_adoption(population):
    """
    Estimate total phone users for this settlement.

    """
    phone_adoption_rate = 0.7

    phones = population * phone_adoption_rate

    return phones

def estimate_smartphone_adoption(phones):
    """
    Estimate total smartphone users for this settlement.

    """
    smartphone_adoption_rate = 0.5

    smartphones = phones * smartphone_adoption_rate

    return smartphones


def estimate_active_smarthpone_users(smartphones):
    """
    Estimate active smartphone users for this settlement.

    """
    active_user_rate = 0.1

    active_users = smartphones * active_user_rate

    return active_users


def estimate_data_consumption(active_users):
    """
    Estimate annual data consumption for this settlement.

    """
    months = 12
    monthly_data_consumption = 12

    data_consumption = active_users * monthly_data_consumption * months

    return data_consumption


def estimate_electricity_consumption(data_consumption):
    """
    Estimate annual electricity consumption for this settlement.

    """
    kWh_per_GB = 0.25

    electricity_consumption = data_consumption * kWh_per_GB

    return electricity_consumption


def estimate_emissions(electricity_consumption):
    """
    Estimate emissions released from energy consumption.

    """
    carbon_per_kWh = 0.5 #kgs of carbon per kWh
    nitrogen_oxide_per_kWh = 0.00009#kgs of nitrogen oxide (NOx) per kWh
    sulpher_dioxide_per_kWh = 0.007 #kgs of sulpher dioxide (SO2) per kWh
    pm10_per_kWh = 0.002 #kgs of PM10 per kWh

    output = {}

    output['carbon_kgs'] = electricity_consumption * carbon_per_kWh
    output['nitrogen_oxides_kgs'] = electricity_consumption * nitrogen_oxide_per_kWh
    output['sulpher_oxides_kgs'] = electricity_consumption * sulpher_dioxide_per_kWh
    output['pm10_kgs'] = electricity_consumption * pm10_per_kWh

    return output


if __name__ == '__main__':

    # countries = find_country_list(['Africa'])

    countries = [
        {'iso3': 'PER', 'iso2': 'PE', 'regional_level': 2, #'regional_nodes_level': 3,
            'region': 'SSA', 'pop_density_km2': 25, 'settlement_size': 500,
            'subs_growth': 3.5, 'smartphone_growth': 5, 'cluster': 'C1', 'coverage_4G': 16
        },
        # {'iso3': 'IDN', 'iso2': 'ID', 'regional_level': 2, #'regional_nodes_level': 3,
        #     'region': 'SEA', 'pop_density_km2': 100, 'settlement_size': 100,
        #     'subs_growth': 3.5, 'smartphone_growth': 5, 'cluster': 'C1', 'coverage_4G': 16
        # },
    ]

    for country in countries:

        print('Working on {}'.format(country['iso3']))

        run_country(country)
