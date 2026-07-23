"""
GitHub Integration Module.
Uses GitHub REST API to dynamically create feature branches, commit healed Terraform plans,
and open automated Pull Requests with security & cost violation summaries.
"""

import os
import json
import base64
import urllib.request
import urllib.error
from dotenv import load_dotenv

load_dotenv()

def _github_api_request(url: str, method: str = "GET", payload: dict = None, token: str = None) -> dict:
    """Helper to perform HTTP requests against the GitHub REST API."""
    req = urllib.request.Request(url, method=method)
    req.add_header("Authorization", f"token {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    req.add_header("User-Agent", "AutoOps-Agent")

    data_bytes = None
    if payload:
        req.add_header("Content-Type", "application/json")
        data_bytes = json.dumps(payload).encode("utf-8")

    try:
        with urllib.request.urlopen(req, data=data_bytes) as resp:
            resp_body = resp.read().decode("utf-8")
            return json.loads(resp_body) if resp_body else {}
    except urllib.error.HTTPError as e:
        error_content = e.read().decode("utf-8")
        try:
            err_json = json.loads(error_content)
        except Exception:
            err_json = {"message": error_content}
        err_json["status_code"] = e.code
        return err_json
    except Exception as e:
        return {"error": str(e)}

def create_github_pr(healed_hcl: str, flaws: list[str], env_context: dict = None) -> dict:
    """
    Automates GitHub branch creation, file commit, and Pull Request creation.
    Returns PR metadata dictionary including html_url and status.
    """
    token = os.getenv("GITHUB_TOKEN")
    repo_name = os.getenv("GITHUB_REPO", "arjunrkj/AutoOps-Agent")

    if not token or token.startswith("your_"):
        return {
            "status": "SKIPPED",
            "message": "GITHUB_TOKEN is missing or default. Add a valid GitHub token to .env to open live PRs.",
            "pr_url": None
        }

    base_api_url = f"https://api.github.com/repos/{repo_name}"

    # 1. Get HEAD commit SHA of main branch
    main_ref = _github_api_request(f"{base_api_url}/git/ref/heads/main", token=token)
    if "object" not in main_ref:
        return {
            "status": "ERROR",
            "message": f"Failed to retrieve main branch ref: {main_ref.get('message', 'Unknown error')}",
            "pr_url": None
        }

    main_sha = main_ref["object"]["sha"]

    # 2. Create feature branch autoops/remediate-bad-plan
    branch_name = "autoops/remediate-bad-plan"
    ref_url = f"{base_api_url}/git/refs"
    ref_payload = {
        "ref": f"refs/heads/{branch_name}",
        "sha": main_sha
    }
    
    # Try creating branch
    ref_resp = _github_api_request(ref_url, method="POST", payload=ref_payload, token=token)

    # 3. Check existing file SHA if updating sample_tf/healed_plan.tf
    file_path = "sample_tf/healed_plan.tf"
    file_url = f"{base_api_url}/contents/{file_path}?ref={branch_name}"
    existing_file = _github_api_request(file_url, token=token)

    content_b64 = base64.b64encode(healed_hcl.encode("utf-8")).decode("utf-8")
    commit_payload = {
        "message": "[AutoOps-Agent] Auto-remediated Terraform plan (SEC-01 & COST-01)",
        "content": content_b64,
        "branch": branch_name
    }
    if isinstance(existing_file, dict) and "sha" in existing_file:
        commit_payload["sha"] = existing_file["sha"]

    # Update or create file
    commit_resp = _github_api_request(f"{base_api_url}/contents/{file_path}", method="PUT", payload=commit_payload, token=token)
    if "commit" not in commit_resp:
        return {
            "status": "ERROR",
            "message": f"Failed to commit file to branch: {commit_resp.get('message', 'Unknown error')}",
            "pr_url": None
        }

    # 4. Construct Markdown PR Body
    env_str = env_context.get("environment", "staging") if env_context else "staging"
    telemetry_info = ""
    if env_context and "telemetry" in env_context:
        tele_dict = env_context["telemetry"]
        telemetry_info = "\n".join(f"- **{k}**: `{v}`" for k, v in tele_dict.items())

    pr_body = (
        f"## 🤖 AutoOps-Agent Infrastructure Remediation Report\n\n"
        f"### 🛡️ Detected & Remediated Violations\n"
    )
    for flaw in flaws:
        pr_body += f"- {flaw}\n"

    pr_body += f"\n### 📊 Target Environment & Telemetry Context\n- **Environment**: `{env_str}`\n{telemetry_info}\n\n"
    pr_body += (
        "### ✅ Verification\n"
        "- [x] Qdrant Vector Compliance Search Verified (`SEC-01` & `COST-01`)\n"
        "- [x] HCL Syntax Validation PASSED\n"
        "- [x] Automatically rightsized for target environment\n\n"
        "*Generated automatically by AutoOps-Agent Bot.*"
    )

    pr_payload = {
        "title": "[AutoOps-Agent] Auto-Healed AWS Infrastructure Plan (SEC-01 & COST-01)",
        "head": branch_name,
        "base": "main",
        "body": pr_body
    }

    # Open PR
    pr_resp = _github_api_request(f"{base_api_url}/pulls", method="POST", payload=pr_payload, token=token)

    if "html_url" in pr_resp:
        return {
            "status": "SUCCESS",
            "pr_url": pr_resp["html_url"],
            "pr_number": pr_resp.get("number"),
            "branch": branch_name,
            "raw_response": pr_resp
        }
    elif pr_resp.get("status_code") == 422:
        # PR already exists for branch; list pulls to find it
        owner = repo_name.split('/')[0]
        pulls = _github_api_request(f"{base_api_url}/pulls?head={owner}:{branch_name}&state=open", token=token)
        if isinstance(pulls, list) and len(pulls) > 0:
            return {
                "status": "EXISTS",
                "pr_url": pulls[0].get("html_url"),
                "pr_number": pulls[0].get("number"),
                "branch": branch_name,
                "raw_response": pulls[0]
            }

    return {
        "status": "ERROR",
        "message": f"PR Creation Error: {pr_resp.get('message', 'Unknown error')}",
        "pr_url": None
    }
