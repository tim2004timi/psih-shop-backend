-- Migration: Add cdek_status to orders table
-- Date: 2026-02-22
-- Description: Adds cdek_status column to store CDEK order status codes

ALTER TABLE orders
ADD COLUMN IF NOT EXISTS cdek_status VARCHAR(50);
