#!/usr/bin/python2
# coding: utf-8
import ConfigParser
import json
import logging
import operator
import socket
import sys
from flask import render_template, Blueprint
from flask import request
from sparql import getdbpediaimage
from flask import send_from_directory
import codecs
from tau import robusttau

config = ConfigParser.RawConfigParser()
config.read('dsm_genres.cfg')

root = config.get('Files and directories', 'root')
modelsfile = config.get('Files and directories', 'models')
our_models = {}

for line in open(root + modelsfile, 'r').readlines():
    if line.startswith("#"):
        continue
    res = line.strip().split('\t')
    (identifier, description, path, default) = res
    our_models[identifier] = description

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

url = config.get('Other', 'url')

tags = config.getboolean('Tags', 'use_tags')

lemmatize = config.getboolean('Other', 'lemmatize')
if lemmatize:
    from tagger import tagword

# Establishing connection to model server
host = config.get('Sockets', 'host')
port = config.getint('Sockets', 'port')
try:
    remote_ip = socket.gethostbyname(host)
except socket.gaierror:
    # could not resolve
    print >> sys.stderr, 'Hostname could not be resolved. Exiting'
    sys.exit()

taglist = set(config.get('Tags', 'tags_list').split())
defaulttag = config.get('Tags', 'default_tag')
cachefile = config.get('Files and directories', 'image_cache')

genre = Blueprint('genres', __name__, template_folder='templates')


def jaccard(set_1, set_2):
    n = len(set_1 & set_2)
    return n / float(len(set_1) + len(set_2) - n)


def process_query(userquery):
    query = userquery.strip()
    if '_' in query:
        query_split = query.split('_')
        if query_split[-1] in taglist:
            query = ''.join(query_split[:-1]).lower() + '_' + query_split[-1]
        else:
            return 'Incorrect tag!'
    else:
        if lemmatize:
            query = tagword(query)
        else:
            return 'Incorrect tag!'
    return query


def serverquery(message):
    # create an INET, STREAMing socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except socket.error:
        print >> sys.stderr, 'Failed to create socket'
        return None

    # Connect to remote server
    s.connect((remote_ip, 15666))
    # Now receive data
    s.recv(1024)

    # Send some data to remote server
    try:
        s.sendall(message.encode('utf-8'))
    except socket.error:
        # Send failed
        print >> sys.stderr, 'Send failed'
        s.close()
        return None
    # Now receive data
    reply = s.recv(65536)
    s.close()
    return reply


@genre.route(url, methods=['GET', 'POST'])
def genrehome():
    if request.method == 'POST':
        try:
            input_data = request.form['query']
        except:
            print >> sys.stderr, 'Error!'
            return render_template('home.html', error="Something wrong with your query!")
        if input_data.replace('_', '').replace('-', '').isalnum():
            query = process_query(input_data)
            if query == 'Incorrect tag!':
                error = query
                return render_template('home.html', error=error)
            message = "1;" + query + ";" + 'ALL'
            associates = json.loads(serverquery(message))
            distances = {}
            images = {}
            images[query.split('_')[0]] = None
            frequencies = {}
            for m in our_models:
                fmessage = "4;" + query + ";" + m
                frequencies[m] = int(serverquery(fmessage))
                if m == 'all':
                    continue
                set_1 = [x[0] for x in associates['all']]
                set_2 = [x[0] for x in associates[m]]
                for word in set_2:
                    images[word.split('_')[0]] = None
                distance = -robusttau(set_1, set_2)
                distances[m] = round(distance, 2)
            distances_r = sorted(distances.items(), key=operator.itemgetter(1))
            values = [x[1] for x in distances_r]
            mindist = min(values)
            if mindist < 0:
        	distances_r2 = []
        	for el in distances_r:
        	    el0 = el[0]
        	    el1 = el[1] + abs(mindist)
        	    if el1 > 1:
        		el1 = 1
        	    distances_r2.append((el0, el1))
    		distances_r = distances_r2
            imagecache = {}
            imagedata = codecs.open(root + cachefile, 'r', 'utf-8')
            for line in imagedata:
                res = line.strip().split('\t')
                (word, image) = res
                imagecache[word.strip()] = image.strip()
            imagedata.close()
            for w in images:
                image = getdbpediaimage(w.encode('utf-8'), imagecache)
                if image:
                    images[w] = image
            return render_template('home.html', result=associates, word=query.split('_')[0], pos=query.split('_')[-1],
                                   distances=distances_r, models=our_models, wordimages=images, freq=frequencies)
    return render_template('home.html')


