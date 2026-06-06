"""
chain.py — Phase 2, Step 3: The LLM layer

WHY THIS FILE EXISTS:
The retriever gives us relevant chunks — raw facts.
The chain turns those raw facts into a conversational answer.

THE RAG PROMPT FORMULA (memorize this for interviews):
  System prompt        → who the bot is, rules it must follow
  + Retrieved context  → the facts from ChromaDB (ONLY source of truth)
  + Conversation history → what was said earlier in this chat
  + User question      → what they're asking right now
  ─────────────────────────────────────────────────────────
  = GPT-4o answer      → grounded, relevant, conversational

KEY CONCEPT — GROUNDING:
  Without RAG, GPT-4o would answer from its training data — which might be
  wrong, outdated, or hallucinated. With RAG, we FORCE it to answer only from
  the chunks we retrieved. This is called "grounding" the LLM.
  The system prompt tells it: "only use the context provided, nothing else."

KEY CONCEPT — CONVERSATION MEMORY:
  LLMs have no memory between API calls. Every call is stateless.
  We simulate memory by appending previous Q&A pairs to each new request.
  This is why "what about a vegan option for that?" works as a follow-up —
  the chain includes the previous exchange so GPT-4o knows what "that" refers to.
"""

import os
from openai import OpenAI
from dotenv import load_dotenv
from retriever import route_query, format_chunks_for_llm

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ── System prompt ─────────────────────────────────────────────────────────────
# WHY THIS MATTERS:
# The system prompt is the most important prompt engineering decision you make.
# It sets the bot's identity, constraints, and behavior for the entire conversation.
# A vague system prompt → vague, unreliable answers.
# A precise system prompt → consistent, trustworthy answers.

SYSTEM_PROMPT = """You are WhatDoIEat, a friendly and knowledgeable food assistant
specifically for Sangam Chettinad Indian Cuisine in Austin, TX.

Your job is to help customers decide what to order based on their preferences,
dietary needs, and curiosity about the restaurant.

STRICT RULES — follow these without exception:
1. ONLY use information from the context provided below. Never make up menu items,
   prices, or facts about the restaurant.
2. If the context doesn't contain enough information to answer, say so honestly.
   For example: "I don't have that information — I'd suggest calling the restaurant."
3. When recommending dishes, always mention the price and spice level.
4. If a user mentions a dietary restriction, only recommend dishes that match it.
5. Be warm and conversational — you're a helpful food guide, not a search engine.
6. Keep answers focused and under 150 words unless the user asks for detail.

YOUR PERSONALITY:
- Enthusiastic about South Indian and Chettinad cuisine
- Honest about spice levels — never downplay heat
- Proactive — if someone asks for one dish, suggest a complementary side
- Transparent — if you're unsure, say so rather than guess
"""


