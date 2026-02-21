import api from './axios';

export const listIssues = () => api.get('/issues/');

export const getIssue = (issueId) => api.get(`/issues/${issueId}`);

export const createIssue = (data) => api.post('/issues/', data);

export const addIssueMessage = (issueId, data) => api.post(`/issues/${issueId}/messages`, data);
