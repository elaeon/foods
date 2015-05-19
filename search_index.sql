
---- Fast search
DROP MATERIALIZED VIEW searchall_index;
DROP INDEX idx_fts_searchall;

CREATE MATERIALIZED VIEW searchall_index AS 
(SELECT ndb_no, long_desc, long_desc_es, setweight(to_tsvector('spanish', coalesce(unaccent(long_desc_es), '')), 'A') as document 
FROM food_des);

CREATE INDEX idx_fts_searchall ON searchall_index USING gin(document);

---- Fuzzy search
CREATE MATERIALIZED VIEW unique_lexeme AS SELECT word FROM ts_stat(
'(SELECT to_tsvector(''simple'', coalesce(unaccent(long_desc_es), '''')) as document 
FROM food_des)');

CREATE INDEX words_idx ON unique_lexeme USING gin(word gin_trgm_ops);



-- search fast
SELECT long_desc_es
        FROM searchall_index
        WHERE document @@ to_tsquery('spanish', 'queso')
        ORDER BY ts_rank(document, to_tsquery('spanish', 'queso')) DESC LIMIT 10;

SELECT long_desc_es
        FROM searchall_index, to_tsquery('spanish', 'queso') as query
        WHERE document @@ query
        ORDER BY ts_rank_cd(document, query) DESC LIMIT 10;

-- search fuzzy
SELECT word, similarity(word, 'quso') as dist
    FROM unique_lexeme
    WHERE similarity(word, 'quso') > 0
    ORDER BY dist DESC LIMIT 10;

SELECT word, word <-> 'quso' as dist
    FROM unique_lexeme
    WHERE  word <-> 'queo' < 1
    ORDER BY dist LIMIT 10;

SELECT ts_rank_cd(document, query), searchall_index.ndb_no, searchall_index.long_desc_es FROM 
(SELECT word
    FROM unique_lexeme
    WHERE  word <-> 'queo' < 1
    ORDER BY word <-> 'queo' LIMIT 10) as words, searchall_index, to_tsquery('spanish', words.word) as query
WHERE document @@ query
ORDER BY ts_rank_cd(document, query);

