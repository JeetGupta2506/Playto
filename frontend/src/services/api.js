import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const postAPI = {
  getAll: () => api.get('/posts/'),
  getOne: (id) => api.get(`/posts/${id}/`),
  create: (data) => api.post('/posts/', data),
  like: (id, user) => api.post(`/posts/${id}/like/`, { user }),
  unlike: (id, user) => api.post(`/posts/${id}/unlike/`, { user }),
};

export const commentAPI = {
  getAll: (postId) => api.get('/comments/', { params: { post: postId } }),
  create: (data) => api.post('/comments/', data),
  like: (id, user) => api.post(`/comments/${id}/like/`, { user }),
  unlike: (id, user) => api.post(`/comments/${id}/unlike/`, { user }),
};

export const leaderboardAPI = {
  get: () => api.get('/leaderboard/'),
};

export default api;
