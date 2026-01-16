#!/bin/bash
# Скрипт для исправления product_id в БД

echo "=================================="
echo "ИСПРАВЛЕНИЕ ДАННЫХ"
echo "=================================="
echo ""
echo "ВНИМАНИЕ! Этот скрипт изменит данные в БД!"
echo ""
echo "Выберите стратегию:"
echo "1 - Создать отдельный Product для каждого ProductColor"
echo "2 - Все ProductColor будут ссылаться на Product ID = 1"
echo ""
read -p "Ваш выбор (1/2): " choice

if [ "$choice" = "1" ]; then
    echo ""
    echo "🔧 Создаём базовые продукты и обновляем ссылки..."
    
    docker exec -it psih-postgres psql -U postgres -d psih_shop << 'EOF'
DO $$
DECLARE
    pc RECORD;
    new_product_id INTEGER;
BEGIN
    FOR pc IN SELECT id, slug, title FROM product_colors WHERE id = product_id
    LOOP
        -- Создаём новый базовый продукт
        INSERT INTO products (description, price, weight, currency, status)
        VALUES (
            'Базовый продукт для ' || pc.title,
            99.99,
            0.5,
            'RUB',
            'in_stock'
        )
        RETURNING id INTO new_product_id;
        
        -- Обновляем product_id в ProductColor
        UPDATE product_colors
        SET product_id = new_product_id
        WHERE id = pc.id;
        
        RAISE NOTICE '✅ %: product_id изменен с % на %', pc.slug, pc.id, new_product_id;
    END LOOP;
END $$;
EOF

elif [ "$choice" = "2" ]; then
    echo ""
    echo "🔧 Обновляем все ProductColor на Product ID = 1..."
    
    docker exec -it psih-postgres psql -U postgres -d psih_shop << 'EOF'
DO $$
DECLARE
    pc RECORD;
    base_product_exists BOOLEAN;
BEGIN
    -- Проверяем, существует ли Product с ID = 1
    SELECT EXISTS(SELECT 1 FROM products WHERE id = 1) INTO base_product_exists;
    
    IF NOT base_product_exists THEN
        RAISE EXCEPTION '❌ Product с ID = 1 не существует!';
    END IF;
    
    FOR pc IN SELECT id, slug FROM product_colors WHERE id = product_id
    LOOP
        UPDATE product_colors
        SET product_id = 1
        WHERE id = pc.id;
        
        RAISE NOTICE '✅ %: product_id изменен с % на 1', pc.slug, pc.id;
    END LOOP;
END $$;
EOF

else
    echo "❌ Отменено"
    exit 0
fi

echo ""
echo "=================================="
echo "ПРОВЕРКА РЕЗУЛЬТАТА"
echo "=================================="
echo ""

docker exec -it psih-postgres psql -U postgres -d psih_shop -c "
SELECT 
    id,
    product_id,
    slug,
    CASE 
        WHEN id = product_id THEN '❌ ПРОБЛЕМА'
        ELSE '✅ OK'
    END as status
FROM product_colors
ORDER BY id;
"
