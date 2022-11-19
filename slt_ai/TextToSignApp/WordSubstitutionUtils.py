
#################################################################
#################################################################

import numpy as np
def read_embeddings(path):
    dic={}
    with open(path, encoding='utf-8') as f:
        rows, dim = map(int,f.readline().split(' '))
        
        for i in range(rows):
            row = f.readline().split(' ')
            dic[row[0].replace('_',' ')] = np.array(row[1:], dtype=np.float32)
            
    return dic

#################################################################
#################################################################

import json
def read_dict(path):
    with open(path,encoding='utf-8') as f:
        dic = json.load(f)
    return dic

#################################################################
#################################################################

ur2embd                  = read_embeddings('static/txt/ur_mini_embeddings.txt') #'static/txt/W2V300dim5winBulk.txt'
en2embd                  = read_embeddings('static/txt/en_mini_embeddings.txt') #'static/txt/English_W2V_100dm.txt'
ur_supportedWord2embd    = read_embeddings('static/txt/ur_supportedWords_embeddings.txt')
en_supportedWord2embd    = read_embeddings('static/txt/en_supportedWords_embeddings.txt')
ur_supportedWord2file    = read_dict('static/txt/ur_supportedWord2file.json')
en_supportedWord2file    = read_dict('static/txt/en_supportedWord2file.json') # airplane, aeroplane --> aeroplane.mp4
ur_ambiguous2resolved    = read_dict('static/txt/ur_ambiguous2resolved.json')
en_ambiguous2resolved    = read_dict('static/txt/en_ambiguous2resolved.json')
ur_firstSubword2compound = read_dict('static/txt/ur_firstSubword2compound.json')
en_firstSubword2compound = read_dict('static/txt/en_firstSubword2compound.json')
ur_supported_words            = np.array(list(ur_supportedWord2embd.keys  ()))
en_supported_words            = np.array(list(en_supportedWord2embd.keys  ()))
ur_supported_words_embeddings = np.array(list(ur_supportedWord2embd.values()))
en_supported_words_embeddings = np.array(list(en_supportedWord2embd.values()))
# file2ur_word            = read_dict('static/txt/file2ur_word.json')
# file2en_word             = read_dict('file2en_word.json')
# ur_substitutes = read_dict('static/txt/ur_substitutes.json')
# en_substitutes = read_dict('static/txt/ur_substitutes.json') # path, way --> road



#################################################################
#################################################################

from sklearn.metrics.pairwise import cosine_similarity

def find_available(word, language, top_n=5,threshold=0.5):
    if language == 'ur':
        word2embd, supported_words_embeddings, supported_words, ambiguous2resolved =  ur2embd, ur_supported_words_embeddings, ur_supported_words, ur_ambiguous2resolved
    elif language == 'en':
        word2embd, supported_words_embeddings, supported_words, ambiguous2resolved =  en2embd, en_supported_words_embeddings, en_supported_words, en_ambiguous2resolved
    else:
        return []

    # try:
    #     return substitutes[word] #pre-computed
    # except:
    try:
        # if embedding exists then compute similarities
        word_embedding = word2embd[word] 
        similarities   = cosine_similarity( word_embedding.reshape(1,-1),
                                            supported_words_embeddings    ).flatten()
    except:             
        # if embedding does not exist, return empty meaning no substitutes are available
        return []
        
    top_n_indexes        = similarities.argsort()[-top_n:] # get indexes of top 5 values in array
    top_n_thresh_indexes = top_n_indexes[similarities[top_n_indexes]>=threshold] # filter values > threshold out of those top 5

    fresh_substitutes = []
    for s_word in supported_words[top_n_thresh_indexes]:
        try:
            fresh_substitutes.extend(ambiguous2resolved[s_word])
        except:
            fresh_substitutes.append(                   s_word )
    
    fresh_substitutes.reverse()
    return fresh_substitutes

#################################################################
#################################################################



#################################################################
#################################################################
