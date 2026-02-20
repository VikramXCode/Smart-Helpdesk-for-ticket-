import api, { USE_MOCK_DATA } from './axios';
import {
  mockListTickets,
  mockGetTicket,
  mockCreateTicket,
  mockUpdateTicket,
  mockAssignTicket,
  mockResolveTicket,
  mockGetMessages,
  mockAddMessage,
  mockGetSimilarArticles,
  mockGetAiSuggestion,
} from './mockData';

export const listTickets = (params = {}) =>
  USE_MOCK_DATA ? mockListTickets(params) : api.get('/tickets/', { params });

export const getTicket = (id) =>
  USE_MOCK_DATA ? mockGetTicket(id) : api.get(`/tickets/${id}`);

export const createTicket = (data) =>
  USE_MOCK_DATA ? mockCreateTicket(data) : api.post('/tickets/', data);

export const updateTicket = (id, data) =>
  USE_MOCK_DATA ? mockUpdateTicket(id, data) : api.patch(`/tickets/${id}`, data);

export const assignTicket = (id, data) =>
  USE_MOCK_DATA ? mockAssignTicket(id, data) : api.post(`/tickets/${id}/assign`, data);

export const resolveTicket = (id) =>
  USE_MOCK_DATA ? mockResolveTicket(id) : api.post(`/tickets/${id}/resolve`);

export const getMessages = (id) =>
  USE_MOCK_DATA ? mockGetMessages(id) : api.get(`/tickets/${id}/messages`);

export const addMessage = (id, data) =>
  USE_MOCK_DATA ? mockAddMessage(id, data) : api.post(`/tickets/${id}/messages`, data);

export const getSimilarArticles = (id) =>
  USE_MOCK_DATA ? mockGetSimilarArticles(id) : api.get(`/tickets/${id}/similar-articles`);

export const getAiSuggestion = (id) =>
  USE_MOCK_DATA ? mockGetAiSuggestion(id) : api.get(`/tickets/${id}/ai-suggestion`);
