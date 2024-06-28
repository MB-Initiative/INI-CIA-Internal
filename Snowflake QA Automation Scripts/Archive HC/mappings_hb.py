# initial column selection
select = {
    'variable_date': 'Date',
    'variable': [
        'Platform', 'Final Country', 'Phase', 'Campaign Name', 
        'Ad Name'
    ],
    'value': {
        ## {regular name}: {custom name}, leave as None if not applicable
        'SPEND': 'Mediabudget',
        'IMPRESSIONS': 'Impressions',
        'CLICKS': 'Clicks',
        'CONVERSIONS': None,
        'REVENUE': 'Revenue',
        'VIDEO_VIEWS': 'Video Views (all)',
        'VIDEO_STARTS': None,
        'VIDEO_25': None,
        'VIDEO_50': '50% Watched',
        'VIDEO_75': None,
        'VIDEO_100': '100% Watched',
        ## put the rest of the values in the list
        'custom value': ['Engagement']
    }
}

## name of calculated values, comment unused ones
value_calculated = [
    'CTR',
    # 'CVR',
    'CPM',
    'CPC',
    # 'CPA',
    'CPV' ,
    # 'ROAS',
    # 'AOV'
]

# the dimension to group by when checking max date
check_date_level = [0]
check_date_end_of_week = 'Sat'

# each list is a level of granularity to check, contains index in select['variable']
check_level = {
    'Country,Channel':[1,2],
    'Country,Channel,Platform':[1,2,3],
    'Campaign':[1,2,3,4]
}

# number of days in each interval for mean & std 
check_variation_interval = [1, 7]

# thershold no of std between mean and each interval
no_std = 3

# number of days to check the value change
check_change_days = [1, 7, 30]

# index in select['variable'], to count the frequency
check_variable_count = [6, 7]
