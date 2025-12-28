from mplsoccer import Pitch


# 1
def plotFrame_Regular(frame):

    frame["pip"] = frame["possession_player_id"] == frame["player_id"]

    pitch = Pitch(
        pitch_type="skillcorner",
        line_alpha=0.75,
        pitch_length=105,
        pitch_width=68,
        pitch_color="grass",
        line_color="white",
        linewidth=1.5,
    )
    fig, ax = pitch.grid(figheight=8, endnote_height=0, title_height=0)
    size = 300


    poss_team = frame[frame.possession_flag == "IP"]
    ax.scatter(
        poss_team["x"],
        poss_team["y"],
        c="blue",
        alpha=0.95,
        s=size,
        edgecolors="white",
        linewidths=1.5,
        zorder=10,
        label="team",
    )

    opp_team = frame[frame.possession_flag != "IP"]
    ax.scatter(
        opp_team["x"],
        opp_team["y"],
        c="red",
        alpha=0.95,
        s=size,
        edgecolors="white",
        linewidths=1.5,
        zorder=10,
        label="opponent",
    )

    possession_player= frame[frame.pip == True]
    # display(possession_team)
    ax.scatter(
        possession_player["x"],
        possession_player["y"],
        c="skyblue",
        alpha=0.95,
        s=size,
        edgecolors="white",
        linewidths=1.5,
        zorder=10,
        label="possession player",
    )

    ax.scatter(
        possession_player["ball_x"],
        possession_player["ball_y"],
        c="white",
        alpha=0.95,
        s=0.50 * size,
        edgecolors="white",
        linewidths=1.5,
        zorder=10,
        label="ball",
    )

#2
def plotFrame_Adjusted(frame):

    frame["pip"] = frame["possession_player_id"] == frame["player_id"]

    pitch = Pitch(
        pitch_type="skillcorner",
        line_alpha=0.75,
        pitch_length=105,
        pitch_width=68,
        pitch_color="grass",
        line_color="white",
        linewidth=1.5,
        # positional=True,
        # positional_linestyle="dashed"
    )
    fig, ax = pitch.grid(figheight=8, endnote_height=0, title_height=0)
    size = 300


    poss_team = frame[frame.possession_flag == "IP"]
    ax.scatter(
        poss_team["adj_x"],
        poss_team["adj_y"],
        c="royalblue",
        alpha=0.95,
        s=size,
        edgecolors="white",
        linewidths=1.5,
        zorder=10,
        label="Teammates",
    )

    opp_team = frame[frame.possession_flag != "IP"]
    ax.scatter(
        opp_team["adj_x"],
        opp_team["adj_y"],
        c="red",
        alpha=0.95,
        s=size,
        edgecolors="white",
        linewidths=1.5,
        zorder=10,
        label="Opponents",
    )

    possession_player= frame[frame.pip == True]
    # display(possession_player)
    ax.scatter(
        possession_player["adj_x"],
        possession_player["adj_y"],
        c="skyblue",
        alpha=0.95,
        s=size,
        edgecolors="white",
        linewidths=1.5,
        zorder=10,
        label="Player in Possession",
    )

    ax.scatter(
        possession_player["ball_adj_x"],
        possession_player["ball_adj_y"],
        c="white",
        alpha=0.95,
        s=0.50 * size,
        edgecolors="black",
        linewidths=1.5,
        zorder=10,
        label="Ball",
    )

    fig.show()