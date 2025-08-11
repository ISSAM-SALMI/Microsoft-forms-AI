import json
from pathlib import Path

class JsonImageChecker:
    def __init__(self, json_path: str):
        self.json_path = Path(json_path)

    def contains_images(self) -> bool:
        """Return True if the JSON file contains images, False otherwise."""
        if not self.json_path.exists():
            raise FileNotFoundError(f"File not found: {self.json_path}")

        with open(self.json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return bool(data.get("contains_images", False))


# Exemple d'utilisation
if __name__ == "__main__":
    json_file_path = r"C:\Users\abdel\OneDrive\Bureau\Microsoft-forms-AI\data\output\jsons\microsoft_forms_complete_data_20250811_202414.json"
    
    checker = JsonImageChecker(json_file_path)
    print(checker.contains_images())
