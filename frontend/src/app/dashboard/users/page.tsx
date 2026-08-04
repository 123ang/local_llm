"use client";
import { useState, useEffect } from "react";
import { Plus, X, ToggleLeft, ToggleRight, KeyRound } from "lucide-react";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { useI18n } from "@/lib/i18n-context";

export default function UsersPage() {
  const { t } = useI18n();
  const { user, isSuperAdmin } = useAuth();
  const [users, setUsers] = useState<any[]>([]);
  const [companies, setCompanies] = useState<any[]>([]);
  const [departments, setDepartments] = useState<any[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ email: "", full_name: "", password: "", role: "user", company_id: "", department_ids: [] as number[] });
  const [grantUser, setGrantUser] = useState<any | null>(null);
  const [grantDepartmentIds, setGrantDepartmentIds] = useState<number[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => { loadUsers(); loadCompanies(); }, []);
  useEffect(() => {
    const companyId = isSuperAdmin ? (form.company_id ? Number(form.company_id) : undefined) : (user?.company_id ?? undefined);
    if (!companyId) {
      setDepartments([]);
      return;
    }
    api.getDepartments(companyId).then(setDepartments).catch(() => setDepartments([]));
  }, [form.company_id, isSuperAdmin, user?.company_id]);

  const generalDepartmentId = departments.find((department) =>
    department.slug === "general" || department.name?.toLowerCase() === "general"
  )?.id;

  useEffect(() => {
    if (!showForm || !form.company_id || form.role === "super_admin" || !generalDepartmentId) return;
    setForm((current) =>
      current.department_ids.length > 0 ? current : { ...current, department_ids: [generalDepartmentId] }
    );
  }, [showForm, form.company_id, form.role, generalDepartmentId]);

  const loadUsers = async () => { try { setUsers(await api.getUsers()); } catch {} };
  const loadCompanies = async () => { try { setCompanies(await api.getCompanies()); } catch {} };

  const openCreateForm = () => {
    setGrantUser(null);
    setDepartments([]);
    setForm({ email: "", full_name: "", password: "", role: "user", company_id: "", department_ids: [] });
    setShowForm(true);
  };

  const handleCreate = async () => {
    if (!form.email || !form.full_name || !form.password) return;
    setLoading(true);
    try {
      const department_ids =
        form.department_ids.length > 0
          ? form.department_ids
          : form.company_id && form.role !== "super_admin" && generalDepartmentId
            ? [generalDepartmentId]
            : [];
      await api.createUser({ ...form, company_id: form.company_id ? Number(form.company_id) : null, department_ids });
      await loadUsers();
      setShowForm(false); setForm({ email: "", full_name: "", password: "", role: "user", company_id: "", department_ids: [] });
    } catch {}
    setLoading(false);
  };

  const toggleActive = async (user: any) => {
    if (!isSuperAdmin) return;
    try { await api.updateUser(user.id, { is_active: !user.is_active }); await loadUsers(); } catch {}
  };

  const openGrantPanel = async (targetUser: any) => {
    setGrantUser(targetUser);
    setGrantDepartmentIds(targetUser.department_ids || []);
    if (targetUser.company_id) {
      try {
        setDepartments(await api.getDepartments(targetUser.company_id));
      } catch {}
    }
  };

  const saveGrants = async () => {
    if (!grantUser) return;
    setLoading(true);
    try {
      await api.updateUserDepartmentGrants(grantUser.id, grantDepartmentIds);
      await loadUsers();
      setGrantUser(null);
    } catch {}
    setLoading(false);
  };

  const toggleGrant = (departmentId: number) => {
    setGrantDepartmentIds((current) =>
      current.includes(departmentId)
        ? current.filter((id) => id !== departmentId)
        : [...current, departmentId]
    );
  };

  const roleBadge = (role: string) => {
    const map: Record<string, string> = {
      super_admin: "bg-red-100 text-red-700",
      admin: "bg-orange-100 text-orange-700",
      user: "bg-blue-100 text-blue-700",
    };
    const labels: Record<string, string> = {
      super_admin: t("common.superAdmin"),
      admin: t("common.admin"),
      user: t("common.normalUser"),
    };
    return <span className={`px-2 py-1 text-xs font-medium rounded-full ${map[role] || "bg-slate-100"}`}>{labels[role] || role.replace("_", " ")}</span>;
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div><h1 className="text-2xl font-bold text-slate-900">{t("users.title")}</h1><p className="text-slate-500 mt-1">{t("users.copy")}</p></div>
        {isSuperAdmin && <button onClick={openCreateForm} className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-red-600 hover:bg-red-700 text-white text-sm font-medium"><Plus size={16} /> {t("users.add")}</button>}
      </div>

      {showForm && isSuperAdmin && (
        <div className="bg-white rounded-xl border border-slate-200 p-6">
          <div className="flex items-center justify-between mb-4"><h2 className="text-lg font-semibold">{t("users.new")}</h2><button onClick={() => setShowForm(false)} title={t("common.close")} className="text-slate-400"><X size={20} /></button></div>
          <div className="grid grid-cols-2 gap-4">
            <div><label className="block text-sm font-medium text-slate-700 mb-1">{t("users.fullName")}</label><input value={form.full_name} onChange={e => setForm({...form, full_name: e.target.value})} className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" /></div>
            <div><label className="block text-sm font-medium text-slate-700 mb-1">{t("users.email")}</label><input type="email" value={form.email} onChange={e => setForm({...form, email: e.target.value})} className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" /></div>
            <div><label className="block text-sm font-medium text-slate-700 mb-1">{t("users.password")}</label><input type="password" value={form.password} onChange={e => setForm({...form, password: e.target.value})} className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" /></div>
            <div><label className="block text-sm font-medium text-slate-700 mb-1">{t("users.role")}</label><select value={form.role} onChange={e => setForm({...form, role: e.target.value, department_ids: e.target.value === "super_admin" ? [] : form.department_ids})} className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm"><option value="user">{t("common.normalUser")}</option><option value="admin">{t("common.admin")}</option><option value="super_admin">{t("common.superAdmin")}</option></select></div>
            <div><label className="block text-sm font-medium text-slate-700 mb-1">{t("users.organization")}</label><select value={form.company_id} onChange={e => setForm({...form, company_id: e.target.value, department_ids: []})} className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm"><option value="">{t("users.noOrganization")}</option>{companies.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}</select></div>
            <div className="col-span-2">
              <label className="block text-sm font-medium text-slate-700 mb-2">{t("users.initialAccess")}</label>
              <div className="flex flex-wrap gap-2">
                {departments.map((department) => (
                  <button
                    type="button"
                    key={department.id}
                    onClick={() => setForm((current) => ({
                      ...current,
                      department_ids: current.department_ids.includes(department.id)
                        ? current.department_ids.filter((id) => id !== department.id)
                        : [...current.department_ids, department.id],
                    }))}
                    className={`px-2.5 py-1.5 rounded-lg border text-xs font-medium ${form.department_ids.includes(department.id) ? "bg-red-50 border-red-300 text-red-700" : "bg-white border-slate-200 text-slate-500"}`}
                  >
                    {department.id === generalDepartmentId ? t("users.generalDefault") : department.name}
                  </button>
                ))}
                {form.company_id && departments.length === 0 && <span className="text-xs text-slate-400">{t("users.noDepartments")}</span>}
              </div>
            </div>
          </div>
          <div className="mt-4 flex gap-2"><button onClick={handleCreate} disabled={loading} className="px-4 py-2 rounded-lg bg-red-600 hover:bg-red-700 text-white text-sm font-medium disabled:opacity-50">{loading ? t("users.creating") : t("users.create")}</button><button onClick={() => setShowForm(false)} className="px-4 py-2 rounded-lg border border-slate-300 text-sm text-slate-600 hover:bg-slate-50">{t("common.cancel")}</button></div>
        </div>
      )}

      {grantUser && (
        <div className="bg-white rounded-xl border border-slate-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-lg font-semibold">{t("users.departmentAccess")}</h2>
              <p className="text-sm text-slate-500">{grantUser.full_name}</p>
            </div>
            <button onClick={() => setGrantUser(null)} className="text-slate-400"><X size={20} /></button>
          </div>
          <div className="flex flex-wrap gap-2">
            {departments.map((department) => (
              <button
                type="button"
                key={department.id}
                onClick={() => toggleGrant(department.id)}
                className={`px-3 py-2 rounded-lg border text-sm font-medium ${grantDepartmentIds.includes(department.id) ? "bg-red-50 border-red-300 text-red-700" : "bg-white border-slate-200 text-slate-500"}`}
              >
                {department.name}
              </button>
            ))}
          </div>
          <div className="mt-4 flex gap-2">
            <button onClick={saveGrants} disabled={loading} className="px-4 py-2 rounded-lg bg-red-600 hover:bg-red-700 text-white text-sm font-medium disabled:opacity-50">{t("users.saveAccess")}</button>
            <button onClick={() => setGrantUser(null)} className="px-4 py-2 rounded-lg border border-slate-300 text-sm text-slate-600 hover:bg-slate-50">{t("common.cancel")}</button>
          </div>
        </div>
      )}

      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
        <table className="w-full">
          <thead className="bg-slate-50 border-b border-slate-200"><tr>
            <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase">{t("users.user")}</th>
            <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase">{t("users.email")}</th>
            <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase">{t("users.role")}</th>
            <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase">{t("users.organization")}</th>
            <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase">{t("users.departments")}</th>
            <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase">{t("users.status")}</th>
            <th className="px-6 py-3"></th>
          </tr></thead>
          <tbody className="divide-y divide-slate-100">
            {users.map(u => (
              <tr key={u.id} className="hover:bg-slate-50">
                <td className="px-6 py-4 text-sm font-medium text-slate-900">{u.full_name}</td>
                <td className="px-6 py-4 text-sm text-slate-600">{u.email}</td>
                <td className="px-6 py-4">{roleBadge(u.role)}</td>
                <td className="px-6 py-4 text-sm text-slate-500">{u.company_name || "—"}</td>
                <td className="px-6 py-4">
                  <div className="flex flex-wrap gap-1">
                    {(u.departments || []).map((department: any) => (
                      <span key={department.id} className="px-2 py-0.5 rounded-full bg-slate-100 text-xs text-slate-600">{department.name}</span>
                    ))}
                    {(u.departments || []).length === 0 && <span className="text-sm text-slate-400">{t("common.noAccess")}</span>}
                  </div>
                </td>
                <td className="px-6 py-4"><span className={`px-2 py-1 text-xs font-medium rounded-full ${u.is_active ? "bg-emerald-100 text-emerald-700" : "bg-slate-100 text-slate-500"}`}>{u.is_active ? t("common.active") : t("common.inactive")}</span></td>
                <td className="px-6 py-4">
                  <div className="flex items-center justify-end gap-2">
                    <button onClick={() => openGrantPanel(u)} className="text-slate-400 hover:text-red-600" title={t("users.manageAccess")}><KeyRound size={18} /></button>
                    {isSuperAdmin && <button onClick={() => toggleActive(u)} className="text-slate-400 hover:text-slate-600">{u.is_active ? <ToggleRight size={20} className="text-emerald-500" /> : <ToggleLeft size={20} />}</button>}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {users.length === 0 && <div className="text-center py-12 text-slate-400">{t("users.empty")}</div>}
      </div>
    </div>
  );
}
