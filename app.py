from flask import Flask, request, jsonify, make_response
from flask_restplus import Api, Resource, fields
from flask_cors import CORS
import numpy as np
import sys
import json
import pickle
import pandas as pd 
from keras.preprocessing import sequence
from keras.preprocessing.text import Tokenizer
from keras.models import load_model

flask_app = Flask(__name__)
CORS(flask_app)

app = Api(app = flask_app, 
		  version = "1.0", 
		  title = "Veritas", 
		  description = "Predict trust index of a news")

name_space = app.namespace('prediction', description='Prediction APIs')

model = app.model('Prediction params', 
				  {'inputText': fields.String(required = True, 
				  							   description="Input Text for the Model", 
    					  				 	   help="Input Text cannot be blank")})

ML_model = load_model('./model.h5')
ML_model._make_predict_function()

def get_prediction_score(websiteDescription):
	# Load the pickle file (dictionary)
	with open('./word_dict.pickle', 'rb') as handle:
		token = pickle.load(handle)

	# Setup the dataset
	data = pd.DataFrame([])
	data['Headline'] = pd.Series([websiteDescription])
	input_data = data['Headline'].fillna('')

	# Text to sequence and padding
	input_data = token.texts_to_sequences(input_data)
	input_data = sequence.pad_sequences(input_data, maxlen = 76)

	# Prediction on the classification Model
	prediction = ML_model.predict_classes(input_data)
	prediction_pro = ML_model.predict_proba(input_data)
	pred = "FAKE" if int(prediction[0]) == 0 else "REAL" 
	prob_pred = round(float(prediction_pro[0]),2)
	
	return pred, prob_pred

@name_space.route("/")
class MainClass(Resource):

	def options(self):
		response = make_response()
		response.headers.add("Access-Control-Allow-Origin", "*")
		response.headers.add('Access-Control-Allow-Headers', "*")
		response.headers.add('Access-Control-Allow-Methods', "*")
		return response

	@app.expect(model)		
	def post(self):
		try: 
			req = json.loads(request.data.decode("utf-8"))
			websiteDescription = req["data"]

			### Pre-Processinga and prediction on the websiteDescription
			pred, prob_pred =get_prediction_score(websiteDescription)


			stringToSendBack = "Prediction: " + str(pred) + " _ Probability: " + str(prob_pred)
			response = jsonify({
				"statusCode": 200,
				"status": "Prediction made",
				"result": stringToSendBack
				})
			response.headers.add('Access-Control-Allow-Origin', '*')
			return response
		except Exception as error:
			return jsonify({
				"statusCode": 500,
				"status": "Could not make prediction",
				"error": str(error)
			})

if __name__ == '__main__':
	# Threaded option to enable multiple instances for multiple user access support
	flask_app.run(threaded=True, port=5000)