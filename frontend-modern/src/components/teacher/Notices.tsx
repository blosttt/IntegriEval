"use client";

import { AlertCircle, CheckCircle2, X } from "lucide-react";
import { useDashboard } from "./DashboardContext";
import { Panel } from "./ui";

export default function Notices() {
  const { error, setError, success, setSuccess, flashLink } = useDashboard();
  return (
    <>
      {error && (
        <div className="flex items-center justify-between rounded-control border border-red-500/20 bg-red-500/10 p-4 text-xs text-red-400">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
          <button type="button" onClick={() => setError("")} className="text-red-400 hover:text-white">
            <X className="h-4 w-4" />
          </button>
        </div>
      )}
      {success && (
        <div className="flex items-center justify-between rounded-control border border-emerald-500/20 bg-emerald-500/10 p-4 text-xs text-emerald-400">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4 shrink-0" />
            <span>{success}</span>
          </div>
          <button type="button" onClick={() => setSuccess("")} className="text-emerald-400 hover:text-white">
            <X className="h-4 w-4" />
          </button>
        </div>
      )}
      {flashLink && (
        <Panel size="sm" radius="control" stack={false} className="text-sm text-brand-ink">
          <a href={flashLink} target="_blank" rel="noopener noreferrer">
            Abrir Flash Test del estudiante ↗
          </a>
          <p className="mt-2 text-xs text-muted">{flashLink}</p>
        </Panel>
      )}
    </>
  );
}
