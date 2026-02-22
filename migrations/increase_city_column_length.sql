-- Increase city column length from 50 to 255 characters
ALTER TABLE orders ALTER COLUMN city TYPE VARCHAR(255);
ALTER TABLE users ALTER COLUMN city TYPE VARCHAR(255);
