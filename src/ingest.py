"""
ingest.py — Chunks + embeds + stores in Pinecone (cloud vector DB)

CHANGE FROM CHROMADB VERSION:
ChromaDB stored vectors locally on your laptop — not accessible from the cloud.
Pinecone stores vectors in the cloud — accessible from anywhere, including
Streamlit Cloud. This is the production-ready version.

HOW PINECONE STORES DATA DIFFERENTLY FROM CHROMADB:
ChromaDB: stores (id, text, embedding, metadata) together
Pinecone: stores (id, embedding, metadata) — text goes in metadata
          because Pinecone is a pure vector store, not a document store
"""

import json
import os
from pathlib import Path
from collections import Counter
from dotenv import load_dotenv
from openai import OpenAI
from pinecone import Pinecone

load_dotenv()

DATA_PATH = Path(__file__).parent.parent / "data" / "sangam_chettinad_data.json"
INDEX_NAME = "whatdoieat"

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))


def embed(text: str) -> list:
    response = openai_client.embeddings.create(
        input=text,
        model="text-embedding-3-small"
    )
    return response.data[0].embedding


def load_data() -> dict:
    with open(DATA_PATH, "r") as f:
        return json.load(f)


def build_chunks(data: dict) -> list:
    chunks = []
    restaurant_name = data["restaurant_name"]

    # Restaurant info chunk
    hours_str = " | ".join([f"{k}: {v}" for k, v in data["hours"].items()])
    dietary_str = ", ".join(data["dietary_tags"])
    info_text = (
        f"{restaurant_name} is a {data['cuisine_type']} restaurant "
        f"located at {data['location']}. Phone: {data['phone']}. "
        f"Hours: {hours_str}. "
        f"Dietary options available: {dietary_str}. "
        f"Last updated: {data.get('last_updated', 'unknown')}."
    )
    chunks.append({
        "id": "restaurant_info",
        "text": info_text,
        "metadata": {
            "type": "restaurant_info",
            "name": restaurant_name,
            "location": data["location"],
            "phone": data["phone"],
            "text": info_text,
        }
    })

    # Menu item chunks
    for category_group in data["menu"]:
        category = category_group["category"]
        for item in category_group["items"]:
            tags_str = ", ".join(item.get("tags", []))
            popular_str = "This is a popular dish." if item.get("popular") else ""
            sig_str = "This is a signature dish." if item.get("is_signature") else ""

            text = (
                f"{item['name']} is a {category} dish at {restaurant_name}. "
                f"{item['description']} "
                f"It costs ${item['price']:.2f}. "
                f"Spice level: {item.get('spice_level', 'unknown')}. "
                f"Dietary tags: {tags_str}. "
                f"{popular_str} {sig_str}"
            ).strip()

            chunk_id = f"menu_{item['name'].lower().replace(' ', '_').replace('(', '').replace(')', '').replace('/', '_')}"

            chunks.append({
                "id": chunk_id,
                "text": text,
                "metadata": {
                    "type": "menu_item",
                    "name": item["name"],
                    "category": category,
                    "price": float(item["price"]),
                    "spice_level": item.get("spice_level", "unknown"),
                    "is_signature": item.get("is_signature", False),
                    "popular": item.get("popular", False),
                    "is_vegetarian": "Vegetarian" in item.get("tags", []),
                    "is_vegan": "Vegan" in item.get("tags", []),
                    "is_gluten_free": "Gluten-Free" in item.get("tags", []),
                    "tags": tags_str,
                    "text": text,
                }
            })

    # Review chunks
    for review in data["google_reviews"]:
        text = (
            f"Customer review of {restaurant_name} by {review['author']} "
            f"(rated {review['rating']}/5 on {review['timestamp']}): "
            f"{review['text']}"
        )
        chunks.append({
            "id": review["review_id"],
            "text": text,
            "metadata": {
                "type": "review",
                "review_id": review["review_id"],
                "author": review["author"],
                "rating": int(review["rating"]),
                "timestamp": review["timestamp"],
                "text": text,
            }
        })

    # Unlisted items chunk
    items = data.get("known_unlisted_items", [])
    if items:
        items_text = " ".join([f"{i['name']}: {i['note']}" for i in items])
        text = (
            f"The following items have been mentioned by customers at "
            f"{restaurant_name} but are not on the standard menu: {items_text}"
        )
        chunks.append({
            "id": "unlisted_items",
            "text": text,
            "metadata": {"type": "unlisted_items", "text": text}
        })

    return chunks


def ingest():
    print("Loading data...")
    data = load_data()

    print("Building chunks...")
    chunks = build_chunks(data)
    print(f"  {len(chunks)} chunks ready")

    print(f"\nConnecting to Pinecone index '{INDEX_NAME}'...")
    index = pc.Index(INDEX_NAME)

    print("Embedding and uploading chunks...")
    vectors = []
    for i, chunk in enumerate(chunks):
        print(f"  [{i+1}/{len(chunks)}] {chunk['id']}")
        embedding = embed(chunk["text"])
        vectors.append({
            "id": chunk["id"],
            "values": embedding,
            "metadata": chunk["metadata"],
        })

    print(f"\nUploading {len(vectors)} vectors to Pinecone...")
    index.upsert(vectors=vectors)

    print(f"\nDone! {len(vectors)} vectors stored in Pinecone.")
    type_counts = Counter(c["metadata"]["type"] for c in chunks)
    for t, count in type_counts.items():
        print(f"  {t}: {count}")

    stats = index.describe_index_stats()
    print(f"\nPinecone index stats: {stats.total_vector_count} vectors total")


if __name__ == "__main__":
    ingest()