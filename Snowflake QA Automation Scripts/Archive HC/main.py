# Importing libraries
import os
import pandas as pd
import numpy as np
from datetime import datetime
from datetime import timedelta
import time

# Libraries for SQL connection
from sqlalchemy import create_engine
from snowflake.sqlalchemy import URL

# AWS Mappings
import mappings_hb as mappings
import queries
import checks


# Constants
current_path = os.getcwd()
current_sep = os.path.sep
output_name = 'sample_output_%s.xlsx'%(datetime.now().strftime('%Y%m%d_%H%M'))

input_file = '20230913_1142_HB_Clean_Output.csv'
output_file = 'sample_output_%s.xlsx'%(datetime.now().strftime('%Y%m%d_%H%M'))


#### Use local file
file_name = '20230913_1142_HB_Clean_Output.csv'
file_path = current_sep.join([current_path, file_name])
df = queries.select_table_by_path(file_path, mappings.select, date_format = '%d/%m/%y')

# Running QA

# check the end date of each source
df_check_date = checks.check_date_end(df, mappings.select, mappings.check_date_level, mappings.check_date_end_of_week)
# group by, and find % change of metric
df_change_dict = checks.check_variation(df, mappings.select, mappings.check_level, mappings.value_calculated, mappings.check_variation_interval, mappings.no_std)
# count variable
df_count = checks.aggregate_count(df, mappings.select, mappings.check_variable_count)

# Output
output_path = os.getcwd() + "\\" + output_file

with pd.ExcelWriter(output_path) as writer:
 
    df_check_date.to_excel(writer, sheet_name='check date', index = False, na_rep='nan')
    
    for name, result in df_change_dict.items():
        result.to_excel(writer, sheet_name=name, index = False)
    df_count.to_excel(writer, sheet_name='Variable frequency', index = False, na_rep='nan')
    
    df.to_excel(writer, sheet_name='raw data', index = False, na_rep='nan')
    