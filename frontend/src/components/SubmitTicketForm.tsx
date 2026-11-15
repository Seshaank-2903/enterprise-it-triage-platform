import React, { useState } from 'react';
import { createTicket } from '../api/client';
import { Priority } from '../types';

interface Props {
  onCreated: () => void;
}

export const SubmitTicketForm: React.FC<Props> = ({ onCreated }) => {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [priority, setPriority] = useState<Priority>('Medium');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setStatusMessage(null);
    try {
      await createTicket({ title, description, priority });
      setTitle('');
      setDescription('');
      setPriority('Medium');
      setStatusMessage('Ticket submitted successfully! AI triage completed.');
      onCreated();
    } catch (err: unknown) {
      console.error('Failed to submit ticket', err);
      setStatusMessage('Failed to submit ticket. Please check connection.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-base font-bold text-slate-800">Submit IT Request</h2>
        <span className="text-xs bg-indigo-50 text-indigo-700 px-2 py-0.5 rounded font-medium">
          Instant AI Triage
        </span>
      </div>

      {statusMessage && (
        <div className={`p-3 rounded-lg text-xs mb-4 ${
          statusMessage.includes('successfully') ? 'bg-emerald-50 text-emerald-800' : 'bg-rose-50 text-rose-800'
        }`}>
          {statusMessage}
        </div>
      )}

      <div className="space-y-4">
        <div>
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wide">
            Subject / Issue Title
          </label>
          <input
            type="text"
            required
            className="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 focus:outline-none transition"
            placeholder="e.g. Cannot access AWS Production database"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
          />
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wide">
            Reported Priority
          </label>
          <select
            value={priority}
            onChange={(e) => setPriority(e.target.value as Priority)}
            className="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 focus:outline-none bg-white"
          >
            <option value="Low">Low - Informational / Minor</option>
            <option value="Medium">Medium - Standard Request</option>
            <option value="High">High - Significant Impairment (Requires Review)</option>
            <option value="Critical">Critical - Production Outage</option>
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wide">
            Detailed Description & Error Context
          </label>
          <textarea
            required
            rows={4}
            className="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 focus:outline-none transition"
            placeholder="Include screenshots, error logs, user accounts, and urgency details..."
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
        </div>

        <button
          type="submit"
          disabled={isSubmitting}
          className="w-full inline-flex items-center justify-center rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white shadow hover:bg-indigo-500 focus:outline-none disabled:opacity-50 transition"
        >
          {isSubmitting ? 'Evaluating Knowledge Base & Triaging...' : 'Submit Request'}
        </button>
      </div>
    </form>
  );
};
