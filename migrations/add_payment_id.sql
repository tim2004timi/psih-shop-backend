-- Migration: Add payment_id to orders table
-- Date: 2026-02-03
-- Description: Adds payment_id column to store TBank payment IDs

ALTER TABLE orders 
ADD COLUMN IF NOT EXISTS payment_id VARCHAR(50);

CREATE INDEX IF NOT EXISTS idx_orders_payment_id ON orders(payment_id);

