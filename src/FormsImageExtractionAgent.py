import os
import sys
import warnings
from PIL import Image
import torch

warnings.filterwarnings("ignore")

try:
    from transformers import AutoProcessor, AutoModelForImageTextToText
except ImportError as e:
    print("Erreur: Les dépendances requises ne sont pas installées.")
    print("Veuillez installer les dépendances avec: pip install transformers torch pillow")
    print(f"Détail de l'erreur: {e}")
    sys.exit(1)

import json

class OCRExtractor:
    def __init__(self):
        self.processor = None
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self._load_model()
    
    def _load_model(self):
        try:
            self.processor = AutoProcessor.from_pretrained("JackChew/Qwen2-VL-2B-OCR")
            self.model = AutoModelForImageTextToText.from_pretrained("JackChew/Qwen2-VL-2B-OCR")
            self.model = self.model.to(self.device)
        except Exception as e:
            sys.exit(1)
    
    def extract_text_from_image(self, image_path, prompt="Extract all text from this image"):
        try:
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image non trouvée: {image_path}")
            
            image = Image.open(image_path)
            
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            conversation = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]
            
            text_prompt = self.processor.apply_chat_template(conversation, add_generation_prompt=True)
            inputs = self.processor(text=[text_prompt], images=[image], padding=True, return_tensors="pt")
            inputs = inputs.to(self.device)
            
            with torch.no_grad():
                output_ids = self.model.generate(**inputs, max_new_tokens=2048)
                generated_ids = [output_ids[len(input_ids):] for input_ids, output_ids in zip(inputs.input_ids, output_ids)]
                output_text = self.processor.batch_decode(generated_ids, skip_special_tokens=True, clean_up_tokenization_spaces=True)
            
            return output_text[0] if output_text else None
            
        except Exception as e:
            return None
    
    def extract_payslip_data(self, image_path):
        prompt = "extract all data from this payslip without miss anything"
        return self.extract_text_from_image(image_path, prompt)
    
    def process_multiple_images(self, image_folder, prompt="Extract all text from this image"):
        if not os.path.exists(image_folder):
            return {}
        
        results = {}
        supported_formats = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp')
        
        for filename in os.listdir(image_folder):
            if filename.lower().endswith(supported_formats):
                image_path = os.path.join(image_folder, filename)
                
                text = self.extract_text_from_image(image_path, prompt)
                results[filename] = text
        
        return results
    
    def save_results_to_json(self, results, output_file="extracted_text.json"):
        data_to_append = []
        if isinstance(results, dict):
            for filename, text in results.items():
                data_to_append.append({"filename": filename, "text": text})
        else:
            data_to_append.append({"filename": None, "text": results})

        if os.path.exists(output_file):
            try:
                with open(output_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            except Exception:
                existing_data = []
        else:
            existing_data = []

        existing_data.extend(data_to_append)

        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            pass

if __name__ == "__main__":
    ocr_extractor = OCRExtractor()
    folder_path = "./images"
    output_folder = "./output"
    os.makedirs(output_folder, exist_ok=True)
    results = ocr_extractor.process_multiple_images(folder_path)
    output_file = os.path.join(output_folder, "extracted_text.json")
    ocr_extractor.save_results_to_json(results, output_file)

    
