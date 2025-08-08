import json
import os
import sys
from datetime import datetime
from pathlib import Path

try:
    import easyocr
    OCR_ENGINE = "easyocr"
    print("Utilisation d'EasyOCR")
except ImportError:
    try:
        import pytesseract
        from PIL import Image
        OCR_ENGINE = "pytesseract"
        print("Utilisation de Pytesseract")
    except ImportError:
        print("Aucun moteur OCR disponible.")
        print("Installez EasyOCR avec: pip install easyocr")
        print("Ou Pytesseract avec: pip install pytesseract pillow")
        sys.exit(1)

class FormsOCRProcessor:
    def __init__(self, base_path=None):
        if base_path is None:
            self.base_path = Path(__file__).parent.parent / "src"
        else:
            self.base_path = Path(base_path)
        
        if OCR_ENGINE == "easyocr":
            self.reader = easyocr.Reader(['en', 'fr', 'de'])
        elif OCR_ENGINE == "pytesseract":
            self.reader = None
        
        print(f"OCR Processor initialisé avec {OCR_ENGINE}")
    
    def load_json_data(self, json_path):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"JSON chargé: {len(data.get('questions', []))} questions trouvées")
            return data
        except Exception as e:
            print(f"Erreur lors du chargement du JSON: {e}")
            return None
    
    def get_absolute_image_path(self, relative_path):
        if os.path.isabs(relative_path):
            return relative_path
        
        clean_path = relative_path.replace('\\', os.sep).replace('/', os.sep)
        
        if clean_path.startswith('data'):
            clean_path = clean_path[len('data' + os.sep):]
        
        full_path = self.base_path / "data" / clean_path
        return str(full_path)
    
    def extract_text_from_image(self, image_path):
        try:
            if not os.path.exists(image_path):
                print(f"Image non trouvée: {image_path}")
                return "Image non trouvée"
            
            print(f"Traitement OCR: {os.path.basename(image_path)}")
            
            if OCR_ENGINE == "easyocr":
                results = self.reader.readtext(image_path)
                extracted_text = ' '.join([result[1] for result in results])
            elif OCR_ENGINE == "pytesseract":
                image = Image.open(image_path)
                extracted_text = pytesseract.image_to_string(image, lang='eng+fra+deu')
            else:
                return "Moteur OCR non configuré"
            
            if extracted_text and extracted_text.strip():
                print(f"Texte extrait: {len(extracted_text)} caractères")
                return extracted_text.strip()
            else:
                print("Aucun texte extrait")
                return "Aucun texte détecté"
                
        except Exception as e:
            print(f"Erreur OCR: {e}")
            return f"Erreur OCR: {str(e)}"
    
    def process_json_with_ocr(self, json_path):
        data = self.load_json_data(json_path)
        if not data:
            return None
        
        print(f"\nDébut du traitement OCR pour {len(data.get('questions', []))} questions...")
        
        total_images_processed = 0
        
        for question in data.get('questions', []):
            question_num = question.get('question_number', 'N/A')
            print(f"\nQuestion {question_num}:")
            
            if question.get('has_images', False) and question.get('images'):
                for image_info in question['images']:
                    relative_path = image_info.get('filepath', '')
                    absolute_path = self.get_absolute_image_path(relative_path)
                    
                    print(f"  Chemin: {absolute_path}")
                    
                    extracted_text = self.extract_text_from_image(absolute_path)
                    
                    image_info['ocr_extracted_text'] = extracted_text
                    image_info['ocr_processed_at'] = datetime.now().isoformat()
                    
                    total_images_processed += 1
            else:
                print("  Pas d'images dans cette question")
        
        data['ocr_processing'] = {
            'processed_at': datetime.now().isoformat(),
            'total_images_processed': total_images_processed,
            'ocr_agent_version': '1.0'
        }
        
        print(f"\nTraitement terminé: {total_images_processed} images traitées")
        return data
    
    def save_enhanced_json(self, enhanced_data, original_json_path):
        if not enhanced_data:
            print("Aucune donnée à sauvegarder")
            return None
        
        original_path = Path(original_json_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        new_filename = f"{original_path.stem}_with_ocr_{timestamp}{original_path.suffix}"
        output_path = original_path.parent / new_filename
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(enhanced_data, f, indent=2, ensure_ascii=False)
            
            print(f"JSON enrichi sauvegardé: {output_path}")
            return str(output_path)
            
        except Exception as e:
            print(f"Erreur lors de la sauvegarde: {e}")
            return None
    
    def print_summary(self, enhanced_data):
        if not enhanced_data:
            return
        
        ocr_info = enhanced_data.get('ocr_processing', {})
        questions = enhanced_data.get('questions', [])
        
        print("\n" + "="*60)
        print("RÉSUMÉ DU TRAITEMENT OCR".center(60))
        print("="*60)
        print(f"Questions totales: {len(questions)}")
        print(f"Images traitées: {ocr_info.get('total_images_processed', 0)}")
        print(f"Date de traitement: {ocr_info.get('processed_at', 'N/A')}")
        
        questions_with_ocr = sum(1 for q in questions if any(
            'ocr_extracted_text' in img for img in q.get('images', [])
        ))
        print(f"Questions avec OCR: {questions_with_ocr}")
        
        print("\nDÉTAIL PAR QUESTION:")
        for question in questions:
            q_num = question.get('question_number', 'N/A')
            images_count = len(question.get('images', []))
            ocr_count = sum(1 for img in question.get('images', []) if 'ocr_extracted_text' in img)
            print(f"  Question {q_num}: {ocr_count}/{images_count} images avec OCR")
        
        print("="*60)

def main():
    json_path = r"C:\Users\abdel\OneDrive\Bureau\Microsoft-forms-AI\src\data\output\jsons\microsoft_forms_complete_data_20250808_173742.json"
    
    if not os.path.exists(json_path):
        print(f"Fichier JSON non trouvé: {json_path}")
        return
    
    print("FormsOCRProcessor - Agent de traitement OCR")
    print("="*60)
    print(f"Fichier d'entrée: {json_path}")
    
    processor = FormsOCRProcessor()
    
    enhanced_data = processor.process_json_with_ocr(json_path)
    
    if enhanced_data:
        output_path = processor.save_enhanced_json(enhanced_data, json_path)
        processor.print_summary(enhanced_data)
        
        if output_path:
            print(f"\nTraitement réussi! Fichier de sortie: {output_path}")
        else:
            print("\nErreur lors de la sauvegarde")
    else:
        print("\nÉchec du traitement")

if __name__ == "__main__":
    main()
