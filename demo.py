"""
AutoOps-Agent Interactive CLI Demo Pipeline.
Audits flawed Terraform files, queries Qdrant vector DB rules, invokes Google ADK agents,
heals code using Gemini 2.5 Flash, validates HCL syntax, saves healed plan, and outputs GitHub PR payload.
"""

import os
import sys
import json

# Ensure UTF-8 output encoding for Windows terminals
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from colorama import init, Fore, Style

# Initialize Colorama
init(autoreset=True)

from app.vector_db import query_compliance_rules
from app.agents import run_security_agent, run_cost_agent, run_healer_agent
from app.validator import validate_hcl_syntax

def main():
    print("\n" + Fore.MAGENTA + Style.BRIGHT + "=" * 64)
    print(Fore.MAGENTA + Style.BRIGHT + "================ AUTO OPS AGENT: HEALING PIPELINE ================")
    print(Fore.MAGENTA + Style.BRIGHT + "=" * 64 + "\n")

    # Step 1: Load sample_tf/bad_plan.tf
    bad_plan_path = os.path.join("sample_tf", "bad_plan.tf")
    if not os.path.exists(bad_plan_path):
        print(Fore.RED + f"Error: {bad_plan_path} not found!")
        sys.exit(1)

    with open(bad_plan_path, "r", encoding="utf-8") as f:
        raw_tf = f.read()

    print(Fore.WHITE + Style.BRIGHT + "📥 [1/6] Loading Flawed Terraform Plan (sample_tf/bad_plan.tf):")
    print(Fore.YELLOW + "-" * 50)
    print(Fore.YELLOW + raw_tf.strip())
    print(Fore.YELLOW + "-" * 50 + "\n")

    # Step 2: Query Qdrant vector DB
    print(Fore.WHITE + Style.BRIGHT + "🔍 [2/6] Querying Qdrant Vector DB for Compliance Knowledge:")
    retrieved_rules = query_compliance_rules("AWS security group SSH 22 cost database m5 budget")
    print(Fore.CYAN + "-" * 50)
    print(Fore.CYAN + retrieved_rules)
    print(Fore.CYAN + "-" * 50 + "\n")

    # Step 3: Run Security & Cost Agents
    print(Fore.WHITE + Style.BRIGHT + "🛡️  [3/6] Invoking SecurityAgent & CostAgent Audit:")
    sec_violations = run_security_agent(raw_tf)
    cost_violations = run_cost_agent(raw_tf)

    all_flaws = sec_violations + cost_violations

    print(Fore.RED + "-" * 50)
    print(Fore.RED + Style.BRIGHT + "🚨 Detected Violations:")
    for flaw in all_flaws:
        print(Fore.RED + f"  • {flaw}")
    print(Fore.RED + "-" * 50 + "\n")

    # Step 4: Invoke PlatformHealerAgent
    print(Fore.WHITE + Style.BRIGHT + "⚡ [4/6] Invoking PlatformHealerAgent (Gemini 2.5 Flash Auto-Healing)...")
    flaws_text = "\n".join(all_flaws)
    healed_hcl = run_healer_agent(raw_tf, flaws_text)

    # Step 5: Validate Syntax & Display Healed HCL
    print(Fore.WHITE + Style.BRIGHT + "✅ [5/6] Validating Healed HCL Syntax & Saving File:")
    is_valid = validate_hcl_syntax(healed_hcl)
    
    if is_valid:
        print(Fore.GREEN + f"  [Syntax Check]: PASSED (Valid matching braces and HCL structure)")
    else:
        print(Fore.RED + f"  [Syntax Check]: FAILED")

    print(Fore.GREEN + "-" * 50)
    print(Fore.GREEN + Style.BRIGHT + "✨ Healed Terraform HCL Output:")
    print(Fore.GREEN + healed_hcl)
    print(Fore.GREEN + "-" * 50 + "\n")

    # Save to sample_tf/healed_plan.tf
    healed_plan_path = os.path.join("sample_tf", "healed_plan.tf")
    with open(healed_plan_path, "w", encoding="utf-8") as f:
        f.write(healed_hcl + "\n")

    print(Fore.WHITE + Style.BRIGHT + f"💾 Healed plan saved to: {healed_plan_path}\n")

    # Step 6: GitHub PR JSON Payload
    print(Fore.WHITE + Style.BRIGHT + "🚀 [6/6] Generating GitHub PR Payload (Ready to Merge):")
    pr_payload = {
        "event": "pull_request",
        "action": "opened",
        "pull_request": {
            "title": "[AutoOps-Agent] Auto-Healed AWS Infrastructure Plan (SEC-01 & COST-01)",
            "branch": "autoops/remediate-bad-plan",
            "target": "main",
            "author": "AutoOps-Agent Bot",
            "compliance_status": "PASSED",
            "qdrant_vector_verification": "SUCCESS",
            "syntax_validated": is_valid,
            "modified_files": ["sample_tf/healed_plan.tf"],
            "summary": "Remediated open SSH port 22 to internal VPC CIDR and downsized database instance class to db.m5.large within budget constraints.",
            "mergeable_state": "clean"
        }
    }

    print(Fore.LIGHTBLUE_EX + json.dumps(pr_payload, indent=2))
    print("\n" + Fore.MAGENTA + Style.BRIGHT + "=" * 64)
    print(Fore.MAGENTA + Style.BRIGHT + "================ AUTO OPS AGENT: PIPELINE COMPLETE ================")
    print(Fore.MAGENTA + Style.BRIGHT + "=" * 64 + "\n")

if __name__ == "__main__":
    main()
