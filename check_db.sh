#!/bin/bash
# Скрипт для проверки и исправления product_id в БД

echo "=================================="
echo "ПРОВЕРКА ДАННЫХ product_colors"
echo "=================================="
echo ""

# Подключаемся к PostgreSQL через Docker контейнер
docker exec -it psih-postgres psql -U postgres -d psih_shop -c "
SELECT 
    id,
    product_id,
    slug,
    title,
    CASE 
        WHEN id = product_id THEN '❌ ПРОБЛЕМА: id = product_id'
        ELSE '✅ OK'
    END as status
FROM product_colors
ORDER BY id;
"

echo ""
echo "=================================="
echo "СТАТИСТИКА"
echo "=================================="

docker exec -it psih-postgres psql -U postgres -d psih_shop -c "
SELECT 
    COUNT(*) as total_colors,
    COUNT(CASE WHEN id = product_id THEN 1 END) as problem_count,
    COUNT(CASE WHEN id != product_id THEN 1 END) as ok_count
FROM product_colors;
"
