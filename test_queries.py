"""Test content-specific retrieval"""
from backend.core.rag.vectorstore import _get_collection
from backend.core.rag.embedder import embed_query

collection = _get_collection()

# Test different queries
queries = [
    "What is the career counselling framework?",
    "How should counselling be done after 10th and 12th?",
    "What are cognitive patterns in students?",
]

for query in queries:
    print(f'\n=== Query: "{query}" ===')
    query_emb = embed_query(query)
    
    results = collection.query(
        query_embeddings=[query_emb],
        n_results=5,
        include=['metadatas', 'distances']
    )
    
    print('Top 5 results:')
    for i, meta in enumerate(results['metadatas'][0]):
        source = meta.get('source', 'unknown')
        distance = results['distances'][0][i]
        similarity = 1 - distance
        print(f'  {i+1}. {source} (similarity: {similarity:.4f})')
    
    # Count counselling results
    counselling_count = sum(1 for m in results['metadatas'][0] if 'Counselling' in m.get('source', ''))
    print(f'  → Counselling PDF: {counselling_count}/5 results')
