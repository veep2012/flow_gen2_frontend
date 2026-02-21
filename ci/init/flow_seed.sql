-- ========================================================
-- POSTGRESQL SEED DATA SCRIPT FOR FLOW
-- ========================================================
-- 1. Populates lookup tables from your 5_base_content.sql
-- 2. Generates fake Documents and Revisions for testing
-- NOTE: Must be executed by a privileged role (e.g., postgres/db_owner).
--       app_user is read-only on workflow tables and cannot run this seed.
-- ========================================================

SET search_path TO ref, core, workflow;

-- --------------------------------------------------------
-- 1. Base Content (Lookup Tables)
-- --------------------------------------------------------

-- Areas
INSERT INTO areas (area_id, area_name, area_acronym) VALUES 
(1,'Field ','F'),(2,'Korolev','K'),(3,'SGP','61'),(4,'KTL 1','62'),
(5,'KTL 2','63'),(6,'KTL 3','64'),(7,'Offplot','O'),(8,'SGI','73');

-- Disciplines
INSERT INTO disciplines (discipline_id, discipline_name, discipline_acronym) VALUES 
(1,'ELECTRICAL','P'),(2,'INSTRUMENT','J'),(3,'STRUCTURES','M'),(4,'GENERAL','A'),
(5,'PROCESS','B'),(6,'SAFETY','O'),(7,'FOUNDATION','Q'),(8,'BUILDING','U'),
(9,'PLAN','R'),(10,'PIPING','L'),(11,'TELECOMMS','I'),(12,'HVAC, VACUUM EQUIPMENT','H');

-- Projects
INSERT INTO projects (project_id, project_name) VALUES 
(1,'PR-2345-DSN-0003-001'),(2,'PR-2345-DSN-0003-002'),(3,'PR-2345-DSN-0003-003'),
(4,'PR-2345-DSN-0003-004'),(5,'PR-2345-DSN-0003-005'),(6,'PR-2345-DSN-0003-006'),
(7,'PR-2345-DSN-0003-007'),(8,'PR-2345-DSN-0003-008'),(9,'PR-2345-DSN-0003-009'),
(10,'PR-2345-DSN-0003-010');

-- Person Duties
INSERT INTO person_duty (duty_id, duty_name) VALUES
(1,'Engineer'),
(2,'DCC specialist'),
(3,'Project Manager'),
(4,'Director');

-- Person
INSERT INTO person (person_id, person_name, photo_s3_uid, email) VALUES 
(1,'ZHANDOS MYLTYKBAYEV',NULL,NULL),(2,'ALEKSEY KRUTSKIH',NULL,NULL),
(3,'ASYLKHAN BOKHAYEV',NULL,NULL),(4,'KONSTANTIN NI',NULL,NULL),
(5,'IVANOV IVANOV',NULL,NULL);

-- Doc Types (Truncated list for brevity, ensures key disciplines exist)
INSERT INTO doc_types (type_id, doc_type_name, ref_discipline_id, doc_type_acronym) VALUES 
(1,'EQUIPMENT LAYOUT ',1,'LAY'),(2,'SCHEMATIC DIAGRAM',1,'SCH'),
(3,'KEY SINGLE LINE DIAGRAM',1,'SLD'),(21,'INSTRUMENT CABLE BLOCK DIAGRAM',2,'IBD'),
(44,'STRUCTURAL STEELWORK LAYOUT',3,'LAY'),(51,'PLOT PLAN',4,'PLN'),
(56,'PROCESS FLOW DIAGRAM',5,'PFD'),(58,'PIPING AND INSTRUMENTATION DIAGRAM',5,'PID'),
(59,'GENERAL PLOT PLAN',6,'GPP'),(63,'RC DETAILS FOUNDATIONS',7,'DET'),
(68,'ARCHITECTURAL GENERAL ARRANGEMENT',8,'AGA'),(73,'EQUIPMENT GENERAL ARRANGEMENT',10,'EGA'),
(86,'TELECOMMS CABLE BLOCK DIAGRAM',11,'CBD'),(93,'HVAC FLOW DIAGRAM',12,'HFD');

-- Jobpacks
INSERT INTO jobpacks (jobpack_id, jobpack_name) VALUES 
(1,'JP2344567'),(2,'JP2344568'),(3,'JP2344569'),(4,'JP2344570'),(5,'JP2344571');

-- Units
INSERT INTO units (unit_id, unit_name) VALUES 
(1,'2300'),(2,'2301'),(3,'2302'),(12,'310.1'),(13,'311.2'),(26,'4601');

