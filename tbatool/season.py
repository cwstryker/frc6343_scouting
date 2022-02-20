import pandas as pd


CLIMB_CODES_2022 = {"None": "-", "Low": "L", "Mid": "M", "High": "H", "Traversal": "T"}
CLIMB_SCORES_2022 = {"None": 0, "Low": 4, "Mid": 6, "High": 10, "Traversal": 15}


def hang_history_2022(tba, event):
    """Find the hang history for each team at a 2022 event"""
    climb_history = {}
    climb_scores = {}
    matches = tba.event_matches(event)
    for match_data in matches:
        if match_data["comp_level"] == "qm" and match_data["score_breakdown"]:
            for alliance in ["red", "blue"]:
                teams = [int(i[3:]) for i in match_data["alliances"][alliance]["team_keys"]]
                climbs = [match_data["score_breakdown"][alliance][f"endgameRobot{i + 1}"] for i in range(3)]
                for i, team in enumerate(teams):
                    climb_history.setdefault(team, []).append(CLIMB_CODES_2022[climbs[i]])
                    climb_scores.setdefault(team, []).append(CLIMB_SCORES_2022[climbs[i]])

    # Create a dataframe
    df_teams = sorted(climb_history.keys())
    df = pd.DataFrame(index=df_teams)
    df["HAP"] = [sum(climb_scores[i])/len(climb_scores[i]) for i in df_teams]
    df["HH"] = [''.join(climb_history[i]) for i in df_teams]
    return df


SPECIAL_REPORTS = {
    "2019": [],
    "2020": [],
    "2022": [hang_history_2022],
}
