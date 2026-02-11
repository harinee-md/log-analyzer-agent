import React from 'react';
import './FunnelChart.css';

const FunnelChart = ({ totalConversations, resolutionRate, escalationRate }) => {
    // Calculate counts
    const total = totalConversations || 0;
    const resolved = Math.round(total * (resolutionRate || 0));
    const escalated = Math.round(total * (escalationRate || 0));

    // Calculate percentages
    const resolvedPercent = total > 0 ? Math.round((resolved / total) * 100) : 0;
    const escalatedPercent = total > 0 ? Math.round((escalated / total) * 100) : 0;

    return (
        <div className="funnel-chart-container">
            <h3 className="chart-title">Conversation Flow</h3>
            <div className="funnel-wrapper">
                <div className="funnel-stage funnel-stage-1">
                    <div className="funnel-label">Total Conversations</div>
                    <div className="funnel-value">{total}</div>
                    <div className="funnel-percent">100%</div>
                </div>

                <div className="funnel-stage funnel-stage-2">
                    <div className="funnel-label">Resolution Achieved</div>
                    <div className="funnel-value">{resolved}</div>
                    <div className="funnel-percent">{resolvedPercent}%</div>
                </div>

                <div className="funnel-stage funnel-stage-3">
                    <div className="funnel-label">Escalations</div>
                    <div className="funnel-value">{escalated}</div>
                    <div className="funnel-percent">{escalatedPercent}%</div>
                </div>
            </div>
        </div>
    );
};

export default FunnelChart;
