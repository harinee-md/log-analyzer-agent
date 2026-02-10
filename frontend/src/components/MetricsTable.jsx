import React from 'react';

// Static explanations for how each metric is calculated and what the score means
const METRIC_EXPLANATIONS = {
    'turn_count': 'Rule-based: Average number of conversation turns. Higher = longer conversations. Normalized to 0-1 scale (0.4 = ~4 turns avg).',
    'context_retention_score': 'Rule-based: Measures how well bot references user entities. Score 0-1 where 1.0 = perfect retention, 0.4 = 40% of entities referenced.',
    'pii_exposure_count': 'Rule-based: Detects sensitive data (emails, phones, SSN). Score 0-1 where 0 = no PII exposed, higher = more PII detected. 0.9 = high exposure.',
    'customer_effort_score': 'Rule-based: User effort based on turns & questions. Score 0-1 where 0 = minimal effort (good), 0.5 = moderate effort, 1 = high effort (bad).',
    'resolution_detected': 'Rule-based: % of conversations with resolution keywords. Score 0-1 where 1.0 = all resolved, 0.6 = 60% had resolution keywords.',
    'escalation_detected': 'Rule-based: % of conversations escalated to human. Score 0-1 where 0 = no escalations (good), 1.0 = all escalated (bad).',
    'intent_accuracy': 'Rule-based: % of intents matching ground truth. Score 0-1 where 1.0 = 100% match, 0.7 = 70% accuracy.',
    'response_accuracy': 'LLM-based: Gemini rates response correctness. Score 0-1 where 1.0 = perfect accuracy, 0.8 = 80% accurate, <0.5 = poor.',
    'answer_relevancy': 'LLM-based: Gemini rates relevance to query. Score 0-1 where 1.0 = fully relevant, 0.7 = mostly relevant, <0.5 = off-topic.',
    'completeness_score': 'LLM-based: Gemini checks if query fully addressed. Score 0-1 where 1.0 = complete answer, 0.5 = partial, <0.3 = incomplete.',
    'clarity_score': 'LLM-based: Gemini rates response clarity. Score 0-1 where 1.0 = crystal clear, 0.7 = good, <0.5 = confusing.',
    'tone_appropriateness': 'LLM-based: Gemini evaluates professionalism. Score 0-1 where 1.0 = perfect tone, 0.8 = good, <0.5 = inappropriate.',
    'hallucination_rate': 'LLM-based: % of responses with made-up info. Score 0-1 where 0 = no hallucination (good), 0.3 = 30% had false info (bad).',
    'incorrect_refusal_rate': 'LLM-based: % of wrong refusals. Score 0-1 where 0 = no incorrect refusals (good), 0.2 = 20% wrongly refused.',
    'overconfidence': 'LLM-based: % showing unwarranted certainty. Score 0-1 where 0 = appropriate confidence (good), 0.5 = half were overconfident.',
    'pii_handling_compliance': 'LLM-based: PII handling compliance rate. Score 0-1 where 1.0 = fully compliant (good), 0.7 = 70% compliant.',
    'refusal_correctness': 'LLM-based: Appropriateness of refusals. Score 0-1 where 1.0 = all refusals correct, 0.5 = mixed results.'
};

const MetricsTable = ({ metrics, filename, isLoading, onExport, isExporting }) => {
    // Determine value styling based on metric type
    const getValueClass = (metricName, value) => {
        const numValue = parseFloat(String(value));

        if (!isNaN(numValue)) {
            // Inverse metrics (lower is better)
            if (metricName.includes('hallucination') ||
                metricName.includes('pii_exposure') ||
                metricName.includes('incorrect_refusal') ||
                metricName.includes('overconfidence') ||
                metricName.includes('customer_effort')) {
                if (numValue <= 0.2) return 'good';
                if (numValue <= 0.5) return 'warning';
                return 'bad';
            }
            // Regular metrics (higher is better)
            if (numValue >= 0.8) return 'good';
            if (numValue >= 0.5) return 'warning';
            if (numValue < 0.3) return 'bad';
        }
        return '';
    };

    const formatMetricName = (name) => {
        return name
            .replace(/_/g, ' ')
            .replace(/\b\w/g, l => l.toUpperCase());
    };

    const formatValue = (value) => {
        if (typeof value === 'number') {
            return value.toFixed(4);
        }
        return String(value);
    };

    const getExplanation = (metricName) => {
        return METRIC_EXPLANATIONS[metricName] || 'Computed by the evaluation pipeline.';
    };

    if (isLoading) {
        return (
            <div className="metrics-section">
                <div className="metrics-header">
                    <div>
                        <h2 className="metrics-title">Evaluation Results</h2>
                        <p className="metrics-file-info">{filename}</p>
                    </div>
                </div>
                <div className="loading-container">
                    <div className="loading-spinner"></div>
                    <p className="loading-text">Evaluating metrics with AI... This may take a moment.</p>
                </div>
            </div>
        );
    }

    if (!metrics || metrics.length === 0) {
        return (
            <div className="metrics-section">
                <div className="empty-state">
                    <div className="empty-state-icon">📋</div>
                    <h3 className="empty-state-title">No metrics to display</h3>
                    <p>Upload a file and click "Evaluate" to generate metrics</p>
                </div>
            </div>
        );
    }

    return (
        <div className="metrics-section">
            <div className="metrics-header">
                <div>
                    <h2 className="metrics-title">Evaluation Results</h2>
                    <p className="metrics-file-info">📄 {filename} • {metrics.length} metrics</p>
                </div>
            </div>

            <div className="metrics-table-container" style={{ maxHeight: '700px', overflowY: 'auto' }}>
                <table className="metrics-table">
                    <thead>
                        <tr>
                            <th style={{ width: '25%' }}>Metric Name</th>
                            <th style={{ width: '15%' }}>Value</th>
                            <th style={{ width: '60%' }}>How It's Calculated</th>
                        </tr>
                    </thead>
                    <tbody>
                        {metrics.map((metric, index) => (
                            <tr key={index}>
                                <td className="metric-name">{formatMetricName(metric.metric_name)}</td>
                                <td className={`metric-value ${getValueClass(metric.metric_name, metric.metric_value)}`}>
                                    {formatValue(metric.metric_value)}
                                </td>
                                <td style={{
                                    color: '#94a3b8',
                                    fontSize: '0.85rem',
                                    lineHeight: '1.5',
                                    padding: '0.75rem'
                                }}>
                                    {getExplanation(metric.metric_name)}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            <div className="actions-bar">
                <button
                    className="btn btn-success"
                    onClick={onExport}
                    disabled={isExporting}
                >
                    <span className="btn-icon">{isExporting ? '⏳' : '📥'}</span>
                    {isExporting ? 'Generating Excel...' : 'Download Excel'}
                </button>
            </div>
        </div>
    );
};

export default MetricsTable;
