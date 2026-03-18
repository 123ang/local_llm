# UUM Data & LLM Question Suggestions

This document describes the UUM database content (`uum_db.sql`), the imported tables used by the AskAI assistant, and suggested questions users can ask the LLM.

---

## 1. Data source

- **File:** `uum_db.sql`
- **Origin:** phpMyAdmin dump from MariaDB (UUM database)
- **Import:** Script `investment/fix_uum_import.py` loads the SQL into the app’s PostgreSQL DB under company **UUM utlc** (Company ID: 2).
- **Post-import tables:** `c2_comments`, `c2_staff` (prefix `c2_` = company 2).

---

## 2. Comments table (student / course feedback)

**Display name:** `comments`  
**PostgreSQL table:** `c2_comments`  
**Row count:** 37,453

Student evaluation feedback: one row per student comment, linked to a course and lecturer.

| Column          | Type        | Description |
|-----------------|------------|-------------|
| `id`            | BIGSERIAL  | Primary key |
| `no`            | INTEGER    | Sequence number |
| `pp`            | VARCHAR(16)| Faculty/school code (e.g. SEFB, IBS, SoL) |
| `course_id`     | VARCHAR(32)| Course code (e.g. BECA1013, BWFF2033) |
| `course_name`   | VARCHAR(255)| Course title (e.g. BIOLOGI, PENGURUSAN KEWANGAN) |
| `level`         | INTEGER    | Level (1000, 2000, 3000) |
| `student_group` | VARCHAR(100)| Group (e.g. A, B, C) |
| `lecturer_name` | VARCHAR(255)| Lecturer full name |
| `staff_no`      | VARCHAR(32)| Staff number |
| `post`          | VARCHAR(255)| Post title (e.g. Pensyarah Universiti DS51) |
| `form`          | VARCHAR(64)| Form version (e.g. SG_v2, LG_v2) |
| `enrolled`      | INTEGER    | Number enrolled |
| `evaluated`     | INTEGER    | Number evaluated |
| `percentage`    | DECIMAL(6,2)| Evaluation percentage (e.g. 99.20) |
| `comment_text`  | TEXT       | Free-text student comment |
| `imported_at`   | TIMESTAMP  | Import time |

---

## 3. Staff table (staff directory)

**Display name:** `staff`  
**PostgreSQL table:** `c2_staff`  
**Row count:** 6,475

Staff directory snapshot (e.g. 2023): one row per staff member with role and school.

| Column                    | Type        | Description |
|---------------------------|------------|-------------|
| `id`                      | BIGSERIAL  | Primary key |
| `trend_date_year`         | INTEGER    | Year (e.g. 2023) |
| `tarikh_proses_data_staf` | DATE       | Data process date |
| `total_staff_snapshot`    | INTEGER    | Total staff in snapshot |
| `status_umum`             | VARCHAR(64)| General status (e.g. Berkhidmat) |
| `no_staf`                 | VARCHAR(32)| Staff number |
| `nama_staf_dan_gelaran`   | VARCHAR(255)| Full name and title |
| `status_perkhidmatan`     | VARCHAR(64)| Service status (e.g. Aktif) |
| `tarikh_lapor_uum`        | DATE       | Date reported to UUM |
| `jawatan_akademik`        | VARCHAR(128)| Academic position (e.g. Profesor, Pensyarah Kanan, Pentadbiran) |
| `jawatan_hakiki_penuh`    | VARCHAR(255)| Full substantive post |
| `jawatan_semasa_penuh`    | VARCHAR(255)| Full current post |
| `jawatan_semasa_singkatan`| VARCHAR(128)| Short current post (e.g. Prof Madya, Dekan) |
| `pusat_pengajian`         | VARCHAR(128)| School/centre (e.g. SBM, SEFB, SoE, Lain-lain) |
| `bil_staf_trend`          | INTEGER    | Trend count |
| `imported_at`             | TIMESTAMP  | Import time |

---

## 4. What was implemented

