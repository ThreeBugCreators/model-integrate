import os
import shutil
import requests
import json
import librosa
import soundfile as sf
from flask import current_app
from .chunk import chunk_extension
from .featuring import Prediction

class Pipe:

    COMMANDS = ['', '', '', '', '']

    @staticmethod
    def get_3rd_transcript(path):
        y, s = librosa.load(path, sr=8000)
        sf.write(path, y, 8000)
        with open(path, 'rb') as f:
            data = f.read()
            res = requests.post(
                url = 'http://20.198.187.38/sttfull?noiseDetection=true',
                data = data,
                headers = {
                    'Content-Type': 'application/octet-stream',
                    'Authorization': 'wWPBZb7rKryrXLABP62cu2S6WqfSxcaQ',
                },
            );
            transcript = json.loads(res.text)['data']['transcript']
            return transcript

    
    @staticmethod
    def create_folder(name):
        folder_path = os.path.join(current_app.config['UPLOAD_PATH'], name)
        if os.path.exists(folder_path) and os.path.isdir(folder_path):
            shutil.rmtree(folder_path)
        os.mkdir(folder_path)
        return folder_path

    @staticmethod
    def get_filename_from_path(path):
        full_name = path.split("/")[-1]
        return full_name.split('.')[0]
    
    @staticmethod
    def process(path):
        filename = Pipe.get_filename_from_path(path)
        folder_path = Pipe.create_folder(filename)
        paths = chunk_extension.silence_cut_off(path, folder_path)
        transcript_auth = Prediction.get_transcript(paths=paths)
        transcript = Pipe.get_3rd_transcript(path)
        print(transcript_auth + ' vs ' + transcript)
        if transcript_auth.lower() == transcript.lower():
            return {
                'transcript': transcript_auth,
                'origin': 'h5.model',
            }
        else:
            return {
                'transcript': transcript,
                'origin': 'validation',
            }