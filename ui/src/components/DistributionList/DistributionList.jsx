import React from "react";
import PropTypes from "prop-types";
import "./DistributionList.css";
import { fetchWithAuthHandling, isAuthResponseError } from "../../utils/authFetch";

const PURPOSE_OPTIONS = ["For Information", "For Review", "For Approval", "For Action"];

const DistributionList = ({ docId, apiBase, onAuthFailure }) => {
  const [persons, setPersons] = React.useState([]);
  const [roles, setRoles] = React.useState([]);
  const [loadingPersons, setLoadingPersons] = React.useState(false);
  const [savingEntry, setSavingEntry] = React.useState(false);
  const [saveError, setSaveError] = React.useState("");
  const [isAddModalOpen, setIsAddModalOpen] = React.useState(false);
  const [modalPersonId, setModalPersonId] = React.useState("");
  const [modalPurpose, setModalPurpose] = React.useState("");

  const loadPersons = React.useCallback(async () => {
    try {
      setLoadingPersons(true);
      const [personResponse, rolesResponse] = await Promise.all([
        fetchWithAuthHandling(`${apiBase}/people/persons`, {}, { onAuthFailure }),
        fetchWithAuthHandling(`${apiBase}/people/roles`, {}, { onAuthFailure }),
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
      if (isAuthResponseError(err)) {
        return;
      }
      console.error("Error loading persons or roles:", err);
    } finally {
      setLoadingPersons(false);
    }
  }, [apiBase, onAuthFailure]);

  const getRoleForPerson = (personId) => {
    if (!personId) return "-";
    const personRole = roles.find((r) => String(r.person_id) === String(personId));
    return personRole ? personRole.role_name : "N/A";
  };

  // Load persons on mount
  React.useEffect(() => {
    loadPersons();
  }, [loadPersons]);

  const closeAddModal = React.useCallback(() => {
    setIsAddModalOpen(false);
    setModalPersonId("");
    setModalPurpose("");
    setSaveError("");
  }, []);

  const handleSaveDistributionEntry = React.useCallback(async () => {
    if (!docId) {
      setSaveError("Document ID is required to add a distribution entry.");
      return;
    }

    if (!modalPersonId || !modalPurpose) {
      setSaveError("Please fill in all required fields.");
      return;
    }

    try {
      setSavingEntry(true);
      setSaveError("");

      const response = await fetchWithAuthHandling(
        `${apiBase}/documents/${docId}/distribution-lists`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            person_id: parseInt(modalPersonId, 10),
            purpose: modalPurpose,
          }),
        },
        { onAuthFailure },
      );

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(errorText || `Failed to save distribution entry (${response.status})`);
      }

      closeAddModal();
    } catch (err) {
      if (isAuthResponseError(err)) {
        return;
      }
      console.error("Error saving distribution entry:", err);
      setSaveError(err.message || "Failed to save distribution entry");
    } finally {
      setSavingEntry(false);
    }
  }, [apiBase, closeAddModal, docId, modalPersonId, modalPurpose, onAuthFailure]);

  return (
    <div className="distribution-list-container" data-doc-id={docId ?? ""}>
      <div className="distribution-list-header">
        <h3>Distribution List</h3>
        <div className="button-group">
          <button
            type="button"
            className="btn-add"
            onClick={() => {
              setSaveError("");
              setIsAddModalOpen(true);
            }}
          >
            + Add
          </button>
        </div>
      </div>
      <div className="empty-state">
        No documents sent yet. Add recipients and click &quot;Send&quot; to start the distribution.
      </div>

      {isAddModalOpen ? (
        <div className="distribution-modal-overlay" role="dialog" aria-modal="true">
          <div className="distribution-modal">
            <div className="distribution-modal__header">
              <div className="distribution-modal__title">
                <span className="distribution-modal__icon">＋</span>
                <div>
                  <div className="distribution-modal__headline">Add Distribution Entry</div>
                  <div className="distribution-modal__subhead">
                    Fill in the details to add a new distribution entry
                  </div>
                </div>
              </div>
              <button
                type="button"
                className="distribution-modal__close"
                onClick={closeAddModal}
                aria-label="Close"
              >
                ×
              </button>
            </div>
            <div className="distribution-modal__body">
              <label className="distribution-modal__label" htmlFor="distribution-name">
                Name *
              </label>
              <select
                id="distribution-name"
                className="distribution-modal__select"
                value={modalPersonId}
                onChange={(e) => setModalPersonId(e.target.value)}
                disabled={loadingPersons}
              >
                <option value="" disabled>
                  Select person...
                </option>
                {persons.map((person) => (
                  <option key={person.person_id} value={person.person_id}>
                    {person.person_name}
                  </option>
                ))}
              </select>

              <label className="distribution-modal__label" htmlFor="distribution-role">
                Role
              </label>
              <input
                id="distribution-role"
                className="distribution-modal__input"
                value={modalPersonId ? getRoleForPerson(parseInt(modalPersonId, 10)) : "-"}
                readOnly
              />

              <label className="distribution-modal__label" htmlFor="distribution-purpose">
                Purpose *
              </label>
              <select
                id="distribution-purpose"
                className="distribution-modal__select"
                value={modalPurpose}
                onChange={(e) => setModalPurpose(e.target.value)}
              >
                <option value="" disabled>
                  Select purpose...
                </option>
                {PURPOSE_OPTIONS.map((purpose) => (
                  <option key={purpose} value={purpose}>
                    {purpose}
                  </option>
                ))}
              </select>
            </div>
            <div className="distribution-modal__footer">
              <span className="distribution-modal__required">* Required fields</span>
              <div className="distribution-modal__actions">
                <button type="button" className="distribution-modal__btn" onClick={closeAddModal}>
                  Cancel
                </button>
                <button
                  type="button"
                  className="distribution-modal__btn distribution-modal__btn--primary"
                  onClick={handleSaveDistributionEntry}
                  disabled={savingEntry}
                >
                  {savingEntry ? "Saving..." : "Save"}
                </button>
              </div>
            </div>
            {saveError ? <div className="alert alert-error">{saveError}</div> : null}
          </div>
        </div>
      ) : null}
    </div>
  );
};

DistributionList.propTypes = {
  docId: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  apiBase: PropTypes.string.isRequired,
  onAuthFailure: PropTypes.func,
};

export default DistributionList;
