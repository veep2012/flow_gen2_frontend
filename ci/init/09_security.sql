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
GRANT EXECUTE ON FUNCTION workflow.create_notification(
    SMALLINT, VARCHAR, TEXT, INTEGER, INTEGER, SMALLINT[], SMALLINT[], VARCHAR, TEXT, INTEGER
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
    VARCHAR
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

-- admin override only for db_admin
GRANT EXECUTE ON FUNCTION workflow.admin_override_transition(INTEGER, SMALLINT, TEXT) TO db_admin;
