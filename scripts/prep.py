"""
Process settlement layer

"""
import os
import configparser
import json
import math
import glob
import numpy as np
import pandas as pd
import geopandas as gpd
import random
import pyproj
from shapely.geometry import Point, LineString, Polygon, MultiPolygon, shape, mapping, box
from shapely.ops import unary_union, transform, nearest_points
import rasterio
# import networkx as nx
# from rasterio.warp import calculate_default_transform, reproject, Resampling
from rasterio.mask import mask
from rasterstats import zonal_stats, gen_zonal_stats, point_query
# import unrasterize

random.seed(1)

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

DATA_RAW = os.path.join(BASE_PATH, 'raw')
DATA_INTERMEDIATE = os.path.join(BASE_PATH, 'intermediate')
DATA_PROCESSED = os.path.join(BASE_PATH, 'processed')


def find_country_list(continent_list):
    """
    This function produces country information by continent.

    Parameters
    ----------
    continent_list : list
        Contains the name of the desired continent, e.g. ['Africa']

    Returns
    -------
    countries : list of dicts
        Contains all desired country information for countries in
        the stated continent.

    """
    path = os.path.join(DATA_RAW, 'gadm36_levels_shp', 'gadm36_0.shp')
    countries = gpd.read_file(path)

    glob_info_path = os.path.join(DATA_RAW, 'global_information.csv')
    load_glob_info = pd.read_csv(glob_info_path, encoding = "ISO-8859-1")
    countries = countries.merge(load_glob_info, left_on='GID_0',
        right_on='ISO_3digit')

    subset = countries.loc[countries['continent'].isin(continent_list)]

    countries = []

    for index, country in subset.iterrows():

        if country['GID_0'] in ['LBY', 'ESH']:
            continue

        if country['GID_0'] in ['LBY', 'ESH'] :
            regional_level =  1
        else:
            regional_level = 2

        countries.append({
            'country_name': country['country'],
            'iso3': country['GID_0'],
            'iso2': country['ISO_2digit'],
            'regional_level': regional_level,
        })

    return countries


def process_country_shapes(country):
    """
    Creates a single national boundary for the desired country.

    Parameters
    ----------
    country : dict
        Contains all country ID information.

    """
    iso3 = country['iso3']

    path = os.path.join(DATA_INTERMEDIATE, iso3)

    if os.path.exists(os.path.join(path, 'national_outline.shp')):
        return

    print('Processing country boundary ready to export')

    if not os.path.exists(path):
        os.makedirs(path)

    shape_path = os.path.join(path, 'national_outline.shp')

    path = os.path.join(DATA_RAW, 'gadm36_levels_shp', 'gadm36_0.shp')
    countries = gpd.read_file(path)

    single_country = countries[countries.GID_0 == iso3]

    single_country['geometry'] = single_country.apply(
        exclude_small_shapes, axis=1)

    glob_info_path = os.path.join(DATA_RAW, 'global_information.csv')
    load_glob_info = pd.read_csv(glob_info_path, encoding = "ISO-8859-1")
    single_country = single_country.merge(
        load_glob_info,left_on='GID_0', right_on='ISO_3digit')

    single_country.to_file(shape_path, driver='ESRI Shapefile')

    return


def process_regions(country):
    """
    Function for processing the lowest desired subnational regions for the
    chosen country.

    Parameters
    ----------
    country : dict
        Contains all country ID information.

    """
    regions = []

    iso3 = country['iso3']
    level = country['regional_level']

    for regional_level in range(1, level + 1):

        filename = 'regions_{}_{}.shp'.format(regional_level, iso3)
        folder = os.path.join(DATA_INTERMEDIATE, iso3, 'regions')
        path_processed = os.path.join(folder, filename)

        if os.path.exists(path_processed):
            continue

        print('Processing regions ready to export')

        if not os.path.exists(folder):
            os.mkdir(folder)

        filename = 'gadm36_{}.shp'.format(regional_level)
        path_regions = os.path.join(DATA_RAW, 'gadm36_levels_shp', filename)
        regions = gpd.read_file(path_regions)

        regions = regions[regions.GID_0 == iso3]

        regions['geometry'] = regions.apply(exclude_small_shapes, axis=1)

        regions = regions[~regions.is_empty]

        try:
            regions.to_file(path_processed, driver='ESRI Shapefile')
        except:
            pass

    return


