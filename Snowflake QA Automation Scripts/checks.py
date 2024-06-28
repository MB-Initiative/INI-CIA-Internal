# Importing libraries
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def day_intervals(start_date, end_date, interval = 1, reverse = True):
    '''generate a 2d list of intervals'''
    date_list = []
        
    # start_date = datetime.date(start_date)
    # end_date = datetime.date(end_date)
    sign = 1
    
    if reverse:
        start_date, end_date = end_date, start_date
        sign = -1
        
    S = start_date
    E = S + timedelta(days = (interval - 1)*sign)
    date_list.append([S, E, interval])

    while E != end_date:  
        S = E + timedelta(days = 1*sign)
        E = S + timedelta(days = (interval - 1)*sign)
        
        if reverse:
            E = max(E, end_date)
        else:
            E = min(E, end_date)
        date_list.append([S, E, abs((E-S).days) + 1])
    
    return date_list 

def check_date_end(df, mapping_select, mapping_check_date_level, end_of_week):
    '''given a level and date column, find date range of each level and check if they are up to date
    end_of_week: 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun' '''
    
    column_date = mapping_select['variable_date']
    column_variable = [mapping_select['variable'][i] for i in mapping_check_date_level]
    
    df_dates = df.groupby(
        column_variable, as_index=False
    ).agg({column_date:[min,max]})
    
    df_dates.columns = column_variable + ['MIN DATE', 'MAX DATE']
    
    max_date = df_dates['MAX DATE'].max()
    
    last_7 = [datetime.date(datetime.today() - timedelta(days=i)) for i in range(1,8)]
    yesterday = last_7[0]
    
    last_7_weekday = [i.weekday() for i in last_7] ## Monday is 0
    end_index = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].index(end_of_week)
    end = last_7[last_7_weekday.index(end_index)]
    
    df_dates['VS LAST %s'%(end_of_week.upper())] = df_dates['MAX DATE'].map(
        lambda x: 
        'updated' if x >= yesterday else
        'updated to last %s'%(end_of_week) if x >= end else '* missing %d days'%((end - x).days)
    )
    
    df_dates['VS MAX DATE'] = df_dates['MAX DATE'].map(
        lambda x: 
        'updated' if x >= max_date
        else '* missing %d days'%((max_date - x).days)
    )
    
    return df_dates.sort_values('MAX DATE', ascending=False)

def value_calculation(df, mapping_select):
    '''add calculated columns'''
    df_new = df.copy()
    
    col_spd = mapping_select['value']['SPEND']
    col_imp = mapping_select['value']['IMPRESSIONS']
    col_clk = mapping_select['value']['CLICKS']
    col_con = mapping_select['value']['CONVERSIONS']
    col_rev = mapping_select['value']['REVENUE']
    col_vid = mapping_select['value']['VIDEO_VIEWS']
    
    if col_clk and col_imp:
        df_new['CTR'] = df[[col_clk, col_imp]].apply(lambda x: x[0]/x[1], axis = 1)
    
    if col_con and col_clk:
        df_new['CVR'] = df[[col_con, col_clk]].apply(lambda x: x[0]/x[1], axis = 1)
    
    if col_spd and col_imp:
        df_new['CPM'] = df[[col_spd, col_imp]].apply(lambda x: x[0]/x[1]*1000, axis = 1)
    
    if col_spd and col_clk:
        df_new['CPC'] = df[[col_spd, col_clk]].apply(lambda x: x[0]/x[1], axis = 1)
        
    if col_spd and col_con:
        df_new['CPA'] = df[[col_spd, col_con]].apply(lambda x: x[0]/x[1], axis = 1)
   
    if col_spd and col_vid:
        df_new['CPV'] = df[[col_spd, col_vid]].apply(lambda x: x[0]/x[1], axis = 1)
    
    if col_rev and col_spd:
        df_new['ROAS'] = df[[col_rev, col_spd]].apply(lambda x: x[0]/x[1], axis = 1)
        
    if col_rev and col_con:
        df_new['AOV'] = df[[col_rev, col_con]].apply(lambda x: x[0]/x[1], axis = 1)
    
    return df_new.replace([np.inf, -np.inf], np.nan)

