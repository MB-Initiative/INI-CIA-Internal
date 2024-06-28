file = {
    'output_prefix': 'WFS_QA',
    'output_raw_data': True,
    'template': None,
    'template_sheets': []
}

login = {
    'input_file': None, ## put None for using SF
    'input_date_format': '%d/%m/%Y',
    ## SF info
    'cred_file': 'cred_WFS.json', ## a json file, put None if not applicable
    'account': 'kinesso.us-east-1',
    'role': 'INIUK_AMAZON_EMEA',
    'warehouse': 'INIUK_AMAZON_EMEA',
    'database': 'GR_KINESSO',
    'schema': 'INIUK_AMAZON_EMEA',
    'table': 'WFS_OUTPUT_004_TBL'
}

# initial column selection
select = {
    ## date range, only when using Sf
    'days': 30, ## a number
    'date_start': None,
    'date_end': None, ## 'YYYY-MM-DD', used for SF, if both have value, ignore 'days'

    ## columns, for using both files and SF
    'variable_date': 'DATE',
    'variable': [
        'SOURCE', 'MARKET', 'CHANNEL', 'PLATFORM', 
        'FORMAT', 'OBJECTIVE'
    ],
    'value': {
        ## {regular name}: {custom name}, do not change any keys, if not applicable, leave values as None
        'SPEND': 'NETCOST_LOCAL',
        'IMPRESSIONS': 'IMPRESSIONS',
        'CLICKS': 'CLICKS',
        'CONVERSIONS': 'TOTALCONVERSIONS_COMPLETEDAPPS',
        'REVENUE': None,
        'VIDEO_VIEWS': None,
        'VIDEO_STARTS': 'VIDEO_STARTS',
        'VIDEO_25': 'VIDEO_25',
        'VIDEO_50': 'VIDEO_50',
        'VIDEO_75': 'VIDEO_75',
        'VIDEO_100': 'VIDEO_100',
        ## put the rest of the values in the list
        'custom value': []
    }
}


## each list is a level of granularity to check, contains the index in list select['variable']
check_level = {
    'Platform':[1,2,3],
    'Channel':[1,2]
}
## number of days in each interval for mean & std 
check_variation_interval = [1, 7]
## thershold of z-score
no_std_threshold = 3
## thershold of days considered as recent
recent_day_threshold = 7


## the index in list select['variable'] when checking max date
check_date_level = [0,3] ## 0: SOURCE, 3:PLATFORM
## The day of week in 3 letters, that is the end of the week
check_date_end_of_week = 'Sat'


## the index in select['variable'], to count the frequency
check_variable_count = [4,5]
