# Muscle Group Mapping: Specific Muscle -> Major Group
GROUP_MAPPING = {
    'biceps': 'arms',
    'triceps': 'arms',
    'forearms': 'arms',
    'calves': 'legs',
    'quads': 'legs',
    'hamstrings': 'legs',
    'glutes': 'legs',
    'upper_back': 'back',
    'lats': 'back',
    'traps': 'back'
}

# Explicit Sort Order (Chromatic/User Preference)
MUSCLE_GROUP_ORDER = ['arms', 'shoulders', 'chest', 'core', 'back', 'legs', 'unknown']

# Colors for specific muscles and major groups
MUSCLE_GROUP_COLORS = {
    'arms': '#ef476f',
    'biceps': '#ef476f',
    'triceps': '#f6bd60',
    'forearms': '#b38647',
    'shoulders': '#f78c6b',
    'chest': '#ffd166',
    'core': '#06d6a0',
    'back': '#118ab2',
    'upper_back': '#118ab2',
    'lats': '#533a7b',
    'traps': '#f59ca9',
    'legs': '#073b4c',
    'quads': '#073b4c',
    'hamstrings': '#42bfdd',
    'glutes': '#c7b8ea',
    'calves': '#fcffeb',
    'unknown': '#ffffff'
}

PHASE_COLORS = {
    'bulk': '#FFD700',      # Bright Gold
    'cut': '#FF00FF',       # Magenta/Purple (High contrast)
    'maintenance': '#B0BEC5', # Blue-ish Gray
    'unknown': '#5f6368'
}
