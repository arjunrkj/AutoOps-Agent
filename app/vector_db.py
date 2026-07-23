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
        "text": "AWS Security Groups must never expose SSH port 22 or any inbound port to 0.0.0.0/0 across any environment (dev, staging, prod).",
        "vector": [1.0, 0.0, 0.0, 0.0]
    },
    {
        "id": 2,
        "rule_id": "COST-01",
        "category": "cost",
        "text": "In dev/staging environments or workloads with low P95 CPU utilization (< 25%), AWS Database instances must not exceed db.m5.large ($300/month budget). Downscale oversized instances based on telemetry metrics.",
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

import re

# Auto-initialize on import
init_vector_db()

def parse_tf_ast(tf_code: str) -> dict:
    """
    Lightweight HCL AST Parser.
    Extracts resource blocks, resource types, names, key attributes, and dynamic search terms.
    """
    resources = []
    # Pattern to match resource "type" "name" { body }
    resource_pattern = re.compile(r'resource\s+"([^"]+)"\s+"([^"]+)"\s*\{([^}]*)\}', re.MULTILINE | re.DOTALL)
    
    for match in resource_pattern.finditer(tf_code):
        res_type, res_name, res_body = match.groups()
        
        attributes = []
        for line in res_body.splitlines():
            line_str = line.strip()
            if not line_str or line_str.startswith("#"):
                continue
            attr_match = re.match(r'([a-zA-Z0-9_]+)\s*=\s*(.+)', line_str)
            if attr_match:
                key, val = attr_match.groups()
                attributes.append({"key": key.strip(), "value": val.strip().strip('"')})
            elif "{" in line_str:
                block_name = line_str.split("{")[0].strip()
                attributes.append({"block": block_name})
                
        resources.append({
            "type": res_type,
            "name": res_name,
            "attributes": attributes,
            "raw_body": res_body.strip()
        })

    # Dynamically extract search terms from AST
    sec_keywords = []
    cost_keywords = []
    
    for res in resources:
        res_type = res["type"]
        if "security_group" in res_type or "firewall" in res_type:
            sec_keywords.append(f"security {res_type}")
            for attr in res["attributes"]:
                if attr.get("block") == "ingress" or "port" in str(attr):
                    sec_keywords.append("ingress port 22 0.0.0.0/0")
        if "db" in res_type or "instance" in res_type or "compute" in res_type:
            cost_keywords.append(f"cost {res_type}")
            for attr in res["attributes"]:
                if attr.get("key") == "instance_class" or "storage" in attr.get("key", ""):
                    cost_keywords.append(f"instance {attr.get('value', '')} budget telemetry")
                    
    return {
        "resources": resources,
        "sec_query": " ".join(sec_keywords) if sec_keywords else "security ssh port 22 0.0.0.0/0",
        "cost_query": " ".join(cost_keywords) if cost_keywords else "cost db.m5 database instance budget telemetry"
    }

def query_rules_from_ast(tf_code: str, category: str = None) -> tuple[str, dict]:
    """
    Parses HCL code into AST, dynamically builds query terms, and queries Qdrant DB.
    Returns tuple of (matched_rules_text, ast_metadata).
    """
    ast_data = parse_tf_ast(tf_code)
    
    if category == "security":
        query_text = ast_data["sec_query"]
    elif category == "cost":
        query_text = ast_data["cost_query"]
    else:
        query_text = f"{ast_data['sec_query']} {ast_data['cost_query']}"
        
    rules_text = query_compliance_rules(query_text)
    return rules_text, ast_data

def query_compliance_rules(query: str) -> str:
    """
    Queries Qdrant for matching compliance rules based on context query.
    Returns matched compliance rule context string.
    """
    query_lower = query.lower()
    
    # Semantic vector search scoring based on query terms
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
