"use client";

import type { ComponentType } from "react";
import Navbar from "@/components/Navbar";
import TeacherTutorial from "@/components/TeacherTutorial";
import AppointmentForm from "@/components/AppointmentForm";
import StudentEditor from "@/components/StudentEditor";
import AdminTeacherContext from "@/components/AdminTeacherContext";
import { DashboardProvider, useDashboard } from "@/components/teacher/DashboardContext";
import DashboardHeader from "@/components/teacher/DashboardHeader";
import OperationsBar from "@/components/teacher/OperationsBar";
import Notices from "@/components/teacher/Notices";
import TabNav from "@/components/teacher/TabNav";
import MarkdownPreviewModal from "@/components/teacher/MarkdownPreviewModal";
import CoursesTab from "@/components/teacher/tabs/CoursesTab";
import StudentsTab from "@/components/teacher/tabs/StudentsTab";
import EvaluationsTab from "@/components/teacher/tabs/EvaluationsTab";
import MaterialsTab from "@/components/teacher/tabs/MaterialsTab";
import ReportsTab from "@/components/teacher/tabs/ReportsTab";
import QuestionsTab from "@/components/teacher/tabs/QuestionsTab";
import ResultsTab from "@/components/teacher/tabs/ResultsTab";
import AppointmentsTab from "@/components/teacher/tabs/AppointmentsTab";
import AvailabilityTab from "@/components/teacher/tabs/AvailabilityTab";
import type { TabId } from "@/components/teacher/types";

const TAB_VIEWS: Record<TabId, ComponentType> = {
  courses: CoursesTab,
  students: StudentsTab,
  evaluations: EvaluationsTab,
  materials: MaterialsTab,
  reports: ReportsTab,
  questions: QuestionsTab,
  results: ResultsTab,
  appointments: AppointmentsTab,
  availability: AvailabilityTab,
};

const SHELL = "flex min-h-screen flex-col bg-canvas text-fg font-ui";

function DashboardView() {
  const {
    loading,
    activeTab,
    setActiveTab,
    isAssistant,
    adminTeacher,
    courses,
    students,
    selectedCourseId,
    studentToEdit,
    setStudentToEdit,
    appointmentDraft,
    setAppointmentDraft,
    saveAppointment,
    loadInitialData,
    loadCourseSubData,
  } = useDashboard();

  if (loading) {
    return (
      <div className={SHELL}>
        <Navbar />
        <div className="flex flex-1 items-center justify-center">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-brand border-t-transparent" />
        </div>
      </div>
    );
  }

  const ActiveTab = TAB_VIEWS[activeTab];

  return (
    <div className={`${SHELL} pb-20`}>
      <Navbar />
      {appointmentDraft && (
        <AppointmentForm
          students={students}
          initial={appointmentDraft}
          onSave={saveAppointment}
          onClose={() => setAppointmentDraft(null)}
        />
      )}
      <TeacherTutorial onStep={setActiveTab} assistant={isAssistant} />
      {studentToEdit && selectedCourseId && (
        <StudentEditor
          courseId={selectedCourseId}
          student={studentToEdit}
          onClose={() => setStudentToEdit(null)}
          onSaved={() => loadCourseSubData(selectedCourseId)}
        />
      )}
      <main className="mx-auto mt-6 flex w-full max-w-[1360px] flex-col gap-6 px-4 pt-2.5 sm:px-6">
        {adminTeacher && (
          <AdminTeacherContext person={adminTeacher} courses={courses} onChanged={loadInitialData} />
        )}
        <DashboardHeader />
        <OperationsBar />
        <Notices />
        <TabNav />
        <ActiveTab />
      </main>
      <MarkdownPreviewModal />
    </div>
  );
}

export default function TeacherDashboard() {
  return (
    <DashboardProvider>
      <DashboardView />
    </DashboardProvider>
  );
}
