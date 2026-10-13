export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export type Product = {
  id: string;
  name: string;
  description: string;
  category: string;
  unit_price: number;
  currency: string;
  image_emoji: string;
};

export type OrderItem = {
  product_id: string;
  name: string;
  quantity: number;
  unit_price: string | number;
  line_total: string | number;
};

export type Order = {
  order_id: string;
  status: string;
  delivery_address: string | null;
  created_at: string | null;
  dispatch_date: string | null;
  shipping_date: string | null;
  receiving_date: string | null;
  delivered_at: string | null;
  items: OrderItem[];
  total_amount: string | number;
  currency: string;
  payment_method: string;
  refund_eligible: boolean;
  refund_reason: string | null;
  refund_deadline: string | null;
  refund_status: string | null;
  refund_request_id: string | null;
};

export type CheckoutItem = {
  product_id: string;
  quantity: number;
};

export type CheckoutPayload = {
  name: string;
  email: string;
  delivery_address: string;
  items: CheckoutItem[];
  payment_method: "cod";
};

export type CheckoutResponse = {
  customer_id: string;
  order_id: string;
  status: string;
  name: string;
  email: string;
  delivery_address: string;
  items: OrderItem[];
  total_amount: string | number;
  currency: string;
  payment_method: string;
  access_token: string;
  token_type: string;
  expires_in_minutes: number;
};

export type RefundResponse = {
  status: string;
  order_id?: string | null;
  refund_status?: string | null;
  refund_request_id?: string | null;
  reason?: string | null;
  message?: string | null;
  created_at?: string | null;
};

export type ChatResponse = {
  thread_id: string;
  response: string;
};

export type TokenResponse = {
  access_token: string;
  customer_id?: string;
  name?: string;
  email?: string;
  token_type: string;
  expires_in_minutes: number;
};

export class ApiError extends Error {
  status?: number;

  constructor(message: string, status?: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function parseResponse(response: Response) {
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    throw new ApiError(
      body?.detail || "The server could not complete that request.",
      response.status,
    );
  }
  return body;
}

export async function getProducts(): Promise<Product[]> {
  const response = await fetch(`${API_BASE_URL}/store/products`);
  return parseResponse(response);
}

export async function requestToken(customerId: string | undefined, email: string): Promise<TokenResponse> {
  const payload: Record<string, string> = { email: email.trim() };
  if (customerId && customerId.trim()) {
    payload.customer_id = customerId.trim();
  }
  const response = await fetch(`${API_BASE_URL}/auth/token`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return parseResponse(response);
}

export async function checkout(
  payload: CheckoutPayload,
  token?: string,
): Promise<CheckoutResponse> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (token) headers.Authorization = `Bearer ${token}`;

  const response = await fetch(`${API_BASE_URL}/store/checkout`, {
    method: "POST",
    headers,
    body: JSON.stringify(payload),
  });
  return parseResponse(response);
}

export async function getOrders(token: string): Promise<Order[]> {
  const response = await fetch(`${API_BASE_URL}/orders`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return parseResponse(response);
}

export async function getOrder(token: string, orderId: string): Promise<Order> {
  const response = await fetch(`${API_BASE_URL}/orders/${orderId}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return parseResponse(response);
}

export async function createRefund(
  token: string,
  orderId: string,
  reason: string,
): Promise<RefundResponse> {
  const response = await fetch(`${API_BASE_URL}/refund`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ order_id: orderId, reason }),
  });
  return parseResponse(response);
}

export async function getRefundStatus(
  token: string,
  orderId: string,
): Promise<RefundResponse> {
  const response = await fetch(`${API_BASE_URL}/refund/${orderId}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return parseResponse(response);
}

export async function sendChatMessage(
  token: string,
  threadId: string,
  message: string,
): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE_URL}/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ thread_id: threadId, message }),
  });

  if (response.status === 401) {
    throw new ApiError("SESSION_EXPIRED", 401);
  }

  return parseResponse(response);
}

export type Project = {
  id: string;
  name: string;
  slug: string;
  api_key: string;
  system_prompt: string | null;
  llm_model: string | null;
  widget_title: string;
  widget_greeting: string;
  primary_color: string;
  created_at: string;
};

export type DocumentItem = {
  doc_id: string;
  file_name: string;
  file_type: string;
  total_chunks: number;
  total_pages: number;
  upload_timestamp: string;
  status: string;
};

export type ProjectTool = {
  id: string;
  project_id: string;
  name: string;
  description: string;
  method: string;
  endpoint_url: string;
  headers: Record<string, string>;
  parameters_schema: Record<string, any>;
  created_at: string;
};

export async function listProjects(): Promise<Project[]> {
  const response = await fetch(`${API_BASE_URL}/projects`);
  return parseResponse(response);
}

export async function createProject(payload: Partial<Project>): Promise<Project> {
  const response = await fetch(`${API_BASE_URL}/projects`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return parseResponse(response);
}

export async function updateProject(projectId: string, payload: Partial<Project>): Promise<Project> {
  const response = await fetch(`${API_BASE_URL}/projects/${projectId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return parseResponse(response);
}

export async function listProjectDocs(projectId: string): Promise<DocumentItem[]> {
  const response = await fetch(`${API_BASE_URL}/projects/${projectId}/documents`);
  const data = await parseResponse(response);
  return data.documents || [];
}

export async function uploadProjectDocs(projectId: string, files: FileList | File[]): Promise<any> {
  const formData = new FormData();
  for (let i = 0; i < files.length; i++) {
    formData.append("files", files[i]);
  }
  const response = await fetch(`${API_BASE_URL}/projects/${projectId}/documents/upload`, {
    method: "POST",
    body: formData,
  });
  return parseResponse(response);
}

export async function deleteProjectDoc(projectId: string, docId: string): Promise<any> {
  const response = await fetch(`${API_BASE_URL}/projects/${projectId}/documents/${docId}`, {
    method: "DELETE",
  });
  return parseResponse(response);
}

export async function listProjectTools(projectId: string): Promise<ProjectTool[]> {
  const response = await fetch(`${API_BASE_URL}/projects/${projectId}/tools`);
  return parseResponse(response);
}

export async function createProjectTool(
  projectId: string,
  tool: { name: string; description: string; method: string; endpoint_url: string }
): Promise<ProjectTool> {
  const response = await fetch(`${API_BASE_URL}/projects/${projectId}/tools`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(tool),
  });
  return parseResponse(response);
}

export async function deleteProjectTool(projectId: string, toolId: string): Promise<any> {
  const response = await fetch(`${API_BASE_URL}/projects/${projectId}/tools/${toolId}`, {
    method: "DELETE",
  });
  return parseResponse(response);
}

