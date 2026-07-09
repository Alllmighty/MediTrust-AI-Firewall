import json
from pathlib import Path
from src.firewall import MediTrustAssurance
from src.logger import SecurityLogger

def main() -> None:
    print("🛡️Starting MediTrust AI Security Interface (Production Simulation)...\n")

    firewall = MediTrustAssurance()
    logger = SecurityLogger()

    # Load cases dynamically from the unified test_cases.json
    cases_path = Path(__file__).resolve().parent / "tests" / "test_cases.json"
    with open(cases_path, 'r', encoding='utf-8') as f:
        test_cases = json.load(f)

    for i, case in enumerate(test_cases, 1):
        condition = case["condition"]
        response = case["ai_response"]

        print(f"[INPUT {i:02}] Condition: '{condition}' | AI: '{response}'")

        verdict_json = firewall.verify_with_ai(condition, response)

        try:
            data = json.loads(verdict_json)
            action = data.get("suggested_action", "Unknown")
            risk = data.get("risk_level", "Unknown")

            log_entry = f"Condition: {condition} | Risk: {risk} | Action: {action}"

            if risk in ["RED", "YELLOW"]:
                logger.log_threat("Semantic Risk Detected", log_entry)
                print(f"❌ VERDICT: BLOCKED (Risk: {risk})\n")
            else:
                logger.log_safe(log_entry)
                print(f"✅ VERDICT: ALLOWED (Risk: {risk})\n")

        except json.JSONDecodeError:
            print("⚠️ System Error: Failed to parse Judge response.\n")
            logger.log_threat("Parse Error",f"Condition: {condition}")

if __name__ == "__main__":
    main()