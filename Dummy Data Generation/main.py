import pandas as pd
import numpy as np
import datetime
import time
import os

np.random.seed(1)

from input import *

def df_build_from_input():

    # Extracting keys as lists
    countries = list(performance_dict['Country'].keys())
    channels = list(performance_dict['Channel'].keys())
    categories = list(performance_dict['Category'].keys())
    markets = list(performance_dict['Market'].keys())
    products = list(performance_dict['Product'].keys())

    # Creating a DataFrame from all possible combinations
    df = pd.DataFrame([
        (country, channel, category, market, product, performance_dict['Country'][country][0], performance_dict['Category'][category][0], performance_dict['Market'][market][0], performance_dict['Product'][product][0])
        for country in countries
        for channel in channels
        for category in categories
        for market in markets
        for product in products
        ], columns=['Country', 'Channel', 'Category', 'Market', 'Product', 'country_split', 'category_split', 'market_split', 'product_split'])
    
    return df

def df_apply_weeks(df):

    # Build out the dataframe to have the number of defined weeks
    df = pd.concat([df]*weeks, ignore_index=True)
    df['Week'] = df.groupby(['Country', 'Channel', 'Category', 'Market', 'Product']).cumcount() + 1

    # Assign week 1 to the defined start date and increment the date by 7 days for each week
    df['Date'] = pd.to_datetime(start_date) + pd.to_timedelta(df['Week'] - 1, unit='W')

    return df

def df_apply_splits(df):

    # Apply channel splits to the dataframe
    df['channel_split'] = df['Channel'].apply(lambda x: float(performance_dict['Channel'][x][0]) * np.random.uniform(0.8, 1.1))

    # Normalise the splits so that they always sum to 100%
    df['channel_split'] = df.groupby(['Country', 'Category', 'Market', 'Product', 'Week'], group_keys=False)['channel_split'].apply(lambda x: x / x.sum())
    df['country_split'] = df.groupby(['Channel', 'Category', 'Market', 'Product', 'Week'], group_keys=False)['country_split'].apply(lambda x: x / x.sum())
    df['category_split'] = df.groupby(['Country', 'Channel', 'Market', 'Product', 'Week'], group_keys=False)['category_split'].apply(lambda x: x / x.sum())
    df['market_split'] = df.groupby(['Country', 'Category', 'Channel', 'Product', 'Week'], group_keys=False)['market_split'].apply(lambda x: x / x.sum())
    df['product_split'] = df.groupby(['Country', 'Category', 'Market', 'Channel', 'Week'], group_keys=False)['product_split'].apply(lambda x: x / x.sum())

    return df


def df_weekly_spend(df):

    # make a df of the total spend for each week
    df_spend = df.groupby(['Week', 'Country', 'country_split']).size().reset_index(name='count')
    df_spend.drop(['count'], axis=1, inplace=True)

    df_spend['Spend'] = total_spend * df_spend['country_split']
    df_spend.drop(['country_split'], axis=1, inplace=True)

    seed = 0

    # for loop country in df filter df by country
    for country in list(performance_dict['Country'].keys()):

        df_country = df_spend[df_spend['Country'] == country]
        df_spend = df_spend[df_spend['Country'] != country]

        seed = seed + 1
        np.random.seed(seed)

        # new column for variable factor which is random value between 0.8 and 1.2
        df_country['variable_factor'] = np.random.uniform(0.8, 1.2, weeks)

        # normalise the variable factor between 0 and 1
        df_country['variable_factor'] = (df_country['variable_factor'] / df_country['variable_factor'].sum())

        # apply the variable factor to the total spend
        df_country['Spend'] = df_country['Spend'] * df_country['variable_factor']

        # drop variable factor
        df_country.drop(['variable_factor'], axis=1, inplace=True)

        #df append
        df_spend = pd.concat([df_spend, df_country], ignore_index=True)

        # merge the df_spend with the original df on country and week, replace the spend column with the new spend column
        df = pd.merge(df, df_spend, on=['Country', 'Week'], how='left')

        try:
            df['Spend'] = df['Spend_y']
            df.drop(['Spend_y', 'Spend_x'], axis=1, inplace=True)

        except:
            pass

    return df

