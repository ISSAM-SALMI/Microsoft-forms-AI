import os
import json
import glob
from pathlib import Path
from datetime import datetime

try:
    import easyocr
    OCR_AVAILABLE = True
    print("EasyOCR disponible")
except ImportError:
    OCR_AVAILABLE = False
    print("EasyOCR non disponible. Installez avec: pip install easyocr")

class FormsImageExtractionAgent:
    def __init__(self, json_folder_path=None):
        if json_folder_path is None:
            self.json_folder_path = Path(r"C:\Users\abdel\OneDrive\Bureau\Microsoft-forms-AI\data\output\jsons")
        else:
            self.json_folder_path = Path(json_folder_path)
        
        self.base_path = Path(r"C:\Users\abdel\OneDrive\Bureau\Microsoft-forms-AI")
        
        if OCR_AVAILABLE:
            self.ocr_reader = easyocr.Reader(['en', 'fr', 'de', 'es', 'it'])
            print("OCR Reader initialisé avec support multi-langues")
        else:
            self.ocr_reader = None
        
        print(f"Agent initialisé avec dossier JSON: {self.json_folder_path}")
    
    def find_json_files(self):
        if not self.json_folder_path.exists():
            print(f"Dossier non trouvé: {self.json_folder_path}")
            return []
        
        json_files = list(self.json_folder_path.glob("*.json"))
        print(f"Fichiers JSON trouvés: {len(json_files)}")
        
        for i, file in enumerate(json_files):
            print(f"  {i+1}. {file.name}")
        
        return json_files
    
    def load_json_file(self, json_file_path):
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"JSON chargé: {json_file_path.name}")
            return data
        except Exception as e:
            print(f"Erreur chargement JSON {json_file_path.name}: {e}")
            return None
    
    def resolve_image_path(self, filepath):
        filepath = str(filepath).replace('\\', os.sep).replace('/', os.sep)
        
        if filepath.startswith('..'):
            filepath = filepath[3:]
        
        if filepath.startswith(os.sep):
            filepath = filepath[1:]
        
        absolute_path = self.base_path / filepath
        return absolute_path
    
    def extract_text_with_easyocr(self, image_path):
        if not OCR_AVAILABLE:
            return "EasyOCR non disponible"
        
        try:
            if not os.path.exists(image_path):
                return "Image non trouvée"
            
            print(f"  Traitement OCR: {os.path.basename(image_path)}")
            
            results = self.ocr_reader.readtext(str(image_path))
            
            if results:
                extracted_text = ' '.join([result[1] for result in results])
                print(f"  Texte extrait: {len(extracted_text)} caractères")
                return extracted_text.strip()
            else:
                print("  Aucun texte détecté")
                return "Aucun texte détecté"
                
        except Exception as e:
            print(f"  Erreur OCR: {e}")
            return f"Erreur OCR: {str(e)}"
    
    def process_json_file(self, json_file_path):
        data = self.load_json_file(json_file_path)
        if not data:
            return None
        
        questions = data.get('questions', [])
        print(f"Traitement de {len(questions)} questions...")
        
        total_images_processed = 0
        
        for question in questions:
            question_num = question.get('question_number', 'N/A')
            print(f"\nQuestion {question_num}:")
            
            images = question.get('images', [])
            if not images:
                print("  Aucune image")
                continue
            
            for image_info in images:
                filepath = image_info.get('filepath', '')
                filename = image_info.get('filename', '')
                
                if not filepath:
                    print(f"  Chemin d'image manquant pour {filename}")
                    continue
                
                absolute_path = self.resolve_image_path(filepath)
                print(f"  Image: {filename}")
                print(f"  Chemin: {absolute_path}")
                
                extracted_text = self.extract_text_with_easyocr(absolute_path)
                
                image_info['ocr_extracted_text'] = extracted_text
                image_info['ocr_processed_at'] = datetime.now().isoformat()
                image_info['ocr_method'] = 'easyocr'
                
                total_images_processed += 1
        
        data['ocr_processing_info'] = {
            'processed_at': datetime.now().isoformat(),
            'total_images_processed': total_images_processed,
            'ocr_method': 'easyocr',
            'agent_version': '2.0'
        }
        
        print(f"\nTraitement terminé: {total_images_processed} images traitées")
        return data
    
    def save_processed_json(self, processed_data, original_file_path):
        if not processed_data:
            print("Aucune donnée à sauvegarder")
            return None
        
        original_path = Path(original_file_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        new_filename = f"{original_path.stem}_with_ocr_{timestamp}.json"
        output_path = original_path.parent / new_filename
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(processed_data, f, indent=2, ensure_ascii=False)
            
            print(f"JSON enrichi sauvegardé: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"Erreur sauvegarde: {e}")
            return None
    
    def process_all_json_files(self):
        json_files = self.find_json_files()
        
        if not json_files:
            print("Aucun fichier JSON trouvé")
            return []
        
        results = []
        
        for json_file in json_files:
            print(f"\n{'='*60}")
            print(f"Traitement du fichier: {json_file.name}")
            print(f"{'='*60}")
            
            processed_data = self.process_json_file(json_file)
            
            if processed_data:
                output_path = self.save_processed_json(processed_data, json_file)
                if output_path:
                    results.append({
                        'original_file': json_file,
                        'processed_file': output_path,
                        'status': 'success'
                    })
                else:
                    results.append({
                        'original_file': json_file,
                        'processed_file': None,
                        'status': 'save_error'
                    })
            else:
                results.append({
                    'original_file': json_file,
                    'processed_file': None,
                    'status': 'process_error'
                })
        
        self.print_summary(results)
        return results
    
    def print_summary(self, results):
        print(f"\n{'='*60}")
        print("RÉSUMÉ DU TRAITEMENT")
        print(f"{'='*60}")
        
        successful = [r for r in results if r['status'] == 'success']
        failed = [r for r in results if r['status'] != 'success']
        
        print(f"Fichiers traités avec succès: {len(successful)}")
        print(f"Fichiers en échec: {len(failed)}")
        
        if successful:
            print("\nFICHIERS TRAITÉS:")
            for result in successful:
                print(f"  ✓ {result['original_file'].name}")
                print(f"    → {result['processed_file'].name}")
        
        if failed:
            print("\nFICHIERS EN ÉCHEC:")
            for result in failed:
                print(f"  ✗ {result['original_file'].name} ({result['status']})")
        
        print(f"{'='*60}")

def main():
    agent = FormsImageExtractionAgent()
    
    if not OCR_AVAILABLE:
        print("Impossible de continuer sans EasyOCR")
        print("Installez avec: pip install easyocr")
        return
    
    print("FormsImageExtractionAgent - Traitement OCR des JSON")
    print("=" * 60)
    
    results = agent.process_all_json_files()
    
    if results:
        print(f"\nTraitement terminé. {len(results)} fichier(s) traité(s).")
    else:
        print("\nAucun fichier traité.")

if __name__ == "__main__":
    main()
