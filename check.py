try:
    import streamlit as st
except Exception:
    print("Streamlit n'est pas installé. Installez-le avec: pip install streamlit")
    raise

from typing import List, Dict, Any, Optional
import os
from pathlib import Path

try:
    from elasticsearch import Elasticsearch, exceptions as es_exceptions
except Exception:
    Elasticsearch = None
    es_exceptions = None


@st.cache_resource
def get_es_client(host: str = "http://localhost:9200") -> Any:
    if Elasticsearch is None:
        return None
    try:
        client = Elasticsearch([host])
        if not client.ping():
            return None
        return client
    except Exception:
        return None


def search_forms(client: Any, form_name: Optional[str] = None, size: int = 50) -> List[Dict[str, Any]]:
    """Search forms in Elasticsearch. Not cached because client is unhashable."""
    if client is None:
        return []
    try:
        if form_name:
            query = {"match_phrase": {"form_name": {"query": form_name}}}
        else:
            query = {"match_all": {}}
        resp = client.search(index="forms_ai", query=query, size=size)
        hits = resp.get("hits", {}).get("hits", [])
        return [h.get("_source", {}) for h in hits]
    except Exception as e:
        # Re-raise so caller can show a useful message
        raise


def render_form(src: Dict[str, Any]):
    st.header(src.get("form_name", "(no form_name)"))
    meta_cols = [k for k in src.keys() if k not in ("questions",)]
    if meta_cols:
        with st.expander("Métadonnées", expanded=False):
            for k in meta_cols:
                st.write(f"**{k}**: {src.get(k)}")

    questions = src.get("questions", []) or []
    st.subheader(f"Questions ({len(questions)})")
    for i, q in enumerate(questions, 1):
        with st.expander(f"Q{i}: {q.get('question_text','(no text)')[:120]}"):
            st.write("**Question complète:**")
            st.write(q.get("question_text", ""))
            st.write("**Type:**", q.get("answer_type", ""))
            st.write("**Valeurs possibles:**", q.get("answer_values", ""))
            st.write("**LLM - Réponse:**", q.get("llm_answer", ""))
            st.write("**LLM - Justification:**", q.get("llm_justification", ""))
            st.write("**LLM - Langue détectée:**", q.get("llm_language_detected", ""))
            images = q.get("images", []) or []
            if images:
                st.write("**Images:**")
                # Resolve image sources (URLs or local files)
                img_srcs = []
                for img in images:
                    # Prefer an explicit URL field
                    url = None
                    if isinstance(img, dict):
                        url = img.get("original_src") or img.get("url")
                        fp = img.get("filepath") or img.get("filename")
                    else:
                        fp = str(img)
                        url = None

                    # If we have an http(s) URL, use it
                    if url and isinstance(url, str) and url.startswith("http"):
                        img_srcs.append(url)
                        continue

                    # Try to resolve local file path
                    if fp:
                        p = Path(fp)
                        if not p.is_absolute():
                            # common locations to try
                            candidates = [Path.cwd() / fp,
                                          Path.cwd() / 'data' / 'output' / 'images' / fp,
                                          Path.cwd() / 'data' / 'output' / 'jsons' / fp]
                        else:
                            candidates = [p]

                        found = None
                        for c in candidates:
                            if c.exists():
                                found = c
                                break
                        if found:
                            img_srcs.append(str(found))
                        else:
                            # fallback: display the raw value
                            img_srcs.append(str(fp))
                # Display images in a responsive way
                if img_srcs:
                    cols = st.columns(min(3, len(img_srcs)))
                    for idx, src_img in enumerate(img_srcs):
                        try:
                            with cols[idx % len(cols)]:
                                st.image(src_img, use_column_width=True)
                        except Exception:
                            with cols[idx % len(cols)]:
                                st.write(src_img)


def main():
    st.set_page_config(page_title="Forms AI — Elasticsearch Viewer", layout="wide")
    st.title("Forms AI — Visualiseur Elasticsearch")

    st.markdown("Recherche et affichage des formulaires indexés dans Elasticsearch (index: `forms_ai`).")

    es_host = st.text_input("Elasticsearch URL", value="http://localhost:9200")
    client = get_es_client(es_host)
    if client is None:
        st.error("Impossible de se connecter à Elasticsearch. Vérifiez l'URL et que le service est en cours.")
        return

    col1, col2 = st.columns([3, 1])
    with col2:
        form_name = st.text_input("Nom du formulaire (recherche)")
        size = st.number_input("Max résultats", min_value=1, max_value=200, value=50)
        if st.button("Rechercher"):
            pass

    results = search_forms(client, form_name=form_name.strip() if form_name else None, size=int(size))

    st.sidebar.header("Résultats")
    if not results:
        st.sidebar.write("Aucun document trouvé.")
    else:
        options = [f"{r.get('form_name','(no name)')} — {idx+1}" for idx, r in enumerate(results)]
        sel = st.sidebar.selectbox("Sélectionner un formulaire", options)
        sel_idx = options.index(sel) if sel in options else 0
        render_form(results[sel_idx])


if __name__ == "__main__":
    main()