def process_settlement_layer(country):
    """
    Clip the settlement layer to the chosen country boundary and place in
    desired country folder.

    Parameters
    ----------
    country : dict
        Contains all country ID information.

    """
    iso3 = country['iso3']

    path_settlements = os.path.join(DATA_RAW,'settlement_layer',
        'ppp_2020_1km_Aggregated.tif')

    settlements = rasterio.open(path_settlements, 'r+')
    settlements.nodata = 0
    settlements.crs = {"init": "epsg:4326"}

    iso3 = country['iso3']
    path_country = os.path.join(DATA_INTERMEDIATE, iso3, 'national_outline.shp')

    if os.path.exists(path_country):
        country = gpd.read_file(path_country)
    else:
        print('Must generate national_outline.shp first' )

    path_country = os.path.join(DATA_INTERMEDIATE, iso3)
    shape_path = os.path.join(path_country, 'settlements.tif')

    if os.path.exists(shape_path):
        return

    print('Processing country population raster ready to export')

    geo = gpd.GeoDataFrame({'geometry': country['geometry']})

    coords = [json.loads(geo.to_json())['features'][0]['geometry']]

    out_img, out_transform = mask(settlements, coords, crop=True)

    out_meta = settlements.meta.copy()

    out_meta.update({"driver": "GTiff",
                    "height": out_img.shape[1],
                    "width": out_img.shape[2],
                    "transform": out_transform,
                    "crs": 'epsg:4326'})

    with rasterio.open(shape_path, "w", **out_meta) as dest:
            dest.write(out_img)

    return


def process_electricity_layer(country):
    """
    Clip the electricity distribution layer to the chosen country boundary
    and place in desired country folder.

    Parameters
    ----------
    country : dict
        Contains all country ID information.

    """
    iso3 = country['iso3']

    path_settlements = os.path.join(DATA_RAW,'arderne', 'targets.tif')

    settlements = rasterio.open(path_settlements, 'r+')
    settlements.nodata = 255
    settlements.crs = {"init": "epsg:4326"}

    iso3 = country['iso3']
    path_country = os.path.join(DATA_INTERMEDIATE, iso3, 'national_outline.shp')

    if os.path.exists(path_country):
        country = gpd.read_file(path_country)
    else:
        print('Must generate national_outline.shp first' )

    path_country = os.path.join(DATA_INTERMEDIATE, iso3)
    path_out = os.path.join(path_country, 'electricity_dist.tif')

    if os.path.exists(path_out):
        return

    print('Processing electricity layer raster layer ready to export')

    geo = gpd.GeoDataFrame({'geometry': country['geometry']})

    coords = [json.loads(geo.to_json())['features'][0]['geometry']]

    out_img, out_transform = mask(settlements, coords, crop=True)

    out_meta = settlements.meta.copy()

    out_meta.update({"driver": "GTiff",
                    "height": out_img.shape[1],
                    "width": out_img.shape[2],
                    "transform": out_transform,
                    "crs": 'epsg:4326'})

    with rasterio.open(path_out, "w", **out_meta) as dest:
            dest.write(out_img)

    return


def process_night_lights(country):
    """
    Clip the nightlights layer to the chosen country boundary and place in
    desired country folder.

    Parameters
    ----------
    country : string
        Three digit ISO country code.

    """
    iso3 = country['iso3']

    folder = os.path.join(DATA_INTERMEDIATE, iso3)
    path_output = os.path.join(folder,'night_lights.tif')

    if os.path.exists(path_output):
        return

    print('Working on processing of nightlight layer')

    path_country = os.path.join(folder, 'national_outline.shp')

    filename = 'F182013.v4c_web.stable_lights.avg_vis.tif'
    path_night_lights = os.path.join(DATA_RAW, 'nightlights', '2013', filename)

    country = gpd.read_file(path_country)

    bbox = country.envelope

    geo = gpd.GeoDataFrame()
    geo = gpd.GeoDataFrame({'geometry': bbox}, crs='epsg:4326')

    coords = [json.loads(geo.to_json())['features'][0]['geometry']]

    night_lights = rasterio.open(path_night_lights, "r+")
    night_lights.nodata = 0

    out_img, out_transform = mask(night_lights, coords, crop=True)

    out_meta = night_lights.meta.copy()

    out_meta.update({"driver": "GTiff",
                    "height": out_img.shape[1],
                    "width": out_img.shape[2],
                    "transform": out_transform,
                    "crs": 'epsg:4326'})

    with rasterio.open(path_output, "w", **out_meta) as dest:
            dest.write(out_img)

    return


