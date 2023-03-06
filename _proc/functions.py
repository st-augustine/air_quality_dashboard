def convert(dataframe, float_column, site_column,iteration):
    ''' 
    converts columns to the correct data format
    '''
    dataframe[float_column] = float(dataframe[float_column])
    dataframe[site_column] = iteration[site_column]
    return dataframe


def convert_to_float(dict):
    float(dict)
    return dict