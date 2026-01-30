-- 7. Workflow Functions (schema: workflow)
-- --------------------------------------------------------
SET search_path = workflow;

CREATE OR REPLACE FUNCTION workflow.create_document(
    p_doc_name_unique VARCHAR,
    p_title VARCHAR,
    p_project_id SMALLINT,
    p_jobpack_id SMALLINT,
    p_type_id SMALLINT,
    p_area_id SMALLINT,
    p_unit_id SMALLINT,
    p_rev_code_id SMALLINT,
    p_rev_author_id SMALLINT,
    p_rev_originator_id SMALLINT,
    p_rev_modifier_id SMALLINT,
    p_transmital_current_revision VARCHAR,
    p_milestone_id SMALLINT,
    p_planned_start_date TIMESTAMPTZ,
    p_planned_finish_date TIMESTAMPTZ,
    p_actual_start_date TIMESTAMPTZ,
    p_actual_finish_date TIMESTAMPTZ,
    p_modified_doc_date TIMESTAMPTZ,
    p_as_built BOOLEAN DEFAULT FALSE
) RETURNS TABLE (doc_id INTEGER, rev_id INTEGER)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = core, ref, workflow, audit, pg_temp
AS $$
DECLARE
    v_start_status SMALLINT;
    v_doc_id INTEGER;
BEGIN
    SELECT rev_status_id INTO v_start_status
    FROM ref.doc_rev_statuses WHERE start = TRUE LIMIT 1;

    IF v_start_status IS NULL THEN
        RAISE EXCEPTION 'No start status configured';
    END IF;

    INSERT INTO core.doc (
        doc_name_unique, title, project_id, jobpack_id, type_id, area_id, unit_id
    ) VALUES (
        p_doc_name_unique, p_title, p_project_id, p_jobpack_id, p_type_id, p_area_id, p_unit_id
    ) RETURNING core.doc.doc_id INTO v_doc_id;

    INSERT INTO core.doc_revision (
        doc_id,
        rev_code_id,
        rev_author_id,
        rev_originator_id,
        rev_modifier_id,
        transmital_current_revision,
        milestone_id,
        planned_start_date,
        planned_finish_date,
        actual_start_date,
        actual_finish_date,
        canceled_date,
        rev_status_id,
        seq_num,
        modified_doc_date,
        as_built
    ) VALUES (
        v_doc_id,
        p_rev_code_id,
        p_rev_author_id,
        p_rev_originator_id,
        p_rev_modifier_id,
        p_transmital_current_revision,
        p_milestone_id,
        p_planned_start_date,
        p_planned_finish_date,
        p_actual_start_date,
        p_actual_finish_date,
        NULL,
        v_start_status,
        1,
        COALESCE(p_modified_doc_date, CURRENT_TIMESTAMP),
        COALESCE(p_as_built, FALSE)
    ) RETURNING core.doc_revision.rev_id INTO rev_id;

    UPDATE core.doc
    SET rev_current_id = rev_id
    WHERE core.doc.doc_id = v_doc_id;

    RETURN QUERY SELECT v_doc_id, rev_id;
END;
$$;

CREATE OR REPLACE FUNCTION workflow.create_revision(
    p_doc_id INTEGER,
    p_rev_code_id SMALLINT,
    p_rev_author_id SMALLINT,
    p_rev_originator_id SMALLINT,
    p_rev_modifier_id SMALLINT,
    p_transmital_current_revision VARCHAR,
    p_milestone_id SMALLINT,
    p_planned_start_date TIMESTAMPTZ,
    p_planned_finish_date TIMESTAMPTZ,
    p_actual_start_date TIMESTAMPTZ,
    p_actual_finish_date TIMESTAMPTZ,
    p_modified_doc_date TIMESTAMPTZ,
    p_as_built BOOLEAN DEFAULT FALSE
) RETURNS INTEGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = core, ref, workflow, audit, pg_temp
AS $$
DECLARE
    v_start_status SMALLINT;
    v_seq SMALLINT;
    v_rev_id INTEGER;
