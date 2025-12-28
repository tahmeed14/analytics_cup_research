# Put all packages that need to be loaded here. By importing this script we get everythin

# Data Reading, Engineering, & Processing ---
import pandas as pd
import numpy as np
import re
import json
import requests

# Visualizations --
import matplotlib.pyplot as plt
from mplsoccer import Pitch

# Bayesian Modeling Packages ---
import arviz as az
import bambi as bmb # a beautiful package

from src.universal_helpers import *
from src.universal_global_variables import *
# from src.visualization_helpers import * # we dont need this for the submission
from src.data_processing_helpers import *

def visualizeEstimatedPlayerImpact(trace, k):
    posterior = trace.posterior
    player_var = "alpha_1|player_short_name"

    # shape_results = posterior[player_var]
    means = posterior[player_var].mean(dim=("chain", "draw")).to_series()
    means = means.sort_values()

    bottom5 = means.head(k).index.tolist()
    top5 = means.tail(k).index.tolist()

    subset_params = bottom5 + top5

    # display(posterior[player_var].coords)
    fig = az.plot_forest(
        # idata,
        trace,
        var_names=[player_var],
        coords={"player_short_name__factor_dim": subset_params}, # we got the naming convention by looking at output above!
        kind="ridgeplot",
        ridgeplot_alpha=0.5,
        ridgeplot_overlap=0.78,
        combined=True,
        figsize=(10, 10),
        colors = "salmon",
        hdi_prob=0.95
    )

    # Customize our plot
    ax = plt.gca()
    ax.set_facecolor("#f5f5f5")

    # Get current y-tick labels
    yticks = ax.get_yticks()
    yticklabels = [lbl.get_text() for lbl in ax.get_yticklabels()]

    # Extract text inside brackets
    clean_labels = []
    for lbl in yticklabels:
        match = re.search(r"\[(.*)\]", lbl)
        clean_labels.append(match.group(1) if match else lbl)

    # Insert "..." between the 5th and 6th label
    # (Python indexing: between 5th and 6th is at index 5)
    clean_labels.insert(5, "...")

    # Insert a tick at the same position as the 5th tick to match the labels
    yticks = list(yticks)
    yticks.insert(5, (yticks[4] + yticks[5]) / 2)  # place in between

    # Apply new labels
    ax.set_yticks(yticks)
    ax.set_yticklabels(clean_labels)

    # Add dashed line at zero
    ax.axvline(0, color="black", linestyle="--", linewidth=1.5)

    # Add labels
    # fig.suptitle('Main Plot Title', fontsize=16, fontweight='bold')
    ax.set_xlabel("Posterior Distribution of Player Random Effect\n w/ 95% Credible Intervals", 
                fontweight = "bold")
    ax.set_title('Estimated Player Impact on Ball Speed Tempo "Variance"\n Top 5 and Bottom 5 Players', 
                fontweight="bold",
                fontsize=14)

    ax.annotate(
        "Higher Variance",
        xy=(0.8, -0.10),  # end of arrow in axis coords
        xytext=(0.1, -0.10),
        xycoords="axes fraction",
        textcoords="axes fraction",
        arrowprops=dict(arrowstyle="<->", color="salmon", lw=2),
        ha="center",
        va="center",
        fontsize=10,
        color = "salmon",
        fontweight = "bold"
    )

    ax.text(0.97, -0.10, "Lower Variance", 
            transform=ax.transAxes,
            color = "salmon",
            fontweight="bold",
            ha="right", va="center", fontsize=10)

    plt.show()


