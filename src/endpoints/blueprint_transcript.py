import os
from flask import Blueprint, jsonify, request, current_app, abort
from werkzeug.utils import secure_filename
from src.processing.pipe import Pipe

blueprint_transcript = Blueprint(name="blueprint_transcript", import_name=__name__)

@blueprint_transcript.route('/', methods=['POST'])
def post():
    uploaded_file = request.files['audio']
    filename = secure_filename(uploaded_file.filename)
    if filename != '':
        file_ext = os.path.splitext(filename)[1]
        if file_ext not in current_app.config['UPLOAD_EXTENSIONS']:
            abort(400)
        file_path = os.path.join(current_app.config['UPLOAD_PATH'], filename)
        uploaded_file.save(file_path)
        transcript = Pipe.process(file_path)
        # os.remove(file_path)
        return jsonify({ "transcript": transcript })

    return jsonify({ "transcript": "Your transcript is processing" })
    


