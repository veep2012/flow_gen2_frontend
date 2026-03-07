-- 9. Security / Privileges
-- --------------------------------------------------------
REVOKE ALL ON SCHEMA core, ref, audit FROM PUBLIC;
REVOKE ALL ON SCHEMA core, ref, audit FROM app_user;
REVOKE ALL ON ALL TABLES IN SCHEMA core FROM PUBLIC;
REVOKE ALL ON ALL TABLES IN SCHEMA ref FROM PUBLIC;
REVOKE ALL ON ALL TABLES IN SCHEMA audit FROM PUBLIC;

GRANT USAGE ON SCHEMA workflow TO app_user;
REVOKE INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA workflow FROM app_user;
GRANT SELECT ON ALL TABLES IN SCHEMA workflow TO app_user;

GRANT EXECUTE ON FUNCTION workflow.create_document(
    VARCHAR, VARCHAR, SMALLINT, SMALLINT, SMALLINT, SMALLINT, SMALLINT,
    SMALLINT, SMALLINT, SMALLINT, SMALLINT, VARCHAR, SMALLINT,
    TIMESTAMPTZ, TIMESTAMPTZ, TIMESTAMPTZ, TIMESTAMPTZ, TIMESTAMPTZ, BOOLEAN
) TO app_user;

GRANT EXECUTE ON FUNCTION workflow.create_revision(
    INTEGER, SMALLINT, SMALLINT, SMALLINT, SMALLINT, VARCHAR,
    SMALLINT, TIMESTAMPTZ, TIMESTAMPTZ, TIMESTAMPTZ, TIMESTAMPTZ, TIMESTAMPTZ, BOOLEAN
) TO app_user;

GRANT EXECUTE ON FUNCTION workflow.transition_revision(INTEGER, TEXT) TO app_user;
GRANT EXECUTE ON FUNCTION workflow.cancel_revision(INTEGER) TO app_user;
GRANT EXECUTE ON FUNCTION workflow.update_document(INTEGER, JSONB) TO app_user;
GRANT EXECUTE ON FUNCTION workflow.update_revision(INTEGER, JSONB) TO app_user;
GRANT EXECUTE ON FUNCTION workflow.delete_document(INTEGER) TO app_user;
GRANT EXECUTE ON FUNCTION workflow.create_file(INTEGER, VARCHAR, TEXT, VARCHAR) TO app_user;
GRANT EXECUTE ON FUNCTION workflow.update_file(INTEGER, VARCHAR) TO app_user;
GRANT EXECUTE ON FUNCTION workflow.delete_file(INTEGER) TO app_user;
GRANT EXECUTE ON FUNCTION workflow.create_file_commented(INTEGER, INTEGER, TEXT, VARCHAR) TO app_user;
GRANT EXECUTE ON FUNCTION workflow.delete_file_commented(INTEGER) TO app_user;
GRANT EXECUTE ON FUNCTION workflow.create_written_comment(INTEGER, SMALLINT, TEXT) TO app_user;
GRANT EXECUTE ON FUNCTION workflow.delete_written_comment(INTEGER, SMALLINT) TO app_user;
GRANT EXECUTE ON FUNCTION workflow.update_written_comment(INTEGER, SMALLINT, TEXT) TO app_user;
GRANT EXECUTE ON FUNCTION workflow.create_notification(
    SMALLINT, VARCHAR, TEXT, INTEGER, INTEGER, SMALLINT[], SMALLINT[], VARCHAR, TEXT
) TO app_user;
GRANT EXECUTE ON FUNCTION workflow.replace_notification(
    SMALLINT, INTEGER, VARCHAR, TEXT, TEXT
) TO app_user;
GRANT EXECUTE ON FUNCTION workflow.delete_notification(
    SMALLINT, INTEGER, TEXT
) TO app_user;
GRANT EXECUTE ON FUNCTION workflow.mark_notification_read(
    INTEGER, SMALLINT
) TO app_user;
GRANT EXECUTE ON FUNCTION workflow.create_distribution_list(
    VARCHAR, INTEGER
) TO app_user;
GRANT EXECUTE ON FUNCTION workflow.delete_distribution_list(
    SMALLINT
) TO app_user;
GRANT EXECUTE ON FUNCTION workflow.add_distribution_list_member(
    SMALLINT, SMALLINT
) TO app_user;
GRANT EXECUTE ON FUNCTION workflow.remove_distribution_list_member(
    SMALLINT, SMALLINT
) TO app_user;
GRANT EXECUTE ON FUNCTION workflow.check_user_permission(
    BIGINT, TEXT, TEXT, BIGINT, BIGINT, BIGINT, BIGINT
) TO app_user;
GRANT EXECUTE ON FUNCTION workflow.check_lookup_scope_permission(
    BIGINT, TEXT, BIGINT, TEXT, TEXT
) TO app_user;
-- admin override only for db_admin
GRANT EXECUTE ON FUNCTION workflow.admin_override_transition(INTEGER, SMALLINT, TEXT) TO db_admin;

ALTER TABLE core.doc ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS p_core_doc_read ON core.doc;
CREATE POLICY p_core_doc_read ON core.doc
FOR SELECT
TO app_user
USING (
    workflow.check_user_permission(
        NULLIF(current_setting('app.user_id', true), '')::BIGINT,
        'doc',
        'read-only',
        NULL,
        project_id,
        area_id,
        unit_id
    )
);

ALTER TABLE core.doc_revision ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS p_core_doc_revision_read ON core.doc_revision;
CREATE POLICY p_core_doc_revision_read ON core.doc_revision
FOR SELECT
TO app_user
USING (
    workflow.check_user_permission(
        NULLIF(current_setting('app.user_id', true), '')::BIGINT,
        'doc_revision',
        'read-only',
        doc_id
    )
);

ALTER TABLE core.files ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS p_core_files_read ON core.files;
CREATE POLICY p_core_files_read ON core.files
FOR SELECT
TO app_user
USING (
    workflow.check_user_permission(
        NULLIF(current_setting('app.user_id', true), '')::BIGINT,
        'files',
        'read-only',
        (
            SELECT r.doc_id
            FROM core.doc_revision r
            WHERE r.rev_id = core.files.rev_id
            LIMIT 1
        )
    )
);

ALTER TABLE core.files_commented ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS p_core_files_commented_read ON core.files_commented;
CREATE POLICY p_core_files_commented_read ON core.files_commented
FOR SELECT
TO app_user
USING (
    workflow.check_user_permission(
        NULLIF(current_setting('app.user_id', true), '')::BIGINT,
        'files_commented',
        'read-only',
        (
            SELECT r.doc_id
            FROM core.files f
            JOIN core.doc_revision r ON r.rev_id = f.rev_id
            WHERE f.id = core.files_commented.file_id
            LIMIT 1
        )
    )
);

-- Indexes to support RLS policy correlated subqueries and joins
-- Improves performance of:
--   - doc_revision lookup via files.rev_id in p_core_files_read
--   - files lookup via files_commented.file_id in p_core_files_commented_read
CREATE INDEX IF NOT EXISTS idx_core_files_rev_id
    ON core.files (rev_id);

CREATE INDEX IF NOT EXISTS idx_core_files_commented_file_id
    ON core.files_commented (file_id);
