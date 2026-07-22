"""
Vector Database Module using Qdrant (in-memory).
Stores and retrieves platform compliance rules.
"""

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue

# Initialize in-memory Qdrant client
_client = QdrantClient(":memory:")
_COLLECTION_NAME = "compliance_rules"

# Rules definition
RULES = [
    {
        "id": 1,
        "rule_id": "SEC-01",
        "category": "security",
        "text": "AWS Security Groups must never expose SSH port 22 or any inbound port to 0.0.0.0/0.",
        "vector": [1.0, 0.0, 0.0, 0.0]
    },
    {
        "id": 2,
        "rule_id": "COST-01",
        "category": "cost",
        "text": "AWS Database instances must not exceed db.m5.large or $300/month budget.",
        "vector": [0.0, 1.0, 0.0, 0.0]
    }
]

def init_vector_db():
    """Initializes compliance_rules collection in Qdrant and seeds knowledge vectors."""
    collections = _client.get_collections().collections
    exists = any(c.name == _COLLECTION_NAME for c in collections)
    
    if not exists:
        _client.create_collection(
            collection_name=_COLLECTION_NAME,
            vectors_config=VectorParams(size=4, distance=Distance.COSINE)
        )
        
        points = [
            PointStruct(
                id=item["id"],
                vector=item["vector"],
                payload={
                    "rule_id": item["rule_id"],
                    "category": item["category"],
                    "text": item["text"]
                }
            )
            for item in RULES
        ]
        _client.upsert(collection_name=_COLLECTION_NAME, points=points)

# Auto-initialize on import
init_vector_db()

def query_compliance_rules(query: str) -> str:
    """
    Queries Qdrant for matching compliance rules based on context query.
    Returns matched compliance rule context string.
    """
    query_lower = query.lower()
    
    # Simple semantic vector search scoring based on query terms
    sec_score = sum(term in query_lower for term in ["sec", "ssh", "port", "22", "ingress", "security", "0.0.0.0"])
    cost_score = sum(term in query_lower for term in ["cost", "db", "database", "m5", "budget", "instance", "overpriced"])
    
    if sec_score > cost_score and sec_score > 0:
        query_vector = [1.0, 0.0, 0.0, 0.0]
    elif cost_score > sec_score and cost_score > 0:
        query_vector = [0.0, 1.0, 0.0, 0.0]
    else:
        query_vector = [0.5, 0.5, 0.0, 0.0]

    search_result = _client.query_points(
        collection_name=_COLLECTION_NAME,
        query=query_vector,
        limit=2
    )

    matched_texts = []
    for point in search_result.points:
        rule_id = point.payload.get("rule_id", "")
        text = point.payload.get("text", "")
        matched_texts.append(f"[{rule_id}] {text}")

    return "\n".join(matched_texts)
