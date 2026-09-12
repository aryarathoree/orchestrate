import os
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import enum

# --- Enums for strict output compliance ---
class Affordability(enum.Enum):
    NOW = "affordable_now"
    PLAN = "affordable_with_plan"
    LATER = "affordable_later"
    NONE = "not_affordable"

class PaymentMethod(enum.Enum):
    FULL = "full_payment"
    PARTIAL = "partial_payment"
    INSTALLMENTS = "installments"
    WAIT = "wait"
    NOT_REC = "not_recommended"

# --- Services ---

class DataRepository:
    """Handles data loading and relational joins."""
    def __init__(self, data_dir: str):
        self.dir = data_dir
        self.requests = pd.read_csv(f"{self.dir}/requests.csv")
        self.profiles = pd.read_csv(f"{self.dir}/financial_profiles.csv")
        self.events = pd.read_csv(f"{self.dir}/financial_events.csv")
        self.options = pd.read_csv(f"{self.dir}/request_payment_options.csv")
        self.images = pd.read_csv(f"{self.dir}/images.csv")
        self.rates = pd.read_csv(f"{self.dir}/exchange_rates.csv")

    def get_user_profile(self, user_id: str) -> pd.Series:
        return self.profiles[self.profiles['user_id'] == user_id].iloc[0]

    def get_user_events(self, user_id: str) -> pd.DataFrame:
        return self.events[self.events['user_id'] == user_id]

class VisionAgent:
    """Handles extraction of missing financial amounts from images."""
    def extract_amount(self, image_id: str, image_path: str) -> float:
        # TODO: Implement your VLM call here (e.g., OpenAI GPT-4o or Gemini 1.5 Pro).
        # Prompt the VLM to return ONLY a numerical float extracted from the document.
        # For now, returning a safe mock value to prevent zero-errors.
        return 100.0 

class Forecaster:
    """Projects future cashflow and identifies safe spending limits."""
    def __init__(self, repo: DataRepository, vision: VisionAgent):
        self.repo = repo
        self.vision = vision

    def calculate_safe_amount_today(self, current_balance: float, min_balance: float, events: pd.DataFrame, request_date: str) -> float:
        # TODO: Implement discrete-time daily balance simulation.
        # 1. Start with current_balance on request_date.
        # 2. Iterate day-by-day, applying income and deducting pending/recurring expenses.
        # 3. Track the lowest buffer (balance - min_balance) over the period.
        # 4. amount_safe_to_pay = max(0, lowest_buffer)
        
        # Mock logic for structural setup:
        return current_balance - min_balance 

class PolicyEvaluator:
    """Applies conflict-resolution rules to determine the final recommendation."""
    def evaluate(self, request: pd.Series, safe_amount: float, earliest_date: Optional[str]) -> Dict[str, Any]:
        req_amount = request['requested_amount']
        
        if safe_amount >= req_amount:
            return {
                "amount_safe_to_pay": req_amount,
                "affordability_status": Affordability.NOW.value,
                "recommended_payment_method": PaymentMethod.FULL.value,
                "payment_plan": f"{request['request_date']}:{req_amount}",
                "earliest_date_for_full_payment": request['request_date'],
                "spending_changes_needed": "none",
                "decision_explanation": "User has sufficient safe buffer to cover the expense immediately."
            }
            
        # TODO: Implement conditional branches for partial payments, installments, and spending changes.
        # Follow the exact hierarchy defined in the problem statement.
        
        return {
            "amount_safe_to_pay": max(0.0, safe_amount),
            "affordability_status": Affordability.NONE.value,
            "recommended_payment_method": PaymentMethod.NOT_REC.value,
            "payment_plan": "none",
            "earliest_date_for_full_payment": "",
            "spending_changes_needed": "none",
            "decision_explanation": "Insufficient funds to maintain minimum balance without compromising essential expenses."
        }

class AgentOrchestrator:
    """Main pipeline execution."""
    def __init__(self, data_dir: str):
        self.repo = DataRepository(data_dir)
        self.vision = VisionAgent()
        self.forecaster = Forecaster(self.repo, self.vision)
        self.policy = PolicyEvaluator()

    def run(self, output_path: str):
        results = []
        for _, req in self.repo.requests.iterrows():
            profile = self.repo.get_user_profile(req['user_id'])
            events = self.repo.get_user_events(req['user_id'])
            
            # TODO: Detect blank amounts in events and cross-reference self.repo.images
            # image_val = self.vision.extract_amount(image_id, path)
            
            safe_amount = self.forecaster.calculate_safe_amount_today(
                profile['current_balance'], 
                profile['preferred_minimum_balance'], 
                events, 
                req['request_date']
            )
            
            earliest_date = "" # TODO: Calculate via sliding window in forecaster
            
            decision = self.policy.evaluate(req, safe_amount, earliest_date)
            decision['request_id'] = req['request_id']
            results.append(decision)

        # Ensure exact column order
        columns = [
            "request_id", "amount_safe_to_pay", "affordability_status", 
            "recommended_payment_method", "payment_plan", 
            "earliest_date_for_full_payment", "spending_changes_needed", 
            "decision_explanation"
        ]
        pd.DataFrame(results)[columns].to_csv(output_path, index=False)

if __name__ == "__main__":
    orchestrator = AgentOrchestrator(data_dir="dataset")
    orchestrator.run(output_path="output.csv")
    print("Execution complete. Predictions saved to output.csv.")
