"""LangChain-based orchestration pipeline for Microsoft Forms AI project.

Flow:
  1. Read Excel -> extract form links
  2. For each link: scrape form (text+images) -> save raw JSON
  3. Validate JSON & classify (contains images?)
  4. If images: run OCR enrichment
  5. For every question produce (question_text, type, answer_values)
  6. Use LLM (Ollama) to generate an answer suggestion per question
  7. Persist augmented JSON with answers appended under question['llm_answer']

Logging & error handling included; modular for future extension.
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import List, Dict, Any

from langchain_core.runnables import RunnableLambda, RunnableSequence

from ExcelLinksExtractorAgent import get_links_list
from MicrosoftFormsCompleteAnalysisAgent import MicrosoftFormsCompleteScraper
from JsonImageDetectorAgent import JsonImageChecker
from FormsImageExtractionAgent import FormsImageExtractionAgent, OCR_AVAILABLE
from JsonQuestionExtractorAgent import JsonQuestionExtractor
from TextLanguageDetectionAgent import LanguageDetector
from LlamaLanguageModelAgent import OllamaAgent

INPUT_EXCEL_DIR = Path(r"C:\Users\abdel\OneDrive\Bureau\Microsoft-forms-AI\data\input")
OUTPUT_BASE_DIR = Path(r"C:\Users\abdel\OneDrive\Bureau\Microsoft-forms-AI\data\output")
JSON_DIR = OUTPUT_BASE_DIR / "jsons"
IMAGES_DIR = OUTPUT_BASE_DIR / "images"

JSON_DIR.mkdir(parents=True, exist_ok=True)
IMAGES_DIR.mkdir(parents=True, exist_ok=True)


def step_extract_links(_: Dict[str, Any]) -> Dict[str, Any]:
    links = get_links_list(str(INPUT_EXCEL_DIR))
    return {"links": links}


def step_scrape_forms(state: Dict[str, Any]) -> Dict[str, Any]:
    scraped_files: List[Path] = []
    for link in state.get("links", []):
        try:
            scraper = MicrosoftFormsCompleteScraper(
                url=link,
                headless=True,
                images_folder=str(IMAGES_DIR),
                output_folder=str(JSON_DIR)
            )
            data = scraper.run()
            saved = scraper.save_to_json()
            if saved:
                scraped_files.append(Path(saved))
        except Exception as e:
            print(f"[SCRAPE][ERREUR] {link}: {e}")
    state["scraped_json_files"] = scraped_files
    return state


def step_validate_and_flag(state: Dict[str, Any]) -> Dict[str, Any]:
    validated: List[Dict[str, Any]] = []
    for json_path in state.get("scraped_json_files", []):
        try:
            checker = JsonImageChecker(str(json_path))
            has_images = checker.contains_images()
            validated.append({
                "path": json_path,
                "contains_images": has_images
            })
        except Exception as e:
            print(f"[VALIDATE][ERREUR] {json_path.name}: {e}")
    state["validated_jsons"] = validated
    return state


def step_ocr_if_needed(state: Dict[str, Any]) -> Dict[str, Any]:
    enriched_paths: List[Path] = []
    if not OCR_AVAILABLE:
        print("[OCR] EasyOCR indisponible - étape ignorée")
        state["enriched_json_files"] = [v["path"] for v in state.get("validated_jsons", [])]
        return state
    agent = FormsImageExtractionAgent(str(JSON_DIR))
    for meta in state.get("validated_jsons", []):
        if meta["contains_images"]:
            try:
                processed = agent.process_json_file(meta["path"])
                if processed:
                    new_path = agent.save_processed_json(processed, meta["path"])
                    if new_path:
                        enriched_paths.append(new_path)
                        continue
            except Exception as e:
                print(f"[OCR][ERREUR] {meta['path'].name}: {e}")
        # If no OCR or failed, keep original
        enriched_paths.append(meta["path"])
    state["enriched_json_files"] = enriched_paths
    return state


def build_prompt(language: str, qtype: str, text: str, values: Any) -> str:
    if isinstance(values, list):
        opts = " | ".join(values)
    else:
        opts = str(values)
    return f"""You are an expert assistant for Microsoft Forms.
Question language: {language}
Question type: {qtype}
Question: {text}
Options: {opts}

Rules:
- If type is choiceItem or npsContainer: reply with EXACT option text only.
- If type is textInput: reply with a concise, relevant answer in {language}.
- Never translate question or options.
- No explanations.

Answer:"""


def step_generate_answers(state: Dict[str, Any]) -> Dict[str, Any]:
    llm = OllamaAgent()
    lang_detector = LanguageDetector()
    augmented: List[Path] = []
    for path in state.get("enriched_json_files", []):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            modified = False
            questions = data.get("questions", [])
            print(f"[LLM] Traitement fichier {path.name} - {len(questions)} question(s)")
            for idx, q in enumerate(questions, 1):
                if "llm_answer" in q:
                    continue  # already answered
                q_text = q.get("question_text", "")
                # If OCR text embedded in images, optionally concatenate
                if q.get("has_images") and q.get("images"):
                    for img in q.get("images", []):
                        if isinstance(img, dict) and img.get("question_text"):
                            q_text += f" | OCR: {img.get('question_text')}"
                qtype = q.get("answer_type", "unknown")
                answer_values = q.get("answer_values", [])
                try:
                    language = lang_detector.detect_language(q_text[:400]) if q_text else "Unknown"
                except Exception:
                    language = "Unknown"
                prompt = build_prompt(language, qtype, q_text, answer_values)
                try:
                    print(f"  [LLM][Q{idx}] Type={qtype} Lang={language} ... en cours")
                    answer = llm.ask(prompt, timeout=35)
                    print(f"  [LLM][Q{idx}] Réponse reçue: {answer[:60]}...")
                except Exception as e:
                    answer = f"LLM_ERROR: {e}"
                    print(f"  [LLM][Q{idx}] Erreur: {e}")
                q["llm_answer"] = answer
                q["llm_language_detected"] = language
                modified = True
            if modified:
                out_path = path.parent / f"{path.stem}_with_answers.json"
                with open(out_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                print(f"[LLM] Fichier enrichi sauvegardé: {out_path.name}")
                augmented.append(out_path)
            else:
                augmented.append(path)
        except Exception as e:
            print(f"[LLM][ERREUR] {path.name}: {e}")
    state["final_json_files"] = augmented
    return state


def run_pipeline() -> Dict[str, Any]:
    pipeline = RunnableSequence(
        RunnableLambda(step_extract_links)
        | RunnableLambda(step_scrape_forms)
        | RunnableLambda(step_validate_and_flag)
        | RunnableLambda(step_ocr_if_needed)
        | RunnableLambda(step_generate_answers)
    )
    result = pipeline.invoke({})
    print("\nPIPELINE TERMINÉ")
    print("Liens traités:", result.get("links"))
    print("JSON finaux:")
    for p in result.get("final_json_files", []):
        print("  -", p)
    return result


if __name__ == "__main__":
    run_pipeline()
