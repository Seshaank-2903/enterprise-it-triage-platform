import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import AgentDashboard from '../components/AgentDashboard';
import * as client from '../api/client';
import { Ticket } from '../types';

vi.mock('../api/client');

describe('AgentDashboard', () => {
  const mockTickets: Ticket[] = [
    {
      id: 'ticket-1',
      title: 'Database connection issue',
      description: 'Cannot connect to postgres cluster',
      ticket_status: 'In Progress',
      ai_review_status: 'Pending',
      priority: 'High',
      ai_triage_category: 'Access',
      ai_drafted_response: 'Check VPN credentials',
      ai_citations: [{ title: 'IAM Guide', url: 'https://kb.corp/iam' }],
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders dashboard headers and ticket queue', async () => {
    vi.mocked(client.getTickets).mockResolvedValue(mockTickets);
    vi.mocked(client.getReportsSummary).mockResolvedValue([
      { category: 'Access', total: 5, avg_hours: 1.5, pending_reviews: 1 },
    ]);

    render(<AgentDashboard />);

    expect(screen.getByText(/IT Helpdesk & Guardrailed Triage/i)).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('Database connection issue')).toBeInTheDocument();
      expect(screen.getByText('Inspect AI Draft & Citations')).toBeInTheDocument();
    });
  });
});
