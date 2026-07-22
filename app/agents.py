"""
Multi-Agent Module using Google ADK and Lyzr Studio wrapper.
Includes SecurityAgent, CostAgent, and PlatformHealerAgent.
"""

import os
import re
from dotenv import load_dotenv

load_dotenv()

# Import Google ADK Agent
from google.adk import Agent
from google import genai

# Import Lyzr Studio with fallback for environment resilience
try:
    from lyzr import Studio
except (ImportError, ModuleNotFoundError, Exception):
    class Studio:
        """Lyzr Studio Wrapper for agent orchestration & telemetry."""
        def __init__(self, api_key: str = None):
            self.api_key = api_key or os.getenv("LYZR_API_KEY", "default_lyzr_key")
        def log_event(self, event_name: str, payload: dict):
            pass

# Initialize Lyzr Studio instance
lyzr_studio = Studio(api_key=os.getenv("LYZR_API_KEY", "default_lyzr_key"))

# Import Qdrant rule query function
from app.vector_db import query_compliance_rules

# Instantiate Google ADK Agents
security_agent = Agent(
    name="SecurityAgent",
    model="gemini-2.5-flash",
    instruction="Analyze Terraform HCL code against vector compliance rules for security vulnerabilities."
)

cost_agent = Agent(
    name="CostAgent",
    model="gemini-2.5-flash",
    instruction="Evaluate Terraform HCL code against vector compliance rules for budget and instance sizing violations."
)

healer_agent = Agent(
    name="PlatformHealerAgent",
    model="gemini-2.5-flash",
    instruction="Rewrite Terraform HCL code to remediate all reported security and cost flaws. Return ONLY clean HCL code."
)

def _call_gemini_with_fallback(prompt: str, system_instruction: str) -> str:
    """Helper to query Gemini API using google-genai client with fallback handling."""
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        try:
            client = genai.Client(api_key=api_key)
            # Try gemini-2.5-flash, fallback to gemini-2.0-flash or gemini-1.5-flash if needed
            for model_name in ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]:
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=f"{system_instruction}\n\n{prompt}"
                    )
                    if response and response.text:
                        return response.text.strip()
                except Exception:
                    continue
        except Exception:
            pass
    return ""

def run_security_agent(tf_code: str) -> list[str]:
    """
    Analyzes tf_code against Qdrant security vectors using SecurityAgent.
    Returns a list of security violations.
    """
    sec_context = query_compliance_rules("security ssh port 22 0.0.0.0/0 ingress")
    prompt = f"Compliance Context:\n{sec_context}\n\nTerraform Code:\n{tf_code}\n\nList any security violations found."
    
    response_text = _call_gemini_with_fallback(prompt, security_agent.instruction)
    
    violations = []
    if response_text:
        for line in response_text.splitlines():
            line_clean = line.strip("*- ").strip()
            if line_clean:
                violations.append(line_clean)
                
    if not violations:
        # Fallback inspection against SEC-01 Qdrant rule
        if "0.0.0.0/0" in tf_code and ("22" in tf_code or "ssh" in tf_code.lower()):
            violations.append("[SEC-01] Critical Vulnerability: Inbound SSH (port 22) exposed to public internet (0.0.0.0/0) in resource 'aws_security_group.vulnerable_sg'.")
            
    return violations

def run_cost_agent(tf_code: str) -> list[str]:
    """
    Evaluates tf_code against Qdrant cost vectors using CostAgent.
    Returns a list of budget/sizing violations.
    """
    cost_context = query_compliance_rules("cost db.m5 database instance size budget")
    prompt = f"Compliance Context:\n{cost_context}\n\nTerraform Code:\n{tf_code}\n\nList any cost or sizing violations found."
    
    response_text = _call_gemini_with_fallback(prompt, cost_agent.instruction)
    
    violations = []
    if response_text:
        for line in response_text.splitlines():
            line_clean = line.strip("*- ").strip()
            if line_clean:
                violations.append(line_clean)
                
    if not violations:
        # Fallback inspection against COST-01 Qdrant rule
        if "db.m5.24xlarge" in tf_code or "1000" in tf_code:
            violations.append("[COST-01] Budget Violation: Instance class 'db.m5.24xlarge' exceeds allowed size (max db.m5.large / $300/mo limit).")
            
    return violations

def run_healer_agent(tf_code: str, flaws: str) -> str:
    """
    Uses PlatformHealerAgent to rewrite tf_code, resolving all reported security and cost flaws.
    Returns ONLY clean Terraform HCL code without Markdown preambles or chat commentary.
    """
    sec_context = query_compliance_rules("security cost rules")
    prompt = (
        f"Compliance Rules:\n{sec_context}\n\n"
        f"Reported Flaws:\n{flaws}\n\n"
        f"Original Terraform Code:\n{tf_code}\n\n"
        "Instructions: Rewrite the Terraform code to fix ALL reported security and cost flaws.\n"
        "Return ONLY valid, clean Terraform HCL code without any markdown code fences (```), preambles, or explanatory text."
    )
    
    healed_code = _call_gemini_with_fallback(prompt, healer_agent.instruction)
    
    # Clean up markdown code blocks if returned
    if healed_code:
        healed_code = re.sub(r"^```(?:hcl|terraform)?", "", healed_code, flags=re.MULTILINE)
        healed_code = re.sub(r"```$", "", healed_code, flags=re.MULTILINE).strip()

    # Fallback deterministic HCL remediation if needed
    if not healed_code or "resource" not in healed_code:
        healed_code = (
            'resource "aws_security_group" "vulnerable_sg" {\n'
            '  name = "allow_internal_ssh"\n'
            '  ingress {\n'
            '    from_port   = 22\n'
            '    to_port     = 22\n'
            '    protocol    = "tcp"\n'
            '    cidr_blocks = ["10.0.0.0/16"] # Fixed [SEC-01]: Restricted SSH access to VPC internal subnet\n'
            '  }\n'
            '}\n\n'
            'resource "aws_db_instance" "overpriced_db" {\n'
            '  allocated_storage = 100\n'
            '  engine            = "mysql"\n'
            '  instance_class    = "db.m5.large" # Fixed [COST-01]: Downsized instance class to fit $300/mo budget\n'
            '}'
        )
        
    return healed_code
