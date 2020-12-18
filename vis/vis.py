"""
Visualize demand.

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

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), '..', 'scripts', 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

DATA_RAW = os.path.join(BASE_PATH, 'raw')
DATA_INTERMEDIATE = os.path.join(BASE_PATH, 'intermediate')
RESULTS = os.path.join(BASE_PATH, '..', 'results')
VIS = os.path.join(BASE_PATH, '..', 'vis', 'figures')

if not os.path.exists(VIS):
    os.makedirs(VIS)

def generate_settlement_plot(countries, categories, filename_out):
    """
    Generate a set of visualizing settlement distribution and size.

    """
    fig, axs = plt.subplots(2, figsize=(12, 12))

    for country in countries:

        iso3 = country[0]
        x = country[1]
        plot_title = country[2]
        regional_level = country[3]

        outline_path = os.path.join(DATA_INTERMEDIATE, iso3, 'national_outline.shp')
        country_outline = gpd.read_file(outline_path, crs='epsg:4326')

        filename = 'regions_{}_{}.shp'.format(regional_level, iso3)
        regions_path = os.path.join(DATA_INTERMEDIATE, iso3, 'regions', filename)
        regions = gpd.read_file(regions_path)
        regions.plot(facecolor="none", edgecolor='lightgrey', lw=1, ax=axs[x])

        data_path = os.path.join(RESULTS, iso3, 'results.csv')
        data = pd.read_csv(data_path)
        data = gpd.GeoDataFrame(data, geometry=gpd.points_from_xy(data.lon, data.lat), crs='epsg:4326')

        data.query(categories[0][0]).plot(color='black', markersize=10, ax=axs[x])
        data.query(categories[1][0]).plot(color='maroon', markersize=8, ax=axs[x])
        data.query(categories[2][0]).plot(color='red', markersize=6, ax=axs[x])
        data.query(categories[3][0]).plot(color='orangered', markersize=4, ax=axs[x])
        data.query(categories[4][0]).plot(color='lightpink', markersize=2, ax=axs[x])
        data.query(categories[5][0]).plot(color='white', markersize=1, ax=axs[x])

        axs[x].legend([
            categories[0][1],
            categories[1][1],
            categories[2][1],
            categories[3][1],
            categories[4][1],
            categories[5][1],
        ], prop={'size': 10})

        axs[x].set_title(plot_title)

        bbox = country_outline.bounds

        axs[x].set_xlim([bbox['minx'][0], bbox['maxx'][0]])
        axs[x].set_ylim([bbox['miny'][0], bbox['maxy'][0]])

        ctx.add_basemap(axs[x], crs=data.crs.to_string())

    fig.tight_layout()

    plt.savefig(os.path.join(VIS, filename_out))


if __name__ == '__main__':

    countries = [
        ('PER', 0, 'Peru - Settlement Sizes', 2),
        ('IDN', 1, 'Indonesia - Settlement Sizes', 2),
    ]

    categories = [
        ('20000 <= population', '>20k'),
        ('10000 <= population < 20000', '<20k'),
        ('5000 <= population < 10000', '<10k'),
        ('1000 <= population < 5000', '<5k'),
        ('500 <= population < 1000', '<1k'),
        ('0 <= population < 500', '<0.5k'),
    ]

    filename_out = 'settlements.png'

    generate_settlement_plot(countries, categories, filename_out)

    countries = [
        ('PER', 0, 'Peru - Phone Adoption', 2),
        ('IDN', 1, 'Indonesia - Phone Adoption', 2),
    ]

    categories = [
        ('0 <= phones < 500', '<0.5k'),
        ('500 <= phones < 1000', '<1k'),
        ('1000 <= phones < 5000', '<5k'),
        ('5000 <= phones < 10000', '<10k'),
        ('10000 <= phones < 20000', '<20k'),
        ('20000 <= phones', '>20k'),
    ]

    filename_out = 'phone_adoption.png'

    generate_settlement_plot(countries, categories, filename_out)

    countries = [
        ('PER', 0, 'Peru - Smartphone Adoption', 2),
        ('IDN', 1, 'Indonesia - Smartphone Adoption', 2),
    ]

    categories = [
        ('0 <= smartphones < 500', '<0.5k'),
        ('500 <= smartphones < 1000', '<1k'),
        ('1000 <= smartphones < 5000', '<5k'),
        ('5000 <= smartphones < 10000', '<10k'),
        ('10000 <= smartphones < 20000', '<20k'),
        ('20000 <= smartphones', '>20k'),
    ]

    filename_out = 'smartphone_adoption.png'

    generate_settlement_plot(countries, categories, filename_out)
