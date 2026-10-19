"use client";

import Navbar from "@/components/Navbar";
import TeacherTutorial from "@/components/TeacherTutorial";
import AppointmentForm from "@/components/AppointmentForm";
import StudentEditor from "@/components/StudentEditor";
import AdminTeacherContext from "@/components/AdminTeacherContext";
import { DashboardProvider, useDashboard } from "@/components/teacher/DashboardContext";
import DashboardHeader from "@/components/teacher/DashboardHeader";
import Notices from "@/components/teacher/Notices";
import TabNav from "@/components/teacher/TabNav";
import CoursesTab from "@/components/teacher/tabs/CoursesTab";
import StudentsTab from "@/components/teacher/tabs/StudentsTab";
import EvaluationsTab from "@/components/teacher/tabs/EvaluationsTab";
import MaterialsTab from "@/components/teacher/tabs/MaterialsTab";
import ReportsTab from "@/components/teacher/tabs/ReportsTab";
import QuestionsTab from "@/components/teacher/tabs/QuestionsTab";
import ResultsTab from "@/components/teacher/tabs/ResultsTab";
import AppointmentsTab from "@/components/teacher/tabs/AppointmentsTab";
import AvailabilityTab from "@/components/teacher/tabs/AvailabilityTab";

function DashboardView() {
  const {
    loading, activeTab, accountRole, adminTeacher, courses, students, selectedCourseId, selectedEvalId,
    appointmentDraft, setAppointmentDraft, saveAppointment, studentToEdit, setStudentToEdit,
    loadCourseSubData, loadInitialData, setActiveTab,
  } = useDashboard();

  if (loading) {
    return (
      <div className="ie-shell ie-teacher-view flex min-h-screen flex-col">
        <Navbar />
        <div className="flex flex-1 items-center justify-center">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-brand border-t-transparent" />
        </div>
      </div>
    );
  }

  return (
    <div className="ie-shell ie-teacher-view flex min-h-screen flex-col pb-20">
      <Navbar />
      {appointmentDraft && (
        <AppointmentForm
          students={students}
          initial={appointmentDraft}
          onSave={saveAppointment}
          onClose={() => setAppointmentDraft(null)}
        />
      )}
      <TeacherTutorial onStep={(tab: any) => setActiveTab(tab)} assistant={accountRole === "ayudante"} />
      {studentToEdit && selectedCourseId && (
        <StudentEditor
          courseId={selectedCourseId}
          student={studentToEdit}
          onClose={() => setStudentToEdit(null)}
          onSaved={() => loadCourseSubData(selectedCourseId)}
        />
      )}

      <main className="mx-auto mt-6 flex w-full max-w-7xl flex-col gap-6 px-4 sm:px-6">
        {adminTeacher && (
          <AdminTeacherContext person={adminTeacher} courses={courses} onChanged={loadInitialData} />
        )}
        <DashboardHeader />
        <Notices />
        <TabNav />

        {activeTab === "courses" && <CoursesTab />}
        {activeTab === "students" && <StudentsTab />}
        {activeTab === "evaluations" && <EvaluationsTab />}
        {activeTab === "materials" && <MaterialsTab />}
        {activeTab === "reports" && <ReportsTab />}
        {activeTab === "questions" && <QuestionsTab />}
        {activeTab === "results" && <ResultsTab />}
        {activeTab === "appointments" && <AppointmentsTab key={selectedEvalId ?? "none"} />}
        {activeTab === "availability" && <AvailabilityTab />}
      </main>
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
