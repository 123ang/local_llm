"use client";
import { useState, useEffect } from "react";
import { Plus, Pencil, Trash2, Eye, EyeOff, HelpCircle, X } from "lucide-react";
import { api } from "@/lib/api";
import { useCompanyId } from "@/hooks/useCompanyId";

export default function FAQPage() {
  const companyId = useCompanyId();
  const [items, setItems] = useState<any[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState<any>(null);
  const [form, setForm] = useState({
    question: "",
    answer: "",
    category: "",
    is_published: true,
  });

  useEffect(() => {
    if (companyId) loadFAQ();
  }, [companyId]);

  const loadFAQ = async () => {
    if (!companyId) return;
    try {
      setItems(await api.getFAQ(companyId));
    } catch {}
  };

  const handleSave = async () => {
    if (!companyId || !form.question || !form.answer) return;
    try {
      if (editing) {
        await api.updateFAQ(companyId, editing.id, form);
      } else {
        await api.createFAQ(companyId, form);
      }
      await loadFAQ();
      resetForm();
    } catch {}
  };

  const handleDelete = async (id: number) => {
    if (!companyId || !confirm("Delete this FAQ?")) return;
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
    });
    setShowForm(true);
  };

  const resetForm = () => {
    setShowForm(false);
    setEditing(null);
    setForm({ question: "", answer: "", category: "", is_published: true });
  };

  if (!companyId)
    return (
      <div className="text-slate-400 text-center py-12">
        Select a company to manage FAQ
      </div>
    );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">FAQ</h1>
          <p className="text-slate-500 mt-1">
            Manage frequently asked questions
          </p>
        </div>
        <button
          onClick={() => {
            resetForm();
            setShowForm(true);
          }}
          className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-red-600 hover:bg-red-700 text-white text-sm font-medium transition-colors"
        >
          <Plus size={16} /> Add FAQ
        </button>
      </div>

      {showForm && (
        <div className="bg-white rounded-xl border border-slate-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">
              {editing ? "Edit FAQ" : "New FAQ"}
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
                Question
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
                Answer
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
                  Category
                </label>
                <input
                  value={form.category}
                  onChange={(e) =>
                    setForm({ ...form, category: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm"
                  placeholder="e.g. Policy, General"
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
                  <span className="text-sm text-slate-600">Published</span>
                </label>
              </div>
            </div>
            <div className="flex gap-2">
              <button
                onClick={handleSave}
                className="px-4 py-2 rounded-lg bg-red-600 hover:bg-red-700 text-white text-sm font-medium"
              >
                Save
              </button>
              <button
                onClick={resetForm}
                className="px-4 py-2 rounded-lg border border-slate-300 text-slate-600 text-sm hover:bg-slate-50"
              >
                Cancel
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
                  {!item.is_published && (
                    <span className="px-2 py-0.5 text-xs rounded-full bg-amber-100 text-amber-700">
                      Draft
                    </span>
                  )}
                </div>
                <p className="text-sm text-slate-600 ml-6">{item.answer}</p>
              </div>
              <div className="flex items-center gap-1 ml-4">
                <button
                  onClick={() => togglePublish(item)}
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
                  className="p-1.5 rounded-lg hover:bg-slate-100 text-slate-400 hover:text-blue-500"
                >
                  <Pencil size={16} />
                </button>
                <button
                  onClick={() => handleDelete(item.id)}
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
            No FAQ items yet. Click &quot;Add FAQ&quot; to create one.
          </div>
        )}
      </div>
    </div>
  );
}
