create database HistorialCursos

use HistorialCursos

-- 1. Tabla de Catálogo de Cursos
CREATE TABLE courses (
    course_id INTEGER IDENTITY(1,1) PRIMARY KEY,
    course_name NVARCHAR(255) UNIQUE NOT NULL      -- Ej: 'Programacion_desde_0_Parte_1'
);

-- 2. Tabla de Estados del Flujo Único (Adelina/Eleodoro)
CREATE TABLE stages (
    stage_id INTEGER IDENTITY(1,1) PRIMARY KEY,
    stage_name NVARCHAR(255) UNIQUE NOT NULL        -- 'ADELINA_TEORIA', 'ELEODORO_EVALUACION'
);

-- 3. Tabla Relacional de Progreso (Registro al Vuelo)
CREATE TABLE student_progress (
    user_email NVARCHAR(255) PRIMARY KEY,              -- El email o ID invisible del Token
    current_course_id INTEGER NOT NULL,
    current_stage_id INTEGER NOT NULL,
    updated_at DATETIME NOT NULL,
    FOREIGN KEY (current_course_id) REFERENCES courses(course_id),
    FOREIGN KEY (current_stage_id) REFERENCES stages(stage_id)
);