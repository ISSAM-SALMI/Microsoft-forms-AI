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

    LANGUAGE = "German"
    QUESTION_TYPE = "choiceItem"
    QUESTION = (
    )
    OPTIONS = [
    ]

    prompt = f"""You are an expert assistant for Microsoft Forms.
    Question language: {LANGUAGE}
    Question type: {QUESTION_TYPE}
    Question: {QUESTION}
    Options: {" | ".join(OPTIONS)}

    Rules:
    - If type is "choiceItem" or "npsContainer": reply with EXACT option text only.
    - If type is "textInput": reply with a complete relevant answer in {LANGUAGE}.
    - Never translate question or options; keep original language.
    - Do not add explanations.

    Answer:"""

    answer = agent.ask(prompt)
    print("Réponse Ollama:", answer)
