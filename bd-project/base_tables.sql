-- 0) Categorias para los registros
CREATE TABLE IF NOT EXISTS categories (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(255) UNIQUE,
    description TEXT,
    created_at  TIMESTAMP DEFAULT NOW(),
    updated_at  TIMESTAMP DEFAULT NOW()
);

-- 1) Sitios fuente: guarda el dominio/URL raíz y su árbol (lo que ya tienes)
CREATE TABLE IF NOT EXISTS websites (
     id            SERIAL PRIMARY KEY,
     domain        VARCHAR(255) UNIQUE,             -- ej: unisabana.edu.co
     url           VARCHAR(1024) NOT NULL,          -- home del dominio
     tree          JSONB,                           -- árbol de navegación
     description   TEXT,
     category_id   INTEGER,
     created_at    TIMESTAMP DEFAULT NOW(),
     updated_at    TIMESTAMP DEFAULT NOW()
);


CREATE TABLE IF NOT EXISTS website_config (
    id SERIAL PRIMARY KEY,
    website_id INTEGER NOT NULL REFERENCES websites(id) ON DELETE CASCADE,
    total_results_selector VARCHAR(255) NOT NULL,
    pagination_pattern VARCHAR(500),
    link_selector VARCHAR(255),
    link_job VARCHAR(500),
    link_pattern VARCHAR(500),
    job_data_selector VARCHAR(255),
    job_detail_selector VARCHAR(255),
    jobs_per_page INTEGER DEFAULT 50,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- índice útil para consultas por dominio
CREATE INDEX IF NOT EXISTS idx_websites_domain ON websites(domain);

-- 2) Páginas del dominio: cada URL concreta que procesamos
CREATE TABLE IF NOT EXISTS program_pages_raw (
     id            UUID DEFAULT gen_random_uuid() PRIMARY KEY,
     website_id    INTEGER REFERENCES websites(id) ON DELETE CASCADE,
     url           VARCHAR(2048) UNIQUE,            -- URL de la página del programa (o candidata)
     status        VARCHAR(40)   DEFAULT 'pending', -- pending|ok|timeout|cloudflare|forbidden|no-program|error
     http_code     INTEGER,
     content_hash  VARCHAR(64),                     -- hash del HTML para detectar cambios
     html          TEXT,                            -- HTML crudo
     fetched_at    TIMESTAMP,                       -- cuándo se descargó
     created_at    TIMESTAMP DEFAULT NOW(),
     updated_at    TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_program_pages_raw_status ON program_pages_raw(status);
CREATE INDEX IF NOT EXISTS idx_program_pages_raw_website ON program_pages_raw(website_id);

ALTER TABLE program_pages_raw ADD CONSTRAINT unique_program_page_url UNIQUE (url);

-- 3) Datos estructurados extraídos de cada página (para análisis y vector DB)
CREATE TABLE IF NOT EXISTS program_records_structured (
    id              UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    page_id         UUID REFERENCES program_pages_raw(id) ON DELETE CASCADE,
    program_name    VARCHAR(512),
    level           VARCHAR(64),        -- pregrado|posgrado|maestria|doctorado|etc
    modality        VARCHAR(64),        -- presencial|virtual|mixta
    duration        VARCHAR(128),       -- "4 semestres", "2 años", etc
    price           VARCHAR(128),
    subjects        JSONB,              -- lista/JSON de materias si la extraes
    description     TEXT,
    extracted_at    TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_program_structured_level ON program_records_structured(level);
CREATE INDEX IF NOT EXISTS idx_program_structured_domain ON program_records_structured(domain);
CREATE INDEX IF NOT EXISTS idx_program_structured_name   ON program_records_structured(program_name);

ALTER TABLE program_records_structured ADD CONSTRAINT program_records_structured_page_id_unique UNIQUE (page_id);

-- 4) Datos de trabajos en crudo
CREATE TABLE IF NOT EXISTS job_pages_raw (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    website_id INTEGER REFERENCES websites(id) ON DELETE CASCADE,
    url VARCHAR(2048) UNIQUE,
    status TEXT,
    http_code INTEGER,
    content_hash TEXT,
    html TEXT,
    fetched_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

ALTER TABLE job_pages_raw
    ADD CONSTRAINT job_pages_raw_url_unique UNIQUE (url);

-- 5) Datos estructurados de las ofertas de trabajo
CREATE TABLE IF NOT EXISTS job_records_structured (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    page_id UUID UNIQUE REFERENCES job_pages_raw(id) ON DELETE CASCADE,
    domain VARCHAR(255),
    job_title TEXT,
    company TEXT,
    location TEXT,
    salary TEXT,
    posted_at TIMESTAMP NULL,
    tags JSONB,
    description TEXT,
    extracted_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_job_structured_domain ON job_records_structured(domain);
CREATE INDEX IF NOT EXISTS idx_job_structured_job_title   ON job_records_structured(job_title);


CREATE TABLE scraper_jobs (
    id SERIAL PRIMARY KEY,
    website_id INTEGER,
    category INTEGER,
    url TEXT,
    status TEXT DEFAULT 'pending', -- pending, running, finished, error, timeout
    started_at TIMESTAMP,
    finished_at TIMESTAMP,
    last_heartbeat TIMESTAMP,
    tree JSONB,
    error TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
