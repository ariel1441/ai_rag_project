"""
Analyze the CSV file to see actual data distribution and inform field weighting decisions.
"""
import csv
import os
from collections import Counter

csv_path = 'data/raw/request.csv'

print("=" * 80)
print("ANALYZING CSV FILE FOR FIELD WEIGHTING")
print("=" * 80)
print()

if not os.path.exists(csv_path):
    print(f"ERROR: File not found: {csv_path}")
    exit(1)

# Read CSV
print(f"Reading {csv_path}...")
with open(csv_path, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

print(f"Total rows: {len(rows):,}")
print(f"Total columns: {len(rows[0]) if rows else 0}")
print()

# Analyze each field
print("=" * 80)
print("FIELD ANALYSIS")
print("=" * 80)
print()

# Categories
critical_fields = []
important_fields = []
supporting_fields = []
low_priority_fields = []
exclude_fields = []

for col_name in rows[0].keys():
    # Count non-null, non-empty values
    non_null = 0
    non_empty = 0
    distinct_values = set()
    sample_values = []
    
    for row in rows:
        value = row.get(col_name, '')
        if value and value.strip() and value.strip().upper() != 'NULL':
            non_null += 1
            if value.strip():
                non_empty += 1
                distinct_values.add(value.strip())
                if len(sample_values) < 3:
                    sample_values.append(value.strip()[:50])
    
    distinct_count = len(distinct_values)
    coverage_pct = (non_empty / len(rows) * 100) if rows else 0
    
    # Categorize
    col_lower = col_name.lower()
    
    # CRITICAL: Core descriptive text
    if any(x in col_lower for x in ['projectname', 'projectdesc', 'areadesc', 'remarks', 
                                    'description', 'job', 'penetrategrounddesc']):
        category = "CRITICAL"
        weight = 3.0
        reason = "Core descriptive text - main content"
        critical_fields.append((col_name, weight, reason, non_empty, distinct_count, coverage_pct, sample_values))
    
    # IMPORTANT: Names, contacts, responsible people, status/type
    elif any(x in col_lower for x in ['name', 'contact', 'responsible', 'employee', 
                                      'updatedby', 'createdby', 'status', 'type']):
        category = "IMPORTANT"
        weight = 2.0
        reason = "Names, contacts, responsible people, or status/type"
        important_fields.append((col_name, weight, reason, non_empty, distinct_count, coverage_pct, sample_values))
    
    # SUPPORTING: IDs, numbers, dates, metadata
    elif any(x in col_lower for x in ['id', 'num', 'number', 'date', 'org', 'company', 
                                      'authority', 'source', 'reference', 'plan']):
        category = "SUPPORTING"
        weight = 1.0
        reason = "IDs, numbers, dates, or metadata"
        supporting_fields.append((col_name, weight, reason, non_empty, distinct_count, coverage_pct, sample_values))
    
    # LOW PRIORITY: Coordinates, flags, technical
    elif any(x in col_lower for x in ['x', 'y', 'min', 'max', 'extent', 'center', 
                                      'is', 'flag', 'convert', 'manual', 'active', 
                                      'valid', 'square', 'tz']):
        category = "LOW_PRIORITY"
        weight = 0.5
        reason = "Coordinates, flags, or technical fields"
        low_priority_fields.append((col_name, weight, reason, non_empty, distinct_count, coverage_pct, sample_values))
    
    else:
        # Unknown - default to supporting
        category = "SUPPORTING"
        weight = 1.0
        reason = "Unknown category - default to supporting"
        supporting_fields.append((col_name, weight, reason, non_empty, distinct_count, coverage_pct, sample_values))

# Print results
def print_category(title, fields_list, color="✓"):
    if not fields_list:
        return
    print(f"\n{title} (Weight: {fields_list[0][1] if fields_list else 'N/A'}x)")
    print("-" * 80)
    for col_name, weight, reason, non_empty, distinct_count, coverage_pct, samples in fields_list:
        print(f"  {color} {col_name:40s} | {non_empty:6,} values ({coverage_pct:5.1f}%) | {distinct_count:6,} distinct")
        print(f"    Reason: {reason}")
        if samples:
            sample_str = ", ".join([str(s)[:30] for s in samples[:2]])
            print(f"    Samples: {sample_str}")
        print()

print_category("🔴 CRITICAL FIELDS", critical_fields, "🔴")
print_category("🟠 IMPORTANT FIELDS", important_fields, "🟠")
print_category("🟡 SUPPORTING FIELDS", supporting_fields, "🟡")
print_category("⚪ LOW PRIORITY FIELDS", low_priority_fields, "⚪")

# Summary
print("=" * 80)
print("SUMMARY")
print("=" * 80)
print()
print(f"Total rows analyzed: {len(rows):,}")
print(f"Total fields: {len(rows[0]) if rows else 0}")
print()
print(f"  🔴 Critical: {len(critical_fields)}")
print(f"  🟠 Important: {len(important_fields)}")
print(f"  🟡 Supporting: {len(supporting_fields)}")
print(f"  ⚪ Low Priority: {len(low_priority_fields)}")
print()

# Key findings
print("KEY FINDINGS:")
print()
print("Fields with HIGH coverage (>80%):")
high_coverage = []
for category in [critical_fields, important_fields, supporting_fields, low_priority_fields]:
    for col_name, weight, reason, non_empty, distinct_count, coverage_pct, samples in category:
        if coverage_pct > 80:
            high_coverage.append((col_name, coverage_pct, category[0][1] if category else 0))
for col_name, pct, weight in sorted(high_coverage, key=lambda x: x[1], reverse=True)[:15]:
    print(f"  - {col_name:40s} ({pct:5.1f}% coverage, weight: {weight}x)")

print()
print("Fields with MEDIUM coverage (20-80%):")
medium_coverage = []
for category in [critical_fields, important_fields, supporting_fields, low_priority_fields]:
    for col_name, weight, reason, non_empty, distinct_count, coverage_pct, samples in category:
        if 20 <= coverage_pct <= 80:
            medium_coverage.append((col_name, coverage_pct, category[0][1] if category else 0))
for col_name, pct, weight in sorted(medium_coverage, key=lambda x: x[1], reverse=True)[:10]:
    print(f"  - {col_name:40s} ({pct:5.1f}% coverage, weight: {weight}x)")

print()
print("=" * 80)

