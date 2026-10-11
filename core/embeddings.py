"""Turn text into vectors ("embeddings") so we can search by meaning, not just keywords.

Model: Qwen/Qwen3-Embedding-8B on Nebius Token Factory (no NVIDIA embedding model
was available there), shortened to 1024 dimensions.
"""
from core.llm import client

MODEL = "Qwen/Qwen3-Embedding-8B"
DIMENSIONS = 1024

# Qwen3-Embedding works best when a search QUERY carries a short task instruction.
# Documents (the schemes) are embedded as-is.
QUERY_INSTRUCTION = (
    "Instruct: Given a person's description of their situation or need, "
    "retrieve government schemes and benefits that could help them\nQuery: "
)


def embed_documents(texts: list[str]) -> list[list[float]]:
    response = client().embeddings.create(model=MODEL, input=texts, dimensions=DIMENSIONS)
    return [item.embedding for item in sorted(response.data, key=lambda d: d.index)]


def embed_query(text: str) -> list[float]:
    return embed_documents([QUERY_INSTRUCTION + text])[0]


def scheme_document(scheme: dict) -> str:
    """The text that represents a scheme for search: what it is, who it's for, what it gives."""
    sections = scheme["sections"]
    meta = scheme.get("meta") or {}
    parts = [
        scheme["name"],
        scheme.get("summary") or "",
        "Categories: " + ", ".join(scheme.get("categories") or []),
        "Tags: " + ", ".join(meta.get("tags") or []),
        "Eligibility: " + (sections.get("eligibility") or sections.get("overview") or "")[:1500],
        "Benefits: " + (sections.get("benefits") or "")[:800],
    ]
    return "\n".join(p for p in parts if p.strip())
