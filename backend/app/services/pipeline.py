"""
Pipeline Orchestrator

Chains all pipeline stages together:
1. Ingestion + Cleaning (log_parser)
2. Data Normalization
3. Rule-Based Feature Extraction
4. Ground Truth Extraction
5. Hybrid Metric Computation
6. Binary Labeling
7. Metric Normalization
8. Aggregation
"""

import os
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd

from .data_normalizer import DataNormalizer, NormalizedConversation
from .rule_engine import RuleEngine
from .binary_labeler import BinaryLabeler
from .metric_normalizer import MetricNormalizer
from .aggregator import Aggregator, ConversationMetrics, TurnMetrics, AggregatedResults


class LogAnalyzerPipeline:
    """
    Main pipeline orchestrator that chains all processing stages.
    """
    
    def __init__(self, evaluator=None):
        """
        Initialize pipeline with optional LLM evaluator.
        
        Args:
            evaluator: Optional MetricEvaluator instance for LLM metrics
        """
        self.normalizer = DataNormalizer()
        self.rule_engine = RuleEngine()
        self.binary_labeler = BinaryLabeler()
        self.metric_normalizer = MetricNormalizer()
        self.aggregator = Aggregator()
        self.evaluator = evaluator
    
    def process_file(
        self,
        file_path: str,
        use_llm_metrics: bool = True
    ) -> AggregatedResults:
        """
        Process an Excel/CSV log file through the full pipeline.
        
        Args:
            file_path: Path to the log file
            use_llm_metrics: Whether to compute LLM-based metrics
            
        Returns:
            AggregatedResults with all metrics at all levels
        """
        # Stage 1: Ingestion
        if file_path.endswith('.xlsx') or file_path.endswith('.xls'):
            df = pd.read_excel(file_path)
        elif file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_path}")
        
        return self.process_dataframe(df, use_llm_metrics)
    
    def process_dataframe(
        self,
        df: pd.DataFrame,
        use_llm_metrics: bool = True
    ) -> AggregatedResults:
        """
        Process a DataFrame through the full pipeline.
        
        Args:
            df: pandas DataFrame with log data
            use_llm_metrics: Whether to compute LLM-based metrics
            
        Returns:
            AggregatedResults with all metrics at all levels
        """
        # Stage 2: Data Normalization
        conversations = self.normalizer.normalize_dataframe(df)
        
        # Process each conversation
        conversation_results = []
        
        for conv in conversations:
            result = self.process_conversation(conv, use_llm_metrics)
            conversation_results.append(result)
        
        # Stage 8: Aggregation
        return self.aggregator.aggregate_all(conversation_results)
    
    def process_conversation(
        self,
        conv: NormalizedConversation,
        use_llm_metrics: bool = True
    ) -> ConversationMetrics:
        """
        Process a single conversation through stages 3-7.
        
        Args:
            conv: Normalized conversation data
            use_llm_metrics: Whether to compute LLM-based metrics
            
        Returns:
            ConversationMetrics with all computed metrics
        """
        # Stage 4: Ground Truth Extraction (Moved up for Intent Accuracy)
        # We need subject/intent for Rule Engine's Intent Accuracy metric
        case_number, subject, gt_emails = self.normalizer.parse_ground_truth_json(conv.ground_truth_emails)
        gt_text = self.normalizer.get_ground_truth_text(gt_emails)

        # Stage 3: Rule-Based Feature Extraction
        rule_metrics = self.rule_engine.compute_all(
            multi_turn_text=conv.raw_multi_turn,
            case_intent=conv.case_intent,
            gt_intent=subject
        )
        rule_dict = self.rule_engine.to_dict(rule_metrics)
        rule_reasoning = self.rule_engine.get_reasoning(rule_metrics)
        
        # Get bot response for comparison
        bot_messages = self.normalizer.get_bot_messages(conv.turns)
        agent_response = '\n'.join(bot_messages)
        
        # Stage 5: Hybrid Metric Computation
        llm_dict = {}
        llm_reasoning = {}
        if use_llm_metrics and self.evaluator:
            llm_dict, llm_reasoning = self._compute_llm_metrics(conv, gt_text)
        else:
            # Use default scores when LLM is not available
            llm_dict = self._get_default_llm_metrics()
            llm_reasoning = self._get_default_llm_reasoning()
        
        # Merge rule + LLM metrics
        combined_metrics = {**rule_dict, **llm_dict}
        
        # Merge reasoning from rule engine and LLM
        combined_reasoning = {**rule_reasoning, **llm_reasoning}
        
        # Stage 6: Binary Labeling
        if conv.download_action_score is not None and conv.download_intent_score is not None:
            # Use pre-computed scores
            label_result = self.binary_labeler.classify_from_scores(
                conv.download_action_score,
                conv.download_intent_score,
                agent_response
            )
        else:
            # Classify from metrics
            label_result = self.binary_labeler.classify_from_metrics(
                rule_dict,
                llm_dict,
                agent_response,
                gt_text
            )
        
        # Stage 7: Metric Normalization
        normalized = self.metric_normalizer.normalize_metrics(combined_metrics)
        composite_score = self.metric_normalizer.compute_composite_score(normalized)
        
        # Create turn metrics (simplified - one per conversation for now)
        turn_metrics = [
            TurnMetrics(
                turn_index=i,
                role=turn.role,
                metrics={},
                normalized_metrics={}
            )
            for i, turn in enumerate(conv.turns)
        ]
        
        return self.aggregator.aggregate_conversation(
            conversation_id=conv.conversation_id,
            case_intent=conv.case_intent,
            turn_metrics=turn_metrics,
            rule_metrics=rule_dict,
            llm_metrics=llm_dict,
            normalized_metrics=normalized,
            binary_label=label_result.label.value,
            composite_score=composite_score,
            metric_reasoning=combined_reasoning
        )
    
    def _compute_llm_metrics(
        self,
        conv: NormalizedConversation,
        gt_text: str
    ) -> Tuple[Dict[str, Any], Dict[str, str]]:
        """Compute LLM-based semantic metrics (18-metric set). Returns (metrics, reasoning)."""
        if not self.evaluator:
            return self._get_default_llm_metrics(), self._get_default_llm_reasoning()
        
        # Get user and bot messages
        user_messages = self.normalizer.get_user_messages(conv.turns)
        bot_messages = self.normalizer.get_bot_messages(conv.turns)
        
        user_query = '\n'.join(user_messages)
        agent_response = '\n'.join(bot_messages)
        conversation_history = conv.raw_multi_turn
        
        # Create LogEntry
        from ..models import LogEntry
        entry = LogEntry(
            user=user_query,
            human=gt_text,
            agent=agent_response
        )
        
        metrics = {}
        reasoning = {}
        
        # Helper to safely execute evaluator methods and collect reasoning
        def safe_eval(method, key, *args):
            try:
                result = method(*args)
                # Collect reasoning from MetricResult.description
                if result.description:
                    reasoning[key] = result.description
                return self._parse_metric_value(result.metric_value)
            except Exception as e:
                print(f"Error computing {key}: {e}")
                reasoning[key] = f"Error during evaluation: {str(e)}"
                return 50.0  # Default fallback

        # 1. Semantic Metrics
        metrics['response_accuracy'] = safe_eval(self.evaluator.evaluate_response_accuracy, 'response_accuracy', entry)
        metrics['answer_relevancy'] = safe_eval(self.evaluator.evaluate_answer_relevancy, 'answer_relevancy', entry)
        metrics['completeness_score'] = safe_eval(self.evaluator.evaluate_completeness, 'completeness_score', entry)
        metrics['clarity_score'] = safe_eval(self.evaluator.evaluate_clarity, 'clarity_score', entry)
        metrics['tone_appropriateness'] = safe_eval(self.evaluator.evaluate_tone_appropriateness, 'tone_appropriateness', entry)
        
        # 2. Risk/Compliance Metrics
        metrics['hallucination_rate'] = safe_eval(self.evaluator.evaluate_hallucination, 'hallucination_rate', entry)
        metrics['incorrect_refusal_rate'] = safe_eval(self.evaluator.evaluate_incorrect_refusal, 'incorrect_refusal_rate', entry)
        metrics['overconfidence'] = safe_eval(self.evaluator.evaluate_overconfidence, 'overconfidence', entry)
        metrics['pii_handling_compliance'] = safe_eval(self.evaluator.evaluate_pii_compliance, 'pii_handling_compliance', entry)
        metrics['refusal_correctness'] = safe_eval(self.evaluator.evaluate_refusal_correctness, 'refusal_correctness', entry)
        
        # 3. Hybrid Metric Validations (LLM side)
        # Just computing them, Aggregator will decide whether to use Rule or LLM
        metrics['customer_effort_score_llm'] = safe_eval(self.evaluator.evaluate_customer_effort_llm, 'customer_effort_score_llm', entry)
        metrics['context_retention_llm'] = safe_eval(self.evaluator.evaluate_context_retention_llm, 'context_retention_llm', conversation_history, agent_response)
        metrics['escalation_rate_llm'] = safe_eval(self.evaluator.evaluate_escalation_llm, 'escalation_rate_llm', agent_response)
        
        return metrics, reasoning
    
    def _parse_metric_value(self, value: Any) -> float:
        """Parse metric value to float"""
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            # Remove % sign if present
            clean = value.replace('%', '').strip()
            try:
                return float(clean)
            except:
                return 50.0
        return 50.0
    
    def _get_default_llm_metrics(self) -> Dict[str, float]:
        """Return default metrics when LLM is not available"""
        return {
            # Semantic
            'response_accuracy': 50,
            'answer_relevancy': 50,
            'completeness_score': 50,
            'clarity_score': 50,
            'tone_appropriateness': 50,
            
            # Risk
            'hallucination_rate': 0,
            'incorrect_refusal_rate': 0,
            'overconfidence': 0,
            'pii_handling_compliance': 100,
            'refusal_correctness': 50,
            
            # Hybrid metrics excluded as they are covered by Rule Engine
        }
    
    def _get_default_llm_reasoning(self) -> Dict[str, str]:
        """Return default reasoning when LLM is not available"""
        return {
            'response_accuracy': 'LLM not available for evaluation.',
            'answer_relevancy': 'LLM not available for evaluation.',
            'completeness_score': 'LLM not available for evaluation.',
            'clarity_score': 'LLM not available for evaluation.',
            'tone_appropriateness': 'LLM not available for evaluation.',
            'hallucination_rate': 'LLM not available for evaluation.',
            'incorrect_refusal_rate': 'LLM not available for evaluation.',
            'overconfidence': 'LLM not available for evaluation.',
            'pii_handling_compliance': 'LLM not available for evaluation.',
            'refusal_correctness': 'LLM not available for evaluation.',
        }
    
    def to_json(self, results: AggregatedResults) -> Dict[str, Any]:
        """Convert results to JSON-serializable dictionary"""
        return self.aggregator.to_dict(results)
