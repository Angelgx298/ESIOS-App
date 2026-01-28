-- migrations/001_add_indexes.sql
-- Composite index for common query pattern (zone + timestamp)
CREATE INDEX IF NOT EXISTS idx_zone_timestamp 
ON electricity_prices(zone_id, timestamp DESC);

-- BRIN index for time-series data (space-efficient)
CREATE INDEX IF NOT EXISTS idx_timestamp_brin 
ON electricity_prices USING BRIN(timestamp) WITH (pages_per_range = 128);

-- Analyze table to update query planner statistics
ANALYZE electricity_prices;

-- Show index sizes
SELECT 
    indexrelname as index_name,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size
FROM pg_stat_user_indexes
WHERE schemaname = 'public' AND relname = 'electricity_prices'
ORDER BY pg_relation_size(indexrelid) DESC;
