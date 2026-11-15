-- Sample schema owned by the PHP/MariaDB demo.
-- Recreate in an isolated demo database only.
CREATE TABLE items (
    id INT NOT NULL PRIMARY KEY,
    code VARCHAR(12) NOT NULL,
    rating TINYINT SIGNED NOT NULL
);
-- Controlled migration for the invalidation/new-column scenario:
-- ALTER TABLE items ADD COLUMN internal_note TEXT;
