-- Replace IPCA with the indicator code under investigation.
SELECT code, connector_type, connector_config, last_collected_at
FROM indicators
WHERE code = 'IPCA';
