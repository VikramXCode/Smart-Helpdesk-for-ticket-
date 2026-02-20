import api, { USE_MOCK_DATA } from './axios';
import { mockSendChat } from './mockData';

export const sendChat = (data) =>
  USE_MOCK_DATA ? mockSendChat(data) : api.post('/chat/', data);
