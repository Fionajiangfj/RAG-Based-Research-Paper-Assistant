import axios from 'axios';
import { QueryResponse } from '../types';

// Use environment variable for API URL, fallback to localhost for development
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const submitQuery = async (query: string): Promise<QueryResponse> => {
  try {
    const response = await api.post<QueryResponse>('/query', { query });
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      throw new Error(error.response?.data?.detail || 'Failed to submit query');
    }
    throw error;
  }
};
