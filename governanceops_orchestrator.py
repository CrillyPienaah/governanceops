"""
GovernanceOps - Automated AI Model Promotion Pipeline
Christopher Crilly Pienaah | 2026

Category: GovernanceOps
Positioning:
  DevOps governs software delivery.
  MLOps governs model delivery.
  GovernanceOps governs AI deployment.

Flow:
  New model registered
      |
  GovernanceOps reads model card + metrics
      |
  Creates governance evaluation run
      |
  Calls Governance Control Tower
      |
  Generates audit evidence package
      |
  Writes promotion decision: APPROVED / CONDITIONAL / BLOCKED

Antigravity-compatible: this pipeline is designed to be orchestrated
by Antigravity or any ADK-compatible agent runtime. The core logic
is pure Python -- portable across any infrastructure.
"""

import json
import yaml
import asyncio
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)

GOVERNANCE_THRESHOLDS = {
    "air_min": 0.80,
    "psi_max": 0.20,
    "psi_warning": 0.10,
    "hallucination_max": 0.10,
    "auc_min": 0.70,
    "ece_max": 0.05,
    "tpr_gap_max": 0.10,
}

REGISTRY_PATH = Path("registry")
OUTPUTS_PATH = Path("outputs")


class ModelRegistryReader:
    def __init__(self, registry_path: Path = REGISTRY_PATH):
        self.registry_path = registry_path

    def list_models(self):
        return [d.name for d in self.registry_path.iterdir() if d.is_dir()]

    def read_model_card(self, model_id: str) -> Dict[str, Any]:
        path = self.registry_path / model_id / "model_card.yaml"
        if not path.exists():
            raise FileNotFoundError(f"No model card found for {model_id}")
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f)

    def read_metrics(self, model_id: str) -> Dict[str, Any]:
        path = self.registry_path / model_id / "metrics.json"
        if not path.exists():
            raise FileNotFoundError(f"No metrics found for {model_id}")
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    def model_exists(self, model_id: str) -> bool:
        return (self.registry_path / model_id).exists()


def evaluate_guardrails(metrics: Dict, model_card: Dict) -> Dict[str, Any]:
    failures = []
    warnings = []
    passed = []
    m = metrics
    doc = model_card.get("documentation", {})

    air = m["fairness"]["air"]
    if air < GOVERNANCE_THRESHOLDS["air_min"]:
        failures.append({"rule": "FAIRNESS_AIR", "severity": "CRITICAL",
            "message": f"AIR {air:.3f} below minimum {GOVERNANCE_THRESHOLDS['air_min']}",
            "osfi_reference": "OSFI E-23 Section 6.2",
            "remediation": "Retrain with fairness constraints or apply post-processing calibration"})
    else:
        passed.append(f"Fairness AIR: {air:.3f} PASS")

    tpr_gap = m["fairness"]["tpr_gap"]
    if tpr_gap > GOVERNANCE_THRESHOLDS["tpr_gap_max"]:
        failures.append({"rule": "FAIRNESS_EQUAL_OPPORTUNITY", "severity": "HIGH",
            "message": f"TPR gap {tpr_gap:.3f} exceeds maximum {GOVERNANCE_THRESHOLDS['tpr_gap_max']}",
            "osfi_reference": "OSFI E-23 Section 6.2",
            "remediation": "Apply equalized odds post-processing"})
    else:
        passed.append(f"Equal Opportunity TPR gap: {tpr_gap:.3f} PASS")

    psi = m["drift"]["psi"]
    if psi > GOVERNANCE_THRESHOLDS["psi_max"]:
        failures.append({"rule": "DRIFT_PSI_CRITICAL", "severity": "CRITICAL",
            "message": f"PSI {psi:.3f} indicates significant distribution shift",
            "osfi_reference": "OSFI E-23 Section 5.1",
            "remediation": "Immediate model retraining required"})
    elif psi > GOVERNANCE_THRESHOLDS["psi_warning"]:
        warnings.append({"rule": "DRIFT_PSI_WARNING",
            "message": f"PSI {psi:.3f} moderate drift -- monitor closely"})
    else:
        passed.append(f"Drift PSI: {psi:.3f} PASS")

    auc = m["performance"]["auc"]
    if auc < GOVERNANCE_THRESHOLDS["auc_min"]:
        failures.append({"rule": "PERFORMANCE_AUC", "severity": "HIGH",
            "message": f"AUC {auc:.3f} below minimum {GOVERNANCE_THRESHOLDS['auc_min']}",
            "osfi_reference": "OSFI E-23 Section 4.2",
            "remediation": "Improve model or replace"})
    else:
        passed.append(f"Performance AUC: {auc:.3f} PASS")

    hal = m["reliability"]["hallucination_risk"]
    if hal > GOVERNANCE_THRESHOLDS["hallucination_max"]:
        failures.append({"rule": "RELIABILITY_HALLUCINATION", "severity": "CRITICAL",
            "message": f"Hallucination risk {hal:.3f} exceeds maximum",
            "osfi_reference": "OSFI E-23 Section 7.1",
            "remediation": "Implement RAG with citation validation"})
    else:
        passed.append(f"Hallucination Risk: {hal:.3f} PASS")

    if not doc.get("fairness_testing"):
        failures.append({"rule": "DOC_FAIRNESS", "severity": "HIGH",
            "message": "Fairness testing not documented",
            "osfi_reference": "OSFI E-23 Section 6.2",
            "remediation": "Add fairness testing documentation to model card"})
    else:
        passed.append("Fairness testing documented PASS")

    if not doc.get("drift_monitoring"):
        failures.append({"rule": "DOC_DRIFT_MONITORING", "severity": "HIGH",
            "message": "Drift monitoring not configured",
            "osfi_reference": "OSFI E-23 Section 5.1",
            "remediation": "Configure PSI/CSI monitoring before deployment"})
    else:
        passed.append("Drift monitoring configured PASS")

    if not doc.get("independent_validation"):
        failures.append({"rule": "DOC_INDEPENDENT_VALIDATION", "severity": "HIGH",
            "message": "Independent validation not completed",
            "osfi_reference": "OSFI E-23 Section 4.3",
            "remediation": "Complete independent model validation"})
    else:
        passed.append("Independent validation completed PASS")

    if not doc.get("audit_trail"):
        failures.append({"rule": "DOC_AUDIT_TRAIL", "severity": "HIGH",
            "message": "Audit trail not generated",
            "osfi_reference": "OSFI E-23 Section 8.1",
            "remediation": "Generate complete audit trail"})
    else:
        passed.append("Audit trail generated PASS")

    critical = [f for f in failures if f["severity"] == "CRITICAL"]
    status = "BLOCKED" if failures else ("CONDITIONAL" if warnings else "APPROVED")

    return {
        "status": status,
        "summary": {
            "total_rules": len(failures) + len(warnings) + len(passed),
            "passed": len(passed),
            "warnings": len(warnings),
            "failures": len(failures),
            "critical_failures": len(critical),
        },
        "failures": failures,
        "warnings": warnings,
        "passed_rules": passed,
        "llm_override_possible": False,
    }


