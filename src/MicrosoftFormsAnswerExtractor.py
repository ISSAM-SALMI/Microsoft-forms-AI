import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import time
import gc

class MicrosoftFormsScraper:
    def __init__(self, url):
        self.url = url
        self.driver = None

    def start_browser(self):
        options = uc.ChromeOptions()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-web-security")
        options.add_argument("--allow-running-insecure-content")
        print("Initialisation du navigateur...")
        self.driver = uc.Chrome(
            version_main=118,
            options=options,
            enable_cdp_events=True,
            use_subprocess=False
        )

    def questionType(self, qst):
        qst_types = ['choiceItem', 'textInput', 'npsContainer']
        for qst_type in qst_types:
            try:
                qst.find_element(By.CSS_SELECTOR, f'[data-automation-id="{qst_type}"]')
                return qst_type
            except:
                continue
        return "unknown"

    def textInput(self, qst):
        return "Input text"
    
    def choiceItem(self, qst):
        items = qst.find_elements(By.CSS_SELECTOR, '[data-automation-id="choiceItem"]')
        return [item.text for item in items]
    def npsContainer(self, qst):
        question = qst.find_element(By.CSS_SELECTOR, f'[data-automation-id="npsContainer"]')
        tbody = question.find_element(By.TAG_NAME, 'tbody')
        td = tbody.find_elements(By.TAG_NAME, 'td')
        return [td.find_element(By.TAG_NAME, 'span').text for td in td]

    def scrape(self):
        try:
            self.start_browser()
            print(f"Navigation vers: {self.url}")
            self.driver.get(self.url)
            time.sleep(5)
            print("Page chargée avec succès!")
            questionItems = self.driver.find_elements(By.CSS_SELECTOR, '[data-automation-id="questionItem"]')
            print(f"Nombre de questions trouvées: {len(questionItems)}")
            for idx, qst in enumerate(questionItems, 1):
                qst_type = self.questionType(qst)
                print(f"Question {idx}:")
                print(f"  Type de question: {qst_type}")
                value = None
                if qst_type == "choiceItem":
                    value = self.choiceItem(qst)
                elif qst_type == "npsContainer":
                    value = self.npsContainer(qst)
                elif qst_type == "textInput":
                    value = self.textInput(qst)
                else:
                    value = "Type de question non reconnu"
                print(f"  Valeur: {value}")
        except Exception as e:
            print(f"Erreur: {str(e)}")
        finally:
            self.close_browser()

    def close_browser(self):
        if self.driver is not None:
            try:
                self.driver.quit()
                print("Navigateur fermé proprement.")
            except Exception as e:
                print(f"Erreur lors de la fermeture propre: {str(e)}")
                try:
                    self.driver.close()
                    print("Navigateur fermé avec close().")
                except Exception as e:
                    print(f"Erreur lors de la fermeture avec close(): {str(e)}")
            finally:
                del self.driver
                gc.collect()