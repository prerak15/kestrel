-- Kestrel: indexes on the loaded Stack Exchange tables.
-- Built AFTER the load, not in schema.sql: keeping indexes up to date
-- during 3M inserts is slower than building each one once at the end.
--
-- Rule: only index a column that appears in a WHERE or JOIN of a query
-- we actually run, and only if a typical value matches a small share of
-- the table. Primary keys (id) are already indexed automatically.

-- Find the answers to a question: answers.parent_id = question.id
-- Measured before this index: 399 ms, scanning all 844,092 posts.
CREATE INDEX IF NOT EXISTS idx_posts_parent_id ON posts (parent_id);

-- Get one post's edit history: ~2.6 matching rows out of 2,187,478.
CREATE INDEX IF NOT EXISTS idx_posthistory_post_id ON posthistory (post_id);

-- Deliberately NOT indexed:
--   posts.post_type_id        two values cover 99.5% of rows, so Postgres would scan anyway
--   posts.creation_date       the temporal split selects a large share of rows; a scan is faster
--   posts.accepted_answer_id  the lookup goes q.accepted_answer_id -> posts.id, the primary key
--   postlinks (any column)    35,699 rows; a full scan takes a few milliseconds

-- Refresh table statistics so the planner knows about the new indexes.
ANALYZE;
