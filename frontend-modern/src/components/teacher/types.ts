import type { ComponentType } from "react";

export type TabId =
  | "courses"
  | "students"
  | "evaluations"
  | "materials"
  | "reports"
  | "questions"
  | "results"
  | "appointments"
  | "availability";

export const TAB_IDS: TabId[] = [
  "courses",
  "students",
  "evaluations",
  "materials",
  "reports",
  "questions",
  "results",
  "appointments",
  "availability",
];

export type IconType = ComponentType<{ className?: string; size?: number }>;
