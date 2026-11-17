import csv
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

def run_rfm_and_cohorts(input_path: str):
    print("Loading cleaned dataset for analytics...")
    input_file = Path(input_path)
    
    data = []
    with open(input_file, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            inv_date_str = row["InvoiceDate"].strip()
            dt = None
            for fmt in ("%Y-%m-%d %H:%M:%S", "%m/%d/%y %H:%M", "%m/%d/%Y %H:%M", "%d/%m/%Y %H:%M"):
                try:
                    dt = datetime.strptime(inv_date_str, fmt)
                    break
                except ValueError:
                    continue
            
            if dt is None:
                continue

            data.append({
                "CustomerID": row["CustomerID"],
                "InvoiceNo": row["InvoiceNo"],
                "InvoiceDate": dt,
                "InvoiceMonth": row["InvoiceMonth"],
                "TotalRevenue": float(row["TotalRevenue"])
            })

    if not data:
        print("No valid data found for analysis.")
        return

    # Find snapshot date (1 day after latest invoice)
    max_date = max(row["InvoiceDate"] for row in data)
    snapshot_date = max_date + timedelta(days=1)
    print(f"Dataset date range: {min(row['InvoiceDate'] for row in data).strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')}")
    print(f"RFM Snapshot Date set to: {snapshot_date.strftime('%Y-%m-%d')}")

    # 1. Calculate RFM Metrics per Customer
    customers = defaultdict(lambda: {"min_date": None, "max_date": None, "freq": set(), "monetary": 0.0})
    
    for row in data:
        cid = row["CustomerID"]
        cust = customers[cid]
        cust["freq"].add(row["InvoiceNo"])
        cust["monetary"] += row["TotalRevenue"]
        
        inv_dt = row["InvoiceDate"]
        if cust["min_date"] is None or inv_dt < cust["min_date"]:
            cust["min_date"] = inv_dt
        if cust["max_date"] is None or inv_dt > cust["max_date"]:
            cust["max_date"] = inv_dt

    rfm_results = []
    for cid, metrics in customers.items():
        recency = (snapshot_date - metrics["max_date"]).days
        frequency = len(metrics["freq"])
        monetary = round(metrics["monetary"], 2)
        cohort_month = metrics["min_date"].strftime("%Y-%m")
        
        rfm_results.append({
            "CustomerID": cid,
            "Recency": recency,
            "Frequency": frequency,
            "Monetary": monetary,
            "CohortMonth": cohort_month
        })

    print(f"Calculated RFM metrics for {len(rfm_results):,} unique customers.")

    # Save RFM summary
    rfm_output = Path("data/processed/customer_rfm.csv")
    rfm_output.parent.mkdir(parents=True, exist_ok=True)
    with open(rfm_output, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["CustomerID", "Recency", "Frequency", "Monetary", "CohortMonth"])
        writer.writeheader()
        writer.writerows(rfm_results)
    
    print(f"Saved customer RFM summary to {rfm_output}")

if __name__ == "__main__":
    run_rfm_and_cohorts("data/processed/cleaned_retail.csv")
