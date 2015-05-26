# -*- coding: utf-8 -*-
#!/usr/bin/env python

import sys
import re
from math import sqrt
from heapq import nlargest

def create_synonyms_dictionary(synonyms_file):
  synonyms = {}
  with open(synonyms_file) as f:
    for line in f:
      words = unicode(line, "utf-8").split(', ')
      for word in words[1:]:
        synonyms[word] = words[0]
  return synonyms

def get_stoplist(stoplist_file):
  stoplist = {}
  with open(stoplist_file) as f:
    for line in f:
      stoplist[unicode(line, "utf-8").strip()] = True
  return stoplist

def vectorize(corpus_file, synonyms):
  with open(corpus_file) as f:
    data = unicode(f.read(), "utf-8")
  data = re.findall(ur"(#[\d]+)([^#]*)(?#[\d]+)", data, re.DOTALL)
  labels = []
  documents = []

  for item in data:
    labels.append(item[0])
    value = [word.lower() for word in re.findall(ur"[a-zA-ZżółćęśąźńŻÓŁĆĘŚĄŹŃ]+", item[1])]
    value = [synonyms[word] if word in synonyms else word for word in value]
    documents.append(value)

  return labels, documents

def wordcount(documents, document_frequency=False):
  words = {}
  for document in documents:
    checked = {}
    for word in document:
      if document_frequency == False or word not in checked:
        if word not in words:
          words[word] = 1.
        else:
          words[word] += 1.
      checked[word] = True
  return words

def filter_words_in_documents(documents, hapax_legomena, too_frequent_terms, stoplist):
  for i in xrange(len(documents)):
    documents[i] = [word for word in documents[i] if word not in hapax_legomena and word not in too_frequent_terms and word not in stoplist]
  return documents

def make_graph(documents, k):
  graph_documents = []
  for p in xrange(len(documents)):
    graph_documents.append({})
    for current_k in xrange(0,k+1):
      for j in xrange(0, len(documents[p])-current_k):
        key = (documents[p][j], documents[p][j+current_k])
        if key in graph_documents[p]:
          graph_documents[p][key] += 1.
        else:
          graph_documents[p][key] = 1.
  return graph_documents

def cosine_distance_generator(document_a):
  distance_a = sqrt(sum([x*x for x in document_a.values()]))

  def cosine_distance(document_b):
    distance = 0.
    for word in document_a:
      if word in document_b:
        distance += document_a[word] * document_b[word]
    distance /= distance_a
    distance_b = sqrt(sum([x*x for x in document_b.values()]))
    distance /= distance_b
    return distance
  return cosine_distance

def find_by_document_id(graph, document_id, limit=10):
  my_document = graph[document_id]
  cosine_distance = cosine_distance_generator(graph[document_id])

  max_list = []
  for i in xrange(len(graph)):
    max_list.append((i, cosine_distance(graph[i])))
  return nlargest(limit, max_list, key=lambda e:e[1])


if __name__ == '__main__':
  if len(sys.argv) >= 5:
    corpus_file = sys.argv[1]
    synonyms_file = sys.argv[2]
    stoplist_file = sys.argv[3]
    vector_label = unicode(sys.argv[4], "utf-8")
    k = int(sys.argv[5]) if len(sys.argv) >= 6 else 3
    limit_for_results = int(sys.argv[6]) if len(sys.argv) >= 7 else 10

    synonyms = create_synonyms_dictionary(synonyms_file)
    stoplist = get_stoplist(stoplist_file)
    labels, documents = vectorize(corpus_file, synonyms)

    words = wordcount(documents)
    hapax_legomena = {k : v for k, v in words.iteritems() if v == 1.}
    df = wordcount(documents, document_frequency=True)
    limit = len(documents)*0.7
    too_frequent_terms = {k : v for k, v in words.iteritems() if v > limit}

    print "all words: ", len(words)
    print "all documents: ", len(labels)
    print "hapax legomena: ", len(hapax_legomena)
    print "too frequent terms: ", len(too_frequent_terms)
    print "stoplist: ", len(stoplist)

    documents = filter_words_in_documents(documents, hapax_legomena, too_frequent_terms, stoplist)
    graph = make_graph(documents, k)

    vector_id = labels.index(vector_label)
    cosine_distance = cosine_distance_generator(graph[vector_id])

    found_documents = find_by_document_id(graph, vector_id, limit_for_results)
    for document in found_documents:
      print(labels[ document[0] ] + " : " + str(document[1]))

  else:
    print("python -p graph_stats [corpus] [synonyms] [stoplist] [vector_label] [k=3] [limit for results=10]")
