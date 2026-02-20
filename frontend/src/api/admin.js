import api, { USE_MOCK_DATA } from './axios';
import {
  mockListAgents,
  mockCreateAgent,
  mockUpdateAgent,
  mockDeleteAgent,
  mockListTeams,
  mockCreateTeam,
  mockUpdateTeam,
  mockDeleteTeam,
  mockAssignAgentToTeam,
  mockRemoveAgentFromTeam,
  mockGetMappings,
  mockSaveMappings,
  mockGetNotifications,
  mockUpdateNotifications,
} from './mockData';

export const listAgents = (params = {}) =>
  USE_MOCK_DATA ? mockListAgents(params) : api.get('/admin/agents', { params });

export const createAgent = (data) =>
  USE_MOCK_DATA ? mockCreateAgent(data) : api.post('/admin/agents', data);

export const updateAgent = (id, data) =>
  USE_MOCK_DATA ? mockUpdateAgent(id, data) : api.patch(`/admin/agents/${id}`, data);

export const deleteAgent = (id) =>
  USE_MOCK_DATA ? mockDeleteAgent(id) : api.delete(`/admin/agents/${id}`);

export const listTeams = () =>
  USE_MOCK_DATA ? mockListTeams() : api.get('/admin/teams');

export const createTeam = (data) =>
  USE_MOCK_DATA ? mockCreateTeam(data) : api.post('/admin/teams', data);

export const updateTeam = (id, data) =>
  USE_MOCK_DATA ? mockUpdateTeam(id, data) : api.patch(`/admin/teams/${id}`, data);

export const deleteTeam = (id) =>
  USE_MOCK_DATA ? mockDeleteTeam(id) : api.delete(`/admin/teams/${id}`);

export const assignAgentToTeam = (teamId, agentId) =>
  USE_MOCK_DATA ? mockAssignAgentToTeam(teamId, agentId) : api.post(`/admin/teams/${teamId}/agents`, { agent_id: agentId });

export const removeAgentFromTeam = (teamId, agentId) =>
  USE_MOCK_DATA ? mockRemoveAgentFromTeam(teamId, agentId) : api.delete(`/admin/teams/${teamId}/agents/${agentId}`);

export const getMappings = () =>
  USE_MOCK_DATA ? mockGetMappings() : api.get('/admin/mappings');

export const saveMappings = (mappings) =>
  USE_MOCK_DATA ? mockSaveMappings(mappings) : api.post('/admin/mappings', { mappings });

export const getNotifications = () =>
  USE_MOCK_DATA ? mockGetNotifications() : api.get('/admin/notifications');

export const updateNotifications = (data) =>
  USE_MOCK_DATA ? mockUpdateNotifications(data) : api.put('/admin/notifications', data);
