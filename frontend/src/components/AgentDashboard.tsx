import React, { Suspense, lazy, useEffect, useState, useCallback } from 'react';
import { getTickets } from '../api/client';
import { Ticket } from '../types';
import { SubmitTicketForm } from './SubmitTicketForm';
import { ReviewTicketModal } from './ReviewTicketModal';

// Code-split heavy Recharts library with React.lazy
const AnalyticsDashboard = lazy(() => import('./AnalyticsDashboard'));

export const AgentDashboard: React.FC = () => {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [selectedTicket, setSelectedTicket] = useState<Ticket | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [filterView, setFilterView] = useState<'pending' | 'all'>('pending');

  const fetchTickets = useCallback(async () => {
    setIsLoading(true);
    try {
      const params = filterView === 'pending' ? { ai_review_status: 'Pending' } : undefined;
      const data = await getTickets(params);
      setTickets(data);
    } catch (err) {
      console.error('Failed to load tickets', err);
    } finally {
      setIsLoading(false);
    }
  }, [filterView]);

  useEffect(() => {
    fetchTickets();
  }, [fetchTickets]);

  return (
    <div className="min-h-screen bg-slate-100 p-6 sm:p-10 space-y-8 font-sans">
      {/* Top Header */}
      <header className="flex flex-col sm:flex-row justify-between sm:items-center gap-4 bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
        <div>
          <div className="flex items-center gap-2">
            <span className="h-3 w-3 rounded-full bg-emerald-500 animate-pulse"></span>
            <span className="text-xs font-bold uppercase tracking-wider text-indigo-600">Enterprise AI Operations</span>
          </div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight mt-1">
            IT Helpdesk & Guardrailed Triage
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Deterministic RAG Triage • Mistral API • Real-Time Human Review Verification
          </p>
        </div>

        <div className="flex items-center gap-2 bg-slate-100 p-1.5 rounded-xl border border-slate-200">
          <button
            onClick={() => setFilterView('pending')}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition ${
              filterView === 'pending'
                ? 'bg-white text-indigo-600 shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Pending Reviews
          </button>
          <button
            onClick={() => setFilterView('all')}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition ${
              filterView === 'all'
                ? 'bg-white text-indigo-600 shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            All Tickets
          </button>
        </div>
      </header>

      {/* Code-Split Lazy Loaded Analytics with Suspense Boundary */}
      <Suspense
        fallback={
          <div className="h-64 w-full bg-white animate-pulse rounded-xl border border-slate-200 flex items-center justify-center text-slate-400 text-sm">
            <div className="flex items-center gap-3">
              <span className="h-4 w-4 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin"></span>
              <span>Loading Analytics Engine & Charts...</span>
            </div>
          </div>
        }
      >
        <AnalyticsDashboard />
      </Suspense>

      {/* Main Content Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Submit Request Panel */}
        <div className="lg:col-span-1">
          <SubmitTicketForm onCreated={fetchTickets} />
        </div>

        {/* Tickets Queue */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-200 flex justify-between items-center bg-slate-50/50">
              <div className="flex items-center gap-2">
                <h2 className="text-sm font-bold text-slate-800">
                  {filterView === 'pending' ? 'Triage Review Queue' : 'All IT Tickets'}
                </h2>
                <span className="text-xs bg-indigo-100 text-indigo-800 px-2 py-0.5 rounded-full font-bold">
                  {tickets.length}
                </span>
              </div>
              <button
                onClick={fetchTickets}
                className="text-xs text-indigo-600 hover:text-indigo-800 font-semibold"
              >
                ↻ Refresh
              </button>
            </div>

            {isLoading ? (
              <div className="p-12 text-center text-slate-400 text-sm">
                Fetching updated ticket statuses...
              </div>
            ) : tickets.length === 0 ? (
              <div className="p-12 text-center text-slate-400 text-sm">
                No tickets currently match this view.
              </div>
            ) : (
              <div className="divide-y divide-slate-100">
                {tickets.map((t) => (
                  <div
                    key={t.id}
                    className="p-5 hover:bg-slate-50/80 transition flex flex-col sm:flex-row sm:items-center justify-between gap-4"
                  >
                    <div className="space-y-1.5 flex-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span
                          className={`text-[11px] px-2 py-0.5 rounded font-bold uppercase ${
                            t.priority === 'Critical'
                              ? 'bg-rose-100 text-rose-800'
                              : t.priority === 'High'
                              ? 'bg-amber-100 text-amber-800'
                              : 'bg-slate-100 text-slate-700'
                          }`}
                        >
                          {t.priority}
                        </span>

                        <span className="text-[11px] px-2 py-0.5 rounded bg-indigo-50 text-indigo-700 font-medium font-mono">
                          {t.ai_triage_category || 'Unassigned'}
                        </span>

                        <span
                          className={`text-[11px] px-2 py-0.5 rounded font-semibold ${
                            t.ai_review_status === 'Pending'
                              ? 'bg-amber-50 text-amber-700 border border-amber-200'
                              : t.ai_review_status === 'Approved'
                              ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                              : t.ai_review_status === 'Failed'
                              ? 'bg-rose-50 text-rose-700 border border-rose-200'
                              : 'bg-slate-50 text-slate-600'
                          }`}
                        >
                          AI: {t.ai_review_status}
                        </span>

                        <span className="text-[11px] text-slate-400">
                          Status: {t.ticket_status}
                        </span>
                      </div>

                      <h4 className="text-sm font-bold text-slate-900">{t.title}</h4>
                      <p className="text-xs text-slate-500 line-clamp-2 leading-relaxed">
                        {t.description}
                      </p>
                    </div>

                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => setSelectedTicket(t)}
                        className="w-full sm:w-auto px-4 py-2 bg-indigo-50 text-indigo-700 border border-indigo-200/80 rounded-lg text-xs font-bold hover:bg-indigo-100 transition whitespace-nowrap"
                      >
                        Inspect AI Draft & Citations
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Review Modal Dialog */}
      {selectedTicket && (
        <ReviewTicketModal
          ticket={selectedTicket}
          onClose={() => setSelectedTicket(null)}
          onActionComplete={fetchTickets}
        />
      )}
    </div>
  );
};

export default AgentDashboard;
