import React from 'react';
import { PieChart, Pie, Cell } from 'recharts';
import './GaugeChart.css';

const GaugeChart = ({ value, label, max = 1, thresholds = { good: 0.8, warning: 0.5 } }) => {
    // Convert value to percentage
    const percentage = Math.min((value / max) * 100, 100);

    // Determine color based on value and thresholds
    const getColor = () => {
        const normalizedValue = value / max;
        if (normalizedValue >= thresholds.good) return '#10b981'; // green
        if (normalizedValue >= thresholds.warning) return '#f59e0b'; // yellow
        return '#ef4444'; // red
    };

    // Create data for semi-circle gauge
    const data = [
        { name: 'value', value: percentage },
        { name: 'remaining', value: 100 - percentage }
    ];

    const COLORS = [getColor(), 'rgba(55, 65, 81, 0.3)'];

    return (
        <div className="gauge-chart-container">
            <div className="gauge-chart">
                <PieChart width={200} height={120}>
                    <Pie
                        data={data}
                        cx={100}
                        cy={100}
                        startAngle={180}
                        endAngle={0}
                        innerRadius={60}
                        outerRadius={90}
                        paddingAngle={0}
                        dataKey="value"
                    >
                        {data.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={COLORS[index]} />
                        ))}
                    </Pie>
                </PieChart>
                <div className="gauge-value">
                    {Math.round(percentage)}%
                </div>
            </div>
            <div className="gauge-label">{label}</div>
        </div>
    );
};

export default GaugeChart;
