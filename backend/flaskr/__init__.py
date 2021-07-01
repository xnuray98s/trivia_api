import os
from flask import Flask, request, abort, jsonify
from flask.globals import current_app
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10
current_category = "History"


def paginate_questions(request, selection):
    page = request.args.get("page", 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in selection]
    current_questions = questions[start:end]

    return current_questions


def format_previous_questions(prev):
    list_of_ids = []
    for question in prev:
        list_of_ids.append(question.id)

    return list_of_ids


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    @app.after_request
    def after_request(response):
        response.headers.add(
            "Access-Control-Allow-Headers", "Content-Type,Authorization,true"
        )
        response.headers.add(
            "Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS"
        )
        return response

    @app.route("/categories")
    def get_categories():
        categories = {
            category.format()["id"]: category.format()["type"]
            for category in Category.query.all()
        }
        return jsonify({"success": True, "categories": categories})

    @app.route("/questions")
    def get_questions():
        selection = Question.query.order_by(Question.category).all()
        current_questions = paginate_questions(request, selection)
        categories = Category.query.all()
        categories_formatted = [category.format() for category in categories]
        if len(current_questions) == 0:
            abort(404)

        current_category = Category.query.get(current_questions[-1]["category"]).type

        return jsonify(
            {
                "success": True,
                "questions": current_questions,
                "totalQuestions": len(Question.query.all()),
                "categories": categories_formatted,
                "currentCategories": current_category,
            }
        )

    @app.route("/questions/<int:id>", methods=["DELETE"])
    def delete_question(id):
        try:
            question = Question.query.filter(Question.id == id).one_or_none()

            if question is None:
                abort(404)

            question.delete()
            selection = Question.query.order_by(Question.id).all()
            current_questions = paginate_questions(request, selection)

            return jsonify(
                {
                    "success": True,
                    "deleted": id,
                    "question": current_questions,
                    "totalQuestions": len(Question.query.all()),
                }
            )

        except:
            abort(422)

    @app.route("/questions", methods=["POST"])
    def add_question_or_search():
        body = request.get_json()
        search_term = body.get("searchTerm")
        if search_term is not None:
            questions = Question.query.filter(
                Question.question.ilike(f"%{search_term}%")
            ).all()
            if not questions:
                abort(404)
            result = [question.format() for question in questions]
            current_category = Category.query.get(result[-1]["category"]).type
            return jsonify(
                {
                    "success": True,
                    "questions": result,
                    "totalQuestions": len(Question.query.all()),
                    "currentCategories": current_category,
                }
            )

        else:
            question = body.get("question")
            answer = body.get("answer")
            category = body.get("category")
            difficulty = body.get("difficulty")
            try:
                new_question = Question(
                    question=question,
                    answer=answer,
                    category=category,
                    difficulty=difficulty,
                )
                new_question.insert()

                return jsonify(
                    {
                        "success": True,
                    }
                )

            except:
                abort(422)

    @app.route("/categories/<int:id>/questions")
    def get_questions_by_category(id):
        selection = Question.query.filter(Question.category == id).all()
        questions = [question.format() for question in selection]
        current_category = questions[-1]["category"]
        return jsonify(
            {
                "success": True,
                "questions": questions,
                "totalQuestions": len(Question.query.all()),
                "currentCategories": current_category,
            }
        )

    @app.route("/quizzes", methods=["POST"])
    def play_quiz():
        body = request.get_json()

        quiz_category = (
            body.get("quiz_category") if body.get("quiz_category")["id"] != 0 else None
        )
        previous_questions = (
            body.get("previous_questions")
            if body.get("previous_questions") is not None
            else []
        )
        if quiz_category:
            all_questions = format_previous_questions(
                Question.query.filter(Question.category == quiz_category["id"]).all()
            )
        else:
            all_questions = format_previous_questions(Question.query.all())
        list_of_ids = [id for id in all_questions if id not in previous_questions]
        if list_of_ids:
            random_id = random.choice(list_of_ids)
            question = Question.query.get(random_id).format()
        else:
            question = None

        return jsonify({"question": question})

    @app.errorhandler(404)
    def not_found(error):
        return (
            jsonify({"success": False, "error": 404, "message": "resource not found"}),
            404,
        )

    @app.errorhandler(422)
    def unprocessable(error):
        return (
            jsonify({"success": False, "error": 422, "message": "unprocessable"}),
            422,
        )

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({"success": False, "error": 400, "message": "bad request"}), 400

    @app.errorhandler(405)
    def not_allowed(error):
        return (
            jsonify({"success": False, "error": 405, "message": "method not allowed"}),
            405,
        )

    @app.errorhandler(500)
    def server_error(error):
        return (
            jsonify(
                {"success": False, "error": 500, "message": "internal server error"}
            ),
            500,
        )

    return app
