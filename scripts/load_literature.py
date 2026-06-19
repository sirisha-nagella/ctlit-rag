
"""
Fetch PubMed papers on a topic, chunk them, embed, and add to the SAME
vector store as the trials.
Run from project root: python -m scripts.load_literature
"""

from data_sources.pubmed import search_papers
from chunking import paper_to_chunks
from rag.embedding_model import embed
from rag.vector_store import get_collection

QUERY = "sofosbuvir velpatasvir hepatitis C"


def main():
    papers = search_papers(QUERY, max_results=20)
    print(f"Fetched {len(papers)} papers.")

    chunks = []
    for paper in papers:
        chunks.extend(paper_to_chunks(paper))
    print(f"Built {len(chunks)} literature chunks.")

    ids = [c["id"] for c in chunks]
    texts = [c["text"] for c in chunks]
    metadatas = [c["metadata"] for c in chunks]
    embeddings = embed(texts)

    collection = get_collection()
    collection.upsert(
        ids=ids, documents=texts,
        embeddings=embeddings.tolist(), metadatas=metadatas,
    )
    print(f"Store now holds {collection.count()} chunks total (trials + literature).")

if __name__ == "__main__":
    main()
  