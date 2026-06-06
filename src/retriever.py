"""
retriever.py — Phase 2, Step 2: Query ChromaDB to find relevant chunks

WHY THIS FILE EXISTS:
The retriever bridges the user's question and the LLM.
Its only job: given a question, return the most relevant chunks from ChromaDB.

KEY LESSON FROM OUR FIRST TEST:
  - "What should I order if I don't like spicy food?" returned HOT dishes
  - Why? Semantic search matched the TOPIC (spicy food) not the INTENT (avoid spice)
  - Fix: detect question intent first, then choose the right retrieval strategy
  - This is called query routing — a critical real-world RAG pattern

TWO RETRIEVAL MODES:
  semantic_search()  → pure meaning-based search, no filters
  hybrid_search()    → metadata filter FIRST, then semantic search within results

ONE ROUTER:
  route_query()      → reads the question, picks the right mode + filters automatically
"""

import os
import re
from pathlib import Path
from dotenv import load_dotenv
import chromadb
from chromadb.utils import embedding_functions

load_dotenv()

CHROMA_PATH = Path(__file__).parent.parent / "chroma_db"
COLLECTION_NAME = "sangam_restaurant"


def get_collection():
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    openai_ef = embedding_functions.OpenAIEmbeddingFunction(
        api_key=os.getenv("OPENAI_API_KEY"),
        model_name="text-embedding-3-small",
    )
    return client.get_collection(
        name=COLLECTION_NAME,
        embedding_function=openai_ef,
    )


def semantic_search(question: str, n_results: int = 5, chunk_types: list = None) -> list[dict]:
    """
    Pure semantic search — finds chunks whose MEANING is closest to the question.

    chunk_types: optional filter e.g. ["menu_item"] or ["review"]
                 use this when you know what kind of chunk you need
    """
    collection = get_collection()

    where_filter = None
    if chunk_types:
        if len(chunk_types) == 1:
            where_filter = {"type": {"$eq": chunk_types[0]}}
        else:
            where_filter = {"type": {"$in": chunk_types}}

    results = collection.query(
        query_texts=[question],
        n_results=n_results,
        where=where_filter,
        include=["documents", "metadatas", "distances"],
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
) -> list[dict]:
    """
    Metadata filter FIRST, then semantic search within the filtered results.

    WHY: Hard constraints (price, diet, spice) should never be overridden by
    semantic similarity. Filter first guarantees the constraints are respected.
    """
    collection = get_collection()

    conditions = []

    if chunk_types:
        if len(chunk_types) == 1:
            conditions.append({"type": {"$eq": chunk_types[0]}})
        else:
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

    where_filter = None
    if len(conditions) == 1:
        where_filter = conditions[0]
    elif len(conditions) > 1:
        where_filter = {"$and": conditions}

    results = collection.query(
        query_texts=[question],
        n_results=n_results,
        where=where_filter,
        include=["documents", "metadatas", "distances"],
    )

    return _unpack(results)


