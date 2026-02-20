import api, { USE_MOCK_DATA } from './axios';
import { mockLogin, mockGetMe } from './mockData';

export const login = (email, password) =>
  USE_MOCK_DATA
    ? mockLogin(email, password)
    : api.post('/auth/login', { email, password });

export const getMe = () => (USE_MOCK_DATA ? mockGetMe() : api.get('/auth/me'));
