import api, { USE_MOCK_DATA } from './axios';
import {
  mockListArticles,
  mockGetArticle,
  mockCreateArticle,
  mockUpdateArticle,
  mockDeleteArticle,
} from './mockData';

export const listArticles = (params = {}) =>
  USE_MOCK_DATA ? mockListArticles(params) : api.get('/knowledge/', { params });

export const getArticle = (id) =>
  USE_MOCK_DATA ? mockGetArticle(id) : api.get(`/knowledge/${id}`);

export const createArticle = (data) =>
  USE_MOCK_DATA ? mockCreateArticle(data) : api.post('/knowledge/', data);

export const updateArticle = (id, data) =>
  USE_MOCK_DATA ? mockUpdateArticle(id, data) : api.patch(`/knowledge/${id}`, data);

export const deleteArticle = (id) =>
  USE_MOCK_DATA ? mockDeleteArticle(id) : api.delete(`/knowledge/${id}`);
