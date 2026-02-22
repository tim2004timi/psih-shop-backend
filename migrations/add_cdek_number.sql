-- Add cdek_number column to orders table for storing CDEK tracking number
ALTER TABLE orders ADD COLUMN IF NOT EXISTS cdek_number VARCHAR(50) DEFAULT NULL;