def value_validation(df, mapping_select):
    '''validate if any rows have click>impressions, conversions>click, or video metric not in order'''
    df_new = df.copy()
    
    col_imp = mapping_select['value']['IMPRESSIONS']
    col_clk = mapping_select['value']['CLICKS']
    col_con = mapping_select['value']['CONVERSIONS']
    col_vidstarts = mapping_select['value']['VIDEO_STARTS']
    col_vid25 = mapping_select['value']['VIDEO_25']
    col_vid50 = mapping_select['value']['VIDEO_50']
    col_vid75 = mapping_select['value']['VIDEO_75']
    col_vid100 = mapping_select['value']['VIDEO_100']
    
    df_new['VALIDATION'] = ''
    
    if col_clk and col_imp:
        df_new['VALIDATION'] = df_new[['VALIDATION', col_clk, col_imp]].apply(
            lambda x: x[0]+'CLICKS>IMPRESSIONS;' if x[1]>x[2] else x[0], axis = 1)
        
    if col_clk and col_con:
        df_new['VALIDATION'] = df_new[['VALIDATION', col_con, col_clk]].apply(
            lambda x: x[0]+'CONVERSIONS>CLICKS;' if x[1]>x[2] else x[0], axis = 1)
        
    if col_vidstarts and col_vid25 and col_vid50 and col_vid75 and col_vid100:
        df_new['VALIDATION'] = df_new[['VALIDATION', col_vidstarts, col_vid25, col_vid50, col_vid75, col_vid100]].apply(
            lambda x: x[0]+'VIDEO NOT IN ORDER;' if (x[1]<x[2] or x[2]<x[3] or x[3]<x[4] or x[4]<x[5]) else x[0], axis = 1)
    
    df_new['VALIDATION'] = df_new['VALIDATION'].map(lambda x: x.strip(';'))
    
    return df_new

def aggregate_level(df, mapping_select, mapping_check_level, mapping_value_calculated = False):
    '''aggregate by different combination of variables, return all dfs in one dictionary
    If there is mapping_value_calculated , also add calculated value'''
    df_dict = {}
    for i, index_list in mapping_check_level.items():
            
        column_variable = [mapping_select['variable_date']] + [mapping_select['variable'][i] for i in index_list]
        
        value_list = [
            mapping_select['value'][key] 
            for key in mapping_select['value'] 
            if key != 'custom value' and mapping_select['value'][key]
        ]+ mapping_select['value']['custom value']
        
        df_i = df.groupby(column_variable, as_index=False)[value_list].sum()
        
        if mapping_value_calculated:
            df_i = value_calculation(df_i, mapping_select)
        
        df_i = df_i.replace([np.inf, -np.inf], np.nan)
        df_dict[i] = df_i
    
    return df_dict


def aggregate_variation(df, mapping_select, mapping_value_calculated = False, interval = 1, no_std_threshold = 3, recent_day_threshold = 7):
    '''given an aggregated df, return a variation table with mean, sd, z-scroe, and an invalid table from value_variation()
    If mapping_value_calculated , also find variation of calculated value'''

    column_date = mapping_select['variable_date']
    column_value = [
        mapping_select['value'][key] 
        for key in mapping_select['value'] 
        if key != 'custom value' and mapping_select['value'][key]
    ] + mapping_select['value']['custom value']
    column_variable = [i for i in df.columns if i in mapping_select['variable']]
    
    ## split date range into intervals, [start date, end date, interval]
    date_list = day_intervals(df[column_date].min(), df[column_date].max(), interval, reverse = True)
    date_list = [item for item in date_list if item[-1] == interval] ## remove the last interval if it's incomplete 
    
    ## filter and aggragate by intervals
    df_agg = df[df[column_date] >= date_list[-1][1]] ## remove dates from the incomplete interval
    df_agg[['MAX DATE', 'MIN DATE']] = df_agg[[column_date]].apply(
        (lambda x: [item[0:2] for item in date_list if x[0] <= item[0] and x[0] >= item[1]][0]),
        axis=1, result_type='expand'
    )
    df_agg = df_agg.groupby(
        ['MIN DATE', 'MAX DATE'] + column_variable, as_index=False)[column_value].sum()
    df_agg = df_agg[df_agg[column_value].apply(lambda x: sum(x.fillna(0)), axis = 1) >= 0]
    
    df_agg = value_validation(df_agg, mapping_select)
    df_filter = df_agg[df_agg['VALIDATION'] == '']
    df_invalid = df_agg[df_agg['VALIDATION'] != '']                                                
                                                    
    if mapping_value_calculated:
        column_before = df_filter.columns
        df_filter = value_calculation(df_filter, mapping_select)
        column_value = column_value + [
            i for i in df_filter.columns if i not in column_before] ## new calculated columns
    
    ## melt
    df_melt = pd.melt(
        df_filter, 
        id_vars = ['MIN DATE', 'MAX DATE'] + column_variable, value_vars = column_value,
        var_name='VALUE NAME', value_name = 'VALUE'
    )
    df_melt = df_melt[~df_melt['VALUE'].isnull()] ## calculated maybe pd.nan when divided by 0
    
    ## mean and std
    df_mean = df_melt.groupby(
        column_variable+['VALUE NAME'], as_index=False).agg({'VALUE': ['mean','std']})
    df_mean.columns = column_variable + ['VALUE NAME', 'MEAN', 'STD']
    
    df_final = pd.merge(df_melt, df_mean, on = column_variable+['VALUE NAME'], how = 'left')
    df_final['Z-SCORE'] = df_final[['VALUE','MEAN', 'STD']].apply(lambda x: (x[0]-x[1])/x[2], axis = 1)
    df_final['OUTLIER'] = df_final['Z-SCORE'].map(lambda x: "!" if abs(x)>no_std_threshold else "")
    
    ## order
    recent = datetime.date(datetime.today() - timedelta(days = recent_day_threshold)) #.strftime('%Y-%m-%d')


    df_final['RECENT'] = df_final['MAX DATE'].map(lambda x: '!' if x >= recent else '')
    df_final['DATE INTERVAL'] = interval
    df_final['ORDER'] = df_final['VALUE NAME'].map(lambda x: column_value.index(x))
    df_final = df_final.sort_values(
        ['ORDER', 'MAX DATE'],
        ascending = [True, False]
    )
    df_final_ordered = df_final[
        ['RECENT', 'DATE INTERVAL', 'MIN DATE', 'MAX DATE'] + 
        column_variable + 
        ['VALUE NAME', 'MEAN', 'STD', 'VALUE', 'Z-SCORE', 'OUTLIER']
    ]
    
    df_invalid['RECENT'] = df_invalid['MAX DATE'].map(lambda x: '!' if x >= recent else '')
    df_invalid['DATE INTERVAL'] = interval
    df_invalid = df_invalid.sort_values(
        ['MAX DATE'],
        ascending = [False]
    )
    df_invalid_ordered = df_invalid[['RECENT', 'DATE INTERVAL']+[i for i in df_invalid.columns if i not in  ['RECENT', 'DATE INTERVAL']]]

    return df_final_ordered.replace([np.inf, -np.inf], np.nan), df_invalid_ordered

