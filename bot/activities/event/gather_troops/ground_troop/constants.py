"""
constants.py — ảnh, ngưỡng và action riêng của nhiệm vụ Ground Troop.
"""
from ...constants import THRESHOLDS as EVENT_THRESHOLDS

# Ô chọn ở group Gather Troops (Day 2): {"value": số lính, "level": cấp lính, "day": 2}.
KEY = "ground_troop"

THRESHOLDS = {
    **EVENT_THRESHOLDS,
}
REGIONS = {}
