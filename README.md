# UCSD Course Search Engine

UCSD Course Search Engine is a command-line tool for searching UC San Diego courses. It allows users to search for courses by department, keywords, and division level, as well as building the prerequisite chains for a course.

## Usage

## Command: search-course

Search for courses with matching keywords, departments and divisions.

#### Arguments

---

##### `--departments`, `-d`
Comma-separated department codes to search.

Examples:
```bash
-d DSC
-d DSC,CSE,MATH
```

An empty string searches all departments.

---

##### `--keywords`, `-k`
Comma-separated keywords used to match course titles and descriptions.

Examples:
```bash
-k "machine learning"
-k "data science,statistics"
```

An empty string returns all courses in the selected departments.

---

##### `--division`
Comma-separated division filters.

Supported values:

| Value | Description |
|---------|-------------|
| lower | Courses numbered 1–99 |
| upper | Courses numbered 100–199 |
| grad | Courses numbered 200–299 |
| professional | Courses numbered 300–499 |
| teacher | Courses numbered 500–599 |
| all | All courses |

Examples:

```bash
--division lower
--division upper,grad
--division lower,upper,grad
--division all
```

---

##### `--formatting`, `-f`
Optional output formatting.

Supported values:

| Value | Description |
|--------|-------------|
| "" | No formatting |
| bold | Wrap matched keywords with `**...**` |

Example:

```bash
-f bold
```

---

##### `--threshold`, `-t`
Keyword match percentage from `0` to `100`.

- `0` → A course matches if **any** keyword appears.
- `100` → A course matches only if **all** keywords appear.
- Any value between `0` and `100` requires that percentage of keywords to appear.

Examples:

```bash
-t 0
-t 50
-t 100
```

---

#### Example

```bash
ucsd-search search-course \
    --departments MATH \
    --keywords probability,statistics \
    --division upper,lower \
    --formatting bold \
    --threshold 50
```

This command searches the Mathematics department (`MATH`) for upper-division and lower-division courses (1–199) whose course title or description contains at least 50% of the specified keywords (`probability` and `statistics`).

The `bold` formatting option highlights matched keywords by surrounding them with `**...**` in the output.

---

## Command: search-prereq

Display the recursive prerequisite tree for a course.

```bash
ucsd-search search-prereq "DSC 20"
```

Example output:

```text
└── DSC 20
    └── DSC 10
```

This command searches the UCSD catalog for DSC 20, identifies its prerequisite courses, and recursively builds a prerequisite tree showing all course dependencies.

---
