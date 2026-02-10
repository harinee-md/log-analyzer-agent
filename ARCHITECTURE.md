# System Architecture

## Overview
The Log Analyzer Agent is a hybrid evaluation system that combines deterministic rule-based logic with LLM-based semantic analysis to audit chatbot performance. The system processes conversation logs (Excel/CSV/JSON) and generates detailed metrics, binary classifications, and aggregated insights.

## Architecture Diagram

```mermaid
graph TD
    %% Client Layer
    subgraph Client ["Frontend (React)"]
        UI[User Interface]
        Upload[Log Upload Component]
        Dashboard[Results Dashboard]
    end

    %% Backend Layer
    subgraph Backend ["Backend (FastAPI)"]
        API[API Router]
        
        subgraph Pipeline ["Log Analyzer Pipeline"]
            Orchestrator[Pipeline Orchestrator]
            
            subgraph DataProc ["Data Processing"]
                Ingest[Log Parser]
                Norm[Data Normalizer]
            end
            
            subgraph Engines ["Evaluation Engines"]
                RuleBased[Rule Engine<br/>(Regex/Heuristic)]
                LLMBased[Metric Evaluator<br/>(LangChain + OpenAI)]
            end
            
            subgraph PostProc ["Post-Processing"]
                Labeler[Binary Labeler]
                Scorer[Metric Normalizer]
                Agg[Aggregator]
            end
        end
        
        Cache[(In-Memory Cache)]
    end

    %% External Services
    subgraph External ["External Services"]
        OpenAI[OpenAI API<br/>(GPT-4o-mini)]
    end

    %% Data Flow
    UI -->|1. Upload File| Upload
    Upload -->|2. POST /analyze| API
    API -->|3. Init| Orchestrator
    
    Orchestrator -->|4. Raw Data| Ingest
    Ingest -->|5. DataFrame| Norm
    Norm -->|6. Normalized Convos| Orchestrator
    
    Orchestrator -->|7. Multi-Turn Text| RuleBased
    Orchestrator -->|8. Log Entries| LLMBased
    
    LLMBased <-->|9. API Calls| OpenAI
    
    RuleBased -->|10. Rule Metrics| Orchestrator
    LLMBased -->|11. Semantic Metrics| Orchestrator
    
    Orchestrator -->|12. Combined Metrics| Labeler
    Labeler -->|13. TP/TN/FP/FN| Scorer
    Scorer -->|14. Composite Score| Agg
    
    Agg -->|15. JSON Result| Orchestrator
    Orchestrator -->|16. Cache Result| Cache
    API -->|17. Return JSON| Dashboard
```

## Component Details

### 1. Frontend (React)
- **Upload Component**: Handles file selection and sends `FormData` to the backend.
- **Dashboard**: Visualizes metrics, displays conversation drill-downs, and shows reasoning for scores.

### 2. Backend (FastAPI)
- **API Router**: Exposes endpoints for analysis (`/analyze`), result retrieval (`/results`), and export.
- **Pipeline Orchestrator** (`LogAnalyzerPipeline`): Manages the flow of data through all stages.
- **Data Normalizer**: Converts various input formats (Genesys, standard CSV, etc.) into a unified `NormalizedConversation` structure.
- **Rule Engine**:
  - Uses Regex for **PII Detection** (Email, Phone, SSN).
  - Uses Heuristics for **Customer Effort** (turn count, questions).
  - Detects **Resolution** and **Escalation** keywords.
  - Computes **Context Retention** via entity tracking.
- **Metric Evaluator**:
  - Uses `LangChain` and `ChatOpenAI` (GPT-4o-mini).
  - Evaluates semantic metrics: **Empathy, Hallucination, Response Accuracy, Completeness**.
- **Binary Labeler**: Classifies conversations into **True Positive (Successful)**, **True Negative (Correct logic)**, **False Positive (Hallucination)**, or **False Negative (Missed opportunity)**.
- **Aggregator**: Computes statistics at three levels:
  - **Turn Level**: Individual message analysis.
  - **Conversation Level**: Full interaction summary.
  - **Scenario Level**: Use-case specific performance (e.g., "Password Reset" vs. "Billing").

### 3. External Services
- **OpenAI API**: The system relies on `gpt-4o-mini` for high-accuracy semantic evaluation where rule-based logic is insufficient.
