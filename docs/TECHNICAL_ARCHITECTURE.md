# Log Analyzer Agent - Technical Architecture Documentation

## Executive Summary

The **Log Analyzer Agent** is a hybrid AI evaluation system that analyzes chatbot conversation logs to assess performance quality. It combines **rule-based pattern matching** with **LLM-powered semantic analysis** (Google Gemini) to provide comprehensive quality metrics.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND                                    │
│                         React + Vite (Port 5173)                        │
├─────────────────────────────────────────────────────────────────────────┤
│  FileUpload.jsx  │  MetricsTable.jsx  │  HistorySidebar.jsx  │  App.jsx │
└─────────────────────────┬───────────────────────────────────────────────┘
                          │ HTTP (REST API)
                          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                              BACKEND                                     │
│                      FastAPI + Python (Port 5000)                        │
├─────────────────────────────────────────────────────────────────────────┤
│                           API Routes Layer                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐  │
│  │ /api/upload  │  │ /api/pipeline│  │ /api/metrics │  │ /api/export │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  └─────────────┘  │
├─────────────────────────────────────────────────────────────────────────┤
│                         Services Layer                                   │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    LogAnalyzerPipeline                          │    │
│  │  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────────────┐│    │
│  │  │   Data    │ │   Rule    │ │   LLM     │ │    Aggregator    ││    │
│  │  │Normalizer │ │  Engine   │ │ Evaluator │ │                  ││    │
│  │  └───────────┘ └───────────┘ └───────────┘ └───────────────────┘│    │
│  └─────────────────────────────────────────────────────────────────┘    │
│  ┌───────────────┐ ┌───────────────┐ ┌────────────────────────────┐     │
│  │ BinaryLabeler │ │MetricNormalizer│ │      ExcelExporter        │     │
│  └───────────────┘ └───────────────┘ └────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         External Services                                │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │              Google Gemini API (gemini-2.5-flash)                │   │
│  │                   via LangChain Integration                      │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Frontend** | React 18 + Vite | UI for file upload, metrics display |
| **Backend** | FastAPI (Python 3.11+) | REST API, business logic |
| **LLM Integration** | LangChain + Google Gemini | Semantic evaluation |
| **Data Processing** | Pandas | Excel/CSV parsing, data manipulation |
| **Export** | OpenPyXL | Excel report generation |

---

## Data Flow - End to End Pipeline

### Stage 1: File Upload & Ingestion
```
User uploads Excel/CSV file
        ↓
POST /api/pipeline/analyze
        ↓
Pandas reads file → DataFrame
```

**Input Format Expected:**
| Column | Description |
|--------|-------------|
| `Case Intent` | User's intended action |
| `Multi Turn` | Full conversation text (Bot:/User: format) |
| `Ground Truth Emails` | Expected correct response (JSON) |
| `Download Action Score` | Optional pre-computed score |
| `Download Intent Score` | Optional pre-computed score |

---

### Stage 2: Data Normalization
**File:** `services/data_normalizer.py`

```python
class DataNormalizer:
    def normalize_dataframe(df) → List[NormalizedConversation]
```

**What it does:**
1. Standardizes column names (handles variations)
2. Parses multi-turn conversations into structured turns
3. Extracts ground truth from JSON format
4. Creates `NormalizedConversation` objects

**Output Structure:**
```python
@dataclass
class NormalizedConversation:
    conversation_id: str
    case_intent: str
    raw_multi_turn: str
    turns: List[Turn]
    ground_truth_emails: str
    download_action_score: Optional[float]
    download_intent_score: Optional[float]
```

---

### Stage 3: Rule-Based Feature Extraction
**File:** `services/rule_engine.py`

```python
class RuleEngine:
    def compute_all(multi_turn_text, case_intent, gt_intent) → RuleMetrics
```

**Metrics Computed:**

