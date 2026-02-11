import React from 'react';
import { BarChart, Bar, XAxis, YAxis, Cell, ResponsiveContainer } from 'recharts';
import './HorizontalBarChart.css';

const HorizontalBarChart = ({ metrics }) => {
    // Transform metrics into bar chart data
    const data = [
        { name: 'Response Accuracy', value: (metrics.response_accuracy || 0) * 100 },
        { name: 'Answer Relevancy', value: (metrics.answer_relevancy || 0) * 100 },
        { name: 'Completeness', value: (metrics.completeness_score || 0) * 100 },
        { name: 'Clarity', value: (metrics.clarity_score || 0) * 100 },
        { name: 'Tone', value: (metrics.tone_appropriateness || 0) * 100 },
        { name: 'Refusal Correctness', value: (metrics.refusal_correctness || 0) * 100 },
    ];

    // Color gradient from red to yellow
    const getColor = (value) => {
        if (value >= 80) return '#10b981'; // green
        if (value >= 50) return '#f59e0b'; // yellow
        return '#ef4444'; // red
    };

    return (
        <div className="horizontal-bar-container">
            <h3 className="chart-title">Response Accuracy</h3>
            <div className="bar-chart-wrapper">
                {data.map((item, index) => (
                    <div key={index} className="bar-item">
                        <div className="bar-label">{item.name}</div>
                        <div className="bar-visual">
                            <div
                                className="bar-fill"
                                style={{
                                    width: `${item.value}%`,
                                    background: `linear-gradient(90deg, ${getColor(item.value)} 0%, ${getColor(item.value)}dd 100%)`
                                }}
                            >
                            </div>
                        </div>
                        <div className="bar-value">{Math.round(item.value)}%</div>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default HorizontalBarChart;
