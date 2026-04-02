"""
GigShield Premium Calculator
Converts risk score to weekly premium with breakdown
Author: Member 1
"""

from datetime import datetime, timedelta

class WeeklyPremiumCalculator:
    """
    Calculates weekly premium based on risk score
    Premium range: ₹49-₹99 (matches Phase 1 slide)
    """
    
    def __init__(self):
        self.min_premium = 49
        self.max_premium = 99
        self.base_percentage = 0.02  # 2% of weekly income
    
    def calculate(self, worker_data, risk_prediction):
        """
        Calculate weekly premium with full breakdown
        
        Input:
        worker_data = {'avg_daily_income': 500, 'experience_days': 60, 'city': 'Mumbai'}
        risk_prediction = {'risk_score': 72.5, 'risk_band': 'High'}
        
        Output:
        {
            'weekly_premium': 86,
            'breakdown': {...},
            'coverage_amount': 2800
        }
        """
        
        weekly_income = worker_data.get('avg_daily_income', 500) * 7
        risk_score = risk_prediction.get('risk_score', 50)
        
        # STEP 1: Base premium (2% of weekly income)
        base_premium = weekly_income * self.base_percentage
        
        # STEP 2: Risk loading (adds 0-3% based on risk score)
        risk_loading_pct = (risk_score / 100) * 0.03
        risk_loading = weekly_income * risk_loading_pct
        
        # STEP 3: Location adjustment (±10%)
        location_adjustment = 0
        location_note = ""
        
        high_risk_cities = ['Mumbai', 'Chennai', 'Kolkata']
        low_risk_cities = ['Pune', 'Ahmedabad', 'Jaipur']
        
        if worker_data.get('city') in high_risk_cities:
            location_adjustment = base_premium * 0.10
            location_note = "High-risk city (coastal/flood-prone)"
        elif worker_data.get('city') in low_risk_cities:
            location_adjustment = -base_premium * 0.10
            location_note = "Low-risk city discount"
        
        # STEP 4: Experience adjustment
        experience_adjustment = 0
        experience_note = ""
        exp_days = worker_data.get('experience_days', 30)
        
        if exp_days > 180:  # 6+ months
            experience_adjustment = -base_premium * 0.08
            experience_note = "Loyalty discount (6+ months)"
        elif exp_days < 30:  # Less than 1 month
            experience_adjustment = base_premium * 0.05
            experience_note = "New worker loading"
        
        # STEP 5: Calculate total
        # STEP 5a: Forecast adjustment (±15% on base premium)
        # Accept forecast adjustment as decimal fraction (e.g., 0.10 = +10%)
        forecast_adj_pct = 0.0
        # Look for value in worker_data first, then the risk prediction
        if isinstance(risk_prediction, dict):
            forecast_adj_pct = risk_prediction.get('forecast_adjustment_pct', 0.0)
        forecast_adj_pct = worker_data.get('forecast_adjustment_pct', forecast_adj_pct)

        # Clamp to allowed range
        forecast_adj_pct = max(-0.15, min(0.15, float(forecast_adj_pct)))
        forecast_adjustment = base_premium * forecast_adj_pct

        premium = base_premium + risk_loading + location_adjustment + experience_adjustment + forecast_adjustment
        
        # Clamp to min/max range
        final_premium = max(self.min_premium, min(self.max_premium, round(premium)))
        
        # Coverage is 80% of weekly income
        coverage_amount = round(weekly_income * 0.8)
        
        # Build breakdown for display
        breakdown = {
            "base_premium": round(base_premium),
            "risk_loading": round(risk_loading),
            "risk_score": risk_score,
            "adjustments": []
        }
        
        if location_adjustment != 0:
            breakdown["adjustments"].append({
                "name": location_note,
                "amount": round(location_adjustment)
            })
        
        if experience_adjustment != 0:
            breakdown["adjustments"].append({
                "name": experience_note,
                "amount": round(experience_adjustment)
            })

        # Include forecast adjustment in breakdown
        if abs(forecast_adjustment) > 0:
            breakdown["adjustments"].append({
                "name": "Forecast adjustment",
                "amount": round(forecast_adjustment)
            })
        
        return {
            "weekly_premium": final_premium,
            "breakdown": breakdown,
            "coverage_amount": coverage_amount,
            "valid_from": datetime.now().date().isoformat(),
            "valid_until": (datetime.now().date() + timedelta(days=7)).isoformat()
        }


premium_calculator = WeeklyPremiumCalculator()