def check_variation(
    df, mapping_select, mapping_check_level, 
    mapping_value_calculated = False, mapping_check_variation_interval = [1], mapping_no_std_threshold = 3, mapping_recent_day_threshold = 7
):
    '''run aggregate_level() to get a dictionary of agg dfs, then run aggregate_variation() for each df,
    also return a table of all outliers'''

    lowest_level = [
        k for k,v in mapping_check_level.items() 
        if len(v) == max([len(v) for v in mapping_check_level.values()])]

    df_dict = aggregate_level(df, mapping_select, mapping_check_level, mapping_value_calculated = None)
    df_result_dict = {}
    df_outlier = pd.DataFrame()

    for level, df_agg in df_dict.items():
        df_result = pd.DataFrame()
        
        for interval in mapping_check_variation_interval:
            df_result_single, df_invalid_single = aggregate_variation(
                df_agg, mapping_select, 
                mapping_value_calculated, interval = interval, no_std_threshold = mapping_no_std_threshold, recent_day_threshold = mapping_recent_day_threshold)
            df_result = pd.concat([df_result, df_result_single], axis = 0)
            
            if interval == min(mapping_check_variation_interval) and level in lowest_level:
                df_invalid = df_invalid_single
        
        df_result_dict[level] = df_result

        df_outlier_single = df_result[df_result['OUTLIER'] == '!']
        df_outlier_single['BREAKDOWN'] = level
        df_outlier = pd.concat([df_outlier, df_outlier_single], axis = 0)
    

    df_outlier = df_outlier[
        ['BREAKDOWN', 'RECENT', 'DATE INTERVAL', 'MIN DATE', 'MAX DATE'] + 
        [i for i in df_outlier.columns if i not in ['BREAKDOWN', 'RECENT', 'DATE INTERVAL', 'MIN DATE', 'MAX DATE','VALUE NAME', 'MEAN', 'STD', 'VALUE', 'Z-SCORE', 'OUTLIER']] + 
        ['VALUE NAME', 'MEAN', 'STD', 'VALUE', 'Z-SCORE']
    ]

    df_result_dict['Summary of Outlier'] = df_outlier
    df_result_dict['Invaild rows'] = df_invalid

    return df_result_dict
                                                    
# def aggregate_day_comparison(df, mapping_select, mapping_value_calculated = None, days = 1):
    
#     column_date = mapping_select['variable_date']
#     column_value = [
#         mapping_select['value'][key] 
#         for key in mapping_select['value'] 
#         if key != 'custom value' and mapping_select['value'][key]
#     ] + mapping_select['value']['custom value']
#     column_variable = [i for i in df.columns if i in mapping_select['variable']]

    
#     date_to = df[column_date].max()
#     date_from = date_to - timedelta(days=days-1)
#     date_to_comparison = date_from - timedelta(days=1)
#     date_from_comparison = date_to_comparison - timedelta(days=days-1)
    
