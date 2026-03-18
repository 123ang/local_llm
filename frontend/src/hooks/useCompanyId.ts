"use client";
import { useEffect, useSyncExternalStore } from "react";
import { useAuth } from "@/lib/auth-context";

const STORAGE_KEY = "askai_selected_company_id";

let listeners: Array<() => void> = [];

function getSnapshot(): number | null {
  if (typeof window === "undefined") return null;
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored && stored !== "null") return parseInt(stored, 10);
  return null;
}

function subscribe(callback: () => void) {
  listeners.push(callback);
  const onStorage = (e: StorageEvent) => {
    if (e.key === STORAGE_KEY) callback();
  };
  window.addEventListener("storage", onStorage);
  return () => {
    listeners = listeners.filter((l) => l !== callback);
    window.removeEventListener("storage", onStorage);
  };
}

export function setSelectedCompanyId(id: number | null) {
  if (id === null) {
    localStorage.removeItem(STORAGE_KEY);
  } else {
    localStorage.setItem(STORAGE_KEY, String(id));
  }
  listeners.forEach((l) => l());
}

export function useCompanyId(): number | null {
  const { user } = useAuth();

  const companyId = useSyncExternalStore(subscribe, getSnapshot, () => null);

  // If nothing is stored yet and user has a company, set it
  useEffect(() => {
    if (companyId === null && user?.company_id) {
      setSelectedCompanyId(user.company_id);
    }
  }, [user, companyId]);

  return companyId ?? user?.company_id ?? null;
}