- **Import & parser:** `uum_db.sql` is parsed (quote-aware split, CREATE+INSERT in same block, VALUES span) and loaded into PostgreSQL via `fix_uum_import.py`. Default timestamp is applied when `imported_at` is missing.
- **Assistant UI:** When the chat is empty, the Assistant page shows **“Try asking”** with clickable suggestion chips that fill the input.
- **SQL hints:** In `backend/app/llm/unified_query.py`, the text-to-SQL prompt gets short semantic hints for tables whose display name contains “comment” or “staff”, and an extra rule for “what do students say” / feedback-style questions so the model uses the comments table and columns like `comment_text`, `lecturer_name`, `course_name`.

---

## 5. Suggested questions (shown in the Assistant UI)

These six suggestions appear as **“Try asking”** chips on the Assistant page when there are no messages. Clicking a chip fills the input; the user can edit or send.

1. **Which lecturers have the highest evaluation percentage?**
2. **Show me student comments for a course**
3. **List staff by school or department**
4. **What do students say about teaching quality?**
5. **How many students were evaluated per course?**
6. **What data or tables do we have?**

They target the **comments** table (evaluation %, comment_text, lecturer, course) and **staff** table (school/department, name, role). On other companies they may return no rows but still illustrate the kinds of questions the assistant supports.

---

## 6. SQL / LLM prompt hints (backend)

In `unified_query.py`, when building the text-to-SQL prompt:

- **Comments-style table** (display name contains “comment”): hint that the table is student/course feedback and to use `course_id`, `course_name`, `lecturer_name`, `percentage`, `comment_text` for evaluation or “what students said” questions.
- **Staff-style table** (display name contains “staff”): hint that the table is a staff directory and to use `no_staf`, `nama_staf_dan_gelaran`, `jawatan_akademik`, `pusat_pengajian` for lecturers or staff by school/department.
- **Extra rule:** For “what do students say” or feedback-style questions, query the comments/feedback table and include `comment_text` and lecturer or course identifiers.

This steers the LLM to the right tables and columns for evaluation and feedback questions.

---

## 7. Additional question ideas (for users or docs)

You can suggest or support these as well; they map to the **comments** and **staff** schemas above.

### Comments (evaluations & feedback)

- Show comments for lecturer **Dr. Hartinee** (filter by `lecturer_name`).
- Which courses have the **best evaluation percentage**? (aggregate by course, order by `percentage`).
- List comments for course **BECA1013** (filter by `course_id`).
- What feedback did students give for **SEFB**? (filter by `pp` and show `comment_text`).
- **Average evaluation percentage by school** (e.g. group by `pp` if it represents school/faculty).
- How many comments mention “terbaik” or “thank you”? (filter or search `comment_text` if full-text or LIKE is available).

### Staff

- List all **Profesor** (filter by `jawatan_akademik` or `jawatan_semasa_singkatan`).
- Who is in **SBM** (School of Business Management)? (filter by `pusat_pengajian`).
- Show staff with **Dekan** as current post (filter by `jawatan_semasa_penuh` or `jawatan_semasa_singkatan`).
- How many staff per **pusat_pengajian**?

### Combined

- Which **lecturers** (from staff) have the **highest evaluation percentage** in comments? (join staff and comments on name or staff_no if consistent).

---

## 8. Quick reference

| Topic                    | Table(s)   | Key columns |
|--------------------------|------------|-------------|
| Evaluation %             | comments   | `percentage`, `lecturer_name`, `course_name` |
| What students said       | comments   | `comment_text`, `lecturer_name`, `course_id` |
| By course                | comments   | `course_id`, `course_name`, `comment_text` |
| By school/faculty        | comments   | `pp`; staff: `pusat_pengajian` |
| Staff directory          | staff      | `nama_staf_dan_gelaran`, `jawatan_akademik`, `pusat_pengajian` |
| Enrolled / evaluated     | comments   | `enrolled`, `evaluated`, `percentage` |

---

*Generated for the AskAI project (UUM data import and LLM suggestions).*
