import pickle
import pandas as pd
import json
import os
from nltk.metrics.distance import edit_distance


class predict:
    symptoms_path = os.path.join(os.getcwd(),"src/processing/base/symptoms.json")
    f1 = open(symptoms_path)
    symptoms = json.load(f1)
    f1.close()

    symptom_and_weight_path = os.path.join(os.getcwd(),"src/processing/base/symptom_and_weight.json")
    f2 = open(symptom_and_weight_path)
    symptoms_and_weights = json.load(f2)
    f2.close()

    disease_path = os.path.join(os.getcwd(),"src/processing/base/disease.json")
    f3 = open(disease_path)
    disease = json.load(f3)
    f3.close()

    model_path = os.path.join(os.getcwd(),"src/processing/base/model.pkl")
    model = pickle.load(open(model_path, "rb"))

    # constructor
    def __init__(self):
        print("\n init \n")

    def get_weight(self, symptom):
        return self.symptoms_and_weights[symptom]['weight']

    def correct_symptom(self, input_symptoms):
        output = []
        for s in input_symptoms:
            temp = [(edit_distance(s, w), w) for w in self.symptoms if w[0] == s[0]]
            output.append(sorted(temp, key = lambda val:val[0])[0][1])
        return output

    def predict_symp(self, weights):
        result = self.mapping(self.model.predict_proba(weights)[0])
        return result

    def mapping(self, y):
        dict = {(self.disease)[i]: y[i] for i in range(len(y))}
        return dict

    def process(self, input_symptoms, output_num=10):
        if output_num > 41 or output_num < 0:
            output_num = 10
        symptoms_correct = self.correct_symptom(input_symptoms)
        weights = [ self.get_weight(s) for s in symptoms_correct ]
        padding_len = 17 - len(weights)
        padding = [0] * padding_len
        x = weights + padding
        df_x = pd.DataFrame(
            [x],
            columns=[
                "Symptom_1",
                "Symptom_2",
                "Symptom_3",
                "Symptom_4",
                "Symptom_5",
                "Symptom_6",
                "Symptom_7",
                "Symptom_8",
                "Symptom_9",
                "Symptom_10",
                "Symptom_11",
                "Symptom_12",
                "Symptom_13",
                "Symptom_14",
                "Symptom_15",
                "Symptom_16",
                "Symptom_17",
            ],
        )
        y = self.predict_symp(df_x)
        y = sorted(y, key=y.get, reverse=True)[-output_num:]
        return y

api = predict()