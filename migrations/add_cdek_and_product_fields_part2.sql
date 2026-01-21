-- ============================================================================
-- ЧАСТЬ 2: Добавление колонок и изменение default
-- ============================================================================
-- ВАЖНО: Выполните эту часть ПОСЛЕ успешного выполнения ЧАСТИ 1!
-- Если была ошибка в ЧАСТИ 1, сначала выполните ROLLBACK в pgAdmin

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
        EXECUTE format('ALTER TABLE orders ALTER COLUMN status SET DEFAULT %L::%I', 'NOT_PAID', enum_type_name);
        RAISE NOTICE 'Set default status to "NOT_PAID" using enum type "%"', enum_type_name;
    ELSE
        -- Если enum не найден, возможно колонка VARCHAR, устанавливаем как строку
        ALTER TABLE orders ALTER COLUMN status SET DEFAULT 'NOT_PAID';
        RAISE NOTICE 'Set default status to "NOT_PAID" (column is VARCHAR, not enum)';
    END IF;
END $$;

COMMIT;