def exclude_small_shapes(x):
    """
    Remove small multipolygon shapes.

    Parameters
    ---------
    x : polygon
        Feature to simplify.

    Returns
    -------
    MultiPolygon : MultiPolygon
        Shapely MultiPolygon geometry without tiny shapes.

    """
    # if its a single polygon, just return the polygon geometry
    if x.geometry.geom_type == 'Polygon':
        return x.geometry

    # if its a multipolygon, we start trying to simplify
    # and remove shapes if its too big.
    elif x.geometry.geom_type == 'MultiPolygon':

        area1 = 0.01
        area2 = 50

        # dont remove shapes if total area is already very small
        if x.geometry.area < area1:
            return x.geometry
        # remove bigger shapes if country is really big

        if x['GID_0'] in ['CHL','IDN']:
            threshold = 0.01
        elif x['GID_0'] in ['RUS','GRL','CAN','USA']:
            threshold = 0.01

        elif x.geometry.area > area2:
            threshold = 0.1
        else:
            threshold = 0.001

        # save remaining polygons as new multipolygon for
        # the specific country
        new_geom = []
        for y in x.geometry:
            if y.area > threshold:
                new_geom.append(y)

        return MultiPolygon(new_geom)


def get_regional_data(country):
    """
    Allocate regional coverage, estimated sites and backhaul.

    Parameters
    ----------
    country : string
        Three digit ISO country code.

    """
    iso3 = country['iso3']
    regional_level = country['regional_level']
    GID_level = 'GID_{}'.format(regional_level)

    path_output = os.path.join(DATA_INTERMEDIATE, iso3, 'regions', 'regional_data.csv')

    # if os.path.exists(path_output):
    #     return

    print('Getting regional data')

    filename = 'regions_{}_{}.shp'.format(regional_level, iso3)
    path_input = os.path.join(DATA_INTERMEDIATE, iso3, 'regions', filename)
    regions = gpd.read_file(path_input, crs='epsg:4326')#[:5]
    regions = regions.to_crs('epsg:3857') #need to be this crs for get_coverage

    coverage = get_regional_coverage(country, regions)
    coverage_lut = convert_coverage_to_lookup(country, coverage)

    path_night_lights = os.path.join(DATA_INTERMEDIATE, iso3, 'night_lights.tif')
    path_settlements = os.path.join(DATA_INTERMEDIATE, iso3, 'settlements.tif')

    regions = regions.to_crs('epsg:4326') #need to be this crs for population estimate

    results = []

    for index, region in regions.iterrows():

        area_km2 = get_area(region)

        with rasterio.open(path_night_lights) as src:

            affine = src.transform
            array = src.read(1)
            array[array <= 0] = 0

            luminosity_mean = zonal_stats(
                region['geometry'], array, stats=['mean'], affine=affine, nodata=-999)[0]

        with rasterio.open(path_settlements) as src:

            affine = src.transform
            array = src.read(1)
            array[array <= 0] = 0

            population_summation = zonal_stats(
                region['geometry'], array, stats=['sum'], affine=affine, nodata=-999)[0]

        results.append({
            'GID_0': region['GID_0'],
            'GID_level': region[GID_level],
            'population': population_summation['sum'],
            'area_km2': area_km2,
            'population_km2': population_summation['sum'] / area_km2,
            'luminosity_mean': luminosity_mean['mean'],
            'coverage_2G_percent': coverage_lut[region[GID_level]]['2G'],
            'coverage_3G_percent': coverage_lut[region[GID_level]]['3G'],
            'coverage_4G_percent': coverage_lut[region[GID_level]]['4G'],
            'coverage_5G_percent': coverage_lut[region[GID_level]]['5G'],
        })

    results = estimate_sites(country, results)

    results_df = pd.DataFrame(results)
    results_df.to_csv(path_output, index=False)

    return


def convert_coverage_to_lookup(country, coverage):
    """
    Takes a list of dicts and returns a dict for each access.

    """
    GID_level = 'GID_{}'.format(country['regional_level'])

    output = {}

    for item in coverage:
        output[item[GID_level]] = {
            '2G': item['2G'],
            '3G': item['3G'],
            '4G': item['4G'],
            '5G': item['5G']
        }

    return output