BEGIN
    SELECT rev_status_id INTO v_start_status
    FROM ref.doc_rev_statuses WHERE start = TRUE LIMIT 1;

    IF v_start_status IS NULL THEN
        RAISE EXCEPTION 'No start status configured';
    END IF;

    SELECT COALESCE(MAX(seq_num), 0) + 1 INTO v_seq
    FROM core.doc_revision WHERE doc_id = p_doc_id;

    INSERT INTO core.doc_revision (
        doc_id,
        rev_code_id,
        rev_author_id,
        rev_originator_id,
        rev_modifier_id,
        transmital_current_revision,
        milestone_id,
        planned_start_date,
        planned_finish_date,
        actual_start_date,
        actual_finish_date,
        canceled_date,
        rev_status_id,
        seq_num,
        modified_doc_date,
        as_built
    ) VALUES (
        p_doc_id,
        p_rev_code_id,
        p_rev_author_id,
        p_rev_originator_id,
        p_rev_modifier_id,
        p_transmital_current_revision,
        p_milestone_id,
        p_planned_start_date,
        p_planned_finish_date,
        p_actual_start_date,
        p_actual_finish_date,
        NULL,
        v_start_status,
        v_seq,
        COALESCE(p_modified_doc_date, CURRENT_TIMESTAMP),
        COALESCE(p_as_built, FALSE)
    ) RETURNING rev_id INTO v_rev_id;

    UPDATE core.doc
    SET rev_current_id = v_rev_id
    WHERE doc_id = p_doc_id;

    RETURN v_rev_id;
END;
$$;

CREATE OR REPLACE FUNCTION workflow.transition_revision(
    p_rev_id INTEGER,
    p_direction TEXT
) RETURNS core.doc_revision
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = core, ref, workflow, audit, pg_temp
AS $$
DECLARE
    v_rev core.doc_revision%ROWTYPE;
    v_status ref.doc_rev_statuses%ROWTYPE;
    v_next_status ref.doc_rev_statuses%ROWTYPE;
    v_next_status_id SMALLINT;
BEGIN
    SELECT * INTO v_rev FROM core.doc_revision WHERE rev_id = p_rev_id FOR UPDATE;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Revision not found';
    END IF;

    IF v_rev.superseded THEN
        RAISE EXCEPTION 'Superseded revision cannot be transitioned';
    END IF;

    SELECT * INTO v_status FROM ref.doc_rev_statuses WHERE rev_status_id = v_rev.rev_status_id;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Invalid current status';
    END IF;

    IF p_direction NOT IN ('forward', 'back') THEN
        RAISE EXCEPTION 'Invalid direction';
    END IF;

    IF p_direction = 'forward' THEN
        IF v_status.final OR v_status.next_rev_status_id IS NULL THEN
            RAISE EXCEPTION 'Revision already at final status';
        END IF;
        v_next_status_id := v_status.next_rev_status_id;
    ELSE
        IF v_status.start THEN
            RAISE EXCEPTION 'Revision already at start status';
        END IF;
        IF NOT v_status.revertible THEN
            RAISE EXCEPTION 'Revision status not revertible';
        END IF;
        SELECT rev_status_id INTO v_next_status_id
        FROM ref.doc_rev_statuses
        WHERE next_rev_status_id = v_status.rev_status_id;
        IF v_next_status_id IS NULL THEN
            RAISE EXCEPTION 'Previous status not found';
        END IF;
    END IF;

    SELECT * INTO v_next_status FROM ref.doc_rev_statuses WHERE rev_status_id = v_next_status_id;

    -- Rule 7: files must exist before entering any non-start state
    IF NOT v_next_status.start THEN
        PERFORM 1 FROM core.files WHERE rev_id = p_rev_id LIMIT 1;
        IF NOT FOUND THEN
            RAISE EXCEPTION 'Files must exist before leaving the start status';
        END IF;
    END IF;

    PERFORM set_config('app.action', 'transition', true);
    UPDATE core.doc_revision
    SET rev_status_id = v_next_status_id
    WHERE rev_id = p_rev_id;

    INSERT INTO audit.revision_status_audit (
        rev_id, doc_id, from_status_id, to_status_id, action, reason, changed_by
    ) VALUES (
        p_rev_id, v_rev.doc_id, v_status.rev_status_id, v_next_status_id, 'transition', NULL,
        NULLIF(current_setting('app.user', true), '')::SMALLINT
    );

    IF v_next_status.final THEN
        PERFORM set_config('app.action', 'transition_final', true);
        -- Supersede previous final revision (if any)
        UPDATE core.doc_revision
        SET superseded = TRUE
        WHERE doc_id = v_rev.doc_id
          AND rev_id <> p_rev_id
          AND rev_status_id IN (SELECT rev_status_id FROM ref.doc_rev_statuses WHERE final = TRUE)
          AND superseded = FALSE;

        UPDATE core.doc
        SET rev_actual_id = p_rev_id,
            rev_current_id = p_rev_id
        WHERE doc_id = v_rev.doc_id;
    END IF;

    SELECT * INTO v_rev FROM core.doc_revision WHERE rev_id = p_rev_id;
    RETURN v_rev;
