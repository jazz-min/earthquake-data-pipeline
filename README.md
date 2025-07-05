
---

## 🔁 Pipeline Flow

1. **Extract**: Airflow fetches real-time earthquake data from the USGS API.
2. **Load**: Data is written to a raw table in PostgreSQL.
3. **Transform**: dbt models transform and enrich the raw data.
4. **Visualize**: Superset dashboards present trends, severity, and geospatial analysis.

---

## ⚙️ How to Run Locally (with Docker Compose)

> *Coming soon...*

---

## 📈 Metrics Visualized

- Map of global earthquake locations
- Daily earthquake counts
- Distribution of magnitudes
- Top 10 strongest earthquakes
- Filters by region, depth, and date range

---

## 🧪 Future Improvements

- Add Slack alerts for earthquakes over a certain magnitude
- Join with population or geographic risk data
- Integrate with cloud DBs (e.g., BigQuery or Snowflake)

---

## 🧠 Learnings

> Summarize what you learned: Airflow orchestration, dbt modeling, API ingestion, Superset charts, etc.

---

## 📄 License

MIT License – feel free to use and adapt this project.

---

## ✨ Credits

Data source: [USGS Earthquake Hazards Program](https://earthquake.usgs.gov/)
