def fuzzy_query(pg_version, term, ordering=True, headline=False):
    if headline and pg_version == "9.1":
        headline = "ts_headline('spanish', searchall_index.long_desc_es, to_tsquery('spanish', words.word)) as name"
    elif headline and pg_version != "9.1":
        headline = "ts_headline('spanish', searchall_index.long_desc_es, query) as name"
    else:
        headline = "searchall_index.long_desc_es as name"

    if pg_version == "9.1":
        query = """
            (SELECT DISTINCT searchall_index.ndb_no, {headline}, ts_rank_cd(document, to_tsquery('spanish', words.word)) as r FROM 
            (SELECT word
                FROM unique_lexeme
                WHERE  word <-> '{term}' < 1
                ORDER BY word <-> '{term}' LIMIT 2) as words, searchall_index
            WHERE document @@ to_tsquery('spanish', words.word))
                    """.format(headline=headline, term=term)
    else:
        query = """
            (SELECT DISTINCT searchall_index.ndb_no, searchall_index.long_desc_es as name, ts_rank_cd(document, query) as r FROM 
            (SELECT word
                FROM unique_lexeme
                WHERE  word <-> '{term}' < 1
                ORDER BY word <-> '{term}' LIMIT 2) as words, searchall_index, to_tsquery('spanish', words.word) as query
            WHERE document @@ query)""".format(headline=headline, term=term)

    if ordering:
        query += " ORDER BY r, name"

    return query
