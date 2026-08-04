"use client";
import { Bell } from "lucide-react";

export default function Topbar() {
  return (
    <header className="h-14 border-b border-slate-200 bg-white flex items-center justify-between px-6">
      <div />
      <div className="flex items-center gap-3">
        <button className="relative p-2 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100">
          <Bell size={18} />
        </button>
      </div>
    </header>
  );
}