# Data Reading & Processing Functions
def read_SkillCornerData(match_ids):
    # read all events
    print("***-- Reading & Processing SkillCorner Dynamic Events --***")
    all_events = readEvents(match_list = match_ids)
    pp_data, poss_metrics = process_PPdata(event_df = all_events)
    poss_metrics["team_id"] = poss_metrics["team_id"].astype("str")
    poss_metrics["match_id"] = poss_metrics["match_id"].astype("str")

    print("\n***-- Reading & Processing SkillCorner Tracking Data --***")
    # Read & process the raw tracking data
    tracking_df = readTrackingData(match_list = match_ids, retrieve_metadata=True)
    tracking_df = create_LeftToRightPoss(df = tracking_df)
    tracking_df["team_id"] = tracking_df["team_id"].astype("str")

    # From tracking data pull the player metadata
    player_metadata = tracking_df[["player_id", "match_id", "team_id", "team_name", 
                                    "player_short_name", "player_role.name"]].drop_duplicates().reset_index(drop = True)
    player_metadata["team_id"] = player_metadata["team_id"].astype("str")

    print("***-- Successfully Pulled & Processed Data --***")
    return tracking_df, player_metadata, pp_data, poss_metrics

def getEDA(tracking_df, poss_metrics):
    match_names = tracking_df[["match_id", "match_name"]].drop_duplicates().reset_index(drop = True)
    team_names = tracking_df[["team_id", "team_name"]].drop_duplicates().reset_index(drop = True)

    match_info = poss_metrics.groupby(["match_id"])["match_team_possession_id"].nunique().reset_index()
    match_info = pd.merge(left = match_info, right = match_names, on = "match_id")
    match_info.rename({"match_team_possession_id" : "num_possession_changes"}, axis = 1, inplace = True)


    # number of different
    team_info = poss_metrics.groupby(["match_id", "team_id"])["team_possession_num_sequences"].sum().reset_index()
    team_info = pd.merge(left = team_info, right = team_names, on = "team_id")

    return match_info, team_info

def add_ModelContext(model_df, context_df):
    pp_model = context_df[['individual_poss_id', 'match_team_possession_id',
                          'duration', 'start_type', 'end_type', 
                          'pass_outcome', 'pass_distance', 'separation_start', 'separation_end', 
                          'n_passing_options', 'n_off_ball_runs', 
                          # game context
                          'game_state', 'team_in_possession_phase_type', 'third_start',
                          'first_player_possession_in_team_possession',
                          'last_player_possession_in_team_possession']]

    output_df = pd.merge(
        left = model_df,
        right = pp_model,
        on = ["individual_poss_id"],
        how = "left"
    )

    return output_df

def create_SkillCornerModelData(pp_df, tracking_df, player_metadata, include_pass):
    print("***-- Merging tracking & event data. This may take some time. Please wait... --***")
    poss_track_df = mergeTrack_and_PP(event_df = pp_df,
                                      track_df = tracking_df,
                                      include_pass = include_pass,
                                      track_type = "SkillCorner")
    
    # Create out model target variables by estimating the distance traveled by ball
    model_df = distance_BallCoveredInPossession(df = poss_track_df)
    model_df = pd.merge(left = model_df, 
                    right = poss_track_df[["individual_poss_id", "ball_time_in_poss_tempo"]].drop_duplicates(),
                    on = "individual_poss_id",
                    how = "left")
    
    model_df["player_id"] = model_df["player_id"].astype("str") # type casting

    # Merge Player Data
    print("***-- Adding Context to Model Data --***")
    model_df = pd.merge(left = model_df,
                        right = player_metadata,
                        on = ["match_id", "player_id"],
                        how = "left")
    
    # Add Model Context for our Model Framework
    model_df = add_ModelContext(model_df=model_df, context_df=pp_df)
    
    print("***-- ...Dataset Generated... --***\n\n")
    return model_df

