import axios from 'axios';

const API_BASE_URL = 'http://localhost:5000/api';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// API functions
export const authAPI = {
  register: (userData) => api.post('/auth/register', userData),
  login: (credentials) => api.post('/auth/login', credentials),
  getProfile: () => api.get('/auth/profile')
};

export const uploadAPI = {
  uploadProfile: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/upload/profile', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
  uploadGroup: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/upload/group', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  }
};

export const photosAPI = {
  getMyPhotos: () => api.get('/photos/my-photos')
};

export default api;
