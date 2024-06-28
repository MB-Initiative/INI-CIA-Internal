# Importing libraries
import os
import pandas as pd
import numpy as np
from datetime import datetime
from datetime import timedelta
import time
import shutil
import warnings

import queries
import checks
import mappings


warnings.filterwarnings("ignore")

#### Output path
current_path = os.getcwd()
current_sep = os.path.sep
timestamp = datetime.now().strftime('%Y%m%d_%H%M')
output_name = '%s_%s.xlsx'%(mappings.file['output_prefix'], timestamp)
output_path = current_sep.join([current_path, output_name])

input_name = mappings.login['input_file']
#### Use local file
if input_name:
    input_path = current_sep.join([current_path, input_name])
    print('Reading file: '+input_path)
    df = queries.select_table_by_path(input_path, mappings.select, date_format = mappings.login['input_date_format'])
#### Use SF
else:
    print('Reading file from Snowflake')
    df = queries.select_table_by_query(
        mappings.login, mappings.select, 
        days = mappings.select['days'], date_start = mappings.select['date_start'], date_end = mappings.select['date_end'])

#### Running QA
print('Start QA')
# check the end date of each source
df_check_date = checks.check_date_end(df, mappings.select, mappings.check_date_level, mappings.check_date_end_of_week)
# group by, and find % change of metric
df_change_dict = checks.check_variation(df, mappings.select, mappings.check_level, True, mappings.check_variation_interval, mappings.no_std_threshold, mappings.recent_day_threshold)
# count variable
df_count = checks.aggregate_count(df, mappings.select, mappings.check_variable_count)

# Output

print('Saving results')

template_name = mappings.file['template']

if template_name:
    print('Copy template')
    template_path = current_sep.join([current_path, template_name])
    shutil.copy(template_path, output_path)
    
    writer = pd.ExcelWriter(output_path, engine='openpyxl', mode='a')
    workbook = writer.book
    for name in workbook.sheetnames:
        if not (name in mappings.file['template_sheets']):
            workbook.remove(workbook[name])

else:
    writer = pd.ExcelWriter(output_path, engine='openpyxl', mode='w')

df_check_date.to_excel(writer, sheet_name='Check date', index = False, na_rep='nan')

for name, value in df_change_dict.items():
    value.to_excel(writer, sheet_name=name, index = False)

df_count.to_excel(writer, sheet_name='Variable frequency', index = False, na_rep='nan')

writer._save()
writer.close()
print('Result saved at ' + output_path)

if mappings.file['output_raw_data']:
    output_name_raw = '%s_raw_%s.xlsx'%(mappings.file['output_prefix'], timestamp)
    output_path_raw = current_sep.join([current_path, output_name_raw])
    df.to_excel(output_path_raw, index = False, na_rep=None)
    print('Raw data saved at ' + output_path_raw)

print('Done!')

