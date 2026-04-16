const STORAGE_KEY = "gigshield-admin";
const ADMIN_EMAIL = "admin@gigshield.local";
const ADMIN_PASSWORD = "admin123";

export function loginAdmin(email, password) {
  const normalized = (email || "").trim().toLowerCase();
  if (normalized !== ADMIN_EMAIL || password !== ADMIN_PASSWORD) {
    return { ok: false, message: "Invalid admin credentials" };
  }

  if (typeof window !== "undefined") {
    window.localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({ email: ADMIN_EMAIL, loggedAt: new Date().toISOString() }),
    );
  }

  return { ok: true };
}

export function getAdminSession() {
  if (typeof window === "undefined") return null;
  const raw = window.localStorage.getItem(STORAGE_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export function logoutAdmin() {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(STORAGE_KEY);
}
