import React, { useState, useRef } from 'react';

const FileUpload = ({ onUpload, isUploading }) => {
    const [isDragOver, setIsDragOver] = useState(false);
    const fileInputRef = useRef(null);

    const handleDragOver = (e) => {
        e.preventDefault();
        setIsDragOver(true);
    };

    const handleDragLeave = (e) => {
        e.preventDefault();
        setIsDragOver(false);
    };

    const handleDrop = (e) => {
        e.preventDefault();
        setIsDragOver(false);

        const files = e.dataTransfer.files;
        if (files.length > 0) {
            onUpload(files[0]);
        }
    };

    const handleFileSelect = (e) => {
        const files = e.target.files;
        if (files.length > 0) {
            onUpload(files[0]);
        }
    };

    const handleClick = () => {
        fileInputRef.current?.click();
    };

    return (
        <div
            className={`upload-zone ${isDragOver ? 'drag-over' : ''}`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={handleClick}
        >
            <input
                ref={fileInputRef}
                type="file"
                accept=".json,.csv,.xlsx,.xls"
                onChange={handleFileSelect}
                style={{ display: 'none' }}
            />

            <div className="upload-icon">
                {isUploading ? '⏳' : '📂'}
            </div>

            <h3 className="upload-title">
                {isUploading ? 'Uploading...' : 'Drop your log file here'}
            </h3>

            <p className="upload-subtitle">
                {isUploading
                    ? 'Please wait while we process your file'
                    : 'or click to browse files'
                }
            </p>

            {!isUploading && (
                <div className="upload-formats">
                    <span className="format-badge">JSON</span>
                    <span className="format-badge">CSV</span>
                    <span className="format-badge">XLSX</span>
                </div>
            )}
        </div>
    );
};

export default FileUpload;
