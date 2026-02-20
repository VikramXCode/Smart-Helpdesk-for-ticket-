import api, { USE_MOCK_DATA } from './axios';
import {
  mockGetOverview,
  mockGetVolume,
  mockGetCategories,
  mockGetTeamPerformance,
  mockGetTrends,
} from './mockData';

export const getOverview = () =>
  USE_MOCK_DATA ? mockGetOverview() : api.get('/analytics/overview');

export const getVolume = (period = '7d') =>
  USE_MOCK_DATA ? mockGetVolume(period) : api.get('/analytics/volume', { params: { period } });

export const getCategories = () =>
  USE_MOCK_DATA ? mockGetCategories() : api.get('/analytics/categories');

export const getTeamPerformance = () =>
  USE_MOCK_DATA ? mockGetTeamPerformance() : api.get('/analytics/team-performance');

export const getTrends = () =>
  USE_MOCK_DATA ? mockGetTrends() : api.get('/analytics/trends');
