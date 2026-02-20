import api from './axios';

export const listTickets = (params = {}) =>
  api.get('/tickets/', { params });

export const getTicket = (id) =>
  api.get(`/tickets/${id}`);

export const createTicket = (data) =>
  api.post('/tickets/', data);

export const updateTicket = (id, data) =>
  api.patch(`/tickets/${id}`, data);

export const assignTicket = (id, data) =>
  api.post(`/tickets/${id}/assign`, data);

export const resolveTicket = (id) =>
  api.post(`/tickets/${id}/resolve`);

export const getMessages = (id) =>
  api.get(`/tickets/${id}/messages`);

export const addMessage = (id, data) =>
  api.post(`/tickets/${id}/messages`, data);

export const getSimilarArticles = (id) =>
  api.get(`/tickets/${id}/similar-articles`);

export const getAiSuggestion = (id) =>
  api.get(`/tickets/${id}/ai-suggestion`);