@genre.route(url+'word/<word>/', methods=['GET', 'POST'])
def genreword(word):
    input_data = word
    if request.method == 'POST':
        input_data = request.form['query']
    if input_data.replace('_', '').replace('-', '').isalnum():
        query = process_query(input_data)
        if query == 'Incorrect tag!':
            error = query
            print >> sys.stderr, 'Error!'
            return render_template('home.html', error=error)
        message = "1;" + query + ";" + 'ALL'
        associates = json.loads(serverquery(message))
        distances = {}
        images = {}
        images[query.split('_')[0]] = None
        frequencies = {}
        for m in our_models:
            fmessage = "4;" + query + ";" + m
            frequencies[m] = int(serverquery(fmessage))
            if m == 'all':
                continue
            set_1 = [x[0] for x in associates['all']]
            set_2 = [x[0] for x in associates[m]]
            for word in set_2:
                images[word.split('_')[0]] = None
            distance = -robusttau(set_1, set_2)
            distances[m] = round(distance, 2)
        distances_r = sorted(distances.items(), key=operator.itemgetter(1))
        values = [x[1] for x in distances_r]
        mindist = min(values)
        if mindist < 0:
            distances_r2 = []
            for el in distances_r:
                el0 = el[0]
        	el1 = el[1] + abs(mindist)
        	if el1 > 1:
        	    el1 = 1
        	distances_r2.append((el0, el1))
    	    distances_r = distances_r2
        imagecache = {}
        imagedata = codecs.open(root + cachefile, 'r', 'utf-8')
        for line in imagedata:
            res = line.strip().split('\t')
            (word, image) = res
            imagecache[word.strip()] = image.strip()
        imagedata.close()
        for w in images:
            image = getdbpediaimage(w.encode('utf-8'), imagecache)
            if image:
                images[w] = image
        return render_template('home.html', result=associates, word=query.split('_')[0], pos=query.split('_')[-1],
                               distances=distances_r, models=our_models, wordimages=images, freq=frequencies)
    return render_template('home.html')


@genre.route(url+'concordance/<word>/<register>/', methods=['GET'])
def genreconcordance(word, register):
    if word.replace('_', '').replace('-', '').isalnum():
        message = "3;" + word.strip().encode('utf-8')
        sentences = json.loads(serverquery(message))
        if not 'Error' in sentences:
            result = sentences[register]
            result2 = []
            for sentence in result:
                slemmas = ['_'.join(w.split('_')[1:]) for w in sentence]
                position = slemmas.index(word)
                if position < 6:
                    add = ['...'] * (6-position)
                    sentence = add + sentence
                    slemmas = ['_'.join(w.split('_')[1:]) for w in sentence]
                    position = slemmas.index(word)
                newsentence = sentence[position-6:position+6]
                newsentence = ['...']+newsentence+['...']
                result2.append(newsentence)
            return render_template('concordance.html', result=result2, word=word, register=register, models=our_models)
        else:
            error = sentences['Error']
            return render_template('concordance.html', error=error)



@genre.route(url+'text/', methods=['GET', 'POST'])
def genretext():
    if request.method == 'POST':
        try:
            input_data = request.form['textquery']
        except:
            print >> sys.stderr, 'Error!'
            return render_template('text.html', error="Something wrong with your query!")

        query = input_data.strip().replace('\r\n', ' ')
        message = "2;" + query
        result = json.loads(serverquery(message))
        lemmas = result['words']
        result.pop('words')
        result.pop('all')
        ranking = sorted(result.items(), key=operator.itemgetter(1), reverse=True)
        return render_template('text.html', result=ranking, text=input_data, models=our_models, lemmas=lemmas,
                               tags=taglist)
    return render_template('text.html')


@genre.route(url+'about/', methods=['GET'])
def genreabout():
    return render_template('about.html')
