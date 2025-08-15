import subprocess
import shutil
from typing import Optional
import locale

PREFERRED_ENCODING = 'utf-8'

class OllamaAgent:
    """Wrapper around local Ollama CLI with robustness (timeout, availability check)."""
    def __init__(self, model: str = 'deepseek-r1:8b', offline_fallback: bool = True):
        self.model = model
        self.offline_fallback = offline_fallback
        self.available = shutil.which('ollama') is not None
        if not self.available:
            print("[LLM] Commande 'ollama' introuvable. Mode fallback activé.")

    def extract_final_answer(self, text: str) -> str:
        marker = "...done thinking."
        if marker in text:
            parts = text.split(marker)
            final_part = parts[-1].strip()
            return final_part
        return text.strip()

    def ask(self, prompt: str, timeout: int = 30) -> str:
        """Query the model; returns answer or fallback token on failure.
        Uses enforced UTF-8 decoding with replacement to avoid cp1252 decode errors on Windows.
        """
        if not self.available:
            return self._fallback_answer(prompt, reason="NO_OLLAMA")
        try:
            # Force UTF-8 decoding; errors='replace' to avoid UnicodeDecodeError in _readerthread
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
                # Still log truncated stderr for diagnostics
                print(f"[LLM][STDERR] {stderr.strip()[:200]}")
            answer = self.extract_final_answer(stdout)
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
        # Simple heuristic fallback
        return f"FALLBACK_{reason}" \
               f"_AUTO_ANSWER"



if __name__ == "__main__":
    agent = OllamaAgent()
    demo_prompt = "Test prompt for Ollama availability check."
    print(agent.ask(demo_prompt))
