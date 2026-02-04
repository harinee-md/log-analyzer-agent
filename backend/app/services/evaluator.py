"""
Metric Evaluator Service

Main evaluation orchestrator using LangChain with Google Gemini (gemini-2.5-flash).
Implements the correct comparison logic for each metric category.
"""

import os
import json
import re
from typing import List, Dict, Any, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import LLMChain

from ..models import LogEntry, MetricResult
from ..prompts.metric_prompts import METRIC_PROMPTS


class MetricEvaluator:
    """
    Evaluates chatbot logs using LangChain with Google Gemini.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the evaluator with Google Gemini LLM."""
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY is required. Set it as an environment variable or pass it to the constructor.")
        
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=self.api_key,
            temperature=0.1,  # Low temperature for consistent evaluation
            convert_system_message_to_human=True
        )
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON from LLM response, handling markdown code blocks."""
        # Remove markdown code blocks if present
        cleaned = re.sub(r'```json\s*', '', response)
        cleaned = re.sub(r'```\s*', '', cleaned)
        cleaned = cleaned.strip()
        
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            # Try to extract JSON from the response
            match = re.search(r'\{.*\}', cleaned, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    pass
            return {"error": "Failed to parse response", "raw": response}
    
    def _run_prompt(self, prompt_name: str, variables: Dict[str, str]) -> Dict[str, Any]:
        """Run a prompt template and return parsed result."""
        if prompt_name not in METRIC_PROMPTS:
            return {"error": f"Unknown metric: {prompt_name}"}
        
        prompt = METRIC_PROMPTS[prompt_name]
        chain = prompt | self.llm
        
        try:
            result = chain.invoke(variables)
            return self._parse_json_response(result.content)
        except Exception as e:
            return {"error": str(e)}
    
    # =========================================================================
    # AGENT VS HUMAN METRICS
    # =========================================================================
    
    def evaluate_response_accuracy(self, entry: LogEntry) -> MetricResult:
        """Evaluate if agent response is factually correct compared to human."""
        result = self._run_prompt("response_accuracy", {
            "user_query": entry.user,
            "human_response": entry.human,
            "agent_response": entry.agent
        })
        
        return MetricResult(
            metric_name="Response Accuracy",
            metric_value=result.get("score", 0),
            description=result.get("reasoning", "")
        )
    
    def evaluate_intent_accuracy(self, entry: LogEntry) -> MetricResult:
        """Evaluate if agent correctly understood user intent."""
        result = self._run_prompt("intent_accuracy", {
            "user_query": entry.user,
            "human_response": entry.human,
            "agent_response": entry.agent
        })
        
        return MetricResult(
            metric_name="Intent Accuracy",
            metric_value=result.get("score", 0),
            description=result.get("reasoning", "")
        )
    
    def evaluate_completeness(self, entry: LogEntry) -> MetricResult:
        """Evaluate if agent response contains all necessary information."""
        result = self._run_prompt("completeness_score", {
            "user_query": entry.user,
            "human_response": entry.human,
            "agent_response": entry.agent
        })
        
        return MetricResult(
            metric_name="Completeness Score",
            metric_value=result.get("score", 0),
            description=result.get("reasoning", "")
        )
    
    def evaluate_clarity(self, entry: LogEntry) -> MetricResult:
        """Evaluate how clear and understandable the response is."""
        result = self._run_prompt("clarity_score", {
            "user_query": entry.user,
            "human_response": entry.human,
            "agent_response": entry.agent
        })
        
        return MetricResult(
            metric_name="Clarity Score",
            metric_value=result.get("score", 0),
            description=result.get("reasoning", "")
        )
    
    # =========================================================================
    # AGENT VS USER METRICS
    # =========================================================================
    
    def evaluate_answer_relevancy(self, entry: LogEntry) -> MetricResult:
        """Evaluate if response directly addresses the user's question."""
        result = self._run_prompt("answer_relevancy", {
            "user_query": entry.user,
            "agent_response": entry.agent
        })
        
        return MetricResult(
            metric_name="Answer Relevancy",
            metric_value=result.get("score", 0),
            description=result.get("reasoning", "")
        )
    
    def evaluate_context_retention(self, entries: List[LogEntry], current_index: int) -> MetricResult:
        """Evaluate if agent remembers earlier conversation context."""
        # Build conversation history from previous entries
        history = ""
        for i in range(max(0, current_index - 3), current_index):
            history += f"User: {entries[i].user}\nAgent: {entries[i].agent}\n\n"
        
        if not history:
            history = "No previous context available"
        
        current_entry = entries[current_index]
        result = self._run_prompt("context_retention", {
            "conversation_history": history,
            "current_user_query": current_entry.user,
            "agent_response": current_entry.agent
        })
        
        return MetricResult(
            metric_name="Context Retention",
            metric_value=result.get("score", 0),
            description=result.get("reasoning", "")
        )
    
    def evaluate_tone_appropriateness(self, entry: LogEntry) -> MetricResult:
        """Evaluate if agent maintains appropriate tone."""
        result = self._run_prompt("tone_appropriateness", {
            "user_query": entry.user,
            "agent_response": entry.agent
        })
        
        return MetricResult(
            metric_name="Tone Appropriateness",
            metric_value=result.get("score", 0),
            description=result.get("reasoning", "")
        )
    
    def evaluate_customer_effort(self, entry: LogEntry) -> MetricResult:
        """Evaluate how much effort customer needs to resolve issue."""
        result = self._run_prompt("customer_effort_score", {
            "user_query": entry.user,
            "agent_response": entry.agent,
            "human_response": entry.human
        })
        
        return MetricResult(
            metric_name="Customer Effort Score",
            metric_value=result.get("score", 0),
            description=result.get("reasoning", "")
        )
    
    # =========================================================================
    # AGENT-ONLY METRICS
    # =========================================================================
    
    def evaluate_hallucination(self, entry: LogEntry) -> MetricResult:
        """Detect fabricated or incorrect information."""
        result = self._run_prompt("hallucination_rate", {
            "user_query": entry.user,
            "human_response": entry.human,
            "agent_response": entry.agent
        })
        
        detected = result.get("hallucination_detected", False)
        count = result.get("hallucination_count", 0)
        
        return MetricResult(
            metric_name="Hallucination Rate",
            metric_value=f"{count} detected" if detected else "None detected",
            description=result.get("details", "")
        )
    
    def evaluate_pii_exposure(self, entry: LogEntry) -> MetricResult:
        """Count PII exposure instances."""
        result = self._run_prompt("pii_exposure", {
            "agent_response": entry.agent
        })
        
        exposed = result.get("pii_exposed", False)
        count = result.get("exposure_count", 0)
        
        return MetricResult(
            metric_name="PII Exposure Count",
            metric_value=count,
            description=result.get("details", "")
        )
    
    def evaluate_pii_handling(self, entry: LogEntry) -> MetricResult:
        """Evaluate PII handling compliance."""
        result = self._run_prompt("pii_handling_compliance", {
            "user_query": entry.user,
            "agent_response": entry.agent
        })
        
        return MetricResult(
            metric_name="PII Handling Compliance",
            metric_value=result.get("score", 0),
            description=result.get("reasoning", "")
        )
    
    def evaluate_overconfidence(self, entry: LogEntry) -> MetricResult:
        """Detect overconfidence without evidence."""
        result = self._run_prompt("overconfidence", {
            "user_query": entry.user,
            "agent_response": entry.agent,
            "human_response": entry.human
        })
        
        overconfident = result.get("overconfident", False)
        
        return MetricResult(
            metric_name="Overconfidence Without Evidence",
            metric_value="Yes" if overconfident else "No",
            description=result.get("reasoning", "")
        )
    
    def evaluate_incorrect_refusal(self, entry: LogEntry) -> MetricResult:
        """Detect incorrect refusals of legitimate requests."""
        result = self._run_prompt("incorrect_refusal", {
            "user_query": entry.user,
            "agent_response": entry.agent,
            "human_response": entry.human
        })
        
        incorrect = result.get("incorrect_refusal", False)
        
        return MetricResult(
            metric_name="Incorrect Refusal Rate",
            metric_value="Yes" if incorrect else "No",
            description=result.get("reasoning", "")
        )
    
    def evaluate_refusal_correctness(self, entry: LogEntry) -> MetricResult:
        """Evaluate if refusal decisions are correct."""
        result = self._run_prompt("refusal_correctness", {
            "user_query": entry.user,
            "agent_response": entry.agent,
            "human_response": entry.human
        })
        
        return MetricResult(
            metric_name="Refusal Correctness",
            metric_value=result.get("score", 0),
            description=result.get("reasoning", "")
        )
    
    # =========================================================================
    # AGGREGATE METRICS
    # =========================================================================
    
    def evaluate_escalation(self, entry: LogEntry) -> MetricResult:
        """Detect if conversation was escalated."""
        result = self._run_prompt("escalation_detection", {
            "agent_response": entry.agent
        })
        
        escalated = result.get("escalated", False)
        
        return MetricResult(
            metric_name="Escalation Rate",
            metric_value="Escalated" if escalated else "Not Escalated",
            description=result.get("reasoning", "")
        )
    
    def evaluate_resolution(self, entry: LogEntry) -> MetricResult:
        """Detect if issue was resolved."""
        result = self._run_prompt("resolution_detection", {
            "user_query": entry.user,
            "agent_response": entry.agent
        })
        
        resolved = result.get("resolved", False)
        
        return MetricResult(
            metric_name="Resolution Rate",
            metric_value="Resolved" if resolved else "Not Resolved",
            description=result.get("reasoning", "")
        )
    
    def calculate_average_latency(self, entries: List[LogEntry]) -> MetricResult:
        """Calculate average latency across entries."""
        latencies = [e.latency_ms for e in entries if e.latency_ms is not None]
        
        if latencies:
            avg = sum(latencies) / len(latencies)
            return MetricResult(
                metric_name="Average Latency",
                metric_value=f"{avg:.2f} ms",
                description=f"Calculated from {len(latencies)} entries"
            )
        
        return MetricResult(
            metric_name="Average Latency",
            metric_value="N/A",
            description="No latency data available"
        )
    
    def calculate_turns_to_resolution(self, entries: List[LogEntry]) -> MetricResult:
        """Calculate average turns to resolution."""
        return MetricResult(
            metric_name="Average Turns to Resolution",
            metric_value=len(entries),
            description=f"Based on {len(entries)} conversation turns"
        )
    
    # =========================================================================
    # MAIN EVALUATION
    # =========================================================================
    
    def evaluate_all(self, entries: List[LogEntry]) -> List[MetricResult]:
        """
        Run all evaluations on the provided log entries.
        Returns aggregated metrics across all entries.
        """
        if not entries:
            return []
        
        all_results = []
        
        # Aggregate counters for rate calculations
        total_entries = len(entries)
        hallucination_count = 0
        pii_exposure_count = 0
        escalation_count = 0
        resolution_count = 0
        incorrect_refusal_count = 0
        
        # Score accumulators
        response_accuracy_scores = []
        intent_accuracy_scores = []
        completeness_scores = []
        clarity_scores = []
        answer_relevancy_scores = []
        context_retention_scores = []
        tone_scores = []
        customer_effort_scores = []
        pii_handling_scores = []
        refusal_correctness_scores = []
        overconfidence_count = 0
        
        # Evaluate each entry
        for i, entry in enumerate(entries):
            # Agent vs Human metrics
            result = self.evaluate_response_accuracy(entry)
            if isinstance(result.metric_value, (int, float)):
                response_accuracy_scores.append(result.metric_value)
            
            result = self.evaluate_intent_accuracy(entry)
            if isinstance(result.metric_value, (int, float)):
                intent_accuracy_scores.append(result.metric_value)
            
            result = self.evaluate_completeness(entry)
            if isinstance(result.metric_value, (int, float)):
                completeness_scores.append(result.metric_value)
            
            result = self.evaluate_clarity(entry)
            if isinstance(result.metric_value, (int, float)):
                clarity_scores.append(result.metric_value)
            
            # Agent vs User metrics
            result = self.evaluate_answer_relevancy(entry)
            if isinstance(result.metric_value, (int, float)):
                answer_relevancy_scores.append(result.metric_value)
            
            result = self.evaluate_context_retention(entries, i)
            if isinstance(result.metric_value, (int, float)):
                context_retention_scores.append(result.metric_value)
            
            result = self.evaluate_tone_appropriateness(entry)
            if isinstance(result.metric_value, (int, float)):
                tone_scores.append(result.metric_value)
            
            result = self.evaluate_customer_effort(entry)
            if isinstance(result.metric_value, (int, float)):
                customer_effort_scores.append(result.metric_value)
            
            # Agent-only metrics
            result = self.evaluate_hallucination(entry)
            if "detected" in str(result.metric_value) and "None" not in str(result.metric_value):
                hallucination_count += 1
            
            result = self.evaluate_pii_exposure(entry)
            if isinstance(result.metric_value, (int, float)) and result.metric_value > 0:
                pii_exposure_count += result.metric_value
            
            result = self.evaluate_pii_handling(entry)
            if isinstance(result.metric_value, (int, float)):
                pii_handling_scores.append(result.metric_value)
            
            result = self.evaluate_overconfidence(entry)
            if result.metric_value == "Yes":
                overconfidence_count += 1
            
            result = self.evaluate_incorrect_refusal(entry)
            if result.metric_value == "Yes":
                incorrect_refusal_count += 1
            
            result = self.evaluate_refusal_correctness(entry)
            if isinstance(result.metric_value, (int, float)):
                refusal_correctness_scores.append(result.metric_value)
            
            # Aggregate metrics
            result = self.evaluate_escalation(entry)
            if result.metric_value == "Escalated":
                escalation_count += 1
            
            result = self.evaluate_resolution(entry)
            if result.metric_value == "Resolved":
                resolution_count += 1
        
        # Calculate averages and rates
        def avg(scores):
            return round(sum(scores) / len(scores), 2) if scores else 0
        
        def rate(count, total):
            return round((count / total) * 100, 2) if total > 0 else 0
        
        # Build final results
        all_results = [
            MetricResult(metric_name="Answer Relevancy", metric_value=f"{avg(answer_relevancy_scores)}%"),
            MetricResult(metric_name="Average Latency", metric_value=self.calculate_average_latency(entries).metric_value),
            MetricResult(metric_name="Average Turns to Resolution", metric_value=total_entries),
            MetricResult(metric_name="Clarity Score", metric_value=f"{avg(clarity_scores)}%"),
            MetricResult(metric_name="Completeness Score", metric_value=f"{avg(completeness_scores)}%"),
            MetricResult(metric_name="Context Retention", metric_value=f"{avg(context_retention_scores)}%"),
            MetricResult(metric_name="Customer Effort Score", metric_value=f"{avg(customer_effort_scores)}%"),
            MetricResult(metric_name="Escalation Rate", metric_value=f"{rate(escalation_count, total_entries)}%"),
            MetricResult(metric_name="Hallucination Rate", metric_value=f"{rate(hallucination_count, total_entries)}%"),
            MetricResult(metric_name="Incorrect Refusal Rate", metric_value=f"{rate(incorrect_refusal_count, total_entries)}%"),
            MetricResult(metric_name="Intent Accuracy", metric_value=f"{avg(intent_accuracy_scores)}%"),
            MetricResult(metric_name="Overconfidence Without Evidence", metric_value=f"{rate(overconfidence_count, total_entries)}%"),
            MetricResult(metric_name="PII Exposure Count", metric_value=pii_exposure_count),
            MetricResult(metric_name="PII Handling Compliance", metric_value=f"{avg(pii_handling_scores)}%"),
            MetricResult(metric_name="Refusal Correctness", metric_value=f"{avg(refusal_correctness_scores)}%"),
            MetricResult(metric_name="Resolution Rate", metric_value=f"{rate(resolution_count, total_entries)}%"),
            MetricResult(metric_name="Response Accuracy", metric_value=f"{avg(response_accuracy_scores)}%"),
            MetricResult(metric_name="Tone Appropriateness", metric_value=f"{avg(tone_scores)}%"),
        ]
        
        return all_results
