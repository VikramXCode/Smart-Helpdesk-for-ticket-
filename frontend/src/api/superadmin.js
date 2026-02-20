import api, { USE_MOCK_DATA } from './axios';
import {
  mockGetStats,
  mockListCompanies,
  mockCreateCompany,
  mockUpdateCompany,
  mockDeleteCompany,
} from './mockData';

export const getStats = () =>
  USE_MOCK_DATA ? mockGetStats() : api.get('/super-admin/stats');

export const listCompanies = (params = {}) =>
  USE_MOCK_DATA ? mockListCompanies(params) : api.get('/super-admin/companies', { params });

export const createCompany = (data) =>
  USE_MOCK_DATA ? mockCreateCompany(data) : api.post('/super-admin/companies', data);

export const updateCompany = (id, data) =>
  USE_MOCK_DATA ? mockUpdateCompany(id, data) : api.patch(`/super-admin/companies/${id}`, data);

export const deleteCompany = (id) =>
  USE_MOCK_DATA ? mockDeleteCompany(id) : api.delete(`/super-admin/companies/${id}`);
