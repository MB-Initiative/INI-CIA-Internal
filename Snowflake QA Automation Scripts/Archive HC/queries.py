# Importing libraries
import json
import snowflake.connector
from snowflake.connector.pandas_tools import write_pandas
import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime, timedelta


def run_query(mapping_login, query):
    
    f = open(mapping_login['cred_file'])
    cred = json.load(f)
    
    con = snowflake.connector.connect(
            user = cred['user'],
            password = cred['password'],
            account = mapping_login['account'],
            role = mapping_login['role'],
            warehouse = mapping_login['warehouse'],
            database = mapping_login['database'],
            schema = mapping_login['schema']
        )

    df = pd.read_sql(query, con, index_col=None)

    con.close()
    return df


def select_table_by_query(mapping_login, mapping_select, days = 90, date_start = None, date_end = None):
    
    date_column = mapping_select['variable_date'], days = days

    if not date_start or not date_end:
        date_filter = '''{date_column} >= DATEADD(DAY, -{days}, CURRENT_DATE()) AND {date_column} < CURRENT_DATE()'''.format(
            date_column = mapping_select['variable_date'], days = days)
    else:
        date_filter = '''{date_column} >= {date_start} AND {date_column} <= {date_end}'''.format(
            date_column = mapping_select['variable_date'], date_start = date_start, date_end = date_end)

    variable_str = mapping_select['variable_date'] + ','  + ', '.join(mapping_select['variable'])
    
    value_list = [
            mapping_select['value'][key] 
            for key in mapping_select['value'] 
            if key != 'custom value' and mapping_select['value'][key]
        ] + mapping_select['value']['custom value']
    
    value_str = ', '.join([
        'SUM({value}) AS {value}'.format(value = value) for value in value_list
        ])

    query = '''
    SELECT {variable_str}, {value_str}
    FROM {database}.{schema}.{table}
    WHERE {date_filter}
    GROUP BY {variable_str}
    ORDER BY {variable_str}
    '''.format(
        variable_str = variable_str, 
        value_str = value_str,
        database = mapping_login['database'], 
        schema = mapping_login['schema'], 
        table = mapping_login['table'], 
        date_filter = date_filter
    )
    
    df = run_query(mapping_login, query)

    df[date_column] = df[date_column].map(lambda x: datetime.date(x))
    
    return df

def select_table_by_path(file_path, mapping_select, date_format = '%d/%m/%Y'):
    
    column_date = mapping_select['variable_date']
    
    if '.xlsx' in file_path:
        df = pd.read_excel(file_path, dtypes = {column_date:str})
    else:
        df = pd.read_csv(file_path)
    
    df[column_date] = df[column_date].map(lambda x: datetime.date(datetime.strptime(x, date_format)))
    
    value_list = [
            mapping_select['value'][key] 
            for key in mapping_select['value'] 
            if key != 'custom value' and mapping_select['value'][key]
        ] + mapping_select['value']['custom value']
    
    df = df.groupby(
        [column_date] + mapping_select['variable'], as_index=False
    )[value_list].sum()
    
    return df