"""
Electricity cost module.

Written by Ed Oughton.

December 2020

"""

def electricity_cost(elec, on_grid, strategy, mix, energy_costs, dist):
    """
    Calculate the cost of electricity consumption.

    Parameters
    ----------
    elec : int
        The quantity of electricity consumption.
    strategy : string
        The strategy being implemented.
    mix : list of dicts
        Contains the electricity generation mix.
    energy_costs : dict
        Contains the cost per kWh by electricity generation type.
    dist : int
        Distance to nearest major settlement.

    Returns
    -------
    cost : int
        Cost of electricity consumption in US dollars.

    """

    if on_grid == 'on_grid':

        capex = 0

        oil = elec * mix['oil'] * energy_costs['oil_usd_kwh']
        gas = elec * mix['gas'] * energy_costs['gas_usd_kwh']
        coal = elec * mix['coal'] * energy_costs['coal_usd_kwh']
        nuclear = elec * mix['nuclear'] * energy_costs['nuclear_usd_kwh']
        hydro = elec * mix['hydro'] * energy_costs['hydro_usd_kwh']
        renewables = elec * mix['renewables'] * energy_costs['renewables_usd_kwh']

        opex = oil + gas + coal + nuclear + hydro + renewables

    elif on_grid == 'off_grid_diesel':

        capex = 5000

        diesel_price = 1
        speed = 50 #km/h
        t = dist / speed #dist in km, t in hours

        opex =  elec * (diesel_price / 3) * (1 + 0.08 * t) + 0.01

    elif on_grid == 'off_grid_solar':

        capex = 5000

        renewables = elec * energy_costs['renewables_usd_kwh']

        opex = renewables

    else:
        print('Cost module did not recognize: {}'.format(strategy))

    return capex, opex
