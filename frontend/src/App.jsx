import React, { useState, useEffect } from 'react';
import FileUpload from './components/FileUpload';
import MetricsTable from './components/MetricsTable';
import Dashboard from './components/Dashboard';
import Navbar from './components/Navbar';
import {
    analyzePipeline,
    getUploadHistory,
    exportToExcel
} from './services/api';
import './App.css';

function App() {
    // State
    const [history, setHistory] = useState([]);
    const [selectedFile, setSelectedFile] = useState(null);
    const [pipelineResults, setPipelineResults] = useState(null);
    const [isProcessing, setIsProcessing] = useState(false);
    const [useLlm, setUseLlm] = useState(true);
    const [error, setError] = useState(null);
    const [success, setSuccess] = useState(null);
    const [showDetailedMetrics, setShowDetailedMetrics] = useState(false);

    // Load history on mount
    useEffect(() => {
        loadHistory();
    }, []);

    const loadHistory = async () => {
        try {
            const data = await getUploadHistory();
            setHistory(data);
        } catch (err) {
            console.error('Failed to load history:', err);
        }
    };

    const handleUpload = async (file) => {
        setIsProcessing(true);
        setError(null);
        setSuccess(null);
        setPipelineResults(null);

        try {
            const result = await analyzePipeline(file, useLlm);
            setPipelineResults(result);
            setSuccess(`Successfully analyzed ${result.filename} (${result.total_conversations} conversations)`);

            // Set selected file context
            setSelectedFile({
                id: result.file_id,
                filename: result.filename,
                entry_count: result.total_conversations
            });

            await loadHistory();
        } catch (err) {
            setError(err.response?.data?.detail || 'Failed to analyze file');
        } finally {
            setIsProcessing(false);
        }
    };

    const handleSelectFile = async (item) => {
        // For now just set selected, in real app we'd fetch cached results
        setSelectedFile(item);
        setError(null);
        // We'd need an API to get cached pipeline results here
        // setPipelineResults(cachedResults); 
    };

    const handleExport = async () => {
        if (!selectedFile) return;

        try {
            const blobUrl = await exportToExcel(selectedFile.id);
            const link = document.createElement('a');
            link.href = blobUrl;
            link.download = `analysis_${selectedFile.filename.replace(/\.[^/.]+$/, '')}.xlsx`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(blobUrl);
            setSuccess('Excel file downloaded successfully!');
        } catch (err) {
            setError('Failed to export Excel file');
        }
    };

    // Helper to render label distribution
    const renderLabelDist = (dist) => {
        if (!dist) return null;
        return (
            <div className="label-dist">
                {Object.entries(dist).map(([label, count]) => (
                    <div key={label} className={`label-badge label-${label}`}>
                        <span className="label-name">{label}</span>
                        <span className="label-count">{count}</span>
                    </div>
                ))}
            </div>
        );
    };

    return (
        <div className="app-container">
            <Navbar />

            <main className="main-content main-content-full">
                <header className="content-header">
                    <h1 className="page-title">AI Agent Evaluation Overview</h1>
                    <p className="page-subtitle">
                        Hybrid Evaluation Pipeline (Rule-Based + LLM)
                    </p>
                    <div className="pipeline-controls">
                        <label className="toggle-switch">
                            <input
                                type="checkbox"
                                checked={useLlm}
                                onChange={(e) => setUseLlm(e.target.checked)}
                            />
                            <span className="toggle-slider"></span>
                            <span className="toggle-label">Use LLM for Semantic Metrics</span>
                        </label>
                    </div>
                </header>

                {/* Alerts */}
                {error && (
                    <div className="alert alert-error">
                        <span>⚠️</span><span>{error}</span>
                        <button onClick={() => setError(null)}>✕</button>
                    </div>
                )}

                {success && (
                    <div className="alert alert-success">
                        <span>✓</span><span>{success}</span>
                        <button onClick={() => setSuccess(null)}>✕</button>
                    </div>
                )}

                {/* File Upload */}
                <FileUpload
                    onUpload={handleUpload}
                    isUploading={isProcessing}
                />

                {/* Results Dashboard */}
                {pipelineResults && (
                    <div className="results-dashboard">
                        {/* Main Dashboard */}
                        <Dashboard data={pipelineResults} />

                        {/* Detailed Metrics Table - Collapsible */}
                        <div className="section-header" style={{ marginTop: '3rem' }}>
                            <h2>Detailed Metrics</h2>
                            <div style={{ display: 'flex', gap: '1rem' }}>
                                <button
                                    className="btn btn-secondary"
                                    onClick={() => setShowDetailedMetrics(!showDetailedMetrics)}
                                >
                                    {showDetailedMetrics ? 'Hide Details' : 'Show Details'}
                                </button>
                                <button className="btn btn-secondary" onClick={handleExport}>
                                    Export Excel
                                </button>
                            </div>
                        </div>
                        {showDetailedMetrics && (
                            <MetricsTable
                                metrics={Object.entries(pipelineResults.overall.metrics).map(
                                    ([name, value]) => ({ metric_name: name, metric_value: value })
                                )}
                                filename={pipelineResults.filename}
                            />
                        )}
                    </div>
                )}
            </main>
        </div>
    );
}

export default App;
