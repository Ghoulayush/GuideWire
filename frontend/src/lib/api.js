const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

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
    
    // Fetch policies (try multiple possible endpoints)
    let policies = [];
    try {
      const policiesRes = await fetch(`${API_BASE_URL}/policies`);
      if (policiesRes.ok) {
        policies = await policiesRes.json();
      } else {
        // Try alternative endpoint
        const altPoliciesRes = await fetch(`${API_BASE_URL}/api/policies`);
        if (altPoliciesRes.ok) {
          policies = await altPoliciesRes.json();
        }
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
      } else {
        // Try alternative endpoint
        const altClaimsRes = await fetch(`${API_BASE_URL}/api/claims`);
        if (altClaimsRes.ok) {
          claims = await altClaimsRes.json();
        }
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
  const formData = new URLSearchParams();
  Object.entries(payload).forEach(([key, value]) => {
    formData.append(key, value);
  });
  
  const response = await fetch(`${API_BASE_URL}/onboard`, {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body: formData,
  });
  
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || "Onboarding failed");
  }
  
  const html = await response.text();
  
  // Parse message from HTML response
  let message = "Worker onboarded successfully";
  const messageMatch = html.match(/<p class="notice">(.*?)<\/p>/s);
  if (messageMatch) {
    message = messageMatch[1].replace(/<[^>]*>/g, '').trim();
  }
  
  // Parse risk score and premium if available
  let riskScore = null;
  let premium = null;
  let riskBand = null;
  
  const riskMatch = html.match(/Risk: (\w+)\s*\((\d+)\/100\)/i);
  if (riskMatch) {
    riskBand = riskMatch[1];
    riskScore = parseInt(riskMatch[2]);
  }
  
  const premiumMatch = html.match(/Premium: ₹(\d+)\/week/i);
  if (premiumMatch) {
    premium = parseInt(premiumMatch[1]);
  }
  
  return { 
    message, 
    risk_score: riskScore,
    risk_band: riskBand,
    weekly_premium: premium
  };
}

/**
 * Trigger a disruption event and process claim with fraud detection
 */
export async function triggerEvent(payload) {
  const formData = new URLSearchParams();
  Object.entries(payload).forEach(([key, value]) => {
    formData.append(key, value);
  });
  
  const response = await fetch(`${API_BASE_URL}/trigger`, {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body: formData,
  });
  
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || "Event trigger failed");
  }
  
  const html = await response.text();
  
  // Parse message from HTML response
  let message = "Claim processed";
  const messageMatch = html.match(/<p class="notice">(.*?)<\/p>/s);
  if (messageMatch) {
    message = messageMatch[1].replace(/<[^>]*>/g, '').trim();
  }
  
  // Parse error if any
  let error = null;
  const errorMatch = html.match(/<p class="error">(.*?)<\/p>/s);
  if (errorMatch) {
    error = errorMatch[1].replace(/<[^>]*>/g, '').trim();
  }
  
  // 🚀 PARSE FRAUD DETECTION DATA from HTML response
  let fraudData = null;
  
  // Method 1: Look for data-fraud attribute
  const dataFraudMatch = html.match(/data-fraud='([^']+)'/);
  if (dataFraudMatch) {
    try {
      fraudData = JSON.parse(dataFraudMatch[1]);
    } catch (e) {
      console.warn("Failed to parse data-fraud attribute:", e);
    }
  }
  
  // Method 2: Look for fraud result div with class
  if (!fraudData) {
    const fraudDivMatch = html.match(/<div class="fraud-result"[^>]*>([\s\S]*?)<\/div>/i);
    if (fraudDivMatch) {
      const fraudHtml = fraudDivMatch[1];
      
      // Extract fraud score
      const scoreMatch = fraudHtml.match(/fraud-score["']?\s*:\s*(\d+)/i);
      const actionMatch = fraudHtml.match(/action["']?\s*:\s*['"](\w+)['"]/i);
      const reasonMatch = fraudHtml.match(/reason["']?\s*:\s*['"]([^'"]+)['"]/i);
      
      if (scoreMatch || actionMatch) {
        fraudData = {
          fraud_score: scoreMatch ? parseInt(scoreMatch[1]) : 0,
          action: actionMatch ? actionMatch[1] : "APPROVE",
          reason: reasonMatch ? reasonMatch[1] : "No fraud detected",
          detector_results: []
        };
      }
    }
  }
  
  // Method 3: Look for fraud score in the message
  if (!fraudData && message.includes("Fraud")) {
    const scoreMatch = message.match(/score[:\s]*(\d+)/i);
    fraudData = {
      fraud_score: scoreMatch ? parseInt(scoreMatch[1]) : 50,
      action: message.includes("REJECT") ? "REJECT" : (message.includes("REVIEW") ? "REVIEW" : "APPROVE"),
      reason: message,
      detector_results: []
    };
  }
  
  return {
    message: error || message,
    fraud_data: fraudData,
    has_error: !!error
  };
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

export { API_BASE_URL };