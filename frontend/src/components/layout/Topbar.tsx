"use client";
import { useState, useEffect } from "react";
import { ChevronDown, Bell } from "lucide-react";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { useCompanyId, setSelectedCompanyId } from "@/hooks/useCompanyId";

interface Company {
  id: number;
  name: string;
}

export default function Topbar() {
  const { isSuperAdmin } = useAuth();
  const selectedCompanyId = useCompanyId();
  const [companies, setCompanies] = useState<Company[]>([]);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (isSuperAdmin) {
      api.getCompanies().then(setCompanies).catch(() => {});
    }
  }, [isSuperAdmin]);

  // Auto-select first company if none selected
  useEffect(() => {
    if (isSuperAdmin && companies.length > 0 && !selectedCompanyId) {
      setSelectedCompanyId(companies[0].id);
    }
  }, [isSuperAdmin, companies, selectedCompanyId]);

  const selectedCompany = companies.find((c) => c.id === selectedCompanyId);

  return (
    <header className="h-14 border-b border-slate-200 bg-white flex items-center justify-between px-6">
      <div className="flex items-center gap-4">
        {isSuperAdmin && companies.length > 0 && (
          <div className="relative">
            <button
              onClick={() => setOpen(!open)}
              className="flex items-center gap-2 px-3 py-1.5 text-sm font-medium border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors"
            >
              <span>{selectedCompany?.name || "Select Company"}</span>
              <ChevronDown size={14} />
            </button>
            {open && (
              <div className="absolute top-full left-0 mt-1 w-56 bg-white border border-slate-200 rounded-lg shadow-xl z-50">
                {companies.map((c) => (
                  <button
                    key={c.id}
                    onClick={() => {
                      setSelectedCompanyId(c.id);
                      setOpen(false);
                    }}
                    className={`block w-full text-left px-4 py-2.5 text-sm hover:bg-slate-50 ${
                      c.id === selectedCompanyId ? "bg-red-50 text-red-600 font-medium" : "text-slate-700"
                    }`}
                  >
                    {c.name}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
      <div className="flex items-center gap-3">
        <button className="relative p-2 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100">
          <Bell size={18} />
        </button>
      </div>
    </header>
  );
}
