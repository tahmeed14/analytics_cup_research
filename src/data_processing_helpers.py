# Author: Tahmeed Tureen <tureen@umich.edu>
import pandas as pd
import requests
import numpy as np
from src.universal_global_variables import *

# 1 This function helps us create a possession index/identifier
def createPossessionIndex(pp_df: pd.DataFrame) -> pd.DataFrame:
    """
        Takes in SkillCorner events dataset filtered for player possession and then creates a team possession label
        The possession label allows the user to identify sequence of player possessions within a team possession
        Additionally, this can be used to count the number of possessions in a match, durations of each possession (# passes, total time)
    """

    #TODO asserts

    pp_out = pp_df.sort_values(["match_id", "index"], ascending = True) # sort the dataset appropriately by making sure index is moving from 0 to infinity
    pp_out["team_possession_start"] = (pp_out.groupby("match_id")["first_player_possession_in_team_possession"].transform(lambda indicator : (indicator == True))).astype(int) # create a numeric in the sequence that represents the start of a new possession
    pp_out["match_possession_id"] = pp_out.groupby(["match_id"])["team_possession_start"].cumsum() # by summing the cumulative posession starts, we can get the n-th posession in the match
    pp_out["match_team_possession_id"] = pp_out["match_id"].astype(str) + "_" + pp_out["team_shortname"].str.strip() + "_" + pp_out["match_possession_id"].astype(str)
    pp_out["individual_poss_id"] = pp_out["match_id"].astype("str") + "_" + pp_out["index"].astype("str") + "_" + pp_out["event_id"].astype("str") # create 

    # ** Calculate possession metrics for each match and possession
    # team_possession_duration: duration (seconds) of the team possession until possession changes to opposition team
    # team_possession_num_sequences : number of player possession changes within the team possession
    possession_metrics = (pp_out.groupby(["match_id", "match_possession_id", "match_team_possession_id", "team_id"])
                                .agg(team_possession_duration = ("duration", "sum"),
                                     team_possession_num_sequences = ("index", "size"))
                         )
    
    # Make sure the IDs are strings for future use
    pp_out["match_id"] = pp_out["match_id"].astype("str")
    pp_out["team_id"] = pp_out["team_id"].astype("str")
    pp_out["player_id"] = pp_out["player_id"].astype("str")

    possession_metrics = possession_metrics.reset_index(drop = False)

    return pp_out, possession_metrics.sort_values(["match_id", "match_possession_id"], ascending = True)

# 2 # add a new column frame_end_v2 that represents the end frame for any passes 
# # (in other words, the frame_start of a reception from a successful pass in a team possession)
def createPassEndFrame(df: pd.DataFrame) -> pd.DataFrame:
    """TODO add description"""
    # TODO: add asserts!
    
    df = df.sort_values(["match_id", "match_possession_id", "index"]) # sort to make sure every row is in order

    # group by our unique possession id and then create a variable that captures what the next frame is
    # this works for us because we already filtered the data for just possession
    df["next_frame_start"] = (
        df.groupby("match_team_possession_id")["frame_start"].shift(-1)
    )

    # We will create a frame_end version 2 which captures where the ball ends up when there is a successful pass
    # filters:
    # (1) Player Possession ends with a pass
    # (2) Pass outcome is successful
    # (3) This action is not the last action in the Team Possession (TODO: Ask @NanoSkillCorner question about this)
    bool_successful_pass = (df["end_type"] == "pass") & (df["pass_outcome"] == "successful") & (df["last_player_possession_in_team_possession"] == False)
    df["frame_end_v2"] = df["frame_end"] # assign this as a catch all since not all possessions end with a successful pass
    df.loc[bool_successful_pass, "frame_end_v2"] = df.loc[bool_successful_pass, "next_frame_start"] # using the filter we now assign the new frame (where the ball is sent via a pass)

    df["frame_end_v2"] = df["frame_end_v2"].astype("int") # convert this to integer
    df.drop(columns = ["next_frame_start"], inplace = True) # drop this variable

    return df

