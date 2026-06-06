# 🍛 what do I eat?

**An AI-powered restaurant assistant built with RAG (Retrieval-Augmented Generation)**

🔗 **Live Demo:** https://what-do-i-eat.streamlit.app/

Ask the bot anything about Sangam Chettinad Indian Cuisine in Austin, TX — what to order, dietary options, hours, what customers say, and more.

---

## What it does

- Recommends dishes based on your spice preference, dietary restrictions, and budget
- Answers questions about the menu, hours, and location
- Summarizes what real customers say in reviews
- Remembers context within a conversation (follow-up questions work naturally)
- Shows which data chunks were retrieved for full RAG transparency (debug mode)

---

## RAG Architecture

```
JSON Data → Chunking → OpenAI Embeddings → Pinecone Vector DB
                                                    ↓
User Question → Query Router → Semantic / Hybrid Search → Top-k Chunks
                                                    ↓
                              Chunks + Question → GPT-4o → Answer
```

### Pipeline breakdown

| Stage | What happens | Tech used |
|---|---|---|
| Data ingestion | Restaurant JSON split into 24 meaningful chunks | Python |
| Embedding | Each chunk converted to 1536-dimensional vector | OpenAI text-embedding-3-small |
| Vector storage | Vectors + metadata stored in cloud vector DB | Pinecone |
| Query routing | Question intent detected → right retrieval strategy selected | Python (regex) |
| Retrieval | Semantic search or hybrid (metadata filter + semantic) | Pinecone |
| Generation | Retrieved chunks injected into prompt → natural language answer | GPT-4o mini |
| UI | Chat interface with debug mode and quick-question buttons | Streamlit |

---

## Chunk strategy

| Chunk type | Count | Purpose |
|---|---|---|
| `restaurant_info` | 1 | Hours, location, phone, dietary tags |
| `menu_item` | 17 | One chunk per dish with price, spice level, tags |
| `review` | 5 | One chunk per Google review |
| `unlisted_items` | 1 | Off-menu items mentioned in reviews |
| **Total** | **24** | |

---

## Query routing

The retriever detects question intent and picks the right strategy automatically:

| Question type | Strategy | Example |
|---|---|---|
| Spice/diet/price constraint | Hybrid search (metadata filter + semantic) | "vegetarian under $12" |
| Hours or location | Semantic → restaurant_info only | "what time do you open?" |
| Reviews / opinions | Semantic → reviews only | "what do customers say?" |
| Signature / popular dishes | Hybrid → re-ranked by is_signature + popular | "what's the best dish?" |
| General | Broad semantic search | "what should I try?" |

---

## Tech stack

- **Language:** Python 3.13
- **Embeddings:** OpenAI `text-embedding-3-small`
- **Vector DB:** Pinecone (free tier, cloud hosted)
- **LLM:** OpenAI `gpt-4o-mini`
- **UI:** Streamlit
- **Deployment:** Streamlit Community Cloud

---

## Project structure

```
whatdoieat/
├── data/
│   └── sangam_chettinad_data.json   # Restaurant data (menu + reviews)
├── src/
│   ├── ingest.py                    # Chunk → embed → store in Pinecone
│   ├── retriever.py                 # Query router + Pinecone search
│   ├── chain.py                     # LangChain RAG chain + conversation memory
│   └── verify_db.py                 # Validates ChromaDB ingestion (local dev)
├── app.py                           # Streamlit web UI
├── requirements.txt
└── .env                             # API keys (never committed)
```

---

## Run locally

```bash
# Clone the repo
git clone https://github.com/digvijaypatil11/whatdoieat.git
cd whatdoieat

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Add your API keys
cp .env.example .env
# Edit .env and add:
# OPENAI_API_KEY=sk-...
# PINECONE_API_KEY=pcsk_...

# Load data into Pinecone
python src/ingest.py

# Run the app
streamlit run app.py
```

---

## Key concepts learned

- **Chunking strategy** — why chunk size and structure directly affect retrieval quality
- **Vector embeddings** — how text becomes numbers that capture semantic meaning
- **Cosine similarity** — how ChromaDB/Pinecone finds the closest matching chunks
- **Hybrid search** — combining hard metadata filters with semantic search
- **Query routing** — detecting question intent to pick the right retrieval strategy
- **RAG grounding** — forcing the LLM to answer only from retrieved context
- **Conversation memory** — simulating stateful chat with a stateless LLM API

---

## Built by

**Digvijay Patil** — Data Engineer  
[GitHub](https://github.com/digvijaypatil11)
