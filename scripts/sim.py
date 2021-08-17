"""
Runner for system_simulator.py

Written by Edward Oughton

Based on the pysim5G repository.

Adapted June 2021

"""
import os
import sys
import configparser
import csv

import math
import fiona
from shapely.geometry import shape, Point, LineString, mapping
import numpy as np
from random import choice
from rtree import index
import pandas as pd
import geopandas as gpd
import random

from collections import OrderedDict

from seismic.generate_hex import produce_sites_and_site_areas
from seismic.system_simulator import SimulationManager
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

        output[hour] = item['share']

    return output


def generate_receivers(site_area, quantity):
    """

    Generate receiver locations as points within the site area.

    Sampling points can either be generated on a grid (grid=1)
    or more efficiently between the transmitter and the edge
    of the site (grid=0) area.

    Parameters
    ----------
    site_area : polygon
        Shape of the site area we want to generate receivers within.

    Output
    ------
    receivers : List of dicts
        Contains the quantity of desired receivers within the area boundary.

    """
    receivers = []

    geom = shape(site_area[0]['geometry'])
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


def allocate_receiver_properties(receivers, param_values, demand):
    """

    Generate receiver locations as points within the site area.

    Sampling points can either be generated on a grid (grid=1)
    or more efficiently between the transmitter and the edge
    of the site (grid=0) area.

    Parameters
    ----------
    site_area : polygon
        Shape of the site area we want to generate receivers within.
    param_values : dict
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
                "misc_losses": param_values['rx_misc_losses'],
                "gain": param_values['rx_gain'],
                "losses": param_values['rx_losses'],
                "ue_height": param_values['rx_height'],
                "indoor": receiver['properties']['indoor'],
                'demand': demand,
            }
        })

    return output


# def obtain_percentile_values(results, transmission_type, parameters, confidence_intervals):
#     """

#     Get the threshold value for a metric based on a given percentiles.

#     Parameters
#     ----------
#     results : list of dicts
#         All data returned from the system simulation.

#     parameters : dict
#         Contains all necessary simulation parameters.

#     Output
#     ------
#     percentile_site_results : dict
#         Contains the percentile value for each site metric.

#     """
#     output = []

#     path_loss_values = []
#     received_power_values = []
#     interference_values = []
#     noise_values = []
#     sinr_values = []
#     spectral_efficiency_values = []
#     estimated_capacity_values = []
#     estimated_capacity_values_km2 = []

#     for result in results:

#         path_loss_values.append(result['path_loss'])

#         received_power_values.append(result['received_power'])

#         interference_values.append(result['interference'])

#         noise_values.append(result['noise'])

#         sinr = result['sinr']
#         if sinr == None:
#             sinr = 0
#         else:
#             sinr_values.append(sinr)

#         spectral_efficiency = result['spectral_efficiency']
#         if spectral_efficiency == None:
#             spectral_efficiency = 0
#         else:
#             spectral_efficiency_values.append(spectral_efficiency)

#         estimated_capacity = result['capacity_mbps']
#         if estimated_capacity == None:
#             estimated_capacity = 0
#         else:
#             estimated_capacity_values.append(estimated_capacity)

#         estimated_capacity_km2 = result['capacity_mbps_km2']
#         if estimated_capacity_km2 == None:
#             estimated_capacity_km2 = 0
#         else:
#             estimated_capacity_values_km2.append(estimated_capacity_km2)

#     for confidence_interval in confidence_intervals:

#         output.append({
#             'confidence_interval': confidence_interval,
#             'tranmission_type': transmission_type,
#             'path_loss': np.percentile(
#                 path_loss_values, confidence_interval #<- low path loss is better
#             ),
#             'received_power': np.percentile(
#                 received_power_values, 100 - confidence_interval
#             ),
#             'interference': np.percentile(
#                 interference_values, confidence_interval #<- low interference is better
#             ),
#             'noise': np.percentile(
#                 noise_values, confidence_interval #<- low interference is better
#             ),
#             'sinr': np.percentile(
#                 sinr_values, 100 - confidence_interval
#             ),
#             'spectral_efficiency': np.percentile(
#                 spectral_efficiency_values, 100 - confidence_interval
#             ),
#             'capacity_mbps': np.percentile(
#                 estimated_capacity_values, 100 - confidence_interval
#             ),
#             'capacity_mbps_km2': np.percentile(
#                 estimated_capacity_values_km2, 100 - confidence_interval
#             )
#         })

