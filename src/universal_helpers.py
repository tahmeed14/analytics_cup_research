import pandas as pd
import numpy as np
import json
import requests

from src.data_processing_helpers import *

# 1 From SkillCorner tutorials (convert time to seconds)
def time_to_seconds(time_str):
    """Reads in time (soccer/football minutes) in string format and then converts to seconds"""
    if time_str is None:
        return 90 * 60  # 120 minutes = 7200 seconds
    h, m, s = map(int, time_str.split(':'))
    return h * 3600 + m * 60 + s


# 2 Read JSON dynamic events from GitHub
def readEvents(match_list : list[int]) -> pd.DataFrame:
    """Reads in dynamic events data from SkillCorner GitHub as specifed by list of match ids"""

    assert type(match_list) == type([]), "match_list must be a list of integers"
    assert type(match_list[0]) == type(1), "match_list must be a list of integers"

    print("match_id:", match_list[0])
    output_df = pd.read_csv(f"https://raw.githubusercontent.com/SkillCorner/opendata/master/data/matches/{match_list[0]}/{match_list[0]}_dynamic_events.csv")

    # loop through the remaining matches, read them, and append to dataset (this only runs if there are more than 1 match in the match_list)
    if len(match_list) > 1:
        for id in match_list[1:]:
            print("match_id:", id)
            temp_df = pd.read_csv(f"https://raw.githubusercontent.com/SkillCorner/opendata/master/data/matches/{id}/{id}_dynamic_events.csv")

            assert output_df.shape[1] == temp_df.shape[1], "number of columns for appending dataset must be the same as output dataset"

            output_df = pd.concat([output_df, temp_df])

    assert len(output_df["match_id"].unique()) == len(match_list), "number of matches should be same as number of matches specified in the input"
    return output_df

# 3 Read JSON tracking data from GitHub
def readTrackingData(match_list : list[int], retrieve_metadata : bool = True) -> pd.DataFrame:

    """Reads in tracking data from SkillCorner GitHub as specific by list of match ids"""

    assert type(match_list) == type([]), "match_list must be a list of integers"
    assert type(match_list[0]) == type(1), "match_list must be a list of integers"

    if retrieve_metadata:
        print("\n*** Retrieving Player Meta Data (This will increase processing time) ***\n")

    print("match_id:", match_list[0])
    output_df = pd.read_json(f"https://media.githubusercontent.com/media/SkillCorner/opendata/master/data/matches/{match_list[0]}/{match_list[0]}_tracking_extrapolated.jsonl",
                            lines = True)

    output_df = cleanTrackingData(df = output_df, match_id = match_list[0]) # Use our helper function to clean up the tracking data

    if retrieve_metadata == True:
        
        players_df = playerMetaData(match_id = match_list[0])
        output_df = pd.merge(left = output_df, right = players_df, on = ["player_id", "match_id"]) # Append metadata for tracking data

    # loop through the remaining matches, read them, and append to dataset (this only runs if there are more than 1 match in the match_list)
    if len(match_list) > 1:
        for id in match_list[1:]:
            print("match_id:", id)
            temp_df = pd.read_json(f"https://media.githubusercontent.com/media/SkillCorner/opendata/master/data/matches/{id}/{id}_tracking_extrapolated.jsonl",
                                   lines = True)
            
            temp_df = cleanTrackingData(df = temp_df, match_id = id)

            if retrieve_metadata == True:
                players_df = playerMetaData(match_id=id)
                temp_df = pd.merge(left = temp_df, right = players_df, on = ["player_id", "match_id"]) # append metadata for tracking data

            assert output_df.shape[1] == temp_df.shape[1], "number of columns for appending dataset must be the same as output dataset"
            output_df = pd.concat([output_df, temp_df])

    return output_df
