import pandas as pd
import time
import os

from mappings import *

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

def create_folders():

    # Get current working directory
    cwd = os.getcwd()

    # Define paths
    data_path = f'{cwd}/Data'
    output_path = f'{cwd}/Output'

    path_list = [data_path, output_path]

    # Create folders if they do not exist
    for path in path_list:
        if not os.path.exists(path):
            os.makedirs(path)

def read_xlsx():

    xls = pd.ExcelFile('Data/Task-3-BOSS_Eyewear_SR23_Final-Data.xlsx')
    ga_data = pd.read_excel(xls, 'Campaign GA Data', engine='openpyxl', usecols=['Source / Medium', 'Ad Content', 'Keyword', 'Date', 'Country', 'Sessions', 'Session Quality', 'New Customers', 'Bounces', 'Add to Cart', 'Sales (LC Brutto)', 'Turnover (Brutto)', 'Country Short'])
    performance_data = pd.read_excel(xls, 'Campaign Performance Data', engine='openpyxl', usecols=['Date', 'Market', 'Platform', 'Ident-Thema', 'Phase', 'Campaign Name', 'Gender', 'Target_Group', 'Ad Name', 'Ad Format', 'Static/Video', 'ImpressionsVideo', "Impressions", "Mediabudget Video", "Mediabudget", "Clicks", "Video Views (all)", "50% Watched", "100% Watched", "Page Likes", "Post Likes", "Post Comments", "Post Shares", "Post Saves", "Link Clicks", "Page View", "ATC", "Order", "Revenue", "Engagement", "Post Reactions"])

    return ga_data, performance_data

def read_pickle(df):

    path = f"Data/{df}.pkl"
    df = pd.read_pickle(path)

    return df

def store_pickle(df, name):

    path = f"Data/{name}.pkl"
    df.to_pickle(path)

def cleaning_ga_data(df):

    # Drop any rows with nan
    df = df.dropna().copy()

    # Removing any duplicate rows
    df = df.drop_duplicates().copy()

    # Cleaning country names
    df['Country Short Clean'] = df['Country'].map(country_dict)
    
    # Checking for errors in raw data
    country_checking(df)

    # Dropping old country column and renaming
    df = df.drop(columns=['Country', 'Country Short'])
    df = df.rename(columns={'Country Short Clean': 'Market'})

    # Creating Platform column
    df['Platform'] = df['Source / Medium'].apply(lambda x: 'YT' if 'youtube' in x else ('IG' if 'instagram' in x else ''))
    df = df.drop(columns=['Source / Medium'])

    # Finding Ad Name from Keyword
    df['Ad Name'] = df['Keyword'].apply(lambda s: s.split('_', 1)[1] if '_' in s else '')

    # Mapping GA data onto the corresponding target audience
    df['Target Group'] = 'engager+lal'

    # Converting Date column to proper datetime
    df['Date'] = pd.to_datetime(df['Date'], format='%Y%m%d')

    return df

