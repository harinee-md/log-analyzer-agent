import React from 'react';

const HistorySidebar = ({ history, selectedId, onSelect, onRefresh }) => {
    const formatDate = (dateString) => {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    return (
        <aside className="sidebar">
            <div className="sidebar-header">
                <div className="logo">
                    <div className="logo-icon">📊</div>
                    <span className="logo-text">Log Analyzer</span>
                </div>
            </div>

            <div className="sidebar-section">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                    <h3 className="section-title" style={{ marginBottom: 0 }}>Upload History</h3>
                    <button
                        className="btn btn-secondary"
                        onClick={onRefresh}
                        style={{ padding: '0.5rem 0.75rem', fontSize: '0.75rem' }}
                    >
                        ↻ Refresh
                    </button>
                </div>

                {history.length === 0 ? (
                    <div className="history-empty">
                        <p>No files uploaded yet</p>
                        <p style={{ fontSize: '0.8rem', marginTop: '0.5rem' }}>
                            Upload a JSON or CSV log file to get started
                        </p>
                    </div>
                ) : (
                    <div className="history-list">
                        {history.map((item) => (
                            <div
                                key={item.id}
                                className={`history-item ${selectedId === item.id ? 'active' : ''}`}
                                onClick={() => onSelect(item)}
                            >
                                <div className="history-filename" title={item.filename}>
                                    📄 {item.filename}
                                </div>
                                <div className="history-meta">
                                    <span>{item.entry_count} entries</span>
                                    <span>{formatDate(item.upload_time)}</span>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </aside>
    );
};

export default HistorySidebar;
