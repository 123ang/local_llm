"use client";
import { useState, useEffect } from "react";
import { Plus, X, ToggleLeft, ToggleRight } from "lucide-react";
import { api } from "@/lib/api";

export default function UsersPage() {
  const [users, setUsers] = useState<any[]>([]);
  const [companies, setCompanies] = useState<any[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ email: "", full_name: "", password: "", role: "user", company_id: "" });
  const [loading, setLoading] = useState(false);

  useEffect(() => { loadUsers(); loadCompanies(); }, []);

  const loadUsers = async () => { try { setUsers(await api.getUsers()); } catch {} };
  const loadCompanies = async () => { try { setCompanies(await api.getCompanies()); } catch {} };

  const handleCreate = async () => {
    if (!form.email || !form.full_name || !form.password) return;
    setLoading(true);
    try {
      await api.createUser({ ...form, company_id: form.company_id ? Number(form.company_id) : null });
      await loadUsers();
      setShowForm(false); setForm({ email: "", full_name: "", password: "", role: "user", company_id: "" });
    } catch {}
    setLoading(false);
  };

  const toggleActive = async (user: any) => {
    try { await api.updateUser(user.id, { is_active: !user.is_active }); await loadUsers(); } catch {}
  };

  const roleBadge = (role: string) => {
    const map: Record<string, string> = {
      super_admin: "bg-red-100 text-red-700",
      admin: "bg-orange-100 text-orange-700",
      user: "bg-blue-100 text-blue-700",
    };
    return <span className={`px-2 py-1 text-xs font-medium rounded-full ${map[role] || "bg-slate-100"}`}>{role.replace("_", " ")}</span>;
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div><h1 className="text-2xl font-bold text-slate-900">Users</h1><p className="text-slate-500 mt-1">Manage platform users</p></div>
        <button onClick={() => setShowForm(true)} className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-red-600 hover:bg-red-700 text-white text-sm font-medium"><Plus size={16} /> Add User</button>
      </div>

      {showForm && (
        <div className="bg-white rounded-xl border border-slate-200 p-6">
          <div className="flex items-center justify-between mb-4"><h2 className="text-lg font-semibold">New User</h2><button onClick={() => setShowForm(false)} className="text-slate-400"><X size={20} /></button></div>
          <div className="grid grid-cols-2 gap-4">
            <div><label className="block text-sm font-medium text-slate-700 mb-1">Full Name</label><input value={form.full_name} onChange={e => setForm({...form, full_name: e.target.value})} className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" /></div>
            <div><label className="block text-sm font-medium text-slate-700 mb-1">Email</label><input type="email" value={form.email} onChange={e => setForm({...form, email: e.target.value})} className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" /></div>
            <div><label className="block text-sm font-medium text-slate-700 mb-1">Password</label><input type="password" value={form.password} onChange={e => setForm({...form, password: e.target.value})} className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" /></div>
            <div><label className="block text-sm font-medium text-slate-700 mb-1">Role</label><select value={form.role} onChange={e => setForm({...form, role: e.target.value})} className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm"><option value="user">User</option><option value="admin">Admin</option><option value="super_admin">Super Admin</option></select></div>
            <div><label className="block text-sm font-medium text-slate-700 mb-1">Company</label><select value={form.company_id} onChange={e => setForm({...form, company_id: e.target.value})} className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm"><option value="">No company (platform)</option>{companies.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}</select></div>
          </div>
          <div className="mt-4 flex gap-2"><button onClick={handleCreate} disabled={loading} className="px-4 py-2 rounded-lg bg-red-600 hover:bg-red-700 text-white text-sm font-medium disabled:opacity-50">{loading ? "Creating..." : "Create User"}</button><button onClick={() => setShowForm(false)} className="px-4 py-2 rounded-lg border border-slate-300 text-sm text-slate-600 hover:bg-slate-50">Cancel</button></div>
        </div>
      )}

      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
        <table className="w-full">
          <thead className="bg-slate-50 border-b border-slate-200"><tr>
            <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase">User</th>
            <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase">Email</th>
            <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase">Role</th>
            <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase">Company</th>
            <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase">Status</th>
            <th className="px-6 py-3"></th>
          </tr></thead>
          <tbody className="divide-y divide-slate-100">
            {users.map(u => (
              <tr key={u.id} className="hover:bg-slate-50">
                <td className="px-6 py-4 text-sm font-medium text-slate-900">{u.full_name}</td>
                <td className="px-6 py-4 text-sm text-slate-600">{u.email}</td>
                <td className="px-6 py-4">{roleBadge(u.role)}</td>
                <td className="px-6 py-4 text-sm text-slate-500">{u.company_name || "—"}</td>
                <td className="px-6 py-4"><span className={`px-2 py-1 text-xs font-medium rounded-full ${u.is_active ? "bg-emerald-100 text-emerald-700" : "bg-slate-100 text-slate-500"}`}>{u.is_active ? "Active" : "Inactive"}</span></td>
                <td className="px-6 py-4"><button onClick={() => toggleActive(u)} className="text-slate-400 hover:text-slate-600">{u.is_active ? <ToggleRight size={20} className="text-emerald-500" /> : <ToggleLeft size={20} />}</button></td>
              </tr>
            ))}
          </tbody>
        </table>
        {users.length === 0 && <div className="text-center py-12 text-slate-400">No users found</div>}
      </div>
    </div>
  );
}
