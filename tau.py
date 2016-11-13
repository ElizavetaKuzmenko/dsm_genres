#!/usr/bin/python2
# coding: utf-8

from scipy.stats import kendalltau


def robusttau(a, b):
    lexicon = set(a+b)
    intersection = set(a) & set(b)
    if len(intersection) == 0:
        return -1
    ranking_a = []
    ranking_b = []
    for word in lexicon:
	if word in a:
	    ranking_a.append(a.index(word))
	else:
	    ranking_a.append(1000)
	if word in b:
	    ranking_b.append(b.index(word))
	else:
	    ranking_b.append(1000)
    corr, p = kendalltau(ranking_a, ranking_b)
    return corr
