import api from './axios';

export const sendChat = (data) =>
  api.post('/chat/', data);
