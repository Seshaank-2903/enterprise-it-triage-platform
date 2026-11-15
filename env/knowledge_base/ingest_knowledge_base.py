"""
Enterprise IT Knowledge Base Ingestion Script.

Reads markdown documents from external/knowledge_base/ and loads them
into the ChromaDB vector database with proper metadata citations.
"""
import os
import re
import chromadb

KB_DIR = os.path.dirname(os.path.abspath(__file__))
CHROMA_PATH = os.getenv("CHROMA_PERSIST_DIR", os.path.join(KB_DIR, "../../backend/chroma_db"))


def parse_markdown_metadata(file_path: str):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Extract title from first H1
    title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else os.path.basename(file_path)

    # Extract Canonical URL
    url_match = re.search(r"Canonical URL:\s*`([^`]+)`", content)
    url = url_match.group(1).strip() if url_match else f"https://kb.enterprise.internal/docs/{os.path.basename(file_path)}"

    # Extract Doc ID
    id_match = re.search(r"Doc ID:\s*`([^`]+)`", content)
    doc_id = id_match.group(1).strip() if id_match else os.path.splitext(os.path.basename(file_path))[0]

    return doc_id, content, {"title": title, "url": url}


def ingest_all_docs():
    print(f"Connecting to ChromaDB at: {CHROMA_PATH}")
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_or_create_collection("enterprise_it_kb")

    ids = []
    documents = []
    metadatas = []

    for file_name in os.listdir(KB_DIR):
        if file_name.endswith(".md"):
            full_path = os.path.join(KB_DIR, file_name)
            doc_id, text, metadata = parse_markdown_metadata(full_path)
            ids.append(doc_id)
            documents.append(text)
            metadatas.append(metadata)
            print(f"Parsed: {doc_id} -> '{metadata['title']}' ({metadata['url']})")

    if ids:
        collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
        print(f"\nSuccessfully ingested {len(ids)} documentation articles into ChromaDB collection 'enterprise_it_kb'!")
    else:
        print("No markdown documents found to ingest.")


if __name__ == "__main__":
    ingest_all_docs()
