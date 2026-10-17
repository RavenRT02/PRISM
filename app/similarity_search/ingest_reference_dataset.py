from app.similarity_search.reference_store import ingest_reference_dataset

if __name__ == '__main__':
    count = ingest_reference_dataset()
    print(f"Successfully ingested {count} reference records.")