# New API Endpoints Documentation

## Cancel Revision

### Endpoint
```
PATCH /api/v1/documents/revisions/{rev_id}/cancel
```

### Description
Cancels a document revision by setting the `canceled_date` field to the current datetime.
Cancellation is allowed only when the current revision status is not final. If `canceled_date`
is already set, the endpoint is idempotent and returns the existing revision state.

### Path Parameters
- `rev_id` (integer, required): The ID of the revision to cancel

### Response
- **200 OK**: Returns the updated revision object with `canceled_date` set
- **404 Not Found**: Revision or document does not exist (or is voided)
- **409 Conflict**: Revision status does not allow cancellation

### Example Request
```bash
curl -X PATCH "http://localhost:5556/api/v1/documents/revisions/123/cancel"
```

### Example Response
```json
{
  "rev_id": 123,
  "doc_id": 456,
  "seq_num": 1,
  "rev_code_id": 1,
  "rev_code_name": "Initial",
  "canceled_date": "2024-01-15T20:45:00",
  ...
}
```

---

## Delete Document

### Endpoint
```
DELETE /api/v1/documents/{doc_id}
```

### Description
Deletes or voids a document based on its revision state:
- If the document has only one revision with a status equal to the start status, the document is permanently deleted (cascading to all revisions)
- Otherwise, the document's `voided` field is set to `true` (soft delete)

### Path Parameters
- `doc_id` (integer, required): The ID of the document to delete

### Response
- **200 OK**: Returns `{ "result": "deleted" }` or `{ "result": "voided" }`
- **404 Not Found**: Document with the specified ID does not exist

### Example Request
```bash
curl -X DELETE "http://localhost:5556/api/v1/documents/456"
```

### Behavior Examples

#### Example 1: Hard Delete
Document with one revision in start status:
- Document is permanently deleted
- Associated revisions are deleted (CASCADE)

#### Example 2: Soft Delete (Void)
Document with multiple revisions OR document with one revision not in start status:
- Document's `voided` field is set to `true`
- Document and revisions remain in database
- Document is marked as voided in list responses

---

## Related Model Changes

### Doc Model
Added field:
- `voided` (boolean): Indicates whether the document has been voided. Defaults to `false`.

### Database Schema
Added column to `doc` table:
```sql
voided BOOLEAN NOT NULL DEFAULT FALSE
```

### Migration Notes
If you need to migrate an existing database, apply the change with a default and backfill:
```sql
ALTER TABLE doc
    ADD COLUMN voided BOOLEAN NOT NULL DEFAULT FALSE;

UPDATE doc
SET voided = FALSE
WHERE voided IS NULL;

CREATE INDEX idx_doc_voided ON doc (voided);
```
The hard delete path relies on `doc_revision.doc_id` using `ON DELETE CASCADE` (already set in schema).

### DocOut Schema
Added field to response:
- `voided` (boolean): Whether the document is voided
