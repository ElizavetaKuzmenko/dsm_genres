# coding: utf-8
from flask import Flask
from flask import request, render_template
import os, codecs, logging, gensim, sys

app = Flask(__name__)

import ConfigParser, socket

config = ConfigParser.RawConfigParser()
config.read('dsm_genres.cfg')

# Establishing connection to model server
host = config.get('Sockets', 'host')
port = config.getint('Sockets', 'port')
try:
    remote_ip = socket.gethostbyname(host)
except socket.gaierror:
    # could not resolve
    print >> sys.stderr, 'Hostname could not be resolved. Exiting'
    sys.exit()


def serverquery(message):
    # create an INET, STREAMing socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except socket.error:
        print >> sys.stderr, 'Failed to create socket'
        return None

    # Connect to remote server
    s.connect((remote_ip, port))
    # Now receive data
    reply = s.recv(1024)

    # Send some data to remote server
    try:
        s.sendall(message.encode('utf-8'))
    except socket.error:
        # Send failed
        print >> sys.stderr, 'Send failed'
        s.close()
        return None
    # Now receive data
    reply = s.recv(32768)
    s.close()
    return reply

# todo: config is not working, fix it
# root = config.get('Files and directories', 'root')
root = '/home/kender/Docs/bigdata/genres/dsm_genres/'
# modelsfile = config.get('Files and directories', 'models')
modelsfile = 'models.csv'
# temp = config.get('Files and directories', 'temp')
# tags = config.getboolean('Tags', 'use_tags')
tags = True
# lemmatize = config.getboolean('Other', 'lemmatize')
lemmatize = True
# dbpedia = config.getboolean('Other', 'dbpedia_images')
if lemmatize:
    from tagger import tagword, tagsentence
# taglist = set(config.get('Tags', 'tags_list').split())
# defaulttag = config.get('Tags', 'default_tag')
default_tag = 'SUBST'
tags_list = 'ADJ VERB SUBST UNC ADV'
taglist = set(tags_list.split())

our_models = {}
for line in open(root + modelsfile, 'r').readlines():
    if line.startswith("#"):
        continue
    res = line.strip().split('#')
    (identifier, path) = res
    our_models[identifier] = path


logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

models_dic = {}
for m in our_models:
    models_dic[m] = gensim.models.Word2Vec.load(root + our_models[m])
    models_dic[m].init_sims(replace=True)
    print >> sys.stderr, "Model", m, "from file", our_models[m], "loaded successfully."


def jaccard(set_1, set_2):
    n = len(set_1 & set_2)
    return n / float(len(set_1) + len(set_2) - n)


def process_query(userquery):
    userquery = userquery.strip()
    if tags:
        if '_' in userquery:
            query_split = userquery.split('_')
            if query_split[-1] in taglist:
                query = ''.join(query_split[:-1]).lower() + '_' + query_split[-1]
            else:
                return 'Incorrect tag!'
        else:
            if lemmatize:
            #pos_tag = freeling_lemmatizer(userquery)
            #if pos_tag == 'A' and userquery.endswith(u'о'):
            #    pos_tag = 'ADV'
            #query = userquery.lower() + '_' + pos_tag
                query = tagword(userquery)
            else:
                return 'Incorrect tag!'
    return query





@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        input_data = 'dummy'
        try:
            input_data = request.form['query']
        except:
            pass
        if input_data != 'dummy' and input_data.replace('_', '').replace('-', '').isalnum():
            query = process_query(input_data)
            if query == 'Incorrect tag!':
                error = query
                return render_template('home.html', error=error)
            #query = query.split('_')
            message = "1;" + query + ";" + 'ALL'
            associates = serverquery(message)
            #associates = find_synonyms(query)
            distances = {}
            for m in models_dic:
                if m == 'all':
                    continue
                set_1 = set([x.split('#')[0] for x in associates['all']])
                set_2 = set([x.split('#')[0] for x in associates[m]])
                distance = 1 - jaccard(set_1, set_2)
                distances[m] = distance
            return render_template('home.html', result=associates, word=query[0], pos=query[1], distances=distances)
    return render_template('home.html')


@app.route('/genres', methods=['GET', 'POST'])
def genres():
    if request.method == 'POST':
        input_data = 'dummy'
        try:
            input_data = request.form['query']
        except:
            pass
        if input_data != 'dummy' and input_data.replace('_', '').replace('-', '').isalnum():
            query = process_query(input_data)
            if query == "Incorrect tag!":
                return render_template('genres.html', error=query)
            model_value = request.form.getlist('model')
            if len(model_value) < 1:
                model = defaultmodel
            else:
                model = model_value[0]
            message = "1;" + query + ";" + 'ALL' + ";" + model
            result = ''  # todo: get result
            associates_list = []
            if "unknown to the" in result or "No result" in result:
                return render_template('home.html', error=result.decode('utf-8'))
            else:
                output = result.split('&')
                associates = output[0]
                for word in associates.split():
                    w = word.split("#")
                    associates_list.append((w[0].decode('utf-8'), float(w[1])))

                return render_template('home.html', list_value=associates_list, word=query, model=model, tags=tags)
        else:
            error_value = u"Incorrect query!"
            return render_template("home.html", error=error_value, tags=tags)
    return render_template('home.html', tags=tags)


if __name__ == '__main__':
    app.run()
