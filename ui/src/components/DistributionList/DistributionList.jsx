import React from "react";
import PropTypes from "prop-types";
import "./DistributionList.css";

const DistributionList = ({ docId, apiBase, onClose }) => {
  const [lists, setLists] = React.useState([]);
  const [selectedListId, setSelectedListId] = React.useState(null);
  const [selectedPerson, setSelectedPerson] = React.useState("");
  const [isCreating, setIsCreating] = React.useState(false);
  const [persons, setPersons] = React.useState([]);
  const [roles, setRoles] = React.useState([]);
  const [recipients, setRecipients] = React.useState([]);
  const [newRecipient, setNewRecipient] = React.useState("");
  const [loading, setLoading] = React.useState(false);
  const [loadingPersons, setLoadingPersons] = React.useState(false);
  const [error, setError] = React.useState(null);
  const [success, setSuccess] = React.useState(null);
  const [sentLists, setSentLists] = React.useState(new Set());

  // Load distribution lists and persons on mount
  React.useEffect(() => {
    if (docId) {
      loadDistributionLists();
    }
    loadPersons();
  }, [docId]);

  // Load recipients when list is selected
  React.useEffect(() => {
    if (selectedListId) {
      loadRecipients();
    } else {
      setRecipients([]);
    }
  }, [selectedListId]);

  const loadPersons = async () => {
    try {
      setLoadingPersons(true);
      const [personResponse, rolesResponse] = await Promise.all([
        fetch(`${apiBase}/people/persons`),
        fetch(`${apiBase}/people/roles`)
      ]);
      
      if (personResponse.ok) {
        const personData = await personResponse.json();
        setPersons(Array.isArray(personData) ? personData : []);
      } else if (personResponse.status === 404) {
        setPersons([]);
      } else {
        console.error("Failed to load persons");
      }
      
      if (rolesResponse.ok) {
        const rolesData = await rolesResponse.json();
        setRoles(Array.isArray(rolesData) ? rolesData : []);
      } else if (rolesResponse.status === 404) {
        setRoles([]);
      } else {
        console.error("Failed to load roles");
      }
    } catch (err) {
      console.error("Error loading persons or roles:", err);
    } finally {
      setLoadingPersons(false);
    }
  };

  const getRoleForPerson = (personId) => {
    const personRole = roles.find((r) => r.person_id === personId);
    return personRole ? personRole.role_name : "N/A";
  };

  const loadDistributionLists = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch(`${apiBase}/documents/${docId}/distribution-lists`);
      if (response.ok) {
        const data = await response.json();
        setLists(data || []);
      } else if (response.status === 404) {
        setLists([]);
      } else {
        setError("Failed to load distribution lists");
      }
    } catch (err) {
      console.error("Error loading distribution lists:", err);
      setError("Failed to load distribution lists");
    } finally {
      setLoading(false);
    }
  };

  const loadRecipients = async () => {
    if (!selectedListId) return;
    try {
      setLoading(true);
      setError(null);
      const response = await fetch(
        `${apiBase}/documents/${docId}/distribution-lists/${selectedListId}/recipients`
      );
      if (response.ok) {
        const data = await response.json();
        setRecipients(data || []);
      } else {
        setError("Failed to load recipients");
      }
    } catch (err) {
      console.error("Error loading recipients:", err);
      setError("Failed to load recipients");
    } finally {
      setLoading(false);
    }
  };

  const handleCreateList = async () => {
    if (!selectedPerson) {
      setError("Please select a person");
      return;
    }

    const selectedPersonObj = persons.find((p) => p.person_id === parseInt(selectedPerson));
    const listName = selectedPersonObj?.person_name || selectedPerson;

    try {
      setLoading(true);
      setError(null);
      const response = await fetch(`${apiBase}/documents/${docId}/distribution-lists`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: listName }),
      });

      if (response.ok) {
        const newList = await response.json();
        
        // Automatically add the selected person as a recipient
        if (selectedPersonObj?.email) {
          await fetch(
            `${apiBase}/documents/${docId}/distribution-lists/${newList.dist_list_id}/recipients`,
            {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ 
                email: selectedPersonObj.email,
                person_name: selectedPersonObj.person_name
              }),
            }
          );
        }
        
        setLists([...lists, newList]);
        setSelectedListId(newList.dist_list_id);
        setSelectedPerson("");
        setSuccess("Distribution list created successfully");
        setTimeout(() => setSuccess(null), 3000);
      } else {
        const errorData = await response.json().catch(() => ({ detail: response.statusText }));
        const errorMsg = errorData?.detail || `Failed to create distribution list (${response.status})`;
        setError(errorMsg);
        console.error("Create list error:", response.status, errorData);
      }
    } catch (err) {
      console.error("Error creating distribution list:", err);
      setError(`Error: ${err.message || "Failed to create distribution list"}`);
    } finally {
      setLoading(false);
    }
  };

  const handleAddRecipient = async () => {
    if (!newRecipient.trim() || !selectedListId) {
      setError("Please select a person to add");
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const response = await fetch(
        `${apiBase}/documents/${docId}/distribution-lists/${selectedListId}/recipients`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ person_id: parseInt(newRecipient) }),
        }
      );

      if (response.ok) {
        const newRec = await response.json();
        setRecipients([...recipients, newRec]);
        setNewRecipient("");
        setSuccess("Recipient added successfully");
        setTimeout(() => setSuccess(null), 3000);
      } else {
        const errorData = await response.json().catch(() => ({ detail: response.statusText }));
        const errorMsg = errorData?.detail || `Failed to add recipient (${response.status})`;
        setError(errorMsg);
        console.error("Add recipient error:", response.status, errorData);
      }
    } catch (err) {
      console.error("Error adding recipient:", err);
      setError(`Error: ${err.message || "Failed to add recipient"}`);
    } finally {
      setLoading(false);
    }
  };

  const handleRemoveRecipient = async (recipientId) => {
    if (!selectedListId) return;

    try {
      setLoading(true);
      setError(null);
      const response = await fetch(
        `${apiBase}/documents/${docId}/distribution-lists/${selectedListId}/recipients/${recipientId}`,
        { method: "DELETE" }
      );

      if (response.ok) {
        setRecipients(recipients.filter((r) => r.id !== recipientId));
        setSuccess("Recipient removed successfully");
        setTimeout(() => setSuccess(null), 3000);
      } else {
        const errorData = await response.json().catch(() => ({ detail: response.statusText }));
        const errorMsg = errorData?.detail || `Failed to remove recipient (${response.status})`;
        setError(errorMsg);
        console.error("Remove recipient error:", response.status, errorData);
      }
    } catch (err) {
      console.error("Error removing recipient:", err);
      setError(`Error: ${err.message || "Failed to remove recipient"}`);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteList = async (listId) => {
    if (!window.confirm("Are you sure you want to delete this distribution list?")) return;

    try {
      setLoading(true);
      setError(null);
      const response = await fetch(`${apiBase}/documents/${docId}/distribution-lists/${listId}`, {
        method: "DELETE",
      });

      if (response.ok) {
        setLists(lists.filter((l) => l.id !== listId));
        if (selectedListId === listId) {
          setSelectedListId(null);
          setRecipients([]);
        }
        setSuccess("Distribution list deleted successfully");
        setTimeout(() => setSuccess(null), 3000);
      } else {
        const errorData = await response.json().catch(() => ({ detail: response.statusText }));
        const errorMsg = errorData?.detail || `Failed to delete distribution list (${response.status})`;
        setError(errorMsg);
        console.error("Delete list error:", response.status, errorData);
      }
    } catch (err) {
      console.error("Error deleting distribution list:", err);
      setError(`Error: ${err.message || "Failed to delete distribution list"}`);
    } finally {
      setLoading(false);
    }
  };

  const handleSendForReview = async () => {
    if (!selectedPerson) {
      setError("Please select a recipient to send");
      return;
    }

    const listId = parseInt(selectedPerson);

    try {
      setLoading(true);
      setError(null);
      const response = await fetch(
        `${apiBase}/documents/${docId}/distribution-lists/${listId}/send-for-review`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({}),
        }
      );

      if (response.ok) {
        console.log("Send successful, marking list as sent:", listId);
        const newSentLists = new Set(sentLists);
        newSentLists.add(listId);
        console.log("Updated sentLists:", newSentLists);
        setSentLists(newSentLists);
        setSuccess("Document sent for review and comments");
        setTimeout(() => setSuccess(null), 3000);
      } else {
        const errorData = await response.json().catch(() => ({ detail: response.statusText }));
        const errorMsg = errorData?.detail || `Failed to send for review (${response.status})`;
        setError(errorMsg);
        console.error("Send for review error:", response.status, errorData);
      }
    } catch (err) {
      console.error("Error sending for review:", err);
      setError(`Error: ${err.message || "Failed to send for review"}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="distribution-list-container">
    </div>
  );
};

DistributionList.propTypes = {
  docId: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  apiBase: PropTypes.string.isRequired,
  onClose: PropTypes.func,
};

export default DistributionList;
