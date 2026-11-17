import csv
from pathlib import Path
from collections import defaultdict
import math
import random
from datetime import datetime

def run_advanced_analytics():
    print("--- Starting Advanced Analytics & Segmentation Pipeline ---")
    
    # 1. Load customer RFM data
    rfm_path = Path("data/processed/customer_rfm.csv")
    if not rfm_path.exists():
        print("Error: customer_rfm.csv not found. Run rfm_analysis.py first.")
        return

    customers = []
    with open(rfm_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            customers.append({
                "CustomerID": row["CustomerID"],
                "Recency": float(row["Recency"]),
                "Frequency": float(row["Frequency"]),
                "Monetary": float(row["Monetary"]),
                "CohortMonth": row["CohortMonth"]
            })

    print(f"Loaded {len(customers):,} customer RFM profiles.")

    # 2. Log-transformation & Feature Standardization
    for c in customers:
        c["R_log"] = math.log(c["Recency"] + 1)
        c["F_log"] = math.log(c["Frequency"] + 1)
        c["M_log"] = math.log(c["Monetary"] + 1)

    for key in ["R_log", "F_log", "M_log"]:
        vals = [c[key] for c in customers]
        min_v, max_v = min(vals), max(vals)
        rng = max_v - min_v if max_v != min_v else 1.0
        for c in customers:
            c[f"{key}_norm"] = (c[key] - min_v) / rng

    # 3. K-Means Clustering (K=4)
    k = 4
    random.seed(42)
    centroids = []
    for _ in range(k):
        sample = random.choice(customers)
        centroids.append([sample["R_log_norm"], sample["F_log_norm"], sample["M_log_norm"]])

    for iteration in range(50):
        clusters = defaultdict(list)
        for c in customers:
            point = [c["R_log_norm"], c["F_log_norm"], c["M_log_norm"]]
            best_cluster = 0
            min_dist = float("inf")
            for i, centroid in enumerate(centroids):
                dist = sum((p - centroid[j]) ** 2 for j, p in enumerate(point))
                if dist < min_dist:
                    min_dist = dist
                    best_cluster = i
            clusters[best_cluster].append(c)
            c["Cluster"] = best_cluster

        new_centroids = []
        for i in range(k):
            group = clusters[i]
            if not group:
                new_centroids.append(centroids[i])
                continue
            mean_r = sum(c["R_log_norm"] for c in group) / len(group)
            mean_f = sum(c["F_log_norm"] for c in group) / len(group)
            mean_m = sum(c["M_log_norm"] for c in group) / len(group)
            new_centroids.append([mean_r, mean_f, mean_m])
        centroids = new_centroids

    # 4. Assign Business Personas based on Cluster Centroid Profiles
    cluster_stats = {}
    for i in range(k):
        group = [c for c in customers if c["Cluster"] == i]
        avg_m = sum(c["Monetary"] for c in group) / len(group) if group else 0
        avg_f = sum(c["Frequency"] for c in group) / len(group) if group else 0
        avg_r = sum(c["Recency"] for c in group) / len(group) if group else 0
        cluster_stats[i] = {"avg_m": avg_m, "avg_f": avg_f, "avg_r": avg_r, "count": len(group)}

    sorted_clusters = sorted(cluster_stats.keys(), key=lambda x: cluster_stats[x]["avg_m"], reverse=True)
    
    label_map = {}
    label_map[sorted_clusters[0]] = "Champions"
    label_map[sorted_clusters[1]] = "Loyal Customers"
    label_map[sorted_clusters[2]] = "At-Risk Customers"
    label_map[sorted_clusters[3]] = "Lost / Hibernating"

    for c in customers:
        c["Segment"] = label_map[c["Cluster"]]

    print("\n--- Unsupervised Machine Learning Segmentation Summary ---")
    for seg_name, stats in sorted(cluster_stats.items(), key=lambda x: label_map[x[0]]):
        s_name = label_map[seg_name]
        print(f"Segment: {s_name:<20} | Count: {stats['count']:5,d} | Avg Monetary:  | Avg Freq: {stats['avg_f']:4.1f} | Avg Recency: {stats['avg_r']:5.1f} days")

    # Save segmented output
    seg_output = Path("data/processed/customer_segmented.csv")
    with open(seg_output, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["CustomerID", "Recency", "Frequency", "Monetary", "CohortMonth", "Segment"])
        writer.writeheader()
        for c in customers:
            writer.writerow({
                "CustomerID": c["CustomerID"],
                "Recency": c["Recency"],
                "Frequency": c["Frequency"],
                "Monetary": c["Monetary"],
                "CohortMonth": c["CohortMonth"],
                "Segment": c["Segment"]
            })
    print(f"\nSaved segmented customer dataset to {seg_output}")

    # 5. Cohort Analysis & Retention Matrix
    print("\n--- Generating Cohort Retention Matrix ---")
    cleaned_path = Path("data/processed/cleaned_retail.csv")
    if not cleaned_path.exists():
        print("Error: cleaned_retail.csv not found.")
        return

    customer_cohort = {c["CustomerID"]: c["CohortMonth"] for c in customers}

    cohort_totals = defaultdict(int)
    unique_cohort_customers = defaultdict(set)
    with open(cleaned_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cid = row["CustomerID"]
            inv_month = row["InvoiceMonth"]
            if cid in customer_cohort:
                c_month = customer_cohort[cid]
                if inv_month == c_month:
                    unique_cohort_customers[c_month].add(cid)

    for c_month, custs in unique_cohort_customers.items():
        cohort_totals[c_month] = len(custs)

    active_per_cohort_month = defaultdict(lambda: defaultdict(set))
    with open(cleaned_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cid = row["CustomerID"]
            inv_month = row["InvoiceMonth"]
            if cid in customer_cohort:
                c_month = customer_cohort[cid]
                active_per_cohort_month[c_month][inv_month].add(cid)

    months_list = sorted(cohort_totals.keys())
    header = "Cohort   | Size  | " + " | ".join([f"M{i}" for i in range(6)])
    print(header)
    print("-" * len(header))

    matrix_rows = []
    for c_month in months_list:
        size = cohort_totals[c_month]
        row_str = f"{c_month} | {size:5d} | "
        c_index_data = {}
        
        c_dt = datetime.strptime(c_month + "-01", "%Y-%m-%d")
        for i in range(6):
            target_dt = c_dt
            for _ in range(i):
                if target_dt.month == 12:
                    target_dt = target_dt.replace(year=target_dt.year + 1, month=1)
                else:
                    target_dt = target_dt.replace(month=target_dt.month + 1)
            target_month_str = target_dt.strftime("%Y-%m")
            
            active_count = len(active_per_cohort_month[c_month][target_month_str])
            pct = (active_count / size * 100) if size > 0 else 0.0
            row_str += f"{pct:5.1f}% | "
            c_index_data[f"M{i}"] = round(pct, 1)
        
        print(row_str)
        matrix_rows.append({"CohortMonth": c_month, "Size": size, **c_index_data})

    reports_dir = Path("reports")
    reports_dir.mkdir(parents=True, exist_ok=True)
    matrix_output = reports_dir / "cohort_retention_matrix.csv"
    
    with open(matrix_output, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["CohortMonth", "Size", "M0", "M1", "M2", "M3", "M4", "M5"])
        writer.writeheader()
        writer.writerows(matrix_rows)

    print(f"\nSaved Cohort Retention Matrix to {matrix_output}")
    print("\n--- Advanced Analytics Pipeline Completed Successfully! ---")

if __name__ == "__main__":
    run_advanced_analytics()
