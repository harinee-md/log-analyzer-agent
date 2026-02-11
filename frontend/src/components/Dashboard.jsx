import React from 'react';
import MetricCard from './MetricCard';
import GaugeChart from './GaugeChart';
import RadarChart from './RadarChart';
import HorizontalBarChart from './HorizontalBarChart';
import FunnelChart from './FunnelChart';
import './Dashboard.css';

const Dashboard = ({ data }) => {
    if (!data || !data.overall) {
        return <div className="dashboard-loading">Loading dashboard...</div>;
    }

    const metrics = data.overall.metrics || {};
    const totalConversations = data.total_conversations || 0;

    // Determine metric status based on value and type
    const getMetricStatus = (value, type = 'higher-better') => {
        if (type === 'higher-better') {
            if (value >= 0.8) return 'good';
            if (value >= 0.5) return 'warning';
            return 'critical';
        } else {
            // lower-better metrics
            if (value <= 0.2) return 'good';
            if (value <= 0.5) return 'warning';
            return 'critical';
        }
    };

    // Check for critical conditions
    const criticalAlerts = [];
    if (metrics.intent_accuracy === 0) {
        criticalAlerts.push('Intent Accuracy = 0.0');
    }
    if (metrics.hallucination_rate >= 1.0) {
        criticalAlerts.push('Hallucination = 1.0');
    }
    if (metrics.overconfidence >= 1.0) {
        criticalAlerts.push('Overconfidence = 1.0');
    }
    if (metrics.incorrect_refusal_rate >= 1.0) {
        criticalAlerts.push('Incorrect Refusal = 1.0');
    }
    if ((metrics.pii_exposure_count || 0) > 0.5) {
        criticalAlerts.push('High PII Exposure');
    }

    const showCriticalBanner = criticalAlerts.length > 0;

    return (
        <div className="dashboard-container">
            {/* Critical Alerts Banner */}
            {showCriticalBanner && (
                <div className="critical-alert-banner">
                    <span className="alert-icon">⚠️</span>
                    <span className="alert-text">
                        CRITICAL MODEL RISK DETECTED | {criticalAlerts.join(' | ')}
                    </span>
                </div>
            )}

            {/* Top Metric Cards Row */}
            <div className="metric-cards-row">
                <MetricCard
                    title="Intent Accuracy"
                    value={metrics.intent_accuracy || 0}
                    status={getMetricStatus(metrics.intent_accuracy || 0)}
                    format="decimal"
                />
                <MetricCard
                    title="Resolution Rate"
                    value={metrics.resolution_detected || 0}
                    status={getMetricStatus(metrics.resolution_detected || 0)}
                    format="decimal"
                />
                <MetricCard
                    title="Escalation Rate"
                    value={metrics.escalation_detected || 0}
                    status={getMetricStatus(metrics.escalation_detected || 0, 'lower-better')}
                    format="decimal"
                />
                <MetricCard
                    title="Customer Effort"
                    value={metrics.customer_effort_score || 0}
                    status={getMetricStatus(metrics.customer_effort_score || 0, 'lower-better')}
                    format="decimal"
                />
                <MetricCard
                    title="Context Retention"
                    value={metrics.context_retention_score || 0}
                    status={getMetricStatus(metrics.context_retention_score || 0)}
                    format="decimal"
                />
                <MetricCard
                    title="Turn Count"
                    value={metrics.turn_count || 0}
                    status={getMetricStatus((metrics.turn_count || 0) / 10, 'lower-better')}
                    format="decimal"
                />
            </div>

            {/* Main Content Grid */}
            <div className="dashboard-grid">
                {/* Left Column: Radar Chart */}
                <div className="dashboard-section radar-section">
                    <RadarChart metrics={metrics} />
                </div>

                {/* Middle Column: Gauges */}
                <div className="dashboard-section gauges-section">
                    <div className="gauges-grid">
                        <GaugeChart
                            value={metrics.response_accuracy || 0}
                            label="Response Accuracy"
                            thresholds={{ good: 0.8, warning: 0.5 }}
                        />
                        <GaugeChart
                            value={metrics.answer_relevancy || 0}
                            label="Answer Relevancy"
                            thresholds={{ good: 0.8, warning: 0.5 }}
                        />
                        <GaugeChart
                            value={metrics.completeness_score || 0}
                            label="Completeness"
                            thresholds={{ good: 0.8, warning: 0.5 }}
                        />
                        <GaugeChart
                            value={metrics.clarity_score || 0}
                            label="Clarity"
                            thresholds={{ good: 0.8, warning: 0.5 }}
                        />
                    </div>
                </div>

                {/* Right Column: Horizontal Bars */}
                <div className="dashboard-section bars-section">
                    <HorizontalBarChart metrics={metrics} />
                </div>
            </div>

            {/* Bottom Section: Funnel and Additional Metrics */}
            <div className="dashboard-bottom">
                <div className="funnel-section">
                    <FunnelChart
                        totalConversations={totalConversations}
                        resolutionRate={metrics.resolution_detected || 0}
                        escalationRate={metrics.escalation_detected || 0}
                    />
                </div>

                <div className="bottom-metrics-row">
                    <MetricCard
                        title="Turn Count"
                        value={metrics.turn_count || 0}
                        status={getMetricStatus((metrics.turn_count || 0) / 10, 'lower-better')}
                        format="decimal"
                        showIndicator={false}
                    />
                    <MetricCard
                        title="Customer Effort"
                        value={metrics.customer_effort_score || 0}
                        status={getMetricStatus(metrics.customer_effort_score || 0, 'lower-better')}
                        format="decimal"
                        showIndicator={false}
                    />
                    <MetricCard
                        title="Context Retention"
                        value={metrics.context_retention_score || 0}
                        status={getMetricStatus(metrics.context_retention_score || 0)}
                        format="decimal"
                        showIndicator={false}
                    />
                </div>
            </div>
        </div>
    );
};

export default Dashboard;
