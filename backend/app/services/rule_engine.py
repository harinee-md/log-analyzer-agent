"""
Rule Engine for Deterministic Metrics

Computes rule-based metrics without LLM calls:
- Context retention (entity reuse)
- Turn count
- Customer effort (heuristic)
- PII exposure detection
- Resolution keyword detection
- Intent Accuracy (Rule-based match)
"""

import re
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass


@dataclass
class ConversationTurn:
    """Single turn in a conversation"""
    role: str  # "Bot" or "User"
    message: str
    is_action: bool = False  # True if JSON action payload


@dataclass
class RuleMetrics:
    """Output of rule-based metric computation"""
    turn_count: int
    user_turn_count: int
    bot_turn_count: int
    context_retention_score: float
    pii_exposure_count: int
    pii_types: List[str]
    customer_effort_score: float
    resolution_detected: bool
    escalation_detected: bool
    intent_matched: bool # Intent Accuracy
    entities_found: List[str]
    order_numbers: List[str]
    metric_reasoning: Dict[str, str] = None  # Explanations for each metric


class RuleEngine:
    """
    Computes deterministic metrics using pattern matching and heuristics.
    """
    
    # PII Detection Patterns
    PII_PATTERNS = {
        "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        "phone": r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b',
        "ssn": r'\b\d{3}[-.\s]?\d{2}[-.\s]?\d{4}\b',
        "credit_card": r'\b(?:\d{4}[-.\s]?){3}\d{4}\b',
        "ip_address": r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
    }
    
    # Resolution Keywords
    RESOLUTION_KEYWORDS = [
        "resolved", "fixed", "completed", "done", "solved",
        "helped", "thank you", "thanks", "that works",
        "issue is resolved", "problem solved", "all set",
        "perfect", "great", "awesome", "appreciate"
    ]
    
    # Escalation Keywords
    ESCALATION_KEYWORDS = [
        "transfer", "supervisor", "manager", "human agent",
        "speak to someone", "escalate", "connect me",
        "real person", "live agent"
    ]
    
    # Order/Reference Number Patterns
    ORDER_PATTERNS = [
        r'\b(?:order|invoice|case|ticket|ref|reference)[\s#:]*([A-Z0-9-]{5,})\b',
        r'\bINV[0-9]+\b',
        r'\b[A-Z]{2,4}[0-9]{5,}\b',
    ]
    
    def parse_conversation(self, multi_turn_text: str) -> List[ConversationTurn]:
        """
        Parse multi-turn conversation text into structured turns.
        """
        turns = []
        lines = multi_turn_text.strip().split('\n')
        current_role = None
        current_message = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check for role prefix
            if line.startswith("Bot:"):
                # Save previous turn
                if current_role and current_message:
                    msg = '\n'.join(current_message).strip()
                    is_action = msg.startswith('{') and '"' in msg
                    turns.append(ConversationTurn(
                        role=current_role,
                        message=msg,
                        is_action=is_action
                    ))
                current_role = "Bot"
                current_message = [line[4:].strip()]
            elif line.startswith("User:"):
                if current_role and current_message:
                    msg = '\n'.join(current_message).strip()
                    is_action = msg.startswith('{') and '"' in msg
                    turns.append(ConversationTurn(
                        role=current_role,
                        message=msg,
                        is_action=is_action
                    ))
                current_role = "User"
                current_message = [line[5:].strip()]
            else:
                # Continuation of current message
                if current_role:
                    current_message.append(line)
        
        # Don't forget the last turn
        if current_role and current_message:
            msg = '\n'.join(current_message).strip()
            is_action = msg.startswith('{') and '"' in msg
            turns.append(ConversationTurn(
                role=current_role,
                message=msg,
                is_action=is_action
            ))
        
        return turns
    
    def extract_entities(self, text: str) -> List[str]:
        """Extract named entities (simple pattern-based approach)"""
        entities = []
        
        # Extract capitalized multi-word phrases (potential names/products)
        name_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b'
        entities.extend(re.findall(name_pattern, text))
        
        # Extract order/reference numbers
        entities.extend(self.detect_order_numbers(text))
        
        # Remove common words
        common_words = {'I', 'The', 'This', 'That', 'Hello', 'Hi', 'Thank', 'Thanks', 
                       'Please', 'Yes', 'No', 'Ok', 'Okay', 'Bot', 'User'}
        entities = [e for e in entities if e not in common_words]
        
        return list(set(entities))
    
    def detect_order_numbers(self, text: str) -> List[str]:
        """Detect order/invoice/reference numbers"""
        matches = []
        for pattern in self.ORDER_PATTERNS:
            found = re.findall(pattern, text, re.IGNORECASE)
            matches.extend(found)
        return list(set(matches))
    
    def count_turns(self, turns: List[ConversationTurn]) -> Tuple[int, int, int, str]:
        """Count total, user, and bot turns. Returns (total, user, bot, reasoning)"""
        total = len(turns)
        user_turns = sum(1 for t in turns if t.role == "User")
        bot_turns = sum(1 for t in turns if t.role == "Bot")
        reasoning = f"Counted {total} turns (User: {user_turns}, Bot: {bot_turns})."
        return total, user_turns, bot_turns, reasoning
    
    def detect_pii(self, text: str) -> Tuple[int, List[str], str]:
        """Detect PII patterns in text. Returns (count, types, reasoning)"""
        found_types = []
        total_count = 0
        
        for pii_type, pattern in self.PII_PATTERNS.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                found_types.append(pii_type)
                total_count += len(matches)
        
        if total_count > 0:
            reasoning = f"Found {total_count} PII instances: {', '.join(found_types)}."
        else:
            reasoning = "No PII detected in the conversation."
        
        return total_count, found_types, reasoning
    
    def compute_customer_effort(self, turns: List[ConversationTurn]) -> Tuple[float, str]:
        """
        Compute customer effort score (0-1, lower is better).
        Returns (score, reasoning)
        """
        user_turns = [t for t in turns if t.role == "User"]
        
        if not user_turns:
            return 0.0, "No user turns found, minimal effort required."
        
        # Base effort from turn count (normalized, max 10 turns)
        turn_effort = min(len(user_turns) / 10.0, 1.0)
        
        # Count questions (indicates seeking help)
        question_count = sum(
            1 for t in user_turns 
            if '?' in t.message
        )
        question_effort = min(question_count / 5.0, 1.0)
        
        # Combine factors
        effort_score = (turn_effort * 0.6) + (question_effort * 0.4)
        
        reasoning = f"User made {len(user_turns)} turns with {question_count} questions. Effort based on turn count ({turn_effort:.2f}) and question frequency ({question_effort:.2f})."
        return round(effort_score, 3), reasoning
    
    def detect_resolution(self, turns: List[ConversationTurn]) -> Tuple[bool, str]:
        """Detect if conversation appears resolved. Returns (detected, reasoning)"""
        # Check last few turns for resolution keywords
        last_turns = turns[-3:] if len(turns) >= 3 else turns
        
        for turn in last_turns:
            text_lower = turn.message.lower()
            for keyword in self.RESOLUTION_KEYWORDS:
                if keyword in text_lower:
                    reasoning = f"Detected resolution keyword '{keyword}' in last {len(last_turns)} turns."
                    return True, reasoning
        
        reasoning = f"No resolution keywords found in last {len(last_turns)} turns."
        return False, reasoning
    
    def detect_escalation(self, turns: List[ConversationTurn]) -> Tuple[bool, str]:
        """Detect if conversation was escalated. Returns (detected, reasoning)"""
        full_text = ' '.join(t.message.lower() for t in turns)
        
        for keyword in self.ESCALATION_KEYWORDS:
            if keyword in full_text:
                reasoning = f"Detected escalation keyword '{keyword}' in conversation."
                return True, reasoning
        
        reasoning = "No escalation keywords detected."
        return False, reasoning
    
    def compute_context_retention(self, turns: List[ConversationTurn]) -> Tuple[float, str]:
        """
        Compute context retention score based on entity reuse.
        Returns (score, reasoning)
        """
        if len(turns) < 2:
            return 1.0, "Insufficient turns to measure context retention."
        
        user_entities = set()
        bot_references = 0
        total_user_entities = 0
        
        for i, turn in enumerate(turns):
            if turn.role == "User":
                entities = self.extract_entities(turn.message)
                user_entities.update(entities)
                total_user_entities += len(entities)
            elif turn.role == "Bot" and user_entities:
                # Check if bot references user entities
                for entity in user_entities:
                    if entity.lower() in turn.message.lower():
                        bot_references += 1
        
        if total_user_entities == 0:
            return 1.0, "No user entities found to track."
        
        retention_score = min(bot_references / max(len(user_entities), 1), 1.0)
        reasoning = f"Bot referenced {bot_references}/{len(user_entities)} user entities."
        return round(retention_score, 3), reasoning
        
    def check_intent_match(self, case_intent: str, gt_intent: str) -> bool:
        """
        Check if case_intent matches Ground Truth intent.
        Simple fuzzy matching.
        """
        if not case_intent or not gt_intent:
            return False
        
        return case_intent.lower() in gt_intent.lower() or gt_intent.lower() in case_intent.lower()

    def compute_all(
        self, 
        multi_turn_text: str,
        case_intent: str = "",
        gt_intent: str = ""
    ) -> RuleMetrics:
        """
        Compute all rule-based metrics for a conversation.
        """
        # Parse conversation
        turns = self.parse_conversation(multi_turn_text)
        
        # Initialize reasoning dictionary
        metric_reasoning = {}
        
        # Compute metrics with reasoning
        total, user_count, bot_count, turn_reasoning = self.count_turns(turns)
        metric_reasoning["turn_count"] = turn_reasoning
        
        # Full text
        full_text = ' '.join(t.message for t in turns)
        pii_count, pii_types, pii_reasoning = self.detect_pii(full_text)
        metric_reasoning["pii_exposure_count"] = pii_reasoning
        
        # Entity extraction
        entities = self.extract_entities(full_text)
        order_numbers = self.detect_order_numbers(full_text)
        
        # Context retention
        context_score, context_reasoning = self.compute_context_retention(turns)
        metric_reasoning["context_retention_score"] = context_reasoning
        
        # Customer effort
        effort_score, effort_reasoning = self.compute_customer_effort(turns)
        metric_reasoning["customer_effort_score"] = effort_reasoning
        
        # Resolution
        resolution, resolution_reasoning = self.detect_resolution(turns)
        metric_reasoning["resolution_detected"] = resolution_reasoning
        
        # Escalation
        escalation, escalation_reasoning = self.detect_escalation(turns)
        metric_reasoning["escalation_detected"] = escalation_reasoning
        
        # Intent accuracy
        intent_matched = self.check_intent_match(case_intent, gt_intent)
        if not case_intent or not gt_intent:
            metric_reasoning["intent_accuracy"] = "No intent information provided for comparison."
        elif intent_matched:
            metric_reasoning["intent_accuracy"] = f"Case intent '{case_intent[:50]}' matches ground truth intent."
        else:
            metric_reasoning["intent_accuracy"] = f"Case intent '{case_intent[:50]}' does not match ground truth intent."
        
        return RuleMetrics(
            turn_count=total,
            user_turn_count=user_count,
            bot_turn_count=bot_count,
            context_retention_score=context_score,
            pii_exposure_count=pii_count,
            pii_types=pii_types,
            customer_effort_score=effort_score,
            resolution_detected=resolution,
            escalation_detected=escalation,
            intent_matched=intent_matched,
            entities_found=entities,
            order_numbers=order_numbers,
            metric_reasoning=metric_reasoning
        )
    
    def to_dict(self, metrics: RuleMetrics) -> Dict[str, Any]:
        """Convert RuleMetrics to dictionary"""
        result = {
            "turn_count": metrics.turn_count,
            "user_turn_count": metrics.user_turn_count,
            "bot_turn_count": metrics.bot_turn_count,
            "context_retention_score": metrics.context_retention_score,
            "pii_exposure_count": metrics.pii_exposure_count,
            "pii_types": metrics.pii_types,
            "customer_effort_score": metrics.customer_effort_score,
            "resolution_detected": metrics.resolution_detected,
            "escalation_detected": metrics.escalation_detected,
            "intent_accuracy": 100.0 if metrics.intent_matched else 0.0,
            "entities_found": metrics.entities_found,
            "order_numbers": metrics.order_numbers
        }
        return result
    
    def get_reasoning(self, metrics: RuleMetrics) -> Dict[str, str]:
        """Get reasoning dictionary from RuleMetrics"""
        return metrics.metric_reasoning if metrics.metric_reasoning else {}
