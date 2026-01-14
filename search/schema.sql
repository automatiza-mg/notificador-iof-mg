CREATE TABLE IF NOT EXISTS documentos (
    id INTEGER PRIMARY KEY,
    titulo TEXT NOT NULL,
    num_pagina INTEGER NOT NULL,
    descricao TEXT NOT NULL,
    conteudo TEXT NOT NULL,
    data_publicacao TIMESTAMP NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_documentos_data_publicacao_num_pagina ON documentos(data_publicacao, num_pagina);

CREATE VIRTUAL TABLE IF NOT EXISTS documentos_fts USING fts5(
    conteudo,
    content='documentos',
    content_rowid='id'
);

CREATE TRIGGER IF NOT EXISTS documentos_ai AFTER INSERT ON documentos BEGIN
  INSERT INTO documentos_fts(rowid, conteudo)
  VALUES (new.id, new.conteudo);
END;

CREATE TRIGGER IF NOT EXISTS documentos_ad AFTER DELETE ON documentos BEGIN
  INSERT INTO documentos_fts(documentos_fts, rowid) VALUES('delete', old.id);
END;

CREATE TRIGGER IF NOT EXISTS documentos_au AFTER UPDATE ON documentos BEGIN
  INSERT INTO documentos_fts(documentos_fts, rowid) VALUES('delete', old.id);
  INSERT INTO documentos_fts(rowid, conteudo)
  VALUES (new.id, new.conteudo);
END;

