-- Wallet registry table definition
CREATE TABLE wallets (
  id serial PRIMARY KEY,
  address text UNIQUE,
  chain text,
  label text,
  source_hint text,
  signature text,
  verified boolean DEFAULT true,
  balance_bigint numeric,
  balance_usd numeric,
  last_checked timestamptz,
  metadata jsonb
);
