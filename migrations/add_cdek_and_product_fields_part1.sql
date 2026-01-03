-- ============================================================================
-- ЧАСТЬ 1: Добавление нового значения в enum
-- ============================================================================
-- ВАЖНО: Выполните эту часть ПЕРВОЙ, ОТДЕЛЬНО от части 2
-- В pgAdmin: выделите и выполните только этот блок (до строки с ЧАСТЬ 2)

-- Находим имя enum типа для колонки status в таблице orders и добавляем значение
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
            -- Добавляем значение в enum
            EXECUTE format('ALTER TYPE %I ADD VALUE %L', enum_type_name, 'not_paid');
            RAISE NOTICE 'Added value "not_paid" to enum type "%"', enum_type_name;
        ELSE
            RAISE NOTICE 'Value "not_paid" already exists in enum type "%"', enum_type_name;
        END IF;
    ELSE
        RAISE NOTICE 'Enum type for orders.status not found. Column might be VARCHAR, not enum. Skipping enum modification.';
    END IF;
EXCEPTION 
    WHEN duplicate_object THEN
        -- Если значение уже существует, просто игнорируем
        RAISE NOTICE 'Value "not_paid" already exists in enum. Continuing...';
    WHEN OTHERS THEN
        -- Если произошла любая ошибка, просто логируем
        RAISE NOTICE 'Error in enum modification: %. You may need to add enum value manually.', SQLERRM;
END $$;

