"""
retriever.py — Queries Pinecone instead of ChromaDB

KEY DIFFERENCE FROM CHROMADB VERSION:
ChromaDB query returns documents (text) automatically.
Pinecone only returns vectors + metadata — text is retrieved from metadata["text"]
which we stored during ingestion. Everything else (routing logic) stays the same.
"""

import os
import re
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from pinecone import Pinecone

load_dotenv()

INDEX_NAME = "whatdoieat"

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))


def get_index():
    return pc.Index(INDEX_NAME)


def embed(text: str) -> list:
    response = openai_client.embeddings.create(
        input=text,
        model="text-embedding-3-small"
    )
    return response.data[0].embedding


def semantic_search(question: str, n_results: int = 5, chunk_types: list = None) -> list:
    """Pure semantic search with optional chunk type filter."""
    index = get_index()
    query_vector = embed(question)

    filter_dict = None
    if chunk_types:
        filter_dict = {"type": {"$in": chunk_types}}

    results = index.query(
        vector=query_vector,
        top_k=n_results,
        filter=filter_dict,
        include_metadata=True,
    )

    return _unpack(results)


def hybrid_search(
    question: str,
    n_results: int = 5,
    max_price: float = None,
    spice_levels: list = None,
    vegetarian_only: bool = False,
    vegan_only: bool = False,
    gluten_free_only: bool = False,
    chunk_types: list = None,
) -> list:
    """Metadata filter + semantic search."""
    index = get_index()
    query_vector = embed(question)

    # Build Pinecone filter
    # Pinecone uses same MongoDB-style syntax as ChromaDB: $eq, $in, $lte, $and
    conditions = []

    if chunk_types:
        conditions.append({"type": {"$in": chunk_types}})
    if max_price is not None:
        conditions.append({"price": {"$lte": max_price}})
    if spice_levels:
        conditions.append({"spice_level": {"$in": spice_levels}})
    if vegetarian_only:
        conditions.append({"is_vegetarian": {"$eq": True}})
    if vegan_only:
        conditions.append({"is_vegan": {"$eq": True}})
    if gluten_free_only:
        conditions.append({"is_gluten_free": {"$eq": True}})

    filter_dict = None
    if len(conditions) == 1:
        filter_dict = conditions[0]
    elif len(conditions) > 1:
        filter_dict = {"$and": conditions}

    results = index.query(
        vector=query_vector,
        top_k=n_results,
        filter=filter_dict,
        include_metadata=True,
    )

    return _unpack(results)


def route_query(question: str, n_results: int = 5) -> tuple:
    """
    Detects question intent and picks the right retrieval strategy.
    Same routing logic as before — only the DB calls changed.
    """
    q = question.lower()

    avoid_spice = bool(re.search(
        r"(don.t|not|avoid|hate|no).{0,10}(spic|hot|heat)|mild|not spicy|less spic", q
    ))

    max_price = None
    price_match = re.search(r"under\s*\$?(\d+)|below\s*\$?(\d+)|\$?(\d+)\s*or less", q)
    if price_match:
        val = next(v for v in price_match.groups() if v is not None)
        max_price = float(val)
    if re.search(r"\bcheap\b|\bbudget\b|\baffordable\b|\binexpensive\b", q):
        max_price = max_price or 12.0

    vegetarian = bool(re.search(r"\bvegetarian\b|\bveg\b|\bno meat\b", q))
    vegan      = bool(re.search(r"\bvegan\b|\bplant.based\b|\bdairy.free\b", q))
    gf         = bool(re.search(r"\bgluten.free\b|\bno gluten\b|\bceliac\b", q))

    is_review_q    = bool(re.search(r"\b(review|customer|people|say|think|opinion|worth|recommend|crowd|packed)\b", q))
    is_hours_q     = bool(re.search(r"\b(hour|open|close|time|when|weekend|weekday|lunch|dinner|breakfast)\b", q))
    is_location_q  = bool(re.search(r"\b(where|address|location|phone|contact|find)\b", q))
    is_signature_q = bool(re.search(r"\b(signature|special|best|must.try|famous|popular dish|most popular|popular)\b", q))

    if is_hours_q or is_location_q:
        chunks = semantic_search(question, n_results=2, chunk_types=["restaurant_info"])
        return chunks, "semantic → restaurant_info only"

    if is_review_q and not avoid_spice and not vegetarian and not vegan:
        chunks = semantic_search(question, n_results=4, chunk_types=["review"])
        return chunks, "semantic → reviews only"

    if is_signature_q and not avoid_spice and not vegetarian:
        chunks = hybrid_search(question, n_results=5, chunk_types=["menu_item"])
        chunks.sort(key=lambda c: (
            -int(c["metadata"].get("is_signature", False)),
            -int(c["metadata"].get("popular", False)),
            c["similarity"] * -1
        ))
        return chunks, "hybrid → menu_item, re-ranked by signature+popular"

    if avoid_spice or max_price or vegetarian or vegan or gf:
        spice_filter = ["none", "mild"] if avoid_spice else None
        chunks = hybrid_search(
            question,
            n_results=5,
            max_price=max_price,
            spice_levels=spice_filter,
            vegetarian_only=vegetarian,
            vegan_only=vegan,
            gluten_free_only=gf,
            chunk_types=["menu_item"],
        )
        strategy = f"hybrid → spice={spice_filter}, price≤{max_price}, veg={vegetarian}, vegan={vegan}, gf={gf}"
        return chunks, strategy

    chunks = semantic_search(question, n_results=5)
    return chunks, "semantic → all chunk types"


def format_chunks_for_llm(chunks: list) -> str:
    if not chunks:
        return "No relevant information found."
    formatted = []
    for i, chunk in enumerate(chunks, 1):
        chunk_type = chunk["metadata"].get("type", "unknown")
        formatted.append(
            f"[Source {i} | type: {chunk_type} | relevance: {chunk['similarity']}]\n"
            f"{chunk['text']}"
        )
    return "\n\n---\n\n".join(formatted)


def _unpack(results) -> list:
    """Converts Pinecone response into clean flat list."""
    chunks = []
    for match in results.matches:
        chunks.append({
            "id": match.id,
            "text": match.metadata.get("text", ""),
            "metadata": match.metadata,
            "similarity": round(match.score, 4),
        })
    return chunks


if __name__ == "__main__":
    print("=" * 60)
    print("Retriever Test — Pinecone")
    print("=" * 60)

    tests = [
        "What should I order if I don't like spicy food?",
        "What do customers say about the portions?",
        "Any vegetarian options under $12?",
        "What are the signature dishes?",
        "What time does the restaurant open on weekends?",
        "Something good for a vegan?",
        "What's the most popular dish here?",
    ]

    for question in tests:
        chunks, strategy = route_query(question)
        print(f"\nQ: {question}")
        print(f"Strategy: {strategy}")
        for c in chunks:
            t = c["metadata"].get("type")
            name = c["metadata"].get("name", c["id"])
            spice = c["metadata"].get("spice_level", "")
            price = c["metadata"].get("price", "")
            print(f"  [{t}] {name}{f' | ${price}' if price else ''}{f' | spice:{spice}' if spice else ''} — sim:{c['similarity']}")