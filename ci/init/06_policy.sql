-- 6. Policy Enforcement Triggers
-- --------------------------------------------------------
CREATE OR REPLACE FUNCTION core.fn_doc_revision_enforce_rules() RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = core, ref, pg_temp
AS $$
DECLARE
    v_new_status ref.doc_rev_statuses%ROWTYPE;
    v_old_status ref.doc_rev_statuses%ROWTYPE;
    v_has_other BOOLEAN;
BEGIN
    -- lock document row to serialize per-doc transitions
    PERFORM 1 FROM core.doc WHERE doc_id = NEW.doc_id FOR UPDATE;

    SELECT * INTO v_new_status FROM ref.doc_rev_statuses WHERE rev_status_id = NEW.rev_status_id;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Invalid revision status';
    END IF;

    IF TG_OP = 'UPDATE' THEN
        SELECT * INTO v_old_status FROM ref.doc_rev_statuses WHERE rev_status_id = OLD.rev_status_id;
        -- Final revisions are immutable unless explicitly overridden
        IF v_old_status.final THEN
            IF COALESCE(current_setting('app.action', true), '') NOT IN (
                'transition_final', 'supersede_final', 'admin_override'
            ) THEN
                RAISE EXCEPTION 'Final revision is immutable';
            END IF;
        END IF;
        -- Superseded revisions cannot transition
        IF OLD.superseded AND NEW.rev_status_id <> OLD.rev_status_id THEN
            RAISE EXCEPTION 'Superseded revision cannot be transitioned';
        END IF;
    END IF;

    IF NEW.canceled_date IS NULL AND NOT COALESCE(NEW.superseded, false) THEN
        SELECT EXISTS (
            SELECT 1
            FROM core.doc_revision r
            WHERE r.doc_id = NEW.doc_id
              AND r.rev_id <> COALESCE(NEW.rev_id, 0)
              AND r.rev_code_id = NEW.rev_code_id
              AND r.canceled_date IS NULL
              AND COALESCE(r.superseded, false) = false
        ) INTO v_has_other;
        IF v_has_other THEN
            RAISE EXCEPTION 'Only one non-canceled revision per document may use a revision code';
        END IF;
    END IF;

    -- Rule 3: Only one active (non-final, non-canceled, non-superseded) revision per document
    IF NEW.canceled_date IS NULL AND NOT v_new_status.final AND NOT COALESCE(NEW.superseded, false) THEN
        SELECT EXISTS (
            SELECT 1
            FROM core.doc_revision r
            JOIN ref.doc_rev_statuses s ON s.rev_status_id = r.rev_status_id
            WHERE r.doc_id = NEW.doc_id
              AND r.rev_id <> COALESCE(NEW.rev_id, 0)
              AND r.canceled_date IS NULL
              AND NOT s.final
              AND COALESCE(r.superseded, false) = false
        ) INTO v_has_other;
        IF v_has_other THEN
            RAISE EXCEPTION 'Only one active (non-final, non-canceled) revision allowed per document';
        END IF;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER tr_doc_revision_enforce_rules
BEFORE INSERT OR UPDATE ON core.doc_revision
FOR EACH ROW EXECUTE FUNCTION core.fn_doc_revision_enforce_rules();

CREATE OR REPLACE FUNCTION core.fn_doc_revision_prevent_delete() RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = core, ref, pg_temp
AS $$
BEGIN
    IF COALESCE(current_setting('app.action', true), '') = 'delete_document' THEN
        RETURN OLD;
    END IF;
    RAISE EXCEPTION 'Revision deletion is forbidden; use cancellation instead';
END;
$$;

CREATE TRIGGER tr_doc_revision_prevent_delete
BEFORE DELETE ON core.doc_revision
FOR EACH ROW EXECUTE FUNCTION core.fn_doc_revision_prevent_delete();

CREATE OR REPLACE FUNCTION core.fn_doc_prevent_delete_if_final() RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = core, ref, pg_temp
AS $$
DECLARE
    v_has_final BOOLEAN;
BEGIN
    SELECT EXISTS (
        SELECT 1
        FROM core.doc_revision r
        JOIN ref.doc_rev_statuses s ON s.rev_status_id = r.rev_status_id
        WHERE r.doc_id = OLD.doc_id
          AND s.final
    ) INTO v_has_final;

    IF v_has_final THEN
        RAISE EXCEPTION 'Document deletion forbidden: final revision exists';
    END IF;

    RETURN OLD;
END;
$$;

CREATE TRIGGER tr_doc_prevent_delete_if_final
BEFORE DELETE ON core.doc
FOR EACH ROW EXECUTE FUNCTION core.fn_doc_prevent_delete_if_final();

-- --------------------------------------------------------
