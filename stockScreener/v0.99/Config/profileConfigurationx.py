def get_profilex(profileID):
    # Profile formatted, lowerbound, upperbound, direction, red-flag | direction: (D=Down, meaning below upper bound is good, U=UP, meaning, above uppoer bound is good). 
    # red flag value indicates when a good value turns into bad again. often N/A, but for example, if dividendYield exceeds 10% the company is paying out irrationally, which should be investigated.
    
    profile = {}
    return get_all_profiles()[profileID]


def get_all_profilesx():
    profiles = {}

    # Defensive Profile
    profiles[1] = {
        "Id": 1,
        "Type": 'Defensive profile',
        "beta": (0.99, 1.05, 'D', None),
        "peRatio": (10, 20, 'D', None),
        "pbRatio": (2, 5, 'D', None),
        "icr": (5, 7, 'U', None),
        "currentRatio": (0.95, 1.05, 'U', None),
        "dividendYield": (3, 5, 'U', 10),
        "percRandD": (1, 5, 'U', 25),
        "percentageMakingProfitLastFiveYears": (80, 99, 'U', None)
    }

    # You can add more profiles here in a similar manner
    # For example, adding another profile:
    profiles[2] = {
        "Id": 2,
        "Type": 'Growth profile',
        "beta": (1.1, 1.5, 'U', None),
        "peRatio": (15, 30, 'D', None),
        "pbRatio": (1.5, 4, 'D', None),
        "icr": (7, 10, 'U', None),
        "currentRatio": (1.1, 1.5, 'U', None),
        "dividendYield": (0, 2, 'U', 10),
        "percRandD": (3, 7, 'U', 25),
        "percentageMakingProfitLastFiveYears": (70, 95, 'U', None)
    }

    return profiles
