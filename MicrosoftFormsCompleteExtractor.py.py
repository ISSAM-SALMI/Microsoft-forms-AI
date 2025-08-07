import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import time
import json
import os
import requests
from datetime import datetime
import warnings
import gc


class MicrosoftFormsCompleteScraper:
    def __init__(self, url, headless=False, images_folder="images", output_folder="output"):
        self.url = url
        self.headless = headless
        self.images_folder = images_folder
        self.output_folder = output_folder
        self.driver = None
        self.scraped_data = {
            "url": url,
            "scraping_date": datetime.now().isoformat(),
            "questions": [],
            "statistics": {
                "total_questions": 0,
                "questions_with_text": 0,
                "questions_with_images": 0,
                "total_images_downloaded": 0,
                "errors": []
            }
        }
    
    def _init_driver(self):
        """Initialize Chrome driver with proper options"""
        try:
            options = uc.ChromeOptions()
            if self.headless:
                options.add_argument("--headless=new")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--disable-web-security")
            options.add_argument("--allow-running-insecure-content")
            
            self.driver = uc.Chrome(options=options)
            return True
        except Exception as e:
            self.scraped_data["statistics"]["errors"].append(f"Erreur d'initialisation du driver: {str(e)}")
            return False
    
    def _close_driver_safely(self):
        """Safely close the Chrome driver"""
        if self.driver:
            try:
                warnings.filterwarnings("ignore")
                
                driver_ref = self.driver
                self.driver = None  
                
                try:
                    handles = driver_ref.window_handles.copy()
                    for handle in handles:
                        try:
                            driver_ref.switch_to.window(handle)
                            driver_ref.close()
                        except:
                            pass
                except:
                    pass
                try:
                    driver_ref.quit()
                except:
                    pass
                
                try:
                    if hasattr(driver_ref, 'service') and hasattr(driver_ref.service, 'process'):
                        if driver_ref.service.process and driver_ref.service.process.poll() is None:
                            driver_ref.service.process.terminate()
                            driver_ref.service.process.wait(timeout=3)
                except:
                    pass
                    
                try:
                    if hasattr(driver_ref, 'service') and hasattr(driver_ref.service, 'process'):
                        if driver_ref.service.process and driver_ref.service.process.poll() is None:
                            driver_ref.service.process.kill()
                except:
                    pass
                
                try:
                    del driver_ref
                except:
                    pass
                    
            except Exception as e:
                pass  
                    
            finally:
                self.driver = None
                gc.collect()

    def _create_folders(self):
        """Create necessary folders for images and output"""
        os.makedirs(self.images_folder, exist_ok=True)
        os.makedirs(self.output_folder, exist_ok=True)
        
    def _download_image(self, src, filename):
        """Download image from URL"""
        try:
            response = requests.get(src, timeout=10)
            response.raise_for_status()
            
            filepath = os.path.join(self.images_folder, filename)
            with open(filepath, "wb") as f:
                f.write(response.content)
            return filepath
        except Exception as e:
            self.scraped_data["statistics"]["errors"].append(f"Erreur téléchargement image {filename}: {str(e)}")
            return None
    
    def _extract_question_text(self, question_item):
        """Extract text content from a question item"""
        try:
            text_elements = question_item.find_elements(By.CLASS_NAME, "text-format-content")
            if text_elements:
                return text_elements[0].text.strip()
            return ""
        except Exception as e:
            return ""
    
    def _extract_question_images(self, question_item, question_number):
        """Extract and download images from a question item"""
        downloaded_images = []
        try:
            self.driver.execute_script("arguments[0].scrollIntoView(true);", question_item)
            time.sleep(1)
            
            imgs = question_item.find_elements(By.XPATH, ".//img")
            
            for j, img in enumerate(imgs, 1):
                try:
                    src = img.get_attribute("src")
                    if src and src.startswith("http"):
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"question_{question_number}_image_{j}_{timestamp}.jpg"
                        
                        filepath = self._download_image(src, filename)
                        if filepath:
                            downloaded_images.append({
                                "image_number": j,
                                "filename": filename,
                                "filepath": filepath,
                                "original_src": src
                            })
                            self.scraped_data["statistics"]["total_images_downloaded"] += 1
                            
                except Exception as e:
                    error_msg = f"Erreur extraction image {j} de la question {question_number}: {str(e)}"
                    self.scraped_data["statistics"]["errors"].append(error_msg)
                    
        except Exception as e:
            error_msg = f"Erreur générale extraction images question {question_number}: {str(e)}"
            self.scraped_data["statistics"]["errors"].append(error_msg)
            
        return downloaded_images

    def run(self):
        """Main scraping method that combines text and image extraction"""
        if not self._init_driver():
            self.scraped_data["error"] = "Impossible d'initialiser le driver Chrome"
            return self.scraped_data
            
        try:
            self._create_folders()
            
            print(f"Navigation vers: {self.url}")
            self.driver.get(self.url)
            time.sleep(5)

            question_list = self.driver.find_element(By.ID, "question-list")
            question_list = self.driver.find_element(By.ID, "question-list")
            question_items = question_list.find_elements(
                By.XPATH, ".//div[contains(@data-automation-id, 'questionItem')]"
            )
            
            self.scraped_data["statistics"]["total_questions"] = len(question_items)
            print(f"Nombre de questions trouvées: {len(question_items)}")
            
            for i, item in enumerate(question_items, 1):
                print(f"Traitement de la question {i}/{len(question_items)}...")
                
                try:
                    question_text = self._extract_question_text(item)
                    
                    images = self._extract_question_images(item, i)
                    
                    question_data = {
                        "question_number": i,
                        "question_text": question_text,
                        "has_text": bool(question_text),
                        "has_images": len(images) > 0,
                        "images_count": len(images),
                        "images": images,
                        "scraped_at": datetime.now().isoformat()
                    }
                    
                    if question_text:
                        self.scraped_data["statistics"]["questions_with_text"] += 1
                    if images:
                        self.scraped_data["statistics"]["questions_with_images"] += 1
                    
                    self.scraped_data["questions"].append(question_data)
                    
                    print(f"  - Texte: {'✓' if question_text else '✗'}")
                    print(f"  - Images: {len(images)} téléchargée(s)")
                    
                except Exception as e:
                    error_msg = f"Erreur traitement question {i}: {str(e)}"
                    self.scraped_data["statistics"]["errors"].append(error_msg)
                    print(f"  - Erreur: {error_msg}")

        except Exception as e:
            self.scraped_data["error"] = str(e)
            print(f"Erreur générale: {str(e)}")

        finally:
            self._close_driver_safely()
        
        return self.scraped_data

    def save_to_json(self, filename=None):
        """Save scraped data to JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"microsoft_forms_complete_data_{timestamp}.json"
        
        filepath = os.path.join(self.output_folder, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.scraped_data, f, indent=2, ensure_ascii=False)
            return filepath
        except Exception as e:
            print(f"Erreur sauvegarde JSON: {str(e)}")
            return None

    def print_summary(self):
        """Print a summary of the scraping results"""
        stats = self.scraped_data["statistics"]
        print("\n" + "="*60)
        print("RÉSUMÉ DU SCRAPING".center(60))
        print("="*60)
        print(f"URL du formulaire: {self.url}")
        print(f"Date de scraping: {self.scraped_data['scraping_date']}")
        print("-"*60)
        print(f"Questions totales: {stats['total_questions']}")
        print(f"Questions avec texte: {stats['questions_with_text']}")
        print(f"Questions avec images: {stats['questions_with_images']}")
        print(f"Images téléchargées: {stats['total_images_downloaded']}")
        print(f"Erreurs: {len(stats['errors'])}")
        
        if stats['errors']:
            print("\nERREURS RENCONTRÉES:")
            for error in stats['errors'][:5]:
                print(f"  - {error}")
            if len(stats['errors']) > 5:
                print(f"  ... et {len(stats['errors']) - 5} autres erreurs")
        print("="*60)


if __name__ == "__main__":
    import warnings
    warnings.filterwarnings("ignore")
    uc.Chrome.__del__ = lambda self: None

    try:
        url = input("Saisir l'URL du formulaire Microsoft Forms : ").strip()
        if not url.startswith("http"):
            raise ValueError("L'URL saisie est invalide.")

        headless_input = input("Mode headless (o/n) [défaut: n] : ").strip().lower()
        headless = headless_input in ['o', 'oui', 'y', 'yes']

        scraper = MicrosoftFormsCompleteScraper(
            url=url,
            headless=headless,
            images_folder="images",
            output_folder="output"
        )

        print("\nDémarrage du scraping...")
        data = scraper.run()

        output_path = scraper.save_to_json()

        scraper.print_summary()

        if output_path:
            print(f"\nDonnées sauvegardées dans: {output_path}")
            print(f"Images sauvegardées dans: {scraper.images_folder}/")
        else:
            print("\nÉchec de la sauvegarde JSON.")

    except KeyboardInterrupt:
        print("\nScraping interrompu par l'utilisateur.")
    except Exception as e:
        print(f"\nUne erreur s'est produite: {str(e)}")
