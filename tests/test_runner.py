import sys
import json
import warnings
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

warnings.filterwarnings("ignore", category=UserWarning, module="groq")

# Setting up import paths
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

try:
    from src.firewall import MediTrustAssurance
except ImportError:
    print("❌ Error: Failed to import MediTrustAssurance. Check the folder structure.")

def load_test_cases(filepath: Path) -> List[Dict[str, Any]]:
    """
    Loads JSON test cases for LLM Observability Pipeline.
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def run_tests() -> None:
    """
    Executes the automated test suite against the MediTrust AI Firewall.
    Validates semantic routing, risk detection, and response logic.
    """
    firewall = MediTrustAssurance()

    current_dir = Path(__file__).resolve().parent
    test_cases_path = current_dir / 'test_cases.json'
    report_path = current_dir / 'test_report.md'

    cases = load_test_cases(test_cases_path)
    results = []
    stats = {"PASSED": 0, "FAILED": 0, "TOTAL": len(cases)}

    print(f"🚀 Starting MediTrust-AI-Firewall CI/CD Runner. Total cases: {len(cases)}\n")

    for case in cases:
        print(f"Evaluating {case['id']} [{case['category']}]...")

        try:
            judge_output = firewall.verify_with_ai(
                case['patient_id'],
                case['history'],
                case['condition'],
                case['ai_response']
            )

            # Extracting JSON if wrapped in markdown or raw text
            if isinstance(judge_output, str):
                start_idx = judge_output.find('{')
                end_idx = judge_output.rfind('}') + 1
                judge_data = json.loads(judge_output[start_idx:end_idx])
            else:
                judge_data = judge_output

            actual_action = judge_data.get("suggested_action", "Unknown").strip()
            actual_risk = judge_data.get("risk_level", "Unknown")
            reasoning = judge_data.get("reasoning", "No reasoning provided.")

            is_passed = (actual_action.lower() == case['expected_action'].strip().lower())
            status = "PASSED" if is_passed else "FAILED"
            stats[status] += 1

            results.append({
                "id": case['id'],
                "category": case['category'],
                "patient_id": case['patient_id'],
                "history": case['history'],
                "condition": case['condition'],
                "ai_response": case['ai_response'],
                "expected": case['expected_action'],
                "actual": actual_action,
                "risk_level": actual_risk,
                "status": status,
                "reasoning": reasoning
            })

        except Exception as e:
            print(f"❌ Execution error on {case.get('id', 'Unknown')}: {e}")
            stats["FAILED"] += 1
            results.append({
                "id": case.get('id', 'N/A'),
                "category": case.get('category', 'N/A'),
                "patient_id": case.get('patient_id', 'N/A'),
                "history": case.get('history', 'N/A'),
                "condition": case.get('condition', 'N/A'),
                "ai_response": case.get('ai_response', 'N/A'),
                "expected": case.get('expected_action', 'Block'),
                "actual": "ERROR",
                "risk_level": "ERROR",
                "status": "FAILED",
                "reasoning": f"System Exception: {str(e)}"
            })

    generate_markdown_report(report_path, stats, results)
    print(f"\n📊 CI/CD Pipeline completed. Passed: {stats['PASSED']}, Failed: {stats['FAILED']}")

    sys.exit(1 if stats["FAILED"] > 0 else 0)

def generate_markdown_report(filepath: Path, stats: Dict[str, int], results: List[Dict[str, Any]]) -> None:
    """
    Generates an automated Markdown audit report for GitHub viewing.
    """
    pass_rate = (stats["PASSED"] / stats["TOTAL"]) * 100 if stats["TOTAL"] > 0 else 0

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"# 🛡️ MediTrust-AI-Firewall / LLM Observability Report\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (UTC)\n")
        f.write(f"**Audit Strategy:** Strict Binary Decision (Block/Allow)\n\n")

        f.write(f"## 📊 Pipeline Statistics\n")
        f.write(f"| Total Cases | Passed | Failed | Pass Rate |\n| :--- | :--- | :--- | :--- |\n")
        f.write(f"| {stats['TOTAL']} | ✅ {stats['PASSED']} | ❌ {stats['FAILED']} | {pass_rate:.1f}% |\n")

        f.write(f"## 📝 Semantic Audit Results\n")
        f.write(f"| ID | Category | Patient ID | Condition | Expected | Actual | Risk | Status |\n")
        f.write(f"| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n")

        for r in results:
            status_emoji = "✅" if r["status"] == "PASSED" else "❌"
            f.write(f"| {r['id']} | {r['category']} | `{r['patient_id']}` | `{r['condition']}` | **{r['expected']}** | **{r['actual']}** | `{r['risk_level']}` | {status_emoji} {r['status']} |\n")

        f.write(f"\n## 🧠 Judge LLM Reasoning (Trace Logs)\n")
        for r in results:
            icon = "❌" if r["status"] == "FAILED" or r["risk_level"] == "ERROR" else "✅"
            f.write(f"### {icon} {r['id']} - {r['category']}\n")
            f.write(f"**Audit Context:**\n")
            f.write(f"> **Pateint ID:** `{r['patient_id']}`\n>\n")
            f.write(f"> **History Context:** *{r['history']}*\n>\n")
            f.write(f"> **Input Condition:** `{r['condition']}`\n>\n")
            f.write(f"> **Evaluated AI Output:** *{r['ai_response']}*\n\n")
            f.write(f"**Security Guardrail Reasoning:**\n```text\n{r['reasoning']}\n```\n\n")

if __name__ == "__main__":
    run_tests()