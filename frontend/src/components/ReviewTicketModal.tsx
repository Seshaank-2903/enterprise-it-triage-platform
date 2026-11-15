import React, { useState } from 'react';
import { reviewTicket } from '../api/client';
import { Ticket } from '../types';

interface Props {
  ticket: Ticket;
  onClose: () => void;
  onActionComplete: () => void;
}

export const ReviewTicketModal: React.FC<Props> = ({ ticket, onClose, onActionComplete }) => {
  const [responseDraft, setResponseDraft] = useState(ticket.ai_drafted_response || '');
  const [isProcessing, setIsProcessing] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleReview = async (action: 'Approved' | 'Rejected') => {
    setIsProcessing(true);
    setErrorMessage(null);
    try {
      await reviewTicket(ticket.id, action, responseDraft);
      onActionComplete();
      onClose();
    } catch (err: unknown) {
      console.error('Action failed', err);
      const message = err instanceof Error ? err.message : 'Failed to process ticket review.';
      setErrorMessage(message);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="bg-white max-w-3xl w-full rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[92vh] border border-slate-200">
        {/* Header */}
        <div className="bg-slate-900 px-6 py-4 flex justify-between items-center text-white">
          <div className="flex items-center gap-3">
            <span className="text-xs uppercase tracking-wider font-semibold bg-indigo-500/20 text-indigo-300 border border-indigo-400/30 px-2.5 py-1 rounded-md font-mono">
              {ticket.ai_triage_category || 'Unassigned'}
            </span>
            <span className={`text-xs px-2.5 py-1 rounded-md font-bold uppercase tracking-wider ${
              ticket.priority === 'High' || ticket.priority === 'Critical'
                ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
            }`}>
              {ticket.priority} Priority
            </span>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white p-1 rounded-md transition"
            aria-label="Close"
          >
            ✕
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto space-y-6">
          {errorMessage && (
            <div className="p-3 bg-rose-50 border border-rose-200 text-rose-800 text-xs rounded-lg">
              {errorMessage}
            </div>
          )}

          <div>
            <h3 className="text-lg font-bold text-slate-900">{ticket.title}</h3>
            <div className="mt-2 text-sm text-slate-700 bg-slate-50 p-4 rounded-xl border border-slate-200 whitespace-pre-wrap leading-relaxed">
              {ticket.description}
            </div>
          </div>

          {/* RAG Source Citations */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                Retrieved IT Documentation Sources (RAG)
              </h4>
              <span className="text-xs text-slate-400">
                {ticket.ai_citations?.length || 0} Sources Retrieved
              </span>
            </div>

            {ticket.ai_citations && ticket.ai_citations.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                {ticket.ai_citations.map((cite, idx) => (
                  <a
                    key={idx}
                    href={cite.url}
                    target="_blank"
                    rel="noreferrer"
                    className="flex flex-col p-3 bg-indigo-50/60 border border-indigo-100/80 rounded-lg hover:bg-indigo-100/70 transition group"
                  >
                    <span className="text-xs font-semibold text-indigo-900 group-hover:text-indigo-950">
                      {cite.title}
                    </span>
                    <span className="text-[11px] text-indigo-500 truncate font-mono mt-1 underline">
                      {cite.url}
                    </span>
                  </a>
                ))}
              </div>
            ) : (
              <div className="text-xs text-slate-400 italic p-3 bg-slate-50 rounded-lg border border-slate-200">
                No external IT citations were attached to this request.
              </div>
            )}
          </div>

          {/* AI Draft Response with Editing */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                AI Suggested Solution (Agent Editable)
              </label>
              <span className="text-[11px] text-slate-400">Human-in-the-Loop review before dispatch</span>
            </div>
            <textarea
              rows={5}
              className="mt-1 block w-full rounded-xl border border-slate-300 p-3.5 text-sm text-slate-800 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 focus:outline-none transition leading-relaxed"
              value={responseDraft}
              onChange={(e) => setResponseDraft(e.target.value)}
              placeholder="Enter resolution notes or modify the AI suggested response..."
            />
          </div>
        </div>

        {/* Actions Footer */}
        <div className="bg-slate-50 px-6 py-4 border-t border-slate-200 flex items-center justify-between">
          <div className="text-xs text-slate-500">
            Current Review Status: <span className="font-semibold text-amber-700">{ticket.ai_review_status}</span>
          </div>
          <div className="flex gap-3">
            <button
              onClick={() => handleReview('Rejected')}
              disabled={isProcessing}
              className="px-4 py-2 border border-rose-300 text-rose-700 bg-white rounded-lg text-sm font-semibold hover:bg-rose-50 focus:outline-none disabled:opacity-50 transition"
            >
              Reject / Escalate
            </button>
            <button
              onClick={() => handleReview('Approved')}
              disabled={isProcessing}
              className="px-5 py-2 bg-emerald-600 text-white rounded-lg text-sm font-semibold hover:bg-emerald-500 focus:outline-none disabled:opacity-50 shadow-sm transition"
            >
              Approve & Dispatch
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
