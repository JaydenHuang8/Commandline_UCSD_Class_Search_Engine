import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from difflib import get_close_matches
import re


##################################################################
#
#   Course Search
#
##################################################################



def scrape_courses(
    url: str,
    division: str = "all",
) -> dict[str, list[tuple[str, str | None]]]:
    """
    Scrape UCSD course catalog courses and filter by course number.

    Args:
        url:
            UCSD department course catalog URL.

        division:
            Comma-separated division filters.

            Supported values:
                "lower"        : courses numbered 1-99
                "upper"        : courses numbered 100-199
                "grad"         : courses numbered 200-299
                "professional" : courses numbered 300-499
                "teacher"      : courses numbered 500-599
                "all"          : all courses

            Examples:
                "lower"
                "upper,grad"
                "lower,upper,grad"
                "all"

    Returns:
        {
            "Lower Division": [
                ("DSC 10. Principles of Data Science (4)", "Description...")
            ],
            "Upper Division": [...],
            "Graduate": [...],
            "Professional": [...],
            "Teacher": [...]
        }
    """

    requested_divisions = {
        item.strip().lower()
        for item in division.split(",")
        if item.strip()
    }

    valid_divisions = {
        "lower",
        "upper",
        "grad",
        "professional",
        "teacher",
        "all",
    }

    if not requested_divisions:
        requested_divisions = {"all"}

    invalid_divisions = requested_divisions - valid_divisions

    if invalid_divisions:
        raise ValueError(
            "Invalid division(s): "
            + ", ".join(sorted(invalid_divisions))
            + '. Use "lower", "upper", "grad", '
            + '"professional", "teacher", or "all".'
        )

    response = requests.get(url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    courses = {
        "Lower Division": [],
        "Upper Division": [],
        "Graduate": [],
        "Professional": [],
        "Teacher": [],
    }

    def get_course_number(course_name: str) -> int | None:
        """
        Extract the numeric part of a course name.

        Examples:
            "DSC 10. Principles..." -> 10
            "DSC 40A. Theoretical..." -> 40
            "CSE 151A. Machine Learning..." -> 151
        """

        match = re.search(r"\b[A-Z]+\s+(\d+)", course_name)

        if not match:
            return None

        return int(match.group(1))

    def classify_course(course_number: int) -> str | None:
        """Classify course number into a division."""

        if 1 <= course_number <= 99:
            return "Lower Division"

        if 100 <= course_number <= 199:
            return "Upper Division"

        if 200 <= course_number <= 299:
            return "Graduate"

        if 300 <= course_number <= 499:
            return "Professional"

        if 500 <= course_number <= 599:
            return "Teacher"

        return None

    division_name_to_key = {
        "Lower Division": "lower",
        "Upper Division": "upper",
        "Graduate": "grad",
        "Professional": "professional",
        "Teacher": "teacher",
    }

    for course_tag in soup.find_all("p", class_="course-name"):
        description = course_tag.find_next_sibling(
            "p",
            class_="course-descriptions",
        )

        course_name = course_tag.get_text(strip=True)
        course_description = (
            description.get_text(" ", strip=True)
            if description
            else None
        )

        course_number = get_course_number(course_name)

        if course_number is None:
            continue

        course_division = classify_course(course_number)

        if course_division is None:
            continue

        division_key = division_name_to_key[course_division]

        if "all" in requested_divisions or division_key in requested_divisions:
            courses[course_division].append(
                (course_name, course_description)
            )

    if "all" in requested_divisions:
        return courses

    return {
        division_name: course_list
        for division_name, course_list in courses.items()
        if division_name_to_key[division_name] in requested_divisions
    }



def scrape_ucsd_department_courses_links() -> list[tuple[str, str, str]]:
    """
    Scrape the UCSD catalog and return departments that have
    both a subject code and a course catalog page.

    Returns:
        [
            (
                department_name,
                department_code,
                course_url,
            ),
            ...
        ]
    """

    # ----------------------------
    # Subject code lookup
    # ----------------------------

    subject_url = (
        "https://blink.ucsd.edu/instructors/courses/"
        "schedule-of-classes/subject-codes.html"
    )

    response = requests.get(subject_url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    code_lookup = {}

    table = soup.find("table")

    for row in table.find_all("tr")[1:]:
        cols = row.find_all("td")

        if len(cols) != 2:
            continue

        code = cols[0].get_text(strip=True)
        description = cols[1].get_text(" ", strip=True)

        code_lookup[code] = description

    # ----------------------------
    # Catalog page
    # ----------------------------

    catalog_url = "https://catalog.ucsd.edu/front/courses.html"

    response = requests.get(catalog_url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    departments = []

    for p in soup.find_all("p"):
        course_link = None

        for a in p.find_all("a"):
            if a.get_text(strip=True).lower() == "courses":
                course_link = a.get("href")
                break

        if not course_link:
            continue

        department_name = p.get_text(" ", strip=True).split("[")[0].strip()

        full_course_url = urljoin(catalog_url, course_link)

        # ../courses/AASM.html -> AASM
        department_code = (
            course_link.split("/")[-1]
            .replace(".html", "")
            .strip()
        )

        # Keep only departments that have a subject code
        if department_code not in code_lookup:
            continue

        departments.append(
            (
                department_name,
                department_code,
                full_course_url,
            )
        )

    return departments


def search_ucsd_courses(
    department_codes: str,
    keywords: str,
    division: str = "all",
    formatting: str = "",
    match_threshold: str = "0",
) -> dict[str, list[tuple[str, str | None]]]:
    """
    Search UCSD courses by department code and keywords.

    Args:
        department_codes:
            Comma-separated department codes, e.g. "DSC,CSE,MATH".
            Empty string searches all departments.

        keywords:
            Comma-separated keywords, e.g. "machine learning,data science".
            Empty string returns all courses in the selected departments.

        division:
            Comma-separated division filters.

            Supported values:
                "lower"        : courses numbered 1-99
                "upper"        : courses numbered 100-199
                "grad"         : courses numbered 200-299
                "professional" : courses numbered 300-499
                "teacher"      : courses numbered 500-599
                "all"          : all courses

            Examples:
                "lower"
                "upper,grad"
                "lower,upper,grad"
                "all"

        formatting:
            Optional output formatting.

            Supported values:
                ""      : no formatting
                "bold"  : wrap keyword matches in **...**

        match_threshold:
            String integer from "0" to "100".

            "0" means a course matches if any keyword appears.
            "100" means a course matches only if all keywords appear.
            Other values require that percentage of keywords to appear.

    Returns:
        Dictionary mapping department codes to matching courses.

        Example:
        {
            "DSC": [
                (
                    "DSC 180A. **Machine Learning** Platforms",
                    "Introduction to **machine learning** systems..."
                )
            ]
        }

    Notes:
        - If both department_codes and keywords are empty,
          an error is printed and an empty dictionary is returned.
        - Invalid department codes generate suggestions.
        - Keyword matching is case-insensitive.
    """

    try:
        threshold = int(match_threshold)
    except ValueError:
        print("Error: match_threshold must be an integer between 0 and 100.")
        return {}

    if not 0 <= threshold <= 100:
        print("Error: match_threshold must be an integer between 0 and 100.")
        return {}


    def highlight_keywords(
        text: str,
        keywords: list[str],
    ) -> str:
        """Wrap keyword matches in **...** if formatting is 'bold'."""

        if formatting.lower() != "bold":
            return text

        for keyword in sorted(keywords, key=len, reverse=True):
            pattern = re.compile(
                re.escape(keyword),
                re.IGNORECASE,
            )

            text = pattern.sub(
                lambda match: f"**{match.group(0)}**",
                text,
            )

        return text

    department_links = scrape_ucsd_department_courses_links()

    code_to_url = {
        code.upper(): url
        for department_name, code, url in department_links
    }

    all_codes = set(code_to_url)

    requested_codes = [
        code.strip().upper()
        for code in department_codes.split(",")
        if code.strip()
    ]

    requested_keywords = [
        keyword.strip().lower()
        for keyword in keywords.split(",")
        if keyword.strip()
    ]

    if not requested_codes and not requested_keywords:
        print("Error: Please provide at least one department code or keyword.")
        return {}

    if not requested_codes:
        selected_codes = sorted(all_codes)
    else:
        selected_codes = []

        for code in requested_codes:
            if code not in all_codes:
                suggestions = get_close_matches(
                    code,
                    all_codes,
                    n=5,
                    cutoff=0.5,
                )

                if suggestions:
                    print(
                        f'Error: "{code}" is not a valid department code. '
                        f'Did you mean: {", ".join(suggestions)}?'
                    )
                else:
                    print(f'Error: "{code}" is not a valid department code.')

                continue

            selected_codes.append(code)

    results = {}

    for code in selected_codes:
        department_courses = scrape_courses(
            code_to_url[code],
            division,
        )

        matched_courses = []

        for division_courses in department_courses.values():
            for course_name, description in division_courses:
                searchable_text = f"{course_name} {description or ''}".lower()

                if not requested_keywords:
                    matched_courses.append(
                        (course_name, description)
                    )
                    continue

                matched_keyword_count = sum(
                    keyword in searchable_text
                    for keyword in requested_keywords
                )

                match_percent = (
                    matched_keyword_count / len(requested_keywords)
                ) * 100

                if threshold == 0:
                    is_match = matched_keyword_count > 0
                else:
                    is_match = match_percent >= threshold

                if is_match:
                    highlighted_name = highlight_keywords(
                        course_name,
                        requested_keywords,
                    )

                    highlighted_description = (
                        highlight_keywords(
                            description,
                            requested_keywords,
                        )
                        if description
                        else None
                    )

                    matched_courses.append(
                        (
                            highlighted_name,
                            highlighted_description,
                        )
                    )

        if matched_courses:
            results[code] = matched_courses

    return results


##################################################################
#
#   Prerequisite Search
#
##################################################################


COURSE_CODE_RE = re.compile(r"\b([A-Z]{2,5})\s+(\d+[A-Z]*)\b")


def normalize_course_code(course_code: str) -> str:
    course_code = course_code.upper().strip()
    course_code = re.sub(r"\s+", " ", course_code)
    return course_code


def extract_course_code(course_name: str) -> str | None:
    match = COURSE_CODE_RE.search(course_name)

    if not match:
        return None

    return f"{match.group(1)} {match.group(2)}"


def extract_prereq_text(description_tag) -> str:
    """
    Looks inside a course description tag and extracts only the text
    after the Prerequisites label.
    """

    if description_tag is None:
        return ""

    strong_tags = description_tag.find_all("strong")

    for strong in strong_tags:
        label = strong.get_text(" ", strip=True).lower()

        if "prerequisite" in label:
            full_text = description_tag.get_text(" ", strip=True)

            return re.split(
                r"prerequisites?:",
                full_text,
                maxsplit=1,
                flags=re.IGNORECASE,
            )[-1].strip()

    return ""


def parse_prerequisites(prereq_text: str) -> dict:
    """
    Extract course codes and standing requirements.

    This does not perfectly preserve AND/OR logic yet.
    It just collects all possible course prerequisites.
    """

    prereq_text_lower = prereq_text.lower()

    course_matches = COURSE_CODE_RE.findall(prereq_text)

    courses = [
        f"{subject} {number}"
        for subject, number in course_matches
    ]

    standing = []

    if "upper-division standing" in prereq_text_lower:
        standing.append("upper-division standing")

    if "graduate standing" in prereq_text_lower:
        standing.append("graduate standing")

    return {
        "courses": sorted(set(courses)),
        "standing": standing,
        "raw": prereq_text,
    }


def find_course_on_page(
    department_url: str,
    target_course_code: str,
) -> dict | None:
    """
    Finds one course on a department catalog page.

    Returns:
        {
            "course_code": "DSC 100",
            "course_name": "...",
            "description": "...",
            "prereq_text": "...",
            "parsed_prereqs": {...}
        }
    """

    target_course_code = normalize_course_code(target_course_code)

    response = requests.get(department_url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    for course_tag in soup.find_all("p", class_="course-name"):
        course_name = course_tag.get_text(" ", strip=True)
        course_code = extract_course_code(course_name)

        if course_code != target_course_code:
            continue

        description_tag = course_tag.find_next_sibling(
            "p",
            class_="course-descriptions",
        )

        description = (
            description_tag.get_text(" ", strip=True)
            if description_tag
            else ""
        )

        prereq_text = extract_prereq_text(description_tag)

        return {
            "course_code": course_code,
            "course_name": course_name,
            "description": description,
            "prereq_text": prereq_text,
            "parsed_prereqs": parse_prerequisites(prereq_text),
        }

    return None


def search_course_prereq(
    start_course_code: str,
) -> dict:
    """
    Recursively builds a prerequisite tree.

    Args:
        start_course_code:
            Example: "DSC 100"
    """
    departments = scrape_ucsd_department_courses_links()

    department_links = {
        department_code: course_url
        for department_name, department_code, course_url in departments
    }

    visited = set()

    def helper(course_code: str) -> dict:
        course_code = normalize_course_code(course_code)

        if course_code in visited:
            return {
                "course_code": course_code,
                "cycle": True,
                "prerequisites": {},
            }

        visited.add(course_code)

        subject = course_code.split()[0]

        if subject not in department_links:
            return {
                "course_code": course_code,
                "error": "No department link found",
                "prerequisites": {},
            }

        department_url = department_links[subject]

        course_info = find_course_on_page(
            department_url,
            course_code,
        )

        if course_info is None:
            return {
                "course_code": course_code,
                "error": "Course not found on department page",
                "prerequisites": {},
            }

        parsed = course_info["parsed_prereqs"]

        prereq_tree = {}

        for prereq_course in parsed["courses"]:
            prereq_tree[prereq_course] = helper(prereq_course)

        return {
            "course_code": course_code,
            "course_name": course_info["course_name"],
            "standing": parsed["standing"],
            "raw_prerequisites": parsed["raw"],
            "prerequisites": prereq_tree,
        }

    return helper(start_course_code)
