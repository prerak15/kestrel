-- Kestrel: Stack Exchange posts (questions and answers).
-- Source: serverfault.com.7z, dump 2024-04-06. See data/manifest.json.
-- All timestamps are UTC. Stored as TIMESTAMP (no tz) so Postgres
-- does not reinterpret them in the session timezone.

DROP TABLE IF EXISTS posts;

CREATE TABLE posts (
    id                  INT PRIMARY KEY,
    post_type_id        SMALLINT  NOT NULL,
    creation_date       TIMESTAMP NOT NULL,
    score               INT,
    body                TEXT,
    comment_count       INT,
    content_license     TEXT,
    accepted_answer_id  INT,
    view_count          INT,
    title               TEXT,
    tags                TEXT[],
    answer_count        INT,
    parent_id           INT,
    owner_user_id       INT,
    owner_display_name  TEXT,
    closed_date         TIMESTAMP,
    favorite_count      INT
);
