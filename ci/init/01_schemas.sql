-- 1. Schemas
-- --------------------------------------------------------
DROP SCHEMA IF EXISTS core CASCADE;
DROP SCHEMA IF EXISTS ref CASCADE;
DROP SCHEMA IF EXISTS workflow CASCADE;
DROP SCHEMA IF EXISTS audit CASCADE;

CREATE SCHEMA core AUTHORIZATION db_owner;
CREATE SCHEMA ref AUTHORIZATION db_owner;
CREATE SCHEMA workflow AUTHORIZATION db_owner;
CREATE SCHEMA audit AUTHORIZATION db_owner;

-- --------------------------------------------------------
