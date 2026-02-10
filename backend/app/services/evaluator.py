"""
Metric Evaluator Service

Evaluates semantic chatbot logs using LangChain with Google Gemini (gemini-2.5-flash).
Focuses only on metrics that require LLM judgment.

Updated to match the 18-metric final list.
"""

import os
import json
import re
from typing import List, Dict, Any, Optional
from langchain_openai import ChatOpenAI

from ..models import LogEntry, MetricResult
from ..prompts.metric_prompts import METRIC_PROMPTS


class MetricEvaluator:
    """
    Evaluates semantic chatbot logs using LangChain with OpenAI GPT-4o-mini.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the evaluator with OpenAI LLM."""
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is required. Set it as an environment variable or pass it to the constructor.")
        
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            api_key=self.api_key,
            temperature=0.1  # Low temperature for consistent evaluation
        )
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON from LLM response, handling markdown code blocks."""
        cleaned = re.sub(r'```json\s*', '', response)
        cleaned = re.sub(r'```\s*', '', cleaned)
        cleaned = cleaned.strip()
        
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            match = re.search(r'\{.*\}', cleaned, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    pass
            # Very aggressive cleanup
            try:
                # Sometimes keys are not quoted properly in older models, 
                # but gemini-2.5-flash is usually compliant.
                return json.loads(cleaned.replace("'", '"'))
            except:
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
    # SEMANTIC METRICS (LLM-Based)
    # =========================================================================
    
    def evaluate_response_accuracy(self, entry: LogEntry) -> MetricResult:
        result = self._run_prompt("response_accuracy", {
            "user_query": entry.user,
            "human_response": entry.human,
            "agent_response": entry.agent
        })
        reasoning = result.get("reasoning", "LLM evaluation of response accuracy.")
        return MetricResult(metric_name="Response Accuracy", metric_value=result.get("score", 50), description=reasoning)
    
    def evaluate_completeness(self, entry: LogEntry) -> MetricResult:
        result = self._run_prompt("completeness_score", {
            "user_query": entry.user,
            "human_response": entry.human,
            "agent_response": entry.agent
        })
        reasoning = result.get("reasoning", "LLM evaluation of response completeness.")
        return MetricResult(metric_name="Completeness Score", metric_value=result.get("score", 50), description=reasoning)
    
    def evaluate_clarity(self, entry: LogEntry) -> MetricResult:
        result = self._run_prompt("clarity_score", {
            "agent_response": entry.agent
        })
        reasoning = result.get("reasoning", "LLM evaluation of response clarity.")
        return MetricResult(metric_name="Clarity Score", metric_value=result.get("score", 50), description=reasoning)
    
    def evaluate_answer_relevancy(self, entry: LogEntry) -> MetricResult:
        result = self._run_prompt("answer_relevancy", {
            "user_query": entry.user,
            "agent_response": entry.agent
        })
        reasoning = result.get("reasoning", "LLM evaluation of answer relevancy.")
        return MetricResult(metric_name="Answer Relevancy", metric_value=result.get("score", 50), description=reasoning)
    
    def evaluate_tone_appropriateness(self, entry: LogEntry) -> MetricResult:
        result = self._run_prompt("tone_appropriateness", {
            "agent_response": entry.agent
        })
        reasoning = result.get("reasoning", "LLM evaluation of tone appropriateness.")
        return MetricResult(metric_name="Tone Appropriateness", metric_value=result.get("score", 50), description=reasoning)
    
    def evaluate_hallucination(self, entry: LogEntry) -> MetricResult:
        result = self._run_prompt("hallucination_rate", {
            "user_query": entry.user,
            "human_response": entry.human,
            "agent_response": entry.agent
        })
        is_hallucinating = result.get("hallucination_detected", False)
        reasoning = result.get("reasoning", "Hallucination detected." if is_hallucinating else "No hallucination detected.")
        return MetricResult(metric_name="Hallucination Rate", metric_value=100 if is_hallucinating else 0, description=reasoning)
    
    def evaluate_incorrect_refusal(self, entry: LogEntry) -> MetricResult:
        result = self._run_prompt("incorrect_refusal_rate", {
            "user_query": entry.user,
            "human_response": entry.human,
            "agent_response": entry.agent
        })
        is_incorrect = result.get("incorrect_refusal", False)
        reasoning = result.get("reasoning", "Incorrect refusal detected." if is_incorrect else "No incorrect refusal detected.")
        return MetricResult(metric_name="Incorrect Refusal Rate", metric_value=100 if is_incorrect else 0, description=reasoning)

    def evaluate_refusal_correctness(self, entry: LogEntry) -> MetricResult:
        result = self._run_prompt("refusal_correctness", {
            "user_query": entry.user,
            "human_response": entry.human,
            "agent_response": entry.agent
        })
        reasoning = result.get("reasoning", "LLM evaluation of refusal correctness.")
        return MetricResult(metric_name="Refusal Correctness", metric_value=result.get("score", 50), description=reasoning)

    def evaluate_overconfidence(self, entry: LogEntry) -> MetricResult:
        result = self._run_prompt("overconfidence", {
            "user_query": entry.user,
            "agent_response": entry.agent
        })
        detected = result.get("overconfidence_detected", False)
        reasoning = result.get("reasoning", "Overconfidence detected." if detected else "No overconfidence detected.")
        return MetricResult(metric_name="Overconfidence", metric_value=100 if detected else 0, description=reasoning)

    def evaluate_pii_compliance(self, entry: LogEntry) -> MetricResult:
        result = self._run_prompt("pii_handling_compliance", {
            "user_query": entry.user,
            "agent_response": entry.agent
        })
        reasoning = result.get("reasoning", "LLM evaluation of PII handling compliance.")
        return MetricResult(metric_name="PII Handling Compliance", metric_value=result.get("score", 100), description=reasoning)
    
    def evaluate_customer_effort_llm(self, entry: LogEntry) -> MetricResult:
        result = self._run_prompt("customer_effort_score", {
            "user_query": entry.user,
            "agent_response": entry.agent
        })
        reasoning = result.get("reasoning", "LLM evaluation of customer effort.")
        return MetricResult(metric_name="Customer Effort Score (LLM)", metric_value=result.get("score", 50), description=reasoning)
    
    def evaluate_context_retention_llm(self, history: str, response: str) -> MetricResult:
        result = self._run_prompt("context_retention", {
            "conversation_history": history,
            "agent_response": response
        })
        reasoning = result.get("reasoning", "LLM evaluation of context retention.")
        return MetricResult(metric_name="Context Retention (LLM)", metric_value=result.get("score", 50), description=reasoning)

    def evaluate_escalation_llm(self, response: str) -> MetricResult:
        result = self._run_prompt("escalation_rate", {
            "agent_response": response
        })
        escalated = result.get("escalated", False)
        reasoning = result.get("reasoning", "Escalation detected." if escalated else "No escalation detected.")
        return MetricResult(metric_name="Escalation Rate (LLM)", metric_value=100 if escalated else 0, description=reasoning)
