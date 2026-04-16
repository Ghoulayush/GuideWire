import { createClient } from "@supabase/supabase-js";

const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL;
const SUPABASE_ANON_KEY = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

export const isSupabaseConfigured =
  Boolean(SUPABASE_URL) && Boolean(SUPABASE_ANON_KEY);

let supabase = null;

if (isSupabaseConfigured) {
  supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
}

export { supabase };

function notConfiguredResult() {
  return {
    ok: false,
    skipped: true,
    reason: "supabase_not_configured",
  };
}

export async function signUpWithEmail(email, password, name) {
  if (!isSupabaseConfigured || !supabase) {
    return notConfiguredResult();
  }

  const { data, error } = await supabase.auth.signUp({
    email,
    password,
    options: {
      data: {
        name: name || "Gig Worker",
      },
    },
  });

  if (error) {
    return { ok: false, skipped: false, reason: error.message };
  }

  return { ok: true, data };
}

export async function signInWithEmail(email, password) {
  if (!isSupabaseConfigured || !supabase) {
    return notConfiguredResult();
  }

  const { data, error } = await supabase.auth.signInWithPassword({
    email,
    password,
  });

  if (error) {
    return { ok: false, skipped: false, reason: error.message };
  }

  return { ok: true, data };
}

export async function signOutUser() {
  if (!isSupabaseConfigured || !supabase) {
    return notConfiguredResult();
  }

  const { error } = await supabase.auth.signOut();
  if (error) {
    return { ok: false, skipped: false, reason: error.message };
  }

  return { ok: true };
}

export async function getCurrentSession() {
  if (!isSupabaseConfigured || !supabase) {
    return null;
  }

  const { data } = await supabase.auth.getSession();
  return data?.session || null;
}

export async function getCurrentUser() {
  const session = await getCurrentSession();
  return session?.user || null;
}

export function onAuthStateChange(callback) {
  if (!isSupabaseConfigured || !supabase) {
    return { data: { subscription: { unsubscribe() {} } } };
  }

  return supabase.auth.onAuthStateChange(callback);
}

export async function saveUserProfile(user) {
  if (!isSupabaseConfigured || !supabase || !user?.email || !user?.id) {
    return notConfiguredResult();
  }

  const payload = {
    user_id: user.id,
    email: user.email,
    worker_id: user.worker_id || null,
    name: user.name || "Gig Worker",
    auth_mode: user.mode || "login",
    updated_at: new Date().toISOString(),
  };

  const { error } = await supabase
    .from("user_profiles")
    .upsert(payload, { onConflict: "user_id" });

  if (error) {
    return { ok: false, skipped: false, reason: error.message };
  }

  return { ok: true };
}

export async function getCurrentUserWorkerId() {
  if (!isSupabaseConfigured || !supabase) {
    return null;
  }

  const user = await getCurrentUser();
  if (!user?.id) {
    return null;
  }

  const { data, error } = await supabase
    .from("user_profiles")
    .select("worker_id")
    .eq("user_id", user.id)
    .single();

  if (error) {
    return null;
  }

  return data?.worker_id || null;
}

export async function setCurrentUserWorkerId(workerId) {
  if (!isSupabaseConfigured || !supabase) {
    return notConfiguredResult();
  }

  const user = await getCurrentUser();
  if (!user?.id || !user?.email) {
    return { ok: false, skipped: false, reason: "no_authenticated_user" };
  }

  const payload = {
    user_id: user.id,
    email: user.email,
    worker_id: workerId,
    name: user.user_metadata?.name || "Gig Worker",
    auth_mode: "login",
    updated_at: new Date().toISOString(),
  };

  const { error } = await supabase
    .from("user_profiles")
    .upsert(payload, { onConflict: "user_id" });

  if (error) {
    return { ok: false, skipped: false, reason: error.message };
  }

  return { ok: true };
}

export async function saveDeliveryIssue(issue) {
  if (!isSupabaseConfigured || !supabase || !issue?.user_id) {
    return notConfiguredResult();
  }

  const payload = {
    user_id: issue.user_id,
    worker_id: issue.worker_id,
    disruption_type: issue.disruption_type,
    severity: issue.severity,
    description: issue.description,
    reporter_email: issue.reporter_email || null,
    backend_message: issue.backend_message || null,
    triggered: Boolean(issue.triggered),
    payout_amount: Number(issue.payout_amount || 0),
    latitude:
      issue.latitude !== undefined && issue.latitude !== null
        ? Number(issue.latitude)
        : null,
    longitude:
      issue.longitude !== undefined && issue.longitude !== null
        ? Number(issue.longitude)
        : null,
    location_source: issue.location_source || null,
    location_accuracy:
      issue.location_accuracy !== undefined && issue.location_accuracy !== null
        ? Number(issue.location_accuracy)
        : null,
    created_at: new Date().toISOString(),
  };

  const { error } = await supabase.from("delivery_issues").insert(payload);
  if (error) {
    return { ok: false, skipped: false, reason: error.message };
  }

  return { ok: true };
}
