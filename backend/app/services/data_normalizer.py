"""
Data Normalizer Service

Normalizes log file data into structured conversation format:
- Parses multi-turn conversations
- Extracts ground truth from email JSON
- Structures data for downstream processing
"""

import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from pydantic import BaseModel


class ConversationTurn(BaseModel):
    """Single turn in a conversation"""
    role: str  # "Bot" or "User"
    message: str
    is_action: bool = False


class GroundTruthEmail(BaseModel):
    """Parsed ground truth email"""
    email_index: int
    body: str
    conversation_id: Optional[str] = None


class NormalizedConversation(BaseModel):
    """Fully normalized conversation with all components"""
    conversation_id: str
    turns: List[ConversationTurn]
    case_intent: str
    ground_truth_emails: List[GroundTruthEmail]
    download_action_score: Optional[float] = None
    download_intent_score: Optional[float] = None
    raw_multi_turn: str = ""


class DataNormalizer:
    """
    Normalizes raw log data into structured conversation format.
    """
    
    def parse_multi_turn_conversation(self, text: str) -> List[ConversationTurn]:
        """
        Parse multi-turn conversation text into structured turns.
        
        Expected format:
        Bot: message
        User: message
        Bot: {"quickReplies": ...}
        """
        if not text or not isinstance(text, str):
            return []
        
        turns = []
        lines = text.strip().split('\n')
        current_role = None
        current_message = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check for role prefix
            if line.startswith("Bot:"):
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
                if current_role:
                    current_message.append(line)
        
        # Add last turn
        if current_role and current_message:
            msg = '\n'.join(current_message).strip()
            is_action = msg.startswith('{') and '"' in msg
            turns.append(ConversationTurn(
                role=current_role,
                message=msg,
                is_action=is_action
            ))
        
        return turns
    
    def parse_ground_truth_json(self, gt_json: str) -> tuple[str, str, List[GroundTruthEmail]]:
        """
        Parse ground truth emails JSON.
        
        Returns: (case_number, subject, list of emails)
        """
        if not gt_json or not isinstance(gt_json, str):
            return "", "", []
        
        try:
            data = json.loads(gt_json)
            
            case_number = data.get("case_number", "")
            subject = data.get("subject", "")
            
            emails = []
            for email_data in data.get("emails", []):
                emails.append(GroundTruthEmail(
                    email_index=email_data.get("email_index", 0),
                    body=email_data.get("body", ""),
                    conversation_id=email_data.get("conversation_id")
                ))
            
            return case_number, subject, emails
        
        except json.JSONDecodeError:
            return "", "", []
    
    def normalize_row(
        self,
        row_id: str,
        multi_turn_conv: str,
        case_intent: str,
        ground_truth_emails: str,
        download_action_score: Optional[float] = None,
        download_intent_score: Optional[float] = None
    ) -> NormalizedConversation:
        """
        Normalize a single row from the log file.
        
        Args:
            row_id: Unique identifier for the row
            multi_turn_conv: Raw multi-turn conversation text
            case_intent: Case intent/summary
            ground_truth_emails: JSON string with GT emails
            download_action_score: Binary score from file
            download_intent_score: Binary score from file
            
        Returns:
            NormalizedConversation with all parsed components
        """
        # Parse conversation turns
        turns = self.parse_multi_turn_conversation(multi_turn_conv)
        
        # Parse ground truth
        case_number, subject, gt_emails = self.parse_ground_truth_json(ground_truth_emails)
        
        # Use case_intent from column, fallback to subject from JSON
        final_intent = case_intent if case_intent else subject
        
        return NormalizedConversation(
            conversation_id=row_id or case_number,
            turns=turns,
            case_intent=final_intent,
            ground_truth_emails=gt_emails,
            download_action_score=download_action_score,
            download_intent_score=download_intent_score,
            raw_multi_turn=multi_turn_conv or ""
        )
    
    def normalize_dataframe(self, df) -> List[NormalizedConversation]:
        """
        Normalize all rows from a pandas DataFrame.
        
        Expected columns:
        - example.multi_turn_conv
        - example.case_intent
        - example.ground_truth_emails
        - Download Action chat.score
        - Download intent GT Email.score
        """
        normalized = []
        
        for idx, row in df.iterrows():
            conv = self.normalize_row(
                row_id=f"conv_{idx}",
                multi_turn_conv=row.get("example.multi_turn_conv", ""),
                case_intent=row.get("example.case_intent", ""),
                ground_truth_emails=row.get("example.ground_truth_emails", ""),
                download_action_score=row.get("Download Action chat.score"),
                download_intent_score=row.get("Download intent GT Email.score")
            )
            normalized.append(conv)
        
        return normalized
    
    def get_bot_messages(self, turns: List[ConversationTurn]) -> List[str]:
        """Extract all bot messages from turns"""
        return [t.message for t in turns if t.role == "Bot" and not t.is_action]
    
    def get_user_messages(self, turns: List[ConversationTurn]) -> List[str]:
        """Extract all user messages from turns"""
        return [t.message for t in turns if t.role == "User"]
    
    def get_ground_truth_text(self, gt_emails: List[GroundTruthEmail]) -> str:
        """Combine all GT email bodies into single text"""
        return "\n\n".join(email.body for email in gt_emails)
