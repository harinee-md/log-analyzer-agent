# AI Agent Evaluation Metrics - Client Documentation

## Overview

This document explains how each metric in the Log Analyzer evaluates your AI agent's performance. All scores are normalized to a **0-1 scale** where the meaning depends on the metric type.

---

## 📊 Score Interpretation Guide

| Score Range | For "Higher is Better" Metrics | For "Lower is Better" Metrics |
|-------------|-------------------------------|-------------------------------|
| **0.8 - 1.0** | ✅ Excellent | ⚠️ Needs Attention |
| **0.5 - 0.79** | ⚠️ Acceptable | ⚠️ Acceptable |
| **0.0 - 0.49** | ❌ Needs Improvement | ✅ Excellent |

---

## Rule-Based Metrics (Automated Detection)

These metrics use pattern matching and counting - no AI judgment involved.

### 1. Turn Count
**What it measures:** Average length of conversations (number of back-and-forth messages).

**How it works:** Counts all "User:" and "Bot:" message exchanges.

**Score meaning:**
- 0.4 = Average of ~4 turns per conversation
- Higher = Longer conversations (may indicate complex issues or inefficiency)
- Lower = Quick resolutions

**Example:**
```
User: What's my order status?
Bot: Your order #12345 shipped yesterday.
User: Thanks!
Bot: You're welcome!
```
This = 4 turns, normalized score ≈ 0.4

---

### 2. Context Retention Score
**What it measures:** How well the bot remembers and references information the user provided earlier.

**How it works:** Tracks entities (names, order numbers, etc.) mentioned by user, checks if bot references them later.

**Score meaning:**
- 1.0 = Bot referenced all user-provided entities ✅
- 0.6 = Bot referenced 60% of entities
- 0.0 = Bot never referenced user's information ❌

**Example:**
```
User: My name is John and order is #ABC123
Bot: Hi John, I see order #ABC123 was shipped.  ← References both entities ✅
```

---

### 3. PII Exposure Count
**What it measures:** Detection of sensitive personal information in conversations.

**How it works:** Pattern matching for emails, phone numbers, SSN, credit cards, IP addresses.

**Score meaning (LOWER IS BETTER):**
- 0.0 = No PII detected ✅
- 0.5 = Moderate PII exposure
- 0.9+ = High PII exposure ❌

**Detected patterns:**
- Email: `john@example.com`
- Phone: `555-123-4567`
- SSN: `123-45-6789`
- Credit Card: `4111-1111-1111-1111`

---

### 4. Customer Effort Score
**What it measures:** How much effort the customer had to exert to get help.

**How it works:** Based on number of user messages and questions asked.

**Score meaning (LOWER IS BETTER):**
- 0.0-0.3 = Low effort, quick resolution ✅
- 0.4-0.6 = Moderate effort
- 0.7-1.0 = High effort, customer struggled ❌

**Example:**
- 2 user messages, 0 questions = Low effort (0.12)
- 8 user messages, 5 questions = High effort (0.76)

---

### 5. Resolution Detected
**What it measures:** Whether the conversation ended with a resolution.

**How it works:** Scans last 3 messages for keywords like: "resolved", "fixed", "thank you", "that works", "perfect", "great".

**Score meaning:**
- 1.0 = 100% of conversations showed resolution ✅
- 0.6 = 60% had resolution keywords
- 0.0 = No resolutions detected ❌

---

### 6. Escalation Detected
**What it measures:** Whether the conversation required human agent intervention.

**How it works:** Detects keywords like: "transfer", "supervisor", "human agent", "speak to someone", "real person".

**Score meaning (LOWER IS BETTER):**
- 0.0 = No escalations needed ✅
- 0.3 = 30% escalated
- 1.0 = All conversations escalated ❌

---

### 7. Intent Accuracy
**What it measures:** Whether the bot correctly understood what the user wanted.

**How it works:** Compares detected intent against ground truth intent using fuzzy matching.

**Score meaning:**
- 1.0 = 100% intent match ✅
- 0.7 = 70% accuracy
- 0.0 = Intent never matched ❌

---

## LLM-Based Metrics (AI Judgment)

These metrics use Google Gemini to evaluate conversation quality with human-like judgment.

### 8. Response Accuracy
**What it measures:** Whether the bot's response is factually correct compared to the expected answer.

**How it works:** Gemini compares agent response to ground truth and rates correctness.

**Score meaning:**
- 0.9-1.0 = Highly accurate ✅
- 0.7-0.89 = Mostly accurate
- <0.5 = Significant inaccuracies ❌

**Example:**
```
User: What's the return policy?
Ground Truth: 30-day returns with receipt
Bot Response: You can return within 30 days if you have your receipt.
```
Score: ~0.95 (accurate paraphrase)

---

### 9. Answer Relevancy
**What it measures:** How relevant the bot's answer is to the user's question.

**How it works:** Gemini evaluates if the response addresses the actual query.

**Score meaning:**
- 1.0 = Directly answers the question ✅
- 0.6 = Partially relevant
- <0.3 = Off-topic response ❌

