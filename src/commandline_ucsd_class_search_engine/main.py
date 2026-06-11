import argparse

from commandline_ucsd_class_search_engine.functions import (
    search_ucsd_courses,
    search_course_prereq,
)


def print_results(results):
    if not results:
        print("No matching courses found.")
        return

    for code, courses in results.items():
        print(f"\n{'=' * 60}")
        print(code)
        print(f"{'=' * 60}")

        for course_name, description in courses:
            print(f"\n{course_name}")

            if description:
                print(description)


def print_prereq_tree(node: dict, prefix: str = "", is_last: bool = True):
    connector = "└── " if is_last else "├── "

    course_code = node.get("course_code", "Unknown")

    print(prefix + connector + course_code)

    standing = node.get("standing", [])
    if standing:
        for req in standing:
            print(
                prefix
                + ("    " if is_last else "│   ")
                + f"[{req}]"
            )

    children = list(node.get("prerequisites", {}).values())

    child_prefix = prefix + ("    " if is_last else "│   ")

    for i, child in enumerate(children):
        print_prereq_tree(
            child,
            child_prefix,
            i == len(children) - 1,
        )


def main():
    parser = argparse.ArgumentParser(
        description="Search UCSD courses and prerequisite trees."
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    search_parser = subparsers.add_parser(
        "search-course",
        help="Search UCSD courses by department and keyword.",
    )

    search_parser.add_argument(
        "--departments",
        "-d",
        default="",
    )

    search_parser.add_argument(
        "--keywords",
        "-k",
        default="",
    )

    search_parser.add_argument(
        "--division",
        default="all",
    )

    search_parser.add_argument(
        "--formatting",
        "-f",
        default="",
        choices=["", "bold"],
    )

    search_parser.add_argument(
        "--threshold",
        "-t",
        default="0",
    )

    prereq_parser = subparsers.add_parser(
        "search-prereq",
        help="Show recursive prerequisites for a course.",
    )

    prereq_parser.add_argument(
        "course",
        help='Course code, e.g. "DSC 100" or "MATH 20C".',
    )

    args = parser.parse_args()

    if args.command == "search-course":
        results = search_ucsd_courses(
            department_codes=args.departments,
            keywords=args.keywords,
            division=args.division,
            formatting=args.formatting,
            match_threshold=args.threshold,
        )

        print_results(results)

    elif args.command == "search-prereq":
        tree = search_course_prereq(args.course)
        print_prereq_tree(tree)


if __name__ == "__main__":
    main()