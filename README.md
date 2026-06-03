# PharmaOps Monitor

> AI-powered pharma manufacturing observability platform on Splunk

## Problem
India exports $25B pharma annually. Batch failures cost Rs 50-150 lakhs each. FDA issues 500+ warning letters/year for inadequate monitoring. No real-time AI view exists for plant managers.

## Solution
PharmaOps Monitor ingests pharma manufacturing data into Splunk and uses AI anomaly detection to catch GMP violations in real-time.

## Features
- AI temperature deviation detection (Median Absolute Deviation)
- Moisture anomaly monitoring
- Batch pass/fail QC dashboard
- Equipment downtime analytics
- Natural language queries via Splunk MCP Server

## Setup
1. Install Splunk Enterprise 10.4.0
2. Install Splunk AI Toolkit from Splunkbase
3. Run: python3 generate_pharma_data.py
4. Upload CSVs to index: pharma_manufacturing
5. Open PharmaOps Monitor dashboard

## Data
- temperature_logs.csv: 1800 rows
- moisture_logs.csv: 600 rows
- batch_summary.csv: 50 rows
- equipment_downtime.csv: 23 rows

## AI Query
```
index=pharma_manufacturing source="temperature_logs.csv"
| eval _time=strptime(timestamp, "%Y-%m-%dT%H:%M:%S")
| timechart span=1h avg(temperature_C) as temperature
| streamstats window=50 current=true median(temperature) as median
| eval absDev=(abs(temperature-median))
| streamstats window=50 current=true median(absDev) as medianAbsDev
| eval lowerBound=(median-medianAbsDev*3), upperBound=(median+medianAbsDev*3)
| eval isOutlier=if(temperature < lowerBound OR temperature > upperBound, 1, 0)
```

## Track
Observability - Splunk Agentic Ops Hackathon 2026

## Author
Prakash Raj K, Associate Professor, Sri Balaji Vidyapeeth, Puducherry, India

## License
MIT