-- Milestones
INSERT INTO doc_rev_milestones (milestone_id, milestone_name, progress) VALUES 
(1,'Issued for construction',0),(2,'Internal Discipline Check',10);

-- Revision Overview
INSERT INTO revision_overview (rev_code_id, rev_code_name, rev_code_acronym, rev_description, percentage) VALUES 
(1,'IDC','B','INTERDISCIPLINE CHECK',30),(2,'IFRC','C','ISSUED FOR REVIEW AND COMMENTS',100),
(3,'AFD','D','APPROVED FOR DESIGN',NULL),(4,'AFC','E','APPROVED FOR CONSTRUCTION',NULL),
(5,'AS-BUILT','Z','AS-BUILT',NULL),(6,'INDESIGN','A','IN-DESIGN',10);

-- Rev Status UI Behaviors
INSERT INTO doc_rev_status_ui_behaviors (ui_behavior_id, ui_behavior_name, ui_behavior_file) VALUES
(1,'INDESIGN','InDesignBehavior.jsx'),
(2,'IDC','IDCBehavior.jsx'),
(3,'READY FOR ISSUE','ReadyForIssueBehavior.jsx'),
(4,'OFFICIAL','OfficialBehavior.jsx');

-- Rev Statuses
INSERT INTO doc_rev_statuses (
    rev_status_id,
    rev_status_name,
    ui_behavior_id,
    next_rev_status_id,
    revertible,
    editable,
    final,
    start
) VALUES 
(1,'INDESIGN',1,2,FALSE,TRUE,FALSE,TRUE),
(2,'IDC',2,3,TRUE,TRUE,FALSE,FALSE),
(3,'READY FOR ISSUE',3,4,TRUE,FALSE,FALSE,FALSE),
(4,'OFFICIAL',4,NULL,FALSE,FALSE,TRUE,FALSE);

-- Roles
INSERT INTO roles (role_id, role_name) VALUES 
(1,'SuperUser'),(2,'User/DCC'),(3,'Limited User');

