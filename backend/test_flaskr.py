import os
import unittest
import json
from flask_sqlalchemy import SQLAlchemy

from flaskr import create_app
from models import setup_db, Question, Category


class TriviaTestCase(unittest.TestCase):
    """This class represents the trivia test case"""

    def setUp(self):
        """Define test variables and initialize app."""
        self.app = create_app()
        self.client = self.app.test_client
        self.database_name = "trivia_test"
        self.database_path = "postgres://{}:{}@{}/{}".format(
            "postgres", "postgres", "localhost:5432", self.database_name
        )
        setup_db(self.app, self.database_path)

        # binds the app to the current context
        with self.app.app_context():
            self.db = SQLAlchemy()
            self.db.init_app(self.app)
            # create all tables
            self.db.create_all()

    def tearDown(self):
        """Executed after reach test"""
        pass

    """
    TODO
    Write at least one test for each test for successful operation and for expected errors.
    """

    def test_get_categories(self):
        res = self.client().get("/questions")
        data = json.loads(res.data.decode("utf-8"))

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertTrue(data["categories"])

    def test_get_questions(self):
        res = self.client().get("/questions?page=1")
        data = json.loads(res.data.decode("utf-8"))

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertTrue(data["categories"])
        self.assertTrue(data["currentCategories"])
        self.assertTrue(data["totalQuestions"])
        self.assertTrue(len(data["questions"]))

    def test_get_questions_by_category(self):
        res = self.client().get("/categories/3/questions")
        data = json.loads(res.data.decode("utf-8"))

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertTrue(data["currentCategories"], "Geography")
        self.assertTrue(data["totalQuestions"])
        self.assertTrue(len(data["questions"]))

    def test_404_request_beyond_page(self):
        res = self.client().get("/questions?page=1000")
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 404)
        self.assertEqual(data["success"], False)
        self.assertEqual(data["message"], "resource not found")

    def test_delete_question(self):
        res = self.client().delete("/questions/2")
        data = json.loads(res.data)

        question = Question.query.filter(Question.id == 2).one_or_none()

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertEqual(data["deleted"], 2)
        self.assertTrue(data["totalQuestions"])
        self.assertTrue(len(data["question"]))
        self.assertEqual(question, None)

    def test_422_invalid_question_id(self):
        res = self.client().delete("/questions/1000")
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 422)
        self.assertEqual(data["success"], False)
        self.assertEqual(data["message"], "unprocessable")

    def test_search_questions(self):
        res = self.client().post("/questions", json={"searchTerm": "body"})
        data = json.loads(res.data)

        search = Question.query.filter(Question.question.ilike("body")).all()

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertTrue(data["currentCategories"])
        self.assertTrue(data["totalQuestions"])
        self.assertTrue(data["questions"], search)

    def test_add_question(self):
        res = self.client().post(
            "/questions",
            json={
                "question": "What's the biggest animal in the world?",
                "answer": "The blue whale",
                "difficulty": 1,
                "category": 1,
            },
        )
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)

    def test_405_add_question_not_allowed(self):
        res = self.client().post(
            "/questions/45",
            json={
                "question": "In what franchise would you find the character Katniss Everdeen?",
                "answer": "The Hunger Games",
                "difficulty": 2,
                "category": 5,
            },
        )
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 405)
        self.assertEqual(data["success"], False)
        self.assertEqual(data["message"], "method not allowed")


# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()
