import os
import boto3
from flask import Flask, jsonify
from flask import request
from flask_cors import CORS


client = boto3.client('sts')
print(client.get_caller_identity())
app = Flask(__name__)
CORS(app, origins=[
     "http://nandhana-course-public.s3-website.ap-south-2.amazonaws.com"])


REGION = os.environ.get("AWS_REGION", "ap-south-2")

dynamodb = boto3.resource("dynamodb", region_name=REGION)
courses_table = dynamodb.Table("nandhana-course")


@app.route("/nandhana-student/courses", methods=["POST"])
def create_course():
    data = request.get_json()

    # Basic validation
    if not data or "id" not in data:
        return jsonify({"error": "Course ID is required"}), 400

    try:
        courses_table.put_item(Item=data)
        return jsonify({"message": "Course created successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/nandhana-student")
def home():
    return "OK", 200


@app.route("/nandhana-student/health")
def health():
    return jsonify({"status": "ok", "service": "course-service"}), 200


@app.route("/nandhana-student/courses/<course_code>", methods=["GET"])
def get_course(course_code):
    resp = courses_table.get_item(Key={"id": course_code})
    item = resp.get("Item")
    if not item:
        return jsonify({"error": "Course not found"}), 404
    return jsonify(item), 200


@app.route("/nandhana-student/courses", methods=["GET"])
def list_courses():
    resp = courses_table.scan(Limit=50)
    return jsonify(resp.get("Items", [])), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3001, debug=False)
