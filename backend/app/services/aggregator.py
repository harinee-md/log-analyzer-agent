"""
Aggregator Service

Aggregates metrics at multiple levels:
- Per Turn: Individual turn metrics
- Per Conversation: Averaged across all turns in a conversation
- Per Scenario: Averaged across all conversations of same type

Updated to strictly output the 17 finalized metrics.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class TurnMetrics:
    """Metrics for a single conversation turn"""
    turn_index: int
    role: str
    metrics: Dict[str, float]
    normalized_metrics: Dict[str, float]


@dataclass
class ConversationMetrics:
    """Aggregated metrics for a full conversation"""
    conversation_id: str
    case_intent: str
    turn_count: int
    turn_metrics: List[TurnMetrics]
    aggregated_metrics: Dict[str, float]
    binary_label: str
    composite_score: float
    quality_grade: str


@dataclass
class ScenarioMetrics:
    """Aggregated metrics for a scenario/intent category"""
    scenario_name: str
    conversation_count: int
    aggregated_metrics: Dict[str, float]
    label_distribution: Dict[str, int]
    avg_composite_score: float
    quality_grade: str


@dataclass
class AggregatedResults:
    """Complete aggregated results at all levels"""
    total_conversations: int
    turn_level: List[TurnMetrics]
    conversation_level: List[ConversationMetrics]
    scenario_level: List[ScenarioMetrics]
    overall_metrics: Dict[str, float]
    overall_label_distribution: Dict[str, int]
    overall_composite_score: float


class Aggregator:
    """
    Aggregates metrics at turn, conversation, and scenario levels.
    """
    
    # Final List of 17 Metrics to output (as keys)
    TARGET_METRICS = {
        "answer_relevancy",
        "turn_count",
        "clarity_score",
        "completeness_score",
        "context_retention_score",
        "customer_effort_score",
        "escalation_detected", # Will rename/map later if needed
        "hallucination_rate",
        "incorrect_refusal_rate",
        "intent_accuracy",
        "overconfidence",
        "pii_exposure_count",
        "pii_handling_compliance",
        "refusal_correctness",
        "resolution_detected",
        "response_accuracy",
        "tone_appropriateness"
    }

    def _filter_metrics(self, metrics: Dict[str, float]) -> Dict[str, float]:
        """
        Filter and strictly map internal keys to the final outcome.
        Removes internal helpers (user_turn_count, _llm suffixes, etc.)
        """
        filtered = {}
        for key, value in metrics.items():
            if key in self.TARGET_METRICS:
                filtered[key] = value
        
        return filtered

    def aggregate_turn_metrics(
        self,
        turns: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Aggregate metrics across multiple turns."""
        if not turns:
            return {}
        
        aggregated = defaultdict(list)
        
        for turn in turns:
            for metric_name, value in turn.items():
                if isinstance(value, (int, float)):
                    aggregated[metric_name].append(value)
        
        avg_metrics = {
            name: round(sum(values) / len(values), 4)
            for name, values in aggregated.items()
            if values
        }
        
        return self._filter_metrics(avg_metrics)
    
    def aggregate_conversation(
        self,
        conversation_id: str,
        case_intent: str,
        turn_metrics: List[TurnMetrics],
        rule_metrics: Dict[str, Any],
        llm_metrics: Dict[str, Any],
        normalized_metrics: Dict[str, float],
        binary_label: str,
        composite_score: float
    ) -> ConversationMetrics:
        """Create conversation-level aggregation."""
        from .metric_normalizer import MetricNormalizer
        normalizer = MetricNormalizer()
        
        # Filter metrics before storing
        clean_metrics = self._filter_metrics(normalized_metrics)
        
        return ConversationMetrics(
            conversation_id=conversation_id,
            case_intent=case_intent,
            turn_count=len(turn_metrics),
            turn_metrics=turn_metrics,
            aggregated_metrics=clean_metrics,
            binary_label=binary_label,
            composite_score=composite_score,
            quality_grade=normalizer.get_quality_grade(composite_score)
        )
    
    def aggregate_by_scenario(
        self,
        conversations: List[ConversationMetrics]
    ) -> List[ScenarioMetrics]:
        """Aggregate metrics by scenario/intent category."""
        from .metric_normalizer import MetricNormalizer
        normalizer = MetricNormalizer()
        
        scenario_groups = defaultdict(list)
        for conv in conversations:
            scenario_key = "All Conversations"
            scenario_groups[scenario_key].append(conv)
        
        scenarios = []
        for scenario_name, convs in scenario_groups.items():
            all_metrics = defaultdict(list)
            label_dist = defaultdict(int)
            scores = []
            
            for conv in convs:
                for metric_name, value in conv.aggregated_metrics.items():
                    if isinstance(value, (int, float)):
                        all_metrics[metric_name].append(value)
                
                label_dist[conv.binary_label] += 1
                scores.append(conv.composite_score)
            
            avg_metrics = {
                name: round(sum(values) / len(values), 4)
                for name, values in all_metrics.items()
                if values
            }
            
            # Ensure filtering is applied here too
            avg_metrics = self._filter_metrics(avg_metrics)
            
            avg_score = sum(scores) / len(scores) if scores else 0.0
            
            scenarios.append(ScenarioMetrics(
                scenario_name=scenario_name,
                conversation_count=len(convs),
                aggregated_metrics=avg_metrics,
                label_distribution=dict(label_dist),
                avg_composite_score=round(avg_score, 4),
                quality_grade=normalizer.get_quality_grade(avg_score)
            ))
        
        return sorted(scenarios, key=lambda x: x.conversation_count, reverse=True)
    
    def compute_overall(
        self,
        conversations: List[ConversationMetrics]
    ) -> tuple[Dict[str, float], Dict[str, int], float]:
        """Compute overall metrics across all conversations."""
        if not conversations:
            return {}, {}, 0.0
        
        all_metrics = defaultdict(list)
        label_dist = defaultdict(int)
        scores = []
        
        for conv in conversations:
            for metric_name, value in conv.aggregated_metrics.items():
                if isinstance(value, (int, float)):
                    all_metrics[metric_name].append(value)
            
            label_dist[conv.binary_label] += 1
            scores.append(conv.composite_score)
        
        avg_metrics = {
            name: round(sum(values) / len(values), 4)
            for name, values in all_metrics.items()
            if values
        }
        
        # Filter
        avg_metrics = self._filter_metrics(avg_metrics)
        
        avg_score = sum(scores) / len(scores) if scores else 0.0
        return avg_metrics, dict(label_dist), round(avg_score, 4)
    
    def aggregate_all(
        self,
        conversation_results: List[ConversationMetrics]
    ) -> AggregatedResults:
        """Create complete aggregation at all levels."""
        all_turns = []
        for conv in conversation_results:
            all_turns.extend(conv.turn_metrics)
        
        scenario_metrics = self.aggregate_by_scenario(conversation_results)
        overall_metrics, overall_labels, overall_score = self.compute_overall(conversation_results)
        
        return AggregatedResults(
            total_conversations=len(conversation_results),
            turn_level=all_turns,
            conversation_level=conversation_results,
            scenario_level=scenario_metrics,
            overall_metrics=overall_metrics,
            overall_label_distribution=overall_labels,
            overall_composite_score=overall_score
        )
    
    def to_dict(self, results: AggregatedResults) -> Dict[str, Any]:
        """Convert AggregatedResults to dictionary for JSON serialization"""
        return {
            "total_conversations": results.total_conversations,
            "overall": {
                "metrics": results.overall_metrics,
                "label_distribution": results.overall_label_distribution,
                "composite_score": results.overall_composite_score
            },
            "scenario_level": [
                {
                    "scenario": s.scenario_name,
                    "conversation_count": s.conversation_count,
                    "metrics": s.aggregated_metrics,
                    "labels": s.label_distribution,
                    "composite_score": s.avg_composite_score,
                    "grade": s.quality_grade
                }
                for s in results.scenario_level
            ],
            "conversation_level": [
                {
                    "id": c.conversation_id,
                    "intent": c.case_intent[:100] if c.case_intent else "",
                    "turn_count": c.turn_count,
                    "label": c.binary_label,
                    "composite_score": c.composite_score,
                    "grade": c.quality_grade,
                    "metrics": c.aggregated_metrics
                }
                for c in results.conversation_level
            ]
        }