| Metric | Method | Patterns Used |
|--------|--------|---------------|
| Turn Count | `count_turns()` | Line counting |
| PII Detection | `detect_pii()` | Regex: email, phone, SSN, credit card |
| Context Retention | `compute_context_retention()` | Entity extraction + reference tracking |
| Customer Effort | `compute_customer_effort()` | Turn count + question frequency |
| Resolution Detection | `detect_resolution()` | Keywords: "resolved", "fixed", "thank you" |
| Escalation Detection | `detect_escalation()` | Keywords: "supervisor", "transfer" |
| Intent Accuracy | `check_intent_match()` | Fuzzy string matching |

**PII Patterns:**
```python
PII_PATTERNS = {
    "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    "phone": r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b',
    "ssn": r'\b\d{3}[-.\s]?\d{2}[-.\s]?\d{4}\b',
    "credit_card": r'\b(?:\d{4}[-.\s]?){3}\d{4}\b'
}
```

---

### Stage 4: LLM-Based Semantic Evaluation
**File:** `services/evaluator.py`

```python
class MetricEvaluator:
    def __init__(api_key):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.1  # Low for consistent evaluation
        )
```

**LLM Metrics & Prompts:**

| Metric | Prompt Template | Output Format |
|--------|-----------------|---------------|
| Response Accuracy | Compare agent vs ground truth | `{"score": 0-100, "reasoning": "..."}` |
| Answer Relevancy | Rate relevance to query | `{"score": 0-100, "reasoning": "..."}` |
| Completeness | Check if fully addressed | `{"score": 0-100, "reasoning": "..."}` |
| Clarity | Rate readability | `{"score": 0-100, "reasoning": "..."}` |
| Tone Appropriateness | Evaluate professionalism | `{"score": 0-100, "reasoning": "..."}` |
| Hallucination | Detect fabricated info | `{"hallucination_detected": bool, "reasoning": "..."}` |
| Incorrect Refusal | Detect wrong refusals | `{"incorrect_refusal": bool, "reasoning": "..."}` |
| Overconfidence | Check certainty level | `{"overconfidence_detected": bool, "reasoning": "..."}` |

**Prompt Example (Response Accuracy):**
```python
METRIC_PROMPTS["response_accuracy"] = """
You are evaluating a customer service bot response.

User Query: {user_query}
Expected Response (Ground Truth): {human_response}
Bot Response: {agent_response}

Rate the accuracy of the bot response compared to ground truth.
Return JSON: {"score": 0-100, "reasoning": "explanation"}
"""
```

---

### Stage 5: Binary Labeling (TP/TN/FP/FN)
**File:** `services/binary_labeler.py`

```python
class BinaryLabeler:
    def classify_from_metrics(rule_metrics, llm_metrics, response, gt) → LabelResult
```

**Classification Logic:**
```
IF bot_responded AND response_matches_ground_truth → TP (True Positive)
IF bot_refused AND should_have_refused → TN (True Negative)  
IF bot_responded AND response_wrong → FP (False Positive)
IF bot_refused AND should_have_responded → FN (False Negative)
```

---

### Stage 6: Metric Normalization
**File:** `services/metric_normalizer.py`

```python
class MetricNormalizer:
    def normalize_metrics(raw_metrics) → Dict[str, float]  # All 0-1 scale
    def compute_composite_score(normalized) → float
    def get_quality_grade(score) → str  # A/B/C/D/F
```

**Normalization Rules:**
| Metric Type | Normalization |
|-------------|---------------|
| Percentage (0-100) | Divide by 100 |
| Count-based | Sigmoid or min-max |
| Boolean | 1.0 or 0.0 |
| Effort scores | Invert (1 - score) for display |

**Composite Score Weights:**
```python
METRIC_WEIGHTS = {
    'response_accuracy': 0.15,
    'answer_relevancy': 0.12,
    'completeness_score': 0.10,
    'clarity_score': 0.08,
    'tone_appropriateness': 0.08,
    'hallucination_rate': 0.12,  # Inverted
    'context_retention_score': 0.08,
    # ... etc
}
```

---

### Stage 7: Aggregation
**File:** `services/aggregator.py`

```python
class Aggregator:
    def aggregate_conversation(...) → ConversationMetrics
    def aggregate_by_scenario(conversations) → List[ScenarioMetrics]
    def compute_overall(conversations) → (metrics, labels, score)
    def to_dict(results) → Dict  # JSON-serializable
```

