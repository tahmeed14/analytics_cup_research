# exhaustive list of match ids for the SkillCorner open data
match_ids = [1886347,
             1899585,
             1925299,
             1953632,
             1996435,
             2006229,
             2011166, 
             2013725,
             2015213,
             2017461]

# variables to be selected for Player Possession dataset
pp_variables = [
    # Must need characteristics
    "match_id",
    "index",
    "event_id",
    "event_type",
    "x_start",
    "y_start",
    "x_end",
    "y_end",
    "frame_start",
    "frame_end",
    "duration",
    "player_id",
    "player_name",
    # "player_in_possession_name",
    # "associated_player_possession_event_id",
    "team_id",
    "team_shortname",

    # Passing option information
    "targeted_passing_option_event_id", # so we can merge
    "player_targeted_name",

    # Characteristics that can be potential predictors in model
    "start_type",
    "end_type",
    "pass_outcome",
    "pass_distance",
    "separation_start",
    "separation_end",
    "distance_covered",
    "n_passing_options",
    "n_off_ball_runs",
    "team_score",
    "opponent_team_score",
    "game_state",
    "speed_avg",
    "speed_avg_band",
    # "team_possession_loss_in_phase",
    
    # Filtering variables
    "team_in_possession_phase_type",
    "team_out_of_possession_phase_type",
    "third_start",
    # "third_end",
    # "channel_start",
    # "channel_end",
    
    # Possession data that is helpful to identify and create possession statistics
    "first_player_possession_in_team_possession",
    "last_player_possession_in_team_possession"
]

# variables to be selected for Passing Option dataset
po_variables = [
    "match_id",
    "player_id",
    "player_name",
    "associated_player_possession_event_id",
    "interplayer_distance", # distance between passer and pass-ee at the moment of the pass
    "interplayer_angle", # angle between direction of attack & the pass vector
    "passing_option_score",

    # For future steps: we can extend this to add a predictor that considers how much work the passing options do
    # to get open
    "separation_start",
    "separation_end",
    "separation_gain"
]

# variables to be selected for On Ball Engagement dataset
obe_variables = [
    "match_id",
    "event_subtype",
    "player_id",
    "player_name",
    "associated_player_possession_event_id",
    "speed_avg",
    "speed_avg_band",
    "distance_covered",

    # future steps
    "pressing_chain",
    "pressing_chain_end_type",
    "pressing_chain_length",
    "simultaneous_defensive_engagement_same_target"
]

# skillcorner frame precision
skillcorner_frame_precision = (1/10)

# fin.