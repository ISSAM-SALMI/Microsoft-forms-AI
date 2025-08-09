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
    prompt = "1 + x = 10, alors x = ?"
    answer = agent.ask(prompt)
    print("Réponse Ollama :", answer)
