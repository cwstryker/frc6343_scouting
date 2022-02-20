CLIMB_CODES_2022 = {"None": "-", "Low": "L", "Mid": "M", "High": "H", "Traversal": "T"}


def print_climb_history(tba, event):
    """Display the climb history for each team at an event"""
    climb_history = {}
    matches = tba.event_matches(event)
    for match_data in matches:
        if match_data["comp_level"] == "qm" and match_data["score_breakdown"]:
            for alliance in ["red", "blue"]:
                teams = [int(i[3:]) for i in match_data["alliances"][alliance]["team_keys"]]
                climbs = [match_data["score_breakdown"][alliance][f"endgameRobot{i + 1}"] for i in range(3)]
                for i, team in enumerate(teams):
                    climb_history.setdefault(team, []).append(CLIMB_CODES_2022[climbs[i]])

    # Print the climb history
    print("Climb History Report")
    print("Team  History")
    for team in sorted(climb_history):
        print(f"{team:4}  {''.join(climb_history[team])}")


SPECIAL_REPORTS = {
    "2019": [],
    "2020": [],
    "2022": [print_climb_history],
}