**Aggregation Levels:**
1. **Turn Level** - Per-message metrics
2. **Conversation Level** - Per-conversation rollup with reasoning
3. **Scenario Level** - Grouped by intent category
4. **Overall Level** - Global averages

**Output JSON Structure:**
```json
{
  "total_conversations": 50,
  "overall": {
    "metrics": {...},
    "label_distribution": {"TP": 30, "FP": 10, "TN": 5, "FN": 5},
    "composite_score": 0.72
  },
  "conversation_level": [
    {
      "id": "conv_1",
      "metrics": {...},
      "reasoning": {
        "turn_count": "Counted 6 turns...",
        "response_accuracy": "LLM evaluation..."
      },
      "label": "TP",
      "grade": "B"
    }
  ]
}
```

---

### Stage 8: Excel Export
**File:** `services/excel_exporter.py`

Generates formatted Excel with:
- Summary sheet (overall metrics)
- Conversation details sheet
- Metrics breakdown sheet
- Charts (optional)

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/pipeline/analyze` | POST | Main analysis endpoint |
| `/api/pipeline/{id}/results` | GET | Get cached results |
| `/api/pipeline/{id}/conversation/{conv_id}` | GET | Single conversation details |
| `/api/upload/history` | GET | List uploaded files |
| `/api/export/excel/{file_id}` | GET | Download Excel report |

---

## Frontend Components

| Component | Purpose |
|-----------|---------|
| `App.jsx` | Main container, state management |
| `FileUpload.jsx` | Drag-drop file upload |
| `MetricsTable.jsx` | Display metrics with explanations |
| `HistorySidebar.jsx` | Upload history |

---

## Configuration

**Environment Variables:**
```bash
GOOGLE_API_KEY=your-gemini-api-key  # Required for LLM metrics
```

**Backend Config:**
```python
# run.py
uvicorn.run("app.main:app", host="0.0.0.0", port=5000, reload=True)
```

---

## File Structure

```
log-analyzer-agent/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app entry
│   │   ├── models.py            # Pydantic models
│   │   ├── routes/
│   │   │   ├── pipeline.py      # Main analysis endpoint
│   │   │   ├── upload.py        # File upload handling
│   │   │   └── export.py        # Excel export
│   │   ├── services/
│   │   │   ├── pipeline.py      # Orchestrator
│   │   │   ├── data_normalizer.py
│   │   │   ├── rule_engine.py
│   │   │   ├── evaluator.py     # LLM integration
│   │   │   ├── binary_labeler.py
│   │   │   ├── metric_normalizer.py
│   │   │   └── aggregator.py
│   │   └── prompts/
│   │       └── metric_prompts.py  # LLM prompt templates
│   ├── requirements.txt
│   └── run.py
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── components/
│   │   │   ├── MetricsTable.jsx
│   │   │   ├── FileUpload.jsx
│   │   │   └── HistorySidebar.jsx
│   │   └── services/
│   │       └── api.js           # API client
│   ├── package.json
│   └── vite.config.js
│
└── docs/
    ├── METRICS_DOCUMENTATION.md  # Client-facing docs
    └── TECHNICAL_ARCHITECTURE.md # This document
```

---

## Performance Considerations

| Factor | Implementation |
|--------|----------------|
| **LLM Rate Limiting** | Sequential calls with error handling |
| **Caching** | In-memory cache for results |
| **Large Files** | Streaming upload, chunked processing |
| **Timeout** | 30s per LLM call, total timeout configurable |

---

## Security

- **API Key Protection**: Environment variable, not hardcoded
- **File Validation**: Only Excel/CSV accepted
- **PII Detection**: Logged but not stored externally
- **CORS**: Configured for frontend origin only

---

## Deployment

**Development:**
```bash
# Backend
cd backend && python run.py

# Frontend
cd frontend && npm run dev
```

**Production:**
```bash
# Backend
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app

# Frontend
npm run build && serve -s dist
```

---

*Document Version: 1.0 | Last Updated: February 2026*