def runDataProcessBatches(match_ids):
   # TODO: We will adapt this code once we get access to more matches or if selected for the Open Source Grant

   tracking_df, player_metadata, pp_data, poss_metrics = read_SkillCornerData(match_ids = match_ids)
   match_info, team_info = getEDA(tracking_df, poss_metrics)
    
   model_df = create_SkillCornerModelData(pp_df = pp_data,
                                       tracking_df = tracking_df,
                                       player_metadata = player_metadata,
                                       include_pass = True)
    
   # match_last5 = match_ids[k:]

   # tracking_df2, player_metadata2, pp_data2, poss_metrics2 = read_SkillCornerData(match_ids = match_last5)
   # match_info2, team_info2 = getEDA(tracking_df2, poss_metrics2)
    
   # model_df2 = create_SkillCornerModelData(pp_df = pp_data2,
   #                                     tracking_df = tracking_df2,
   #                                     player_metadata = player_metadata2,
   #                                     include_pass = True)
    
   # model_df = pd.concat([model_df, model_df2])
   model_df.loc[:,"team_phase"] = model_df.team_in_possession_phase_type
   model_df.loc[model_df.team_in_possession_phase_type.isin(["transition", "quick_break", "direct"]),"team_phase"] = "fast or long"
   model_df.loc[model_df.team_in_possession_phase_type.isin(["chaotic", "disruption"]),"team_phase"] = "chaotic or disruption"
   
   # concatenate our results
   # return model_df, pd.concat([poss_metrics, poss_metrics2]), pd.concat([match_info, match_info2]), pd.concat([team_info, team_info2])
   return model_df, poss_metrics, match_info, team_info

def retrieveDataBatches(match_ids = match_ids):

    # TODO: We hope to optimize the data merging process after the submission.
    # For now, we process the data in batches to prevent a kernel timeout
    model_df, poss_metrics, match_info, team_info  = runDataProcessBatches(match_ids=match_ids[:5])
    model_df2, poss_metrics2, match_info2, team_info2  = runDataProcessBatches(match_ids=match_ids[5:])

    model_df = pd.concat([model_df, model_df2])
    poss_metrics = pd.concat([poss_metrics, poss_metrics2])
    match_info = pd.concat([match_info, match_info2])
    team_info = pd.concat([team_info, team_info2])

    return model_df, poss_metrics, match_info, team_info

def filterModelData(model_df, poss_metrics):
    # Filter for players possession that did not last more than zero seconds as measured by the tracking data
    model_df_filtered = model_df.loc[model_df["ball_total_distance_tempo"] != 0,:].reset_index(drop = True)

    # Create our target variable
    model_df_filtered["ball_speed_tempo"] = model_df_filtered["ball_total_distance_tempo"] / model_df_filtered["ball_time_in_poss_tempo"]

    # Filter for possession with atleast 3 sequences (3 changes in player possession during the team possession)
    poss_samples = poss_metrics.loc[poss_metrics.team_possession_num_sequences > 2]["match_team_possession_id"].tolist()
    model_df_filtered = model_df_filtered.loc[model_df_filtered["match_team_possession_id"].isin(poss_samples),:]

    players_sample = model_df_filtered["player_short_name"].value_counts().reset_index()
    players_sample = players_sample.loc[players_sample["count"] > 30, :] # filter for players with atleast 35 possessions across the data sample
    players_sample["count"].describe().T

    # # filter for players with atleast 30 possessions
    model_df_filtered = model_df_filtered.loc[model_df_filtered["player_short_name"].isin(players_sample["player_short_name"].tolist()),:]

    return model_df_filtered, players_sample

def plotTempo(model_df):
    plt.hist(model_df["ball_speed_tempo"], bins=30)
    plt.title("Distribution of Ball Speed Tempo")
    plt.xlabel("Ball Speed Tempo")

    plt.show()

# Sort Players by their Random Effect on Tempo Variance
def playerRankings(trace, hdi = 0.95):
    trace.posterior.data_vars
    alpha_player_vars = ["alpha_1|player_short_name"] # list in case we want to increase vars

    alpha_player_df = az.summary(
        trace,
        var_names=alpha_player_vars,
        hdi_prob = hdi
    )

    return alpha_player_df.sort_values("mean")

# view the fixed effects from our model
def fixedEffects(trace):
    results = az.summary(trace)
    results["exponentiated_mean"] = round((np.exp(results["mean"])), 2)
    return results.head(11)