class AuditPackageGenerator:

    def generate(self, model_card, metrics, guardrail_result, promotion_decision):
        model_id = model_card["model_id"]
        model_name = model_card["model_name"]
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

        def pf(condition):
            return "PASS" if condition else "FAIL"

        lines = [
            f"# GovernanceOps Audit Evidence Package",
            f"**Model:** {model_name} (`{model_id}`)",
            f"**Generated:** {timestamp}",
            f"**Regulatory Framework:** {model_card.get('regulatory_framework', 'OSFI E-23')}",
            f"**Generated by:** GovernanceOps Automated Pipeline",
            f"",
            f"---",
            f"",
            f"## Promotion Decision: {promotion_decision}",
            f"",
            f"---",
            f"",
            f"## Model Card Summary",
            f"",
            f"| Field | Value |",
            f"|---|---|",
            f"| Model ID | `{model_id}` |",
            f"| Model Type | {model_card.get('model_type', 'N/A')} |",
            f"| Use Case | {model_card.get('use_case', 'N/A')} |",
            f"| Risk Tier | {model_card.get('risk_tier', 'N/A')} |",
            f"| Owner | {model_card.get('owner', 'N/A')} |",
            f"| Created | {model_card.get('created_date', 'N/A')} |",
            f"",
            f"---",
            f"",
            f"## Metrics Summary",
            f"",
            f"| Metric | Value | Threshold | Status |",
            f"|---|---|---|---|",
            f"| AUC | {metrics['performance']['auc']} | >= 0.70 | {pf(metrics['performance']['auc'] >= 0.70)} |",
            f"| AIR | {metrics['fairness']['air']} | >= 0.80 | {pf(metrics['fairness']['air'] >= 0.80)} |",
            f"| PSI | {metrics['drift']['psi']} | < 0.20 | {pf(metrics['drift']['psi'] < 0.20)} |",
            f"| TPR Gap | {metrics['fairness']['tpr_gap']} | < 0.10 | {pf(metrics['fairness']['tpr_gap'] < 0.10)} |",
            f"| ECE | {metrics['performance']['ece']} | < 0.05 | {pf(metrics['performance']['ece'] < 0.05)} |",
            f"| Hallucination Risk | {metrics['reliability']['hallucination_risk']} | < 0.10 | {pf(metrics['reliability']['hallucination_risk'] < 0.10)} |",
            f"",
            f"---",
            f"",
            f"## Guardrail Evaluation",
            f"",
            f"- Rules evaluated: {guardrail_result['summary']['total_rules']}",
            f"- Passed: {guardrail_result['summary']['passed']}",
            f"- Warnings: {guardrail_result['summary']['warnings']}",
            f"- Failures: {guardrail_result['summary']['failures']} ({guardrail_result['summary']['critical_failures']} critical)",
            f"- LLM override possible: {guardrail_result['llm_override_possible']}",
            f"",
        ]

        if guardrail_result["failures"]:
            lines += ["### Failures", ""]
            for f in guardrail_result["failures"]:
                lines += [
                    f"**[{f['severity']}] {f['rule']}**",
                    f"- {f['message']}",
                    f"- OSFI Reference: {f['osfi_reference']}",
                    f"- Remediation: {f['remediation']}",
                    f"",
                ]

        if guardrail_result["warnings"]:
            lines += ["### Warnings", ""]
            for w in guardrail_result["warnings"]:
                lines += [f"- [{w['rule']}] {w['message']}", ""]

        lines += ["### Passed Rules", ""]
        for p in guardrail_result["passed_rules"]:
            lines.append(f"- {p}")

        lines += [
            f"",
            f"---",
            f"",
            f"## Audit Trail",
            f"",
            f"- Pipeline: GovernanceOps Automated Promotion Pipeline v1.0",
            f"- Timestamp: {timestamp}",
            f"- Rules engine: Deterministic Python -- no LLM involvement in final decision",
            f"- Artifacts read: model_card.yaml, metrics.json",
            f"- Output: {model_id}_audit_package.md",
            f"",
            f"---",
            f"",
            f"*Generated by GovernanceOps | github.com/CrillyPienaah/governanceops*",
        ]

        return "\n".join(lines)


