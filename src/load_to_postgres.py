import csv
from pathlib import Path
import os

def generate_sql_inserts():
    print("Preparing SQL insertion scripts for PostgreSQL...")
    
    # 1. Generate SQL for dim_customers from customer_segmented.csv
    seg_path = Path("data/processed/customer_segmented.csv")
    if seg_path.exists():
        with open(seg_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            insert_statements = []
            for row in reader:
                # Handle potential nulls or types
                cid = row["CustomerID"]
                cohort = row["CohortMonth"]
                recency = row["Recency"]
                freq = row["Frequency"]
                monetary = row["Monetary"]
                segment = row["Segment"].replace("'", "''")
                
                stmt = f"INSERT INTO dim_customers (CustomerID, CohortMonth, Recency, Frequency, Monetary, CustomerSegment) VALUES ({cid}, '{cohort}', {recency}, {freq}, {monetary}, '{segment}') ON CONFLICT (CustomerID) DO NOTHING;"
                insert_statements.append(stmt)
                
        output_sql = Path("sql/load_dim_customers.sql")
        with open(output_sql, mode="w", encoding="utf-8") as out:
            out.write("\n".join(insert_statements))
        print(f"Generated {output_sql} with {len(insert_statements):,} customer records.")

    # 2. Generate SQL for cohort_retention from cohort_retention_matrix.csv
    matrix_path = Path("reports/cohort_retention_matrix.csv")
    if matrix_path.exists():
        with open(matrix_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            insert_statements = []
            for row in reader:
                c_month = row["CohortMonth"]
                size = row["Size"]
                m0 = row["M0"]
                m1 = row["M1"]
                m2 = row["M2"]
                m3 = row["M3"]
                m4 = row["M4"]
                m5 = row["M5"]
                
                stmt = f"INSERT INTO cohort_retention (CohortMonth, CohortSize, M0, M1, M2, M3, M4, M5) VALUES ('{c_month}', {size}, {m0}, {m1}, {m2}, {m3}, {m4}, {m5}) ON CONFLICT (CohortMonth) DO NOTHING;"
                insert_statements.append(stmt)
                
        output_sql = Path("sql/load_cohort_retention.sql")
        with open(output_sql, mode="w", encoding="utf-8") as out:
            out.write("\n".join(insert_statements))
        print(f"Generated {output_sql} with {len(insert_statements)} cohort rows.")

    print("\nSQL bulk-load scripts generated successfully inside the sql/ folder!")
    print("You can easily execute load_dim_customers.sql and load_cohort_retention.sql directly in your pgAdmin Query Tool for ecommerce_analytics.")

if __name__ == "__main__":
    generate_sql_inserts()
