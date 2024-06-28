login = {
    'cred_file': 'cred_WFS.json',
    'account': 'kinesso.us-east-1',
    'role': 'INIUK_AMAZON_EMEA',
    'warehouse': 'INIUK_AMAZON_EMEA',
    'database': 'GR_KINESSO',
    'schema': 'INIUK_AMAZON_EMEA',
    'table': 'WFS_OUTPUT_ALL'
}

# initial column selection
select = {
    'variable_date': 'DATE',
    'variable': [
        'SOURCE', 'COUNTRY', 'CHANNEL', 'PLATFORM', 
        'CAMPAIGN_NAME', 'PLACEMENT_NAME',
        'AUDIENCE', 'OBJECTIVE'
    ],
    'value': {
        ## {regular name}: {custom name}, leave as None if not applicable
        'SPEND': 'NET_SPEND',
        'IMPRESSIONS': 'IMPRESSIONS',
        'CLICKS': 'CLICKS',
        'CONVERSIONS': None,
        'REVENUE': None,
        'VIDEO_VIEWS': 'VIDEO_VIEWS',
        'VIDEO_STARTS': 'VIDEO_STARTS',
        'VIDEO_25': 'VIDEO_25',
        'VIDEO_50': 'VIDEO_50',
        'VIDEO_75': 'VIDEO_75',
        'VIDEO_100': 'VIDEO_100',
        ## put the rest of the values in the list
        'custom value': ['GROSS_SPEND', 'ENGAGEMENTS']
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