#     return output


# def obtain_threshold_values_choice(results, parameters):
#     """

#     Get the threshold capacity based on a given percentile.

#     Parameters
#     ----------
#     results : list of dicts
#         All data returned from the system simulation.
#     parameters : dict
#         Contains all necessary simulation parameters.

#     Output
#     ------
#     matching_result : float
#         Contains the chosen percentile value based on the input data.

#     """
#     sinr_values = []

#     percentile = parameters['percentile']

#     for result in results:

#         sinr = result['sinr']

#         if sinr == None:
#             pass
#         else:
#             sinr_values.append(sinr)

#     sinr = np.percentile(sinr_values, percentile, interpolation='nearest')

#     matching_result = []

#     for result in results:
#         if float(result['sinr']) == float(sinr):
#             matching_result.append(result)

#     return float(choice(matching_result))


# def convert_results_geojson(data):
#     """

#     Convert results to geojson format, for writing to shapefile.

#     Parameters
#     ----------
#     data : list of dicts
#         Contains all results ready to be written.

#     Outputs
#     -------
#     output : list of dicts
#         A list of geojson dictionaries ready for writing.

#     """
#     output = []

#     for datum in data:
#         output.append({
#             'type': 'Feature',
#             'geometry': {
#                 'type': 'Point',
#                 'coordinates': [
#                     datum['receiver_x'], datum['receiver_y']]
#                 },
#             'properties': {
#                 'path_loss': float(datum['path_loss']),
#                 'received_power': float(datum['received_power']),
#                 'interference': float(datum['interference']),
#                 'noise': float(datum['noise']),
#                 'sinr': float(datum['sinr']),
#                 'spectral_efficiency': float(
#                     datum['spectral_efficiency']
#                 ),
#                 'capacity_mbps': float(
#                     datum['capacity_mbps']
#                 ),
#                 'capacity_mbps_km2': float(
#                     datum['capacity_mbps_km2']
#                 ),
#                 },
#             }
#         )

#     return output


# def write_full_results(data, environment, site_radius, frequency,
#     bandwidth, generation, ant_type, transmittion_type, directory,
#     filename, parameters):
#     """

#     Write full results data to .csv.

#     Parameters
#     ----------
#     data : list of dicts
#         Contains all results ready to be written.
#     environment : string
#         Either urban, suburban or rural clutter type.
#     site_radius : int
#         Radius of site area in meters.
#     frequency : float
#         Spectral frequency of carrier band in GHz.
#     bandwidth : int
#         Channel bandwidth of carrier band in MHz.
#     generation : string
#         Either 4G or 5G depending on technology generation.
#     ant_type : string
#         The type of transmitter modelled (macro, micro etc.).
#     tranmission_type : string
#         The type of tranmission (SISO, MIMO 4x4, MIMO 8x8 etc.).
#     directory : string
#         Folder the data will be written to.
#     filename : string
#         Name of the .csv file.
#     parameters : dict
#         Contains all necessary simulation parameters.

#     """
#     sectors = parameters['sectorization']
#     inter_site_distance = site_radius * 2
#     site_area_km2 = (
#         math.sqrt(3) / 2 * inter_site_distance ** 2 / 1e6
#     )
#     sites_per_km2 = 1 / site_area_km2

#     if not os.path.exists(directory):
#         os.makedirs(directory)

#     full_path = os.path.join(directory, filename)

#     results_file = open(full_path, 'w', newline='')
#     results_writer = csv.writer(results_file)
#     results_writer.writerow(
#         (
#             'environment',
#             'inter_site_distance_m',
#             'sites_per_km2',
#             'frequency_GHz',
#             'bandwidth_MHz',
#             'number_of_sectors',
#             'generation',
#             'ant_type',
#             'transmittion_type',
#             'receiver_x',
#             'receiver_y',
#             'r_distance',
#             'path_loss_dB',
#             'r_model',
#             'received_power_dB',
#             'interference_dB',
#             'i_model',
#             'noise_dB',
#             'sinr_dB',
#             'spectral_efficiency_bps_hz',
#             'capacity_mbps',
#             'capacity_mbps_km2'
#         )
#     )

