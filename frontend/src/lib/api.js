const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || "Request failed");
  }

  return response.json();
}

export function getDashboard() {
  return request("/dashboard", { method: "GET" });
}

export function onboardWorker(payload) {
  return request("/workers/onboard", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function triggerEvent(payload) {
  return request("/events/trigger", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export { API_BASE_URL };
