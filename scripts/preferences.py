import os
import json
import logging
from pathlib import Path

class UserPreferences:
    """Manage user preferences for the Sticky Note Compiler application."""
    
    def __init__(self):
        self.config_dir = Path(r'c:\LocalStorage\Sticky_Note_Compiler\config')
        self.preferences_file = self.config_dir / 'user_preferences.json'
        self.default_preferences = {
            "theme": "light",
            "defaultSortOrder": "date-desc",
            "sidebarExpanded": True,
            "notesPerPage": 20,
            "autoSave": True,
            "fontSize": "medium",
            "defaultView": "grid",
            "refreshInterval": 60,
            "notifications": {
                "enabled": True,
                "sound": True,
                "desktop": True
            },
            "keyboard_shortcuts": {
                "enabled": True
            }
        }
        self.preferences = self.load_preferences()
        
    def load_preferences(self):
        """Load user preferences from file or create with defaults if not exists."""
        try:
            # Ensure config directory exists
            self.config_dir.mkdir(parents=True, exist_ok=True)
            
            # If preferences file exists, load it
            if self.preferences_file.exists():
                with open(self.preferences_file, 'r') as f:
                    user_prefs = json.load(f)
                    # Ensure all default keys exist by merging with defaults
                    merged = self.default_preferences.copy()
                    self._deep_update(merged, user_prefs)
                    return merged
            
            # If file doesn't exist, create it with defaults
            self.save_preferences(self.default_preferences)
            return self.default_preferences
            
        except Exception as e:
            logging.error(f"Error loading preferences: {str(e)}")
            return self.default_preferences
    
    def _deep_update(self, target, source):
        """Recursively update nested dictionaries."""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_update(target[key], value)
            else:
                target[key] = value
    
    def save_preferences(self, preferences=None):
        """Save preferences to JSON file."""
        if preferences is None:
            preferences = self.preferences
            
        try:
            with open(self.preferences_file, 'w') as f:
                json.dump(preferences, f, indent=4)
            self.preferences = preferences
            return True
        except Exception as e:
            logging.error(f"Error saving preferences: {str(e)}")
            return False
    
    def get_preference(self, key_path, default=None):
        """
        Get a preference value using a dot-notation path.
        Example: get_preference('notifications.sound')
        """
        try:
            keys = key_path.split('.')
            value = self.preferences
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def set_preference(self, key_path, value):
        """
        Set a preference value using a dot-notation path and save to file.
        Example: set_preference('notifications.sound', False)
        """
        try:
            keys = key_path.split('.')
            target = self.preferences
            
            # Navigate to the innermost dictionary
            for key in keys[:-1]:
                if key not in target or not isinstance(target[key], dict):
                    target[key] = {}
                target = target[key]
            
            # Set the value and save
            target[keys[-1]] = value
            return self.save_preferences()
        except Exception as e:
            logging.error(f"Error setting preference {key_path}: {str(e)}")
            return False
