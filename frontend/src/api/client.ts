import axios from 'axios';
import { Ticket, ReportSummaryItem } from '../types';

export const apiClient = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

export const getTickets = async (params?: { ai_review_status?: string; ticket_status?: string; priority?: string }) => {
  const response = await apiClient.get<Ticket[]>('/tickets', { params });
  return response.data;
};

export const createTicket = async (data: { title: string; description: string; priority?: string }) => {
  const response = await apiClient.post<Ticket>('/tickets', data);
  return response.data;
};

export const reviewTicket = async (ticketId: string, action: 'Approved' | 'Rejected', editedResponse?: string) => {
  const response = await apiClient.post<Ticket>(`/tickets/${ticketId}/review`, {
    action,
    edited_response: editedResponse,
  });
  return response.data;
};

export const getReportsSummary = async () => {
  const response = await apiClient.get<ReportSummaryItem[]>('/reports/summary');
  return response.data;
};
