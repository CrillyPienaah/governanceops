# GovernanceOps
### Automated AI Model Promotion Pipeline

> **DevOps governs software delivery. MLOps governs model delivery. GovernanceOps governs AI deployment.**

GovernanceOps introduces governance as a deployment gate rather than a post-deployment review activity.

[![Category](https://img.shields.io/badge/Category-GovernanceOps%20Platform-blue)](https://github.com/CrillyPienaah/governanceops)
[![Regulatory](https://img.shields.io/badge/Regulatory-OSFI%20E--23-red)](https://www.osfi-bsif.gc.ca)
[![Stack](https://img.shields.io/badge/Stack-Python%20%7C%20ADK%20Compatible-green)](https://github.com/CrillyPienaah/governanceops)

---

## The Problem

Most organizations ask: *"How accurate is the model?"*

GovernanceOps asks: *"Should the model be deployed?"*

These are different questions with different consequences. A model can achieve excellent predictive performance and still fail fairness requirements, exhibit population drift, lack monitoring controls, or violate governance documentation standards. Those failures are typically discovered after deployment — during a regulatory examination, not before.

GovernanceOps moves the discovery point to before deployment. GovernanceOps transforms AI governance from a periodic review activity into a continuous deployment control.

### Three Promotion Outcomes

| Decision | Meaning |
|---|---|
| **APPROVED** | All governance rules passed. Model eligible for production. |
| **CONDITIONAL** | Minor gaps present. Remediation required within 30 days. Human review required. |
| **BLOCKED** | Critical fairness or drift failures. Model cannot proceed to production. |

---

## What It Does

Drop a model card and metrics into the registry. GovernanceOps automatically:

1. Reads the model card and metrics from the registry
2. Evaluates governance rules — fairness, drift, performance, reliability, documentation
3. Generates a structured audit evidence package
4. Writes a promotion decision: **APPROVED / CONDITIONAL / BLOCKED**

Human review is reserved for CONDITIONAL or high-risk cases. LLMs may assist with evidence collection and analysis, but promotion decisions are determined exclusively by deterministic governance rules.

---

## Enterprise Benefits

- Reduces governance review cycle times by automating standard model evaluations
- Creates repeatable, examiner-ready audit evidence for every promotion decision
- Prevents non-compliant models from reaching production before issues are discovered
- Standardizes promotion decisions across teams, models, and regulatory domains
- Supports regulatory examinations with immutable audit artifacts

---

## The Key Finding

```
Model: Fraud Detection Model v1

Performance:  AUC = 0.969   (Excellent)
Fairness:     AIR = 0.59    BLOCKED -- below 0.80 minimum
Drift:        PSI = 0.25    BLOCKED -- above 0.20 threshold

PROMOTION DECISION: BLOCKED

7 failures. 2 critical. Model cannot proceed to production.
```

Compare with a well-governed credit model (AUC 0.847, AIR 0.91, PSI 0.08) that receives **APPROVED** across all 9 governance rules.

Accuracy alone is not governance.

---

## Architecture

```
Model Registry
    |
    | model_card.yaml + metrics.json
    v
GovernanceOps Orchestrator
    |
    |-- [1/4] Read model artifacts
    |-- [2/4] Evaluate deterministic guardrails
    |-- [3/4] Generate audit evidence package
    |-- [4/4] Write promotion decision
    v
outputs/
    |-- {model_id}_audit_package.md
    |-- {model_id}_promotion_decision.json
```

---

## Governance Rules

Nine rules evaluated on every model. Any failure blocks promotion.

| Rule | Threshold | Severity |
|---|---|---|
| Fairness AIR | >= 0.80 | CRITICAL |
| Equal Opportunity TPR Gap | < 0.10 | HIGH |
| Drift PSI | < 0.20 | CRITICAL |
| Performance AUC | >= 0.70 | HIGH |
| Hallucination Risk | < 0.10 | CRITICAL |
| Fairness Testing Documented | Required | HIGH |
| Drift Monitoring Configured | Required | HIGH |
| Independent Validation | Required | HIGH |
| Audit Trail Generated | Required | HIGH |

Thresholds are enterprise governance values aligned with model risk management best practices and informed by fairness literature. The 0.80 AIR threshold reflects the widely-used 4/5ths rule.

**LLM override possible: False.** Every rule is a Python `if` statement.

---

## Registry Structure

```
governanceops/
├── governanceops_orchestrator.py   # Core pipeline
├── requirements.txt
├── registry/
│   ├── fraud_model_v1/
│   │   ├── model_card.yaml         # Model metadata + documentation flags
│   │   └── metrics.json            # Performance, fairness, drift, reliability
│   └── credit_model_v3/
│       ├── model_card.yaml
│       └── metrics.json
└── outputs/                        # Generated audit packages (gitignored)
    ├── fraud_model_v1_audit_package.md
    ├── fraud_model_v1_promotion_decision.json
    ├── credit_model_v3_audit_package.md
    └── credit_model_v3_promotion_decision.json
```

---

## Quick Start

```bash
git clone https://github.com/CrillyPienaah/governanceops
cd governanceops
pip install pyyaml
python governanceops_orchestrator.py
```

Expected output:

```
=================================================================
  GOVERNANCEOPS
  Automated AI Model Promotion Pipeline
  DevOps governs software. MLOps governs models.
  GovernanceOps governs AI deployment.
=================================================================

  Models in registry: ['credit_model_v3', 'fraud_model_v1']

  PROMOTION DECISION: APPROVED   (credit_model_v3 -- 9/9 rules passed)
  PROMOTION DECISION: BLOCKED    (fraud_model_v1  -- 7 failures, 2 critical)
```

---

## Adding a New Model

Create a folder in `registry/` with two files:

**model_card.yaml**
```yaml
model_id: your_model_id
model_name: "Your Model Name"
model_type: credit_risk
use_case: retail_credit_adjudication
owner: "team@organization.com"
documentation:
  fairness_testing: true
  drift_monitoring: true
  independent_validation: true
  osfi_e23_mapping: true
  audit_trail: true
regulatory_framework: OSFI E-23
risk_tier: LOW
```

**metrics.json**
```json
{
  "model_id": "your_model_id",
  "performance": {"auc": 0.85, "ks_statistic": 0.60, "ece": 0.02},
  "fairness": {"air": 0.88, "demographic_parity": 0.91, "equal_opportunity": 0.87, "tpr_gap": 0.07},
  "drift": {"psi": 0.06, "csi": 0.04},
  "reliability": {"hallucination_risk": 0.04, "grounding_score": 0.93, "citation_coverage": 0.90}
}
```

Run `python governanceops_orchestrator.py` — the pipeline picks it up automatically.

---

## Antigravity Compatible

GovernanceOps is designed to be orchestrated by Antigravity or any ADK-compatible agent runtime. The `GovernanceOpsOrchestrator` class exposes a single `await orchestrator.promote(model_id)` interface that any agent can call as a tool.

To connect Antigravity: point it at `governanceops_orchestrator.py` and prompt:

```
Evaluate all models in the registry and generate governance promotion decisions.
```

---

## Roadmap

- Policy-as-Code governance engine — define governance rules as versioned YAML policies, not hardcoded Python
- MLflow integration — replace mock registry with real MLflow API
- Hugging Face model card ingestion
- GitHub Actions deployment gate — block PRs that fail governance
- Human-in-the-loop workflow for CONDITIONAL decisions
- FastAPI REST endpoint for enterprise integration
- Expanded regulatory frameworks beyond OSFI E-23

---

## Relationship to Governance Control Tower

GovernanceOps is the deployment gate layer above the
[Enterprise AI Governance Control Tower](https://github.com/CrillyPienaah/governance-control-tower).

| Layer | System | Role |
|---|---|---|
| Layer 4 | GovernanceOps | Automated promotion pipeline |
| Layer 3 | Governance Control Tower | Multi-agent governance orchestration |
| Layer 2 | Five live governance systems | Specialist agents |
| Layer 1 | CanFraudBench / CanFinBench | Published benchmarks |

---

## Author

**Christopher Crilly Pienaah**
AI / ML Engineer | AI Governance | Model Risk Management
[chris-pienaah-portfolio.vercel.app](https://chris-pienaah-portfolio.vercel.app)
[github.com/CrillyPienaah](https://github.com/CrillyPienaah)

---

*Designed for regulated AI environments and adaptable to enterprise governance frameworks including OSFI E-23, GDPR, EU AI Act, NIST AI RMF, SR 11-7, and FINTRAC.*
