file = {
    'output_prefix': 'RMI_QA',
    'output_raw_data': False,
    'template': None, ##'RMI_template.xlsx',
    'template_sheets': ['SUMMERY']
}

login = {
    ## file info
    'input_file': None, #'2023-07-18 2_31pm.csv', ## put None for using SF
    'input_date_format': '%d/%m/%Y',
    ## SF info
    'cred_file': 'cred_RMI.json', ## a json file, put None if not applicable, format: {"user": "XXX", "password": "XXX"}
    'account': 'kinesso.us-east-1',
    'role': 'INI_AMAZON_US',
    'warehouse': 'INI_AMAZON_US',
    'database': 'GR_KINESSO',
    'schema': 'INI_AMAZON_US',
    'table': 'AMZ_002_OUTPUT_ALL'
}

# initial column selection
select = {
    ## date range, only when using Sf
    'days': 60, ## a number
    'date_start': None,
    'date_end': None, ## 'YYYY-MM-DD', used for SF, if both have value, ignore 'days'

    ## columns, for using both files and SF
    'variable_date': 'DATE',
    'variable': [
        'SOURCE', 'COUNTRY', 'CHANNEL', 'PLATFORM', 
        'CAMPAIGN_NAME', 'PLACEMENT_NAME',
        'AUDIENCE', 'OBJECTIVE'
    ],
    'value': {
        ## {regular name}: {custom name}, do not change any keys, if not applicable, leave values as None
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


## each list is a level of granularity to check, contains the index in list select['variable']
check_level = {
    'Campaign':[1,2,3,4],
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
check_date_level = [0] ## 0: SOURCE
## The day of week in 3 letters, that is the end of the week
check_date_end_of_week = 'Sat'


## the index in select['variable'], to count the frequency
check_variable_count = [6, 7]
