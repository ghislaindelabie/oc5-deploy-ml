-- PostgreSQL Schema for HR Attrition Predictions
--
-- Purpose: Store all predictions made by the API for:
--   - Auditing and compliance
--   - Model performance monitoring
--   - Historical analysis
--
-- Usage: psql -U postgres -d oc5_attrition -f db/schema.sql

-- Main predictions table
-- TODO: Implement CREATE TABLE predictions with:
--   - id: SERIAL PRIMARY KEY
--   - input_data: JSONB (all employee features)
--   - prediction: VARCHAR(3) CHECK (prediction IN ('Oui', 'Non'))
--   - probability: FLOAT CHECK (probability >= 0 AND probability <= 1)
--   - risk_level: VARCHAR(10) CHECK (risk_level IN ('Low', 'Medium', 'High'))
--   - top_risk_factors: JSONB
--   - model_version: VARCHAR(50) NOT NULL DEFAULT 'xgb_enhanced_v1'
--   - created_at: TIMESTAMP DEFAULT NOW()
--   - user_id: VARCHAR(100) (nullable)
--   - session_id: VARCHAR(100) (nullable)

-- Indexes for performance
-- TODO: CREATE INDEX idx_predictions_created_at ON predictions(created_at DESC);
-- TODO: CREATE INDEX idx_predictions_risk_level ON predictions(risk_level);
-- TODO: CREATE INDEX idx_predictions_model_version ON predictions(model_version);

-- Optional: Model performance monitoring table
-- TODO: CREATE TABLE model_performance (
--   id: SERIAL PRIMARY KEY
--   date: DATE NOT NULL
--   total_predictions: INT
--   pct_high_risk: FLOAT
--   pct_oui: FLOAT
--   avg_probability: FLOAT
--   model_version: VARCHAR(50)
--   created_at: TIMESTAMP DEFAULT NOW()
-- )

-- SQL TO BE WRITTEN IN PHASE 2
