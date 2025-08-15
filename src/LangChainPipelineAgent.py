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
from .logging_utils import log, log_section

from .ExcelLinksExtractorAgent import get_links_list
from .MicrosoftFormsCompleteAnalysisAgent import MicrosoftFormsCompleteScraper
from .JsonImageDetectorAgent import JsonImageChecker
from .FormsImageExtractionAgent import FormsImageExtractionAgent, OCR_AVAILABLE
from .JsonQuestionExtractorAgent import JsonQuestionExtractor
from .TextLanguageDetectionAgent import LanguageDetector
from .LlamaLanguageModelAgent import OllamaAgent

INPUT_EXCEL_DIR = Path(r"C:\Users\abdel\OneDrive\Bureau\Microsoft-forms-AI\data\input")
OUTPUT_BASE_DIR = Path(r"C:\Users\abdel\OneDrive\Bureau\Microsoft-forms-AI\data\output")
JSON_DIR = OUTPUT_BASE_DIR / "jsons"
IMAGES_DIR = OUTPUT_BASE_DIR / "images"

JSON_DIR.mkdir(parents=True, exist_ok=True)
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

# Cleanup configuration: keep only the raw scraped JSON + final JSON with answers
# Set to False if you want to keep intermediates for debugging
CLEANUP_OCR_JSON = True
CLEANUP_IMAGES = True
MAX_LLM_TIMEOUT_RETRIES = 4  # nombre max de réessais si TIMEOUT


def step_extract_links(_: Dict[str, Any]) -> Dict[str, Any]:
    links = get_links_list(str(INPUT_EXCEL_DIR))
    log('PIPELINE', f"Liens trouvés: {len(links)}")
    return {"links": links}


def step_scrape_forms(state: Dict[str, Any]) -> Dict[str, Any]:
    scraped_files: List[Path] = []
    for link in state.get("links", []):
        try:
            log('SCRAPE', f"Scraping: {link}")
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
                log('SCRAPE', f"JSON sauvegardé: {saved}")
        except Exception as e:
            log('SCRAPE', f"Erreur: {e}", level='ERROR')
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
            log('VALIDATE', f"{json_path.name} images={has_images}")
        except Exception as e:
            log('VALIDATE', f"Erreur {json_path.name}: {e}", level='ERROR')
    state["validated_jsons"] = validated
    return state


def step_ocr_if_needed(state: Dict[str, Any]) -> Dict[str, Any]:
    enriched_paths: List[Path] = []
    ocr_intermediate: List[Path] = []
    if not OCR_AVAILABLE:
        log('OCR', "EasyOCR indisponible - étape ignorée", level='WARN')
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
                        ocr_intermediate.append(new_path)
                        log('OCR', f"OCR OK: {new_path.name}")
                        continue
            except Exception as e:
                log('OCR', f"Erreur {meta['path'].name}: {e}", level='ERROR')
        # If no OCR or failed, keep original
        enriched_paths.append(meta["path"])
    state["enriched_json_files"] = enriched_paths
    state["ocr_intermediate_files"] = ocr_intermediate
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

TASK:
Provide the best possible answer AND a concise justification.

OUTPUT FORMAT (MANDATORY JSON):
{{"answer":"<ANSWER_ONLY>","justification":"<SHORT_REASONING>"}}

RULES:
- If type is choiceItem or npsContainer: answer MUST be EXACT option text ONLY (no extra chars).
- If type is textInput: answer is a concise relevant response in {language}.
- justification: max 30 words, refer only to information present in question/OCR/context; no hallucination; same language as question.
- Never translate options or fabricate data.
- Do NOT wrap JSON in markdown fences.
- Do NOT add extra keys.

