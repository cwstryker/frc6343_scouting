import os
from collections import namedtuple

import tbapy
import pandas as pd
import numpy as np
from numpy.linalg import linalg
from pprint import pprint

CalcContribMetric = namedtuple("CalcContribMetric", ["cc_name", "cc_func"])

#EVENT = "2019orwil"
EVENT = "2020orore"
#EVENT = "2022orore"
HOME_TEAM = 6343
MATCH = None


def cc_metric_my_opr(*, match_data, alliance):
    """Find the total score earned during the match"""
    return int(match_data["score_breakdown"][alliance]["totalPoints"])


def cc_metric_fouls(*, match_data, alliance):
    """Find the total score earned during the match"""
    alliance = "red" if alliance == "blue" else "blue"
    return -1 * int(match_data["score_breakdown"][alliance]["foulPoints"])


def cc_metric_2020_power_cell(*, match_data, alliance):
    """Find the total cell points earned during the auto and teleop periods"""
    t_cells = int(match_data["score_breakdown"][alliance]["teleopCellPoints"])
    a_cells = int(match_data["score_breakdown"][alliance]["autoCellPoints"])
    return t_cells + a_cells


CC_METRICS = {
    "2022": [
        CalcContribMetric("FOUL", cc_metric_fouls),
        CalcContribMetric("MY_OPR", cc_metric_my_opr),
        ],
    "2020": [
        CalcContribMetric("PC", cc_metric_2020_power_cell),
        CalcContribMetric("FOUL", cc_metric_fouls),
        CalcContribMetric("MY_OPR", cc_metric_my_opr),
        ],
    "2019": [
        CalcContribMetric("FOUL", cc_metric_fouls),
        CalcContribMetric("MY_OPR", cc_metric_my_opr),
        ],
    }

SORT_BY_COLUMNS = {
    "2022": ["FOUL", "MY_OPR"],
    "2020": ["PC", "FOUL", "MY_OPR"],
    "2019": ["FOUL", "MY_OPR"],
    }


def get_opr_df(tba, event_id, teams):
    try:
        oprs_raw = tba.event_oprs(event_id)
    except TypeError:
        return None
    opr_df = pd.DataFrame(index=teams)
    opr_df["BA_OPR"] = [opr for _, opr in sorted(list(oprs_raw["oprs"].items()))]
    return opr_df.sort_index()


def get_rankings_df(tba, event_id, teams):
    try:
        rankings_raw = tba.event_rankings(event_id)
    except TypeError:
        return None
    ranking_df = pd.DataFrame(index=teams)
    ranking_df["W"] = [i["record"]["wins"] for i in rankings_raw["rankings"]]
    ranking_df["L"] = [i["record"]["losses"] for i in rankings_raw["rankings"]]
    ranking_df["T"] = [i["record"]["ties"] for i in rankings_raw["rankings"]]
    ranking_df["RP"] = [i["extra_stats"][0] for i in rankings_raw["rankings"]]
    ranking_df["Rnk"] = [i["rank"] for i in rankings_raw["rankings"]]
    ranking_df["DQ"] = [i["dq"] for i in rankings_raw["rankings"]]
    return ranking_df.sort_index()


def get_match_cc_metrics(season, match_data, color):
    results = {}
    for cc_name, cc_func in CC_METRICS[season]:
        results[cc_name] = cc_func(match_data=match_data, alliance=color)
    return results


def get_cc_metric(*, season, teams, matches, metric_name):
    """Create a calculated contribution (i.e. OPR) table"""

    # Use linear equation of the form: m * x = s, where x is the calc contribution vector
    m = []
    s = []
    for match in matches:

        # Only consider qualification matches
        if match["comp_level"] == "qm":

            # For each alliance in each match
            for color in ["red", "blue"]:

                # Get the values of the desired metrics
                scores = get_match_cc_metrics(
                    season=season, match_data=match, color=color
                )
                s.append(scores[metric_name])

                # Populate the matrix that shows which teams participated in the match
                row = [0] * len(teams)
                for team_key in match["alliances"][color]["team_keys"]:
                    team = int(team_key[3:])
                    row[list(teams).index(team)] = 1
                m.append(row)

    # Normalize the overdetermined system of equations using least squares
    m_norm = np.array(m).transpose() @ np.array(m)
    s_norm = np.array(m).transpose() @ np.array(s)

    # Solve for x
    if m_norm.ndim == 2:
        return linalg.solve(m_norm, s_norm)


def get_cc_metrics_df(tba, event_id, teams):
    """Create a dataframe for the calculated contribution metrics"""
    season = event_id[:4]
    cc_df = pd.DataFrame(index=teams)
    matches = tba.event_matches(EVENT)
    for metric, _ in CC_METRICS[season]:
        cc_df[metric] = get_cc_metric(season=season, teams=teams, matches=matches, metric_name=metric)
    return cc_df.sort_index()


def main():

    # Create a TBA connection using my API key
    tba = tbapy.TBA(os.environ.get("TBA_READ_KEY"))
    teams = [int(i["key"][3:]) for i in tba.event_teams(EVENT, simple=True)]
    df = pd.DataFrame(index=teams)

    # Use pandas to organize team data
    df = pd.concat([df, get_opr_df(tba, EVENT, teams), get_rankings_df(tba, EVENT, teams)], axis=1)

    # Concatenate the calculated contribution to the master data frame
    my_opr_df = get_cc_metrics_df(tba, EVENT, teams)
    df = pd.concat([df, my_opr_df], axis=1)

    for sort_by in SORT_BY_COLUMNS[EVENT[:4]]:
        # Sort the data and print the master data frame
        df.sort_values(by=[sort_by], inplace=True, ascending=False)
        with pd.option_context(
                "display.max_rows",
                None,
                "display.max_columns",
                None,
                "display.float_format",
                '{:.2f}'.format,
        ):
            # Prefix a '*' in front of the home team
            df.set_index(
                pd.Index([f"* {i:4}" if i == HOME_TEAM else f"{i:6}" for i in df.index]),
                inplace=True,
            )
            print(f"Sorted by {sort_by}")
            print(df)
            print()


if __name__ == "__main__":
    main()
