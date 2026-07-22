# 🚀 AutoOps-Agent: Autonomous Multi-Agent Platform Engineering Framework

![Google ADK](https://img.shields.io/badge/Google--ADK-Agent--Development--Kit-4285F4?logo=google&logoColor=white)
![Qdrant](https://img.shields.io/badge/Qdrant-Vector--Database-DC2626?logo=qdrant&logoColor=white)
![Lyzr](https://img.shields.io/badge/Lyzr-Studio-7C3AED)
![Gemini 2.5 Flash](https://img.shields.io/badge/Gemini--2.5--Flash-Auto--Healing-0052CC?logo=google-gemini&logoColor=white)
![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)

**AutoOps-Agent** is an autonomous multi-agent platform engineering framework built for cloud infrastructure teams. It audits flawed AWS Terraform HCL files against vector compliance rules in Qdrant and uses Google ADK with Gemini 2.5 Flash to automatically remediate code flaws and publish ready-to-merge GitHub Pull Requests.

---

## 📌 Problem Statement

Manual code reviews and infrastructure drift enforcement are slow, error-prone, and expensive. Security misconfigurations (such as open SSH ports) and over-budget cloud instance allocations often bypass manual checks, resulting in security breaches or unexpected cloud bills.

**AutoOps-Agent** solves this by embedding vector search rules into a multi-agent auditing and healing pipeline that operates autonomously on Terraform code.

---

## 🏗 System Architecture

```mermaid
graph TD
    A[Flawed Terraform Code bad_plan.tf] --> B[Qdrant Vector DB compliance_rules]
    B --> C[SecurityAgent Google ADK]
    B --> D[CostAgent Google ADK]
    C -->|Security Violations| E[PlatformHealerAgent Gemini 2.5 Flash]
    D -->|Budget Violations| E
    E --> F[HCL Syntax Validator validator.py]
    F -->|Validated HCL| G[sample_tf/healed_plan.tf]
    G --> H[GitHub PR Payload JSON]
```

---

## ✨ Features

- **In-Memory Vector Rules Database**: Powered by **Qdrant** (`compliance_rules` collection) for lightning-fast compliance vector search.
- **Multi-Agent Infrastructure Audit**: Uses **Google ADK** (`SecurityAgent` and `CostAgent`) to identify vulnerabilities and budget violations.
- **Lyzr Studio Telemetry**: Lyzr integration wrapper for agent orchestration monitoring.
- **Gemini 2.5 Flash Auto-Healing**: Uses **PlatformHealerAgent** to automatically rewrite non-compliant Terraform HCL into secure, cost-effective HCL code.
- **HCL Syntax Validator**: Ensures matching brace structure and valid HCL blocks prior to output.
- **Interactive CLI Pipeline**: Formatted CLI output powered by `colorama` with simulated GitHub PR payload generation.

---

## ⚙️ Installation & Setup

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/arjunrkj/AutoOps-Agent.git
   cd AutoOps-Agent
   ```

2. **Configure Environment Variables:**
   Copy `.env.example` to `.env` and add your Gemini API key:
   ```bash
   cp .env.example .env
   ```
   *`.env` contents:*
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   LYZR_API_KEY=default_lyzr_key
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

---

## 🎮 Running the Demo

Run the interactive CLI demonstration script:

```bash
python demo.py
```

### 📋 Demo Output Workflow
1. Loads `sample_tf/bad_plan.tf` (exposed in **YELLOW**).
2. Queries **Qdrant Vector DB** for `SEC-01` and `COST-01` compliance rules (exposed in **CYAN**).
3. Executes `SecurityAgent` & `CostAgent` auditing (flaws highlighted in **RED**).
4. Invokes `PlatformHealerAgent` to auto-heal the HCL code.
5. Validates HCL syntax and prints clean code (highlighted in **GREEN**).
6. Saves healed code to `sample_tf/healed_plan.tf`.
7. Outputs simulated **GitHub PR JSON payload** ready to merge!

---

## 📁 Repository Structure

```text
autoops-agent/
├── requirements.txt         # Project dependencies
├── .env.example             # Environment template
├── app/
│   ├── __init__.py          # App package initializer
│   ├── vector_db.py         # Qdrant in-memory vector database
│   ├── agents.py            # Google ADK & Lyzr Multi-Agent definitions
│   └── validator.py         # HCL syntax validation logic
├── sample_tf/
│   ├── bad_plan.tf          # Flawed Terraform plan (Input)
│   └── healed_plan.tf       # Auto-remediated Terraform plan (Output)
├── demo.py                  # Colorful interactive CLI pipeline
└── README.md                # Hackathon project documentation
```

---

## 🤝 Tech Stack & Acknowledgments

- **Google ADK** & **Gemini 2.5 Flash**: Multi-Agent orchestration & AI code remediation.
- **Qdrant**: High-performance vector database for compliance rule indexing.
- **Lyzr Studio**: Agent telemetry and workflow tracking.
- **Colorama**: Interactive CLI terminal styling.
