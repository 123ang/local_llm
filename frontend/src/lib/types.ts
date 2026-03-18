export interface Company {
  id: number;
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
  is_active: boolean;
  created_at: string;
}

export interface Document {
  id: number;
  company_id: number;
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
  user_id: number | null;
  action: string;
  resource_type: string | null;
  resource_id: number | null;
  details: any | null;
  ip_address: string | null;
  created_at: string;
}
