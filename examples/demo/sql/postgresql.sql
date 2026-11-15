-- Sample schema owned by the PostgreSQL demo (Java and .NET).
-- Recreate in an isolated demo database only.
CREATE TABLE items (
    id INTEGER PRIMARY KEY,
    code VARCHAR(12) NOT NULL,
    rating SMALLINT NOT NULL
);
-- Controlled migration for the invalidation/new-column scenario:
-- ALTER TABLE items ADD COLUMN internal_note TEXT;
