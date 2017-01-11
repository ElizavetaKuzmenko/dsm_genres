#!/usr/bin/python2
# coding: utf-8

import ConfigParser
import datetime
import json
import socket
import sys
from thread import *

import gzip
import gensim
import logging
import numpy as np

from tagger import tagsentence

config = ConfigParser.RawConfigParser()
config.read('dsm_genres.cfg')

root = config.get('Files and directories', 'root')
HOST = config.get('Sockets', 'host')  # Symbolic name meaning all available interfaces
PORT = config.getint('Sockets', 'port')  # Arbitrary non-privileged port
tags = config.getboolean('Tags', 'use_tags')

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

# Loading models

our_models = {}
for line in open(root + config.get('Files and directories', 'models'), 'r').readlines():
    if line.startswith("#"):
        continue
    res = line.strip().split('\t')
    (identifier, description, path, default) = res
    our_models[identifier] = path

models_dic = {}

for mod in our_models:
    if our_models[mod].endswith('.bin.gz'):
        models_dic[mod] = gensim.models.Word2Vec.load_word2vec_format(our_models[mod], binary=True)
    else:
        models_dic[mod] = gensim.models.Word2Vec.load(our_models[mod])
    print >> sys.stderr, "Model", mod, "from file", our_models[mod], "loaded successfully."

# Loading concordance data

concordance = config.get('Other', 'concordance')
data = gzip.open(root+concordance,'r')
concordance_data = json.loads(data.read())
data.close()
print >> sys.stderr, 'Concordance loaded from', root+concordance

# Vector functions

def find_frequency(query):
    (q,model) = query
    lemma = q.split('_')[0]
    pos = q.split('_')[-1]
    m = models_dic[model]
    noresults = False
    if q not in m:
        candidates_set = set()
        candidates_set.add(q.upper())
        if tags:
            candidates_set.add(lemma + '_UNKN')
            candidates_set.add(lemma.lower() + '_' + pos)
            candidates_set.add(lemma.capitalize() + '_' + pos)
        else:
            candidates_set.add(q.lower())
            candidates_set.add(q.capitalize())
        noresults = True
        for candidate in candidates_set:
            if candidate in m:
                q = candidate
                noresults = False
                break
    if noresults:
        return 0
    frequency = m.wv.vocab[q].count
    return frequency



def find_synonyms(query):
    (q, posfilter) = query
    results = {}
    lemma = q.split('_')[0]
    pos = q.split('_')[-1]
    for model in models_dic:
        m = models_dic[model]
        noresults = False
        if q not in m:
            candidates_set = set()
            candidates_set.add(q.upper())
            if tags:
                candidates_set.add(lemma + '_UNKN')
                candidates_set.add(lemma.lower() + '_' + pos)
                candidates_set.add(lemma.capitalize() + '_' + pos)
            else:
                candidates_set.add(q.lower())
                candidates_set.add(q.capitalize())
            noresults = True
            for candidate in candidates_set:
                if candidate in m:
                    q = candidate
                    noresults = False
                    break
        if noresults:
            results[model] = [q + " is unknown to the model"]
            continue
        if posfilter == 'ALL':
            results[model] = [(i[0], i[1]) for i in m.most_similar(positive=q, topn=50) if i[0].split('_')[-1] == pos][
                             :10]
        else:
            results[model] = [(i[0], i[1]) for i in m.most_similar(positive=q, topn=20) if
                              i[0].split('_')[-1] == posfilter][:10]
    return results


def classify(text):
    text = text[0].strip()
    sentences = tagsentence(text.encode('ascii', 'replace'))
    results = {}
    for model in models_dic:
        m = models_dic[model]
        sc = m.score(sentences, total_sentences=len(sentences))
        sc = np.median(sc)
        sc = np.float(sc)
        results[model] = sc
    results['words'] = sentences
    return results

def concordance(word):
    word = word[0]
    if word in concordance_data:
        return concordance_data[word]
    else:
        return {'Error': 'Word not it concordance data'}


operations = {'1': find_synonyms, '2': classify, '3': concordance, '4': find_frequency}

# Bind socket to local host and port

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print >> sys.stderr, 'Socket created'

try:
    s.bind((HOST, PORT))
except socket.error, msg:
    print >> sys.stderr, 'Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
    sys.exit()

print >> sys.stderr, 'Socket bind complete'

# Start listening on socket
s.listen(100)
print >> sys.stderr, 'Socket now listening on port', PORT


# Function for handling connections. This will be used to create threads
def clientthread(conn, addr):
    # Sending message to connected client
    conn.send('word2vec model server')  # send only takes string

    # infinite loop so that function do not terminate and thread do not end.
    while True:
        # Receiving from client
        data = conn.recv(1024)
        data = data.decode("utf-8")
        if not data:
            break
        query = data.split(";")
        output = operations[query[0]]((query[1:]))
        now = datetime.datetime.now()
        print >> sys.stderr, now.strftime("%Y-%m-%d %H:%M"), '\t', addr[0] + ':' + str(addr[1]), '\t', data
        if query[0] == '4':
            reply = str(output)
        else:
            reply = json.dumps(output)
        conn.sendall(reply.encode('utf-8'))
        break

    # came out of loop
    conn.close()


# now keep talking with the client
while 1:
    # wait to accept a connection - blocking call
    connection, address = s.accept()

    # start new thread takes 1st argument as a function name to be run,
    # second is the tuple of arguments to the function.
    start_new_thread(clientthread, (connection, address))

s.close()