def get_regional_coverage(country, regions):
    """
    Get coverage by technology.

    Parameters
    ----------
    country : string
        Three digit ISO country code.

    """
    iso3 = country['iso3']
    iso2 = country['iso2']
    regional_level = country['regional_level']
    GID_level = 'GID_{}'.format(regional_level)

    filename = 'regional_coverage_lut.csv'
    folder = os.path.join(DATA_INTERMEDIATE, iso3, 'coverage')
    if not os.path.exists(folder):
        os.makedirs(folder)

    path_output = os.path.join(folder, filename)

    if os.path.exists(path_output):
        output = pd.read_csv(path_output)
        output = output.to_dict('records')
        return output

    technologies = ['2G', '3G', '4G', '5G']

    output = []

    for idx, region in regions.iterrows():

        interim = {}

        for tech in technologies:

            folder_nm = 'MCE_{}'.format(tech)
            folder = os.path.join(DATA_RAW, 'MCE 2020', 'Data_MCE', 'ByCountry', folder_nm)
            filename = 'MCE_{}{}_2020.tif'.format(iso2, tech)
            path_input = os.path.join(folder, filename)

            if os.path.exists(path_input):
                path_coverage = path_input
            else:
                folder_nm = 'OCI_{}'.format(tech)
                folder = os.path.join(DATA_RAW, 'MCE 2020', 'Data_OCI', 'ByCountry', folder_nm)
                filename = 'OCI_{}{}_2020.tif'.format(iso2, tech)
                path_input = os.path.join(folder, filename)

                if os.path.exists(path_input):
                    path_coverage = path_input
                else:
                    interim[tech] = 0
                    continue

            with rasterio.open(path_coverage) as src:
                affine = src.transform
                array = src.read(1)
                array[array <= 0] = 0
                array[array > 1] = 1

                results = zonal_stats(
                    region['geometry'],
                    array,
                    stats=['sum', 'count'],
                    affine=affine,
                    nodata=-999)[0]

                total = results['sum']

                if total is not None:
                    interim[tech] = round(total / results['count'] * 100, 1)
                else:
                    interim[tech] = 0

        output.append({
            GID_level: region[GID_level],
            '2G': interim['2G'],
            '3G': interim['3G'],
            '4G': interim['4G'],
            '5G': interim['5G']
            })

    output = pd.DataFrame(output)
    output.to_csv(path_output, index=False)

    output = output.to_dict('records')

    return output


def estimate_sites(country, data):
    """
    Estimate sites based on mobile population coverage (2G-4G).

    Parameters
    ----------
    country :

    data :

    """
    iso3 = country['iso3']

    output = []

    population = 0

    for region in data:
        if region['population'] == None:
            continue
        population += int(region['population'])

    path = os.path.join(DATA_RAW, 'wb_mobile_coverage', 'wb_population_coverage.csv')
    coverage = pd.read_csv(path)
    coverage = coverage.loc[coverage['Country ISO3'] == iso3]
    coverage = coverage['2016'].values[0]

    population_covered = population * (coverage / 100)

    path = os.path.join(DATA_RAW, 'real_site_data', 'tower_counts', 'tower_counts.csv')
    towers = pd.read_csv(path, encoding = "ISO-8859-1")
    towers = towers.loc[towers['ISO_3digit'] == iso3]
    towers = towers['count'].values[0]

    towers_per_pop = towers / population_covered

    data = sorted(data, key=lambda k: k['population_km2'], reverse=True)

    covered_pop_so_far = 0

    for region in data:

        if covered_pop_so_far < population_covered:
            sites_estimated_total = region['population'] * towers_per_pop
            sites_estimated_km2 = region['population_km2'] * towers_per_pop

        else:
            sites_estimated_total = 0
            sites_estimated_km2 = 0

        output.append({
            'GID_0': region['GID_0'],
            'GID_level': region['GID_level'],
            'population': region['population'],
            'area_km2': region['area_km2'],
            'population_km2': region['population_km2'],
            'luminosity_mean': region['luminosity_mean'],
            'coverage_2G_percent': region['coverage_2G_percent'],
            'coverage_3G_percent': region['coverage_3G_percent'],
            'coverage_4G_percent': region['coverage_4G_percent'],
            'coverage_5G_percent': region['coverage_5G_percent'],
            'sites_estimated_total': sites_estimated_total,
            'sites_estimated_km2': sites_estimated_km2,
            })

        if region['population'] == None:
            continue

        covered_pop_so_far += region['population']

    return output


