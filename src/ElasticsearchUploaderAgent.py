import json
from typing import List, Dict, Any, Optional

try:
    from elasticsearch import Elasticsearch, exceptions as es_exceptions
    ELASTICSEARCH_AVAILABLE = True
except ImportError:
    ELASTICSEARCH_AVAILABLE = False

class ElasticsearchUploaderAgent:
    """
    Agent pour uploader les réponses, justifications et questions dans Elasticsearch.
    Chaque document contient : nom_formulaire, questions, réponses, justifications.
    """
    def __init__(self, es_host: str = 'http://localhost:9200', index_name: str = 'forms_ai'):
        self.es_host = es_host
        self.index_name = index_name
        self.client: Optional[Elasticsearch] = None
        self.available = ELASTICSEARCH_AVAILABLE
        if self.available:
            try:
                self.client = Elasticsearch([self.es_host])
                # Test connexion
                if not self.client.ping():
                    self.available = False
            except Exception:
                self.available = False

    def upload_form(self, form_name: str, questions: List[Dict[str, Any]], meta: Dict[str, Any] = None) -> bool:
        """
        form_name: nom du formulaire (depuis Excel)
        questions: liste de dicts (question_text, llm_answer, llm_justification, ...)
        meta: autres infos (url, date, etc.)
        """
        if not self.available or not self.client:
            print("[ELASTIC] Elasticsearch non disponible, upload ignoré.")
            return False
        doc = {
            "form_name": form_name,
            "questions": questions,
        }
        if meta:
            doc.update(meta)
        try:
            res = self.client.index(index=self.index_name, document=doc)
            print(f"[ELASTIC] Document indexé: {res.get('result','?')}")
            return True
        except es_exceptions.ConnectionError:
            print("[ELASTIC] Connexion impossible à Elasticsearch.")
            return False
        except Exception as e:
            print(f"[ELASTIC] Erreur upload: {e}")
            return False
