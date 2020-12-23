"""
Power module.

Written by Ed Oughton.

December 2020

"""

def elec_consumption(data_consumption_GB, strategy):
    """
    Estimate annual electricity consumption for this settlement.

    Parameters
    ----------
    data_consumption_GB : int
        The quantity of annual data consumption estimated for the settlement.
    strategy : string
        The strategy being implemented.

    Returns
    -------
    electricity_consumption : int
        The quantity of electricity consumption estimated for the settlement.

    """
    # kWh_per_GB = 0.25
    settlement_size = 1

    power_for_all_hours = []

    for key, data_consumption_GB in data_consumption_GB.items():

        hourly_GB = data_consumption_GB / 365 #from annual to daily

        hourly_MB = hourly_GB * 1000 #giga to mega

        hourly_Mbps = hourly_MB * 8 #bytes to bits

        Mbps = hourly_Mbps / 3600 #bytes to bits

        Mbps_km = Mbps / settlement_size # get area demand

        if strategy in ['smart_diesel_generators', 'smart_solar']:
            power_w = estimate_link_budget(Mbps_km, settlement_size)
        else:
            power_w = 40

        power_kWh = power_w * 1 / 1000 # 1 hour

        power_per_year = round(power_kWh * 365, 2)

        power_for_all_hours.append(power_per_year)

    return sum(power_for_all_hours)


def estimate_link_budget(data_consumption_Mbps_km, settlement_size):
    """
    Estimate the amount of power needed to serve the given area traffic.

    Parameters
    ----------
    data_consumption_Mbps_km : int
        The quantity of data traffic needing to be served.

    Returns
    -------
    power_w : int
        The quantity of electricity required.

    lut = [
        ['sinr': -6.7,'cqi': '1', 'QAM': 'QPSK', 'code_rate': 0.0762, 'spectral_efficiency':	0.1523],
        ['sinr': -4.7,'cqi': '2', 'QAM': 'QPSK', 'code_rate': 0.1172, 'spectral_efficiency':	0.2344],
        ['sinr': -2.3,'cqi': '3', 'QAM': 'QPSK', 'code_rate': 0.1885, 'spectral_efficiency':	0.377],
        ['sinr': 0.2,'cqi': '4', 'QAM': 'QPSK', 'code_rate': 308, 'spectral_efficiency': 0.6016],
        ['sinr': 2.4,'cqi': '5', 'QAM': 'QPSK', 'code_rate': 449, 'spectral_efficiency': 0.877],
        ['sinr': 4.3,'cqi': '6', 'QAM': 'QPSK', 'code_rate': 602, 'spectral_efficiency': 1.1758],
        ['sinr': 5.9,'cqi': '7', 'QAM': '16QAM', 'code_rate': 378, 'spectral_efficiency': 1.4766],
        ['sinr': 8.1,'cqi': '8', 'QAM': '16QAM', 'code_rate': 490, 'spectral_efficiency': 1.9141],
        ['sinr': 10.3,'cqi': '9', 'QAM': '16QAM', 'code_rate': 616, 'spectral_efficiency': 2.4063],
        ['sinr': 11.7,'cqi': '10', 'QAM': '64QAM', 'code_rate': 466, 'spectral_efficiency': 2.7305],
        ['sinr': 14.1,'cqi': '11', 'QAM': '64QAM', 'code_rate': 567, 'spectral_efficiency': 3.3223],
        ['sinr': 16.3,'cqi': '12', 'QAM': '64QAM', 'code_rate': 666, 'spectral_efficiency': 3.9023],
        ['sinr': 18.7,'cqi': '13', 'QAM': '64QAM', 'code_rate': 772, 'spectral_efficiency': 4.5234],
        ['sinr': 21,'cqi': '14', 'QAM': '64QAM', 'code_rate': 873, 'spectral_efficiency': 5.1152],
        ['sinr': 22.7,'cqi': '15', 'QAM': '64QAM', 'code_rate': 948, 'spectral_efficiency': 5.5547],
    ]

    """
    bandwidth_MHz = 20
    bandwidth_Hz = bandwidth_MHz * 1e6
    data_consumption_bps_km = data_consumption_Mbps_km * 1e6

    #find the spectrum efficiency to provide the required capacity per settlement area
    #rearranged capacity = spectral_efficiency_bps * bandwidth_Hz / area_km2
    spectral_efficiency_bps = data_consumption_bps_km / bandwidth_Hz * settlement_size

    if spectral_efficiency_bps < 0.1523:
        sinr = -6.7
    elif spectral_efficiency_bps < 0.2344:
        sinr = -4.7
    elif spectral_efficiency_bps < 0.377:
        sinr = -2.3
    elif spectral_efficiency_bps < 0.6016:
        sinr = 0.2
    elif spectral_efficiency_bps < 0.877:
        sinr = 2.4
    elif spectral_efficiency_bps < 1.1758:
        sinr = 4.3
    elif spectral_efficiency_bps < 1.4766:
        sinr = 5.9
    elif spectral_efficiency_bps < 1.9141:
        sinr = 8.1
    elif spectral_efficiency_bps < 2.4063:
        sinr = 10.3
    elif spectral_efficiency_bps < 2.7305:
        sinr = 11.7
    elif spectral_efficiency_bps < 3.3223:
        sinr = 14.1
    elif spectral_efficiency_bps < 3.9023:
        sinr = 16.3
    elif spectral_efficiency_bps < 4.5234:
        sinr = 18.7
    elif spectral_efficiency_bps <  5.1152:
        sinr = 21
    else:
        sinr = 22.3

    #calculate received power
    interference = 5 #dB
    noise = 5 #dB
    received_power = sinr * (interference + noise)

    #calculate required transmitter power
    tx_gain = 16
    tx_losses = 1
    path_loss = 111
    rx_misc_losses = 4
    rx_gain = 4
    rx_losses = 4

    power_w = (
        received_power -
        tx_gain +
        tx_losses +
        path_loss +
        rx_misc_losses +
        rx_gain -
        rx_losses
    )

    if power_w < 5:
        power_w = 5

    if power_w > 40:
        power_w = 40

    return power_w