Return ONLY the JSON object.
"""


def parse_answer_and_justification(raw: str) -> Dict[str, str]:
    """Parse model output expecting a JSON with 'answer' and 'justification'.
    Fallback: if parsing fails, treat whole text as answer and set generic justification.
    """
    result = {"answer": raw.strip(), "justification": ""}
    if not raw:
        return result
    # Try direct JSON
    try:
        data = json.loads(raw)
        if isinstance(data, dict) and 'answer' in data and 'justification' in data:
            return {"answer": str(data['answer']).strip(), "justification": str(data['justification']).strip()}
    except Exception:
        pass
    # Try to extract JSON substring
    try:
        start = raw.find('{')
        end = raw.rfind('}')
        if 0 <= start < end:
            snippet = raw[start:end+1]
            data = json.loads(snippet)
            if isinstance(data, dict) and 'answer' in data:
                result['answer'] = str(data['answer']).strip()
                result['justification'] = str(data.get('justification', '')).strip()
                return result
    except Exception:
        pass
    # Fallback heuristic: split first sentence
    if '.' in raw:
        first, *rest = raw.split('.')
        result['answer'] = first.strip()
        result['justification'] = '.'.join(rest).strip()[:160]
    else:
        result['justification'] = 'No structured justification returned.'
    return result


def step_generate_answers(state: Dict[str, Any]) -> Dict[str, Any]:
    llm = OllamaAgent()
    lang_detector = LanguageDetector()
    augmented: List[Path] = []
    removed_images_total = 0
    for path in state.get("enriched_json_files", []):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            modified = False
            questions = data.get("questions", [])
            log('LLM', f"Fichier {path.name} - {len(questions)} question(s)")
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
                    log('LLM', f"Q{idx} type={qtype} lang={language} - génération", indent=1)
                    attempt = 0
                    raw_answer = ""
                    while True:
                        attempt += 1
                        raw_answer = llm.ask(prompt, timeout=35)
                        if raw_answer == "FALLBACK_TIMEOUT_AUTO_ANSWER" and attempt <= MAX_LLM_TIMEOUT_RETRIES:
                            log('LLM', f"Q{idx} timeout fallback -> retry {attempt}/{MAX_LLM_TIMEOUT_RETRIES}", level='WARN', indent=2)
                            continue
                        break
                    if raw_answer == "FALLBACK_TIMEOUT_AUTO_ANSWER" and attempt > MAX_LLM_TIMEOUT_RETRIES:
                        log('LLM', f"Q{idx} abandon après {MAX_LLM_TIMEOUT_RETRIES} timeouts", level='ERROR', indent=2)
                    parsed = parse_answer_and_justification(raw_answer)
                    log('LLM', f"Q{idx} answer: {parsed['answer'][:40]} | justif: {parsed['justification'][:40]}", indent=2)
                except Exception as e:
                    raw_answer = f"LLM_ERROR: {e}"
                    parsed = {"answer": raw_answer, "justification": "Generation failed."}
                    log('LLM', f"Q{idx} exception: {e}", level='ERROR', indent=2)
                q["llm_answer"] = parsed["answer"]
                q["llm_justification"] = parsed.get("justification", "")
                q["llm_language_detected"] = language
                modified = True
            if modified:
                out_path = path.parent / f"{path.stem}_with_answers.json"
                with open(out_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                log('LLM', f"Sauvegardé: {out_path.name}")
                augmented.append(out_path)
                # Optional cleanup of images referenced in this JSON
                if CLEANUP_IMAGES:
                    imgs_deleted = 0
                    for q in data.get("questions", []):
                        for img in q.get("images", []) or []:
                            fp = img.get("filepath") if isinstance(img, dict) else None
                            if not fp:
                                continue
                            try:
                                img_path = Path(fp)
                                if not img_path.is_absolute():
                                    # Try relative to project root
                                    candidate = Path.cwd() / fp
                                    if candidate.exists():
                                        img_path = candidate
                                if img_path.exists() and img_path.is_file():
                                    img_path.unlink()
                                    imgs_deleted += 1
                            except Exception:
                                pass
                    removed_images_total += imgs_deleted
                    if imgs_deleted:
                        log('CLEANUP', f"{imgs_deleted} image(s) supprimée(s) pour {out_path.name}")
            else:
                augmented.append(path)
        except Exception as e:
            log('LLM', f"Erreur fichier {path.name}: {e}", level='ERROR')
    state["final_json_files"] = augmented

    # Cleanup OCR intermediate JSON files (keep only original + final answers)
    if CLEANUP_OCR_JSON:
        for ocr_path in state.get("ocr_intermediate_files", []):
            # Don't remove if it's also a final JSON (unlikely naming overlap, but safety)
            if any(str(ocr_path) == str(final_p) for final_p in augmented):
                continue
            try:
                if ocr_path.exists():
                    ocr_path.unlink()
                    log('CLEANUP', f"OCR intermédiaire supprimé: {ocr_path.name}")
            except Exception as e:
                log('CLEANUP', f"Erreur suppression {ocr_path.name}: {e}", level='ERROR')

    if CLEANUP_IMAGES and removed_images_total:
        log('CLEANUP', f"Total images supprimées: {removed_images_total}")
    return state


def run_pipeline() -> Dict[str, Any]:
    pipeline = RunnableSequence(
        RunnableLambda(step_extract_links)
        | RunnableLambda(step_scrape_forms)
        | RunnableLambda(step_validate_and_flag)
        | RunnableLambda(step_ocr_if_needed)
        | RunnableLambda(step_generate_answers)
    )
    log_section('PIPELINE TERMINÉ')
    result = pipeline.invoke({})
    log('PIPELINE', f"Liens: {len(result.get('links', []))}")
    for p in result.get("final_json_files", []):
        log('PIPELINE', f"Final: {p}")
    return result


if __name__ == "__main__":
    run_pipeline()
