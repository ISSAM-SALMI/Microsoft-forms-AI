import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import time
import json
import os
import requests
from datetime import datetime
import warnings
import gc
from .AnswerMiningAgent import MicrosoftFormsScraper as AnswerAnalyzer
from .logging_utils import log

# Patch Chrome destructor early to avoid WinError 6 on GC (Windows handle invalid)
try:  # pragma: no cover
    if hasattr(uc, 'Chrome') and hasattr(uc.Chrome, '__del__'):
        uc.Chrome.__del__ = lambda self: None  # neutralize library __del__
        log('SCRAPE', 'Patch destructor Chrome (__del__) appliqué', level='DEBUG')
except Exception:
    pass



class MicrosoftFormsCompleteScraper:
    def __init__(self, url, headless=True, images_folder="images", output_folder="output"):
        self.url = url
        self.headless = headless
        self.images_folder = images_folder
        self.output_folder = output_folder
        self.driver = None
        self.scraped_data = {
            "url": url,
            "scraping_date": datetime.now().isoformat(),
            "contains_images": False,
            "questions": [],
            "statistics": {
                "total_questions": 0,
                "questions_with_text": 0,
                "questions_with_images": 0,
                "total_images_downloaded": 0,
                "answer_types": {},
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

    def _analyze_question_answer_type(self, question_item):
        """Analyze question answer type and extract possible values"""
        try:
            analyzer = AnswerAnalyzer(self.url)
            analyzer.driver = self.driver
            
            question_type = analyzer.questionType(question_item)
            answer_values = None
            
            if question_type == "choiceItem":
                answer_values = analyzer.choiceItem(question_item)
            elif question_type == "npsContainer":
                answer_values = analyzer.npsContainer(question_item)
            elif question_type == "textInput":
                answer_values = analyzer.textInput(question_item)
            else:
                answer_values = "Type de question non reconnu"
            
            return {
                "answer_type": question_type,
                "answer_values": answer_values
            }
        except Exception as e:
            error_msg = f"Erreur analyse type réponse: {str(e)}"
            self.scraped_data["statistics"]["errors"].append(error_msg)
            return {
                "answer_type": "unknown",
                "answer_values": "Erreur d'analyse"
            }

    def run(self):
        """Main scraping method that combines text and image extraction"""
        if not self._init_driver():
            self.scraped_data["error"] = "Impossible d'initialiser le driver Chrome"
            return self.scraped_data
        # Hard reference for explicit shutdown control
        driver_local = self.driver
        try:
            self._create_folders()
            log('SCRAPE', f"Navigation: {self.url}")
            self.driver.get(self.url)
            time.sleep(5)

            question_list = self.driver.find_element(By.ID, "question-list")
            question_items = question_list.find_elements(
                By.XPATH, ".//div[contains(@data-automation-id, 'questionItem')]"
            )
            
            self.scraped_data["statistics"]["total_questions"] = len(question_items)
            log('SCRAPE', f"Questions trouvées: {len(question_items)}")
            
            for i, item in enumerate(question_items, 1):
                log('SCRAPE', f"Question {i}/{len(question_items)}", indent=1)
                
                try:
                    question_text = self._extract_question_text(item)
                    
                    images = self._extract_question_images(item, i)
                    
                    answer_analysis = self._analyze_question_answer_type(item)
                    
                    question_data = {
                        "question_number": i,
                        "question_text": question_text,
                        "has_text": bool(question_text),
                        "has_images": len(images) > 0,
                        "images_count": len(images),
                        "images": images,
                        "answer_type": answer_analysis["answer_type"],
                        "answer_values": answer_analysis["answer_values"],
                        "scraped_at": datetime.now().isoformat()
                    }
                    
                    if question_text:
                        self.scraped_data["statistics"]["questions_with_text"] += 1
                    if images:
                        self.scraped_data["statistics"]["questions_with_images"] += 1
                    
                    answer_type = answer_analysis["answer_type"]
                    if answer_type in self.scraped_data["statistics"]["answer_types"]:
                        self.scraped_data["statistics"]["answer_types"][answer_type] += 1
                    else:
                        self.scraped_data["statistics"]["answer_types"][answer_type] = 1
                    
                    self.scraped_data["questions"].append(question_data)
                    
                    log('SCRAPE', f"Texte: {'✓' if question_text else '✗'}", indent=2)
                    log('SCRAPE', f"Images: {len(images)}", indent=2)
                    log('SCRAPE', f"Type: {answer_analysis['answer_type']}", indent=2)
                    log('SCRAPE', f"Valeurs: {str(answer_analysis['answer_values'])[:120]}", indent=2)
                    
                except Exception as e:
                    error_msg = f"Erreur traitement question {i}: {str(e)}"
                    self.scraped_data["statistics"]["errors"].append(error_msg)
                    log('SCRAPE', f"Erreur: {error_msg}", level='ERROR', indent=2)

        except Exception as e:
            self.scraped_data["error"] = str(e)
            log('SCRAPE', f"Erreur générale: {e}", level='ERROR')

        finally:
            try:
                if driver_local:
                    # Explicit quit to avoid late GC destructor call
                    try:
                        driver_local.quit()
                    except Exception:
                        pass
            finally:
                self._close_driver_safely()
        
        # Set top-level flag indicating if the form contains any images
        try:
            self.scraped_data["contains_images"] = (
                self.scraped_data["statistics"]["questions_with_images"] > 0 or
                self.scraped_data["statistics"]["total_images_downloaded"] > 0
            )
        except Exception:
            self.scraped_data["contains_images"] = False
        
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
            log('SCRAPE', f"Erreur sauvegarde JSON: {e}", level='ERROR')
            return None

    def print_summary(self):
        """Print a summary of the scraping results"""
        stats = self.scraped_data["statistics"]
        log('SCRAPE', f"URL: {self.url}")
        log('SCRAPE', f"Date: {self.scraped_data['scraping_date']}")
        log('SCRAPE', f"Totales: {stats['total_questions']}")
        log('SCRAPE', f"Avec texte: {stats['questions_with_text']}")
        log('SCRAPE', f"Avec images: {stats['questions_with_images']}")
        log('SCRAPE', f"Images téléchargées: {stats['total_images_downloaded']}")
        log('SCRAPE', f"Erreurs: {len(stats['errors'])}")
        if stats['answer_types']:
            for answer_type, count in stats['answer_types'].items():
                log('SCRAPE', f"Type {answer_type}: {count}", indent=1)
        if stats['errors']:
            for error in stats['errors'][:5]:
                log('SCRAPE', f"Err: {error}", level='ERROR', indent=1)
            if len(stats['errors']) > 5:
                log('SCRAPE', f"... {len(stats['errors']) - 5} erreurs supplémentaires", level='WARN', indent=1)


if __name__ == "__main__":
    import warnings
    warnings.filterwarnings("ignore")
    uc.Chrome.__del__ = lambda self: None  # éviter exceptions dans le GC

    try:
        # Utiliser l'URL par défaut définie en haut du fichier.
        url = "https://forms.office.com/Pages/ResponsePage.aspx?id=DQSIkWdsW0yxEjajBLZtrQAAAAAAAAAAAAN__4uyZYJUQkNTQlZaTkg3NVFVMUlTRjJFT0tBNDJTVS4u"
        if not url.startswith("http"):
            raise ValueError("L'URL configurée est invalide.")

        # Mode headless activé automatiquement
        headless = True

        scraper = MicrosoftFormsCompleteScraper(
            url=url,
            headless=headless,
            images_folder="../data/output/images",
            output_folder="../data/output/jsons"
        )
        log('SCRAPE', 'Démarrage test individuel')
        data = scraper.run()
        output_path = scraper.save_to_json()
        scraper.print_summary()
        if output_path:
            log('SCRAPE', f"JSON: {output_path}")
            log('SCRAPE', f"Images dossier: {scraper.images_folder}")
        else:
            log('SCRAPE', "Échec sauvegarde JSON", level='ERROR')

    except KeyboardInterrupt:
        log('SCRAPE', "Interruption utilisateur", level='WARN')
    except Exception as e:
        log('SCRAPE', f"Erreur exécution: {e}", level='ERROR')