END;
$$;

CREATE OR REPLACE FUNCTION workflow.cancel_revision(
    p_rev_id INTEGER
) RETURNS core.doc_revision
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = core, ref, workflow, audit, pg_temp
AS $$
DECLARE
    v_rev core.doc_revision%ROWTYPE;
    v_status ref.doc_rev_statuses%ROWTYPE;
BEGIN
    SELECT * INTO v_rev FROM core.doc_revision WHERE rev_id = p_rev_id FOR UPDATE;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Revision not found';
    END IF;

    SELECT * INTO v_status FROM ref.doc_rev_statuses WHERE rev_status_id = v_rev.rev_status_id;
    IF v_status.final THEN
        RAISE EXCEPTION 'Final revision cannot be canceled';
    END IF;

    IF v_rev.canceled_date IS NULL THEN
        UPDATE core.doc_revision
        SET canceled_date = CURRENT_TIMESTAMP
        WHERE rev_id = p_rev_id;
    END IF;

    UPDATE core.doc
    SET rev_current_id = rev_actual_id
    WHERE doc_id = v_rev.doc_id;

    INSERT INTO audit.revision_status_audit (
        rev_id, doc_id, from_status_id, to_status_id, action, reason, changed_by
    ) VALUES (
        p_rev_id, v_rev.doc_id, v_rev.rev_status_id, v_rev.rev_status_id, 'cancel', NULL,
        NULLIF(current_setting('app.user', true), '')::SMALLINT
    );

    SELECT * INTO v_rev FROM core.doc_revision WHERE rev_id = p_rev_id;
    RETURN v_rev;
END;
$$;

CREATE OR REPLACE FUNCTION workflow.admin_override_transition(
    p_rev_id INTEGER,
    p_target_status_id SMALLINT,
    p_reason TEXT
) RETURNS core.doc_revision
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = core, ref, workflow, audit, pg_temp
AS $$
DECLARE
    v_rev core.doc_revision%ROWTYPE;
    v_from_status SMALLINT;
    v_target ref.doc_rev_statuses%ROWTYPE;
