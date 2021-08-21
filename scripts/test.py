"""
Exporatory script for seismic.

Written by Edward Oughton

August 2021

"""
import os
import sys
import configparser
import csv

import math
# import fiona
from shapely.geometry import shape, Point, LineString
import numpy as np
# from random import choice
# from rtree import index
import pandas as pd
import geopandas as gpd
import random
from itertools import tee

from collections import OrderedDict

from seismic.generate_hex import produce_sites_and_site_areas
# from seismic.system_simulator import SimulationManager
from params import (PARAMETERS, SPECTRUM_PORTFOLIO, ANT_TYPES, MODULATION_AND_CODING_LUT,
    CONFIDENCE_INTERVALS, SITE_RADII, ENVIRONMENTS
)

np.random.seed(42)

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']
DATA_RAW = os.path.join(BASE_PATH, 'raw')
DATA_INTERMEDIATE = os.path.join(BASE_PATH, 'intermediate')


def load_hourly_demand(path):
    """
    Load the hourly demand distribution.

    """
    output = {}

    data = pd.read_csv(path)

    for idx, item in data.iterrows():

        hour = int(item['hour'])

        output[hour] = item['percentage_share']

    return output


def generate_receivers(site_area, quantity):
    """

    Generate receiver locations as points within the site area.

    Sampling points can either be generated on a grid (grid=1)
    or more efficiently between the transmitter and the edge
    of the site (grid=0) area.

    Parameters
    ----------
    site_area : pandas df
        Shape of the site area we want to generate receivers within.

    Output
    ------
    receivers : List of dicts
        Contains the quantity of desired receivers within the area boundary.

    """
    receivers = []

    site_area['geometry'] = site_area['geometry'].to_crs('epsg:3857')

    geom = shape(site_area['geometry'][0])
    geom_box = geom.bounds

    minx = geom_box[0]
    miny = geom_box[1]
    maxx = geom_box[2]
    maxy = geom_box[3]

    id_number = 0

    x_axis = np.linspace(
        minx, maxx, num=(
            int(math.sqrt(geom.area) / (math.sqrt(geom.area)/50))
            )
        )
    y_axis = np.linspace(
        miny, maxy, num=(
            int(math.sqrt(geom.area) / (math.sqrt(geom.area)/50))
            )
        )

    xv, yv = np.meshgrid(x_axis, y_axis, sparse=False, indexing='ij')

    for i in range(len(x_axis)):
        for j in range(len(y_axis)):
            receiver = Point((xv[i,j], yv[i,j]))
            indoor_outdoor_probability = np.random.rand(1,1)[0][0]
            if geom.contains(receiver):
                receivers.append({
                    'type': "Feature",
                    'geometry': {
                        "type": "Point",
                        "coordinates": [xv[i,j], yv[i,j]],
                    },
                    'properties': {
                        'ue_id': "id_{}".format(id_number),
                        # "misc_losses": parameters['rx_misc_losses'],
                        # "gain": parameters['rx_gain'],
                        # "losses": parameters['rx_losses'],
                        # "ue_height": float(parameters['rx_height']),
                        "indoor": (True if float(indoor_outdoor_probability) < \
                            float(0.5) else False),
                    }
                })
                id_number += 1

            else:
                pass

    return random.sample(receivers, quantity)


def allocate_receiver_properties(receivers, params, demand):
    """

    Generate receiver locations as points within the site area.

    Sampling points can either be generated on a grid (grid=1)
    or more efficiently between the transmitter and the edge
    of the site (grid=0) area.

    Parameters
    ----------
    site_area : polygon
        Shape of the site area we want to generate receivers within.
    params : dict
        Contains all necessary simulation parameters.

    Output
    ------
    receivers : List of dicts
        Contains the quantity of desired receivers within the area boundary.

    """
    output = []

    for receiver in receivers:
        output.append({
            'type': receiver['type'],
            'geometry': receiver['geometry'],
            'properties': {
                "ue_id": receiver['properties']['ue_id'],
                "misc_losses": params['rx_misc_losses'],
                "gain": params['rx_gain'],
                "losses": params['rx_losses'],
                "ue_height": params['rx_height'],
                "indoor": receiver['properties']['indoor'],
                'demand': demand,
            }
        })

    return output

def calculate_user_demand(params):
    """
    Calculate Mb/second from GB/month supplied by throughput scenario.

    E.g.
        2 GB per month
            * 1024 to find MB
            * 8 to covert bytes to bits
            * busy_hour_traffic = daily traffic taking place in the busy hour
            * 1/30 assuming 30 days per month
            * 1/3600 converting hours to seconds,
        = ~0.01 Mbps required per user

    """
    monthly_data_GB = params['monthly_data_GB']
    hourly_share = params['hourly_share']

    demand = monthly_data_GB * 1024 * 8 * (hourly_share / 100) / 30 / 3600

    if demand < 2:
        demand = 2

    return demand


