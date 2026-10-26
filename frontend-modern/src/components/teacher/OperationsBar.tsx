"use client";

import EvaluationOperations from "@/components/EvaluationOperations";
import { useDashboard } from "./DashboardContext";

export default function OperationsBar() {
  const { selectedCourseId, selectedEval, refreshCourseEvals } = useDashboard();
  if (!selectedCourseId || !selectedEval) return null;
  return (
    <EvaluationOperations
      courseId={selectedCourseId}
      evaluation={selectedEval}
      onChanged={refreshCourseEvals}
    />
  );
}