def ask(question: str, conversation_history: list[dict] = None) -> dict:
    """
    The main function. Takes a question, retrieves relevant chunks,
    builds the prompt, calls GPT-4o, returns the answer.

    Args:
        question:             the user's current question
        conversation_history: list of previous {"role": "...", "content": "..."}
                              dicts from earlier in the conversation

    Returns:
        dict with keys:
          answer       → the LLM's response string
          chunks_used  → the retrieved chunks (for debugging/transparency)
          strategy     → which retrieval strategy was used
          history      → updated conversation history to pass into the next call
    """
    if conversation_history is None:
        conversation_history = []

    # ── Step 1: Retrieve relevant chunks ──────────────────────────────────────
    # WHY route_query instead of semantic_search directly?
    # route_query detects the question type and picks the right retrieval strategy.
    # Passing conversation context helps with follow-up questions like
    # "what about something vegan?" where "something" needs prior context.
    chunks, strategy = route_query(question)
    context = format_chunks_for_llm(chunks)

    # ── Step 2: Build the messages array ─────────────────────────────────────
    # OpenAI's chat API takes a list of messages. The order matters:
    #   [system] → sets the rules for the whole conversation
    #   [user/assistant pairs] → conversation history (memory)
    #   [user with context] → the current question + retrieved facts

    # The context is injected into the USER message, not the system message.
    # WHY? Because context changes every turn (different chunks retrieved each time).
    # The system message stays constant — only the context changes.
    user_message_with_context = f"""Context from Sangam Chettinad restaurant database:
{context}

---
Customer question: {question}

Answer based only on the context above."""

    messages = (
        [{"role": "system", "content": SYSTEM_PROMPT}]
        + conversation_history
        + [{"role": "user", "content": user_message_with_context}]
    )

    # ── Step 3: Call GPT-4o ───────────────────────────────────────────────────
    response = client.chat.completions.create(
        model="gpt-4o-mini",   # cheaper than gpt-4o, still excellent for this task
        messages=messages,
        temperature=0.7,       # 0 = deterministic, 1 = creative. 0.7 is a good balance
        max_tokens=400,        # caps the answer length — prevents runaway responses
    )

    answer = response.choices[0].message.content

    # ── Step 4: Update conversation history ──────────────────────────────────
    # WHY store only the question, not the question+context?
    # The context (chunks) is retrieved fresh each turn. Storing it in history
    # would bloat the prompt with stale data. We only keep the clean Q&A pairs.
    updated_history = conversation_history + [
        {"role": "user",      "content": question},  # clean question, no context
        {"role": "assistant", "content": answer},
    ]

    # Trim history to last 6 exchanges (3 turns) to avoid token limits
    # WHY 6? Each exchange = 2 messages (user + assistant). 3 turns of context
    # is enough for follow-up questions without bloating the prompt.
    if len(updated_history) > 6:
        updated_history = updated_history[-6:]

    return {
        "answer":      answer,
        "chunks_used": chunks,
        "strategy":    strategy,
        "history":     updated_history,
    }


def chat():
    """
    Interactive terminal chat — lets you have a real conversation with the bot.
    Type 'quit' to exit, 'debug' to see which chunks were retrieved last turn.
    """
    print("=" * 60)
    print("WhatDoIEat — Sangam Chettinad Assistant")
    print("Type 'quit' to exit | 'debug' to see retrieved chunks")
    print("=" * 60)

    history = []
    last_chunks = []

    while True:
        question = input("\nYou: ").strip()

        if not question:
            continue
        if question.lower() == "quit":
            print("Goodbye!")
            break
        if question.lower() == "debug":
            if last_chunks:
                print("\n--- Last retrieved chunks ---")
                for c in last_chunks:
                    print(f"  [{c['metadata'].get('type')}] "
                          f"{c['metadata'].get('name', c['id'])} "
                          f"— sim:{c['similarity']}")
            else:
                print("No chunks yet.")
            continue

        result = ask(question, history)
        history = result["history"]
        last_chunks = result["chunks_used"]

        print(f"\nBot: {result['answer']}")
        print(f"     [strategy: {result['strategy']}]")


# ── Automated test ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("Chain Automated Test")
    print("=" * 60)

    # Test 1: Single question
    print("\n[Test 1] Single question")
    result = ask("What should I order if I don't like spicy food?")
    print(f"Q: What should I order if I don't like spicy food?")
    print(f"A: {result['answer']}")
    print(f"Strategy: {result['strategy']}")

    # Test 2: Follow-up conversation (tests memory)
    print("\n[Test 2] Follow-up conversation (tests memory)")
    history = []

    q1 = "What's good for a first timer?"
    r1 = ask(q1, history)
    history = r1["history"]
    print(f"Q: {q1}")
    print(f"A: {r1['answer']}")

    q2 = "Is any of that vegan?"
    r2 = ask(q2, history)
    history = r2["history"]
    print(f"\nQ: {q2}")
    print(f"A: {r2['answer']}")

    q3 = "What time should I come for dinner?"
    r3 = ask(q3, history)
    print(f"\nQ: {q3}")
    print(f"A: {r3['answer']}")

    # Test 3: Edge case — question the bot shouldn't hallucinate on
    print("\n[Test 3] Edge case — out of scope question")
    result = ask("Do you have a loyalty program?")
    print(f"Q: Do you have a loyalty program?")
    print(f"A: {result['answer']}")

    print("\n" + "=" * 60)
    print("If answers are grounded and relevant, chain.py is working.")
    print("Run `python src/chain.py` again to start interactive chat.")
    print("=" * 60)