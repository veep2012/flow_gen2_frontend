# User Data in Database - Summary

## Document Control
- Status: Review
- Owner: Backend Team
- Reviewers: API maintainers
- Created: 2026-02-06
- Last Updated: 2026-02-06
- Version: v1.1

## Purpose
Clarify what user/person identity data exists in the database and how it is exposed through API responses.

## Scope
- In scope:
  - User, person, and role data relationships.
  - API endpoints that expose names and role metadata.
  - Expected usage patterns in the UI.
- Out of scope:
  - Authentication and authorization architecture.
  - Full schema reference for unrelated entities.

## Design / Behavior
The sections below explain entity relationships and how name data flows from database tables to API payloads and UI usage.

## YES, we have user names in the database! ✅

### Database Structure

The user/person data is stored across multiple related tables:

#### 1. **Person Table** (`flow.person`)
- `person_id` (PrimaryKey): Unique identifier
- `person_name` (String): **Full name of the person** ✅
- `photo_s3_uid` (Optional Text): Profile photo reference

#### 2. **User Table** (`flow.users`)
- `user_id` (PrimaryKey): Unique identifier
- `person_id` (ForeignKey): References Person table
- `user_acronym` (String): Short abbreviation (e.g., "KN" for "Konstantin Ni")
- `role_id` (ForeignKey): References Role table

#### 3. **Role Table** (`flow.roles`)
- `role_id` (PrimaryKey): Unique identifier
- `role_name` (String): Role name (e.g., "Designer", "Reviewer", etc.)

### Entity Relationships
```
User (user_id)
  ├─ person_id → Person (person_id)
  │  └─ person_name ✅ [FULL NAME]
  │  └─ photo_s3_uid
  └─ role_id → Role (role_id)
     └─ role_name
```

### API Endpoints to Get Users/People

#### 1. **List all persons** (with names)
```
GET /api/v1/people/persons
```
Returns: List of PersonOut objects with:
- `person_id`
- `person_name` ✅
- `photo_s3_uid`

Example Response:
```json
[
  {
    "person_id": 1,
    "person_name": "Konstantin Ni",
    "photo_s3_uid": null
  },
  {
    "person_id": 2,
    "person_name": "John Doe",
    "photo_s3_uid": "s3://bucket/photo.jpg"
  }
]
```

#### 2. **List all users** (with names and role)
```
GET /api/v1/people/users
```
Returns: List of UserOut objects with:
- `user_id`
- `person_id`
- `user_acronym`
- `role_id`
- `person_name` ✅ (joined from Person table)
- `role_name` (joined from Role table)

Example Response:
```json
[
  {
    "user_id": 1,
    "person_id": 1,
    "user_acronym": "KN",
    "role_id": 2,
    "person_name": "Konstantin Ni",
    "role_name": "Designer"
  },
  {
    "user_id": 2,
    "person_id": 2,
    "user_acronym": "JD",
    "role_id": 1,
    "person_name": "John Doe",
    "role_name": "Reviewer"
  }
]
```

### Schema Definitions

#### PersonOut Schema (`api/schemas/people.py`)
```python
class PersonOut:
    person_id: int
    person_name: str
    photo_s3_uid: Optional[str]
```

#### UserOut Schema (`api/schemas/people.py`)
```python
class UserOut:
    user_id: int
    person_id: int
    user_acronym: str
    role_id: int
    person_name: Optional[str]  # ✅ Added by join
    role_name: Optional[str]    # ✅ Added by join
```

### How User Names Are Used in the Application

1. **File Comments** - When a user uploads a commented file:
   - `FileCommented.user_id` stores which user made the comment
   - User name can be retrieved via the User→Person relationship

2. **Document Revisions** - Author and Originator tracking:
   - `DocRevision.rev_author_id` → Person table → `person_name`
   - `DocRevision.rev_originator_id` → Person table → `person_name`

3. **Permissions** - User access control:
   - `Permission.user_id` → User → Person → `person_name`

### Current Usage in UI

The application currently shows hardcoded user name:
```jsx
// In App.jsx, toolbar area
<div>Konstantin Ni</div>
<div>Designer</div>
```

This could be **dynamically replaced** with actual user data from the API endpoints above.

### Recommendation

To use dynamic user names in the UI:

1. Call the `/api/v1/people/users` endpoint on app initialization
2. Store the current user ID (from authentication/session)
3. Display the `person_name` from the UserOut response
4. Use user data in file comments, document tracking, etc.

### Database Sample Query

```sql
SELECT 
    u.user_id,
    u.user_acronym,
    u.role_id,
    p.person_id,
    p.person_name,
    r.role_name
FROM flow.users u
JOIN flow.person p ON u.person_id = p.person_id
JOIN flow.roles r ON u.role_id = r.role_id
ORDER BY u.user_acronym;
```

---

**Summary**: ✅ YES, we have `person_name` in the database for all users, accessible via:
- `/api/v1/people/persons` - Direct person names
- `/api/v1/people/users` - User info with person names and roles

## Edge Cases
- Users with missing `person` linkage must be treated as data integrity defects.
- Role records missing for a user should return deterministic API validation or fallback handling.
- UI flows must handle missing optional profile photo fields.

## References
- `api/schemas/people.py`
- `api/routers/people.py`
- `documentation/api_interfaces.md`