def generate_settlement_layer(country):
    """
    Generate a lookup table of settlements.

    """
    iso3 = country['iso3']
    regional_level = country['regional_level']
    GID_level = 'GID_{}'.format(regional_level)

    folder = os.path.join(DATA_INTERMEDIATE, iso3, 'settlements')
    if not os.path.exists(folder):
        os.makedirs(folder)
    path_output = os.path.join(folder, 'settlements.shp')

    if os.path.exists(path_output):
        return

    print('Generating the settlement layer ready to export')

    filename = 'regions_{}_{}.shp'.format(regional_level, iso3)
    folder = os.path.join(DATA_INTERMEDIATE, iso3, 'regions')
    path = os.path.join(folder, filename)
    regions = gpd.read_file(path, crs="epsg:4326")#[:1]
    regions = regions.loc[regions.is_valid]

    path_settlements = os.path.join(DATA_INTERMEDIATE, iso3, 'settlements.tif')
    settlements = rasterio.open(path_settlements, 'r+')
    settlements.nodata = 0
    settlements.crs = {"init": "epsg:4326"}

    folder_tifs = os.path.join(DATA_INTERMEDIATE, iso3, 'settlements', 'tifs')
    if not os.path.exists(folder_tifs):
        os.makedirs(folder_tifs)

    for idx, region in regions.iterrows():

        path_output = os.path.join(folder_tifs, region[GID_level] + '.tif')

        if os.path.exists(path_output):
            continue

        bbox = region['geometry'].envelope

        geo = gpd.GeoDataFrame()
        geo = gpd.GeoDataFrame({'geometry': bbox}, index=[idx])
        coords = [json.loads(geo.to_json())['features'][0]['geometry']]

        out_img, out_transform = mask(settlements, coords, crop=True)

        out_meta = settlements.meta.copy()

        out_meta.update({"driver": "GTiff",
                        "height": out_img.shape[1],
                        "width": out_img.shape[2],
                        "transform": out_transform,
                        "crs": 'epsg:4326'})

        with rasterio.open(path_output, "w", **out_meta) as dest:
                dest.write(out_img)

    nodes = find_settlements(country, regions)
    nodes = gpd.GeoDataFrame.from_features(nodes, crs='epsg:4326')
    # nodes.to_file(os.path.join(DATA_INTERMEDIATE, iso3, 'settlements', 'test.shp'))

    bool_list = nodes.intersects(regions['geometry'].unary_union)
    nodes = pd.concat([nodes, bool_list], axis=1)
    nodes = nodes[nodes[0] == True].drop(columns=0)

    settlements = []

    for idx1, region in regions.iterrows():

        # if not region['GID_2'] == 'IDN.9.2_1':
        #     continue

        seen = set()
        for idx2, node in nodes.iterrows():
            if node['geometry'].intersects(region['geometry']):
                if node['sum'] > 0:
                    settlements.append({
                        'type': 'Feature',
                        'geometry': mapping(node['geometry']),
                        'properties': {
                            'node_id': node['id'],
                            'id': idx1,
                            'GID_0': region['GID_0'],
                            GID_level: region[GID_level],
                            'population': node['sum'],
                            'type': node['type'],
                        }
                    })
                    seen.add(region[GID_level])

    settlements = gpd.GeoDataFrame.from_features(
            [
                {
                    'geometry': item['geometry'],
                    'properties': {
                        'node_id': item['properties']['node_id'],
                        'id': item['properties']['id'],
                        'GID_0':item['properties']['GID_0'],
                        GID_level: item['properties'][GID_level],
                        'population': item['properties']['population'],
                        'type': item['properties']['type'],
                    }
                }
                for item in settlements
            ],
            crs='epsg:4326'
        )

    settlements['lon'] = round(settlements['geometry'].x, 5)
    settlements['lat'] = round(settlements['geometry'].y, 5)

    settlements['id'] = (settlements['lon'].astype(str) + ',' + settlements['lat'].astype(str))

    settlements = settlements.drop_duplicates(subset=['lon', 'lat'])

    folder = os.path.join(DATA_INTERMEDIATE, iso3, 'settlements')
    path_output = os.path.join(folder, 'settlements' + '.shp')
    settlements.to_file(path_output)

    return


