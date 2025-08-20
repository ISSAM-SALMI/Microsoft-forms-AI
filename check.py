from elasticsearch import Elasticsearch

es = Elasticsearch(['http://localhost:9200'])
response = es.search(index="forms_ai", query={"match_all": {}}, size=10)

for doc in response["hits"]["hits"]:
    src = doc["_source"]
    print(f"Formulaire: {src.get('form_name', 'N/A')}")
    for q in src.get("questions", []):
        print(f"  Question: {q.get('question_text', 'N/A')}")
        print(f"  Réponse: {q.get('llm_answer', 'N/A')}")
        print(f"  Justification: {q.get('llm_justification', 'N/A')}")
        print("-" * 40)
    print("=" * 60)