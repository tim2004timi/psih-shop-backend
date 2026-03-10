-- Migration: Add custom_statuses table and custom_status_id to orders
-- Date: 2026-03-11
-- Description: Adds custom statuses and links orders to them (nullable)

CREATE TABLE IF NOT EXISTS custom_statuses (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE
);

ALTER TABLE orders
ADD COLUMN IF NOT EXISTS custom_status_id INTEGER;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_orders_custom_status'
          AND table_name = 'orders'
    ) THEN
        ALTER TABLE orders
        ADD CONSTRAINT fk_orders_custom_status
        FOREIGN KEY (custom_status_id) REFERENCES custom_statuses (id)
        ON DELETE SET NULL;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS ix_orders_custom_status_id ON orders (custom_status_id);