# 3
def process_PPdata(event_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
        Takes in SkillCorner events dataset, selects relevant columns based on a global variable (see src.universal_global_variables)
        and creates a dataset that can be used to model possession metrics. The model also returns a match and possession level summary
        statistics table that can be used to filter the modeling dataset
    """

    # TODO assert for dataframe type
    # TODO assert for global variables
    
    # pp_variables is a global variable
    output_df = event_df.loc[event_df["event_type"] == "player_possession", :][pp_variables].reset_index(drop = True)

    # add a possesion label for each PP event and match combo
    output_df, possession_metrics = createPossessionIndex(pp_df = output_df)

    # add a new column frame_end_v2 that represents the end frame for any passes 
    # (in other words, the frame_start of a reception from a successful pass in a team possession)
    output_df = createPassEndFrame(df = output_df)

    # TODO assert for output variable
    return output_df, possession_metrics

# 4
# TODO: add to helpers
def process_POforPP(event_df : pd.DataFrame) -> pd.DataFrame:
    # TODO: add asserts
    output_df = event_df.loc[event_df["event_type"] == "passing_option", :][po_variables]
    output_df.rename({"associated_player_possession_event_id" : "pp_event_id"}, axis = 1, inplace = True)

    # group by and create metrics that could be potential predictors in our model
    output_df = output_df.groupby(["match_id", "pp_event_id"]).agg({"interplayer_distance" : ["min", "mean"],
                                                     "passing_option_score" : ["max", "mean"],
                                                     "player_id" : "nunique"}).reset_index()
    
    output_df.columns = ['_'.join(col).strip() for col in output_df.columns.values]
    output_df.rename({"match_id_" : "match_id", 
                      "pp_event_id_" : "pp_event_id",
                      "player_id_nunique" : "po_options_custom"},
                        axis = 1, inplace = True)

    return output_df

# 5
# TODO add doc
def aggregateOBE(obe_df, subtypes) -> pd.DataFrame:
    # TODO add asserts
    obe_agg = obe_df.loc[obe_df["event_subtype"].isin(subtypes), :]
    obe_agg = obe_agg.groupby(["match_id", "pp_event_id"]).agg({"player_id" : "nunique",
                                                                "distance_covered" : ["mean", "min"],
                                                                "speed_avg" : ["mean", "max"]})
    obe_agg = obe_agg.reset_index()

    obe_agg.columns = ['_'.join(col).strip() for col in obe_agg.columns.values]

    return obe_agg

# 6
# TODO add doc
def process_OBEforPP(event_df : pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    # TODO add asserts

    obe_df = event_df.loc[event_df["event_type"] == "on_ball_engagement", :][obe_variables].reset_index(drop = True)
    obe_df.rename({"associated_player_possession_event_id" : "pp_event_id"}, axis = 1, inplace = True)

    # presses
    press = ["pressing", "counter_press", "recovery_press"]
    press_df = aggregateOBE(obe_df = obe_df, subtypes = press)
    press_df.rename({"match_id_" : "match_id",
                     "pp_event_id_" : "pp_event_id",
                     "player_id_nunique" : "num_opp_press_players",
                     "distance_covered_mean" : "opp_press_dist_covered_mean",
                     "distance_covered_min" : "opp_press_dist_covered_min",
                     "speed_avg_mean" : "opp_press_speed_avg_mean",
                     "speed_avg_max" : "opp_press_speed_avg_max"
                     }, 
                     axis = 1,
                     inplace = True)

    # pressure
    pressure_df = aggregateOBE(obe_df = obe_df, subtypes = ["pressure"])
    pressure_df.rename({"match_id_" : "match_id",
                        "pp_event_id_" : "pp_event_id",
                        "player_id_nunique" : "num_opp_pressure_players",
                        "distance_covered_mean" : "opp_pressure_dist_covered_mean",
                        "distance_covered_min" : "opp_pressure_dist_covered_min",
                        "speed_avg_mean" : "opp_pressure_speed_avg_mean",
                        "speed_avg_max" : "opp_pressure_speed_avg_max"
                        }, 
                        axis = 1,
                        inplace = True)

    # other
    other_df = aggregateOBE(obe_df = obe_df, subtypes = ["other"])
    other_df.rename({"match_id_" : "match_id",
                     "pp_event_id_" : "pp_event_id",
                     "player_id_nunique" : "num_opp_other_obe_players",
                     "distance_covered_mean" : "opp_other_obe_dist_covered_mean",
                     "distance_covered_min" : "opp_other_obe_dist_covered_min",
                     "speed_avg_mean" : "opp_other_obe_speed_avg_mean",
                     "speed_avg_max" : "opp_other_obe_speed_avg_max"}, 
                     axis = 1,
                     inplace = True)

    return press_df, pressure_df, other_df


# 7
def playerMetaData(match_id : int) -> pd.DataFrame:
    # TODO asserts
    # Code inspired by SkillCorner's open tutorials
    
    meta_data_github_url = f"https://raw.githubusercontent.com/SkillCorner/opendata/master/data/matches/{match_id}/{match_id}_match.json"
    
    # Read the JSON data as a JSON object
    response = requests.get(meta_data_github_url)
    raw_match_data = response.json()

    # The output has nested json elements. We process them
    raw_match_df = pd.json_normalize(raw_match_data, max_level=2)  
    raw_match_df["home_team_side"] = raw_match_df["home_team_side"].astype(str)

    players_df = pd.json_normalize(
    raw_match_df.to_dict("records"), 
        record_path="players", 
        meta=[
            "home_team_score",
            "away_team_score",
            "date_time",
            "home_team_side",
            "home_team.name",
            "home_team.id",
            "away_team.name",
            "away_team.id",
        ], 
    )

    # Take only players who played and create their total time
    players_df = players_df[~((players_df.start_time.isna()) & (players_df.end_time.isna()))] # filter for players who have played
    # Create a match name variable
    players_df["match_name"] = (players_df["home_team.name"] + " vs " + players_df["away_team.name"]) # create the name of the match
    # Add a flag if the given player is home or away
    players_df["home_away_player"] = np.where(players_df.team_id == players_df["home_team.id"], "Home", "Away") # Categorical
    # Create flag from player
    players_df["team_name"] = np.where(players_df.team_id == players_df["home_team.id"], players_df["home_team.name"], players_df["away_team.name"],)

    # Figure out sides
    players_df[["home_team_side_1st_half", "home_team_side_2nd_half"]] = (
        players_df["home_team_side"]
        .astype(str)
        .str.strip("[]")
        .str.replace("'", "")
        .str.split(", ", expand=True)
    )

    # Clean up sides
    players_df["direction_player_1st_half"] = np.where(
        players_df.home_away_player == "Home",
        players_df.home_team_side_1st_half,
        players_df.home_team_side_2nd_half,
    )
    
    players_df["direction_player_2nd_half"] = np.where(
        players_df.home_away_player == "Home",
        players_df.home_team_side_2nd_half,
        players_df.home_team_side_1st_half,
    )

    players_df["match_id"] = str(match_id)
    players_df.rename({"id" : "player_id",
                       "short_name" : "player_short_name",
                       "number" : "player_number"}, axis = 1, inplace=True)
    players_df["player_id"] = players_df["player_id"].astype("int").astype("str")

    columns_to_keep = [
        "match_name",
        "match_id",
        "home_team.name",
        "away_team.name",
        "player_id",
        "player_short_name",
        "player_number",
        "team_id",
        "team_name",
        "player_role.position_group",
        "player_role.name",
        "player_role.acronym",
        "direction_player_1st_half",
        "direction_player_2nd_half",
    ]

    return players_df[columns_to_keep]

# 8
# TODO NEED TO FIX THIS function
def cleanTrackingData(df, match_id) -> pd.DataFrame:
    # TODO add asserts
    # Transform the data to observation level data that we can further manipulate for future analysis
    raw_df = pd.json_normalize(
        df.to_dict("records"),
        "player_data",
        ["frame", "timestamp", "period", "possession", "ball_data"],
    )

    # Extract 'player_id' and 'group from the 'possession' column which is a dictionary in the dataframe
    raw_df["possession_player_id"] = raw_df["possession"].apply(lambda x : x.get("player_id"))
    raw_df["possession_group"] = raw_df["possession"].apply(lambda x : x.get("group"))

    # Get ball coordinates
    raw_df[["ball_x", "ball_y", "ball_z", "is_detected_ball"]] = pd.json_normalize(raw_df.ball_data)

    # Drop the possession and ball_data columns as we no longer need it
    raw_df = raw_df.drop(columns=["possession", "ball_data"])

    # change data types for merging purposes
    raw_df["player_id"] = raw_df["player_id"].astype("str")
    # raw_df["possession_player_id"] = raw_df["possession_player_id"].astype("str")
    raw_df["match_id"] = str(match_id) # Add the match_id identifier to your dataframe
    
    return raw_df

# 9
def create_LeftToRightPoss(df) -> pd.DataFrame:
    # TODO asserts
    '''Takes in SkillCorner tracking data and then creates coordinates that represent all possession as left to right'''

    poss_trck_df = df[~df["possession_group"].isnull()].reset_index(drop = True)

    # Create some flags in case we need them later
    poss_trck_df["possession_team_name"] = np.where(
        poss_trck_df["possession_group"] == "home team",
        poss_trck_df["home_team.name"],
        poss_trck_df["away_team.name"],
    )

    # Create a possesion flag so we can filter for visualizations
    poss_trck_df["possession_flag"] = np.where(
        poss_trck_df["possession_team_name"] == poss_trck_df["team_name"], 
        "IP", # In Possession
        "OOP" # Out of Possession
    )

    # Conditions
    # Team In Possession, Players Moving Right to Left --> Flip Their Coordinates
    # Team In Possession, Opponents Moving Left to Right --> Flip Opponents Coordinates
    # Team Out of Possession, Players Moving Left to Right --> Flip Their Coordinates
    # Team Out of Possession, Opponents Moving Right to Left --> Flip Their Coordinates
    # Conditions 1 and 2 would cover 3 and 4 as they are basically the same thing

    # We basically want to convert the X and Y to make sure we're always visualizing left to right. A player's XY will depend on the half so the straight average doesn't work
    poss_trck_df["direction_player"] = np.where(
        poss_trck_df["period"] == 1,
        poss_trck_df["direction_player_1st_half"],
        poss_trck_df["direction_player_2nd_half"],
    )
    # When going right to left, we flip the coordinates (We want our analysis to go from left to right)
    poss_trck_df["adj_x"] = np.where(
        (poss_trck_df["direction_player"] == "right_to_left") & (poss_trck_df["possession_flag"] == "IP"),
        -poss_trck_df["x"], # when going right to left, flip coordinates
        poss_trck_df["x"],
    )  # Convert X

    poss_trck_df["adj_y"] = np.where(
        (poss_trck_df["direction_player"] == "right_to_left") & (poss_trck_df["possession_flag"] == "IP"),
        -poss_trck_df["y"], # when going right to left, flip coordinates
        poss_trck_df["y"],
    )  # Convert Y

    # When going right to left for possession team, we flip the coordinates (We want our analysis to go from left to right)
    poss_trck_df["ball_adj_x"] = np.where(
        (poss_trck_df["direction_player"] == "right_to_left") & (poss_trck_df["possession_flag"] == "IP"),
        -poss_trck_df["ball_x"], # when going right to left, flip coordinates
        poss_trck_df["ball_x"],
    )  # Convert X

    poss_trck_df["ball_adj_y"] = np.where(
        (poss_trck_df["direction_player"] == "right_to_left") & (poss_trck_df["possession_flag"] == "IP"),
        -poss_trck_df["ball_y"], # when going right to left, flip coordinates
        poss_trck_df["ball_y"],
    )  # Convert Y

    # When going right to left, we flip the coordinates (We want our analysis to go from left to right)
    poss_trck_df["adj_x"] = np.where(
        (poss_trck_df["direction_player"] == "left_to_right") & (poss_trck_df["possession_flag"] == "OOP"),
        -poss_trck_df["x"], # when going right to left, flip coordinates
        poss_trck_df["x"],
    )  # Convert X

    poss_trck_df["adj_y"] = np.where(
        (poss_trck_df["direction_player"] == "left_to_right") & (poss_trck_df["possession_flag"] == "OOP"),
        -poss_trck_df["y"], # when going right to left, flip coordinates
        poss_trck_df["y"],
    )  # Convert Y

    
    # Convert possession player ID to string
    poss_trck_df["possession_player_id"] = poss_trck_df["possession_player_id"].fillna(-1)
    poss_trck_df["possession_player_id"] = poss_trck_df["possession_player_id"].astype("int").astype("str")
    poss_trck_df["possession_player_id"] = np.where(poss_trck_df["possession_player_id"] == -1,
                                                    "None",
                                                    poss_trck_df["possession_player_id"])
    
    return poss_trck_df[["adj_x", "adj_y", "ball_adj_x", "ball_adj_y"] + df.columns.tolist() + ["possession_flag", "direction_player"]] # rearrange columns and then return

# ***
# Model Data Mergers

def mergeTrack_and_PP(event_df, track_df, include_pass = True, track_type = "SkillCorner"):
    
    frame_end = "frame_end_v2" if include_pass else "frame_end"
    
    track_df = track_df[["match_id", "frame", "ball_x", "ball_y"]].copy()
    track_df = track_df.drop_duplicates()

    event_df = event_df[["individual_poss_id", "match_id", "match_team_possession_id",
                         "player_id", "player_name", 
                         "index", "frame_start", "frame_end", "frame_end_v2"]].copy()
    
    event_df["num_frames"] = event_df[frame_end] - event_df["frame_start"]
    
    event_df["match_id"] = event_df["match_id"].astype("str")
    track_df["match_id"] = track_df["match_id"].astype("str")

    out_df = pd.merge(left = event_df, right = track_df, on = ["match_id"], suffixes=["_ev", "tr"])
    out_df = out_df.loc[(out_df["frame_start"] <= out_df["frame"]) & (out_df["frame"] <= out_df[frame_end]), :]

    if track_type == "SkillCorner":
        out_df["ball_time_in_poss_tempo"] = skillcorner_frame_precision * out_df["num_frames"]

    return out_df

# 2
def distance_BallCoveredInPossession(df) :
  # TODO add assert statements
  
  cols = ["individual_poss_id", "player_id", "match_id"]

  # ensure rows are in temporal order
  df = df.sort_values(cols + ["frame"])

  # compute per-axis differences within each group
  df["dx"] = df.groupby(cols)["ball_x"].diff()
  df["dy"] = df.groupby(cols)["ball_y"].diff()

  # distance moved between frames
  df["ball_dist_step"] = np.sqrt(df["dx"]**2 + df["dy"]**2)

  # first frame in each group has no movement → set to 0
  df["ball_dist_step"] = df["ball_dist_step"].fillna(0)

  # cumulative distance within possession / sequence
  df["ball_dist_cum"] = df.groupby(cols)["ball_dist_step"].cumsum()

  # total distance per (unique_id, player_id, match_id)
  total_dist = (
      df.groupby(cols)["ball_dist_step"]
        .sum()
        .reset_index(name="ball_total_distance_tempo")
  )

  return total_dist

# fin.