BEGIN
    IF NOT (pg_has_role(current_user, 'db_admin', 'member') OR pg_has_role(current_user, 'db_owner', 'member')) THEN
        RAISE EXCEPTION 'Admin role required';
    END IF;

    SELECT * INTO v_rev FROM core.doc_revision WHERE rev_id = p_rev_id FOR UPDATE;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Revision not found';
    END IF;

    SELECT * INTO v_target FROM ref.doc_rev_statuses WHERE rev_status_id = p_target_status_id;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Target status not found';
    END IF;

    -- Rule 7 enforced for non-start target
    IF NOT v_target.start THEN
        PERFORM 1 FROM core.files WHERE rev_id = p_rev_id LIMIT 1;
        IF NOT FOUND THEN
            RAISE EXCEPTION 'Files must exist before leaving the start status';
        END IF;
    END IF;

    v_from_status := v_rev.rev_status_id;

    PERFORM set_config('app.action', 'admin_override', true);
    UPDATE core.doc_revision
    SET rev_status_id = p_target_status_id
    WHERE rev_id = p_rev_id;

    INSERT INTO audit.admin_override_audit (
        rev_id, doc_id, from_status_id, to_status_id, reason, changed_by
    ) VALUES (
        p_rev_id, v_rev.doc_id, v_from_status, p_target_status_id, p_reason,
        NULLIF(current_setting('app.user', true), '')::SMALLINT
    );

    IF v_target.final THEN
        PERFORM set_config('app.action', 'transition_final', true);
        UPDATE core.doc_revision
        SET superseded = TRUE
        WHERE doc_id = v_rev.doc_id
          AND rev_id <> p_rev_id
          AND rev_status_id IN (SELECT rev_status_id FROM ref.doc_rev_statuses WHERE final = TRUE)
          AND superseded = FALSE;

        UPDATE core.doc
        SET rev_actual_id = p_rev_id,
            rev_current_id = p_rev_id
        WHERE doc_id = v_rev.doc_id;
    END IF;

    INSERT INTO audit.revision_status_audit (
        rev_id, doc_id, from_status_id, to_status_id, action, reason, changed_by
    ) VALUES (
        p_rev_id, v_rev.doc_id, v_from_status, p_target_status_id, 'admin_override', p_reason,
        NULLIF(current_setting('app.user', true), '')::SMALLINT
    );

    SELECT * INTO v_rev FROM core.doc_revision WHERE rev_id = p_rev_id;
    RETURN v_rev;
END;
$$;

CREATE OR REPLACE FUNCTION workflow.update_document(
    p_doc_id INTEGER,
    p_patch JSONB
) RETURNS core.doc
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = core, ref, workflow, audit, pg_temp
AS $$
DECLARE
    v_doc core.doc%ROWTYPE;
BEGIN
    IF p_patch IS NULL OR p_patch = '{}'::jsonb THEN
        RAISE EXCEPTION 'No fields to update';
    END IF;

    SELECT * INTO v_doc FROM core.doc WHERE doc_id = p_doc_id FOR UPDATE;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Document not found';
    END IF;

    UPDATE core.doc
    SET doc_name_unique = CASE
            WHEN p_patch ? 'doc_name_unique' THEN p_patch->>'doc_name_unique'
            ELSE doc_name_unique
        END,
        title = CASE
            WHEN p_patch ? 'title' THEN p_patch->>'title'
            ELSE title
        END,
        project_id = CASE
            WHEN p_patch ? 'project_id' THEN (p_patch->>'project_id')::SMALLINT
            ELSE project_id
        END,
        jobpack_id = CASE
            WHEN p_patch ? 'jobpack_id' THEN (p_patch->>'jobpack_id')::SMALLINT
            ELSE jobpack_id
        END,
        type_id = CASE
            WHEN p_patch ? 'type_id' THEN (p_patch->>'type_id')::SMALLINT
            ELSE type_id
        END,
        area_id = CASE
            WHEN p_patch ? 'area_id' THEN (p_patch->>'area_id')::SMALLINT
            ELSE area_id
        END,
        unit_id = CASE
            WHEN p_patch ? 'unit_id' THEN (p_patch->>'unit_id')::SMALLINT
            ELSE unit_id
        END,
        rev_actual_id = CASE
            WHEN p_patch ? 'rev_actual_id' THEN (p_patch->>'rev_actual_id')::INTEGER
            ELSE rev_actual_id
        END,
        rev_current_id = CASE
            WHEN p_patch ? 'rev_current_id' THEN (p_patch->>'rev_current_id')::INTEGER
            ELSE rev_current_id
        END,
        updated_at = NULL,
        updated_by = NULL
    WHERE doc_id = p_doc_id;

    SELECT * INTO v_doc FROM core.doc WHERE doc_id = p_doc_id;
    RETURN v_doc;
