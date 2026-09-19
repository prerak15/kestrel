-- Kestrel: Stack Exchange tables loaded from the Server Fault dump.
-- Source: serverfault.com.7z, dump 2024-04-06. See data/manifest.json.
-- All timestamps are UTC. Stored as TIMESTAMP (no tz) so Postgres
-- does not reinterpret them in the session timezone.
--
-- No foreign keys, deliberately: the XML is not in dependency order
-- (an answer can appear before its question), and some rows point to
-- posts that were deleted before the dump was taken.

-- posts: every row of Posts.xml, all post types.
-- post_type_id 1 = question, 2 = answer. Types 3-7 are tag wikis,
-- moderator nominations and placeholders; filter with post_type_id IN (1, 2).
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

-- postlinks: every row of PostLinks.xml.
-- link_type_id 1 = linked (someone referenced the other post; weak signal),
--              3 = duplicate (closed as a duplicate; strong relevance label).
-- For duplicates, post_id is the duplicate (closed) question and
-- related_post_id is the original it was closed against.
DROP TABLE IF EXISTS postlinks;

CREATE TABLE postlinks (
    id                  INT PRIMARY KEY,
    creation_date       TIMESTAMP NOT NULL,
    post_id             INT       NOT NULL,
    related_post_id     INT       NOT NULL,
    link_type_id        SMALLINT  NOT NULL
);
