# Campaign Variables
weeks = 8
currency = "$"
total_spend = 10000000
roas = 1.6
som = 0.15

start_date = '2024-01-01'

                                        # Weighting
performance_dict = {'Country':  {'UK':  [0.60],
                                 'FR':  [0.25],
                                 'DE':  [0.15]
                                 },

                                        # Weighting
                    'Category': {'C1':  [0.75],
                                 'C2':  [0.25]
                                 },

                                        # Weighting
                    'Market':   {'M1':  [0.55],
                                 'M2':  [0.30],
                                 'M3':  [0.15]
                                 },

                                        # Weighting
                    'Product':  {'P1':  [0.35],
                                 'P2':  [0.25],
                                 'P3':  [0.18],
                                 'P4':  [0.12],
                                 'P5':  [0.10]
                                 },
                 
                                                    # Mix, CPC, CTR
                    'Channel':  {'Paid Social':     ['0.4', '2.5', '2.0'],
                                 'Online Video':    ['0.35', '2.0', '1.5'],
                                 'Display':         ['0.25', '1.5', '1.0']
                                 },

}

# F&F Scores
fame_flow_dict = {
    'Familiarity': 0.84,
    'Favorability': 0.35,
    'Feeling': 0.16,
    'Fervor': 0.07,
    'Facilitation': 0.63,
    'Finadability': 0.45,
    'Fascination': 0.29,
    'Following': 0.26
}