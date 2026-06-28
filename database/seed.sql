USE sentinela_db;

INSERT INTO curso (nome, codigo) VALUES
  ('Administração', 'ADM'),
  ('Desenvolvimento de Sistemas', 'DS'),
  ('Eletroeletrônica', 'ELETRO'),
  ('Mecânica', 'MEC')
ON DUPLICATE KEY UPDATE nome = VALUES(nome);
