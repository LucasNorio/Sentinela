USE sentinela_db;


-- ============================================================
-- SENTINELA v0.4.0
-- Migração: módulo de chamada e presença escolar
--
-- Origem esperada: Sentinela v0.2.0
-- Destino: SENTINELA v0.4.0
--
-- Esta migration deve ser executada apenas uma vez.
-- ============================================================


-- ============================================================
-- 1. VÍNCULO ENTRE USUÁRIO E PROFESSOR
-- ============================================================

ALTER TABLE usuario
ADD COLUMN id_professor INT NULL
AFTER id_usuario;

ALTER TABLE usuario
ADD CONSTRAINT uq_usuario_professor
UNIQUE (id_professor);

ALTER TABLE usuario
ADD CONSTRAINT fk_usuario_professor
FOREIGN KEY (id_professor)
REFERENCES professor(id_professor)
ON UPDATE CASCADE
ON DELETE RESTRICT;


-- ============================================================
-- 2. FUNÇÃO DO PROFESSOR NA TURMA
-- ============================================================

ALTER TABLE professor_turma
ADD COLUMN funcao ENUM(
    'Responsável',
    'Professor',
    'Auxiliar'
) NOT NULL DEFAULT 'Professor'
AFTER id_turma;


-- ============================================================
-- 3. AULAS
-- ============================================================

CREATE TABLE aula (
    id_aula INT AUTO_INCREMENT PRIMARY KEY,

    id_turma INT NOT NULL,
    id_professor INT NOT NULL,
    id_ambiente INT NOT NULL,

    data_aula DATE NOT NULL,

    horario_inicio TIME NOT NULL,
    horario_fim TIME NOT NULL,

    tolerancia_minutos INT NOT NULL DEFAULT 15,

    status ENUM(
        'Programada',
        'Em andamento',
        'Finalizada',
        'Cancelada'
    ) NOT NULL DEFAULT 'Programada',

    criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME NULL,

    cancelada_em DATETIME NULL,
    motivo_cancelamento VARCHAR(255) NULL,

    INDEX idx_aula_data (
        data_aula
    ),

    INDEX idx_aula_status (
        status
    ),

    INDEX idx_aula_turma (
        id_turma
    ),

    INDEX idx_aula_professor (
        id_professor
    ),

    INDEX idx_aula_ambiente (
        id_ambiente
    ),

    INDEX idx_aula_data_horario (
        data_aula,
        horario_inicio,
        horario_fim
    ),

    CONSTRAINT fk_aula_turma
        FOREIGN KEY (id_turma)
        REFERENCES turma(id_turma)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT fk_aula_professor
        FOREIGN KEY (id_professor)
        REFERENCES professor(id_professor)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT fk_aula_ambiente
        FOREIGN KEY (id_ambiente)
        REFERENCES ambiente(id_ambiente)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);


-- ============================================================
-- 4. PRESENÇAS
-- ============================================================

CREATE TABLE presenca (
    id_presenca INT AUTO_INCREMENT PRIMARY KEY,

    id_aula INT NOT NULL,
    id_aluno INT NOT NULL,

    id_registro_rfid INT NULL,

    status ENUM(
        'Pendente',
        'Presente',
        'Atrasado',
        'Ausente',
        'Justificado'
    ) NOT NULL DEFAULT 'Pendente',

    origem ENUM(
        'Sistema',
        'RFID',
        'Correção'
    ) NOT NULL DEFAULT 'Sistema',

    horario_detectado DATETIME NULL,

    observacao VARCHAR(255) NULL,

    criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME NULL,

    CONSTRAINT uq_presenca_aula_aluno
        UNIQUE (
            id_aula,
            id_aluno
        ),

    INDEX idx_presenca_aula (
        id_aula
    ),

    INDEX idx_presenca_aluno (
        id_aluno
    ),

    INDEX idx_presenca_status (
        status
    ),

    INDEX idx_presenca_registro_rfid (
        id_registro_rfid
    ),

    CONSTRAINT fk_presenca_aula
        FOREIGN KEY (id_aula)
        REFERENCES aula(id_aula)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT fk_presenca_aluno
        FOREIGN KEY (id_aluno)
        REFERENCES aluno(id_aluno)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT fk_presenca_registro_rfid
        FOREIGN KEY (id_registro_rfid)
        REFERENCES registro_rfid(id_registro)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);


-- ============================================================
-- 5. AUDITORIA DE CORREÇÕES DE PRESENÇA
-- ============================================================

CREATE TABLE ajuste_presenca (
    id_ajuste_presenca INT AUTO_INCREMENT PRIMARY KEY,

    id_presenca INT NOT NULL,
    id_usuario INT NOT NULL,

    status_anterior ENUM(
        'Pendente',
        'Presente',
        'Atrasado',
        'Ausente',
        'Justificado'
    ) NOT NULL,

    status_novo ENUM(
        'Pendente',
        'Presente',
        'Atrasado',
        'Ausente',
        'Justificado'
    ) NOT NULL,

    motivo VARCHAR(255) NOT NULL,

    criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_ajuste_presenca (
        id_presenca
    ),

    INDEX idx_ajuste_usuario (
        id_usuario
    ),

    INDEX idx_ajuste_criado_em (
        criado_em
    ),

    CONSTRAINT fk_ajuste_presenca
        FOREIGN KEY (id_presenca)
        REFERENCES presenca(id_presenca)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT fk_ajuste_usuario
        FOREIGN KEY (id_usuario)
        REFERENCES usuario(id_usuario)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);
