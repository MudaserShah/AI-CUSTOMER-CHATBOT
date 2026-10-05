// Single place that knows where the backend lives. Locally this
// defaults to the FastAPI dev server; in production (Docker, cloud)
// set VITE_API_BASE_URL at build time instead of editing this file.
export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export type TokenResponse = {
  access_token: string;
  token_type: string;
  expires_in_minutes: number;
};

export class ApiError extends Error {}

export async function requestToken(
  customerId: string,
  email: string,
): Promise<TokenResponse> {
  const response = await fetch(`${API_BASE_URL}/auth/token`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ customer_id: customerId, email }),
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new ApiError(
      body?.detail || "Could not verify those details. Please check and try again.",
    );
  }

  return response.json();
}

export async function sendChatMessage(
  token: string,
  threadId: string,
  message: string,
): Promise<{ thread_id: string; response: string }> {
  const response = await fetch(`${API_BASE_URL}/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ thread_id: threadId, message }),
  });

  if (response.status === 401) {
    throw new ApiError("SESSION_EXPIRED");
  }

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new ApiError(body?.detail || "The assistant could not respond. Please try again.");
  }

  return response.json();
}
