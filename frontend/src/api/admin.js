import api from './axios';

export const listAgents = (params = {}) =>
  api.get('/admin/agents', { params });

export const createAgent = (data) =>
  api.post('/admin/agents', data);

export const updateAgent = (id, data) =>
  api.patch(`/admin/agents/${id}`, data);

export const deleteAgent = (id) =>
  api.delete(`/admin/agents/${id}`);

export const listTeams = () =>
  api.get('/admin/teams');

export const createTeam = (data) =>
  api.post('/admin/teams', data);

export const updateTeam = (id, data) =>
  api.patch(`/admin/teams/${id}`, data);

export const deleteTeam = (id) =>
  api.delete(`/admin/teams/${id}`);

export const getMappings = () =>
  api.get('/admin/mappings');

export const saveMappings = (mappings) =>
  api.post('/admin/mappings', { mappings });

export const getNotifications = () =>
  api.get('/admin/notifications');

export const updateNotifications = (data) =>
  api.put('/admin/notifications', data);
