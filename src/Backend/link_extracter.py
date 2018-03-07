import constants
import re
import nltk
from nltk import word_tokenize


def extract_main_links(sentencesA, sentencesB, objA, objB):
    '''
    Extracts the most common words from a list of strings.

    sentences:  List
                list of strings
    '''
    # stores all words for object A as keys and the number of times they've been found as values
    worddictA = {}
    # stores all words for object B as keys and the number of times they've been found as values
    worddictB = {}
    for s in sentencesA:
        # find all words in the sentence
        wordlist = re.compile('[A-Za-z]+').findall(s)
        for w in wordlist:
            w = w.lower()
            # check if w is "useful" as a links
            if w not in constants.STOPWORDS and w not in constants.POSITIVE_MARKERS and w not in \
                    constants.NEGATIVE_MARKERS and w != objA and w != objB and w not in \
                    constants.NON_LINKS and w not in constants.NUMBER_STRINGS:
                if w in worddictA:
                    worddictA[w] += 1
                else:
                    worddictA[w] = 1
    for s in sentencesB:
        # find all words in the sentence
        wordlist = re.compile('[A-Za-z]+').findall(s)
        for w in wordlist:
            w = w.lower()
            # check if w is "useful" as a links
            if w not in constants.STOPWORDS and w not in constants.POSITIVE_MARKERS and w not in \
                    constants.NEGATIVE_MARKERS and w != objA and w != objB and w not in \
                    constants.NON_LINKS and w not in constants.NUMBER_STRINGS:
                if w in worddictB:
                    worddictB[w] += 1
                else:
                    worddictB[w] = 1
    result = {}
    resultA = []
    resultB = []
    # return the top 10 links for A, B and both
    rem_temp_list_A = []
    rem_temp_list_B = []
    for word in worddictA:
        tag = nltk.pos_tag(word)[0][1]
        if not tag.startswith('NN'):
            rem_temp_list_A.append(word)
    for word in rem_temp_list_A:
        worddictA.pop(word)
    for word in worddictB:
        tag = nltk.pos_tag(word)[0][1]
        if not tag.startswith('NN'):
            rem_temp_list_B.append(word)
    for word in rem_temp_list_B:
        worddictB.pop(word)
    for word in worddictA:
        if word in worddictB:
            worddictA[word] = worddictA[word] / worddictB[word]
            worddictB[word] = worddictB[word] / worddictA[word]
    while (len(resultA) < 10 and len(resultB) < 10 and (worddictA or worddictB)):
        if worddictA:
            maxA = max(worddictA, key=worddictA.get)
            resultA.append(maxA)
            worddictA.pop(maxA)
        if worddictB:
            maxB = max(worddictB, key=worddictB.get)
            resultB.append(maxB)
            worddictB.pop(maxB)
    result['A'] = resultA
    result['B'] = resultB
    return result
