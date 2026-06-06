"""
verify_db.py — Run this after ingest.py to confirm ChromaDB is healthy.

WHY THIS FILE EXISTS:
Ingestion can silently succeed but store garbage — wrong chunk count,
missing metadata fields, malformed text. Always verify before building
on top of a data layer. This is standard Data Engineering practice.

This script does NOT call OpenAI. It just reads what's already in ChromaDB.

Run with:
    python src/verify_db.py
"""

import chromadb
from pathlib import Path
from collections import defaultdict

CHROMA_PATH = Path(__file__).parent.parent / "chroma_db"
COLLECTION_NAME = "sangam_restaurant"


def verify():
    print("=" * 60)
    print("ChromaDB Verification Report")
    print("=" * 60)

    # Connect (read-only, no API key needed)
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))

    try:
        collection = client.get_collection(COLLECTION_NAME)
    except Exception:
        print("\nERROR: Collection not found.")
        print("Have you run `python src/ingest.py` yet?")
        return

    # ── 1. Total count ──────────────────────────────────────────
    total = collection.count()
    print(f"\nTotal chunks stored: {total}")
    if total != 24:
        print(f"  WARNING: Expected 24, got {total}. Re-run ingest.py.")
    else:
        print("  OK: Count matches expected (24)")

    # ── 2. Fetch everything and inspect ─────────────────────────
    # include=["metadatas", "documents"] skips embeddings (huge number arrays)
    results = collection.get(include=["metadatas", "documents"])
    ids = results["ids"]
    metadatas = results["metadatas"]
    documents = results["documents"]

    # ── 3. Breakdown by type ─────────────────────────────────────
    print("\nChunk breakdown by type:")
    type_counts = defaultdict(int)
    for m in metadatas:
        type_counts[m.get("type", "unknown")] += 1
    for chunk_type, count in sorted(type_counts.items()):
        print(f"  {chunk_type}: {count}")

    # ── 4. Check all required metadata fields exist ──────────────
    print("\nMetadata field check (menu items):")
    required_fields = ["type", "name", "category", "price", "spice_level",
                       "is_signature", "popular", "is_vegetarian", "is_vegan",
                       "is_gluten_free", "tags"]
    menu_items = [(doc, meta) for doc, meta in zip(documents, metadatas)
                  if meta.get("type") == "menu_item"]
    missing_fields = []
    for doc, meta in menu_items:
        for field in required_fields:
            if field not in meta:
                missing_fields.append(f"  {meta.get('name', '?')} is missing '{field}'")
    if missing_fields:
        for m in missing_fields:
            print(f"  WARNING: {m}")
    else:
        print(f"  OK: All {len(required_fields)} fields present on all {len(menu_items)} menu chunks")

    # ── 5. Spot check — print one chunk of each type ─────────────
    print("\nSpot check — one chunk per type:")
    seen_types = set()
    for doc, meta, chunk_id in zip(documents, metadatas, ids):
        t = meta.get("type")
        if t not in seen_types:
            seen_types.add(t)
            print(f"\n  [{t}] id={chunk_id}")
            print(f"  text preview: {doc[:120]}...")
            relevant_meta = {k: v for k, v in meta.items()
                             if k not in ["tags"]}  # tags is long, skip
            print(f"  metadata: {relevant_meta}")

    # ── 6. Filter test — simulates a real user query filter ───────
    print("\nFilter test — vegetarian items under $15:")
    filtered = collection.get(
        where={
            "$and": [
                {"is_vegetarian": {"$eq": True}},
                {"price": {"$lt": 15.0}},
                {"type": {"$eq": "menu_item"}},
            ]
        },
        include=["metadatas"]
    )
    for m in filtered["metadatas"]:
        print(f"  {m['name']} — ${m['price']} — spice: {m['spice_level']}")
    if not filtered["metadatas"]:
        print("  (none found — check metadata fields)")

    # ── 7. Filter test — popular signature dishes ─────────────────
    print("\nFilter test — signature + popular dishes:")
    sig = collection.get(
        where={
            "$and": [
                {"is_signature": {"$eq": True}},
                {"popular": {"$eq": True}},
                {"type": {"$eq": "menu_item"}},
            ]
        },
        include=["metadatas"]
    )
    for m in sig["metadatas"]:
        print(f"  {m['name']} — ${m['price']} — spice: {m['spice_level']}")

    print("\n" + "=" * 60)
    print("Verification complete. If all checks pass, proceed to retriever.py")
    print("=" * 60)


if __name__ == "__main__":
    verify()