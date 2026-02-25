/**
 * Axios 实例配置
 * 仅负责创建和配置 axios 实例，不包含任何业务逻辑
 */

import axios from 'axios';
import toast from 'react-hot-toast';

// 支持本地开发和 nginx 反向代理
// 开发环境：使用 vite 代理（相对路径 /api）
// 生产环境：使用 nginx 代理（相对路径 /api）
const API_BASE_URL = (import.meta as any).env?.VITE_API_URL || '/api';

const axiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json',
  },
});

axiosInstance.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

axiosInstance.interceptors.response.use(
  (response) => response,
  (error) => {
    let errorMsg = '请求失败，请稍后重试';
    
    if (error.response) {
      const status = error.response.status;
      const data = error.response.data;
      
      if (data?.msg) {
        errorMsg = data.msg;
      } else if (status === 401) {
        localStorage.removeItem('token');
        window.location.href = '/login';
        errorMsg = '登录已过期，请重新登录';
      } else if (status === 403) {
        errorMsg = '没有权限执行此操作';
      } else if (status === 404) {
        errorMsg = '请求的资源不存在';
      } else if (status >= 500) {
        errorMsg = '服务器错误，请稍后重试';
      }
    } else if (error.request) {
      errorMsg = '网络连接失败，请检查网络';
    }
    
    toast.error(errorMsg);
    return Promise.reject(error);
  }
);

export const apiClient = axiosInstance;
export default apiClient;
