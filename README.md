# Log Analyzer Agent

AI-powered log evaluation system that analyzes chatbot logs using 18 comprehensive metrics with LangChain and Google Gemini.

## Features

- **18 Evaluation Metrics** covering accuracy, relevance, completeness, tone, security, and more
- **Correct Comparison Logic**: Agent vs Human (ground truth), Agent vs User (query), Agent-only (security)
- **Modern React Dashboard** with dark theme and professional styling
- **File Upload** supporting JSON and CSV formats
- **Upload History** sidebar for easy file management
- **Excel Export** with styled formatting
- **LangChain Integration** with Google Gemini 2.5 Flash

## Project Structure

```
log_analyzer_agent/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── main.py            # FastAPI application
│   │   ├── models.py          # Pydantic models
│   │   ├── routes/            # API endpoints
│   │   ├── services/          # Business logic
│   │   └── prompts/           # LangChain prompt templates
│   ├── requirements.txt
│   └── run.py
├── frontend/                   # React frontend
│   ├── src/
│   │   ├── components/        # React components
│   │   ├── services/          # API integration
│   │   ├── App.jsx
│   │   └── index.css
│   ├── package.json
│   └── vite.config.js
└── sample_logs.json           # Sample test data
```

## Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+
- Google API Key (for Gemini)

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variable
# Create .env file with:
# GOOGLE_API_KEY=your_api_key_here

# Run the server
python run.py
```

The backend will be available at `http://localhost:8000`

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

The frontend will be available at `http://localhost:5173`

## Log File Format

### JSON Format

```json
[
  {
    "user": "How do I reset my password?",
    "human": "You can reset your password by clicking on 'Forgot Password'...",
    "agent": "To reset your password, go to the login page..."
  }
]
```

### CSV Format

```csv
user,human,agent
"How do I reset my password?","You can reset...","To reset..."
```

## Metrics Evaluated

| Category | Metrics |
|----------|---------|
| Agent vs Human | Response Accuracy, Intent Accuracy, Completeness Score, Clarity Score |
| Agent vs User | Answer Relevancy, Context Retention, Tone Appropriateness, Customer Effort Score |
| Agent-only | Hallucination Rate, PII Exposure Count, PII Handling Compliance, Overconfidence, Incorrect Refusal Rate, Refusal Correctness |
| Aggregate | Average Latency, Average Turns to Resolution, Escalation Rate, Resolution Rate |

## API Endpoints

- `POST /api/upload/` - Upload a log file
- `GET /api/upload/history` - Get upload history
- `POST /api/metrics/{file_id}/evaluate` - Evaluate a file
- `GET /api/metrics/{file_id}` - Get cached results
- `GET /api/export/{file_id}/excel` - Export to Excel

## License

MIT