def find_settlements(country, regions):
    """
    Find key settlements.

    """
    iso3 = country['iso3']
    regional_level = country['regional_level']
    GID_level = 'GID_{}'.format(regional_level)

    threshold = country['pop_density_km2']
    settlement_size = country['settlement_size']

    folder_tifs = os.path.join(DATA_INTERMEDIATE, iso3, 'settlements', 'tifs')

    interim = []

    for idx, region in regions.iterrows():

        # if not region['GID_2'] == 'IDN.9.2_1':
        #     continue

        path_raster = os.path.join(folder_tifs, region[GID_level] + '.tif')

        with rasterio.open(path_raster) as src: # convert raster to pandas geodataframe
            data = src.read()
            data[data < threshold] = 0
            data[data >= threshold] = 1
            polygons = rasterio.features.shapes(data, transform=src.transform)

            shapes_df = gpd.GeoDataFrame.from_features(
                [{'geometry': poly, 'properties':{'value':value}}
                    for poly, value in polygons if value > 0], crs='epsg:4326'
            )

        geojson_region = [
            {'geometry': region['geometry'],
            'properties': {GID_level: region[GID_level]}
            }]

        gpd_region = gpd.GeoDataFrame.from_features(
                [{'geometry': poly['geometry'],
                    'properties':{GID_level: poly['properties'][GID_level]}}
                    for poly in geojson_region
                ], crs='epsg:4326'
            )

        if len(shapes_df) == 0:
            continue

        poly_nodes = gpd.overlay(shapes_df, gpd_region, how='intersection')

        results = []

        for idx, node in poly_nodes.iterrows():
            pop = zonal_stats(node['geometry'], path_raster, stats=['sum'])
            if not pop[0]['sum'] == None and pop[0]['sum'] > settlement_size:
                results.append({
                    'geometry': node['geometry'],
                    'properties': {
                        '{}'.format(GID_level): node[GID_level],
                        'sum': pop[0]['sum']
                    },
                })

        poly_nodes = gpd.GeoDataFrame.from_features(
            [{
                'geometry': item['geometry'],
                'properties': {
                        '{}'.format(GID_level): item['properties'][GID_level],
                        'sum': item['properties']['sum'],
                    },
                }
                for item in results
            ],
            crs='epsg:4326'
        )
        # poly_nodes.to_file(os.path.join(DATA_INTERMEDIATE, iso3, 'settlements', 'test2.shp'))
        poly_nodes = poly_nodes.drop_duplicates()

        if len(poly_nodes) == 0:
            continue

        poly_nodes.loc[(poly_nodes['sum'] >= 20000), 'type'] = '>20k'
        poly_nodes.loc[(poly_nodes['sum'] <= 10000) | (poly_nodes['sum'] < 20000), 'type'] = '10-20k'
        poly_nodes.loc[(poly_nodes['sum'] <= 5000) | (poly_nodes['sum'] < 10000), 'type'] = '5-10k'
        poly_nodes.loc[(poly_nodes['sum'] <= 1000) | (poly_nodes['sum'] < 5000), 'type'] = '1-5k'
        poly_nodes.loc[(poly_nodes['sum'] <= 500) | (poly_nodes['sum'] < 1000), 'type'] = '0.5-1k'
        poly_nodes.loc[(poly_nodes['sum'] <= 500), 'type'] = '<0.5k'
        poly_nodes = poly_nodes.dropna()

        for idx, item in poly_nodes.iterrows():
            if item['sum'] > 0:
                geom = item['geometry'].centroid #return_highest_density_point(item, path_raster)
                x, y = list(geom.coords)[0]
                interim.append({
                        'geometry': geom,
                        'properties': {
                            'id': '{},{}'.format(x, y),
                            GID_level: region[GID_level],
                            'sum': item['sum'],
                            'type': item['type'],
                        },
                })

    return interim


# def return_highest_density_point(item, path_raster):
#     """
#     Return the most densly populated point in in the polygon.

#     """

#     with rasterio.open(path_raster) as src:
#         ds = src.read(1)
#         # print(ds)
#         row, col = np.unravel_index(np.argmax(ds, axis=None), ds.shape)
#         maxval = ds[row, col]
#         x, y = src.xy(row, col)
#         print(x, y, maxval)

#     return 0


