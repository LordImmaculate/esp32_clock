import json


def save_settings(file, settings_dict):
    try:
        with open(file, "w") as f:
            json.dump(settings_dict, f)
        print("Settings saved successfully.")
    except Exception as e:
        print(f"Error saving settings: {e}")


def load_settings(file):
    try:
        with open(file, "r") as f:
            settings_dict = json.load(f)
        print("Settings loaded successfully.")
        return settings_dict
    except Exception as e:
        print(f"Error loading settings: {e}")
        return None
