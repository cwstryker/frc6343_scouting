from . import __VERSION__
from .cc_metrics import CC_METRICS
from .season import SORT_BY_COLUMNS
from .season import SPECIAL_REPORTS

import argparse
import os

import tbapy
import pandas as pd
import numpy as np
from numpy.linalg import linalg
from numpy.linalg import LinAlgError


def get_opr_df(oprs_raw):
    teams = [int(team[3:]) for team, _ in sorted(list(oprs_raw["oprs"].items()))]
    opr_df = pd.DataFrame(index=teams)
    opr_df["OPR"] = [opr for _, opr in sorted(list(oprs_raw["oprs"].items()))]
    return opr_df.sort_index()


def get_rankings_df(rankings_raw):
    teams = [int(i["team_key"][3:]) for i in rankings_raw["rankings"]]
    ranking_df = pd.DataFrame(index=teams)
    ranking_df["W"] = [i["record"]["wins"] for i in rankings_raw["rankings"]]
    ranking_df["L"] = [i["record"]["losses"] for i in rankings_raw["rankings"]]
    ranking_df["T"] = [i["record"]["ties"] for i in rankings_raw["rankings"]]
    # ranking_df["RP"] = [i["extra_stats"][0] for i in rankings_raw["rankings"]]
    ranking_df["RNK"] = [i["rank"] for i in rankings_raw["rankings"]]
    ranking_df["DQ"] = [i["dq"] for i in rankings_raw["rankings"]]
    return ranking_df.sort_index()


def is_completed(match):
    return match["post_result_time"] is not None and match["post_result_time"] > 0


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
        if is_completed(match) and match["comp_level"] == "qm":

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
        try:
            return linalg.solve(m_norm, s_norm)
        except LinAlgError:
            print(f"Could not calculate {metric_name}")


def get_cc_metrics_df(matches, event_id, teams):
    """Create a dataframe for the calculated contribution metrics"""
    season = event_id[:4]
    cc_df = pd.DataFrame(index=teams)
    for metric, _ in CC_METRICS[season]:
        cc_df[metric] = get_cc_metric(
            season=season, teams=teams, matches=matches, metric_name=metric
        )
    return cc_df.sort_index()


def print_header(event_name, year, start_date, n_completed, n_total, n_teams):
    print(f"Event Name: {event_name}")
    print(f"Year: {year}")
    print(f"Start Date: {start_date}")
    print(f"Number of Team Competing: {n_teams}")
    print(f"Completed {n_completed} of {n_total} Qualification Matches")
    print()


def find_match_alliances(matches, match_number):
    result = [], []
    if match_number:
        for match in matches:
            if match["comp_level"] == "qm" and match["match_number"] == match_number:
                red = [int(i[3:]) for i in match["alliances"]["red"]["team_keys"]]
                blue = [int(i[3:]) for i in match["alliances"]["blue"]["team_keys"]]
                result = (red, blue)
                break
    return result


def process_and_print_header(event_info, team, matches, teams):
    all_post_result_times = [
        i
        for _, i in sorted(
            [
                (i["match_number"], i["post_result_time"])
                for i in matches
                if i["comp_level"] == "qm"
            ]
        )
    ]
    completed_post_result_times = [i for i in all_post_result_times if i]
    print_header(
        event_info["name"],
        event_info["year"],
        event_info["start_date"],
        len(completed_post_result_times),
        len(all_post_result_times),
        len(teams),
    )

    if team:
        print(f"Matches with Team {team}")
        print("Match       Red Alliance       Blue Alliance")
        for match_number in range(len(all_post_result_times)):
            red, blue = find_match_alliances(matches, match_number+1)
            if team in red or team in blue:
                print(f"{match_number+1:5}   {red[0]:4}  {red[1]:4}  {red[2]:4}    {blue[0]:4}  {blue[1]:4}  {blue[2]:4}")
        print()


def mark_index(index, team, red, blue):
    """Mark the given index for a specific team number or alliance color"""
    result = "*" if team and index == team else " "
    if index in red:
        result += f"R {index:4}"
    elif index in blue:
        result += f"B {index:4}"
    else:
        result += f"  {index:4}"
    return result


def print_df(df, season, team, matches, match_number):
    """Print out the dataframe"""
    red_alliance, blue_alliance = find_match_alliances(matches, match_number)
    saved_index = list(df.index)
    df.set_index(
        pd.Index(
            [
                mark_index(i, team=team, red=red_alliance, blue=blue_alliance)
                for i in df.index
            ]
        ),
        inplace=True,
    )
    for sort_by, ascending in SORT_BY_COLUMNS[season]:
        df.sort_values(by=[sort_by], inplace=True, ascending=ascending)
        with pd.option_context(
            "display.max_rows",
            None,
            "display.max_columns",
            None,
            "display.float_format",
            "{:.1f}".format,
        ):

            print(f"Sorted by {sort_by}", end="" if match_number else "\n")
            if match_number:
                print(f" & Marked for Match {match_number}")
            print(df)
            print()
    df.set_index(pd.Index(saved_index))


def main():

    parser = argparse.ArgumentParser(
        description="Blue Alliance Event Analysis", prog="TBA Tool"
    )
    parser.add_argument("event", help="ID string for an FRC event (i.e. '2022orore')")
    parser.add_argument(
        "-t", "--team", type=int, help="Team number to mark (i.e. home team)"
    )
    parser.add_argument(
        "-m", "--match", type=int, help="Match number used to mark alliances"
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__VERSION__}"
    )
    args = parser.parse_args()

    # Create a TBA connection using my API key
    tba = tbapy.TBA(os.environ.get("TBA_READ_KEY"))
    event_info = tba.event(args.event)
    matches = tba.event_matches(args.event)

    # Use pandas to organize team data
    df = pd.DataFrame()

    # Concatenate the Blue Alliance rankings data
    try:
        rankings = tba.event_rankings(args.event)
    except TypeError:
        print("No ranking data")
    else:
        df = pd.concat([df, get_rankings_df(rankings)], axis=1)

    # Concatenate the Blue Alliance OPR data
    try:
        oprs = tba.event_oprs(args.event)
    except TypeError:
        print("No OPR data")
    else:
        df = pd.concat([df, get_opr_df(oprs)], axis=1)

    # Concatenate the calculated contribution results
    my_opr_df = get_cc_metrics_df(matches, args.event, teams=df.index)
    df = pd.concat([df, my_opr_df], axis=1)

    # Process special reports
    for special in SPECIAL_REPORTS[args.event[:4]]:
        df = pd.concat([df, special(tba, args.event)], axis=1)

    # Display the header
    process_and_print_header(event_info, args.team, matches, teams=df.index)

    # Display the results
    print_df(df, args.event[:4], args.team, matches, args.match)


if __name__ == "__main__":
    main()