def process_major_settlement_layer(country):
    """
    Extracts major settlements over 50,000 people. This value has been
    selected to match up with the approach taken within the OnSSET model.

    """
    iso3 = country['iso3']

    folder = os.path.join(DATA_INTERMEDIATE, iso3, 'settlements')
    if not os.path.exists(folder):
        os.makedirs(folder)
    path_output = os.path.join(folder, 'major_settlements.shp')

    # if os.path.exists(path_output):
    #     return

    print('Extracting major settlement layer ready to export')

    folder = os.path.join(DATA_INTERMEDIATE, iso3, 'settlements')
    path = os.path.join(folder, 'settlements.shp')
    settlements = gpd.read_file(path, crs='epsg:4326')

    major_settlements = settlements.loc[settlements['population'] >= 50000]

    major_settlements.to_file(path_output)

    return


def get_settlement_data(country):
    """
    Get settlement LUT.

    Parameters
    ----------
    country : string
        Three digit ISO country code.

    """
    iso3 = country['iso3']
    regional_level = country['regional_level']
    GID_level = 'GID_{}'.format(regional_level)

    path_output = os.path.join(DATA_INTERMEDIATE, iso3, 'settlements', 'settlement_data.csv')

    # if os.path.exists(path_output):
    #     return

    print('Getting settlement data')

    path_elec_dist = os.path.join(DATA_INTERMEDIATE, iso3, 'electricity_dist.tif')
    path_night_lights = os.path.join(DATA_INTERMEDIATE, iso3, 'night_lights.tif')

    filename = 'major_settlements.shp'
    path_input = os.path.join(DATA_INTERMEDIATE, iso3, 'settlements', filename)
    major_settlements = gpd.read_file(path_input, crs='epsg:4326')
    major_settlements = major_settlements.to_crs('epsg:3857')

    filename = 'settlements.shp'
    path_input = os.path.join(DATA_INTERMEDIATE, iso3, 'settlements', filename)
    settlements = gpd.read_file(path_input, crs='epsg:4326')#[:1]
    settlements = settlements.to_crs('epsg:3857') #need to be this crs for get_coverage

    coverage = get_settlement_coverage(country, settlements)
    coverage_lut = convert_coverage_to_settlement_lookup(coverage)

    results = []

    for index, settlement in settlements.iterrows():

        buffer = settlement['geometry'].buffer(5000)
        buffer = gpd.GeoDataFrame({'geometry': buffer}, index=[0], crs='epsg:3857')
        buffer = buffer.to_crs('epsg:4326')

        with rasterio.open(path_elec_dist) as src:

            affine = src.transform
            array = src.read(1)
            array[array <= 0] = 0

            query = zonal_stats(
                buffer['geometry'], array, stats=['sum'], affine=affine, nodata=-999)[0]

        if query['sum'] > 0:
            power_type = 'on_grid'
        else:
            value = random.random()
            if value > 0.5:
                tech = 'diesel'
            else:
                tech = 'solar'
            power_type = 'off_grid_{}'.format(tech)

        with rasterio.open(path_night_lights) as src:

            affine = src.transform
            array = src.read(1)
            array[array <= 0] = 0

            luminosity_mean = zonal_stats(
                buffer, array, stats=['mean', 'sum', 'max'], affine=affine, nodata=-999)[0]

        distance_km = find_distance_to_major_settlement(country, major_settlements, settlement)

        results.append({
            'GID_0': settlement['GID_0'],
            'GID_level': settlement[GID_level],
            'population': settlement['population'],
            'type': settlement['type'],
            'lon': settlement['lon'],
            'lat': settlement['lat'],
            'on_grid': power_type,
            'luminosity_mean': luminosity_mean['mean'],
            'luminosity_sum': luminosity_mean['sum'],
            'luminosity_max': luminosity_mean['max'],
            'travel_dist': distance_km,
            'coverage_2G_percent': coverage_lut[settlement['id']]['2G'],
            'coverage_3G_percent': coverage_lut[settlement['id']]['3G'],
            'coverage_4G_percent': coverage_lut[settlement['id']]['4G'],
            'coverage_5G_percent': coverage_lut[settlement['id']]['5G'],
        })

    results_df = pd.DataFrame(results)
    results_df.to_csv(path_output, index=False)

    return


