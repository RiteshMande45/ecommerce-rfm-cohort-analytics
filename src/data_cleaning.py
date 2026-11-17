import csv
from pathlib import Path
from datetime import datetime

def clean_retail_data(input_path: str, output_path: str):
    print("Loading and cleaning raw dataset using standard Python...")
    input_file = Path(input_path)
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    initial_rows = 0
    cleaned_rows = 0

    with open(input_file, mode="r", encoding="ISO-8859-1") as infile, \
         open(output_file, mode="w", encoding="utf-8", newline="") as outfile:
        
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames + ["InvoiceMonth", "TotalRevenue"]
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()

        for row in reader:
            initial_rows += 1
            
            # 1. Drop records missing CustomerID
            cust_id = row.get("CustomerID", "").strip()
            if not cust_id:
                continue
                
            # 2. Filter out cancelled transactions ('C') & non-positive values
            invoice_no = row.get("InvoiceNo", "").strip()
            if invoice_no.startswith("C"):
                continue
                
            try:
                quantity = float(row.get("Quantity", 0))
                unit_price = float(row.get("UnitPrice", 0))
            except ValueError:
                continue
                
            if quantity <= 0 or unit_price <= 0:
                continue
                
            # 3. Parse InvoiceDate flexibly and engineer features
            inv_date_str = row.get("InvoiceDate", "").strip()
            dt = None
            for fmt in ("%m/%d/%Y %H:%M", "%Y-%m-%d %H:%M:%S", "%m/%d/%y %H:%M", "%d/%m/%Y %H:%M"):
                try:
                    dt = datetime.strptime(inv_date_str, fmt)
                    break
                except ValueError:
                    continue
            
            if dt is None:
                continue
            
            row["InvoiceMonth"] = dt.strftime("%Y-%m")
            row["TotalRevenue"] = round(quantity * unit_price, 2)
            row["Description"] = row.get("Description", "").strip()
            
            # Format CustomerID as clean integer string
            try:
                row["CustomerID"] = str(int(float(cust_id)))
            except ValueError:
                continue

            writer.writerow(row)
            cleaned_rows += 1

    print(f"Cleaned data: {initial_rows:,} -> {cleaned_rows:,} rows ({initial_rows - cleaned_rows:,} anomalies removed).")
    print(f"Saved cleaned dataset to {output_path}")

if __name__ == "__main__":
    clean_retail_data(
        input_path="data/raw/Online_Retail.csv",
        output_path="data/processed/cleaned_retail.csv"
    )