class GovernanceOpsOrchestrator:

    def __init__(self):
        self.registry = ModelRegistryReader()
        self.audit_generator = AuditPackageGenerator()
        OUTPUTS_PATH.mkdir(exist_ok=True)

    async def promote(self, model_id: str) -> Dict[str, Any]:
        print(f"\n{'='*65}")
        print(f"  GOVERNANCEOPS -- MODEL PROMOTION PIPELINE")
        print(f"  Model: {model_id}")
        print(f"  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
        print(f"{'='*65}")

        if not self.registry.model_exists(model_id):
            raise ValueError(f"Model {model_id} not found in registry")

        logger.info("[1/4] Reading model artifacts from registry")
        model_card = self.registry.read_model_card(model_id)
        metrics = self.registry.read_metrics(model_id)
        print(f"\n  [1/4] Model card and metrics loaded")
        print(f"        Model: {model_card['model_name']}")
        print(f"        Risk tier: {model_card['risk_tier']}")

        logger.info("[2/4] Running deterministic guardrail evaluation")
        guardrail_result = evaluate_guardrails(metrics, model_card)
        status = guardrail_result["status"]
        print(f"\n  [2/4] Guardrail evaluation complete")
        print(f"        Rules evaluated: {guardrail_result['summary']['total_rules']}")
        print(f"        Passed: {guardrail_result['summary']['passed']}")
        print(f"        Failures: {guardrail_result['summary']['failures']} ({guardrail_result['summary']['critical_failures']} critical)")

        logger.info("[3/4] Generating audit evidence package")
        audit_package = self.audit_generator.generate(
            model_card, metrics, guardrail_result, status
        )
        output_path = OUTPUTS_PATH / f"{model_id}_audit_package.md"
        output_path.write_text(audit_package, encoding="utf-8")
        print(f"\n  [3/4] Audit package generated")
        print(f"        Saved: {output_path}")

        logger.info("[4/4] Writing promotion decision")
        promotion_decision = {
            "model_id": model_id,
            "model_name": model_card["model_name"],
            "promotion_status": status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "guardrail_summary": guardrail_result["summary"],
            "failures": guardrail_result["failures"],
            "warnings": guardrail_result["warnings"],
            "audit_package_path": str(output_path),
            "llm_override_possible": False,
            "pipeline": "GovernanceOps Automated Promotion Pipeline v1.0",
        }

        decision_path = OUTPUTS_PATH / f"{model_id}_promotion_decision.json"
        decision_path.write_text(json.dumps(promotion_decision, indent=2), encoding="utf-8")

        print(f"\n  [4/4] Promotion decision written")
        print(f"        Saved: {decision_path}")
        print(f"\n  {'-'*65}")
        print(f"  PROMOTION DECISION: {status}")

        if guardrail_result["failures"]:
            print(f"\n  FAILURES:")
            for f in guardrail_result["failures"]:
                print(f"  [FAIL] [{f['severity']}] {f['rule']}: {f['message']}")

        print(f"  {'-'*65}\n")
        return promotion_decision


async def run_demo():
    orchestrator = GovernanceOpsOrchestrator()

    print("\n" + "="*65)
    print("  GOVERNANCEOPS")
    print("  Automated AI Model Promotion Pipeline")
    print("  DevOps governs software. MLOps governs models.")
    print("  GovernanceOps governs AI deployment.")
    print("="*65)

    models = orchestrator.registry.list_models()
    print(f"\n  Models in registry: {models}\n")

    for model_id in models:
        result = await orchestrator.promote(model_id)

    print("="*65)
    print("  GOVERNANCEOPS PIPELINE COMPLETE")
    print("  Audit packages saved to outputs/")
    print("="*65 + "\n")


if __name__ == "__main__":
    asyncio.run(run_demo())
