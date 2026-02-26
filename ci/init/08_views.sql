-- 8. Read-Only Views (schema: workflow)
-- --------------------------------------------------------
DO $$
DECLARE
    v_view RECORD;
BEGIN
    -- Remove legacy non-prefixed workflow views so only v_* names remain canonical.
    FOR v_view IN
        SELECT schemaname, viewname
        FROM pg_catalog.pg_views
        WHERE schemaname = 'workflow'
          AND viewname NOT LIKE 'v\_%' ESCAPE '\'
    LOOP
        EXECUTE format('DROP VIEW IF EXISTS %I.%I CASCADE', v_view.schemaname, v_view.viewname);
    END LOOP;
END;
$$;

CREATE OR REPLACE VIEW workflow.v_areas AS
SELECT * FROM ref.areas;

CREATE OR REPLACE VIEW workflow.v_disciplines AS SELECT * FROM ref.disciplines;
CREATE OR REPLACE VIEW workflow.v_projects AS
SELECT *
FROM ref.projects p
WHERE workflow.check_lookup_scope_permission(
    NULLIF(current_setting('app.user_id', true), '')::BIGINT,
    'PROJECT',
    p.project_id
);
CREATE OR REPLACE VIEW workflow.v_units AS
SELECT * FROM ref.units;

CREATE OR REPLACE VIEW workflow.v_jobpacks AS SELECT * FROM ref.jobpacks;
CREATE OR REPLACE VIEW workflow.v_roles AS SELECT * FROM ref.roles;
CREATE OR REPLACE VIEW workflow.v_user_roles AS SELECT * FROM ref.user_roles;
CREATE OR REPLACE VIEW workflow.v_role_permissions AS SELECT * FROM ref.role_permissions;
CREATE OR REPLACE VIEW workflow.v_role_scopes AS SELECT * FROM ref.role_scopes;
CREATE OR REPLACE VIEW workflow.v_doc_rev_milestones AS SELECT * FROM ref.doc_rev_milestones;
CREATE OR REPLACE VIEW workflow.v_revision_overview AS SELECT * FROM ref.revision_overview;
CREATE OR REPLACE VIEW workflow.v_doc_rev_statuses AS SELECT * FROM ref.doc_rev_statuses;
CREATE OR REPLACE VIEW workflow.v_doc_rev_status_ui_behaviors AS SELECT * FROM ref.doc_rev_status_ui_behaviors;
CREATE OR REPLACE VIEW workflow.v_files_accepted AS SELECT * FROM ref.files_accepted;
CREATE OR REPLACE VIEW workflow.v_leased_doc_nums AS SELECT * FROM ref.leased_doc_nums;
CREATE OR REPLACE VIEW workflow.v_sql_queries AS SELECT * FROM ref.sql_queries;
CREATE OR REPLACE VIEW workflow.v_instance_parameters AS SELECT * FROM ref.instance_parameters;
CREATE OR REPLACE VIEW workflow.v_person_duty AS SELECT * FROM ref.person_duty;
CREATE OR REPLACE VIEW workflow.v_person AS SELECT * FROM ref.person;
CREATE OR REPLACE VIEW workflow.v_users AS SELECT * FROM ref.users;
CREATE OR REPLACE VIEW workflow.v_doc_types AS SELECT * FROM ref.doc_types;
CREATE OR REPLACE VIEW workflow.v_distribution_list AS SELECT * FROM core.distribution_list;
CREATE OR REPLACE VIEW workflow.v_distribution_list_content AS SELECT * FROM core.distribution_list_content;
CREATE OR REPLACE VIEW workflow.v_permissions AS SELECT * FROM ref.permissions;
CREATE OR REPLACE VIEW workflow.v_doc_cache AS SELECT * FROM ref.doc_cache;

CREATE OR REPLACE VIEW workflow.v_written_comments AS SELECT * FROM core.written_comments;
CREATE OR REPLACE VIEW workflow.v_notifications AS SELECT * FROM core.notifications;
CREATE OR REPLACE VIEW workflow.v_notification_targets AS SELECT * FROM core.notification_targets;
CREATE OR REPLACE VIEW workflow.v_notification_recipients AS SELECT * FROM core.notification_recipients;

CREATE OR REPLACE VIEW workflow.v_notification_inbox AS
SELECT
    nr.recipient_user_id,
    nr.delivered_at,
    nr.read_at,
    n.notification_id,
    n.sender_user_id,
    n.event_type,
    n.title,
    n.body,
    n.remark,
    n.rev_id,
    n.commented_file_id,
    n.created_at,
    n.dropped_at,
    n.dropped_by_user_id,
    n.superseded_by_notification_id
FROM core.notification_recipients nr
JOIN core.notifications n ON n.notification_id = nr.notification_id;

CREATE OR REPLACE VIEW workflow.v_doc_revision_history AS SELECT * FROM audit.doc_revision_history;
CREATE OR REPLACE VIEW workflow.v_doc_revision_history_view AS
SELECT
    rev_id,
    rev_code_id,
    rev_date,
    rev_author_id,
    rev_originator_id,
    as_built,
    superseded,
    transmital_current_revision,
    milestone_id,
    planned_start_date,
    planned_finish_date,
    actual_start_date,
    actual_finish_date,
    canceled_date,
    rev_status_id,
    doc_id,
    seq_num,
    'HISTORY'::varchar(10) AS source_type
FROM audit.doc_revision_history;

CREATE OR REPLACE VIEW workflow.v_documents AS
SELECT
    d.*, s.rev_status_name AS current_status_name
FROM core.doc d
LEFT JOIN core.doc_revision r ON r.rev_id = d.rev_current_id
LEFT JOIN ref.doc_rev_statuses s ON s.rev_status_id = r.rev_status_id
WHERE workflow.check_user_permission(
    NULLIF(current_setting('app.user_id', true), '')::BIGINT,
    'doc',
    'read-only',
    d.doc_id,
    d.project_id,
    d.area_id,
    d.unit_id
);

CREATE OR REPLACE VIEW workflow.v_document_revisions AS
SELECT
    r.*, s.rev_status_name
FROM core.doc_revision r
JOIN ref.doc_rev_statuses s ON s.rev_status_id = r.rev_status_id
WHERE workflow.check_user_permission(
    NULLIF(current_setting('app.user_id', true), '')::BIGINT,
    'doc_revision',
    'read-only',
    r.doc_id
);

CREATE OR REPLACE VIEW workflow.v_files AS
SELECT
    f.*, r.doc_id
FROM core.files f
JOIN core.doc_revision r ON r.rev_id = f.rev_id
WHERE workflow.check_user_permission(
    NULLIF(current_setting('app.user_id', true), '')::BIGINT,
    'files',
    'read-only',
    r.doc_id
);

CREATE OR REPLACE VIEW workflow.v_files_commented AS
SELECT
    fc.*,
    f.rev_id,
    r.doc_id
FROM core.files_commented fc
JOIN core.files f ON f.id = fc.file_id
JOIN core.doc_revision r ON r.rev_id = f.rev_id
WHERE workflow.check_user_permission(
    NULLIF(current_setting('app.user_id', true), '')::BIGINT,
    'files_commented',
    'read-only',
    r.doc_id
);

-- --------------------------------------------------------
