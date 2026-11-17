-- ========================================================
-- E-Commerce RFM & Cohort Analytics - PostgreSQL Star Schema DDL
-- ========================================================

-- Drop existing tables if re-running (CASCADE handles foreign key dependencies)
DROP TABLE IF EXISTS fact_transactions CASCADE;
DROP TABLE IF EXISTS dim_customers CASCADE;
DROP TABLE IF EXISTS cohort_retention CASCADE;

-- 1. Customer Dimension Table (Includes RFM & ML Segments)
CREATE TABLE dim_customers (
    CustomerID INT PRIMARY KEY,
    CohortMonth VARCHAR(7) NOT NULL,
    Recency INT NOT NULL,
    Frequency INT NOT NULL,
    Monetary NUMERIC(10, 2) NOT NULL,
    CustomerSegment VARCHAR(50) NOT NULL
);

-- 2. Transactions Fact Table
CREATE TABLE fact_transactions (
    TransactionID SERIAL PRIMARY KEY,
    InvoiceNo VARCHAR(20) NOT NULL,
    StockCode VARCHAR(20) NOT NULL,
    Description VARCHAR(255),
    Quantity INT NOT NULL,
    UnitPrice NUMERIC(10, 2) NOT NULL,
    TotalRevenue NUMERIC(10, 2) NOT NULL,
    InvoiceDate TIMESTAMP NOT NULL,
    InvoiceMonth VARCHAR(7) NOT NULL,
    CustomerID INT,
    CONSTRAINT fk_customer FOREIGN KEY (CustomerID) REFERENCES dim_customers(CustomerID)
);

-- 3. Cohort Retention Summary Table
CREATE TABLE cohort_retention (
    CohortMonth VARCHAR(7),
    CohortSize INT,
    M0 NUMERIC(5,2),
    M1 NUMERIC(5,2),
    M2 NUMERIC(5,2),
    M3 NUMERIC(5,2),
    M4 NUMERIC(5,2),
    M5 NUMERIC(5,2),
    PRIMARY KEY (CohortMonth)
);
