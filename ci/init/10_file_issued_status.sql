-- 10. File issued status (move file to workflow tab)
-- Adds optional issued_status_id to core.files so files can be "issued" to a status (e.g. IDC).
SET search_path = core, ref, workflow, pg_temp;

ALTER TABLE core.files
    ADD COLUMN IF NOT EXISTS issued_status_id SMALLINT NULL
    REFERENCES ref.doc_rev_statuses(rev_status_id);

-- Update workflow function to allow setting issued_status_id (and optionally filename)
CREATE OR REPLACE FUNCTION workflow.update_file(
    p_file_id INTEGER,
    p_filename VARCHAR DEFAULT NULL,
    p_issued_status_id SMALLINT DEFAULT NULL
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
    SET filename = COALESCE(NULLIF(TRIM(p_filename), ''), filename),
        issued_status_id = COALESCE(p_issued_status_id, issued_status_id)
    WHERE id = p_file_id;

    SELECT * INTO v_file FROM core.files WHERE id = p_file_id;
    RETURN v_file;
END;
$$;