def free_space(frequency, distance, ant_height, ue_height,
    seed_value, iterations):
    """
    Implements the Free Space path loss model.
    Parameters
    ----------
    frequency : int
        Carrier band (f) required in MHz.
    distance : int
        Distance (d) between transmitter and receiver (km).
    ant_height : int
        Transmitter antenna height (h1) (m, above ground).
    ue_height : int
        Receiver antenna height (h2) (m, above ground).
    sigma : int
        Variation in path loss (dB) which is 2.5dB for free space.
    Returns
    -------
    path_loss : float
        Path loss in decibels (dB)
    """
    #model requires frequency in MHz rather than GHz.
    frequency = frequency*1000
    #model requires distance in kilometers rather than meters.
    distance = distance/1000

    random_variation = generate_log_normal_dist_value(
        frequency, 1, 2.5, iterations, None
    )
    # print(random_variation)
    path_loss = (
        32.4 + 10*np.log10((((ant_height - ue_height)/1000)**2 + \
        distance**2)) + (20*np.log10(frequency) + random_variation)
    )

    return round(path_loss, 2)


def generate_log_normal_dist_value(frequency, mu, sigma, draws, seed_value):
    """
    Generates random values using a lognormal distribution,
    given a specific mean (mu) and standard deviation (sigma).
    https://stackoverflow.com/questions/51609299/python-np-lognormal-gives-infinite-
    results-for-big-average-and-st-dev
    The parameters mu and sigma in np.random.lognormal are not the mean
    and STD of the lognormal distribution. They are the mean and STD
    of the underlying normal distribution.
    Parameters
    ----------
    mu : int
        Mean of the desired distribution.
    sigma : int
        Standard deviation of the desired distribution.
    draws : int
        Number of required values.
    Returns
    -------
    random_variation : float
        Mean of the random variation over the specified itations.
    """
    if seed_value == None:
        pass
    else:
        frequency_seed_value = seed_value * frequency * 100

        np.random.seed(int(str(frequency_seed_value)[:2]))

    normal_std = np.sqrt(np.log10(1 + (sigma/mu)**2))
    normal_mean = np.log10(mu) - normal_std**2 / 2

    hs = np.random.lognormal(normal_mean, normal_std, draws)

    return round(np.mean(hs),2)


def calc_power(transmitter, receivers, interfering_tx, params,
    modulation_and_coding_lut):
    """
    Calculate the optimal (minimum) power level.

    """
    results = []

    tx_coords = shape(transmitter['geometry'].to_crs('epsg:3857')[0])
    receivers['geometry'] = receivers['geometry'].to_crs('epsg:3857')

    min_w = params['min_w']
    max_w = params['max_w']
    increment = params['increment']

    for tx_power in range(min_w, max_w + increment, increment):

        print('Working on power: {} watts'.format(tx_power))

        interim = []

        #calculate Equivalent Isotropically Radiated Power (EIRP)
        eirp = (
            float(tx_power) +
            float(params['tx_macro_gain']) -
            float(params['tx_macro_losses'])
        )

        for idx, receiver in receivers.iterrows():

            for i in range(0, 100):

                capacity_mbps = link_capacity(receiver, tx_coords, eirp, params,
                    modulation_and_coding_lut)

                interim.append(capacity_mbps)

        capacity = np.percentile(
                interim, 90
            )

        capacity_km2 = capacity / params['site_area_km2']

        # print(capacity_km2, params['demand_km2'], capacity_km2 // params['demand_km2'])

        if capacity_km2 == 0:
            continue

        capacity_demand_metric = capacity_km2 // params['demand_km2']

        if capacity_demand_metric >= 1: #>=1 is good, capacity meets demand
            results.append({
                'demand_km2': params['demand_km2'],
                'capacity_km2': capacity_km2,
                'capacity_demand_metric': capacity_demand_metric,
                'tx_power': tx_power,
            })

    if len(results) == 0:
        return max_w

    return min(results, key=lambda x:x['tx_power'])


