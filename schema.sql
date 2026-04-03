-- Workers table
CREATE TABLE IF NOT EXISTS workers (
    worker_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    city TEXT NOT NULL,
    pincode TEXT,
    platform TEXT,
    avg_daily_income FLOAT,
    experience_days INT DEFAULT 30,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Policies table
CREATE TABLE IF NOT EXISTS policies (
    policy_id TEXT PRIMARY KEY,
    worker_id TEXT REFERENCES workers(worker_id),
    weekly_premium FLOAT,
    coverage_per_week FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Claims table
CREATE TABLE IF NOT EXISTS claims (
    claim_id TEXT PRIMARY KEY,
    worker_id TEXT REFERENCES workers(worker_id),
    policy_id TEXT REFERENCES policies(policy_id),
    event_id TEXT,
    claimed_amount FLOAT,
    approved_payout FLOAT,
    status TEXT DEFAULT 'PENDING',
    fraud_score INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Disruption events table
CREATE TABLE IF NOT EXISTS disruption_events (
    event_id TEXT PRIMARY KEY,
    worker_id TEXT REFERENCES workers(worker_id),
    disruption_type TEXT,
    severity INT,
    description TEXT,
    triggered BOOLEAN DEFAULT FALSE,
    payout_amount FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);