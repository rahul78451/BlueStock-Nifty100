"""
ETL Script 1 — Extract from SQL Dump
======================================
Parses INSERT INTO statements from the provided .sql dump file
and extracts all 7 tables into clean CSV files in data/raw/.

Usage: python etl/01_extract_from_mysql.py --input path/to/scriptticker.sql
"""
import re
import csv
import os
import sys
import argparse
from pathlib import Path


# Tables to extract from the SQL dump
TABLES = [
    'companies', 'analysis', 'balancesheet',
    'profitandloss', 'cashflow', 'prosandcons', 'documents'
]


def parse_sql_dump(sql_path: str) -> dict:
    """
    Parse a MySQL/MariaDB SQL dump and extract data from INSERT statements.
    Returns a dict of {table_name: (columns, rows)}.
    """
    print(f"📂 Reading SQL dump: {sql_path}")
    with open(sql_path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()

    results = {}

    for table in TABLES:
        print(f"\n🔍 Extracting table: {table}")

        # Find CREATE TABLE to get column names
        create_pattern = rf"CREATE\s+TABLE\s+[`\"']?{table}[`\"']?\s*\((.*?)\)\s*(?:ENGINE|;)"
        create_match = re.search(create_pattern, content, re.DOTALL | re.IGNORECASE)

        columns = []
        if create_match:
            create_body = create_match.group(1)
            col_pattern = r'[`\""](\w+)[`\""]'
            for line in create_body.split('\n'):
                line = line.strip()
                if line.startswith('PRIMARY') or line.startswith('KEY') or \
                   line.startswith('INDEX') or line.startswith('UNIQUE') or \
                   line.startswith('CONSTRAINT') or line.startswith(')'):
                    continue
                col_match = re.match(col_pattern, line)
                if col_match:
                    columns.append(col_match.group(1))

        # Find INSERT INTO statements
        insert_pattern = rf"INSERT\s+INTO\s+[`\"']?{table}[`\"']?\s*(?:\(([^)]+)\))?\s*VALUES\s*(.*?);\s*$"
        insert_matches = re.finditer(insert_pattern, content, re.MULTILINE | re.DOTALL | re.IGNORECASE)

        rows = []
        for match in insert_matches:
            col_list = match.group(1)
            values_str = match.group(2)

            # If column list is in the INSERT statement, use it
            if col_list and not columns:
                columns = [c.strip().strip('`"\'') for c in col_list.split(',')]

            # Parse individual value tuples
            # Handle: (val1, val2, 'str with (parens)', NULL), (...)
            tuple_pattern = r"\(([^)]*(?:'[^']*'[^)]*)*)\)"
            for tuple_match in re.finditer(tuple_pattern, values_str):
                raw = tuple_match.group(1)
                # Parse values handling quoted strings
                values = parse_values(raw)
                rows.append(values)

        results[table] = (columns, rows)
        print(f"  ✓ {len(rows)} rows, {len(columns)} columns: {columns[:5]}{'...' if len(columns) > 5 else ''}")

    return results


def parse_values(raw: str) -> list:
    """Parse a comma-separated value string, handling quoted strings and NULLs."""
    values = []
    current = ''
    in_quotes = False
    quote_char = None
    i = 0

    while i < len(raw):
        ch = raw[i]

        if in_quotes:
            if ch == '\\' and i + 1 < len(raw):
                current += raw[i + 1]
                i += 2
                continue
            elif ch == quote_char:
                in_quotes = False
                current += ch
            else:
                current += ch
        else:
            if ch in ("'", '"'):
                in_quotes = True
                quote_char = ch
                current += ch
            elif ch == ',':
                values.append(clean_value(current.strip()))
                current = ''
            else:
                current += ch
        i += 1

    if current.strip():
        values.append(clean_value(current.strip()))

    return values


def clean_value(val: str) -> str:
    """Clean a parsed SQL value."""
    if val.upper() == 'NULL':
        return ''
    # Remove surrounding quotes
    if (val.startswith("'") and val.endswith("'")) or \
       (val.startswith('"') and val.endswith('"')):
        val = val[1:-1]
    # Unescape
    val = val.replace("\\'", "'").replace('\\"', '"')
    val = val.replace('\\n', '\n').replace('\\r', '').replace('\\t', '\t')
    return val.strip()


def save_to_csv(output_dir: str, table_data: dict):
    """Save extracted data as CSV files."""
    os.makedirs(output_dir, exist_ok=True)

    for table, (columns, rows) in table_data.items():
        filepath = os.path.join(output_dir, f'{table}.csv')
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if columns:
                writer.writerow(columns)
            writer.writerows(rows)
        print(f"  💾 Saved {filepath} ({len(rows)} rows)")


def main():
    parser = argparse.ArgumentParser(description='Extract tables from SQL dump to CSV')
    parser.add_argument('--input', '-i', required=True, help='Path to SQL dump file')
    parser.add_argument('--output', '-o', default='data/raw', help='Output directory for CSVs')
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"❌ File not found: {args.input}")
        sys.exit(1)

    table_data = parse_sql_dump(args.input)
    save_to_csv(args.output, table_data)

    print(f"\n✅ Extraction complete! {sum(len(v[1]) for v in table_data.values())} total rows across {len(table_data)} tables.")


if __name__ == '__main__':
    main()
