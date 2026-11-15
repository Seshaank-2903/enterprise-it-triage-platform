export type TicketStatus = 'Open' | 'In Progress' | 'Resolved' | 'Closed';
export type AIReviewStatus = 'Pending' | 'Approved' | 'Rejected' | 'Not Required' | 'Failed';
export type Priority = 'Low' | 'Medium' | 'High' | 'Critical';

export interface Citation {
  title: string;
  url: string;
}

export interface Ticket {
  id: string;
  title: string;
  description: string;
  ticket_status: TicketStatus;
  ai_review_status: AIReviewStatus;
  priority: Priority;
  ai_triage_category: string | null;
  ai_drafted_response: string | null;
  ai_citations: Citation[];
  created_at: string;
  updated_at: string;
  resolved_at?: string | null;
}

export interface ReportSummaryItem {
  category: string;
  total: number;
  avg_hours: number;
  pending_reviews: number;
}