-- Accepted File Types
INSERT INTO files_accepted (file_type, mimetype) VALUES
('docx', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'),
('doc', 'application/msword'),
('xlsx', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
('xls', 'application/vnd.ms-excel'),
('pdf', 'application/pdf'),
('dwg', 'application/acad'),
('dxf', 'application/dxf');

-- Instance Parameters
INSERT INTO instance_parameters (parameter, value, description) VALUES
(
    'file_name_conv',
    '<DOCNO>-<BODY>_<UACR>_<TIMEST>.<EXT>',
    'Default naming template for uploaded base files: <DOCNO>, <BODY>, <UACR>, <TIMEST>, and <EXT>.'
),
(
    'file_name_com_conv',
    '<BODY>_commented_<UACR>_<TIMEST>.<EXT>',
    'Default naming template for commented files: <BODY>, literal suffix "_commented", <UACR>, <TIMEST>, and <EXT>.'
),
(
    'dl_for_each_doc',
    'true',
    'When true, workflow.create_document auto-creates a document-linked distribution list for every new document.'
);

-- Users
INSERT INTO users (user_id, person_id, user_acronym, role_id) VALUES 
(1,1,'ZAML',3),(2,2,'FDQC',1),(3,3,'ASBB',2),(4,4,'KONI',1);

-- Randomly assign duties for current users (updates linked person rows only)
UPDATE person AS p
SET duty_id = ((random() * 3)::INT + 1)::SMALLINT
FROM users AS u
WHERE u.person_id = p.person_id;

-- Permissions
INSERT INTO permissions (permission_id, user_id, project_id, discipline_id) VALUES 
(1,1,4,NULL),
(2,3,3,NULL);

-- --------------------------------------------------------
-- 2. Sequence Reset (CRITICAL)
-- --------------------------------------------------------
-- Since we manually inserted IDs, we must update the auto-increment sequences
-- so the next INSERT doesn't crash with "Duplicate Key".
SELECT setval(pg_get_serial_sequence('ref.areas', 'area_id'), max(area_id)) FROM ref.areas;
SELECT setval(pg_get_serial_sequence('ref.disciplines', 'discipline_id'), max(discipline_id)) FROM ref.disciplines;
SELECT setval(pg_get_serial_sequence('ref.projects', 'project_id'), max(project_id)) FROM ref.projects;
SELECT setval(pg_get_serial_sequence('ref.units', 'unit_id'), max(unit_id)) FROM ref.units;
SELECT setval(pg_get_serial_sequence('ref.jobpacks', 'jobpack_id'), max(jobpack_id)) FROM ref.jobpacks;
SELECT setval(pg_get_serial_sequence('ref.roles', 'role_id'), max(role_id)) FROM ref.roles;
SELECT setval(pg_get_serial_sequence('ref.revision_overview', 'rev_code_id'), max(rev_code_id)) FROM ref.revision_overview;
SELECT setval(pg_get_serial_sequence('ref.doc_rev_statuses', 'rev_status_id'), max(rev_status_id)) FROM ref.doc_rev_statuses;
SELECT setval(
    pg_get_serial_sequence('ref.doc_rev_milestones', 'milestone_id'),
    (SELECT COALESCE(MAX(milestone_id), 0) FROM ref.doc_rev_milestones),
    true
);
SELECT setval(pg_get_serial_sequence('ref.person_duty', 'duty_id'), max(duty_id)) FROM ref.person_duty;
SELECT setval(pg_get_serial_sequence('ref.person', 'person_id'), max(person_id)) FROM ref.person;
SELECT setval(pg_get_serial_sequence('ref.doc_types', 'type_id'), max(type_id)) FROM ref.doc_types;
SELECT setval(pg_get_serial_sequence('ref.users', 'user_id'), max(user_id)) FROM ref.users;
SELECT setval(pg_get_serial_sequence('ref.permissions', 'permission_id'), max(permission_id)) FROM ref.permissions;
SELECT setval(pg_get_serial_sequence('ref.doc_rev_status_ui_behaviors', 'ui_behavior_id'), max(ui_behavior_id)) FROM ref.doc_rev_status_ui_behaviors;

-- --------------------------------------------------------
-- 3. Generate Fake Documents & Revisions
-- --------------------------------------------------------

DO $$
DECLARE
    i INT;
    v_doc_id INT;
    v_rev_id INT;
    v_project_id INT;
    v_jobpack_id INT;
    v_type_id INT;
    v_area_id INT;
    v_unit_id INT;
    v_doc_name TEXT;
    v_author INT;
    v_rev_code_id INT;
    v_user_id INT;
BEGIN
    SELECT rev_code_id INTO v_rev_code_id
    FROM revision_overview
    WHERE rev_code_acronym = 'A'
    ORDER BY rev_code_id
    LIMIT 1;
    IF v_rev_code_id IS NULL THEN
        v_rev_code_id := 6;
    END IF;

    FOR i IN 1..50 LOOP
        -- 1. Randomly select FKs
        SELECT project_id INTO v_project_id FROM projects ORDER BY random() LIMIT 1;
        SELECT jobpack_id INTO v_jobpack_id FROM jobpacks ORDER BY random() LIMIT 1;
        SELECT type_id INTO v_type_id FROM doc_types ORDER BY random() LIMIT 1;
        SELECT area_id INTO v_area_id FROM areas ORDER BY random() LIMIT 1;
        SELECT unit_id INTO v_unit_id FROM units ORDER BY random() LIMIT 1;
        SELECT person_id INTO v_author FROM person ORDER BY random() LIMIT 1;
        SELECT user_id INTO v_user_id FROM users ORDER BY random() LIMIT 1;
        
        -- 2. Generate Doc Name (e.g., PR-2345-LAY-001)
        v_doc_name := 'DOC-' || lpad(i::text, 4, '0');

        -- 3. Insert document + initial revision via DB function
        PERFORM set_config('app.user', v_user_id::text, true);

        SELECT doc_id, rev_id
        INTO v_doc_id, v_rev_id
        FROM workflow.create_document(
            v_doc_name::VARCHAR(45),
            ('Generated Document Title ' || i)::VARCHAR(45),
            v_project_id::SMALLINT,
            v_jobpack_id::SMALLINT,
            v_type_id::SMALLINT,
            v_area_id::SMALLINT,
            v_unit_id::SMALLINT,
            v_rev_code_id::SMALLINT,
            v_author::SMALLINT,
            v_author::SMALLINT,
            v_author::SMALLINT,
            ('TR-' || lpad(i::text, 2, '0') || '-1')::VARCHAR(45),
            1::SMALLINT,
            NOW()::TIMESTAMPTZ,
            (NOW() + interval '5 days')::TIMESTAMPTZ,
            NULL::TIMESTAMPTZ,
            NULL::TIMESTAMPTZ,
            NULL::TIMESTAMPTZ,
            FALSE
        );

    END LOOP;
END $$;
