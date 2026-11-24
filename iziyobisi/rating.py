import logging
from functools import lru_cache

import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl

log = logging.getLogger(__name__)

LEVELS = ("low", "medium", "high")

# (google, twitter, twitter2) -> rating. Same rule base as the original app;
# google=medium & twitter=low has no rule (see README "Known limitations").
RULES = [
    *[("low", "low", t2, "low") for t2 in LEVELS],
    ("low", "medium", "low", "low"),
    ("low", "medium", "medium", "low"),
    ("low", "medium", "high", "medium"),
    *[("low", "high", t2, "medium") for t2 in LEVELS],
    *[("medium", "medium", t2, "medium") for t2 in LEVELS],
    *[("medium", "high", t2, "high") for t2 in LEVELS],
    *[("high", "low", t2, "medium") for t2 in LEVELS],
    *[("high", "medium", t2, "high") for t2 in LEVELS],
    *[("high", "high", t2, "high") for t2 in LEVELS],
]


def _input_terms(var):
    var["low"] = fuzz.trapmf(var.universe, [0, 0, 40, 45])
    var["medium"] = fuzz.trapmf(var.universe, [40, 45, 70, 75])
    var["high"] = fuzz.trapmf(var.universe, [70, 75, 101, 101])


@lru_cache(maxsize=1)
def _control_system() -> ctrl.ControlSystem:
    universe = np.arange(0, 101, 5)
    google = ctrl.Antecedent(universe, "google")
    twitter = ctrl.Antecedent(universe, "twitter")
    twitter2 = ctrl.Antecedent(universe, "twitter2")
    rating = ctrl.Consequent(universe, "rating")
    for var in (google, twitter, twitter2):
        _input_terms(var)
    rating["low"] = fuzz.trapmf(rating.universe, [0, 0, 30, 35])
    rating["medium"] = fuzz.trapmf(rating.universe, [30, 35, 70, 75])
    rating["high"] = fuzz.trapmf(rating.universe, [70, 75, 101, 101])
    rules = [
        ctrl.Rule(google[g] & twitter[t] & twitter2[t2], rating[r]) for g, t, t2, r in RULES
    ]
    return ctrl.ControlSystem(rules)


def _clamp(value: float) -> float:
    return float(min(max(value, 0), 100))


def fuzzy_rating(google: float, twitter: float, twitter2: float) -> float:
    sim = ctrl.ControlSystemSimulation(_control_system())
    sim.input["google"] = _clamp(google)
    sim.input["twitter"] = _clamp(twitter)
    sim.input["twitter2"] = _clamp(twitter2)
    try:
        sim.compute()
        return float(sim.output["rating"])
    except (ValueError, KeyError):
        log.warning("no fuzzy rule fired for inputs %s/%s/%s", google, twitter, twitter2)
        return 0.0
