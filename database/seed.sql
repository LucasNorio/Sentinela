USE sentinela_db;

INSERT INTO curso (nome, codigo, status) VALUES
  ('Administração', 'ADM', 'Ativo'),
  ('Desenvolvimento de Sistemas', 'DS', 'Ativo'),
  ('Eletroeletrônica', 'ELETRO', 'Ativo'),
  ('Mecânica', 'MEC', 'Ativo')
ON DUPLICATE KEY UPDATE
  nome = VALUES(nome),
  status = VALUES(status);