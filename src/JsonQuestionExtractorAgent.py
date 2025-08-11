import json
from pathlib import Path

class JsonQuestionExtractor:
    def __init__(self, json_path: str):
        self.json_path = Path(json_path)

    def extract_questions_data(self) -> dict:
        """Extract question types, questions, and answer values from JSON file."""
        if not self.json_path.exists():
            raise FileNotFoundError(f"File not found: {self.json_path}")

        with open(self.json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        extracted_data = {
            "file_name": self.json_path.name,
            "total_questions": 0,
            "questions_details": []
        }

        if "questions" in data:
            extracted_data["total_questions"] = len(data["questions"])
            
            for question in data["questions"]:
                # Get main question text
                main_question_text = question.get("question_text", "N/A")
                
                # Check if there's OCR text in images
                ocr_texts = []
                if "images" in question and isinstance(question["images"], list):
                    for image in question["images"]:
                        if isinstance(image, dict) and "question_text" in image:
                            ocr_texts.append(image["question_text"])
                
                # Combine main text and OCR texts if available
                full_question_text = main_question_text
                if ocr_texts:
                    full_question_text += " | OCR: " + " | ".join(ocr_texts)
                
                question_info = {
                    "question_number": question.get("question_number", "N/A"),
                    "question_text": full_question_text,
                    "answer_type": question.get("answer_type", "N/A"),
                    "answer_values": question.get("answer_values", [])
                }
                extracted_data["questions_details"].append(question_info)

        return extracted_data

    def print_questions_data(self):
        """Print the extracted questions data in a formatted way."""
        try:
            data = self.extract_questions_data()
            
            print(f"📁 Fichier: {data['file_name']}")
            print(f"📊 Nombre total de questions: {data['total_questions']}")
            print("-" * 60)
            
            for question in data["questions_details"]:
                print(f"   Texte: {question['question_text']}")
                print(f"   Type: {question['answer_type']}")
                print(f"   Réponses possibles:")
                
                if isinstance(question['answer_values'], list):
                    for i, answer in enumerate(question['answer_values'], 1):
                        print(f"      {i}. {answer}")
                else:
                    print(f"      {question['answer_values']}")
                
        except Exception as e:
            print(f"❌ Erreur: {e}")


# Exemple d'utilisation
if __name__ == "__main__":
    json_file_path = r"C:\Users\abdel\OneDrive\Bureau\Microsoft-forms-AI\data\output\jsons\microsoft_forms_complete_data_20250811_202325_with_ocr_20250811_205151.json"
    
    extractor = JsonQuestionExtractor(json_file_path)
    extractor.print_questions_data()
