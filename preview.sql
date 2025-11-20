CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL, 
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Running upgrade  -> 84eef2bb1c4f

-- offline preview: guarded migration; run in online mode for inspection-aware DDL;

INSERT INTO alembic_version (version_num) VALUES ('84eef2bb1c4f') RETURNING version_num;

