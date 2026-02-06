# Distribution List Feature

## Document Control
- Status: Approved
- Owner: Backend and Frontend Team
- Reviewers: API and UI maintainers
- Created: 2026-02-06
- Last Updated: 2026-02-06
- Version: v1.1

## Purpose
Describe the distribution list user feature, UI integration points, and backend API behaviors used to send documents for review.

## Scope
- In scope:
  - IDC distribution list UI behavior.
  - Distribution list and recipient API usage.
  - Send-for-review interaction and validation behavior.
- Out of scope:
  - Persistent distribution list administration workflows.
  - External email delivery implementation.

## Design / Behavior
The sections below define the user path, component interactions, API contracts, and operational behavior for distribution list usage in the IDC workflow.

## Overview

The Distribution List feature has been added to the Flow document management application within the **Document Flow IDC (Integrated Design Control) tab**. This feature allows users to:

1. **Create Distribution Lists** - Organize recipients into named lists
2. **Manage Recipients** - Add and remove email recipients to/from distribution lists
3. **Send for Review & Comments** - Send documents to multiple recipients for review and collect feedback

## Location

The Distribution List functionality is integrated into the **IDC (Integrated Design Control)** step in the Document Flow section:

1. Navigate to a document in the Document Flow panel
2. Click on the **"IDC"** step to expand it
3. Select the **"Distribution list"** subtab within the IDC section
4. Manage distribution lists and recipients there

## Implementation

### New Components

#### 1. **DistributionList Component** (`ui/src/components/DistributionList/`)

A full-featured React component that provides the complete distribution list interface.

**Features:**
- Create new distribution lists
- View all available lists
- Add/remove recipients from lists
- Send documents for review and comments
- Real-time feedback with success/error messages
- Loading states during API operations

**Props:**
- `docId`: The document ID (string or number) - required for API calls
- `apiBase`: The API base URL (string) - defaults to environment configuration
- `onClose`: Optional callback when closing the component

**Usage:**
```jsx
<DistributionList 
  docId={selectedDoc?.doc_id} 
  apiBase={apiBase}
/>
```

### Integration Points

#### 1. **IDCBehavior Component** (`ui/src/components/DocRevStatusBehaviors/IDCBehavior.jsx`)

Updated to include the DistributionList component as a subtab:
- Imported the `DistributionList` component
- Added "Distribution list" as a subtab in the IDC section
- Passes `docId` and `apiBase` props to the DistributionList component
- Renders the component when "Distribution list" tab is selected

#### 2. **App.jsx Updates**

- Passes `apiBase` prop to the Behavior component (which includes IDCBehavior)
- Removed standalone "Distribution List" tab from the main detail panel
- Distribution List functionality is now exclusively in the Document Flow IDC section

#### 3. **DetailPanel.jsx Updates**

- Cleaned up to remove the Distribution List tab (not used in main application)
- Maintains original tabs: Revisions, TAGs, References, Plan, Information

### API Endpoints

The Distribution List feature expects the following API endpoints to be available (lists/recipients are read-only via API):

#### List Management
- `GET /documents/{docId}/distribution-lists` - Retrieve all distribution lists for a document

#### Recipient Management
- `GET /documents/{docId}/distribution-lists/{listId}/recipients` - Get all recipients in a list

#### Send for Review
- `POST /documents/{docId}/distribution-lists/{listId}/send-for-review` - Send document for review

**Example Request Body for Send for Review:**
```json
{
  "recipients": ["user1@example.com", "user2@example.com"]
}
```

### Styling

The component uses CSS custom properties (CSS variables) for theming and is fully styled in `DistributionList.css`. The design includes:

- Responsive layout with proper spacing
- Status alerts for success and error messages
- Interactive buttons with hover states
- Empty states with helpful messaging
- Scrollable lists for better UX
- Loading indicators during API calls

### User Interface Flow

1. **Access** - In the Document Flow section, click on the IDC (Integrated Design Control) step
2. **View Tabs** - You'll see "Comments" and "Distribution list" subtabs within the IDC section
3. **Select List** - Choose a list from the left panel (lists are read-only via API)
4. **Review Recipients** - Recipients are displayed in a list below (read-only)
5. **Send for Review** - With a list selected
   - Click "📨 Send for Review & Comments"
   - The document is sent to all recipients in the list
   - A confirmation message appears on success
6. **Manage** - List and recipient management is handled outside the API (admin/seed workflows)
   - Delete lists using the trash icon
   - Remove individual recipients using the "✕" button
   - Create multiple lists for different distribution groups

### Error Handling

The component includes comprehensive error handling:

- API errors are caught and displayed to the user
- Loading states prevent multiple simultaneous requests
- Form validation ensures required fields are filled
- Confirmation dialogs for destructive actions (delete)
- Helpful error messages guide users to correct issues

### State Management

Uses React hooks for state management:
- `lists` - Array of distribution lists
- `selectedListId` - Currently selected list ID
- `recipients` - Recipients in the selected list
- `loading` - Loading state for API operations
- `error` - Error messages to display
- `success` - Success messages to display
- `isCreating` - Flag to show/hide create list form
- `newListName` - Input value for new list name
- `newRecipient` - Input value for new recipient email

## Browser Compatibility

- Modern browsers with ES6+ support
- CSS Grid and Flexbox support
- Fetch API for HTTP requests
- React 16.8+ (uses hooks)

## Security Considerations

- Email addresses are not validated on the client (rely on backend validation)
- API calls use standard fetch with application/json content type
- No sensitive data is stored in component state beyond what's necessary

## Future Enhancements

Possible improvements for future versions:

1. **Batch Operations** - Add/remove multiple recipients at once
2. **Import/Export** - CSV import for recipient lists
3. **Templates** - Save and reuse recipient list templates
4. **Notifications** - Track when recipients view/comment on documents
5. **Search** - Filter recipients and lists
6. **Permissions** - Different access levels for distribution lists
7. **History** - Track document distribution history
8. **Reminders** - Auto-send reminders to recipients who haven't reviewed

## Testing

When testing the Distribution List feature:

1. Ensure API endpoints are correctly implemented on the backend
2. Test loading lists and recipients (read-only)
3. Test send for review functionality
4. Verify error handling with invalid recipients list payloads
5. Verify proper error messages display for failed operations
6. Test loading states don't allow multiple concurrent operations

## Troubleshooting

### Distribution lists not loading
- Check browser console for API errors
- Verify API base URL is correct
- Ensure API endpoints are available and responding

### Send for review fails
- Verify recipient email addresses are valid
- Check API endpoint is implemented on backend
- Review network requests in browser DevTools

### Styling issues
- Ensure CSS variables are defined in the application's theme
- Check that DistributionList.css is properly imported
- Verify no CSS conflicts with existing styles

## Edge Cases
- Distribution list API endpoint is reachable but returns an empty list.
- A recipient list contains invalid entries and the API rejects send-for-review.
- User triggers repeated sends while request state is still loading.

## References
- `documentation/distribution_list_implementation.md`
- `api/routers/documents.py`
- `ui/src/components/DistributionList/`
