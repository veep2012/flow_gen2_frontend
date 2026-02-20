-- 5. Utility Triggers (timestamps, created_by)
-- --------------------------------------------------------
SET search_path = core, ref;

CREATE OR REPLACE FUNCTION core.fn_update_timestamp() RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = core, ref, pg_temp
AS $$
BEGIN
    IF NEW.updated_at IS NULL THEN
        NEW.updated_at = CURRENT_TIMESTAMP;
    END IF;
    IF NEW.updated_by IS NULL THEN
        NEW.updated_by = NULLIF(current_setting('app.user', true), '')::SMALLINT;
    END IF;
    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION core.fn_set_created_by() RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = core, ref, pg_temp
AS $$
BEGIN
    IF NEW.created_by IS NULL THEN
        NEW.created_by = NULLIF(current_setting('app.user', true), '')::SMALLINT;
    END IF;
    IF NEW.updated_by IS NULL THEN
        NEW.updated_by = NULLIF(current_setting('app.user', true), '')::SMALLINT;
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER tr_doc_update_timestamp
BEFORE UPDATE ON core.doc
FOR EACH ROW EXECUTE FUNCTION core.fn_update_timestamp();

CREATE TRIGGER tr_doc_set_created_by
BEFORE INSERT ON core.doc
FOR EACH ROW EXECUTE FUNCTION core.fn_set_created_by();

CREATE TRIGGER tr_doc_revision_update_timestamp
BEFORE UPDATE ON core.doc_revision
FOR EACH ROW EXECUTE FUNCTION core.fn_update_timestamp();

CREATE TRIGGER tr_doc_revision_set_created_by
BEFORE INSERT ON core.doc_revision
FOR EACH ROW EXECUTE FUNCTION core.fn_set_created_by();

CREATE TRIGGER tr_files_update_timestamp
BEFORE UPDATE ON core.files
FOR EACH ROW EXECUTE FUNCTION core.fn_update_timestamp();

CREATE TRIGGER tr_files_set_created_by
BEFORE INSERT ON core.files
FOR EACH ROW EXECUTE FUNCTION core.fn_set_created_by();

CREATE TRIGGER tr_files_commented_update_timestamp
BEFORE UPDATE ON core.files_commented
FOR EACH ROW EXECUTE FUNCTION core.fn_update_timestamp();

CREATE TRIGGER tr_files_commented_set_created_by
BEFORE INSERT ON core.files_commented
FOR EACH ROW EXECUTE FUNCTION core.fn_set_created_by();

CREATE TRIGGER tr_written_comments_update_timestamp
BEFORE UPDATE ON core.written_comments
FOR EACH ROW EXECUTE FUNCTION core.fn_update_timestamp();

CREATE TRIGGER tr_written_comments_set_created_by
BEFORE INSERT ON core.written_comments
FOR EACH ROW EXECUTE FUNCTION core.fn_set_created_by();

CREATE TRIGGER tr_notifications_update_timestamp
BEFORE UPDATE ON core.notifications
FOR EACH ROW EXECUTE FUNCTION core.fn_update_timestamp();

CREATE TRIGGER tr_notifications_set_created_by
BEFORE INSERT ON core.notifications
FOR EACH ROW EXECUTE FUNCTION core.fn_set_created_by();

CREATE TRIGGER tr_distribution_list_update_timestamp
BEFORE UPDATE ON core.distribution_list
FOR EACH ROW EXECUTE FUNCTION core.fn_update_timestamp();

CREATE TRIGGER tr_distribution_list_set_created_by
BEFORE INSERT ON core.distribution_list
FOR EACH ROW EXECUTE FUNCTION core.fn_set_created_by();

CREATE TRIGGER tr_distribution_list_content_update_timestamp
BEFORE UPDATE ON core.distribution_list_content
FOR EACH ROW EXECUTE FUNCTION core.fn_update_timestamp();

CREATE TRIGGER tr_distribution_list_content_set_created_by
BEFORE INSERT ON core.distribution_list_content
FOR EACH ROW EXECUTE FUNCTION core.fn_set_created_by();

CREATE TRIGGER tr_notification_targets_update_timestamp
BEFORE UPDATE ON core.notification_targets
FOR EACH ROW EXECUTE FUNCTION core.fn_update_timestamp();

CREATE TRIGGER tr_notification_targets_set_created_by
BEFORE INSERT ON core.notification_targets
FOR EACH ROW EXECUTE FUNCTION core.fn_set_created_by();

CREATE TRIGGER tr_notification_recipients_update_timestamp
BEFORE UPDATE ON core.notification_recipients
FOR EACH ROW EXECUTE FUNCTION core.fn_update_timestamp();

CREATE TRIGGER tr_notification_recipients_set_created_by
BEFORE INSERT ON core.notification_recipients
FOR EACH ROW EXECUTE FUNCTION core.fn_set_created_by();

CREATE OR REPLACE FUNCTION core.fn_files_commented_check_mimetype() RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = core, ref, pg_temp
AS $$
DECLARE
    original_mimetype VARCHAR(90);
BEGIN
    SELECT mimetype INTO original_mimetype FROM core.files WHERE id = NEW.file_id;
    IF original_mimetype IS NULL THEN
        RAISE EXCEPTION 'File not found for commented file_id=%', NEW.file_id
            USING ERRCODE = '23503';
    END IF;
    IF NEW.mimetype IS NULL OR lower(NEW.mimetype) <> lower(original_mimetype) THEN
        RAISE EXCEPTION 'Commented file mimetype % does not match original %',
            NEW.mimetype, original_mimetype
            USING ERRCODE = '23514';
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER tr_files_commented_check_mimetype
BEFORE INSERT OR UPDATE ON core.files_commented
FOR EACH ROW EXECUTE FUNCTION core.fn_files_commented_check_mimetype();

-- --------------------------------------------------------
