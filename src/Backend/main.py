import requests
import json
from utils.es_requester import request_es, extract_sentences, request_es_ML, request_es_triple
from utils.sentence_clearer import clear_sentences, remove_questions
from utils.summarization import find_most_frequent_words
from ml_approach.sentence_preparation_ML import prepare_sentence_DF
from ml_approach.classify import classify_sentences, evaluate
from marker_approach.object_comparer import find_winner

from flask import Flask, request, jsonify
from flask_cors import CORS
import sklearn


app = Flask(__name__)
CORS(app)


@app.route("/")
@app.route('/cam', methods=['GET'])
def cam():
    '''
    to be visited after a user clicked the 'compare' button.
    '''
    fast_search = request.args.get('fs')
    obj_a = Argument(request.args.get('objectA').lower().strip())
    obj_b = Argument(request.args.get('objectB').lower().strip())
    aspects = extract_aspects(request)
    model = request.args.get('model')
    statusID = request.args.get('statusID')

    if model == 'default' or model is None:
        # json obj with all ES hits containing obj_a, obj_b and a marker.
        setStatus(statusID, 'Request ES')
        json_compl = request_es(fast_search, obj_a, obj_b)

        # list of all sentences containing obj_a, obj_b and a marker.
        setStatus(statusID, 'Extract sentences')
        all_sentences = extract_sentences(json_compl)

        # removing sentences that can't be properly analyzed
        setStatus(statusID, 'Clear sentences')
        all_sentences = clear_sentences(all_sentences, obj_a, obj_b)

        # find the winner of the two objects
        setStatus(statusID, 'Find winner')
        return jsonify(find_winner(all_sentences, obj_a, obj_b, aspects))
    
    else:
        setStatus(statusID, 'Request all sentences containing the objects')
        if aspects:
            json_compl_triples = request_es_triple(obj_a, obj_b, aspects)
        json_compl = request_es_ML(fast_search, obj_a, obj_b)

        setStatus(statusID, 'Extract sentences')
        if aspects:
            all_sentences = extract_sentences(json_compl_triples)
            all_sentences.update(extract_sentences(json_compl))
        else:
            all_sentences = extract_sentences(json_compl)

        if len(all_sentences) == 0:
            return jsonify(find_winner(all_sentences, obj_a, obj_b, aspects)) 
        
        remove_questions(all_sentences)

        setStatus(statusID, 'Prepare sentences for classification')
        prepared_sentences = prepare_sentence_DF(all_sentences, obj_a, obj_b, aspects)

        setStatus(statusID, 'Classify sentences')
        classification_results = classify_sentences(prepared_sentences, model)

        setStatus(statusID, 'Evaluate classified sentences; Find winner')
        final_dict = evaluate(all_sentences, prepared_sentences, classification_results, obj_a, obj_b, aspects)
        
        # print('Obj 1:')
        # find_most_frequent_words(obj_a.name, obj_b.name, final_dict['sentencesObject1'], aspects[0].name)
        # print('Obj 2:')
        # find_most_frequent_words(obj_a.name, obj_b.name, final_dict['sentencesObject2'], aspects[0].name)
        
        
        return jsonify(final_dict)

@app.route('/status', methods=['GET'])
@app.route('/cam/status', methods=['GET'])
def getStatus():
    statusID = request.args.get('statusID')
    return jsonify(status[statusID])

@app.route('/remove/status', methods=['DELETE'])
@app.route('/cam/remove/status', methods=['DELETE'])
def removeStatus():
    statusID = request.args.get('statusID')
    print('Remove registered:', statusID)
    del status[statusID]
    return jsonify(True)

@app.route('/register', methods=['GET'])
@app.route('/cam/register', methods=['GET'])
def register():
    statusID = str(len(status))
    setStatus(statusID, '')
    print('Register:', statusID)
    return jsonify(statusID)


def setStatus(statusID, statusText):
    if statusID != None:
        status[statusID] = statusText


def extract_aspects(request):
    aspects = []
    i = 1
    while i is not False:
        asp = 'aspect{}'.format(i)
        wght = 'weight{}'.format(i)
        inputasp = request.args.get(asp)
        inputwght = request.args.get(wght)
        if inputasp is not None and inputwght is not None:
            asp = Aspect(inputasp.lower(), int(inputwght))
            aspects.append(asp)
            i += 1
        else:
            i = False
    return aspects

class Argument:
    '''
    Argument Class for the objects to be compared
    '''

    def __init__(self, name):
        self.name = name.lower()
        self.points = {}
        self.totalPoints = 0
        self.sentences = []

    def add_points(self, aspect, points):
        self.totalPoints = self.totalPoints + points
        if aspect in self.points:
            self.points[aspect] = self.points[aspect] + points
        else:
            self.points[aspect] = points

    def add_sentence(self, sentence):
        self.sentences.append(sentence)

class Aspect:
    '''
    Aspect Class for the user entered aspects
    '''

    def __init__(self, name, weight):
        self.name = name.lower()
        self.weight = weight


if __name__ == "__main__":
    status = {}
    app.run(host="0.0.0.0", threaded=True, port=10100)
