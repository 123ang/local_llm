"use client";
import { useState, useEffect } from "react";
import { Plus, Pencil, Trash2, Eye, EyeOff, HelpCircle, X } from "lucide-react";
import { api } from "@/lib/api";
import { useCompanyId } from "@/hooks/useCompanyId";
import { useI18n } from "@/lib/i18n-context";

export default function FAQPage() {
  const { t } = useI18n();
  const companyId = useCompanyId();
  const [items, setItems] = useState<any[]>([]);
  const [departments, setDepartments] = useState<any[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState<any>(null);
  const [form, setForm] = useState({
    question: "",
    answer: "",
    category: "",
    is_published: true,
    department_id: "",
  });

  useEffect(() => {
    if (companyId) loadFAQ();
  }, [companyId]);

  useEffect(() => {
    if (!companyId) return;
    api.getDepartments(companyId).then((items) => {
      setDepartments(items);
      setForm((current) => ({ ...current, department_id: current.department_id || String(items[0]?.id || "") }));
    }).catch(() => setDepartments([]));
  }, [companyId]);

  const loadFAQ = async () => {
    if (!companyId) return;
    try {
      setItems(await api.getFAQ(companyId));
    } catch {}
  };

  const handleSave = async () => {
    if (!companyId || !form.question || !form.answer || !form.department_id) return;
    const payload = { ...form, department_id: Number(form.department_id) };
    try {
      if (editing) {
        await api.updateFAQ(companyId, editing.id, payload);
      } else {
        await api.createFAQ(companyId, payload);
      }
      await loadFAQ();
      resetForm();
    } catch {}
  };

  const handleDelete = async (id: number) => {
    if (!companyId || !confirm(t("faq.confirmDelete"))) return;
    try {
      await api.deleteFAQ(companyId, id);
      await loadFAQ();
    } catch {}
  };

  const togglePublish = async (item: any) => {
    if (!companyId) return;
    try {
      await api.updateFAQ(companyId, item.id, {
        is_published: !item.is_published,
      });
      await loadFAQ();
    } catch {}
  };

  const startEdit = (item: any) => {
    setEditing(item);
    setForm({
      question: item.question,
      answer: item.answer,
      category: item.category || "",
      is_published: item.is_published,
      department_id: String(item.department_id || departments[0]?.id || ""),
    });
    setShowForm(true);
  };

  const resetForm = () => {
    setShowForm(false);
    setEditing(null);
    setForm({ question: "", answer: "", category: "", is_published: true, department_id: String(departments[0]?.id || "") });
  };

  if (!companyId)
    return (
      <div className="text-slate-400 text-center py-12">
        {t("faq.selectOrganization")}
      </div>
    );

  if (departments.length === 0)
    return (
      <div className="text-slate-400 text-center py-12">{t("faq.noDepartment")}</div>
    );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">{t("faq.title")}</h1>
          <p className="text-slate-500 mt-1">
            {t("faq.copy")}
          </p>
        </div>
        <button
          onClick={() => {
            resetForm();
            setShowForm(true);
          }}
          className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-red-600 hover:bg-red-700 text-white text-sm font-medium transition-colors"
        >
          <Plus size={16} /> {t("faq.addFaq")}
        </button>
      </div>

      {showForm && (
        <div className="bg-white rounded-xl border border-slate-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">
              {editing ? t("faq.editFaq") : t("faq.newFaq")}
            </h2>
            <button
              onClick={resetForm}
              className="text-slate-400 hover:text-slate-600"
            >
              <X size={20} />
            </button>
          </div>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                {t("faq.question")}
              </label>
              <input
                value={form.question}
                onChange={(e) =>
                  setForm({ ...form, question: e.target.value })
                }
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-red-500 focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                {t("faq.answer")}
              </label>
              <textarea
                value={form.answer}
                onChange={(e) => setForm({ ...form, answer: e.target.value })}
                rows={4}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-red-500 focus:border-transparent"
              />
            </div>
            <div className="flex gap-4">
              <div className="flex-1">
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  {t("faq.department")}
                </label>
                <select
                  value={form.department_id}
                  onChange={(e) => setForm({ ...form, department_id: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm"
                >
                  {departments.map((department) => (
                    <option key={department.id} value={department.id}>{department.name}</option>
                  ))}
                </select>
              </div>
              <div className="flex-1">
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  {t("faq.category")}
                </label>
                <input
                  value={form.category}
                  onChange={(e) =>
                    setForm({ ...form, category: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm"
                  placeholder={t("faq.categoryPlaceholder")}
                />
              </div>
              <div className="flex items-end">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={form.is_published}
                    onChange={(e) =>
                      setForm({ ...form, is_published: e.target.checked })
                    }
                    className="rounded"
                  />
                  <span className="text-sm text-slate-600">{t("faq.published")}</span>
                </label>
              </div>
            </div>
            <div className="flex gap-2">
              <button
                onClick={handleSave}
                className="px-4 py-2 rounded-lg bg-red-600 hover:bg-red-700 text-white text-sm font-medium"
              >
                {t("common.save")}
              </button>
              <button
                onClick={resetForm}
                className="px-4 py-2 rounded-lg border border-slate-300 text-slate-600 text-sm hover:bg-slate-50"
              >
                {t("common.cancel")}
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="space-y-3">
        {items.map((item) => (
          <div
            key={item.id}
            className="bg-white rounded-xl border border-slate-200 p-5"
          >
            <div className="flex items-start justify-between">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-2">
                  <HelpCircle
                    size={16}
                    className="text-amber-500 flex-shrink-0"
                  />
                  <h3 className="text-sm font-semibold text-slate-900">
                    {item.question}
                  </h3>
                  {item.category && (
                    <span className="px-2 py-0.5 text-xs rounded-full bg-slate-100 text-slate-600">
                      {item.category}
                    </span>
                  )}
                  <span className="px-2 py-0.5 text-xs rounded-full bg-blue-50 text-blue-700">
                    {departments.find((department) => department.id === item.department_id)?.name || t("faq.department")}
                  </span>
                  {!item.is_published && (
                    <span className="px-2 py-0.5 text-xs rounded-full bg-amber-100 text-amber-700">
                      {t("faq.draft")}
                    </span>
                  )}
                </div>
                <p className="text-sm text-slate-600 ml-6">{item.answer}</p>
              </div>
              <div className="flex items-center gap-1 ml-4">
                <button
                  onClick={() => togglePublish(item)}
                  title={t("faq.togglePublish")}
                  className="p-1.5 rounded-lg hover:bg-slate-100 text-slate-400 hover:text-slate-600"
                >
                  {item.is_published ? (
                    <Eye size={16} />
                  ) : (
                    <EyeOff size={16} />
                  )}
                </button>
                <button
                  onClick={() => startEdit(item)}
                  title={t("faq.edit")}
                  className="p-1.5 rounded-lg hover:bg-slate-100 text-slate-400 hover:text-blue-500"
                >
                  <Pencil size={16} />
                </button>
                <button
                  onClick={() => handleDelete(item.id)}
                  title={t("faq.delete")}
                  className="p-1.5 rounded-lg hover:bg-red-50 text-slate-400 hover:text-red-500"
                >
                  <Trash2 size={16} />
                </button>
              </div>
            </div>
          </div>
        ))}
        {items.length === 0 && (
          <div className="bg-white rounded-xl border border-slate-200 p-12 text-center text-slate-400">
            {t("faq.empty")}
          </div>
        )}
      </div>
    </div>
  );
}