def link_capacity(receiver, tx_coords, eirp, params, modulation_and_coding_lut):
    """
    Estimate the radio link capacity.

    """
    distance = tx_coords.distance(shape(receiver['geometry']))

    path_loss = free_space(0.8, distance, 30, 1.5, 1, 1)

    received_power = (eirp -
        path_loss -
        params['rx_misc_losses'] +
        params['rx_gain'] -
        params['rx_losses']
    )

    interference = estimate_interference(receiver, interfering_tx, eirp, params)

    k = 1.38e-23
    t = 290
    bandwidth_hz = params['bandwidth'] * 1e6
    noise = 10 * np.log10(k * t * 1000) + 1.5 + 10 * np.log10(bandwidth_hz)

    raw_received_power = 10**received_power
    raw_sum_of_interference = sum(interference) * (params['network_load']/100)
    raw_noise = 10**noise
    i_plus_n = (raw_sum_of_interference + raw_noise) #2.19E-63 #

    sinr = round(np.log10(
        raw_received_power / i_plus_n
        ), 2)

    spectral_efficiency = estimate_spectral_efficiency(
        sinr, '4G', modulation_and_coding_lut)

    capacity_mbps = (
        (bandwidth_hz * spectral_efficiency) / 1e6
    )

    return capacity_mbps


def estimate_interference(receiver, interfering_tx, eirp, params):
    """
    Calculate interference from other sites.

    closest_sites contains all sites, ranked based
    on distance, meaning we need to select sites 1-3 (as site 0
    is the actual site in use)

    Parameters
    ----------
    receiver : object
        Receiving User Equipment (UE) item.
    interfering_tx : pandas df
        Interfering transmitters.
    params : dict
        Simulation parameters.

    Returns
    -------
    interference : List
        Received interference power in decibels at the receiver.
    model : string
        Specifies which propagation model was used.
    ave_distance : float
        The average straight line distance in meters between the
        interfering transmitters and receiver.
    ave_pl : string
        The average path loss in decibels between the interfering
        transmitters and receiver.

    """
    interference = []

    for idx, tx_coords in interfering_tx.iterrows():

        distance = tx_coords['geometry'].distance(shape(receiver['geometry']))

        path_loss = free_space(params['frequency'], distance, 30, 1.5, 1, 1)

        received_interference = (eirp -
            path_loss -
            params['rx_misc_losses'] +
            params['rx_gain'] -
            params['rx_losses']
        )

        interference.append(received_interference)

    interference_list = []
    for value in interference:
        output_value = 10**value
        interference_list.append(output_value)

    interference_list.sort(reverse=True)
    interference_list = interference_list#[:3]

    return interference_list


def estimate_spectral_efficiency(sinr, generation,
    modulation_and_coding_lut):
    """
    Uses the SINR to determine spectral efficiency given the relevant
    modulation and coding scheme.

    Parameters
    ----------
    sinr : float
        Signal-to-Interference-plus-Noise-Ratio (SINR) in decibels.
    generation : string
        Either 4G or 5G dependent on technology.
    modulation_and_coding_lut : list of tuples
        A lookup table containing modulation and coding rates,
        spectral efficiencies and SINR estimates.

    Returns
    -------
    spectral_efficiency : float
        Efficiency of information transfer in Bps/Hz

    """
    lookup = modulation_and_coding_lut[generation]

    spectral_efficiency = 0.1
    for lower, upper in pairwise(lookup):
        if lower[0] and upper[0] == generation:

            lower_sinr = lower[6]
            upper_sinr = upper[6]

            if sinr >= lower_sinr and sinr < upper_sinr:
                spectral_efficiency = lower[5]
                return spectral_efficiency

            highest_value = lookup[-1]

            if sinr >= highest_value[6]:
                spectral_efficiency = highest_value[5]
                return spectral_efficiency

            lowest_value = lookup[0]

            if sinr < lowest_value[5]:
                spectral_efficiency = 0
                return spectral_efficiency


def pairwise(iterable):
    """
    Return iterable of 2-tuples in a sliding window.
    >>> list(pairwise([1,2,3,4]))
    [(1,2),(2,3),(3,4)]

    """
    a, b = tee(iterable)
    next(b, None)

    return zip(a, b)