END;
$$;

CREATE OR REPLACE FUNCTION workflow.update_revision(
    p_rev_id INTEGER,
    p_patch JSONB
) RETURNS core.doc_revision
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = core, ref, workflow, audit, pg_temp
AS $$
DECLARE
    v_rev core.doc_revision%ROWTYPE;
BEGIN
    IF p_patch IS NULL OR p_patch = '{}'::jsonb THEN
        RAISE EXCEPTION 'No fields to update';
    END IF;

    SELECT * INTO v_rev FROM core.doc_revision WHERE rev_id = p_rev_id FOR UPDATE;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Revision not found';
    END IF;

    UPDATE core.doc_revision
    SET seq_num = CASE
            WHEN p_patch ? 'seq_num' THEN (p_patch->>'seq_num')::SMALLINT
            ELSE seq_num
        END,
        rev_code_id = CASE
            WHEN p_patch ? 'rev_code_id' THEN (p_patch->>'rev_code_id')::SMALLINT
            ELSE rev_code_id
        END,
        rev_author_id = CASE
            WHEN p_patch ? 'rev_author_id' THEN (p_patch->>'rev_author_id')::SMALLINT
            ELSE rev_author_id
        END,
        rev_originator_id = CASE
            WHEN p_patch ? 'rev_originator_id' THEN (p_patch->>'rev_originator_id')::SMALLINT
            ELSE rev_originator_id
        END,
        rev_modifier_id = CASE
            WHEN p_patch ? 'rev_modifier_id' THEN (p_patch->>'rev_modifier_id')::SMALLINT
            ELSE rev_modifier_id
        END,
        transmital_current_revision = CASE
            WHEN p_patch ? 'transmital_current_revision'
                THEN p_patch->>'transmital_current_revision'
            ELSE transmital_current_revision
        END,
        milestone_id = CASE
            WHEN p_patch ? 'milestone_id' THEN (p_patch->>'milestone_id')::SMALLINT
            ELSE milestone_id
        END,
        planned_start_date = CASE
            WHEN p_patch ? 'planned_start_date' THEN (p_patch->>'planned_start_date')::TIMESTAMPTZ
            ELSE planned_start_date
        END,
        planned_finish_date = CASE
            WHEN p_patch ? 'planned_finish_date' THEN (p_patch->>'planned_finish_date')::TIMESTAMPTZ
            ELSE planned_finish_date
        END,
        actual_start_date = CASE
            WHEN p_patch ? 'actual_start_date' THEN (p_patch->>'actual_start_date')::TIMESTAMPTZ
            ELSE actual_start_date
        END,
        actual_finish_date = CASE
            WHEN p_patch ? 'actual_finish_date' THEN (p_patch->>'actual_finish_date')::TIMESTAMPTZ
            ELSE actual_finish_date
        END,
        as_built = CASE
            WHEN p_patch ? 'as_built' THEN (p_patch->>'as_built')::BOOLEAN
            ELSE as_built
        END,
        modified_doc_date = CASE
            WHEN p_patch ? 'modified_doc_date' THEN (p_patch->>'modified_doc_date')::TIMESTAMPTZ
            ELSE modified_doc_date
        END,
        updated_at = NULL,
        updated_by = NULL
    WHERE rev_id = p_rev_id;

    SELECT * INTO v_rev FROM core.doc_revision WHERE rev_id = p_rev_id;
    RETURN v_rev;
END;
$$;

CREATE OR REPLACE FUNCTION workflow.delete_document(
    p_doc_id INTEGER
) RETURNS TEXT
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = core, ref, workflow, audit, pg_temp
AS $$
DECLARE
    v_start_status SMALLINT;
    v_doc core.doc%ROWTYPE;
    v_rev core.doc_revision%ROWTYPE;
    v_count INTEGER;
