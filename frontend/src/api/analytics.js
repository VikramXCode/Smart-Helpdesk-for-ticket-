import api from './axios';

export const getOverview = () =>
  api.get('/analytics/overview');

export const getVolume = (period = '7d') =>
  api.get('/analytics/volume', { params: { period } });

export const getCategories = () =>
  api.get('/analytics/categories');

export const getTeamPerformance = () =>
  api.get('/analytics/team-performance');

export const getTrends = () =>
  api.get('/analytics/trends');