if __name__ == '__main__':

    path = os.path.join(DATA_RAW, 'hourly_demand', 'hourly_demand.csv')
    hourly_demand = load_hourly_demand(path)

    # Naranjal
    # -8.156502, -74.835480
    # Shambo
    # -8.121020, -74.771790

    unprojected_point = {
        'type': 'Feature',
        'geometry': {
            'type': 'Point',
            'coordinates': (-74.835480, -8.156502),
            },
        'properties': {
            'site_id': 'Naranjal'
            }
        }

    unprojected_crs = 'epsg:4326'
    projected_crs = 'epsg:3857'

    folder = os.path.join(DATA_INTERMEDIATE, 'luts', 'shapes')
    if not os.path.exists(folder):
        os.makedirs(folder)

    # site_radii_generator = SITE_RADII['macro']
    # site_radii_generator['rural']

    site_radius = 10000
    num_population = 500

    transmitter, interfering_tx, site_area, int_site_areas = \
        produce_sites_and_site_areas(
            unprojected_point['geometry']['coordinates'],
            site_radius,
            unprojected_crs,
            projected_crs
            )

    site_area_km2 = shape(site_area[0]['geometry']).area / 1e6
    site_area = gpd.GeoDataFrame.from_features(site_area, crs='epsg:3857')
    site_area['geometry'] = site_area['geometry'].to_crs('epsg:4326')
    path = os.path.join(folder, 'site_area.shp')
    site_area.to_file(path, crs='epsg:4326')

    transmitter = gpd.GeoDataFrame.from_features(transmitter, crs='epsg:3857')
    transmitter['geometry'] = transmitter['geometry'].to_crs('epsg:4326')
    path = os.path.join(folder, 'transmitter.shp')
    transmitter.to_file(path, crs='epsg:4326')

    interfering_tx = gpd.GeoDataFrame.from_features(interfering_tx, crs='epsg:3857')
    interfering_tx['geometry'] = interfering_tx['geometry'].to_crs('epsg:4326')
    path = os.path.join(folder, 'interfering_tx.shp')
    interfering_tx.to_file(path, crs='epsg:4326')

    int_site_areas = gpd.GeoDataFrame.from_features(int_site_areas, crs='epsg:3857')
    int_site_areas['geometry'] = int_site_areas['geometry'].to_crs('epsg:4326')
    path = os.path.join(folder, 'int_site_areas.shp')
    int_site_areas.to_file(path, crs='epsg:4326')

    population = generate_receivers(site_area, num_population)
    population = gpd.GeoDataFrame.from_features(population, crs='epsg:3857')
    population['geometry'] = population['geometry'].to_crs(unprojected_crs)
    path = os.path.join(folder, 'population.shp')
    population.to_file(path, crs='epsg:4326')

    output = []

    for scenario, params in PARAMETERS.items():

        # if not scenario == 'managed_power':
        #     continue

        print('____Scenario____: {}'.format(scenario))

        params['site_area_km2'] = site_area_km2
        params['ant_type'] = 'macro'
        params['environment'] = 'rural'
        params['frequency'] = 0.8
        params['bandwidth'] = 10
        params['generation'] = '4G'
        params['transmission_type'] = '2x2'
        params['monthly_data_GB']  = 100

        for hour in range(0, 24): #range(0, 2):#

            print('--Working on hour: {}'.format(hour))

            hourly_share = hourly_demand[hour] / 100
            params['hourly_share'] = hourly_share

            demand = calculate_user_demand(params)

            num_active_receivers = int(math.ceil(num_population * hourly_share))
            active_receivers = population.sample(n=num_active_receivers)

            total_demand = demand * len(active_receivers)

            params['demand_km2'] = total_demand / site_area_km2

            optimal_watts = calc_power(transmitter, active_receivers,
                interfering_tx, params, MODULATION_AND_CODING_LUT)

            output.append({
                'scenario': scenario,
                'site_radius_km': round(site_radius / 1e3),
                'hour': hour,
                'hourly_share': params['hourly_share'],
                'per_user_capacity_mbps': demand,
                'active_users': len(active_receivers),
                'total_demand_mbps': total_demand,
                'demand_mbps_km2': params['demand_km2'],
                'capacity_mbps_km2': optimal_watts['capacity_km2'],
                'capacity_demand_metric': optimal_watts['capacity_demand_metric'],
                'optimal_watts': optimal_watts['tx_power'],
            })

    output = pd.DataFrame(output)
    folder = os.path.join(BASE_PATH, '..',  'results')
    path = os.path.join(folder, 'results.csv')
    output.to_csv(path, index=False)

    # #     results = gpd.GeoDataFrame.from_features(results, crs='epsg:4326')
    # #     path = os.path.join(folder, 'results.shp')
    # #     results.to_file(path, crs='epsg:4326')

    # # #     folder = os.path.join(DATA_INTERMEDIATE, 'luts', 'full_tables')
    # # #     filename = 'full_capacity_lut_{}_{}_{}_{}_{}_{}.csv'.format(
    # # #         environment, site_radius, generation, frequency, ant_type, transmission_type)

    # # #     write_full_results(results, environment, site_radius,
    # # #         frequency, bandwidth, generation, ant_type, transmission_type,
    # # #         folder, filename, PARAMETERS)

    # # #     percentile_site_results = obtain_percentile_values(
    # # #         results, transmission_type, PARAMETERS, CONFIDENCE_INTERVALS
    # # #     )

    # # #     results_directory = os.path.join(DATA_INTERMEDIATE, 'luts')
    # # #     write_frequency_lookup_table(percentile_site_results, environment,
    # # #         site_radius, frequency, bandwidth, generation,
    # # #         ant_type, transmission_type, results_directory,
    # # #         'capacity_lut_by_frequency.csv', PARAMETERS
    # # #     )
