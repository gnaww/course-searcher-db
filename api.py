from flask import Flask, request
from flask_restful import Resource, Api
from sqlalchemy import create_engine
from json import dumps

e = create_engine('sqlite:///RU SOC.db')

app = Flask(__name__)
api = Api(app)


class Courses(Resource):
    def get(self):
        # Connect to databse
        conn = e.connect()
        # Perform query and return JSON data
        query = conn.execute("select * from Fall_2016_SOC")
        return {'courses': [i for i in query.cursor.fetchall()]}


class CoursesGivenSubject(Resource):
    def get(self, subject_num):
        s = subject_num.zfill(3)

        conn = e.connect()
        query = conn.execute("select * from Fall_2016_SOC where course_subject='%s'" % s)
        # Query the result and get cursor.Dumping that data to a JSON is looked by extension
        result = {'courses': [dict(zip(tuple(query.keys()), i)) for i in query.cursor]}
        return result
        # We can have PUT,DELETE,POST here. But in our API GET implementation is sufficient

class SectionsGivenSubjectAndCourse(Resource):
    def get(self, subject_num, course_num):
        s = subject_num.zfill(3)
        c = course_num.zfill(3)

        conn = e.connect()
        query = conn.execute("select * from Fall_2016_SOC where course_subject='%s' and course_number='%s'" % (s, c))
        # Query the result and get cursor.Dumping that data to a JSON is looked by extension
        result = {'courses': [dict(zip(tuple(query.keys()), i)) for i in query.cursor]}
        return result
        # We can have PUT,DELETE,POST here. But in our API GET implementation is sufficient

api.add_resource(Courses, '/subject=GMA')
api.add_resource(CoursesGivenSubject, '/subject=<string:subject_num>')
api.add_resource(SectionsGivenSubjectAndCourse, '/subject=<string:subject_num>&course=<string:course_num>')


if __name__ == '__main__':
    app.run()