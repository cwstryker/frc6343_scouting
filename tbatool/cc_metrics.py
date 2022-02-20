from collections import namedtuple


CalcContribMetric = namedtuple("CalcContribMetric", ["cc_name", "cc_func"])


# 2019 Events
# EVENT = "2019flwp"   # South Florida Regional
# EVENT = "2019orwil"  # Wilsonville PNW
#
# 2020 Events
# EVENT = "2020orore"  # Clackamas Academy PNW
#
# 2022 Events
# EVENT = "2022orore"  # Clackamas Academy PNW
# EVENT = "2022flwp"   # South Florida Regional
# EVENT = "2022week0"  # Week 0 Event


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


def cc_metric_2022_cargo(*, match_data, alliance):
    t_cargo = int(match_data["score_breakdown"][alliance]["teleopCargoPoints"])
    a_cargo = int(match_data["score_breakdown"][alliance]["autoCargoPoints"])
    return t_cargo + a_cargo


def cc_metric_2022_hang(*, match_data, alliance):
    return int(match_data["score_breakdown"][alliance]["endgamePoints"])



CC_METRICS = {
    "2022": [
        CalcContribMetric("CARGO", cc_metric_2022_cargo),
        CalcContribMetric("HANG", cc_metric_2022_hang),
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
    "2022": ["RNK", "OPR", "CARGO", "HAP"],
    "2020": ["PC", "FOUL", "OPR"],
    "2019": ["FOUL", "OPR"],
}
