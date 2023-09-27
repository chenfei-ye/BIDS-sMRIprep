
import os, sys, shutil, time, glob
import nibabel as nib
import argparse
import numpy as np
import json
import pandas as pd
from dppd import dppd 
dp, X = dppd() 

def read_json_file(json_file, encoding='utf-8'):
    """
    read json file
    :param json_file:
    :param encoding:
    :return:
    """
    if not os.path.exists(json_file):
        print('json file %s not exist' % json_file)
        return None

    with open(json_file, 'r', encoding=encoding) as fp:
        out_dict = json.load(fp)

    return out_dict


def summarize_lesion_volume(sub_path_ls, json_name):
    """
    pool individual lesion volume json files into a group-level dataframe
    :param sub_path_ls: glob.glob(os.path.join(main_path, 'sub-*'))
    :param json_name: filename of input json file
    :return: a group-level dataframe
    """
    df_all= pd.DataFrame()
    for i in range(len(sub_path_ls)):
        sub_path = sub_path_ls[i]
        subname = os.path.basename(sub_path)
        json_path = os.path.join(sub_path, json_name)
        json_file = read_json_file(json_path)
        df_all[subname] = pd.Series(json_file)

    df_all = dp(df_all).transpose().pd
    return df_all


def summarize_parcel_volume(sub_path_ls, csv_name):
    """
    pool individual lesion volume json files into a group-level dataframe
    :param sub_path_ls: glob.glob(os.path.join(main_path, 'sub-*'))
    :param json_name: filename of input json file
    :return: a group-level dataframe
    """
    df_all= pd.DataFrame()
    for i in range(len(sub_path_ls)):
        sub_path = sub_path_ls[i]
        subname = os.path.basename(sub_path)
        csv_path = os.path.join(sub_path, csv_name)
        csv_file = pd.read_csv(csv_path, index_col="region_name")
        # print(csv_file)
        # print(csv_file.shape)
        df_all[subname] = pd.Series(csv_file.loc[:,'volume_mm3'])

    df_all = dp(df_all).transpose().pd
    return df_all


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="pool individual DTI parameter json files into a group-level dataframe",
                                     epilog="Copyright © 2016 - 2021 MindsGo Life Science and Technology Co. Ltd."
                                            " All Rights Reserved")

    parser.add_argument('bids_dir', help='The directory with the input dataset '
                        'formatted according to the BIDS standard.')

    parser.add_argument('analysis_level', help='Level of the analysis that will be performed. '
                        'Multiple participant level analyses can be run independently '
                        '(in parallel) using the same output_dir.',
                        choices=['participant', 'group'])
    parser.add_argument("-mode", metavar="parcel|lesion",
                        help="Which type of volume calculation to run.\n"
                             "'parcel' [DEFAULT]: brain parcel defined in Brainlabel L4.\n"
                             "'lesion': T1 infarct lesion. \n"
                             "multiple modes can be switched on simultaneously by seperating by comma",
                        default="parcel")

    
    args = parser.parse_args()
    modes_ls = args.mode.split(",")
    start = time.time()

    smri_prep_dir = os.path.join(args.bids_dir, 'derivatives', 'smri_prep')
    sub_path_ls = glob.glob(os.path.join(smri_prep_dir, 'sub-*'))
    sub_path_ls.sort()
    num_sub = len(sub_path_ls)
    print('Detected number of subjects: '+ str(num_sub))

    if 'lesion' in modes_ls: 
        df_all_lesion = summarize_lesion_volume(sub_path_ls, 'volume_lesion.json')
        df_all_lesion.to_csv(os.path.join(smri_prep_dir, 'Group_lesion_volume.csv'))

    if 'parcel' in modes_ls:
        df_all_volume = summarize_parcel_volume(sub_path_ls, 'volume_L4_regions.csv')
        df_all_volume.to_csv(os.path.join(smri_prep_dir, 'Group_parcel_volume.csv'))

    end = time.time()
    running_time = end - start
    print('running time: {:.0f}min {:.0f}sec'.format(running_time//60, running_time % 60))