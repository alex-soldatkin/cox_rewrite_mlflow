# Legacy Data Acquisition Map

**Directory:** `DATA_ACQ_DIR`
**Path:** `/Users/alexandersoldatkin/projects/factions-networks-thesis/data_acquisition`

This directory contains scripts and Scrapy spiders for gathering data from various sources (CBR, Banki.ru, Reputation.ru, RBC, Google, DaData) and integrating it with Neo4j.

## Root Scripts

### 1. `async_reputation_seo.py`

- **Purpose**: Asynchronously scrapes company data from `reputation.ru`.
- **Input**: Neo4j database (queries companies).
- **Output**: `ppl_data.jsonl`.
- **Key Dependencies**: `neo4j`, `httpx`, `asyncio`.

### 2. `reputation_seo_neo.py`

- **Purpose**: Fetches company links from Neo4j and queries `reputation.ru` for SEO data.
- **Input**: Neo4j (Entities with links).
- **Output**: `reputation_seo.jsonl`.
- **Key Features**: Rate limiting, retry logic.

### 3. `reputation_client_search.py`

- **Purpose**: Searches for companies on `reputation.ru` using names from Neo4j.
- **Input**: Neo4j (`MATCH (c:Person) ...`).
- **Output**: `ppl_data.jsonl` (saves search results).

### 4. `reputation_accounting.py`

- **Purpose**: Scrapes financial indicators from `companies.rbc.ru` for companies missing accounting data.
- **Input**: `../data/accounting_json/accounting_inn_id.jsonl`.
- **Output**: `../data/accounting_json/accounting_reports_rbc.jsonl`.
- **Key Features**: Checks existing scraped INNs to avoid duplicates.

### 5. `dadata_geocoding.py`

- **Purpose**: Geocodes addresses from reputation files using DaData API.
- **Input**: `../data/reputation_govorgs/reputation_*.jsonl`.
- **Output**: `../data/geocoding_results/dadata_geocoding.jsonl`.
- **Key Features**: Filters out already processed IDs.

### 6. `google_geocoding_api.py`

- **Purpose**: Geocodes organization addresses using Google Places API.
- **Input**: Neo4j (Org nodes).
- **Output**: `../data/geocoding_results/google_geocoding_orgs.jsonl`.
- **Key Features**: Adds `neo4j_id` to the output for graph matching.

## Subdirectory: `banks_cbr/banks_cbr/spiders/`

Scrapy spiders for targeted data collection.

### 1. `banki_ru.py` (Spider: `banki_ru`)

- **Target**: `banki.ru/banks/memory/` (Book of Memory - revoked licenses).
- **Data**: Bank details, news links, license revocation dates.

### 2. `banki_ru_active.py` (Spider: `banki_ru_active`)

- **Target**: `banki.ru/banks/` (Active banks).
- **Data**: Active bank lists, basic info (REGN, OGRN).

### 3. `banks_spider.py` (Spider: `banks_spider`)

- **Target**: `reputation.ru` (Search API).
- **Input**: `cbr.json`.
- **Purpose**: Matches CBR bank list to Reputation.ru entities.

### 4. `reputation_seo.py` (Spider: `reputation_seo`)

- **Target**: `reputation.ru` (Entity SEO API).
- **Input**: Neo4j queries for companies with links.
- **Logic**: Handles foreign entities (Belarus, Kazakhstan) differently.
- **Output**: SEO data for entities.

### 5. `reputation_client_search_spider.py` (Spider: `reputation_client_search`)

- **Target**: `reputation.ru` (Client Search API).
- **Input**: Neo4j query for clients (`to_scrape_client` flag).
- **Purpose**: Scrapes client search results.

### 6. `banksbd_spider.py` (Spider: `banksbd_spider`)

- **Target**: `banksbd.spb.ru`
- **Purpose**: Scrapes historic bank data.
