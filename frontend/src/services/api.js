import axios from 'axios';

const API_BASE_URL = '/api';

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Upload a log file
export const uploadFile = async (file) => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await api.post('/upload/', formData, {
        headers: {
            'Content-Type': 'multipart/form-data',
        },
    });

    return response.data;
};

// Get upload history
export const getUploadHistory = async () => {
    const response = await api.get('/upload/history');
    return response.data;
};

// Get uploaded file details
export const getUploadedFile = async (fileId) => {
    const response = await api.get(`/upload/${fileId}`);
    return response.data;
};

// Delete an uploaded file
export const deleteUploadedFile = async (fileId) => {
    const response = await api.delete(`/upload/${fileId}`);
    return response.data;
};

// Evaluate a log file
export const evaluateFile = async (fileId, force = false) => {
    const response = await api.post(`/metrics/${fileId}/evaluate?force=${force}`);
    return response.data;
};

// Get cached evaluation results
export const getEvaluationResults = async (fileId) => {
    const response = await api.get(`/metrics/${fileId}`);
    return response.data;
};

// Get evaluation status
export const getEvaluationStatus = async (fileId) => {
    const response = await api.get(`/metrics/${fileId}/status`);
    return response.data;
};

// Export to Excel (returns blob URL)
export const exportToExcel = async (fileId) => {
    const response = await api.get(`/export/${fileId}/excel`, {
        responseType: 'blob',
    });

    // Create download URL
    const blob = new Blob([response.data], {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    });

    return URL.createObjectURL(blob);
};

// ==========================================
// PIPELINE APIs (Hybrid Rule + LLM)
// ==========================================

export const analyzePipeline = async (file, useLlm = true) => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await api.post(`/pipeline/analyze?use_llm=${useLlm}`, formData, {
        headers: {
            'Content-Type': 'multipart/form-data',
        },
    });

    return response.data;
};

export const getPipelineResults = async (fileId) => {
    const response = await api.get(`/pipeline/${fileId}/results`);
    return response.data;
};

export const getScenarioBreakdown = async (fileId) => {
    const response = await api.get(`/pipeline/${fileId}/scenarios`);
    return response.data;
};

export const getLabelDistribution = async (fileId) => {
    const response = await api.get(`/pipeline/${fileId}/labels`);
    return response.data;
};

export default api;
