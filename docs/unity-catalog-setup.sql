-- Unity Catalog setup for AgentOps Lakehouse.
-- Run once in the Databricks SQL editor as a metastore admin, after the storage
-- account exists and an access connector has access to it (Storage Blob Data
-- Contributor on the storage account).
--
-- Before running:
--   1. Create a storage credential from the access connector
--      (Catalog > External Data > Credentials). Replace <storage-credential> below.
--   2. Replace <storage-account> with your storage account name. Storage account
--      names are globally unique, so yours will differ from the one in this repo.

CREATE EXTERNAL LOCATION IF NOT EXISTS loc_bronze
  URL 'abfss://bronze@<storage-account>.dfs.core.windows.net/'
  WITH (STORAGE CREDENTIAL `<storage-credential>`);

CREATE EXTERNAL LOCATION IF NOT EXISTS loc_silver
  URL 'abfss://silver@<storage-account>.dfs.core.windows.net/'
  WITH (STORAGE CREDENTIAL `<storage-credential>`);

CREATE EXTERNAL LOCATION IF NOT EXISTS loc_gold
  URL 'abfss://gold@<storage-account>.dfs.core.windows.net/'
  WITH (STORAGE CREDENTIAL `<storage-credential>`);

-- The project used the workspace's default catalog, dbw_agentops. If your
-- metastore has no default storage, add a MANAGED LOCATION to this statement.
CREATE CATALOG IF NOT EXISTS dbw_agentops;

CREATE SCHEMA IF NOT EXISTS dbw_agentops.bronze
  MANAGED LOCATION 'abfss://bronze@<storage-account>.dfs.core.windows.net/tables';

CREATE SCHEMA IF NOT EXISTS dbw_agentops.silver
  MANAGED LOCATION 'abfss://silver@<storage-account>.dfs.core.windows.net/tables';

CREATE SCHEMA IF NOT EXISTS dbw_agentops.gold
  MANAGED LOCATION 'abfss://gold@<storage-account>.dfs.core.windows.net/tables';
