export interface Company {
  id: number;
  name: string;
  slug: string;
  description: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Department {
  id: number;
  company_id: number;
  name: string;
  slug: string;
  description: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: string;
  company_id: number | null;
  company_name: string | null;
  department_ids: number[];
  departments: { id: number; company_id: number; name: string; slug: string }[];
  is_active: boolean;
  created_at: string;
}

export interface Document {
  id: number;
  company_id: number;
  department_id: number | null;
  visibility: string;
  filename: string;
  original_name: string;
  file_size: number | null;
  status: string;
  page_count: number | null;
  chunk_count: number;
  created_at: string;
}

export interface FAQItem {
  id: number;
  company_id: number;
  department_id: number | null;
  visibility: string;
  question: string;
  answer: string;
  category: string | null;
  is_published: boolean;
  sort_order: number;
  created_at: string;
  updated_at: string;
}

export interface Dataset {
  id: number;
  company_id: number;
  department_id: number | null;
  visibility: string;
  table_name: string;
  display_name: string;
  description: string | null;
  columns_schema: { name: string; type: string; nullable: boolean }[] | null;
  row_count: number;
  source: string;
  status: string;
  is_queryable: boolean;
  created_at: string;
  updated_at: string;
}

export interface APIConnector {
  id: number;
  company_id: number;
  department_id: number;
  visibility: string;
  name: string;
  description: string | null;
  method: string;
  url: string;
  headers: Record<string, string>;
  body: string | null;
  curl_command: string | null;
  status: string;
  last_status_code: number | null;
  last_response_text: string | null;
  last_error: string | null;
  last_synced_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface ChatSession {
  id: number;
  title: string | null;
  created_at: string;
  message_count: number;
}

export interface ChatMessage {
  id: number;
  role: string;
  content: string;
  sources: any | null;
  sql_generated: string | null;
  created_at: string;
}

export interface AuditLog {
  id: number;
  company_id: number | null;
  company_name: string | null;
  organization_name: string | null;
  user_id: number | null;
  user_name: string | null;
  user_email: string | null;
  actor_label: string | null;
  action: string;
  resource_type: string | null;
  resource_id: number | null;
  resource_kind_label: string | null;
  resource_label: string | null;
  details: any | null;
  ip_address: string | null;
  created_at: string;
}
