from frc6343_scouting.tbatool import analyze_event


# 2019 Events
# EVENT = "2019flwp"   # South Florida Regional
# EVENT = "2019orwil"  # Wilsonville PNW

# 2020 Events
# EVENT = "2020orore"  # Clackamas Academy PNW

# 2022 Events
# EVENT = "2022orore"  # Clackamas Academy PNW
# EVENT = "2022flwp"   # South Florida Regional
# EVENT = "2022week0"  # Week 0 Event


BA_AUTH_KEY = ""
EVENT = "2022orore"
HOME_TEAM = 6343
MATCH = 1


if __name__ == "__main__":
    analyze_event(auth_key=BA_AUTH_KEY, event=EVENT, team=HOME_TEAM, match=MATCH)