def route_query(question: str, n_results: int = 5) -> tuple[list[dict], str]:
    """
    WHY THIS FUNCTION EXISTS — THE KEY LESSON:
    Our first retriever test showed that "don't like spicy food" returned HOT dishes.
    Semantic search matched the topic, not the intent. We need to detect intent first.

    This function reads the question and decides:
      - Which retrieval mode to use (semantic vs hybrid)
      - Which filters to apply (spice, price, diet, chunk type)

    This is called QUERY ROUTING — a standard pattern in production RAG systems.
    Instead of one-size-fits-all retrieval, we adapt the strategy to the question.

    Returns:
        (chunks, strategy_description) — chunks for the LLM, description for debugging
    """
    q = question.lower()

    # ── Detect spice preference ──────────────────────────────────────────────
    # "don't like spicy", "not too spicy", "mild", "no spice", "hate spice"
    avoid_spice = bool(re.search(
        r"(don.t|not|avoid|hate|no).{0,10}(spic|hot|heat)|mild|not spicy|less spic",
        q
    ))

    # ── Detect price constraint ──────────────────────────────────────────────
    # "under $15", "below 12", "cheap", "budget", "affordable"
    max_price = None
    price_match = re.search(r"under\s*\$?(\d+)|below\s*\$?(\d+)|\$?(\d+)\s*or less", q)
    if price_match:
        val = next(v for v in price_match.groups() if v is not None)
        max_price = float(val)
    if re.search(r"\bcheap\b|\bbudget\b|\baffordable\b|\binexpensive\b", q):
        max_price = max_price or 12.0

    # ── Detect dietary preference ────────────────────────────────────────────
    vegetarian = bool(re.search(r"\bvegetarian\b|\bveg\b|\bno meat\b", q))
    vegan      = bool(re.search(r"\bvegan\b|\bplant.based\b|\bdairy.free\b", q))
    gf         = bool(re.search(r"\bgluten.free\b|\bno gluten\b|\bceliac\b", q))

    # ── Detect question type ─────────────────────────────────────────────────
    is_review_q   = bool(re.search(r"\b(review|customer|people|say|think|opinion|worth|recommend|crowd|packed)\b", q))
    is_hours_q    = bool(re.search(r"\b(hour|open|close|time|when|weekend|weekday|lunch|dinner|breakfast)\b", q))
    is_location_q = bool(re.search(r"\b(where|address|location|phone|contact|find)\b", q))
    is_signature_q = bool(re.search(r"\b(signature|special|best|must.try|famous|popular dish|most popular|popular)\b", q))
    # ── Route to the right strategy ──────────────────────────────────────────

    # Hours / location → only the restaurant_info chunk is relevant
    if is_hours_q or is_location_q:
        chunks = semantic_search(question, n_results=2, chunk_types=["restaurant_info"])
        return chunks, "semantic → restaurant_info only"

    # Review question → only review chunks
    if is_review_q and not avoid_spice and not vegetarian and not vegan:
        chunks = semantic_search(question, n_results=4, chunk_types=["review"])
        return chunks, "semantic → reviews only"

    # Signature/best dishes → menu items only, boost popular+signature
    if is_signature_q and not avoid_spice and not vegetarian:
        chunks = hybrid_search(
            question,
            n_results=5,
            chunk_types=["menu_item"],
        )
        # Re-rank: signature and popular items first
        chunks.sort(key=lambda c: (
            -int(c["metadata"].get("is_signature", False)),
            -int(c["metadata"].get("popular", False)),
            c["similarity"] * -1
        ))
        return chunks, "hybrid → menu_item, re-ranked by signature+popular"

    # Hard constraints present → hybrid search
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
        strategy = f"hybrid → filters: spice={spice_filter}, price≤{max_price}, veg={vegetarian}, vegan={vegan}, gf={gf}"
        return chunks, strategy

    # Default → broad semantic search across all chunk types
    chunks = semantic_search(question, n_results=5)
    return chunks, "semantic → all chunk types"


def format_chunks_for_llm(chunks: list[dict]) -> str:
    """
    Formats retrieved chunks into a clean string for the LLM prompt.
    The LLM will ONLY know what's in this string — nothing else.
    Clear formatting helps it distinguish menu items from reviews.
    """
    if not chunks:
        return "No relevant information found."

    formatted = []
    for i, chunk in enumerate(chunks, 1):
        chunk_type = chunk["metadata"].get("type", "unknown")
        similarity = chunk["similarity"]
        formatted.append(
            f"[Source {i} | type: {chunk_type} | relevance: {similarity}]\n"
            f"{chunk['text']}"
        )
    return "\n\n---\n\n".join(formatted)


def _unpack(results: dict) -> list[dict]:
    """Converts ChromaDB's nested response into a clean flat list."""
    chunks = []
    for doc, meta, dist, chunk_id in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
        results["ids"][0],
    ):
        chunks.append({
            "text": doc,
            "metadata": meta,
            "similarity": round(1 - dist, 4),
            "id": chunk_id,
        })
    return chunks


# ── Manual test ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("Retriever Test — with query routing")
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
        print(f"Results ({len(chunks)}):")
        for c in chunks:
            t = c["metadata"].get("type")
            name = c["metadata"].get("name", c["id"])
            spice = c["metadata"].get("spice_level", "")
            price = c["metadata"].get("price", "")
            spice_str = f" | spice:{spice}" if spice else ""
            price_str = f" | ${price}" if price else ""
            print(f"  [{t}] {name}{price_str}{spice_str} — sim:{c['similarity']}")

    print("\n" + "=" * 60)
    print("Check: spicy question should now return MILD dishes only")
    print("=" * 60)