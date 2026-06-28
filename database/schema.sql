CREATE DATABASE IF NOT EXISTS sentinela_db
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE sentinela_db;

CREATE TABLE IF NOT EXISTS curso (
  id_curso INT AUTO_INCREMENT PRIMARY KEY,
  nome VARCHAR(120) NOT NULL,
  codigo VARCHAR(20) NOT NULL UNIQUE,
  status ENUM('Ativo', 'Inativo') NOT NULL DEFAULT 'Ativo',
  criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  inativado_em DATETIME NULL,
  motivo_inativacao VARCHAR(255) NULL
);

CREATE TABLE IF NOT EXISTS turma (
  id_turma INT AUTO_INCREMENT PRIMARY KEY,
  id_curso INT NOT NULL,
  nome VARCHAR(120) NOT NULL,
  periodo ENUM('Manhã', 'Tarde', 'Noite', 'Integral') NOT NULL,
  ano_letivo INT NOT NULL,
  semestre INT NOT NULL,
  status ENUM('Ativa', 'Inativa', 'Encerrada') NOT NULL DEFAULT 'Ativa',
  criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  inativada_em DATETIME NULL,
  motivo_inativacao VARCHAR(255) NULL,
  encerrada_em DATETIME NULL,
  motivo_encerramento VARCHAR(255) NULL,
  CONSTRAINT fk_turma_curso
    FOREIGN KEY (id_curso) REFERENCES curso(id_curso)
    ON UPDATE CASCADE
    ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS aluno (
  id_aluno INT AUTO_INCREMENT PRIMARY KEY,
  nome VARCHAR(120) NOT NULL,
  matricula VARCHAR(40) NOT NULL UNIQUE,
  email VARCHAR(120) NULL UNIQUE,
  data_nascimento DATE NULL,
  id_turma INT NOT NULL,
  status ENUM('Ativo', 'Inativo') NOT NULL DEFAULT 'Ativo',
  criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  inativado_em DATETIME NULL,
  motivo_inativacao VARCHAR(255) NULL,
  CONSTRAINT fk_aluno_turma
    FOREIGN KEY (id_turma) REFERENCES turma(id_turma)
    ON UPDATE CASCADE
    ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS tag_rfid (
  id_tag INT AUTO_INCREMENT PRIMARY KEY,
  codigo VARCHAR(100) NOT NULL UNIQUE,
  id_aluno INT NOT NULL,
  status ENUM('Ativa', 'Inativa', 'Bloqueada', 'Perdida') NOT NULL DEFAULT 'Ativa',
  data_vinculo DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  inativada_em DATETIME NULL,
  CONSTRAINT fk_tag_aluno
    FOREIGN KEY (id_aluno) REFERENCES aluno(id_aluno)
    ON UPDATE CASCADE
    ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS professor (
  id_professor INT AUTO_INCREMENT PRIMARY KEY,
  nome VARCHAR(120) NOT NULL,
  email VARCHAR(120) NOT NULL UNIQUE,
  registro_professor VARCHAR(50) NOT NULL UNIQUE,
  area VARCHAR(120) NOT NULL,
  telefone VARCHAR(20) NULL,
  status ENUM('Ativo', 'Inativo') NOT NULL DEFAULT 'Ativo',
  criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  inativado_em DATETIME NULL,
  motivo_inativacao VARCHAR(255) NULL
);

CREATE TABLE IF NOT EXISTS professor_turma (
  id_professor_turma INT AUTO_INCREMENT PRIMARY KEY,
  id_professor INT NOT NULL,
  id_turma INT NOT NULL,
  funcao ENUM('Responsável', 'Professor', 'Auxiliar') NOT NULL DEFAULT 'Professor',
  status ENUM('Ativo', 'Inativo') NOT NULL DEFAULT 'Ativo',
  criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  inativado_em DATETIME NULL,
  motivo_inativacao VARCHAR(255) NULL,
  CONSTRAINT fk_professor_turma_professor
    FOREIGN KEY (id_professor) REFERENCES professor(id_professor)
    ON UPDATE CASCADE
    ON DELETE RESTRICT,
  CONSTRAINT fk_professor_turma_turma
    FOREIGN KEY (id_turma) REFERENCES turma(id_turma)
    ON UPDATE CASCADE
    ON DELETE RESTRICT,
  CONSTRAINT uq_professor_turma
    UNIQUE (id_professor, id_turma)
);

CREATE TABLE IF NOT EXISTS ambiente (
  id_ambiente INT AUTO_INCREMENT PRIMARY KEY,
  nome VARCHAR(120) NOT NULL,
  bloco VARCHAR(80) NOT NULL,
  tipo ENUM(
    'Portaria',
    'Sala',
    'Laboratório',
    'Biblioteca',
    'Oficina',
    'Pátio',
    'Secretaria',
    'Coordenação',
    'Área comum',
    'Outro'
  ) NOT NULL,
  capacidade INT NULL,
  status ENUM('Ativo', 'Inativo', 'Manutenção') NOT NULL DEFAULT 'Ativo',
  criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  inativado_em DATETIME NULL,
  motivo_inativacao VARCHAR(255) NULL,
  manutencao_em DATETIME NULL,
  motivo_manutencao VARCHAR(255) NULL
);

CREATE TABLE IF NOT EXISTS leitor_rfid (
  id_leitor INT AUTO_INCREMENT PRIMARY KEY,
  codigo_identificacao VARCHAR(80) NOT NULL UNIQUE,
  tipo_leitor ENUM('Entrada', 'Saída', 'Entrada/Saída', 'Interno', 'Outro') NOT NULL DEFAULT 'Interno',
  nome VARCHAR(120) NOT NULL,
  id_ambiente INT NOT NULL,
  status ENUM('Ativo', 'Inativo', 'Manutenção') NOT NULL DEFAULT 'Ativo',
  instalado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  ultima_comunicacao DATETIME NULL,
  inativado_em DATETIME NULL,
  motivo_inativacao VARCHAR(255) NULL,
  manutencao_em DATETIME NULL,
  motivo_manutencao VARCHAR(255) NULL,
  CONSTRAINT fk_leitor_rfid_ambiente
    FOREIGN KEY (id_ambiente) REFERENCES ambiente(id_ambiente)
    ON UPDATE CASCADE
    ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS registro_rfid (
  id_registro INT AUTO_INCREMENT PRIMARY KEY,
  codigo_tag_lida VARCHAR(100) NOT NULL,
  id_tag INT NULL,
  id_aluno INT NULL,
  id_leitor INT NOT NULL,
  id_ambiente INT NOT NULL,
  tipo ENUM('Entrada', 'Saída', 'Movimentação', 'Alerta') NOT NULL,
  data_hora DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  observacao VARCHAR(255) NULL,
  INDEX idx_registro_data_hora (data_hora),
  INDEX idx_registro_tipo (tipo),
  INDEX idx_registro_aluno (id_aluno),
  INDEX idx_registro_leitor (id_leitor),
  INDEX idx_registro_ambiente (id_ambiente),
  CONSTRAINT fk_registro_tag
    FOREIGN KEY (id_tag) REFERENCES tag_rfid(id_tag)
    ON UPDATE CASCADE
    ON DELETE RESTRICT,
  CONSTRAINT fk_registro_aluno
    FOREIGN KEY (id_aluno) REFERENCES aluno(id_aluno)
    ON UPDATE CASCADE
    ON DELETE RESTRICT,
  CONSTRAINT fk_registro_leitor
    FOREIGN KEY (id_leitor) REFERENCES leitor_rfid(id_leitor)
    ON UPDATE CASCADE
    ON DELETE RESTRICT,
  CONSTRAINT fk_registro_ambiente
    FOREIGN KEY (id_ambiente) REFERENCES ambiente(id_ambiente)
    ON UPDATE CASCADE
    ON DELETE RESTRICT
);