#     df_select = df[df[column_date] >= date_from].groupby(column_variable, as_index=False)[column_value].sum()
#     df_comparison = df[(df[column_date] >= date_from_comparison) & (df[column_date] <= date_to_comparison)
#                       ].groupby(column_variable, as_index=False)[column_value].sum()
    
#     if mapping_value_calculated:
#         df_select = value_calculation(df_select, mapping_select, mapping_value_calculated)
#         df_comparison = value_calculation(df_comparison, mapping_select, mapping_value_calculated)
#         column_value = mapping_value_calculated + column_value
    
#     df_select_melt = pd.melt(
#         df_select, 
#         id_vars = column_variable, value_vars = column_value,
#         var_name='VALUE NAME', value_name = 'VALUE'
#     )
#     df_comparison_melt = pd.melt(
#         df_comparison, 
#         id_vars = column_variable, value_vars = column_value,
#         var_name='VALUE NAME', value_name = 'VALUE'
#     )
        
#     df_final = pd.merge(
#         df_select_melt, df_comparison_melt, 
#         left_on = column_variable+['VALUE NAME'], right_on = column_variable+['VALUE NAME'], 
#         how = 'outer', suffixes=('', ' COMPARISON')).sort_values(column_variable).fillna(0)
    
#     df_final = df_final[(df_final['VALUE'] != 0) | (df_final['VALUE COMPARISON'] != 0)]
    
#     df_final['DAYS'] = days
#     if days == 1:
#         df_final['DATE RANGE'] = date_to.strftime('%Y-%m-%d')
#     else:
#         df_final['DATE RANGE'] = date_from.strftime('%Y-%m-%d') + ' to ' + date_to.strftime('%Y-%m-%d')
    
#     ## calcualte change of value
#     df_final['VALUE %'] = df_final[['VALUE', 'VALUE COMPARISON']].apply(
#         lambda x: 0 if x[0] == x[1] else (
#             None if x[1] == 0 else x[0]/x[1]-1), axis = 1)
    
#     ## order
#     df_final['ORDER'] = df_final['VALUE NAME'].map(lambda x: column_value.index(x))
#     df_final = df_final.sort_values(
#         ['DAYS'] + ['ORDER'] + column_variable, 
#         ascending = [True] + [False] + [True]*len(column_variable)
#     )
    
#     df_final_ordered = df_final[
#         ['DAYS', 'DATE RANGE'] + 
#         column_variable + 
#         ['VALUE NAME', 'VALUE', 'VALUE COMPARISON', 'VALUE %']
#     ]
    
#     return df_final_ordered.replace([np.inf, -np.inf], np.nan)
        
# def check_change(
#     df, mapping_select, mapping_check_level,
#     mapping_value_calculated = None, mapping_check_change_days = [1]
# ):
    
#     df_dict = aggregate_level(df, mapping_select, mapping_check_level, mapping_value_calculated = None)
#     df_result_dict = {}
    
#     for i, df_agg in df_dict.items():
#         df_result = pd.DataFrame()
#         for days in mapping_check_change_days:
#             df_result_single = aggregate_day_comparison(df_agg, mapping_select, mapping_value_calculated, days = days)
#             df_result = pd.concat([df_result, df_result_single], axis = 0)
            
#         df_result = df_result.replace([np.inf, -np.inf], np.nan)
#         df_result_dict[i] = df_result
        
#     return df_result_dict

def aggregate_count(df, mapping_select, mapping_check_variable_count):
    
    df['ROW COUNT'] = 1
    column_date =  mapping_select['variable_date']
    
    df_result = pd.DataFrame()
    for i in mapping_check_variable_count:
        variable = mapping_select['variable'][i]
        
        df[variable] = df[variable].fillna('* NULL *')
        df_i = df.groupby([variable], as_index=False).agg({
            'ROW COUNT':sum,
            column_date: [min, max]
        })
        
        df_i.columns = ['VARIABLE', 'ROW COUNT', 'MIN DATE', 'MAX DATE']
        df_i['VARIABLE NAME'] = variable
        df_i = df_i[['VARIABLE NAME', 'VARIABLE', 'ROW COUNT', 'MIN DATE', 'MAX DATE']].sort_values('ROW COUNT', ascending = True)
        
        df_result = pd.concat([df_result, df_i], axis = 0)
    
    df_result['NO OF DATE'] = df_result[['MIN DATE', 'MAX DATE']].apply(lambda x: (x[1] - x[0]).days + 1, axis = 1)
    return df_result