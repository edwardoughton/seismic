"""
Model parameters.

"""

PARAMETERS = {
    'baseline':{
        'iterations': 1,
        'seed_value1_4G': 3,
        'seed_value2_4G': 4,
        'seed_value1_rural': 11,
        'seed_value2_rural': 12,
        'indoor_users_percentage': 50,
        'los_breakpoint_m': 500,
        'tx_macro_baseline_height': 30,
        'tx_macro_power': 20,
        'tx_macro_gain': 16,
        'tx_macro_losses': 1,
        'rx_gain': 0,
        'rx_losses': 4,
        'rx_misc_losses': 4,
        'rx_height': 1.5,
        'building_height': 5,
        'street_width': 20,
        'above_roof': 0,
        'network_load': 100,
        'percentile': 50,
        'sectorization': 3,
        'mnos': 2,
        'asset_lifetime': 10,
        'discount_rate': 3.5,
        'opex_percentage_of_capex': 10,
        'min_w': 20,
        'max_w': 20,
        'increment': 2,
    },
    'managed_power': {
        'iterations': 1,
        'seed_value1_4G': 3,
        'seed_value2_4G': 4,
        'seed_value1_rural': 11,
        'seed_value2_rural': 12,
        'indoor_users_percentage': 50,
        'los_breakpoint_m': 500,
        'tx_macro_baseline_height': 30,
        'tx_macro_power': 20,
        'tx_macro_gain': 16,
        'tx_macro_losses': 1,
        'rx_gain': 0,
        'rx_losses': 4,
        'rx_misc_losses': 4,
        'rx_height': 1.5,
        'building_height': 5,
        'street_width': 20,
        'above_roof': 0,
        'network_load': 100,
        'percentile': 50,
        'sectorization': 3,
        'mnos': 2,
        'asset_lifetime': 10,
        'discount_rate': 3.5,
        'opex_percentage_of_capex': 10,
        'min_w': 5,
        'max_w': 20,
        'increment': 2,
    },
    # 'smart_power': {
    #     'iterations': 1,
    #     'seed_value1_4G': 3,
    #     'seed_value2_4G': 4,
    #     'seed_value1_rural': 11,
    #     'seed_value2_rural': 12,
    #     'indoor_users_percentage': 50,
    #     'los_breakpoint_m': 500,
    #     'tx_macro_baseline_height': 30,
    #     'tx_macro_power': 20,
    #     'tx_macro_gain': 16,
    #     'tx_macro_losses': 1,
    #     'rx_gain': 0,
    #     'rx_losses': 4,
    #     'rx_misc_losses': 4,
    #     'rx_height': 1.5,
    #     'building_height': 5,
    #     'street_width': 20,
    #     'above_roof': 0,
    #     'network_load': 100,
    #     'percentile': 50,
    #     'sectorization': 3,
    #     'mnos': 2,
    #     'asset_lifetime': 10,
    #     'discount_rate': 3.5,
    #     'opex_percentage_of_capex': 10,
    # },
}

SPECTRUM_PORTFOLIO = [
    # (0.7, 1, '4G', '2x2'),
    (0.8, 1, '4G', '2x2'),
    # (0.85, 1, '4G', '2x2'),
    # (1.7, 1, '4G', '2x2'),
    # (1.8, 1, '4G', '2x2'),
    # (1.9, 1, '4G', '2x2'),
    # (2.3, 1, '4G', '2x2'),
    # (2.5, 1, '4G', '2x2'),
    # (2.6, 1, '4G', '2x2'),
]

ANT_TYPES = [
    ('macro'),
]

MODULATION_AND_CODING_LUT = {
    # ETSI. 2018. ‘5G; NR; Physical Layer Procedures for Data
    # (3GPP TS 38.214 Version 15.3.0 Release 15)’. Valbonne, France: ETSI.
    # Generation MIMO CQI Index	Modulation	Coding rate
    # Spectral efficiency (bps/Hz) SINR estimate (dB)
    '4G': [
        ('4G', '2x2', 1, 'QPSK', 78, 0.3, -6.7),
        ('4G', '2x2', 2, 'QPSK', 120, 0.46, -4.7),
        ('4G', '2x2', 3, 'QPSK', 193, 0.74, -2.3),
        ('4G', '2x2', 4, 'QPSK', 308, 1.2, 0.2),
        ('4G', '2x2', 5, 'QPSK', 449, 1.6, 2.4),
        ('4G', '2x2', 6, 'QPSK', 602, 2.2, 4.3),
        ('4G', '2x2', 7, '16QAM', 378, 2.8, 5.9),
        ('4G', '2x2', 8, '16QAM', 490, 3.8, 8.1),
        ('4G', '2x2', 9, '16QAM', 616, 4.8, 10.3),
        ('4G', '2x2', 10, '64QAM', 466, 5.4, 11.7),
        ('4G', '2x2', 11, '64QAM', 567, 6.6, 14.1),
        ('4G', '2x2', 12, '64QAM', 666, 7.8, 16.3),
        ('4G', '2x2', 13, '64QAM', 772, 9, 18.7),
        ('4G', '2x2', 14, '64QAM', 973, 10.2, 21),
        ('4G', '2x2', 15, '64QAM', 948, 11.4, 22.7),
    ],
}

CONFIDENCE_INTERVALS = [
    5,
    50,
    95,
]

def generate_site_radii(min, max, increment):
    for n in range(min, max, increment):
        yield n

INCREMENT_MA = (5000, 6000, 1000)#(400, 40400, 1000)

SITE_RADII = {
    'macro': {
        # 'urban':
        #     generate_site_radii(INCREMENT_MA[0],INCREMENT_MA[1],INCREMENT_MA[2]),
        # 'suburban':
        #     generate_site_radii(INCREMENT_MA[0],INCREMENT_MA[1],INCREMENT_MA[2]),
        'rural':
            generate_site_radii(INCREMENT_MA[0],INCREMENT_MA[1],INCREMENT_MA[2])
        },
    }

ENVIRONMENTS =[
    # 'urban',
    # 'suburban',
    'rural'
]
