SELECT c.customer_id,
       c.birth_date,
       SUM(o.quantity_product * p.price) AS revenue_cents
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
JOIN product p ON o.product_id = p.product_id
WHERE c.birth_date > '2000-09-25'
  AND c.birth_date <= '2001-09-25'
GROUP BY c.customer_id, c.birth_date
ORDER BY c.customer_id;