def df_calculations(df):

    # Calculate the spend, CPC, CTR, Clicks, Impressions and Conversions
    df['Spend'] = df['Spend'] * df['channel_split'].astype(float) * df['category_split'].astype(float) * df['market_split'].astype(float) * df['product_split'].astype(float)

    df['CPC'] = df['Channel'].apply(lambda x: float(performance_dict['Channel'][x][1]) * np.random.uniform(0.8, 1.1))
    df['CTR'] = df['Channel'].apply(lambda x: float(performance_dict['Channel'][x][2]) * np.random.uniform(0.8, 1.1))

    df['Clicks'] = df['Spend'] / df['CPC']
    df['Impressions'] = df['Clicks'] / (df['CTR'] / 100)
    df['Conversions'] = df['Clicks'] * np.random.uniform(0.01, 0.05)

    # apply random factor to ROI and SOM
    df['ROAS'] = roas
    df['SOM'] = som

    # for each row in df apply random factor to the ROAS and SOM
    for i in range(len(df)):
        df.loc[i, 'ROAS'] = roas * np.random.uniform(0.75, 1.25)
        df.loc[i, 'SOM'] = som * np.random.uniform(0.66, 1.33)

    return df

def df_cleanup(df):

    # Drop columns from df
    df.drop(['country_split', 'category_split', 'market_split', 'product_split', 'channel_split'], axis=1, inplace=True)

    return df

def df_fame_flow():

    # make a new df with the fame and flow metrics
    df = pd.DataFrame(list(fame_flow_dict.items()), columns=['Metric', 'Score'])

    # Build out the dataframe to have the number of defined weeks
    df = pd.concat([df]*weeks, ignore_index=True)
    df['Week'] = df.groupby(['Metric']).cumcount() + 1

    # Assign week 1 to the defined start date and increment the date by 7 days for each week
    df['Date'] = pd.to_datetime(start_date) + pd.to_timedelta(df['Week'] - 1, unit='W')

    seed = 0

    # for loop for each metric in df filter
    for metric in list(fame_flow_dict.keys()):

        # filter df by selected metric
        df_filt = df[df['Metric'] == metric]
        df = df[df['Metric'] != metric]

        seed = seed + 1

        # randomise the values of the metric
        df_filt['Score'] = df_filt['Score'] * np.random.uniform(0.85, 1.15, weeks)

        # append the filtered df back to the original df
        df = pd.concat([df, df_filt], ignore_index=True)

        # replace any values that are equal or greater than 1 with 0.99
        df.loc[df['Score'] >= 1, 'Score'] = 0.99

        # reorder columns to be metric, week, date, score
        df = df[['Metric', 'Week', 'Date', 'Score']]

    return df

def df_export(df, df2, file_name):

    print('Exporting data...')

    # get cwd
    file_path = os.getcwd()

    timestamp = datetime.datetime.fromtimestamp(time.time())
    timestampStr = timestamp.strftime("%Y%m%d")

    # excel writer multiple tabs for df1 and df2
    writer = pd.ExcelWriter(file_path + '\\' + file_name + ' - ' + timestampStr + '.xlsx', engine='xlsxwriter')

    df.to_excel(writer, sheet_name='Performance', index=False)
    df2.to_excel(writer, sheet_name='F-Metrics', index=False)

    writer.close()


def main():

    df = df_build_from_input()
    df = df_apply_weeks(df)
    df = df_apply_splits(df)
    df = df_weekly_spend(df)
    df = df_calculations(df)
    df = df_cleanup(df)

    df_ff = df_fame_flow()

    df_export(df, df_ff, "Dummy Dashboard Data")


if __name__ == '__main__':

    main()
