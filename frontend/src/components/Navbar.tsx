"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Shield, LogOut, User } from "lucide-react";
import { getName, getRole, logout } from "@/lib/api";

export default function Navbar() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [role, setRole] = useState("");

  useEffect(() => {
    setName(getName() || "Usuario");
    setRole(getRole() || "");
  }, []);

  const handleLogout = () => {
    logout();
    router.push("/login");
  };

  const getRoleLabel = (r: string) => {
    if (r === "student") return "Estudiante";
    if (r === "teacher") return "Docente";
    if (r === "admin") return "Administrador";
    return "";
  };

  const getRoleColor = (r: string) => {
    if (r === "student") return "bg-emerald-500/10 text-emerald-400 border-emerald-500/20";
    if (r === "teacher") return "bg-blue-500/10 text-blue-400 border-blue-500/20";
    if (r === "admin") return "bg-red-500/10 text-red-400 border-red-500/20";
    return "";
  };

  return (
    <nav className="glass-panel sticky top-0 z-40 w-full px-6 py-4 flex items-center justify-between border-b">
      {/* Brand logo */}
      <Link href="/" className="flex items-center gap-2 hover:opacity-90 transition-opacity">
        <Shield className="h-6 w-6 text-indigo-400" />
        <span className="text-xl font-bold tracking-tight bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
          IntegriEval
        </span>
      </Link>

      {/* User Actions */}
      <div className="flex items-center gap-4">
        {/* User Info Card */}
        <div className="flex items-center gap-2.5 px-3 py-1.5 rounded-xl bg-zinc-900/30 border border-zinc-800/80">
          <div className="h-7 w-7 rounded-lg bg-zinc-800 flex items-center justify-center text-zinc-300">
            <User className="h-4 w-4" />
          </div>
          <div className="flex flex-col text-left">
            <span className="text-xs font-semibold text-zinc-200 leading-tight">{name}</span>
            <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded border mt-0.5 inline-block text-center uppercase tracking-wide leading-none ${getRoleColor(role)}`}>
              {getRoleLabel(role)}
            </span>
          </div>
        </div>

        {/* Logout Button */}
        <button
          onClick={handleLogout}
          className="p-2.5 rounded-xl border border-zinc-800/80 bg-zinc-900/20 hover:bg-red-500/10 hover:border-red-500/30 text-zinc-400 hover:text-red-400 transition-all duration-200 cursor-pointer"
          title="Cerrar Sesión"
        >
          <LogOut className="h-4.5 w-4.5" />
        </button>
      </div>
    </nav>
  );
}