#     for row in data:
#         results_writer.writerow((
#             environment,
#             inter_site_distance,
#             sites_per_km2,
#             frequency,
#             bandwidth,
#             sectors,
#             generation,
#             ant_type,
#             transmittion_type,
#             row['receiver_x'],
#             row['receiver_y'],
#             row['distance'],
#             row['path_loss'],
#             row['r_model'],
#             row['received_power'],
#             row['interference'],
#             row['i_model'],
#             row['noise'],
#             row['sinr'],
#             row['spectral_efficiency'],
#             row['capacity_mbps'],
#             row['capacity_mbps_km2'],
#             ))


# def write_frequency_lookup_table(results, environment, site_radius,
#     frequency, bandwidth, generation, ant_type, tranmission_type,
#     directory, filename, parameters):
#     """

#     Write the main, comprehensive lookup table for all environments,
#     site radii, frequencies etc.

#     Parameters
#     ----------
#     results : list of dicts
#         Contains all results ready to be written.
#     environment : string
#         Either urban, suburban or rural clutter type.
#     site_radius : int
#         Radius of site area in meters.
#     frequency : float
#         Spectral frequency of carrier band in GHz.
#     bandwidth : int
#         Channel bandwidth of carrier band in MHz.
#     generation : string
#         Either 4G or 5G depending on technology generation.
#     ant_type : string
#         Type of transmitters modelled.
#     tranmission_type : string
#         The transmission type (SISO, MIMO etc.).
#     directory : string
#         Folder the data will be written to.
#     filename : string
#         Name of the .csv file.
#     parameters : dict
#         Contains all necessary simulation parameters.

#     """
#     inter_site_distance = site_radius * 2
#     site_area_km2 = math.sqrt(3) / 2 * inter_site_distance ** 2 / 1e6
#     sites_per_km2 = 1 / site_area_km2

#     sectors = parameters['sectorization']

#     if not os.path.exists(directory):
#         os.makedirs(directory)

#     directory = os.path.join(directory, filename)

#     if not os.path.exists(directory):
#         lut_file = open(directory, 'w', newline='')
#         lut_writer = csv.writer(lut_file)
#         lut_writer.writerow(
#             (
#                 'confidence_interval',
#                 'environment',
#                 'inter_site_distance_m',
#                 'site_area_km2',
#                 'sites_per_km2',
#                 'frequency_GHz',
#                 'bandwidth_MHz',
#                 'number_of_sectors',
#                 'generation',
#                 'ant_type',
#                 'transmission_type',
#                 'path_loss_dB',
#                 'received_power_dBm',
#                 'interference_dBm',
#                 'noise_dB',
#                 'sinr_dB',
#                 'spectral_efficiency_bps_hz',
#                 'capacity_mbps',
#                 'capacity_mbps_km2',
#             )
#         )
#     else:
#         lut_file = open(directory, 'a', newline='')
#         lut_writer = csv.writer(lut_file)

#     for result in results:
#         lut_writer.writerow(
#             (
#                 result['confidence_interval'],
#                 environment,
#                 inter_site_distance,
#                 site_area_km2,
#                 sites_per_km2,
#                 frequency,
#                 bandwidth,
#                 sectors,
#                 generation,
#                 ant_type,
#                 tranmission_type,
#                 result['path_loss'],
#                 result['received_power'],
#                 result['interference'],
#                 result['noise'],
#                 result['sinr'],
#                 result['spectral_efficiency'],
#                 result['capacity_mbps'],
#                 result['capacity_mbps_km2'] * sectors,
#             )
#         )

#     lut_file.close()


