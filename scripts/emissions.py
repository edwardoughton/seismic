"""
Emissions module.

Written by Ed Oughton.

December 2020

"""

def estimate_emissions(elec, on_grid, strategy, mix, tech_lut):
    """
    Estimate emissions released from energy consumption.

    The logic in this module differetiates between those strategies that use
    ongrid power and the offgrid variant based on just solar ('pure_solar').

    Parameters
    ----------
    elec : int
        The quantity of electricity consumption estimated for the settlement.
    on_grid : string
        Whether the settlement is estimated to be ongrid or offgrid.
    strategy : string
        The strategy being implemented.
    mix : list of dicts
        Contains the electricity generation mix.
    tech_lut : dict
        Contains emission information for on-grid or off-grid technologies.

    Returns
    -------
    output : int
        The quantity of emissions released by the settlement cellular network.

    """
    output = {}

    if on_grid == 'on_grid' and not strategy == 'pure_solar':

        elec_types = ['oil', 'gas', 'coal', 'nuclear', 'hydro', 'renewables']

        output['carbon_kgs'] = calc_ongrid(elec, mix, tech_lut, elec_types, 'carbon_per_kWh')

        output['nitrogen_oxides_kgs'] = calc_ongrid(elec, mix, tech_lut, elec_types,
            'nitrogen_oxide_per_kWh')

        output['sulpher_oxides_kgs'] = calc_ongrid(elec, mix, tech_lut, elec_types,
            'sulpher_dioxide_per_kWh')

        output['pm10_kgs'] = calc_ongrid(elec, mix, tech_lut, elec_types,
            'pm10_per_kWh')

    elif on_grid == 'on_grid' and strategy == 'pure_solar':

        output['carbon_kgs'] = elec * tech_lut['renewables']['carbon_per_kWh']

        output['nitrogen_oxides_kgs'] = elec * tech_lut['renewables']['nitrogen_oxide_per_kWh']

        output['sulpher_oxides_kgs'] = elec * tech_lut['renewables']['sulpher_dioxide_per_kWh']

        output['pm10_kgs'] = elec * tech_lut['renewables']['pm10_per_kWh']

    elif on_grid == 'off_grid_diesel':

        output['carbon_kgs'] = elec * tech_lut['diesel']['carbon_per_kWh']

        output['nitrogen_oxides_kgs'] = elec * tech_lut['diesel']['nitrogen_oxide_per_kWh']

        output['sulpher_oxides_kgs'] = elec * tech_lut['diesel']['sulpher_dioxide_per_kWh']

        output['pm10_kgs'] = elec * tech_lut['diesel']['pm10_per_kWh']

    elif on_grid == 'off_grid_solar':

        output['carbon_kgs'] = elec * tech_lut['renewables']['carbon_per_kWh']

        output['nitrogen_oxides_kgs'] = elec * tech_lut['renewables']['nitrogen_oxide_per_kWh']

        output['sulpher_oxides_kgs'] = elec * tech_lut['renewables']['sulpher_dioxide_per_kWh']

        output['pm10_kgs'] = elec * tech_lut['renewables']['pm10_per_kWh']

    else:
        print('Emissions module did not recognize: {}'.format(on_grid))

    return output


def calc_ongrid(elec, mix, tech_lut, elec_types, emission_type):
    """
    Calculate the emissions for a given electricity and emission type.

    Parameters
    ----------
    elec : int
        The quantity of electricity consumption estimated for the settlement.
    mix : list of dicts
        Contains the electricity generation mix.
    tech_lut : dict
        Contains emission information for on-grid or off-grid technologies.
    elec_types : string
        The generation types of the electricity to calculate.
    emission_type : string
        The emissions type for the electricity to calculate.

    Returns
    -------
    emissions : int
        The estimated emissions for the stated electricity consumption.

    """
    emissions = 0

    for elec_type in elec_types:

        emissions += elec * mix[elec_type] * tech_lut[elec_type][emission_type]

    return emissions
