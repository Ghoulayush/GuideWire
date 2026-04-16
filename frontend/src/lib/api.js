const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const RAZORPAY_KEY_ID = process.env.NEXT_PUBLIC_RAZORPAY_KEY_ID || "";

/**
 * Fetch dashboard metrics and data
 */
export async function getDashboard() {
  try {
    // Fetch metrics
    const metricsResponse = await fetch(`${API_BASE_URL}/analytics/metrics`);
    if (!metricsResponse.ok) {
      throw new Error(`Metrics fetch failed: ${metricsResponse.status}`);
    }
    const metrics = await metricsResponse.json();
    
    // Fetch policies
    let policies = [];
    try {
      const policiesRes = await fetch(`${API_BASE_URL}/policies`);
      if (policiesRes.ok) {
        policies = await policiesRes.json();
      }
    } catch (e) {
      console.warn("Could not fetch policies:", e);
    }
    
    // Fetch claims
    let claims = [];
    try {
      const claimsRes = await fetch(`${API_BASE_URL}/claims`);
      if (claimsRes.ok) {
        claims = await claimsRes.json();
      }
    } catch (e) {
      console.warn("Could not fetch claims:", e);
    }
    
    return { metrics, policies, claims };
  } catch (error) {
    console.error("Dashboard fetch error:", error);
    throw error;
  }
}

/**
 * Onboard a new worker and create policy
 */
export async function onboardWorker(payload) {
  try {
    const response = await fetch(`${API_BASE_URL}/workers/onboard`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.message || `Onboarding failed: ${response.status}`);
    }
    
    const data = await response.json();
    
    // Return in format expected by DashboardClient
    return {
      message: data.message,
      risk_score: data.ml_risk_score,
      risk_band: data.risk?.risk_band,
      weekly_premium: data.weekly_premium
    };
  } catch (error) {
    console.error("Onboarding error:", error);
    throw error;
  }
}

/**
 * Trigger a disruption event and process claim with fraud detection
 */
export async function triggerEvent(payload) {
  try {
    const response = await fetch(`${API_BASE_URL}/events/trigger`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.message || `Event trigger failed: ${response.status}`);
    }
    
    const data = await response.json();
    
    // Determine action based on fraud score
    let action = "APPROVE";
    if (data.fraud_score >= 70) {
      action = "REJECT";
    } else if (data.fraud_score >= 40) {
      action = "REVIEW";
    }
    
    return {
      message: data.message,
      fraud_data: {
        fraud_score: data.fraud_score,
        action: action,
        reasons: data.fraud_signals || [],
        final_decision: data.message,
        detector_results: []
      },
      has_error: false
    };
  } catch (error) {
    console.error("Trigger event error:", error);
    return {
      message: error.message,
      fraud_data: null,
      has_error: true
    };
  }
}

/**
 * Get fraud statistics
 */
export async function getFraudStats() {
  try {
    const response = await fetch(`${API_BASE_URL}/fraud/stats`);
    if (!response.ok) {
      throw new Error(`Fraud stats fetch failed: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.warn("Could not fetch fraud stats:", error);
    return {
      total_claims: 0,
      approved_claims: 0,
      rejected_claims: 0,
      fraud_rate: 0,
      total_payouts: 0,
      fraud_prevented: 0
    };
  }
}

/**
 * Get policy exclusions
 */
export async function getExclusions() {
  try {
    const response = await fetch(`${API_BASE_URL}/policy/exclusions`);
    if (!response.ok) {
      throw new Error(`Exclusions fetch failed: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.warn("Could not fetch exclusions:", error);
    return {
      exclusions: [],
      coverage_scope: "LOSS OF INCOME ONLY",
      note: "Parametric insurance - automatic payouts on triggers"
    };
  }
}

/**
 * Health check
 */
export async function healthCheck() {
  try {
    const response = await fetch(`${API_BASE_URL}/health`);
    if (!response.ok) {
      throw new Error(`Health check failed: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error("Health check error:", error);
    return { status: "unhealthy", error: error.message };
  }
}

/**
 * Test ML model endpoint
 */
export async function testMLModel() {
  try {
    const response = await fetch(`${API_BASE_URL}/test/ml`);
    if (!response.ok) {
      throw new Error(`ML test failed: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error("ML test error:", error);
    return { status: "error", message: error.message };
  }
}

/**
 * Create Razorpay order for selected subscription plan
 */
export async function createSubscriptionOrder(payload) {
  const response = await fetch(`${API_BASE_URL}/payments/razorpay/order`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  const data = await response.json();
  if (!response.ok || data.status === "error") {
    throw new Error(data.message || "Could not create subscription order");
  }
  return data;
}

/**
 * Verify Razorpay payment signature from backend
 */
export async function verifySubscriptionPayment(payload) {
  const response = await fetch(`${API_BASE_URL}/payments/razorpay/verify`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  const data = await response.json();
  if (!response.ok || data.status === "error") {
    throw new Error(data.message || "Payment verification failed");
  }
  return data;
}

/**
 * Fetch subscription status for a customer email
 */
export async function getSubscriptionStatus(email) {
  const response = await fetch(
    `${API_BASE_URL}/payments/subscriptions/${encodeURIComponent(email)}`,
  );
  if (!response.ok) {
    throw new Error(`Status fetch failed: ${response.status}`);
  }
  return await response.json();
}

export async function getAllWorkers() {
  const response = await fetch(`${API_BASE_URL}/workers`);
  if (!response.ok) {
    throw new Error(`Workers fetch failed: ${response.status}`);
  }
  return await response.json();
}

export async function getAllSubscriptions(filterStatus = "") {
  const query = filterStatus
    ? `?status=${encodeURIComponent(filterStatus)}`
    : "";
  const response = await fetch(`${API_BASE_URL}/payments/subscriptions${query}`);
  if (!response.ok) {
    throw new Error(`Subscriptions fetch failed: ${response.status}`);
  }
  return await response.json();
}

export async function loadRazorpayScript() {
  if (typeof window === "undefined") return false;
  if (window.Razorpay) return true;

  return new Promise((resolve) => {
    const script = document.createElement("script");
    script.src = "https://checkout.razorpay.com/v1/checkout.js";
    script.async = true;
    script.onload = () => resolve(true);
    script.onerror = () => resolve(false);
    document.body.appendChild(script);
  });
}

/**
 * Simulate rain event (demo control)
 */
export async function simulateRainEvent(workerId, severity = 4) {
  try {
    const response = await fetch(`${API_BASE_URL}/api/simulate/rain`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        worker_id: workerId,
        event_type: "rain",
        severity: severity
      }),
    });
    
    if (!response.ok) {
      throw new Error(`Simulation failed: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error("Simulation error:", error);
    return { error: error.message };
  }
}

export { API_BASE_URL };
export { RAZORPAY_KEY_ID };
