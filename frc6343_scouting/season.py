import pandas as pd


CLIMB_CODES_2022 = {"None": "-", "Low": "L", "Mid": "M", "High": "H", "Traversal": "T"}
CLIMB_SCORES_2022 = {"None": 0, "Low": 4, "Mid": 6, "High": 10, "Traversal": 15}
TAXI_SCORES_2022 = {"No": 0, "Yes": 2}


def hang_history_2022(tba, event):
    """Find the hang history for each team at a 2022 event"""
    hang_history = {}
    hang_scores = {}

    # Get the match data
    matches = tba.event_matches(event)

    # for each alliance in a qualification match with a score breakdown
    for match_data in matches:
        if match_data["comp_level"] == "qm" and match_data["score_breakdown"]:
            for alliance in ["red", "blue"]:

                # extract the team numbers and the hang results for each alliance in each match
                teams = [int(i[3:]) for i in match_data["alliances"][alliance]["team_keys"]]
                hang = [match_data["score_breakdown"][alliance][f"endgameRobot{i + 1}"] for i in range(3)]

                # Tally the hang history and scores for each team
                for i, team in enumerate(teams):
                    hang_history.setdefault(team, []).append(CLIMB_CODES_2022[hang[i]])
                    hang_scores.setdefault(team, []).append(CLIMB_SCORES_2022[hang[i]])

    # Create and return a dataframe
    df_teams = sorted(hang_history.keys())
    df = pd.DataFrame(index=df_teams)
    df["HAP"] = [sum(hang_scores[i])/len(hang_scores[i]) for i in df_teams]
    df["HH"] = [''.join(hang_history[i]) for i in df_teams]
    return df


def taxi_average_points_2022(tba, event):
    """Find the hang history for each team at a 2022 event"""
    taxi_scores = {}

    # Get the match data
    matches = tba.event_matches(event)

    # for each alliance in a qualification match with a score breakdown
    for match_data in matches:
        if match_data["comp_level"] == "qm" and match_data["score_breakdown"]:
            for alliance in ["red", "blue"]:

                # extract the team numbers and the taxi results for each alliance in each match
                teams = [int(i[3:]) for i in match_data["alliances"][alliance]["team_keys"]]
                taxi = [match_data["score_breakdown"][alliance][f"taxiRobot{i + 1}"] for i in range(3)]

                # Tally the taxi scores for each team
                for i, team in enumerate(teams):
                    taxi_scores.setdefault(team, []).append(TAXI_SCORES_2022[taxi[i]])

    # Create and return a dataframe
    df_teams = sorted(taxi_scores.keys())
    df = pd.DataFrame(index=df_teams)
    df["TAP"] = [sum(taxi_scores[i]) / len(taxi_scores[i]) for i in df_teams]
    return df


SPECIAL_REPORTS = {
    "2019": [],
    "2020": [],
    "2022": [taxi_average_points_2022, hang_history_2022],
}

SORT_BY_COLUMNS = {
    "2022": [("RNK", True), ("OPR", False), ("TAP", False), ("CARGO", False), ("HAP", False)],
    "2020": [("PC", False), ("FOUL", True), ("OPR", False)],
    "2019": [("FOUL", True), ("OPR", False)],
}
