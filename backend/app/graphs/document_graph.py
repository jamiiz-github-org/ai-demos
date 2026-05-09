"""
LangGraph document assistant — multi-step reasoning graph.

Flow:
  START
    → classify_intent
    → retrieve_context
    → generate_answer
    → check_confidence
    → END  (or clarify if confidence is low)

State travels through each node and accumulates results.
"""
import logging
from typing import Annotated, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph

from app.core.config import get_settings
from app.services.rag_service import get_rag_service

logger = logging.getLogger("jamiiz.graph.document")


# ── Graph state ───────────────────────────────────────────────────────

class DocumentGraphState(TypedDict):
    # Inputs
    question: str
    namespace: str
    history: list[dict]

    # Intermediate
    intent: str           # "summarise" | "extract" | "question" | "draft" | "evaluate"
    context_docs: list    # raw LangChain documents
    context_str: str      # formatted context for the prompt
    confidence: str       # "high" | "low"

    # Output
    answer: str
    sources: list[str]


# ── Nodes ─────────────────────────────────────────────────────────────

settings = get_settings()
_llm = ChatOpenAI(
    model=settings.openai_model,
    temperature=0.1,
    api_key=settings.openai_api_key,
)


def classify_intent(state: DocumentGraphState) -> dict:
    """Classify what kind of task the question requires."""
    prompt = f"""Classify this question into exactly one of these intents:
- summarise: the user wants a summary or overview
- extract: the user wants specific data, dates, requirements, or lists
- question: the user wants an answer to a specific question
- draft: the user wants to create content (email, proposal, summary doc)
- evaluate: the user wants to assess fit, risk, or completeness

Question: {state['question']}

Reply with just the intent word."""

    result = _llm.invoke([HumanMessage(content=prompt)])
    intent = result.content.strip().lower().split()[0]
    valid = {"summarise", "extract", "question", "draft", "evaluate"}
    if intent not in valid:
        intent = "question"

    logger.debug("Intent classified as: %s", intent)
    return {"intent": intent}


def retrieve_context(state: DocumentGraphState) -> dict:
    """Retrieve relevant chunks from Pinecone."""
    rag = get_rag_service()

    # For summaries, retrieve more chunks
    k = 8 if state["intent"] == "summarise" else 5

    docs, context_str = rag.retrieve_and_format(
        query=state["question"],
        namespace=state["namespace"],
        k=k,
    )
    sources = list({doc.metadata.get("source", "unknown") for doc in docs})

    logger.debug("Retrieved %d chunks, sources: %s", len(docs), sources)
    return {
        "context_docs": docs,
        "context_str": context_str,
        "sources": sources,
    }


def generate_answer(state: DocumentGraphState) -> dict:
    """Generate an answer using the retrieved context."""
    intent_instructions = {
        "summarise": "Provide a clear, structured summary. Use headings if helpful.",
        "extract": "Extract and list the specific information requested. Be precise.",
        "question": "Answer the question directly using the provided context.",
        "draft": "Draft the requested content. Be professional and complete.",
        "evaluate": "Evaluate based on the context. Highlight strengths, gaps, and recommendations.",
    }

    instruction = intent_instructions.get(state["intent"], intent_instructions["question"])

    system = f"""You are a Document AI Assistant for Jamiiz AI Systems. You help users understand, analyse, and act on their documents.

{instruction}

Rules:
- Only use information from the provided context.
- If the context doesn't contain enough information to answer, say so clearly.
- Always cite sources using [Source: filename] format.
- Be concise but complete.
- If drafting content, make it ready to use with minimal editing."""

    context = state.get("context_str", "")
    if context:
        system += f"\n\nDOCUMENT CONTEXT:\n{context}"
    else:
        system += "\n\nNote: No relevant content was found in the uploaded documents."

    messages = [SystemMessage(content=system)]

    # Include recent conversation history
    if state.get("history"):
        from langchain_core.messages import AIMessage
        for turn in state["history"][-4:]:
            if turn["role"] == "user":
                messages.append(HumanMessage(content=turn["content"]))
            elif turn["role"] == "assistant":
                messages.append(AIMessage(content=turn["content"]))

    messages.append(HumanMessage(content=state["question"]))

    result = _llm.invoke(messages)
    answer = result.content.strip()
    logger.debug("Generated answer (%d chars)", len(answer))
    return {"answer": answer}


def check_confidence(state: DocumentGraphState) -> dict:
    """
    Simple confidence check — if the model said it couldn't find info,
    mark confidence as low so we can surface that to the user.
    """
    low_confidence_phrases = [
        "don't have enough",
        "not in the context",
        "no relevant",
        "cannot find",
        "not mentioned",
        "not provided",
    ]
    answer_lower = state["answer"].lower()
    confidence = "low" if any(p in answer_lower for p in low_confidence_phrases) else "high"
    return {"confidence": confidence}


# ── Build the graph ───────────────────────────────────────────────────

def build_document_graph() -> StateGraph:
    graph = StateGraph(DocumentGraphState)

    graph.add_node("classify_intent", classify_intent)
    graph.add_node("retrieve_context", retrieve_context)
    graph.add_node("generate_answer", generate_answer)
    graph.add_node("check_confidence", check_confidence)

    graph.add_edge(START, "classify_intent")
    graph.add_edge("classify_intent", "retrieve_context")
    graph.add_edge("retrieve_context", "generate_answer")
    graph.add_edge("generate_answer", "check_confidence")
    graph.add_edge("check_confidence", END)

    return graph.compile()


# Singleton — compiled once at import time
document_graph = build_document_graph()


def run_document_graph(
    question: str,
    namespace: str,
    history: list[dict] | None = None,
) -> DocumentGraphState:
    """Entry point for the document assistant graph."""
    initial_state: DocumentGraphState = {
        "question": question,
        "namespace": namespace,
        "history": history or [],
        "intent": "",
        "context_docs": [],
        "context_str": "",
        "confidence": "high",
        "answer": "",
        "sources": [],
    }
    result = document_graph.invoke(initial_state)
    return result
