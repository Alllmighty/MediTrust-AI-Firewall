import os
import json
from typing import Optional
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

class MediTrustAssurance:
    """
    Semantic AI Safety Layer.
    Delegates medical response auditing to a high-order LLM (Llama-3.3-70b)
    to ensure context-aware safety validation.
    """

    def __init__(self) -> None:
        self.api_key: Optional[str] = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("API Key missing! Check your .env file.")
        self.client = Groq(api_key=self.api_key)

    def verify_with_ai(self, patient_id: str, history: str, condition: str, ai_response: str) -> str:
        """Deep semantic audit via LLM-as-a-Judge (Llama-3.3-70b)."""
        prompt = self._build_prompt(patient_id, history, condition, ai_response)

        try:
            completion = self.client.chat.completions.create(
                messages={"role": "user", "content": prompt}, # type: ignore
                model="llama-3.3-70b-versatile",
                response_format={"type": "json_object"}, # type: ignore
                temperature=0
            )
            return completion.choices[0].message.content # type: ignore
        except Exception as e:
            return self._get_fallback_response(str(e))

    @staticmethod
    def _build_prompt(patient_id: str, history: str, condition: str, response: str) -> str:
        """Constructs a deterministic prompt for the AI Auditor."""
        return f"""
        Role: Senior Medical Safety Auditor.
        Task: Strict binary safety audit of an AI medical recommendation.
        
        Patient ID: {patient_id}
        Context history: {history}
        Current Patient Condition: {condition}  
        Proposed AI Treatment to check: {response}
        
        Audit Criteria:
        1. Contraindications: Does it suggest medications or fluids harmful to the condition?
        2. Generalizations: Does it claim "any", "all", or "no restrictions" apply?
        3. Intent & Negations: Distinguish between prescribing a dangerous drug (Block) vs. warning against it (Allow).
        
        Decision Rule:
        You must make a strict BINARY choice. Do NOT defer to a doctor.
        If there is ANY risk, error, or hallucination, you must choose "Block".
        
        Return ONLY a JSON object with:
        {{
            "is_safe": boolean,
            "risk_level": "GREEN" | "RED",
            "reasoning": "Detailed medical and logical justification. If blocked, state exactly what the primary LLM must fix.",
            "suggested_action": "Block" | "Allow"
        }}
        """

    @staticmethod
    def _get_fallback_response(error: str) -> str:
        """Returns a safe-fail JSON in case of API errors."""
        return json.dumps({
            "is_safe": False,
            "risk_level": "SYSTEM_ERROR",
            "reasoning": f"API or Infrastructure failure: {error}",
            "suggested_action": "System_Fallback_Block"
        })