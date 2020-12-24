"""
Plot results.

Written by Ed Oughton

December 2020

"""
import os
import configparser
import numpy as np
import pandas as pd
import geopandas as gpd
import contextily as ctx
import matplotlib.pyplot as plt
import matplotlib.colors
from matplotlib import cm
import seaborn as sns

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), '..', 'scripts', 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

DATA_RAW = os.path.join(BASE_PATH, 'raw')
DATA_INTERMEDIATE = os.path.join(BASE_PATH, 'intermediate')
RESULTS = os.path.join(BASE_PATH, '..', 'results')
VIS = os.path.join(BASE_PATH, '..', 'vis', 'figures')

if not os.path.exists(VIS):
    os.makedirs(VIS)

def generate_plots(countries):
    """
    Generate a set of visualizing settlement distribution and size.

    """

    # all_data = []

    for country in countries:

        iso3 = country[0]

        data = pd.read_csv(os.path.join(RESULTS, iso3, 'results.csv'))#[:100]

        data['population_m'] = data['population'] / 1e6
        data['phones_m'] = data['phones'] / 1e6
        data['smartphones_m'] = data['smartphones'] / 1e6
        data['data_consumption_PB'] = data['data_consumption_GB'] / 1e6

        data = data.loc[data['strategy'] == 'baseline']

        # # data['settlement_type'] = pd.cut(
        # #     data['population'],
        # #     bins=[-np.inf, 500, 1000, 5000, 20000, np.inf],
        # #     labels=['<0.5k','<1k', '<5k', '<20k', '>20k']
        # # )

        demand = data[['on_grid', 'population_m', 'phones_m', 'smartphones_m',
            'data_consumption_PB', 'electricity_consumption_kWh',
            # 'carbon_kgs', 'nitrogen_oxides_kgs', 'sulpher_oxides_kgs', 'pm10_kgs'
            ]]

        demand.columns = ['on_grid', 'Population (Mn)', 'Phones (Mn)', 'Smartphones (Mn)',
            'Data Consumption (PB)', 'Mean Site Power Consumption (kWh)',
            # 'Carbon (kg)', 'Nitrogen Oxides (kg)', 'Sulpher Oxides (kg)', 'PM10 (kg)'
            ]

        # # fig, axs = plt.subplots(2, figsize=(12, 12))
        pairplot = sns.pairplot(demand, hue="on_grid")
        pairplot.savefig(os.path.join(VIS, 'pairplot_baseline_{}'.format(iso3)))


def generate_aggregate_plots(countries):
    """
    Generate a set of visualizing settlement distribution and size.

    """

    # all_data = []

    for country in countries:

        iso3 = country[0]

        data = pd.read_csv(os.path.join(RESULTS, iso3, 'aggregate_results.csv'))#[:100]

        data['strategy'] = data['strategy'].replace({
        'baseline': 'Baseline',
        'smart_diesel_generators': 'Smart Diesel',
        'smart_solar': 'Smart Solar',
        'pure_solar': 'Solar',
        })

        data['population_m'] = data['population'] / 1e6
        data['phones_m'] = data['phones'] / 1e6
        data['smartphones_m'] = data['smartphones'] / 1e6
        data['data_consumption_PB'] = data['data_consumption_GB'] / 1e6
        data['electricity_consumption_GWh'] = data['electricity_consumption_kWh'] / 1e6
        data['carbon_t'] = data['carbon_kgs'] / 1e3
        data['nitrogen_oxides_t'] = data['nitrogen_oxides_kgs'] / 1e3
        data['sulpher_oxides_t'] = data['sulpher_oxides_kgs'] / 1e3
        data['pm10_t'] = data['pm10_kgs'] / 1e3

        data = data[['strategy', 'population_m', 'phones_m', 'smartphones_m',
            'data_consumption_PB', 'electricity_consumption_GWh',
            'carbon_t', 'nitrogen_oxides_t', 'sulpher_oxides_t', 'pm10_t'
            ]]

        data.columns = ['Strategy', 'Population (Mn)', 'Phones (Mn)', 'Smartphones (Mn)',
            'Data Consumption (PB)', 'Power Consumption (GWh)',
            'Carbon (T)', 'Nitrogen Oxides (T)', 'Sulpher Oxides (T)', 'PM10 (T)'
            ]

        long_data = pd.melt(data,
            id_vars=['Strategy'],
            value_vars=['Population (Mn)', 'Phones (Mn)', 'Smartphones (Mn)',
            'Data Consumption (PB)', 'Power Consumption (GWh)',
            'Carbon (T)', 'Nitrogen Oxides (T)', 'Sulpher Oxides (T)', 'PM10 (T)'])

        long_data.columns = ['Strategy', 'Metric', 'Value']

        pairplot = sns.catplot(x="Strategy", y='Value', #hue="Frequency (GHz)",
            col="Metric", col_wrap=3, palette=sns.color_palette("husl", 6),
            kind="bar",
            data=long_data, sharex=False, sharey=False, orient='v',
            # facet_kws=dict(sharex=False, sharey=False),
            legend="full")

        plt.subplots_adjust(hspace=0.3, wspace=0.3, bottom=0.07)

        pairplot.savefig(os.path.join(VIS, 'boxplot_{}'.format(iso3)))


if __name__ == '__main__':

    countries = [
        ('PER', 0, 'Peru - Settlement Sizes', 2),
        ('IDN', 1, 'Indonesia - Settlement Sizes', 2),
    ]

    # generate_plots(countries)

    generate_aggregate_plots(countries)
