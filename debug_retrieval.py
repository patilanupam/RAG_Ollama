"""Debug script to check what's in the vector store"""
from backend.core.rag.vectorstore import _get_collection, get_all_sources
from backend.core.rag.embedder import embed_query

collection = _get_collection()

# Get all data
result = collection.get(include=['documents', 'metadatas'])
print(f'Total items in ChromaDB: {len(result["ids"])}')

# Show all sources
print('\n=== Documents in vector store ===')
sources = get_all_sources()
for source_info in sources:
    print(f'  {source_info["source"]}: {source_info["chunk_count"]} chunks')

# Get Counselling PDF chunks
counselling_chunks = []
for i, meta in enumerate(result['metadatas']):
    if 'Counselling_pdf_india_gpt.pdf' in meta.get('source', ''):
        counselling_chunks.append({
            'id': result['ids'][i],
            'text': result['documents'][i]
        })

print(f'\n=== Counselling PDF Analysis ===')
print(f'Total chunks: {len(counselling_chunks)}')

if counselling_chunks:
    print('\n--- First chunk preview ---')
    print(counselling_chunks[0]['text'][:400])
    print('\n...')
    
    print(f'\n--- Second chunk preview ---')
    if len(counselling_chunks) > 1:
        print(counselling_chunks[1]['text'][:400])
        print('\n...')

# Test retrieval
print('\n=== Testing Retrieval ===')
query = "What is in Counselling PDF India GPT?"
query_emb = embed_query(query)

results = collection.query(
    query_embeddings=[query_emb],
    n_results=10,
    include=['metadatas', 'distances']
)

print(f'Query: "{query}"')
print('\nTop 10 results:')
for i, meta in enumerate(results['metadatas'][0]):
    source = meta.get('source', 'unknown')
    distance = results['distances'][0][i]
    similarity = 1 - distance
    print(f'{i+1}. {source} (similarity: {similarity:.4f})')

# Count how many are from Counselling PDF
counselling_results = [m for m in results['metadatas'][0] if 'Counselling' in m.get('source', '')]
print(f'\nCounselling PDF in top 10: {len(counselling_results)} results')
