# Olist data model

Raw CSVs: `data/raw/olist/`  
Names below match **pandas variables** and **DuckDB tables** in `01_data_ingestion.ipynb`.

| CSV file | Variable / table name |
|----------|------------------------|
| olist_orders_dataset.csv | `orders` |
| olist_customers_dataset.csv | `customers` |
| olist_order_items_dataset.csv | `order_items` |
| olist_order_payments_dataset.csv | `payments` → DuckDB `order_payments` |
| olist_order_reviews_dataset.csv | `reviews` → DuckDB `order_reviews` |
| olist_products_dataset.csv | `products` |
| olist_sellers_dataset.csv | `sellers` |
| olist_geolocation_dataset.csv | `geolocation` |
| product_category_name_translation.csv | `product_category_name_translation` |

Target mart: **`orders_analytical`** — grain = one row per `order_id`.

---

## Tables

orders(order_id, customer_id, order_status, order_purchase_timestamp, order_approved_at, order_delivered_carrier_date, order_delivered_customer_date, order_estimated_delivery_date)
PRIMARY KEY (order_id)

customers(customer_id, customer_unique_id, customer_zip_code_prefix, customer_city, customer_state)
PRIMARY KEY (customer_id)

order_items(order_id, order_item_id, product_id, seller_id, shipping_limit_date, price, freight_value)
PRIMARY KEY (order_id, order_item_id)

order_payments(order_id, payment_sequential, payment_type, payment_installments, payment_value)
PRIMARY KEY (order_id, payment_sequential)

order_reviews(review_id, order_id, review_score, review_comment_title, review_comment_message, review_creation_date, review_answer_timestamp)
PRIMARY KEY (review_id)

products(product_id, product_category_name, product_name_lenght, product_description_lenght, product_photos_qty, product_weight_g, product_length_cm, product_height_cm, product_width_cm)
PRIMARY KEY (product_id)

sellers(seller_id, seller_zip_code_prefix, seller_city, seller_state)
PRIMARY KEY (seller_id)

geolocation(geolocation_zip_code_prefix, geolocation_lat, geolocation_lng, geolocation_city, geolocation_state)
PRIMARY KEY (none — reference table, many rows per zip)

product_category_name_translation(product_category_name, product_category_name_english)
PRIMARY KEY (product_category_name)

---

## Foreign keys

orders(customer_id) REFERENCES customers(customer_id)

order_items(order_id) REFERENCES orders(order_id)
order_items(product_id) REFERENCES products(product_id)
order_items(seller_id) REFERENCES sellers(seller_id)

order_payments(order_id) REFERENCES orders(order_id)

order_reviews(order_id) REFERENCES orders(order_id)

products(product_category_name) REFERENCES product_category_name_translation(product_category_name)

customers(customer_zip_code_prefix) REFERENCES geolocation(geolocation_zip_code_prefix)

sellers(seller_zip_code_prefix) REFERENCES geolocation(geolocation_zip_code_prefix)

---

## Notes

- Pandas: `payments`, `reviews`. DuckDB: `order_payments`, `order_reviews`.
- `customer_id` is unique per row in `customers` but Olist issues a new `customer_id` per order; use `customer_unique_id` for the same person across orders.
- Aggregate `order_items` / `order_payments` before joining to `orders` if grain = one row per `order_id`.
