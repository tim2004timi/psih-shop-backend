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
