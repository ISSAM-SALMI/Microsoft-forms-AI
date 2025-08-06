import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import time
import json
import os
from datetime import datetime
import atexit
import sys
import warnings
import gc
import contextlib

class MicrosoftFormsScraper:
    def __init__(self, url):
        self.url = url
        self.driver = None
        self.scraped_data = {
            "url": url,
            "scraping_date": datetime.now().isoformat(),
            "questions": []
        }
    
    def _init_driver(self):
        """Initialize Chrome driver with proper options"""
        try:
            options = uc.ChromeOptions()
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--disable-web-security")
            options.add_argument("--allow-running-insecure-content")
            
            self.driver = uc.Chrome(options=options)
            return True
        except Exception as e:
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
                    
                # Force kill if still running
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

    def run(self):
        if not self._init_driver():
            self.scraped_data["error"] = "Impossible d'initialiser le driver Chrome"
            return self.scraped_data
            
        try:
            self.driver.get(self.url)
            time.sleep(5)

            question_list = self.driver.find_element(By.ID, "question-list")
            question_items = question_list.find_elements(
                By.XPATH, ".//div[contains(@data-automation-id, 'questionItem')]"
            )
            
            for i, item in enumerate(question_items, 1):
                items = item.find_elements(By.CLASS_NAME, "text-format-content")
                question_text = items[0].text if items else "Question non trouvée"
                
                question_data = {
                    "question_number": i,
                    "question_text": question_text,
                    "scraped_at": datetime.now().isoformat()
                }
                
                self.scraped_data["questions"].append(question_data)

        except Exception as e:
            self.scraped_data["error"] = str(e)

        finally:
            self._close_driver_safely()
        
        return self.scraped_data

    def save_to_json(self, filename=None):
        """Save scraped data to JSON file"""
        if filename is None:
            # Create filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"microsoft_forms_data_{timestamp}.json"
        
        output_dir = "output"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        filepath = os.path.join(output_dir, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.scraped_data, f, indent=2, ensure_ascii=False)
            return filepath
        except Exception as e:
            return None
if __name__ == "__main__":
    import warnings
    warnings.filterwarnings("ignore")
    uc.Chrome.__del__ = lambda self: None

    try:
        url = input("Saisir l'URL du formulaire Microsoft Forms : ").strip()
        if not url.startswith("http"):
            raise ValueError("L'URL saisie est invalide.")

        scraper = MicrosoftFormsScraper(url)
        data = scraper.run()
        output_path = scraper.save_to_json()

        if output_path:
            print("\nDonnées bien enregistrées dans :".center(70))
            print(output_path.center(70))
        else:
            print("Échec de l'enregistrement JSON.".center(70))

    except Exception as e:
        print("\nUne erreur s'est produite :".center(70))
        print(str(e).center(70))