**Example:**
```
User: How do I reset my password?
Bot: To reset your password, go to Settings > Security > Reset.  ← Relevant ✅
Bot: Our store hours are 9-5.  ← Irrelevant ❌
```

---

### 10. Completeness Score
**What it measures:** Whether all parts of the user's question were fully addressed.

**How it works:** Gemini checks if multi-part questions received complete answers.

**Score meaning:**
- 1.0 = All parts answered ✅
- 0.5 = Partial answer
- <0.3 = Key information missing ❌

**Example:**
```
User: What's the price AND available colors?
Bot: It costs $50.  ← Incomplete (0.5), missing colors
Bot: It costs $50 and comes in red, blue, green.  ← Complete (1.0) ✅
```

---

### 11. Clarity Score
**What it measures:** How clear and easy to understand the bot's response is.

**How it works:** Gemini rates readability, structure, and simplicity.

**Score meaning:**
- 0.9-1.0 = Crystal clear ✅
- 0.6-0.8 = Understandable
- <0.5 = Confusing or unclear ❌

---

### 12. Tone Appropriateness
**What it measures:** Whether the bot's tone is professional and empathetic.

**How it works:** Gemini evaluates politeness, empathy, and professionalism.

**Score meaning:**
- 0.9-1.0 = Perfect professional tone ✅
- 0.6-0.8 = Acceptable tone
- <0.5 = Inappropriate or rude ❌

---

### 13. Hallucination Rate
**What it measures:** Whether the bot made up information not in the ground truth.

**How it works:** Gemini checks if response contains fabricated facts.

**Score meaning (LOWER IS BETTER):**
- 0.0 = No hallucinations ✅
- 0.3 = 30% had made-up info
- 0.5+ = Serious hallucination problem ❌

**Example:**
```
Ground Truth: Product weighs 2 lbs
Bot: The product weighs 5 lbs and comes with free batteries.
```
Hallucination detected: Wrong weight, invented "free batteries" ❌

---

### 14. Incorrect Refusal Rate
**What it measures:** Whether the bot wrongly refused a valid request.

**How it works:** Gemini detects if bot said "I can't help" when it should have helped.

**Score meaning (LOWER IS BETTER):**
- 0.0 = No incorrect refusals ✅
- 0.2 = 20% wrongly refused
- 0.5+ = Major refusal problem ❌

---

### 15. Overconfidence
**What it measures:** Whether the bot expressed unwarranted certainty.

**How it works:** Gemini checks for absolute statements when uncertainty was appropriate.

**Score meaning (LOWER IS BETTER):**
- 0.0 = Appropriate confidence ✅
- 0.3 = Some overconfident statements
- 0.5+ = Frequently overconfident ❌

---

### 16. PII Handling Compliance
**What it measures:** Whether the bot properly handled requests for sensitive information.

**How it works:** Gemini evaluates if bot appropriately refused or handled PII requests.

**Score meaning:**
- 1.0 = Fully compliant ✅
- 0.7 = Mostly compliant
- <0.5 = Compliance issues ❌

---

### 17. Refusal Correctness
**What it measures:** When the bot refused, was it appropriate to do so?

**How it works:** Gemini evaluates if refusals were justified.

**Score meaning:**
- 1.0 = All refusals were correct ✅
- 0.5 = Mixed results
- <0.3 = Many inappropriate refusals ❌

---

## Composite Score & Grading

The **Composite Score** is a weighted average of all metrics, giving you one overall quality number.

| Grade | Score Range | Meaning |
|-------|-------------|---------|
| A | 0.85 - 1.00 | Excellent performance |
| B | 0.70 - 0.84 | Good performance |
| C | 0.55 - 0.69 | Acceptable, needs improvement |
| D | 0.40 - 0.54 | Below expectations |
| F | < 0.40 | Critical issues |

---

## Binary Labels

Each conversation is classified as:

| Label | Meaning |
|-------|---------|
| **TP** (True Positive) | Bot gave correct response, should have responded |
| **TN** (True Negative) | Bot correctly refused/escalated |
| **FP** (False Positive) | Bot responded but gave wrong answer |
| **FN** (False Negative) | Bot refused when it should have answered |

---

## Quick Reference: What's Good?

| Metric | Good Score | Bad Score |
|--------|------------|-----------|
| Response Accuracy | > 0.8 | < 0.5 |
| Answer Relevancy | > 0.8 | < 0.5 |
| Completeness | > 0.8 | < 0.5 |
| Clarity | > 0.8 | < 0.5 |
| Tone | > 0.8 | < 0.5 |
| Context Retention | > 0.7 | < 0.4 |
| Resolution Detected | > 0.7 | < 0.4 |
| Intent Accuracy | > 0.8 | < 0.5 |
| **Hallucination** | < 0.1 | > 0.3 |
| **Incorrect Refusal** | < 0.1 | > 0.2 |
| **Customer Effort** | < 0.3 | > 0.6 |
| **Escalation** | < 0.2 | > 0.5 |
| **PII Exposure** | 0.0 | > 0.1 |

---

*Document generated for Log Analyzer Agent v1.0*