BEGIN
    SELECT * INTO v_doc FROM core.doc WHERE doc_id = p_doc_id FOR UPDATE;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Document not found';
    END IF;

    SELECT rev_status_id INTO v_start_status
    FROM ref.doc_rev_statuses WHERE start = TRUE LIMIT 1;
    IF v_start_status IS NULL THEN
        RAISE EXCEPTION 'No start status configured';
    END IF;

    SELECT COUNT(*) INTO v_count FROM core.doc_revision WHERE doc_id = p_doc_id;
    IF v_count = 1 THEN
        SELECT * INTO v_rev FROM core.doc_revision WHERE doc_id = p_doc_id LIMIT 1;
        IF v_rev.rev_status_id = v_start_status THEN
            UPDATE core.doc
            SET rev_current_id = NULL,
                rev_actual_id = NULL
            WHERE doc_id = p_doc_id;
            PERFORM set_config('app.action', 'delete_document', true);
            DELETE FROM core.doc WHERE doc_id = p_doc_id;
            RETURN 'deleted';
        END IF;
    END IF;

    UPDATE core.doc SET voided = TRUE WHERE doc_id = p_doc_id;
    RETURN 'voided';
END;
$$;

CREATE OR REPLACE FUNCTION workflow.create_file(
    p_rev_id INTEGER,
    p_filename VARCHAR,
    p_s3_uid TEXT,
    p_mimetype VARCHAR
) RETURNS core.files
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = core, ref, workflow, audit, pg_temp
AS $$
DECLARE
    v_file core.files%ROWTYPE;
BEGIN
    PERFORM 1 FROM core.doc_revision WHERE rev_id = p_rev_id;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Revision not found';
    END IF;

    INSERT INTO core.files (
        rev_id, filename, s3_uid, mimetype
    ) VALUES (
        p_rev_id, p_filename, p_s3_uid, p_mimetype
    ) RETURNING * INTO v_file;

    RETURN v_file;
END;
$$;

CREATE OR REPLACE FUNCTION workflow.update_file(
    p_file_id INTEGER,
    p_filename VARCHAR
) RETURNS core.files
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = core, ref, workflow, audit, pg_temp
AS $$
DECLARE
    v_file core.files%ROWTYPE;
BEGIN
    SELECT * INTO v_file FROM core.files WHERE id = p_file_id FOR UPDATE;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'File not found';
    END IF;

    UPDATE core.files
    SET filename = p_filename
    WHERE id = p_file_id;

    SELECT * INTO v_file FROM core.files WHERE id = p_file_id;
    RETURN v_file;
END;
$$;

CREATE OR REPLACE FUNCTION workflow.delete_file(
    p_file_id INTEGER
) RETURNS VOID
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = core, ref, workflow, audit, pg_temp
AS $$
BEGIN
    PERFORM 1 FROM core.files WHERE id = p_file_id;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'File not found';
    END IF;

    DELETE FROM core.files WHERE id = p_file_id;
END;
$$;

CREATE OR REPLACE FUNCTION workflow.create_file_commented(
    p_file_id INTEGER,
    p_user_id INTEGER,
    p_s3_uid TEXT,
    p_mimetype VARCHAR
) RETURNS core.files_commented
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = core, ref, workflow, audit, pg_temp
AS $$
DECLARE
    v_row core.files_commented%ROWTYPE;
BEGIN
    PERFORM 1 FROM core.files WHERE id = p_file_id;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'File not found';
    END IF;
    PERFORM 1 FROM ref.users WHERE user_id = p_user_id;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'User not found';
    END IF;

    INSERT INTO core.files_commented (
        file_id, user_id, s3_uid, mimetype
    ) VALUES (
        p_file_id, p_user_id, p_s3_uid, p_mimetype
    ) RETURNING * INTO v_row;

    RETURN v_row;
END;
$$;

CREATE OR REPLACE FUNCTION workflow.delete_file_commented(
    p_id INTEGER
) RETURNS VOID
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = core, ref, workflow, audit, pg_temp
AS $$
BEGIN
    PERFORM 1 FROM core.files_commented WHERE id = p_id;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Commented file not found';
    END IF;

    DELETE FROM core.files_commented WHERE id = p_id;
END;
$$;

-- --------------------------------------------------------
