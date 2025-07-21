"""
Real-world probability data for life decision simulations
Compiled by Research Agent for realistic mode
"""

LIFE_DECISION_PROBABILITIES = {
    "career_relocation": {
        "job_satisfaction_increase": 0.67,
        "salary_increase": 0.58,
        "adaptation_success": 0.73,
        "regret_within_2_years": 0.22,
        "career_advancement": 0.61,
        "networking_expansion": 0.84
    },
    "education_choices": {
        "degree_completion": 0.64,
        "employment_in_field": 0.57,
        "positive_roi_5_years": 0.71,
        "career_pivot_success": 0.43,
        "satisfaction_with_choice": 0.68
    },
    "entrepreneurship": {
        "business_survival_1_year": 0.80,
        "business_survival_5_years": 0.50,
        "profitability_year_1": 0.40,
        "scale_to_10_employees": 0.23,
        "exit_opportunity": 0.12,
        "personal_fulfillment": 0.76
    },
    "relationship_decisions": {
        "marriage_success_10_years": 0.67,
        "cohabitation_to_marriage": 0.60,
        "long_distance_survival": 0.42,
        "friendship_maintenance": 0.55,
        "family_approval": 0.73
    },
    "lifestyle_changes": {
        "habit_formation_success": 0.21,
        "fitness_goal_achievement": 0.33,
        "diet_adherence_6_months": 0.20,
        "meditation_practice_sustained": 0.15,
        "work_life_balance_improvement": 0.48
    },
    "financial_decisions": {
        "investment_positive_return": 0.68,
        "debt_payoff_on_schedule": 0.52,
        "emergency_fund_maintained": 0.37,
        "budget_adherence": 0.29,
        "income_increase_from_skill": 0.64
    }
}

def get_probability(category: str, outcome: str, mode: str = "realistic") -> float:
    """Get probability for a specific outcome based on mode"""
    if mode == "realistic" and category in LIFE_DECISION_PROBABILITIES:
        return LIFE_DECISION_PROBABILITIES.get(category, {}).get(outcome, 0.5)
    elif mode == "50/50":
        return 0.5
    else:  # random/crazy mode
        import random
        return random.uniform(0.1, 0.9)