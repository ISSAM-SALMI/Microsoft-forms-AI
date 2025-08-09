import subprocess

class OllamaAgent:
    def __init__(self, model='qwen3:8b'):
        self.model = model

    def extract_final_answer(self, text):
        marker = "...done thinking."
        if marker in text:
            parts = text.split(marker)
            final_part = parts[-1].strip()
            return final_part
        else:
            return text.strip()

    def ask(self, prompt):
        proc = subprocess.Popen(
            ['ollama', 'run', self.model],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = proc.communicate(input=prompt + '\n')
        if stderr:
            print("Erreur Ollama :", stderr)
        answer = self.extract_final_answer(stdout)
        return answer

if __name__ == "__main__":
    agent = OllamaAgent()
    prompt = (
        "Die Shengsi-Inseln liegen im Ostchinesischen Meer. Nicht einmal 20 der rund 400 Inseln sind bewohnt, "
        "und manche, auf denen einst Menschen lebten, wurden wieder verlassen. Ein altes Dorf auf der nun unbewohnten Insel Shengsan "
        "ist zu einer Sehenswürdigkeit geworden. Die Einwohner haben das ehemalige Fischerdorf auf der viereinhalb Quadratkilometer "
        "Insel längst verlassen. Sie sind aus wirtschaftlichen Gründen auf das Festland gezogen. Dort ist es für sie leichter, "
        "Fischfang zu verarbeiten und zu verkaufen. Das Dorf aber, das sie zurückgelassen haben, ist in kürzester Zeit von der Natur "
        "zurückerobert worden. Farne und Gräser überwuchern Häuser, und die Grenzen zwischen den von Menschenhand geschaffenen Gebäuden "
        "und dem umliegenden Urwald verschwinden. Das Mauerwerk ist von wildem Wein überwuchert; Grün soweit das Auge reicht. "
        "An diesem Ort lebt keine Menschenseele mehr.\n"
        "a) Deutscher Forscher startet Expedition auf Vogelinsel in Südamerika\n"
        "b) Die beliebtesten Reiseziele unter den europäischen Inseln\n"
        "c) Fernreisen in eine unberührte Tierwelt\n"
        "d) Geführte Bootsausflüge zu einsamen Badebuchten\n"
        "e) Grüne Geisterinsel in Asien\n"
        "f) Immer mehr Reiseunternehmen streichen Thailand aus ihrem Angebot\n"
        "g) Inseln zählen weltweit zu den wichtigsten Reisedestinationen\n"
        "h) Nachhaltiger Tourismus auf chinesischen Inseln\n"
        "i) Tierparadies auf einer Nordseeinsel\n"
        "j) Umstrittener Umgang mit Tieren als Touristenmagnet\n"
        "Gib mir nur die richtige Antwort."
    )
    answer = agent.ask(prompt)
    print("Réponse Ollama :", answer)

