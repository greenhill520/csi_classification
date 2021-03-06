'''A module that contains df linking functions from CSI,
as well as data preprocessing functions. There are functions
decimation, smoothing.'''

import pandas as pd
from scipy.signal import savgol_filter
from matplotlib import pyplot as plt

# ---------- GROUPING ----------
def split_csi(big_df, num_tones=56):
    '''Returns an array of CSI df, by num_tones amplitudes
     in every df. The opposite of concat_csi (...).
     Accepts Big_df in which are written to a string
     num_tones * 4 = 224 CSI subcarriers.'''
    df_lst = []
    for k in range(4):
        one_df = big_df[[i+k*num_tones for i in range(0, num_tones)]]
        one_df.columns = [i for i in range(0, num_tones)]
        one_df = one_df.assign(object_type=big_df['object_type'].values)
        df_lst.append(one_df)
    return df_lst


def concat_csi(df_lst):
    '''Returns the generic DataFrame in which are written
     row 56 * 4 = 224 CSI subcarriers'''
    type_ds = df_lst[0]['object_type']
    for i in range(len(df_lst)):
        df_lst[i] = df_lst[i].drop(['object_type'], axis=1)
    big_df = pd.concat(df_lst, axis=1)
    big_df.columns = [i for i in range(0, len(df_lst)*df_lst[0].shape[1])]
    return big_df.assign(object_type=type_ds)


# ---------- CHANGE ----------
def down(df, *df_lst):
    '''Lowers csi amplitudes by subtracting from each packet
     minimum value. It is recommended to use individually.
     to packets from each path, and not to the glued df.'''
    object_type = df['object_type']
    min_col = df.drop(['object_type'], axis=1).min(axis=1)
    df_down = df.drop(['object_type'], axis=1).sub(min_col, axis=0)
    df_down['object_type'] = object_type
    if len(df_lst) == 0:
        return df_down
    else:
        df_down_lst = [df_down]
        for df in df_lst:
            min_col = df.drop(['object_type'], axis=1).min(axis=1)
            df_down = df.drop(['object_type'], axis=1).sub(min_col, axis=0)
            df_down['object_type'] = object_type
            df_down_lst.append(df_down)
        return df_down_lst


def smooth_savgol(df, *df_lst, win_width=9, polyorder=3):
    '''Smoothes csi. Not recommended
     apply to glued df. Filter applied
     Savitsky-Golay.'''
    smoothed = savgol_filter(
        df.drop(columns='object_type'), win_width, polyorder)
    if len(df_lst) == 0:
        return pd.DataFrame(smoothed).assign(object_type=df['object_type'].values)
    else:
        smoothed_lst = [pd.DataFrame(smoothed).assign(object_type=df['object_type'].values)]
        for df in df_lst:
            smoothed = savgol_filter(df.drop(columns='object_type'), win_width, polyorder)
            smoothed_lst.append(pd.DataFrame(smoothed).assign(object_type=df['object_type'].values))
        return smoothed_lst

def smooth(df, *df_lst, window=5):
    '''Smoothes csi.'''
    smoothed = df.drop(columns='object_type').T.rolling(window, min_periods=1).mean().T
    if len(df_lst) == 0:
        return smoothed.assign(object_type=df['object_type'].values)
    else:
        smoothed_lst = [smoothed.assign(object_type=df['object_type'].values)]
        for df in df_lst:
            smoothed = df.drop(columns='object_type').T.rolling(5, min_periods=1).mean().T
            smoothed_lst.append(smoothed.assign(object_type=df['object_type'].values))
        return smoothed_lst


# ---------- SCREENING ----------
def cut_csi(df, number, shuffle: bool=True):
    '''Returns the dataframe in which is left
     number of packets for each object. Shuffle -
     Choose packages randomly. Only for
     glued df with shuffle = True!'''
    df_lst = []
    object_types = df['object_type'].unique()
    for obj_type in object_types:
        obj_df = df[df['object_type'] == obj_type] 
        if shuffle:
            obj_df = obj_df.sample(frac=1).reset_index(drop=True)   
        df_lst.append(obj_df.head(number))
    return pd.concat(df_lst, axis=0).reset_index(drop=True)


def decimate_one(df, k, *k_lst):
    '''Deletes every kth row. You can delete any
     multiple lines from df passing multiple
     arguments. Multiple lines may intersect, their repetitions
     will be deleted before drop. Thus, when transmitting
     (df, 2, 2) to the function, 1/2 will remain from the original df.'''
    drop_index_lst = [i for i in range(0, df.shape[0], k)]
    for k in k_lst:
        drop_index_lst += [i for i in range(0, df.shape[0], k)]
    drop_index_lst = list(set(drop_index_lst))
    return df.drop(drop_index_lst).reset_index(drop=True)


def decimate_every(df, k, *k_lst):
    '''Deletes every kth row. Every time after removal
     rows from df in it are reset indices. Thus, when
     passing (df, 2, 2) to the function, 1/4 will remain from the original df.'''
    drop_index_lst = [i for i in range(0, df.shape[0], k)]
    df = df.drop(drop_index_lst).reset_index(drop=True)
    for k in k_lst:
        drop_index_lst = [i for i in range(0, df.shape[0], k)]
        df = df.drop(drop_index_lst).reset_index(drop=True)
    return df