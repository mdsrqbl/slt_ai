import os
import re
import numpy as np
import pandas as pd
import moviepy.editor as mpy
from . import ClipUtils as cu
from . import WordSubstitutionUtils as wsu

def create_subtitles(subtitles, durations, language, width ):
    font_size=width/1080 * 160
    align = ('East') if (language.lower() in ['ur','urd','urdu']) else ('West')
    
    # ۱۲۳۴ highlighted wrong (numbers are finger-spelled)
    # use this --v 
    # 1234, 1234, 1234, 1234 (white   - bottom)
    # 1___, _2__, __3_, ___4 (magenta - middle)
    # 1___, 12__, 123_, 1234 (white   - top   )
    # ltr token in rtl sentence & vice virsa
    # keep token length full
    
    start_time = 0
    textclips = [ ]
    
    for (sentence,start_idx,end_idx), dur in zip(subtitles,durations):
        textclips.extend([
            mpy.TextClip(' '+sentence            , color = b'white'  , font='Jameel-Noori-Nastaleeq-Regular', fontsize=font_size, method='caption', align=align, size = (width, None) ).set_duration(dur).set_start(start_time),
            mpy.TextClip(' '+sentence[:end_idx  ], color = b'magenta', font='Jameel-Noori-Nastaleeq-Regular', fontsize=font_size, method='caption', align=align, size = (width, None) ).set_duration(dur).set_start(start_time),
            mpy.TextClip(' '+sentence[:start_idx], color = b'white'  , font='Jameel-Noori-Nastaleeq-Regular', fontsize=font_size, method='caption', align=align, size = (width, None) ).set_duration(dur).set_start(start_time)
        ])
        start_time += dur
    
    return mpy.CompositeVideoClip(textclips).margin( opacity=0).set_position(('center',0.618),relative=True)

#################################################################
#################################################################
  
def del_punctuation(word):
    return  word.replace('.','').replace(',','').replace('?','').replace('!','').replace('_','') \
                .replace('۔','').replace('،','').replace('؟','').replace('!','')
                
################################################################
#################################################################

def textToSign(sentence, language, video_width=144,
               person_no = 101, camera='front', 
               spell_mode='double', transition_frames=4, 
               trim_mode ='same-wrist-height', max_depth=0.466, max_depth_ratio=0.3, max_cut_size=25):
    
    word2file = wsu.ur_supportedWord2file if language.lower() in ['ur','urd','urdu'] else wsu.en_supportedWord2file
    
    clips     = []
    subtitles = []
    start_idx = 0
    
    sentence = ' '.join(re.split('\s{1,}',sentence))
    words = sentence.split(' ')
    
    for word in words:
        # if sign exists
        try:
            filename =         word2file[ del_punctuation(word.lower()) ] # throws key-error: sign doesnot exist
            clips    .append(  mpy.VideoFileClip(cu.file_info(filename,'video',person_no=person_no,camera=camera).path).resize(width=video_width))
            subtitles.append( [sentence, start_idx , start_idx+len(word)] )
            
        # else finger-spell
        except:
            clean_word  = del_punctuation(word)
            spelled_sentence = sentence[:start_idx]+  ' '.join(clean_word)  +sentence[start_idx+len(word):] # no plus1 in end index cuz we need the space ' ' character
            
            for i,letter in enumerate(clean_word):
            
                filename = word2file[letter]
                clips    .append(  mpy.VideoFileClip(cu.file_info(filename,'video',person_no=person_no,camera=camera).path).resize(width=video_width))
                subtitles.append( [spelled_sentence, start_idx +i*2 , start_idx +i*2+1] )
        
        start_idx += len(word)+1
        
    clips = cu.trim_clips(clips, mode=trim_mode, max_depth=max_depth, max_depth_ratio=max_depth_ratio, max_cut_size=max_cut_size)
    
    transition_time = transition_frames/clips[0].fps
    durations = [clips[0].duration]+[c.duration-transition_time for c in clips[1:]]
    
    subtitle_video = create_subtitles(subtitles,durations,language,video_width*0.9)
    video = cu.concatenate_video_clips(clips, transition_time)
      
    return mpy.CompositeVideoClip([video,subtitle_video])



#################################################################
#################################################################