def cleaning_performance_data(df):

    # Trimming any extra '_' characters from the end of the 'Campaign Name' column
    df['Campaign Name'] = df['Campaign Name'].str.rstrip('_')

    # Rename Target_Group to Target Group
    df = df.rename(columns={'Target_Group': 'Target Group Original'})

    # Replace SL with SI in Market column
    df['Market'] = df['Market'].replace('SL', 'SI')

    # Creating Platform column
    df['Platform'] = df['Platform'].apply(lambda x: 'YT' if 'YT' in x else ('IG' if 'IG' in x else ''))

    # Cleaning Phase column
    df['Phase'] = df['Phase'].replace('eyewear_guaranteed', 'Eyewear')
    df['Phase'] = df['Phase'].str.title()

    # Removing any duplicate rows
    df = df.drop_duplicates().copy()

    # Grouping by the following columns and summing the rest
    df = df.groupby(['Date', 'Market', 'Platform', 'Ident-Thema', 'Phase', 'Campaign Name', 'Target Group Original', 'Gender', 'Ad Name', 'Ad Format', 'Static/Video']).sum().reset_index()

    # Extract year and ISO week number
    df['Final Week'] = df['Date'].apply(lambda x: f"{x.year}/KW{x.isocalendar()[1]}")

    # Create a new column for new Ad Format, which only takes the first section
    df['Ad Format New'] = df['Ad Name'].apply(lambda x: x.split('_', 1)[0])

    # Fill any Nan in Ad Format new with Ad Name value
    df['Ad Format New'] = df['Ad Format New'].fillna(df['Ad Name'])

    # If Ad Format New contains 'carouselad' then make new column with 'Static' if not 'Video'
    df['Static/Video'] = df['Ad Format New'].apply(lambda x: 'Static' if 'carouselad' in x else 'Video')

    # Make new gender column
    df['Gender New'] = df['Ad Name'].apply(lambda x: 'Female' if '_female' in x else ('Male' if '_male' in x else 'Unisex'))

    # If Ad Name contains '_h' then new column for horizontal, if it contains '_v' then new column for vertical
    df['Ad Orientation'] = df['Ad Name'].apply(lambda x: 'Horizontal' if '_h' in x else ('Vertical' if '_v' in x else ''))

    # If Ad Name contains '15' then new column for Duration with this in
    df['Ad Duration (s)'] = df['Ad Name'].apply(lambda x: '15' if '15' in x else ('30' if '30' in x else ('60' if '60' in x else '')))

    # If column contains 16x9 or 9x16 then new column for Dimension with this in
    df['Ad Dimension'] = df['Ad Name'].apply(lambda x: '16x9' if '16x9' in x else ('9x16' if '9x16' in x else ''))

    # Define your dictionaries and columns
    dict_maps = [model_dict, type_dict, target_group_dict]
    source_cols = ['Ad Name', 'Ad Name', 'Target Group Original'] 
    target_cols = ['Model', 'Type', 'Target Group']

    # Loop through and apply mapping and filtering
    for src, tgt, dmap in zip(source_cols, target_cols, dict_maps):
        map_values_and_filter(df, src, tgt, dmap)

    return df

def map_values(value, mapping_dict):

    for key, mapped_value in mapping_dict.items():

        if key in value:
            return mapped_value
        
    return value

def map_values_and_filter(df, source_col, target_col, dict_map):

    # Convert the source column to lowercase
    df[source_col] = df[source_col].str.lower()
    
    # Map values and filter based on dictionary values
    df[target_col] = df[source_col].apply(lambda x: map_values(x, dict_map))

    valid_values = list(set(dict_map.values()))

    df[target_col] = df[target_col].where(df[target_col].isin(valid_values), '')

def categorise_country(country):

    cee_countries = ["PL", "SI", "TR"]
    other_countries = ["DE", "ES", "GB", "US", "MX", "FR"]

    if country in cee_countries:
        return "CEE"
    elif country in other_countries:
        return country
    else:
        return "Others"

def country_checking(df):

    # Defining dataframe
    df = df[['Country', 'Country Short', 'Country Short Clean']].copy()

    # Remove duplicate rows
    df = df.drop_duplicates()

    # Sorting by country name
    df = df.sort_values(by=['Country'])

    # Filter for rows where 'Country Short' and 'Country Short Clean' do not match
    df = df[df['Country Short'] != df['Country Short Clean']]

    # Filter for rows where 'Country' and 'Country Short' do not match
    df = df[df['Country'] != df['Country Short']]

    # Resetting index
    df = df.reset_index(drop=True)

    # Printing instances of inconsistent country names
    print('-' * 75)
    print(f'Unique country errors resolved: {len(df)}')

def post_processing(df):

    df['Final Country'] = df['Market'].apply(categorise_country)

    # rename target group original to target group
    df = df.rename(columns={'Target Group': 'Target Group New',
                            'Target Group Original': 'Target Group'})

    # Drop any duplidate rows
    df = df.drop_duplicates().copy()

    return df

