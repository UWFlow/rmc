from pymongo import Connection

Connection("localhost", 27017).rmc.course_evals.remove()
