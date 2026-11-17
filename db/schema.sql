CREATE TABLE payments (
  payment_id TEXT PRIMARY KEY,
  amount_minor INTEGER NOT NULL CHECK (amount_minor > 0),
  currency CHAR(3) NOT NULL,
  status TEXT NOT NULL,
  provider_reference TEXT,
  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP NOT NULL
);

CREATE INDEX idx_payments_status ON payments(status);
CREATE INDEX idx_payments_provider_reference ON payments(provider_reference);

CREATE TABLE payment_status_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  payment_id TEXT NOT NULL,
  previous_status TEXT,
  next_status TEXT NOT NULL,
  changed_at TIMESTAMP NOT NULL,
  FOREIGN KEY(payment_id) REFERENCES payments(payment_id)
);

CREATE INDEX idx_payment_status_events_payment_id
  ON payment_status_events(payment_id);
