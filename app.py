import json
from pathlib import Path
from src.firewall import MediTrustAssurance
from src.logger import SecurityLogger

def main() -> None:
    print("🛡️ Starting MediTrust AI Security Interface [Agentic Reflection Mode]...\n")

    firewall = MediTrustAssurance()
    logger = SecurityLogger()

    # Load cases dynamically from the unified test_cases.json
    cases_path = Path(__file__).resolve().parent / "tests" / "test_cases.json"
    try:
        with open(cases_path, 'r', encoding='utf-8') as f:
            test_cases = json.load(f)
    except FileNotFoundError:
        print("🚨 Critical Error: tests/test_cases.json not found!\n")
        return

    for i, case in enumerate(test_cases, 1):
        patient_id = case.get('patient_id', f'P-GEN-{i}')
        history = case.get('history', 'No prior history.')
        condition = case.get('condition', 'unknown')
        initial_response = case.get('ai_response', '')

        print(f"==================================================")
        print(f"[CASE {i:02}] Patient: {patient_id} | Condition: '{condition}'")
        print(f"==================================================")

        max_retries = 3
        attempt = 1
        current_response = initial_response
        is_fully_blocked = True

        # Agentic Reflection Loop
        while attempt <= max_retries:
            print(f"[Attempt {attempt}/{max_retries}] Proposed AI Treatment: '{current_response}'")

            verdict_json = firewall.verify_with_ai(patient_id, history, condition, current_response)

            try:
                if isinstance(verdict_json, str):
                    start_idx = verdict_json.find('{')
                    end_idx = verdict_json.rfind('}') + 1
                    data = json.loads(verdict_json[start_idx:end_idx])
                else:
                    data = verdict_json

                if not isinstance(data, dict):
                    data = {}

                action = data.get("suggested_action", "Block").strip()
                risk = data.get("risk_level", "RED")
                reasoning = data.get("reasoning", "No reasoning provided.")

                log_entry = f"Case: {i:02} | Patient: {patient_id} | Condition: {condition} | Risk: {risk} | Action: {action} | Attempt: {attempt}"

                if action.lower() == "allow":
                    print(f"✅ APPROVED by Judge. Ready for Doctor Review.")
                    print(f"History context saved for Patient {patient_id}.")
                    logger.log_safe(log_entry)
                    is_fully_blocked = False
                    break

                else:
                    print(f"❌ BLOCKED by Judge. Reason: {reasoning}")
                    logger.log_threat(f"Semantic Threat Detected", log_entry)

                    if attempt < max_retries:
                        print(f"🔄 Sending feedback back to Primary LLM to regenerate response...")
                        # In real system, there would be a call to the primary LLM with the prompt:
                        # "Your previous answer was blocked. Reason: {data['reasoning']}. Fix it."
                        # To simulate, we break the loop:
                        current_response = "Simulated corrected response based on Judge feedback."
                        print(f"✨ Primary LLM generated alternative response.")
                    else:
                        print(f"🚨 CRITICAL: Response could not be sanitized after {max_retries} attempts. Post-processing failure.\n")

            except (json.JSONDecodeError, ValueError) as e:
                print(f"⚠️ System Parse Error: Failed to Parse Judge response on attempt {attempt}. Error: {e}\n")
                logger.log_threat("Parser error inside App Loop", f"Patient: {patient_id} | Error: {str(e)}")

                if attempt < max_retries:
                    current_response = "[Simulated Emergence Fallback Response] Please consult a human doctor immediately."

            attempt += 1

        if is_fully_blocked:
            print(f"🛑 FINAL VERDICT FOR CASE {i:02}: HARD BLOCKED. Context isolated.\n")
        else:
            print(f"🟢 FINAL VERDICT FOR CASE {i:02}: PASSED TO PRODUCTION.\n")

    print("🛡️ Simulation completed. Security logs successfully compiled.")

if __name__ == "__main__":
    main()