import React, { useState, useEffect } from 'react';
import FileUpload from './components/FileUpload';
import HistorySidebar from './components/HistorySidebar';
import MetricsTable from './components/MetricsTable';
import {
    uploadFile,
    getUploadHistory,
    evaluateFile,
    getEvaluationResults,
    exportToExcel
} from './services/api';
import './App.css';

function App() {
    // State
    const [history, setHistory] = useState([]);
    const [selectedFile, setSelectedFile] = useState(null);
    const [metrics, setMetrics] = useState([]);
    const [isUploading, setIsUploading] = useState(false);
    const [isEvaluating, setIsEvaluating] = useState(false);
    const [isExporting, setIsExporting] = useState(false);
    const [error, setError] = useState(null);
    const [success, setSuccess] = useState(null);

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
        setIsUploading(true);
        setError(null);
        setSuccess(null);

        try {
            const result = await uploadFile(file);
            setSuccess(`Successfully uploaded ${result.entry_count} log entries`);
            await loadHistory();

            // Auto-select the uploaded file
            setSelectedFile({
                id: result.id,
                filename: result.filename,
                entry_count: result.entry_count
            });
            setMetrics([]);
        } catch (err) {
            setError(err.response?.data?.detail || 'Failed to upload file');
        } finally {
            setIsUploading(false);
        }
    };

    const handleSelectFile = async (file) => {
        setSelectedFile(file);
        setMetrics([]);
        setError(null);
        setSuccess(null);

        // Check if already evaluated
        try {
            const result = await getEvaluationResults(file.id);
            if (result && result.metrics) {
                setMetrics(result.metrics);
            }
        } catch (err) {
            // Not evaluated yet, that's fine
        }
    };

    const handleEvaluate = async () => {
        if (!selectedFile) return;

        setIsEvaluating(true);
        setError(null);
        setSuccess(null);

        try {
            const result = await evaluateFile(selectedFile.id);
            setMetrics(result.metrics);
            setSuccess('Evaluation completed successfully!');
        } catch (err) {
            setError(err.response?.data?.detail || 'Evaluation failed. Make sure GOOGLE_API_KEY is set.');
        } finally {
            setIsEvaluating(false);
        }
    };

    const handleExport = async () => {
        if (!selectedFile) return;

        setIsExporting(true);
        setError(null);

        try {
            const blobUrl = await exportToExcel(selectedFile.id);

            // Create download link
            const link = document.createElement('a');
            link.href = blobUrl;
            link.download = `evaluation_${selectedFile.filename.replace(/\.[^/.]+$/, '')}.xlsx`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);

            // Clean up blob URL
            URL.revokeObjectURL(blobUrl);

            setSuccess('Excel file downloaded successfully!');
        } catch (err) {
            setError(err.response?.data?.detail || 'Failed to export Excel file');
        } finally {
            setIsExporting(false);
        }
    };

    return (
        <div className="app-container">
            <HistorySidebar
                history={history}
                selectedId={selectedFile?.id}
                onSelect={handleSelectFile}
                onRefresh={loadHistory}
            />

            <main className="main-content">
                <header className="content-header">
                    <h1 className="page-title">Log Analyzer Agent</h1>
                    <p className="page-subtitle">
                        AI-powered evaluation of chatbot logs using 18 comprehensive metrics
                    </p>
                </header>

                {/* Alerts */}
                {error && (
                    <div className="alert alert-error">
                        <span>⚠️</span>
                        <span>{error}</span>
                        <button
                            onClick={() => setError(null)}
                            style={{ marginLeft: 'auto', background: 'none', border: 'none', color: 'inherit', cursor: 'pointer' }}
                        >
                            ✕
                        </button>
                    </div>
                )}

                {success && (
                    <div className="alert alert-success">
                        <span>✓</span>
                        <span>{success}</span>
                        <button
                            onClick={() => setSuccess(null)}
                            style={{ marginLeft: 'auto', background: 'none', border: 'none', color: 'inherit', cursor: 'pointer' }}
                        >
                            ✕
                        </button>
                    </div>
                )}

                {/* File Upload */}
                <FileUpload
                    onUpload={handleUpload}
                    isUploading={isUploading}
                />

                {/* Selected File Actions */}
                {selectedFile && !isEvaluating && metrics.length === 0 && (
                    <div className="alert alert-info">
                        <span>📄</span>
                        <span>
                            <strong>{selectedFile.filename}</strong> selected ({selectedFile.entry_count} entries)
                        </span>
                        <button
                            className="btn btn-primary"
                            onClick={handleEvaluate}
                            style={{ marginLeft: 'auto' }}
                        >
                            🚀 Evaluate Metrics
                        </button>
                    </div>
                )}

                {/* Metrics Display */}
                {(selectedFile && (isEvaluating || metrics.length > 0)) && (
                    <MetricsTable
                        metrics={metrics}
                        filename={selectedFile.filename}
                        isLoading={isEvaluating}
                        onExport={handleExport}
                        isExporting={isExporting}
                    />
                )}

                {/* Empty State */}
                {!selectedFile && (
                    <div className="metrics-section">
                        <div className="empty-state">
                            <div className="empty-state-icon">📊</div>
                            <h3 className="empty-state-title">Ready to Analyze</h3>
                            <p>Upload a log file or select from history to view evaluation metrics</p>
                        </div>
                    </div>
                )}
            </main>
        </div>
    );
}

export default App;
