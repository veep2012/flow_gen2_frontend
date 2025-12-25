-- ========================================================
-- POSTGRESQL SEED DATA SCRIPT FOR FLOW
-- ========================================================
-- 1. Populates lookup tables from your 5_base_content.sql
-- 2. Generates fake Documents and Revisions for testing
-- ========================================================

SET search_path TO flow;

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

-- Person
INSERT INTO person (person_id, person_name, photo_s3_uid) VALUES 
(1,'ZHANDOS MYLTYKBAYEV',NULL),(2,'ALEKSEY KRUTSKIH',NULL),
(3,'ASYLKHAN BOKHAYEV',NULL),(4,'KONSTANTIN NI',NULL),
(5,'IVANOV IVANOV',NULL);

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

-- Rev Statuses
INSERT INTO doc_rev_statuses (rev_status_id, rev_status_name) VALUES 
(1,'in progress'),(2,'not started'),(3,'done');

-- Roles
INSERT INTO roles (role_id, role_name) VALUES 
(1,'SuperUser'),(2,'User/DCC'),(3,'Limited User');

-- Users
INSERT INTO users (user_id, person_id, user_acronym, role_id) VALUES 
(1,1,'ZAML',3),(2,2,'FDQC',1),(3,3,'ASBB',2),(4,4,'KONI',1);

-- Permissions
INSERT INTO permissions (permission_id, user_id, project_id, discipline_id) VALUES 
(1,1,4,NULL),
(2,3,3,NULL);

-- --------------------------------------------------------
-- 2. Sequence Reset (CRITICAL)
-- --------------------------------------------------------
-- Since we manually inserted IDs, we must update the auto-increment sequences
-- so the next INSERT doesn't crash with "Duplicate Key".
SELECT setval(pg_get_serial_sequence('areas', 'area_id'), max(area_id)) FROM areas;
SELECT setval(pg_get_serial_sequence('disciplines', 'discipline_id'), max(discipline_id)) FROM disciplines;
SELECT setval(pg_get_serial_sequence('projects', 'project_id'), max(project_id)) FROM projects;
SELECT setval(pg_get_serial_sequence('units', 'unit_id'), max(unit_id)) FROM units;
SELECT setval(pg_get_serial_sequence('jobpacks', 'jobpack_id'), max(jobpack_id)) FROM jobpacks;
SELECT setval(pg_get_serial_sequence('roles', 'role_id'), max(role_id)) FROM roles;
SELECT setval(pg_get_serial_sequence('revision_overview', 'rev_code_id'), max(rev_code_id)) FROM revision_overview;
SELECT setval(pg_get_serial_sequence('doc_rev_statuses', 'rev_status_id'), max(rev_status_id)) FROM doc_rev_statuses;
SELECT setval(pg_get_serial_sequence('doc_rev_milestones', 'milestone_id'), max(milestone_id)) FROM doc_rev_milestones;
SELECT setval(pg_get_serial_sequence('person', 'person_id'), max(person_id)) FROM person;
SELECT setval(pg_get_serial_sequence('doc_types', 'type_id'), max(type_id)) FROM doc_types;
SELECT setval(pg_get_serial_sequence('users', 'user_id'), max(user_id)) FROM users;
SELECT setval(pg_get_serial_sequence('permissions', 'permission_id'), max(permission_id)) FROM permissions;

-- --------------------------------------------------------
-- 3. Generate Fake Documents & Revisions
-- --------------------------------------------------------

DO $$
DECLARE
    i INT;
    v_doc_id INT;
    v_project_id INT;
    v_jobpack_id INT;
    v_type_id INT;
    v_area_id INT;
    v_unit_id INT;
    v_doc_name TEXT;
    v_author INT;
BEGIN
    FOR i IN 1..50 LOOP
        -- 1. Randomly select FKs
        SELECT project_id INTO v_project_id FROM projects ORDER BY random() LIMIT 1;
        SELECT jobpack_id INTO v_jobpack_id FROM jobpacks ORDER BY random() LIMIT 1;
        SELECT type_id INTO v_type_id FROM doc_types ORDER BY random() LIMIT 1;
        SELECT area_id INTO v_area_id FROM areas ORDER BY random() LIMIT 1;
        SELECT unit_id INTO v_unit_id FROM units ORDER BY random() LIMIT 1;
        SELECT person_id INTO v_author FROM person ORDER BY random() LIMIT 1;
        
        -- 2. Generate Doc Name (e.g., PR-2345-LAY-001)
        v_doc_name := 'DOC-' || lpad(i::text, 4, '0');

        -- 3. Insert Document (Triggers will handle the rev_current_id pointer updates later)
        INSERT INTO doc (doc_name_unique, title, project_id, jobpack_id, type_id, area_id, unit_id)
        VALUES (
            v_doc_name, 
            'Generated Document Title ' || i,
            v_project_id, v_jobpack_id, v_type_id, v_area_id, v_unit_id
        ) RETURNING doc_id INTO v_doc_id;

        -- 4. Insert Initial Revision (Rev A)
        -- Note: The trigger 'tr_doc_revision_after_insert' defined in the schema 
        -- will automatically update 'doc.rev_current_id' to point to this new revision.
        INSERT INTO doc_revision (
            rev_code_id, rev_date, rev_author_id, rev_originator_id, 
            transmittal_current_revision, milestone_id, 
            planned_start_date, planned_finish_date, 
            rev_status_id, doc_id, seq_num
        ) VALUES (
            6, -- INDESIGN (A)
            NOW() - (random() * interval '30 days'),
            v_author, v_author,
            'TR-00' || i,
            1, -- Issued for Construction
            NOW(), NOW() + interval '5 days',
            1, -- In Progress
            v_doc_id,
            1
        );

        -- 5. Randomly add a second revision (Rev B) for some docs
        IF (random() > 0.5) THEN
            INSERT INTO doc_revision (
                rev_code_id, rev_date, rev_author_id, rev_originator_id, 
                transmittal_current_revision, milestone_id, 
                planned_start_date, planned_finish_date, 
                rev_status_id, doc_id, seq_num
            ) VALUES (
                1, -- IDC (B)
                NOW(),
                v_author, v_author,
                'TR-01' || i,
                2, 
                NOW(), NOW() + interval '10 days',
                3, -- Done
                v_doc_id,
                2
            );
        END IF;

    END LOOP;
END $$;
