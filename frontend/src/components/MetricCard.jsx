import React from 'react';
import './MetricCard.css';

const MetricCard = ({ title, value, status = 'good', showIndicator = true, format = 'number' }) => {
    // Format value based on type
    const formatValue = (val) => {
        if (format === 'percentage') {
            return (val * 100).toFixed(2) + '%';
        } else if (format === 'decimal') {
            return typeof val === 'number' ? val.toFixed(4) : val;
        }
        return val;
    };

    // Determine status class
    const getStatusClass = () => {
        if (status === 'critical') return 'status-critical';
        if (status === 'warning') return 'status-warning';
        return 'status-good';
    };

    return (
        <div className={`metric-card-dashboard ${getStatusClass()}`}>
            <div className="metric-header">
                <h3>{title}</h3>
            </div>
            <div className="metric-value-large">
                {formatValue(value)}
            </div>
            {showIndicator && (
                <div className="metric-indicator">
                    <div className={`indicator-bar ${getStatusClass()}`}></div>
                </div>
            )}
        </div>
    );
};

export default MetricCard;
