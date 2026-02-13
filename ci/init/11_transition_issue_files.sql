-- 11. Status transition: issue all revision files to the new status
-- When a revision transitions forward/back, set issued_status_id on all its files
-- so files "move" with the revision via a single POST status-transitions call.
SET search_path = core, ref, workflow, audit, pg_temp;

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

    -- Move all revision files to the new status (issued_status_id) so they appear in that tab
    UPDATE core.files
    SET issued_status_id = v_next_status_id
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
