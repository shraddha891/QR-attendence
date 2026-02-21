# utils.py

from django.utils import timezone
from datetime import timedelta

from math import radians, sin, cos, sqrt, atan2

# Function to get the current time in UTC (or any timezone you specify)
def get_current_time():
    return timezone.now()

# Function to calculate expiry time (e.g., adding minutes)
def calculate_expiry(minutes=5):
    return timezone.now() + timedelta(minutes=minutes)

# Example: Function to check if a session has expired
def is_session_expired(session_expiry_time):
    return timezone.now() > session_expiry_time




def is_within_radius(lat1, lon1, lat2, lon2, radius_meters=100):
    """
    Returns True if the distance between (lat1, lon1) and (lat2, lon2)
    is within radius_meters.
    """
    R = 6371000  # Earth radius in meters
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = R * c
    return distance <= radius_meters
