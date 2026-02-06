-- 8. Read-Only Views (schema: workflow)
-- --------------------------------------------------------
CREATE OR REPLACE VIEW workflow.areas AS SELECT * FROM ref.areas;
CREATE OR REPLACE VIEW workflow.disciplines AS SELECT * FROM ref.disciplines;
CREATE OR REPLACE VIEW workflow.projects AS SELECT * FROM ref.projects;
CREATE OR REPLACE VIEW workflow.units AS SELECT * FROM ref.units;
CREATE OR REPLACE VIEW workflow.jobpacks AS SELECT * FROM ref.jobpacks;
CREATE OR REPLACE VIEW workflow.roles AS SELECT * FROM ref.roles;
CREATE OR REPLACE VIEW workflow.doc_rev_milestones AS SELECT * FROM ref.doc_rev_milestones;
CREATE OR REPLACE VIEW workflow.revision_overview AS SELECT * FROM ref.revision_overview;
CREATE OR REPLACE VIEW workflow.doc_rev_statuses AS SELECT * FROM ref.doc_rev_statuses;
CREATE OR REPLACE VIEW workflow.doc_rev_status_ui_behaviors AS SELECT * FROM ref.doc_rev_status_ui_behaviors;
CREATE OR REPLACE VIEW workflow.files_accepted AS SELECT * FROM ref.files_accepted;
CREATE OR REPLACE VIEW workflow.leased_doc_nums AS SELECT * FROM ref.leased_doc_nums;
CREATE OR REPLACE VIEW workflow.sql_queries AS SELECT * FROM ref.sql_queries;
CREATE OR REPLACE VIEW workflow.person AS SELECT * FROM ref.person;
CREATE OR REPLACE VIEW workflow.users AS SELECT * FROM ref.users;
CREATE OR REPLACE VIEW workflow.doc_types AS SELECT * FROM ref.doc_types;
CREATE OR REPLACE VIEW workflow.distribution_list AS SELECT * FROM ref.distribution_list;
CREATE OR REPLACE VIEW workflow.distribution_list_content AS SELECT * FROM ref.distribution_list_content;
CREATE OR REPLACE VIEW workflow.permissions AS SELECT * FROM ref.permissions;
CREATE OR REPLACE VIEW workflow.doc_cache AS SELECT * FROM ref.doc_cache;

CREATE OR REPLACE VIEW workflow.doc AS SELECT * FROM core.doc;
CREATE OR REPLACE VIEW workflow.doc_revision AS SELECT * FROM core.doc_revision;
CREATE OR REPLACE VIEW workflow.files AS SELECT * FROM core.files;
CREATE OR REPLACE VIEW workflow.files_commented AS SELECT * FROM core.files_commented;
CREATE OR REPLACE VIEW workflow.notifications AS SELECT * FROM core.notifications;
CREATE OR REPLACE VIEW workflow.notification_targets AS SELECT * FROM core.notification_targets;
CREATE OR REPLACE VIEW workflow.notification_recipients AS SELECT * FROM core.notification_recipients;

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

CREATE OR REPLACE VIEW workflow.doc_revision_history AS SELECT * FROM audit.doc_revision_history;
CREATE OR REPLACE VIEW workflow.doc_revision_history_view AS
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
LEFT JOIN ref.doc_rev_statuses s ON s.rev_status_id = r.rev_status_id;

CREATE OR REPLACE VIEW workflow.v_document_revisions AS
SELECT
    r.*, s.rev_status_name
FROM core.doc_revision r
JOIN ref.doc_rev_statuses s ON s.rev_status_id = r.rev_status_id;

CREATE OR REPLACE VIEW workflow.v_files AS
SELECT
    f.*, r.doc_id
FROM core.files f
JOIN core.doc_revision r ON r.rev_id = f.rev_id;

-- --------------------------------------------------------
