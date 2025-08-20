import subprocess
import shutil
import os

PREFERRED_ENCODING = 'utf-8'


class OllamaAgent:
    """Wrapper around local Ollama CLI with robustness (timeout, availability check).
    Ajouts: MODE_DEBUG + streaming.
    """
    def __init__(self, model: str = 'deepseek-r1:8b', offline_fallback: bool = True):
        self.model = os.getenv('FORMS_AI_LLM_MODEL', model)
        self.offline_fallback = offline_fallback
        self.available = shutil.which('ollama') is not None
        self.debug = os.getenv('FORMS_AI_DEBUG', '0') == '1'
        if not self.available:
            print("[LLM] Commande 'ollama' introuvable. Mode fallback activé.")

    def extract_final_answer(self, text: str) -> str:
        marker = "...done thinking."
        if marker in text:
            parts = text.split(marker)
            final_part = parts[-1].strip()
            return final_part
        return text.strip()

    def ask(self, prompt: str, timeout: int = 45) -> str:
        if not self.available:
            return self._fallback_answer(prompt, reason="NO_OLLAMA")
        try:
            proc = subprocess.Popen(
                ['ollama', 'run', self.model],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding=PREFERRED_ENCODING,
                errors='replace'
            )
            try:
                stdout, stderr = proc.communicate(input=prompt + '\n', timeout=timeout)
            except subprocess.TimeoutExpired:
                proc.kill()
                return self._fallback_answer(prompt, reason="TIMEOUT")
            if stderr:
                print(f"[LLM][STDERR] {stderr.strip()[:200]}")
            answer = self.extract_final_answer(stdout)
            if self.debug:
                print(f"[LLM][DEBUG] Raw length={len(stdout)} answer_length={len(answer)}")
            if not answer.strip():
                return self._fallback_answer(prompt, reason="EMPTY_OUTPUT")
            return answer
        except FileNotFoundError:
            self.available = False
            return self._fallback_answer(prompt, reason="FILE_NOT_FOUND")
        except Exception as e:
            return self._fallback_answer(prompt, reason=f"EXCEPTION:{e}")

    def _fallback_answer(self, prompt: str, reason: str) -> str:
        if not self.offline_fallback:
            return f"LLM_ERROR:{reason}"
        return f"FALLBACK_{reason}_AUTO_ANSWER"

    def ask_stream(self, prompt: str, timeout: int = 90) -> str:
        if not self.available:
            return self._fallback_answer(prompt, reason="NO_OLLAMA")
        try:
            proc = subprocess.Popen(
                ['ollama', 'run', self.model],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding=PREFERRED_ENCODING,
                errors='replace'
            )
            if proc.stdin:
                proc.stdin.write(prompt + '\n')
                proc.stdin.flush()
                proc.stdin.close()
            collected = []
            import time as _t
            start = _t.time()
            while True:
                if proc.stdout:
                    line = proc.stdout.readline()
                    if line:
                        collected.append(line)
                    elif proc.poll() is not None:
                        break
                if _t.time() - start > timeout:
                    proc.kill()
                    return self._fallback_answer(prompt, reason="TIMEOUT_STREAM")
            output = ''.join(collected)
            answer = self.extract_final_answer(output)
            if not answer.strip():
                return self._fallback_answer(prompt, reason="EMPTY_OUTPUT")
            return answer
        except Exception as e:
            return self._fallback_answer(prompt, reason=f"EXCEPTION_STREAM:{e}")


if __name__ == "__main__":
    agent = OllamaAgent()
    demo_prompt = "Hey"
    print(agent.ask(demo_prompt))
