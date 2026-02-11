import React from 'react';
import { Radar, RadarChart as RechartsRadar, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer } from 'recharts';
import './RadarChart.css';

const RadarChart = ({ metrics }) => {
    // Transform metrics into radar chart data
    const data = [
        { subject: 'Response Accuracy', value: (metrics.response_accuracy || 0) * 100, fullMark: 100 },
        { subject: 'Answer Relevancy', value: (metrics.answer_relevancy || 0) * 100, fullMark: 100 },
        { subject: 'Completeness', value: (metrics.completeness_score || 0) * 100, fullMark: 100 },
        { subject: 'Clarity', value: (metrics.clarity_score || 0) * 100, fullMark: 100 },
        { subject: 'Tone', value: (metrics.tone_appropriateness || 0) * 100, fullMark: 100 },
        { subject: 'Refusal Correctness', value: (metrics.refusal_correctness || 0) * 100, fullMark: 100 },
    ];

    // Check if all values are mid-level (quality plateau)
    const avgValue = data.reduce((sum, item) => sum + item.value, 0) / data.length;
    const isPlateau = avgValue > 40 && avgValue < 60 && data.every(item => Math.abs(item.value - avgValue) < 15);

    return (
        <div className="radar-chart-container">
            <h3 className="chart-title">Quality Scores Overview</h3>
            <ResponsiveContainer width="100%" height={300}>
                <RechartsRadar data={data}>
                    <PolarGrid stroke="rgba(156, 163, 175, 0.2)" />
                    <PolarAngleAxis
                        dataKey="subject"
                        tick={{ fill: '#9ca3af', fontSize: 12 }}
                    />
                    <PolarRadiusAxis
                        angle={90}
                        domain={[0, 100]}
                        tick={{ fill: '#6b7280', fontSize: 10 }}
                    />
                    <Radar
                        name="Quality Metrics"
                        dataKey="value"
                        stroke="#3b82f6"
                        fill="#3b82f6"
                        fillOpacity={0.6}
                    />
                </RechartsRadar>
            </ResponsiveContainer>
            {isPlateau && (
                <div className="plateau-warning">
                    Quality plateau detected – All scores at mid-level
                </div>
            )}
        </div>
    );
};

export default RadarChart;
