# Project wide logging architecture
I want the logs to cover 100% project coverage. It must be Self-initializing logging pipeline (App ensures Glue schema → writes Parquet → Athena-ready)

```bash
FastAPI
   ↓
Structured logs (buffer)
   ↓
Startup → ensure Glue table
   ↓
Batch → Parquet file
   ↓
Upload → S3 (partitioned)
   ↓
Register partition / repair
   ↓
Athena query
```
