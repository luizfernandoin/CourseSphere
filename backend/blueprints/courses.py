from flask import Blueprint
from backend.db import execute_query
from backend.utils.responses import error_response, success_response

courses_bp = Blueprint("courses", __name__)


@courses_bp.route("/courses", methods=["GET"])
def get_courses():
    """Retrieves all courses from the database."""
    courses = execute_query("SELECT * FROM courses")
    return success_response(courses, 200)


@courses_bp.route("/courses/<int:course_id>", methods=["GET"])
def get_course(course_id):
    """Retrieves a specific course by its integer ID using parameterized query."""
    courses = execute_query("SELECT * FROM courses WHERE id = ?", (course_id,))
    if courses:
        return success_response(courses[0], 200)
    return error_response("Course not found", 404)


@courses_bp.route("/courses/description/<int:course_id>", methods=["GET"])
def get_course_description(course_id):
    """Retrieves description for a course by its ID using parameterized query."""
    descriptions = execute_query(
        "SELECT description FROM course_descriptions WHERE course_id = ?", (course_id,)
    )
    if descriptions:
        return success_response(descriptions[0], 200)
    return error_response("Course description not found", 404)


@courses_bp.route("/courses/bysection/<int:section_id>", methods=["GET"])
def get_courses_by_section(section_id):
    """Retrieves courses matching a section ID using parameterized query."""
    courses = execute_query(
        "SELECT * FROM courses WHERE section_id = ?", (section_id,)
    )
    if not courses:
        return error_response("No courses found for this section", 404)
    return success_response(courses, 200)


@courses_bp.route("/courses/semester/<string:semester>", methods=["GET"])
def get_courses_by_semester(semester):
    """Retrieves courses for a specific semester using parameterized query."""
    courses = execute_query(
        "SELECT * FROM courses WHERE semester = ?", (semester,)
    )
    if not courses:
        return error_response("No courses found for this semester", 404)
    return success_response(courses, 200)


@courses_bp.route("/courses/department/<string:department>", methods=["GET"])
def get_courses_by_department(department):
    """Retrieves courses for a specific department using parameterized query."""
    courses = execute_query(
        "SELECT * FROM courses WHERE department = ?", (department,)
    )
    if not courses:
        return error_response("No courses found for this department", 404)
    return success_response(courses, 200)


@courses_bp.route("/courses/instructor/<string:instructor>", methods=["GET"])
def get_courses_by_instructor(instructor):
    """Retrieves courses for a specific instructor using parameterized query."""
    courses = execute_query(
        "SELECT * FROM courses WHERE instructor = ?", (instructor,)
    )
    if not courses:
        return error_response("No courses found for this instructor", 404)
    return success_response(courses, 200)
