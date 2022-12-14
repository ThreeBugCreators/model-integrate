import os
from flask import Blueprint, jsonify, request, current_app, abort
from werkzeug.utils import secure_filename
from src.processing.pipe import Pipe
from src.processing.predict import api

predict_api = Blueprint(name="predict_api", import_name=__name__)

@predict_api.route('/', methods=['GET'])
def get():
    query_params = dict(request.args)
    list_symptoms = query_params['symptoms'].split(',')
    result = api.process(list_symptoms)

    return jsonify({ "data": result })
