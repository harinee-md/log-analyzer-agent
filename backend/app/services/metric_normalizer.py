"""
Metric Normalizer Service

Normalizes all metrics to 0-1 range for consistent comparison and aggregation.
Updated to support the final 17-metric list (latency removed).
"""

from typing import Dict, Any, List
from dataclasses import dataclass


@dataclass
class NormalizationConfig:
    """Configuration for metric normalization"""
    min_val: float = 0.0
    max_val: float = 100.0
    invert: bool = False  # If True, higher raw = lower normalized


class MetricNormalizer:
    """
    Normalizes metrics to 0-1 scale.
    """
    
    # Metric-specific normalization configurations
    # All 17 Metric Definitions mapped here
    NORMALIZATION_CONFIG = {
        # --- Rule-Based Metrics ---
        "turn_count": NormalizationConfig(min_val=1, max_val=20, invert=True), # Average Turns
        # Latency Removed
        "pii_exposure_count": NormalizationConfig(min_val=0, max_val=5, invert=True),
        "resolution_detected": NormalizationConfig(min_val=0, max_val=1), # Resolution Rate (binary -> avg)
        "intent_accuracy": NormalizationConfig(min_val=0, max_val=100), # Rule-based intent match
        "escalation_detected": NormalizationConfig(min_val=0, max_val=1, invert=True), # Escalation Rate (binary -> avg)
        "context_retention_score": NormalizationConfig(min_val=0, max_val=1), # Rule-based context
        "customer_effort_score": NormalizationConfig(min_val=0, max_val=1, invert=True), # Rule-based effort
        
        # --- Semantic Metrics (LLM) ---
        "response_accuracy": NormalizationConfig(min_val=0, max_val=100),
        "completeness_score": NormalizationConfig(min_val=0, max_val=100),
        "clarity_score": NormalizationConfig(min_val=0, max_val=100),
        "answer_relevancy": NormalizationConfig(min_val=0, max_val=100),
        "tone_appropriateness": NormalizationConfig(min_val=0, max_val=100),
        
        # --- Risk/Compliance Metrics (LLM) ---
        "hallucination_rate": NormalizationConfig(min_val=0, max_val=100, invert=True),
        "incorrect_refusal_rate": NormalizationConfig(min_val=0, max_val=100, invert=True),
        "overconfidence": NormalizationConfig(min_val=0, max_val=100, invert=True),
        "pii_handling_compliance": NormalizationConfig(min_val=0, max_val=100),
        "refusal_correctness": NormalizationConfig(min_val=0, max_val=100),
        
        # --- Hybrid/Fallback Metrics ---
        "customer_effort_score_llm": NormalizationConfig(min_val=0, max_val=100, invert=True),
        "context_retention_llm": NormalizationConfig(min_val=0, max_val=100),
        "escalation_rate_llm": NormalizationConfig(min_val=0, max_val=100, invert=True),
    }
    
    def normalize_value(
        self,
        value: Any,
        metric_name: str
    ) -> float:
        """
        Normalize a single metric value to 0-1 range.
        
        Args:
            value: Raw metric value
            metric_name: Name of the metric for config lookup
            
        Returns:
            Normalized value between 0 and 1
        """
        # Handle None/missing values
        if value is None:
            return 0.0
        
        # Handle boolean values
        if isinstance(value, bool):
            return 1.0 if value else 0.0
        
        # Handle string percentages like "85%"
        if isinstance(value, str):
            if value.endswith('%'):
                try:
                    value = float(value[:-1])
                except ValueError:
                    return 0.0
            elif value.lower() in ('yes', 'true', 'resolved', 'escalated'):
                return 1.0
            elif value.lower() in ('no', 'false', 'not resolved', 'not escalated'):
                return 0.0
            else:
                try:
                    value = float(value)
                except ValueError:
                    return 0.0
        
        # Convert to float
        try:
            value = float(value)
        except (TypeError, ValueError):
            return 0.0
        
        # Get normalization config
        config = self.NORMALIZATION_CONFIG.get(
            metric_name,
            NormalizationConfig()  # Default: assume 0-100 scale
        )
        
        # Apply min-max normalization
        range_size = config.max_val - config.min_val
        if range_size == 0:
            normalized = 0.0
        else:
            normalized = (value - config.min_val) / range_size
        
        # Clamp to 0-1
        normalized = max(0.0, min(1.0, normalized))
        
        # Invert if needed (for metrics where lower is better)
        if config.invert:
            normalized = 1.0 - normalized
        
        # Special case: Hallucination rate is often just "100" (found) or "0" (not found)
        # Invert logic handles it: 100 -> 0 (bad), 0 -> 1 (good)
        
        return round(normalized, 4)
    
    def normalize_metrics(
        self,
        metrics: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        Normalize all metrics in a dictionary.
        """
        normalized = {}
        
        for name, value in metrics.items():
            # Skip non-numeric fields
            if name in ('pii_types', 'entities_found', 'order_numbers', 'label', 'reasoning'):
                continue
            
            normalized[name] = self.normalize_value(value, name)
        
        return normalized
    
    def compute_composite_score(
        self,
        normalized_metrics: Dict[str, float],
        weights: Dict[str, float] = None
    ) -> float:
        """
        Compute weighted composite score from normalized metrics.
        """
        if not normalized_metrics:
            return 0.0
        
        if weights is None:
            # Equal weighting
            weights = {k: 1.0 for k in normalized_metrics}
        
        weighted_sum = 0.0
        total_weight = 0.0
        
        for metric, value in normalized_metrics.items():
            weight = weights.get(metric, 1.0)
            weighted_sum += value * weight
            total_weight += weight
        
        if total_weight == 0:
            return 0.0
        
        return round(weighted_sum / total_weight, 4)
    
    def get_quality_grade(self, composite_score: float) -> str:
        """
        Convert composite score to letter grade.
        
        Returns: A, B, C, D, or F
        """
        if composite_score >= 0.9:
            return "A"
        elif composite_score >= 0.8:
            return "B"
        elif composite_score >= 0.7:
            return "C"
        elif composite_score >= 0.6:
            return "D"
        else:
            return "F"