def main():

    start_time = time.time()

    # Setting up directories if do not already exist
    create_folders()

    print('-' * 75)
    print('Loading data...')
    print('-' * 75)

    # If there is a .pkl file in the Data folder then the data will be read from there, otherwise the data will be read from the Excel file.
    # To re-run from Excel file, the .pkl files must be deleted first.

    try:

        if not os.path.exists('Data/ga_data.pkl'):

            # Updating data from Excel
            ga_data, performance_data = read_xlsx()

            store_pickle(ga_data, 'ga_data')
            store_pickle(performance_data, 'performance_data')

            print('Source .xlsx data loaded successfully!')

        else:

            # Quickloading existing data in pickle format
            ga_data = read_pickle('ga_data')
            performance_data = read_pickle('performance_data')

            print('Source .pkl data loaded successfully!')

    except:

        print('No files found. Please check the Data folder and try again.')
        print('-' * 75)
        quit()

    # Cleaning data steps for each source
    ga_data = cleaning_ga_data(ga_data)
    performance_data = cleaning_performance_data(performance_data)

    # Stitching dataframes together
    merged_df = pd.merge(performance_data, ga_data, how='outer', on=['Date', 'Platform', 'Market', 'Ad Name', 'Target Group'])

    # Final bits of cleaning ahead of export
    ga_data = post_processing(ga_data)
    performance_data = post_processing(performance_data)
    merged_df = post_processing(merged_df)

    # Reordering columns
    ga_data = ga_data[['Date', 'Market', 'Final Country', 'Platform', 'Ad Content', 'Keyword', 'Ad Name', 'Target Group New', 'Sessions', 'Session Quality', 'New Customers', 'Bounces', 'Add to Cart', 'Sales (LC Brutto)', 'Turnover (Brutto)']]
    performance_data = performance_data[['Date', 'Final Week', 'Market', 'Final Country', 'Platform', 'Ident-Thema', 'Phase', 'Campaign Name', 'Ad Name', 'Ad Format', 'Ad Format New', 'Target Group', 'Target Group New', 'Model', 'Type', 'Static/Video', 'Ad Orientation', 'Ad Duration (s)', 'Ad Dimension', 'Gender', 'Gender New', 'ImpressionsVideo', 'Impressions', 'Mediabudget Video', 'Mediabudget', 'Clicks', 'Video Views (all)', '50% Watched', '100% Watched', 'Page Likes', 'Post Likes', 'Post Comments', 'Post Shares', 'Link Clicks', 'Page View', 'ATC', 'Order', 'Revenue', 'Engagement', 'Post Reactions']]
    merged_df = merged_df[['Date', 'Final Week', 'Market', 'Final Country', 'Platform', 'Ident-Thema', 'Phase', 'Campaign Name', 'Ad Name', 'Ad Format', 'Ad Format New', 'Target Group', 'Target Group New', 'Model', 'Type', 'Static/Video', 'Ad Orientation', 'Ad Duration (s)', 'Ad Dimension', 'Gender', 'Gender New', 'Keyword', 'Ad Content', 'ImpressionsVideo', 'Impressions', 'Mediabudget Video', 'Mediabudget', 'Clicks', 'Video Views (all)', '50% Watched', '100% Watched', 'Page Likes', 'Post Likes', 'Post Comments', 'Post Shares', 'Link Clicks', 'Page View', 'ATC', 'Order', 'Revenue', 'Engagement', 'Post Reactions', 'Sessions', 'Session Quality', 'New Customers', 'Bounces', 'Add to Cart', 'Sales (LC Brutto)', 'Turnover (Brutto)']]

    # Source column if merged_df column keyword is not null and ident-theme is null then 'GA' else 'Performance'
    merged_df['Source'] = merged_df.apply(lambda x: 'GA Only' if pd.notnull(x['Keyword']) and pd.isnull(x['Ident-Thema']) else 'Performance Only', axis=1)
    
    # If keyword column is not null and ident-theme is not null then mark 'Combined' in source column
    merged_df['Source'] = merged_df.apply(lambda x: 'Combined' if pd.notnull(x['Keyword']) and pd.notnull(x['Ident-Thema']) else x['Source'], axis=1)

    # Put source column as the first column of merged_df
    cols = merged_df.columns.tolist()
    cols = cols[-1:] + cols[:-1]
    merged_df = merged_df[cols]

    # Create timestamp
    timestamp = time.strftime("%Y%m%d_%H%M")

    # Export to Excel using writer for multiple sheets
    file_name = f'Output/{timestamp}_HB_Clean_Output.xlsx'

    with pd.ExcelWriter(file_name, engine='xlsxwriter', datetime_format='dd/mm/yy') as writer:

        merged_df.to_excel(writer, sheet_name='Final Merged Data', index=False)
        performance_data.to_excel(writer, sheet_name='Performance Data (Clean)', index=False)
        ga_data.to_excel(writer, sheet_name='GA Data (Clean)', index=False)

    # Execution time
    print('-' * 75)
    print(f'Execution time: {round(time.time() - start_time, 2)} seconds')
    print('-' * 75)


if __name__ == '__main__':

    main()
