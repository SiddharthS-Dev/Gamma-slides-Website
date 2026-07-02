-- SlideVault database setup script
-- Run as postgres superuser

-- Create user if not exists
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'slidevault') THEN
    CREATE USER slidevault WITH PASSWORD 'slidevault';
  END IF;
END
$$;

-- Create database if not exists
SELECT 'CREATE DATABASE slidevault OWNER slidevault'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'slidevault')\gexec

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE slidevault TO slidevault;

-- Connect to the database and install extensions
\c slidevault

CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

GRANT ALL ON SCHEMA public TO slidevault;

\echo 'Setup complete!'
