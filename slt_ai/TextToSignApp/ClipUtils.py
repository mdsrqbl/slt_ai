from asyncore import write
import os
import moviepy.editor as mpy

from scipy.signal import find_peaks
import numpy as np

from django.templatetags.static import static

class file_info:
    # def __init__(self,path):
        # worst language for OOP
        
        # use *args, **kwargs
    def __init__(self,word,filetype=None,person_no='101',camera='front'):
        if filetype is None:
            path = word
            self.filename = os.path.split(path)[-1]
            self.word   = self.filename.split('_')[ 0]
            self.format = self.filename.split('.')[-1]
            self.person = self.filename.split('_')[ 1]
            self.camera = self.filename.split('_')[ 2]
            self.subfolder  = os.path.split(os.path.split(path)[0])[-1]
            self.mainfolder = os.path.split( os.path.split(  os.path.split(path)[0]  )[ 0] )[-1]
            self.path   = path
        else:
            self.format = 'mp4' if filetype == 'video' else 'csv'
            self.filename = f'{word}_person{person_no}_{camera}_stabilized.{self.format}'
            self.word   = self.filename.split('_')[ 0]
            self.person = f'person{person_no}'
            self.camera = self.filename.split('_')[ 2]
            subfolderMap    = {'video':'Clips', 'landmarks':'Pose'}
            self.subfolder  = f'Person{person_no}_{subfolderMap[filetype]}_Stabilized'
            mainfolderMap   = {'video':'Clips', 'landmarks':'Landmarks'}
            self.mainfolder = f'PSL_{mainfolderMap[filetype]}'
            self.path   = os.path.abspath(os.path.join('.','static',self.mainfolder, self.subfolder, self.filename))
        
#################################################################
#################################################################

def concatenate_video_clips(clips, overlap):
    
    return mpy.concatenate(clips[:1]+[clip.crossfadein(overlap) for clip in clips[1:]],
                            padding=-overlap, method="compose")

#################################################################
#################################################################

def read_csv(path,num_landmarks=33,cols=2):
    return np.loadtxt(path,skiprows=1,delimiter=',').reshape((-1,num_landmarks,cols)) # -1 for numr of rows in csv_file or frames in video

#################################################################
#################################################################

def get_cut_points_of_all(landmarks_depths, mode='same-wrist-height', max_depth=0.466, max_depth_ratio=0.3, max_cut_size=25):
    """ the cut points are scaled to the duration of the clip by using the formula cut_frame_position/total_frames so 0 for cut at first frame & 1 for cut at last frame"""
    
    if mode=='same-wrist-height':
        def get_cut_points_of_1(l_depths,max_cut_size=max_cut_size):
            mask = l_depths<=max_depth # True when landmark is ABOVE the threshold
            return  [   min(max_cut_size, np.argmax(mask      )) / (l_depths.shape[0]-1),   # argmax returns the index of first True e.g  argmax([F,F,T,T,T,F]) = 2
                     1- min(max_cut_size, np.argmax(mask[::-1])) / (l_depths.shape[0]-1) ]  # [::-1] reverses the array so now argmax returns the index of the last True
        
        cuts =[get_cut_points_of_1(l_depths) for l_depths in landmarks_depths]
        cuts[ 0][ 0] = 0
        cuts[-1][-1] = 1
        
        return cuts

    elif mode=='smart':
        cuts = [[0,1] for l in landmarks_depths]

        for i in range(0,len(landmarks_depths)-1):
            curr_depths = landmarks_depths[i  ] # curr: current, idx: index/indices
            next_depths = landmarks_depths[i+1]
            
            peaks_idx         = find_peaks (-curr_depths, plateau_size=1)[0] # peak/plateau indicate that the elevated hand has been held to perform something
            mask              = curr_depths[ peaks_idx       ] < (np.max(curr_depths)-0.02) # the max_depth/lowest point is the resting position, 0.02 tolerance
            last_peak_idx     = peaks_idx  [-np.argmax(mask[::-1])-1]
            curr_cutoff_depth = curr_depths[ last_peak_idx   ] * (1-max_depth_ratio) + \
                                np.max     ( curr_depths     ) * (  max_depth_ratio) # go 30% lower than the last peek then cut
            
            peaks_idx         = find_peaks (-next_depths, plateau_size=1)[0]
            mask              = next_depths[ peaks_idx       ] < (np.max(next_depths)-0.02)
            first_peek_idx    = peaks_idx  [ np.argmax(mask) ]
            next_cutoff_depth = next_depths[ first_peek_idx  ] * (1-max_depth_ratio) + \
                                np.max     ( next_depths     ) * (  max_depth_ratio)
           
            final_cutoff_depth = max(curr_cutoff_depth,   # using MAX to keep the most part of the clip
                                     next_cutoff_depth,   
                                     curr_depths[-max_cut_size],
                                     next_depths[ max_cut_size]) 

            cuts[i  ][-1] = 1 - np.argmax(curr_depths[::-1]<=final_cutoff_depth)  / (curr_depths.shape[0]-1) # scale to the length of the clip: frame#/total_frames 
            cuts[i+1][ 0] =     np.argmax(next_depths      <=final_cutoff_depth)  / (curr_depths.shape[0]-1) # (len()-1 to get the max frame#)

        return cuts

    else:
        return [[0,1] for l in landmarks_depths] 

##########################################################################################################################
##########################################################################################################################

import pandas as pd

def trim_clips(clips, mode='same-wrist-height', max_depth=0.466, max_depth_ratio=0.3, max_cut_size=25):
    """
    Cut the begining and ending part of all clips in a list. 
    The start of first clip and the end of last clip is never cut.
    Arguments:
        clips     - A list of moviepy video clip objects
        mode      - Trimming mode. 
                        fixed = cut constant amount from both ends of all clips.
                        smart = find the frame where the hand is moving to/from the rest position at the fastest speed.
                        other = no trimming, just return a copy of original
        trim_secs - Video duration in seconds to be cut off from both ends (fixed mode only).
    Returns:
        A new list of trimmed video clips 
        such that the last frame of one clip is most similar to the first frame of the next clip.
    """
    
    if mode not in ['same-wrist-height', 'smart'] or len(clips)<=1:
        trimmed = clips.copy()
       
        
    words  = [file_info(clip.filename).word for clip in clips] #clip.filename --> path from which the video clip was loaded
    wrists = [(read_csv( file_info(w,'landmarks').path )[:,16,1] if w not in ['گناہ'] else read_csv(file_info(w,'landmarks').path)[:,15,1]) 
              #use y-coordinate of right_wrist for all words   except the ones that are purely left-handed   
              for w in words]
    cut_points = get_cut_points_of_all(wrists, mode=mode, max_depth=max_depth, max_depth_ratio=max_depth_ratio, max_cut_size=max_cut_size)
    
    trimmed = [clips[i].subclip(start*clips[i].duration, end*clips[i].duration) 
               for i, (start, end) in enumerate(cut_points)]

    return trimmed

##########################################################################################################################
##########################################################################################################################