def get_settlement_coverage(country, settlements):
    """
    Get coverage by technology.

    Parameters
    ----------
    country : string
        Three digit ISO country code.

    """
    iso3 = country['iso3']
    iso2 = country['iso2']

    filename = 'settlement_coverage_lut.csv'
    folder = os.path.join(DATA_INTERMEDIATE, iso3, 'coverage')
    if not os.path.exists(folder):
        os.makedirs(folder)

    path_output = os.path.join(folder, filename)

    # if os.path.exists(path_output):
    #     output = pd.read_csv(path_output)
    #     output = output.to_dict('records')
    #     return output

    technologies = ['2G', '3G', '4G', '5G']

    output = []

    for idx, settlement in settlements.iterrows():

        # if not settlement['id'] == '107.61141,-7.09968':
        #     continue
        # print(settlement)
        interim = {}

        for tech in technologies:

            folder_nm = 'MCE_{}'.format(tech)
            folder = os.path.join(DATA_RAW, 'MCE 2020', 'Data_MCE', 'ByCountry', folder_nm)
            filename = 'MCE_{}{}_2020.tif'.format(iso2, tech)
            path_input = os.path.join(folder, filename)

            if os.path.exists(path_input):
                path_coverage = path_input
            else:
                folder_nm = 'OCI_{}'.format(tech)
                folder = os.path.join(DATA_RAW, 'MCE 2020', 'Data_OCI', 'ByCountry', folder_nm)
                filename = 'OCI_{}{}_2020.tif'.format(iso2, tech)
                path_input = os.path.join(folder, filename)

                if os.path.exists(path_input):
                    path_coverage = path_input
                else:
                    interim[tech] = 0
                    continue

            with rasterio.open(path_coverage) as src:
                affine = src.transform
                array = src.read(1)
                array[array <= 0] = 0
                array[array > 1] = 1

                total = point_query(
                    settlement['geometry'],
                    array,
                    # stats=['sum', 'count'],
                    affine=affine,
                    nodata=-999
                    )[0]
                # print(results)
                # total = results['sum']
                # print(total)
                if total is not None:
                    if total > 0:
                        interim[tech] = 1
                    else:
                        interim[tech] = 0
                else:
                    interim[tech] = 0
                # print(interim)
        output.append({
            'id': settlement['id'],
            '2G': interim['2G'],
            '3G': interim['3G'],
            '4G': interim['4G'],
            '5G': interim['5G']
            })

    output = pd.DataFrame(output)
    output.to_csv(path_output, index=False)

    return output


def convert_coverage_to_settlement_lookup(coverage):
    """
    Takes a list of dicts and returns a dict for each access.

    """
    output = {}

    for idx, item in coverage.iterrows():
        output[item['id']] = {
            '2G': item['2G'],
            '3G': item['3G'],
            '4G': item['4G'],
            '5G': item['5G']
        }

    return output


def get_area(region):
    """
    Return the area in square km.

    """
    project = pyproj.Transformer.from_crs('epsg:4326', 'esri:54009', always_xy=True).transform
    new_geom = transform(project, region['geometry'])
    area_km = new_geom.area / 1e6

    return area_km


def find_distance_to_major_settlement(country, major_settlements, settlement):
    """
    Finds the distance to the nearest major settlement.

    """
    nearest = nearest_points(settlement['geometry'], major_settlements.unary_union)[1]

    geom = LineString([
                (
                    settlement['geometry'].coords[0][0],
                    settlement['geometry'].coords[0][1]
                ),
                (
                    nearest.coords[0][0],
                    nearest.coords[0][1]
                ),
            ])

    distance_km = round(geom.length / 1e3)

    return distance_km


if __name__ == '__main__':

    # countries = find_country_list(['Africa'])

    countries = [
        {'iso3': 'PER', 'iso2': 'PE', 'regional_level': 2, #'regional_nodes_level': 3,
            'region': 'LAT', 'pop_density_km2': 100, 'settlement_size': 100,
           # 'subs_growth': 3.5, 'smartphone_growth': 5, 'cluster': 'C1', 'coverage_4G': 16
        },
        {'iso3': 'IDN', 'iso2': 'ID', 'regional_level': 2, #'regional_nodes_level': 3,
            'region': 'SEA', 'pop_density_km2': 100, 'settlement_size': 100,
            # 'subs_growth': 3.5, 'smartphone_growth': 5, 'cluster': 'C1', 'coverage_4G': 16
        },
    ]

    for country in countries:

        print('Working on {}'.format(country['iso3']))

        # process_country_shapes(country)

        # process_regions(country)

        # process_settlement_layer(country)

        # process_electricity_layer(country)

        # process_night_lights(country)

        # get_regional_data(country)

        generate_settlement_layer(country)

        process_major_settlement_layer(country)

        get_settlement_data(country)

    print('Preprocessing complete')
