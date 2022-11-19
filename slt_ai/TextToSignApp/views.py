"""views.py file of TextToSignApp
"""
import os
from deep_translator import GoogleTranslator
from datetime import datetime as dt
# import re
from . import TextToSignUtils as ttsu
from . import WordSubstitutionUtils as wsu

# from urllib.error import HTTPError
from django.shortcuts import render
from django.http import JsonResponse
from django.templatetags.static import static

# Global Objects

gt = GoogleTranslator(source='auto', target='de')

# URLs Functions

def text_to_sign(request):
    """Renders the webpage of TextToSignApp

    Args:
        request (http_request): _description_

    Returns:
        response: an html page rendered
    """

    return render(request, 'TextToSignApp/textToSign.html')


def text_to_text_translate(request):
    """Translate text into text of some other language Use google translate.

    Args:
        request (_type_): get request object containing some text and source and target language codes.

    Returns:
        JsonResponse: a dict of translation of the given text into the given target language
    """

    gt.source = request.GET['src']
    gt.target = request.GET['tgt']
    translation = gt.translate(str(request.GET['txt']))
    return JsonResponse({'translation':translation})
 
def restructure(request):
    """summarize and Rearrange the words of a sentence into the grammar of a sign language.

    Args:
        request (_type_): _description_

    Returns:
        _type_: _description_
    """

    sentence = request.GET['txt']
    if request.GET['lan'] == 'en':
        pass # result = en2psl_model.predict(sentence)
    elif request.GET['lan'] == 'ur':
        pass # result = ur2psl_model.predict(sentence)
    
    return JsonResponse({'modified_txt': sentence[::-1] })

def substitute(request):
    """find supported synonyms for unsupported words

    Args:
        request (_type_): _description_

    Returns:
        _type_: _description_
    """

    sentence = request.GET['txt']
    words = sentence.split(' ') # re.split('\s{1,}',sentence) # collapse whitespace with JS
    substitutes = {}

    word2file = wsu.ur_supportedWord2file    if request.GET['lan'] == 'ur' else wsu.en_supportedWord2file
    ambiguous = wsu.ur_ambiguous2resolved    if request.GET['lan'] == 'ur' else wsu.en_ambiguous2resolved
    compounds = wsu.ur_firstSubword2compound if request.GET['lan'] == 'ur' else wsu.en_firstSubword2compound

    for i,word in enumerate(words):
        clean_word = ttsu.del_punctuation(word)
        if request.GET['lan'] == 'en':
            clean_word = clean_word.lower()

        if clean_word == '':
            continue

        # a is ambiguous --> a = letter , a = a(1) 
        # پاس is ambiguous --> pass, near

        try: # if word is a known/supported ambiguous word, return resolved words
            substitutes[word] = ambiguous[clean_word]
        except KeyError: # some non-ambiguous or unknown or both
            try:
                # PSL clip exists/ word is supported
                word2file[clean_word] # throws key-error
            except KeyError: 
                # PSL clip doesnot exist so return the one for which a clip does exist
                substitutes[word] = wsu.find_available(clean_word, request.GET['lan'], top_n=8, threshold=0.3)

        try: # some supported compound word starts with this word
            compound_words = compounds[clean_word]
            for c_word in compound_words:
                num_subwords = c_word.count('-')+1

                candidates = [ttsu.del_punctuation(w) for w in words[i:i+num_subwords]]

                if '-'.join(candidates) == c_word:
                    try: # ??? will this try block ever be successfull ???
                        substitutes[c_word.replace('-',' ')] .append(c_word)
                    except KeyError:
                        substitutes[c_word.replace('-',' ')] =      [c_word]   
        except KeyError:
            pass # no compound word starting with this word


    context ={  'lan':request.GET['lan'],
                'substitutes':substitutes   }
    
    # match top 5000 words with book, store top matches from book for each of 5000, analyse manually
    return render(request, 'TextToSignApp/availableWords.html', context)

# concat =  3*duration
# write  = 20*duration (1080p)

def create(request): 
    """render a video clip for a given sentence

    Args:
        request (_type_): _description_

    Returns:
        _type_: _description_
    """
    sentence = request.GET['txt']
    filename = sentence.replace('/',"").replace('\\','').replace('*','').replace('<','').replace('>','').replace('"','').replace('?','').replace(':','')
    filename = ttsu.del_punctuation(filename)
    path = os.path.abspath(os.path.join('..','TextToSign','static','videos',f'{filename}.mp4'))
    
    if not os.path.exists(path):
        _ = print(sentence) if request.GET['lan'] == 'en' else print(sentence[::-1])
        print('initiating synthesis.\t\t\t',dt.now())
        video = ttsu.textToSign(sentence, request.GET['lan'], trim_mode='smart',video_width=int(request.GET['res']))
        # send httpStreaming response without saving the the video to disk
        # use the video.iter_frames() generator
        # buffer on client side to enable seek/download
        # or live stream the frames in <img>
        print(f'writing video ({round(video.duration,1)}sec) to disk. \t',dt.now())
        video.write_videofile(path, audio=False, threads = 10, verbose=False,logger=None)
        print('sending response\t\t\t',dt.now())
        
    return JsonResponse({'video': static(f'videos/{filename}.mp4'), 'sentence': sentence })