# dsm_genres
Language registers explorer powered by word embeddings.

This is the framework behind the web service http://ltr.uio.no/embeddings/registers/ accompanying the following paper:
A. Kutuzov, A.Marakasova, and E. Kuzmenko. Exploration of register-dependent lexical semantics using word embeddings. In Proceedings of the Workshop on Language Technology Resources and Tools for Digital Humanities (LT4DH), pp. 26-34. COLING 2016, Osaka, Japan.
https://www.clarin-d.net/images/lt4dh/pdf/LT4DH05.pdf

This source code can be easily adapted to any set of distributional models.

## Installation

1. Clone the repository
2. Tune the config file dsm_genres.cfg according to your setup (especially <i>root</i> and <i>url</i> parameters)
3. Put your models into the <i>models</i> subdirectory (models can be either in gzipped binary word2vec format or in Gensim format)
4. Describe your models in the models.csv file; the model with all identifier will serve as the reference one
5. NB: we presuppose that your models use words augmented with PoS tags ('boot_VERB'); if they don't, you'll have to tune the code a bit
6. Download Stanford Core NLP suite (https://stanfordnlp.github.io/CoreNLP/); we use it for linguistic processing of the queries
7. Run Core NLP in the background (something like java -mx2g -cp "*" edu.stanford.nlp.pipeline.StanfordCoreNLPServer --port 9999)
8. Run the script word2vec_server_genres.py in the background; it loads the models, stays in memory and answers queries from the web interface
9. Install Gunicorn (http://gunicorn.org/)
10. Run the service with something like gunicorn run_explorer:app_explorer -b 127.0.0.1:10000
11. If your <i>url</i> parameter was set to "/mymodels/", your service should now be available at http://127.0.0.1:10000/mymodels/

In case you have any questions about the code, feel free to ask us. Our contacts can be found at http://ltr.uio.no/embeddings/registers/about






