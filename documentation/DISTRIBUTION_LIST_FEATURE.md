# Distribution List Feature

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

The Distribution List feature expects the following API endpoints to be available:

#### List Management
- `GET /documents/{docId}/distribution-lists` - Retrieve all distribution lists for a document
- `POST /documents/{docId}/distribution-lists` - Create a new distribution list
- `DELETE /documents/{docId}/distribution-lists/{listId}` - Delete a distribution list

#### Recipient Management
- `GET /documents/{docId}/distribution-lists/{listId}/recipients` - Get all recipients in a list
- `POST /documents/{docId}/distribution-lists/{listId}/recipients` - Add a recipient to a list
- `DELETE /documents/{docId}/distribution-lists/{listId}/recipients/{recipientId}` - Remove a recipient from a list

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
3. **Create List** - Click on "Distribution list" tab, then click the "➕" button to create a new distribution list
   - Enter a list name
   - Click "Create" to save
4. **Add Recipients** - Select a list from the left panel
   - Enter recipient email in the input field
   - Click "Add" or press Enter to add the recipient
   - Recipients are displayed in a list below
5. **Send for Review** - With recipients added to the selected list
   - Click "📨 Send for Review & Comments"
   - The document is sent to all recipients in the list
   - A confirmation message appears on success
6. **Manage** - Users can:
   - Delete lists using the trash icon
   - Remove individual recipients using the "✕" button
   - Create multiple lists for different distribution groups

## User Interface Flow

1. **Access** - In the Document Flow section, click on the IDC (Integrated Design Control) step
2. **View Tabs** - You'll see "Comments" and "Distribution list" subtabs within the IDC section
3. **Create List** - Click on "Distribution list" tab, then click the "➕" button to create a new distribution list
   - Enter a list name
   - Click "Create" to save
4. **Add Recipients** - Select a list from the left panel
   - Enter recipient email in the input field
   - Click "Add" or press Enter to add the recipient
   - Recipients are displayed in a list below
5. **Send for Review** - With recipients added to the selected list
   - Click "📨 Send for Review & Comments"
   - The document is sent to all recipients in the list
   - A confirmation message appears on success
6. **Manage** - Users can:
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
2. Test creating lists with various names
3. Test adding/removing recipients
4. Test send for review functionality
5. Verify error handling with invalid emails
6. Test delete operations with confirmation dialogs
7. Verify proper error messages display for failed operations
8. Test loading states don't allow multiple concurrent operations

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
