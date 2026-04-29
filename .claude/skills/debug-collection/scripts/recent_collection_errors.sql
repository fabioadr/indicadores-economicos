SELECT *
FROM collection_logs
WHERE status = 'error'
ORDER BY started_at DESC
LIMIT 5;
