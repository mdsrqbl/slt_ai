"""views.py file of SignToTextApp
"""
import os
import csv
import numpy as np

from django.shortcuts import render
from django.http import JsonResponse
from django.templatetags.static import static

# URLs Functions

def sign_to_text(request):
    """render the webpage

    Args:
        request (_type_): _description_

    Returns:
        _type_: _description_
    """

    context =  {'var':5}
    return render(request, 'SignToTextApp/signToText.html',context)

def translate_PSL(request):
    """ translate a sequence of poses into text

    Args:
        request (_type_): _description_

    Returns:
        _type_: _description_
    """

    duration  = float(request.POST['duration'])
    pose = request.POST['pose_landmarks']
    hand = request.POST['hand_landmarks']

    pose = np.array(pose.split('%2C'), dtype=float).reshape((-1,33,4))
    hand = np.array(hand.split('%2C'), dtype=float).reshape((-1,42,3))

    fps = len(pose)/duration
    print(len(pose), len(hand),duration,fps)

    write_landmarks_in_csv(pose, os.path.abspath(os.path.join('.','static','csv','pose.csv')))
    write_landmarks_in_csv(hand, os.path.abspath(os.path.join('.','static','csv','hand.csv')))

    # ur_model.predict(pose,hand)
    # en_model.predict(pose,hand)

    return JsonResponse({'en_gloss':'i go school tomorrow',
                         'ur_gloss':'میں اسکول جانا کل',
                         'en_sentence':'I will go to school tomorrow.',
                         'ur_sentence':'میں کل اسکول جاؤں گا۔'       })

pose_header = [title for i in range(0, 33)  for title in [f'x{i}', f'y{i}', f'z{i}', f'v{i}'] ]
#pose_header= ['x0','y0','z0','v0',   'x1','y1','z1','v1',   ...  ,    'x32','y32','z32','v32']
hand_header = [title for i in range(0, 42)  for title in [f'x{i}', f'y{i}', f'z{i}'         ] ]
#hand_header= ['x0','y0','z0',        'x1','y1','z1',        ...  ,    'x41','y41','z41'      ]

def write_landmarks_in_csv( landmarks, path ):
    """just a place holder function that saves input pose data

    Args:
        landmarks (_type_): _description_
        path (_type_): _description_
    """

    header = pose_header if landmarks.shape[1] == 33 else hand_header

    with open(path, mode='w', newline='') as f:
        csv_writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

        csv_writer.writerow(header)
        for frame in landmarks:
            csv_writer.writerow(frame.flatten()) #1 frame per row