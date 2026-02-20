import api from './axios';

export const listArticles = (params = {}) =>
  api.get('/knowledge/', { params });

export const getArticle = (id) =>
  api.get(`/knowledge/${id}`);

export const createArticle = (data) =>
  api.post('/knowledge/', data);

export const updateArticle = (id, data) =>
  api.patch(`/knowledge/${id}`, data);

export const deleteArticle = (id) =>
  api.delete(`/knowledge/${id}`);
