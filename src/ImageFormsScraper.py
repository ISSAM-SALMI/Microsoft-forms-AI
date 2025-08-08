import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import time
import os
import requests


class MicrosoftFormsImageExtractor:
    
    def __init__(self, headless=True, images_folder="images"):
        self.headless = headless
        self.images_folder = images_folder
        self.driver = None
        
    def _setup_driver(self):
        options = uc.ChromeOptions()
        if self.headless:
            options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        
        self.driver = uc.Chrome(version_main=116, options=options)
        
    def _create_images_folder(self):
        os.makedirs(self.images_folder, exist_ok=True)
        
    def _download_image(self, src, filename):
        try:
            response = requests.get(src, timeout=10)
            response.raise_for_status()
            
            filepath = os.path.join(self.images_folder, filename)
            with open(filepath, "wb") as f:
                f.write(response.content)
            return True
        except Exception as e:
            return False
    
    def extract_images(self, form_url):
        stats = {
            'questions_found': 0,
            'images_found': 0,
            'images_downloaded': 0,
            'errors': []
        }
        
        try:
            self._setup_driver()
            self._create_images_folder()
            
            self.driver.get(form_url)
            time.sleep(7)
            
            question_list = self.driver.find_element(By.ID, "question-list")
            question_items = question_list.find_elements(
                By.XPATH, ".//div[contains(@data-automation-id, 'questionItem')]"
            )
            
            stats['questions_found'] = len(question_items)
            
            for i, item in enumerate(question_items):
                try:
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", item)
                    time.sleep(1.5)
                    
                    imgs = item.find_elements(By.XPATH, ".//img")
                    stats['images_found'] += len(imgs)
                    
                    for j, img in enumerate(imgs):
                        src = img.get_attribute("src")
                        if src and src.startswith("http"):
                            filename = f"image_{i+1}_{j+1}.jpg"
                            
                            if self._download_image(src, filename):
                                stats['images_downloaded'] += 1
                            
                except Exception as e:
                    error_msg = f"Erreur pour la question {i+1} : {e}"
                    stats['errors'].append(error_msg)
                    
        except Exception as e:
            error_msg = f"Erreur générale : {e}"
            stats['errors'].append(error_msg)
            
        finally:
            if self.driver:
                self.driver.quit()
                
        return stats

if __name__ == "__main__":
    extractor = MicrosoftFormsImageExtractor(headless=True, images_folder="images")
    
    form_url = "https://forms.office.com/Pages/ResponsePage.aspx?id=DQSIkWdsW0yxEjajBLZtrQAAAAAAAAAAAAN__4uyZYJUQkNTQlZaTkg3NVFVMUlTRjJFT0tBNDJTVS4u"
    
    stats = extractor.extract_images(form_url)