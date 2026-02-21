import api from './axios';

export const getStats = () =>
  api.get('/super-admin/stats');

export const listCompanies = (params = {}) =>
  api.get('/super-admin/companies', { params });

export const createCompany = (data) =>
  api.post('/super-admin/companies', data);

export const updateCompany = (id, data) =>
  api.patch(`/super-admin/companies/${id}`, data);

export const deleteCompany = (id) =>
  api.delete(`/super-admin/companies/${id}`);
