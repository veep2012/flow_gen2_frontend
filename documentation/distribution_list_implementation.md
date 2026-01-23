# Distribution List Feature Implementation

## Overview
The Distribution List feature allows users to create recipient lists within the Document Flow application and send documents for review and comments to multiple recipients at once.

## Architecture

### Frontend Components
- **Location**: `ui/src/components/DistributionList/DistributionList.jsx`
- **Integration**: Embedded in `IDCBehavior.jsx` as a subtab in the Document Flow workflow
- **Features**:
  - Create distribution lists by selecting a person from a dropdown
  - Add recipients to a list via email address
  - Remove individual recipients
  - Delete distribution lists
  - Send documents for review to all recipients in a list
  - Real-time error messages with API response details
  - Person selection dropdown populated from `/api/v1/people/persons` endpoint

### Backend API Endpoints
All endpoints follow the pattern: `POST /api/v1/documents/{doc_id}/distribution-lists/*`

#### Distribution List Management
1. **Create Distribution List**
   - `POST /documents/{doc_id}/distribution-lists`
   - Request: `{"name": "string"}`
   - Response: `DistributionListOut`

2. **Get All Distribution Lists for Document**
   - `GET /documents/{doc_id}/distribution-lists`
   - Response: `List[DistributionListOut]`

3. **Delete Distribution List**
   - `DELETE /documents/{doc_id}/distribution-lists/{list_id}`
   - Status: 204 No Content

#### Recipient Management
1. **Add Recipient to List**
   - `POST /documents/{doc_id}/distribution-lists/{list_id}/recipients`
   - Request: `{"email": "string", "person_name": "string|null"}`
   - Response: `RecipientOut`

2. **Get Recipients in List**
   - `GET /documents/{doc_id}/distribution-lists/{list_id}/recipients`
   - Response: `List[RecipientOut]`

3. **Remove Recipient from List**
   - `DELETE /documents/{doc_id}/distribution-lists/{list_id}/recipients/{recipient_id}`
   - Status: 204 No Content

#### Review Workflow
1. **Send Document for Review**
   - `POST /documents/{doc_id}/distribution-lists/{list_id}/send-for-review`
   - Request: `{"message": "string|null"}`
   - Response: `{"status": "success", "message": "string", "list_name": "string"}`

## Data Models

### Pydantic Schemas (api/schemas/documents.py)

```python
class DistributionListOut(BaseModel):
    dist_list_id: int
    list_name: str
    recipients: List[RecipientOut]

class DistributionListCreate(BaseModel):
    name: str

class RecipientOut(BaseModel):
    recipient_id: int
    email: str
    person_name: str | None

class RecipientCreate(BaseModel):
    email: str
    person_name: str | None

class SendForReviewRequest(BaseModel):
    message: str | None
```

### Storage
Currently uses in-memory storage (`_distribution_lists_store` dictionary in `api/routers/documents.py`):
```python
{
    doc_id: {
        list_id: {
            "name": "List Name",
            "recipients": [
                {"email": "user@example.com", "person_name": "John Doe"}
            ]
        }
    }
}
```

**Note**: This is a temporary solution. For production, extend the database schema to create a `DocDistributionList` table with proper relationships.

## Implementation Details

### Frontend Features
- **Person Selection**: Dropdown populated from `/api/v1/people/persons` sorted by person name
- **Error Handling**: Displays actual API error messages instead of generic messages
- **Loading States**: Shows loading spinner during API calls
- **Success Feedback**: Displays success messages with auto-dismiss after 3 seconds
- **Responsive UI**: Component fits seamlessly in the Distribution list tab

### Backend Features
- **Document Validation**: Verifies document exists before operations
- **Error Responses**: Returns detailed error messages with appropriate HTTP status codes
  - 404: Document or list not found
  - 400: Invalid request (e.g., no recipients when sending)
- **Automatic ID Management**: Generates unique list and recipient IDs
- **In-Memory State**: Lists and recipients exist for the session duration

## Files Modified/Created

### Backend
- `api/routers/documents.py`
  - Added imports for distribution list schemas
  - Added in-memory storage variables
  - Implemented 7 new endpoints for distribution list operations

- `api/schemas/documents.py`
  - Added `DistributionListOut`, `DistributionListCreate`
  - Added `RecipientOut`, `RecipientCreate`
  - Added `SendForReviewRequest`

### Frontend
- `ui/src/components/DistributionList/DistributionList.jsx`
  - Complete implementation of distribution list UI
  - State management for lists, recipients, loading states
  - Event handlers for all CRUD operations
  - Enhanced error handling with API response details

- `ui/src/components/DocRevStatusBehaviors/IDCBehavior.jsx`
  - Integration of DistributionList component
  - Added "Distribution list" subtab

- `ui/src/components/DistributionList/DistributionList.css`
  - Styling for component UI

- `ui/src/App.jsx`
  - Added `apiBase` prop passing to Behavior components

## Testing the Feature

### Prerequisites
1. Ensure the API server is running
2. Have a valid document ID
3. Have at least one person in the system (from `/api/v1/people/persons`)

### Manual Testing Steps
1. Open a document in the Document Flow
2. Navigate to the IDC (Integrated Design Control) tab
3. Click on the "Distribution list" subtab
4. Click the ➕ button to create a new distribution list
5. Select a person from the dropdown
6. Click "Create" to create the list
7. Click on the created list to select it
8. Add recipients by entering email addresses
9. Click "Send for Review & Comments" to send the document

### Expected Behavior
- All CRUD operations succeed with appropriate feedback messages
- Error messages display API details when operations fail
- Lists persist for the duration of the session
- Person dropdown loads persons from the database

## Future Enhancements

### Database Integration
Replace in-memory storage with proper database tables:
```sql
CREATE TABLE doc_distribution_lists (
    ddl_id INT PRIMARY KEY AUTO_INCREMENT,
    doc_id INT NOT NULL,
    list_name VARCHAR(255),
    created_at TIMESTAMPTZ,
    FOREIGN KEY (doc_id) REFERENCES docs(doc_id)
);

CREATE TABLE ddl_recipients (
    ddl_recipient_id INT PRIMARY KEY AUTO_INCREMENT,
    ddl_id INT NOT NULL,
    email VARCHAR(255),
    person_id INT,
    FOREIGN KEY (ddl_id) REFERENCES doc_distribution_lists(ddl_id),
    FOREIGN KEY (person_id) REFERENCES person(person_id)
);
```

### Email Integration
- Implement actual email sending on "Send for Review"
- Add email templates for review requests
- Track review status and comments from recipients

### Enhanced Features
- Archive old distribution lists
- Reuse distribution lists across documents
- Set review deadlines
- Track recipient responses
- Add comment threads on documents

## Error Handling

The feature includes comprehensive error handling:

### Frontend
- Validates user input before API calls
- Displays API error messages from backend
- Shows loading states to prevent double-submit
- Auto-clears success/error messages after 3 seconds

### Backend
- Validates document existence
- Validates list and recipient existence
- Returns appropriate HTTP status codes
- Provides detailed error messages in response body

## Performance Considerations

### Current (In-Memory)
- O(1) lookups for lists and recipients
- O(n) iteration when returning all lists/recipients
- Memory grows linearly with document count

### After Database Migration
- Consider indexing on `doc_id` and `ddl_id`
- Use pagination for large recipient lists
- Implement caching for frequently accessed lists

## Compatibility

- **Frontend**: React 18+ with hooks
- **Backend**: FastAPI with SQLAlchemy ORM
- **Database**: MySQL/MariaDB (when migrated to persistent storage)
- **Browser**: Modern browsers with Fetch API support
