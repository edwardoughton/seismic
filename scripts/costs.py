"""
Electricity cost module.

Written by Ed Oughton.

December 2020

"""

def calculate_electricity_cost(electricity_consumption, strategy, electricity_mix, energy_costs):
    """
    Calculate the cost of electricity consumption.

    Parameters
    ----------
    electricity_consumption : int
        The quantity of electricity consumption.
    strategy : string
        The strategy being implemented.
    electricity_mix : list of dicts
        Contains the electricity generation mix.
    energy_costs : dict
        Contains the cost per kWh by electricity generation type.

    Returns
    -------
    cost : int
        Cost of electricity consumption in US dollars.

    """

    if strategy == 'baseline':

        oil = electricity_consumption * electricity_mix['oil'] * energy_costs['oil']
        gas = electricity_consumption * electricity_mix['gas'] * energy_costs['gas']
        coal = electricity_consumption * electricity_mix['coal'] * energy_costs['coal']
        nuclear = electricity_consumption * electricity_mix['nuclear'] * energy_costs['nuclear']
        hydro = electricity_consumption * electricity_mix['hydro'] * energy_costs['hydro']
        renewables = electricity_consumption * electricity_mix['renewables'] * energy_costs['renewables']

        cost = oil + gas + coal + nuclear + hydro + renewables

    elif  strategy == 'smart_diesel_generators':

        oil = electricity_consumption * electricity_mix['oil'] * energy_costs['oil']
        gas = electricity_consumption * electricity_mix['gas'] * energy_costs['gas']
        coal = electricity_consumption * electricity_mix['coal'] * energy_costs['coal']
        nuclear = electricity_consumption * electricity_mix['nuclear'] * energy_costs['nuclear']
        hydro = electricity_consumption * electricity_mix['hydro'] * energy_costs['hydro']
        renewables = electricity_consumption * electricity_mix['renewables'] * energy_costs['renewables']

        cost = oil + gas + coal + nuclear + hydro + renewables

    elif strategy == 'solar':

        oil = electricity_consumption * electricity_mix['oil'] * energy_costs['oil']
        gas = electricity_consumption * electricity_mix['gas'] * energy_costs['gas']
        coal = electricity_consumption * electricity_mix['coal'] * energy_costs['coal']
        nuclear = electricity_consumption * electricity_mix['nuclear'] * energy_costs['nuclear']
        hydro = electricity_consumption * electricity_mix['hydro'] * energy_costs['hydro']
        renewables = electricity_consumption * electricity_mix['renewables'] * energy_costs['renewables']

        cost = oil + gas + coal + nuclear + hydro + renewables

    else:
        print('Cost module did not recognize the stated strategy')

    return cost
