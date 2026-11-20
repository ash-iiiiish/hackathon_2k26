-- Prepwise schema. Safe to run repeatedly.

CREATE TABLE IF NOT EXISTS students (
    id              SERIAL PRIMARY KEY,
    name            TEXT NOT NULL,
    email           TEXT,
    exam_name       TEXT DEFAULT 'Final exam',
    exam_date       DATE,
    daily_hours     REAL NOT NULL DEFAULT 3,
    study_start     TIME NOT NULL DEFAULT '17:00',
    sleep_time      TIME NOT NULL DEFAULT '23:00',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS subjects (
    id          SERIAL PRIMARY KEY,
    student_id  INT NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    name        TEXT NOT NULL,
    color       TEXT NOT NULL DEFAULT '#3D6BF5',
    UNIQUE (student_id, name)
);

CREATE TABLE IF NOT EXISTS topics (
    id              SERIAL PRIMARY KEY,
    student_id      INT NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    subject_id      INT REFERENCES subjects(id) ON DELETE SET NULL,
    title           TEXT NOT NULL,
    description     TEXT DEFAULT '',
    weightage       REAL NOT NULL DEFAULT 3,      -- 1..5 exam importance
    difficulty      REAL NOT NULL DEFAULT 2,      -- 1..3
    est_minutes     INT  NOT NULL DEFAULT 45,     -- time to learn from scratch
    mastery         REAL NOT NULL DEFAULT 0,      -- 0..100
    last_studied    TIMESTAMPTZ,
    times_studied   INT NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (student_id, title)
);

CREATE TABLE IF NOT EXISTS mastery_history (
    id          SERIAL PRIMARY KEY,
    topic_id    INT NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
    mastery     REAL NOT NULL,
    source      TEXT NOT NULL DEFAULT 'manual',
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Uploaded study material (the RAG corpus)
CREATE TABLE IF NOT EXISTS documents (
    id          SERIAL PRIMARY KEY,
    student_id  INT NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    subject_id  INT REFERENCES subjects(id) ON DELETE SET NULL,
    title       TEXT NOT NULL,
    filename    TEXT,
    kind        TEXT NOT NULL DEFAULT 'text',
    size_bytes  INT NOT NULL DEFAULT 0,
    content     TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS chunks (
    id          SERIAL PRIMARY KEY,
    document_id INT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    student_id  INT NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    idx         INT NOT NULL,
    heading     TEXT DEFAULT '',
    content     TEXT NOT NULL,
    tsv         TSVECTOR GENERATED ALWAYS AS (
                    setweight(to_tsvector('english', coalesce(heading, '')), 'A') ||
                    setweight(to_tsvector('english', content), 'B')
                ) STORED
);
CREATE INDEX IF NOT EXISTS chunks_tsv_idx ON chunks USING GIN (tsv);
CREATE INDEX IF NOT EXISTS chunks_student_idx ON chunks (student_id);

-- Notion-style pages
CREATE TABLE IF NOT EXISTS notes (
    id          SERIAL PRIMARY KEY,
    student_id  INT NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    parent_id   INT REFERENCES notes(id) ON DELETE CASCADE,
    subject_id  INT REFERENCES subjects(id) ON DELETE SET NULL,
    title       TEXT NOT NULL DEFAULT 'Untitled',
    icon        TEXT NOT NULL DEFAULT '',
    content     TEXT NOT NULL DEFAULT '',
    tags        TEXT[] NOT NULL DEFAULT '{}',
    pinned      BOOLEAN NOT NULL DEFAULT false,
    position    INT NOT NULL DEFAULT 0,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS mindmaps (
    id          SERIAL PRIMARY KEY,
    student_id  INT NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    document_id INT REFERENCES documents(id) ON DELETE SET NULL,
    title       TEXT NOT NULL,
    data        JSONB NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS roadmaps (
    id          SERIAL PRIMARY KEY,
    student_id  INT NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    mode        TEXT NOT NULL,                 -- 'standard' | 'crisis'
    exam_date   DATE,
    summary     JSONB NOT NULL DEFAULT '{}',
    active      BOOLEAN NOT NULL DEFAULT true,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Calendar: study blocks, revisions, breaks, reminders, exams
CREATE TABLE IF NOT EXISTS events (
    id              SERIAL PRIMARY KEY,
    student_id      INT NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    roadmap_id      INT REFERENCES roadmaps(id) ON DELETE CASCADE,
    topic_id        INT REFERENCES topics(id) ON DELETE SET NULL,
    title           TEXT NOT NULL,
    kind            TEXT NOT NULL DEFAULT 'study',   -- study|revise|practice|break|exam|reminder
    phase           TEXT DEFAULT '',
    start_at        TIMESTAMP NOT NULL,
    end_at          TIMESTAMP NOT NULL,
    remind_before   INT NOT NULL DEFAULT 10,         -- minutes
    status          TEXT NOT NULL DEFAULT 'planned', -- planned|done|skipped
    notes           TEXT DEFAULT ''
);
CREATE INDEX IF NOT EXISTS events_student_time_idx ON events (student_id, start_at);

CREATE TABLE IF NOT EXISTS chats (
    id          SERIAL PRIMARY KEY,
    student_id  INT NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    title       TEXT NOT NULL DEFAULT 'New chat',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS messages (
    id          SERIAL PRIMARY KEY,
    chat_id     INT NOT NULL REFERENCES chats(id) ON DELETE CASCADE,
    role        TEXT NOT NULL,
    content     TEXT NOT NULL,
    meta        JSONB NOT NULL DEFAULT '{}',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS study_sessions (
    id          SERIAL PRIMARY KEY,
    student_id  INT NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    topic_id    INT REFERENCES topics(id) ON DELETE SET NULL,
    event_id    INT REFERENCES events(id) ON DELETE SET NULL,
    minutes     INT NOT NULL,
    kind        TEXT NOT NULL DEFAULT 'study',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS quiz_attempts (
    id          SERIAL PRIMARY KEY,
    student_id  INT NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    topic_id    INT REFERENCES topics(id) ON DELETE SET NULL,
    score       INT NOT NULL,
    total       INT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
