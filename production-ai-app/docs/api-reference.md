# API Reference

## `GET /health`

Returns `{"status": "ok"}` when the service is up.

## `POST /query`

Request body:

```json
{
  "query": "string",
  "conversation_id": "optional string",
  "metadata": {}
}
```

Response body:

```json
{
  "answer": "string",
  "citations": [{"source": "...", "score": 0.0, "snippet": "..."}],
  "trace_id": "string"
}
```
