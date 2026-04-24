#!/usr/bin/env python3
"""Process polling data and output as JSON for the dashboard."""

import csv
import json
from datetime import datetime, timedelta

def parse_date(date_str):
    """Parse date from YYYY-MM-DD format."""
    return datetime.strptime(date_str, "%Y-%m-%d")

def process_polling_data():
    """Read CSV and convert to JSON format for Observable Plot."""
    parties = ['Labour', 'Conservative', 'Reform', 'Liberal Democrats', 'Green', 'SNP', 'Plaid Cymru']
    data_points = []

    with open('ytod.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            date = row['Date']
            pollster = row['Pollster']

            for party in parties:
                if party in row and row[party]:
                    try:
                        value = float(row[party])
                        data_points.append({
                            'date': date,
                            'party': party,
                            'support': value,
                            'pollster': pollster
                        })
                    except ValueError:
                        pass

    return data_points

def calculate_averages(data_points, weeks=4):
    """Calculate average support per party over specified weeks."""
    cutoff = datetime.now() - timedelta(weeks=weeks)

    party_totals = {}
    party_counts = {}

    for point in data_points:
        point_date = parse_date(point['date'])
        if point_date >= cutoff:
            party = point['party']
            if party not in party_totals:
                party_totals[party] = 0
                party_counts[party] = 0
            party_totals[party] += point['support']
            party_counts[party] += 1

    averages = []
    for party in party_totals:
        if party_counts[party] > 0:
            averages.append({
                'party': party,
                'average': round(party_totals[party] / party_counts[party], 1)
            })

    return averages

if __name__ == '__main__':
    data = process_polling_data()
    averages_4w = calculate_averages(data, weeks=4)

    output = {
        'polling_data': data,
        'averages_4w': averages_4w,
        'generated': datetime.now().isoformat()
    }

    with open('data.json', 'w') as f:
        json.dump(output, f, indent=2)

    print(f"Processed {len(data)} data points")
    print(f"Parties in averages: {[a['party'] for a in averages_4w]}")
