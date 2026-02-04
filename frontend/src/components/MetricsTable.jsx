import React from 'react';

const MetricsTable = ({ metrics, filename, isLoading, onExport, isExporting }) => {
    // Determine value styling based on metric type
    const getValueClass = (metricName, value) => {
        const strValue = String(value).toLowerCase();

        // Handle percentage values
        if (strValue.includes('%')) {
            const numValue = parseFloat(strValue);
            if (!isNaN(numValue)) {
                if (numValue >= 80) return 'good';
                if (numValue >= 50) return 'warning';
                return 'bad';
            }
        }

        // Handle specific metrics
        if (metricName.toLowerCase().includes('hallucination') ||
            metricName.toLowerCase().includes('pii exposure')) {
            if (strValue === '0' || strValue === '0%' || strValue === 'none detected') {
                return 'good';
            }
            return 'bad';
        }

        if (metricName.toLowerCase().includes('resolution') ||
            metricName.toLowerCase().includes('accuracy')) {
            if (strValue.includes('resolved') || parseFloat(strValue) >= 80) {
                return 'good';
            }
        }

        if (strValue === 'yes' &&
            (metricName.toLowerCase().includes('overconfidence') ||
                metricName.toLowerCase().includes('incorrect'))) {
            return 'bad';
        }

        if (strValue === 'no' &&
            (metricName.toLowerCase().includes('overconfidence') ||
                metricName.toLowerCase().includes('incorrect'))) {
            return 'good';
        }

        return '';
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

            <div className="metrics-table-container">
                <table className="metrics-table">
                    <thead>
                        <tr>
                            <th style={{ width: '50%' }}>Metric Name</th>
                            <th style={{ width: '50%' }}>Metric Value</th>
                        </tr>
                    </thead>
                    <tbody>
                        {metrics.map((metric, index) => (
                            <tr key={index}>
                                <td className="metric-name">{metric.metric_name}</td>
                                <td className={`metric-value ${getValueClass(metric.metric_name, metric.metric_value)}`}>
                                    {String(metric.metric_value)}
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
