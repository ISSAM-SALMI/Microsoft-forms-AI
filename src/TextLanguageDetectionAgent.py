from langdetect import detect, DetectorFactory
from langcodes import Language

DetectorFactory.seed = 0

class LanguageDetector:
    def detect_language(self, text):
        lang_code = detect(text)
        lang_name = Language.get(lang_code).display_name()
        return lang_name

if __name__ == "__main__":
    text = "猿も木から落ちる — Even monkeys fall from trees."
    detector = LanguageDetector()
    lang = detector.detect_language(text)
    print(lang)
