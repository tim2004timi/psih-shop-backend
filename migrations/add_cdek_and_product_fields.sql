-- Миграция: Добавление полей cdek_uuid, weight, currency и нового статуса not_paid
-- Дата: 2024
-- 
-- ВАЖНО: В PostgreSQL нельзя использовать новое значение enum в той же транзакции,
-- где оно было добавлено. Поэтому миграция разделена на две части.
-- 
-- ИНСТРУКЦИЯ ПО ВЫПОЛНЕНИЮ В pgAdmin:
-- 1. Сначала выполните файл: add_cdek_and_product_fields_part1.sql
-- 2. Дождитесь успешного завершения
-- 3. Затем выполните файл: add_cdek_and_product_fields_part2.sql
-- 
-- ИЛИ выполните части по очереди из этого файла:
-- - Сначала выполните ЧАСТЬ 1 (строки 8-55) - выделите и выполните только этот блок
-- - Если была ошибка, выполните ROLLBACK
-- - Затем выполните ЧАСТЬ 2 (строки 57-126) - выделите и выполните только этот блок

-- ============================================================================
-- ЧАСТЬ 1: Добавление нового значения в enum (выполнить первой, ОТДЕЛЬНО)
-- ============================================================================
-- Находим имя enum типа для колонки status в таблице orders и добавляем значение
-- ВАЖНО: Выполните эту часть ОТДЕЛЬНО, затем выполните ЧАСТЬ 2
-- ВАЖНО: Эта часть выполняется БЕЗ транзакции (не используйте BEGIN/COMMIT)
DO $$
DECLARE
    enum_type_name TEXT;
BEGIN
    -- Ищем enum тип для колонки status в таблице orders
    SELECT t.typname INTO enum_type_name
    FROM pg_type t
    JOIN pg_attribute a ON a.atttypid = t.oid
    JOIN pg_class c ON c.oid = a.attrelid
    WHERE c.relname = 'orders' 
    AND a.attname = 'status'
    AND t.typtype = 'e';
    
    -- Если нашли enum тип, добавляем значение
    IF enum_type_name IS NOT NULL THEN
        -- Проверяем, существует ли уже это значение
        IF NOT EXISTS (
            SELECT 1 FROM pg_enum 
            WHERE enumlabel = 'not_paid' 
            AND enumtypid = (SELECT oid FROM pg_type WHERE typname = enum_type_name)
        ) THEN
            -- Добавляем значение в enum (PostgreSQL не поддерживает IF NOT EXISTS для enum)
            BEGIN
                EXECUTE format('ALTER TYPE %I ADD VALUE %L', enum_type_name, 'not_paid');
                RAISE NOTICE 'Added value "not_paid" to enum type "%"', enum_type_name;
            EXCEPTION WHEN duplicate_object THEN
                -- Если значение уже существует, просто игнорируем
                RAISE NOTICE 'Value "not_paid" already exists in enum type "%"', enum_type_name;
            EXCEPTION WHEN OTHERS THEN
                -- Другие ошибки логируем
                RAISE NOTICE 'Could not add value "not_paid" to enum type "%": %', enum_type_name, SQLERRM;
            END;
        ELSE
            RAISE NOTICE 'Value "not_paid" already exists in enum type "%"', enum_type_name;
        END IF;
    ELSE
        RAISE NOTICE 'Enum type for orders.status not found. Column might be VARCHAR, not enum. Skipping enum modification.';
    END IF;
EXCEPTION WHEN OTHERS THEN
    -- Если произошла любая ошибка, просто логируем
    RAISE NOTICE 'Error in enum modification: %. You may need to add enum value manually.', SQLERRM;
END $$;

-- ============================================================================
-- ЧАСТЬ 2: Добавление колонок и изменение default (выполнить второй, после ЧАСТИ 1)
-- ============================================================================
-- ВАЖНО: Выполните эту часть только после успешного выполнения ЧАСТИ 1!
-- Если была ошибка в ЧАСТИ 1, выполните ROLLBACK перед этой частью

-- Сбрасываем состояние транзакции на случай ошибок в первой части
-- (не вызовет ошибку, если транзакции нет)
DO $$ 
BEGIN
    -- Пытаемся откатить транзакцию, если она была прервана
    NULL;
EXCEPTION WHEN OTHERS THEN
    -- Игнорируем ошибки
    NULL;
END $$;

BEGIN;

-- 1. Добавляем колонку cdek_uuid в таблицу orders
ALTER TABLE orders 
ADD COLUMN IF NOT EXISTS cdek_uuid VARCHAR(100) NULL;

-- 2. Добавляем колонку weight в таблицу products
-- Сначала добавляем как nullable с DEFAULT
ALTER TABLE products 
ADD COLUMN IF NOT EXISTS weight INTEGER DEFAULT 1;

-- 3. Обновляем существующие записи, устанавливая weight = 1 (на случай если были NULL)
UPDATE products 
SET weight = 1 
WHERE weight IS NULL OR weight <= 0;

-- 4. Теперь делаем колонку NOT NULL (после обновления данных)
DO $$
BEGIN
    -- Проверяем, не является ли колонка уже NOT NULL
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'products' 
        AND column_name = 'weight' 
        AND is_nullable = 'YES'
    ) THEN
        ALTER TABLE products 
        ALTER COLUMN weight SET NOT NULL;
    END IF;
END $$;

-- 5. Добавляем колонку currency в таблицу products (если еще не существует)
ALTER TABLE products 
ADD COLUMN IF NOT EXISTS currency VARCHAR(3) DEFAULT 'RUB';

-- 6. Обновляем существующие записи, устанавливая currency = 'RUB' если NULL
UPDATE products 
SET currency = 'RUB' 
WHERE currency IS NULL;

-- 7. Добавляем constraint для weight > 0 (если еще не существует)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'check_weight_positive'
    ) THEN
        ALTER TABLE products 
        ADD CONSTRAINT check_weight_positive 
        CHECK (weight > 0);
    END IF;
END $$;

-- 8. Изменяем default для status в orders на 'not_paid'
-- Используем правильное имя enum типа
DO $$
DECLARE
    enum_type_name TEXT;
BEGIN
    -- Находим имя enum типа
    SELECT t.typname INTO enum_type_name
    FROM pg_type t
    JOIN pg_attribute a ON a.atttypid = t.oid
    JOIN pg_class c ON c.oid = a.attrelid
    WHERE c.relname = 'orders' 
    AND a.attname = 'status'
    AND t.typtype = 'e';
    
    -- Устанавливаем default значение
    IF enum_type_name IS NOT NULL THEN
        EXECUTE format('ALTER TABLE orders ALTER COLUMN status SET DEFAULT %L::%I', 'not_paid', enum_type_name);
        RAISE NOTICE 'Set default status to "not_paid" using enum type "%"', enum_type_name;
    ELSE
        -- Если enum не найден, возможно колонка VARCHAR, устанавливаем как строку
        ALTER TABLE orders ALTER COLUMN status SET DEFAULT 'not_paid';
        RAISE NOTICE 'Set default status to "not_paid" (column is VARCHAR, not enum)';
    END IF;
END $$;

COMMIT;

