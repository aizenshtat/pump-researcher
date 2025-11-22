-- Pump Research Database Schema

-- Track detected pumps
CREATE TABLE IF NOT EXISTS pumps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    detected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    price_change_pct REAL NOT NULL,
    time_window_minutes INTEGER NOT NULL,
    price_at_detection REAL,
    volume_change_pct REAL,
    market_cap REAL,
    source TEXT NOT NULL, -- 'binance', 'coinmarketcap', 'both'
    UNIQUE(symbol, detected_at)
);

-- Track investigation findings
CREATE TABLE IF NOT EXISTS findings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pump_id INTEGER NOT NULL,
    source_type TEXT NOT NULL, -- 'reddit', 'twitter', 'discord', 'telegram', 'web', 'grok'
    source_url TEXT,
    content TEXT NOT NULL,
    relevance_score REAL, -- 0.0 to 1.0
    sentiment TEXT, -- 'positive', 'negative', 'neutral'
    found_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT, -- JSON for additional data
    FOREIGN KEY (pump_id) REFERENCES pumps(id)
);

-- Track news triggers identified
CREATE TABLE IF NOT EXISTS news_triggers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pump_id INTEGER NOT NULL,
    trigger_type TEXT NOT NULL, -- 'announcement', 'partnership', 'listing', 'social_hype', 'whale_activity', 'unknown'
    description TEXT NOT NULL,
    confidence REAL NOT NULL, -- 0.0 to 1.0
    supporting_findings TEXT, -- JSON array of finding IDs
    identified_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (pump_id) REFERENCES pumps(id)
);

-- Track Telegram notifications sent
CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pump_id INTEGER NOT NULL,
    message_id TEXT,
    chat_id TEXT NOT NULL,
    sent_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'sent', -- 'sent', 'failed', 'pending'
    FOREIGN KEY (pump_id) REFERENCES pumps(id)
);

-- Track agent runs for monitoring
CREATE TABLE IF NOT EXISTS agent_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME,
    pumps_detected INTEGER DEFAULT 0,
    findings_count INTEGER DEFAULT 0,
    status TEXT DEFAULT 'running', -- 'running', 'completed', 'failed'
    error_message TEXT
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_pumps_symbol ON pumps(symbol);
CREATE INDEX IF NOT EXISTS idx_pumps_detected_at ON pumps(detected_at);
CREATE INDEX IF NOT EXISTS idx_findings_pump_id ON findings(pump_id);
CREATE INDEX IF NOT EXISTS idx_findings_source_type ON findings(source_type);
CREATE INDEX IF NOT EXISTS idx_news_triggers_pump_id ON news_triggers(pump_id);