if __name__ == '__main__':

    path = os.path.join(DATA_RAW, 'hourly_demand', 'hourly_demand.csv')
    hourly_demand = load_hourly_demand(path)

    unprojected_point = {
        'type': 'Feature',
        'geometry': {
            'type': 'Point',
            'coordinates': (0, 0),
            },
        'properties': {
            'site_id': 'Radio Tower'
            }
        }

    unprojected_crs = 'epsg:4326'
    projected_crs = 'epsg:3857'

    folder = os.path.join(DATA_INTERMEDIATE, 'luts', 'shapes')
    if not os.path.exists(folder):
        os.makedirs(folder)

    site_radii_generator = SITE_RADII['macro']

    site_radii_generator['rural']

    transmitter, interfering_transmitters, site_area, int_site_areas = \
        produce_sites_and_site_areas(
            unprojected_point['geometry']['coordinates'],
            5000,
            unprojected_crs,
            projected_crs
            )

    for scenario, param_values in PARAMETERS.items():

        if not scenario == 'baseline':
            continue

        output = []

        quantity = 10

        receivers = generate_receivers(site_area, quantity)

        ant_type = 'macro'
        environment = 'rural'
        frequency = 0.8
        bandwidth = 20
        generation = '4G'
        transmission_type = '2x2'

        # for hour in range(0, 1):#range(0, 24):

        #     traffic_probability = hourly_demand[hour]
        #     demand = 10

        #     receivers = allocate_receiver_properties(receivers, param_values, demand)

        #     MANAGER = SimulationManager(
        #         transmitter, interfering_transmitters, ant_type,
        #         receivers, site_area, param_values
        #         )

        #     results = MANAGER.estimate_link_budget(
        #         frequency,
        #         bandwidth,
        #         generation,
        #         ant_type,
        #         transmission_type,
        #         environment,
        #         MODULATION_AND_CODING_LUT,
        #         param_values
        #         )

        # output = output + results



    #     results = gpd.GeoDataFrame.from_features(results, crs='epsg:4326')
    #     path = os.path.join(folder, 'results.shp')
    #     results.to_file(path, crs='epsg:4326')

    # #     folder = os.path.join(DATA_INTERMEDIATE, 'luts', 'full_tables')
    # #     filename = 'full_capacity_lut_{}_{}_{}_{}_{}_{}.csv'.format(
    # #         environment, site_radius, generation, frequency, ant_type, transmission_type)

    # #     write_full_results(results, environment, site_radius,
    # #         frequency, bandwidth, generation, ant_type, transmission_type,
    # #         folder, filename, PARAMETERS)

    # #     percentile_site_results = obtain_percentile_values(
    # #         results, transmission_type, PARAMETERS, CONFIDENCE_INTERVALS
    # #     )

    # #     results_directory = os.path.join(DATA_INTERMEDIATE, 'luts')
    # #     write_frequency_lookup_table(percentile_site_results, environment,
    # #         site_radius, frequency, bandwidth, generation,
    # #         ant_type, transmission_type, results_directory,
    # #         'capacity_lut_by_frequency.csv', PARAMETERS
    # #     )

    # transmitter = gpd.GeoDataFrame.from_features(transmitter, crs='epsg:4326')
    # path = os.path.join(folder, 'transmitter.shp')
    # transmitter.to_file(path, crs='epsg:4326')

    # interfering_transmitters = gpd.GeoDataFrame.from_features(interfering_transmitters, crs='epsg:4326')
    # path = os.path.join(folder, 'interfering_transmitters.shp')
    # interfering_transmitters.to_file(path, crs='epsg:4326')

    # site_area = gpd.GeoDataFrame.from_features(site_area, crs='epsg:4326')
    # path = os.path.join(folder, 'site_area.shp')
    # site_area.to_file(path, crs='epsg:4326')

    # int_site_areas = gpd.GeoDataFrame.from_features(int_site_areas, crs='epsg:4326')
    # path = os.path.join(folder, 'int_site_areas.shp')
    # int_site_areas.to_file(path, crs='epsg:4326')

    receivers = gpd.GeoDataFrame.from_features(receivers, crs='epsg:4326')
    path = os.path.join(folder, 'receivers.shp')
    receivers.to_file(path, crs='epsg:4326')
