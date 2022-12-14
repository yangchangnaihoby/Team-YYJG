# --------------------------------------------------
# program start

print('program execution succeeded')

# --------------------------------------------------
# module import

import pandas as pd
import numpy as np
import streamlit as st
import mediapipe as mp
import tensorflow as tf

import time
import cv2
from PIL import Image

import webbrowser
from sklearn.model_selection import train_test_split
from collections import deque

# --------------------------------------------------
# function settings

def cal_d(p, n) :
    d = (p[0] - n[0]) ** 2 + (p[1] - n[1]) ** 2
    return d ** (1 / 2) 

def cal_p(x, y) :
    return (x - y)

def get_score(data) :
    score = score_model.predict(data)[0][0]
    score = int(score * 10000)
    score = float(score) / 100
    return score

def get_angle(data) :
    p = angle_model.predict(data)[0][0]
    return (p - 90)

def cor_histogram(correl_imagelist) :
    hists = []
    co01 = []
    co09 = []
    
    for file in correl_imagelist :
        nowimg = file[0]
        hsv = cv2.cvtColor(nowimg, cv2.COLOR_BGR2HSV)
        hist = cv2.calcHist([hsv], [0, 1], None, [180, 256], [0, 180, 0, 256])
        cv2.normalize(hist, hist, 0, 1, cv2.NORM_MINMAX)
        hists.append(hist)

    if hists :
        query = hists[-1]
        methods = ['CORREL']
        compare_hists = []
        
        for i, histogram in enumerate(hists) :
            ret = cv2.compareHist(query, histogram, 0)
            
            if ret < 0.9 :
                co01.append(correl_imagelist[i])
            else:
                co09.append(correl_imagelist[i])

        co09 = sorted(co09, key = lambda x : x[1])

        while len(co09) > correl_save_number :
            del co09[0]

        correl_imagelist = co01 + co09
        correl_imagelist = sorted(correl_imagelist, key = lambda x : x[1])

        while len(correl_imagelist) > picture_save_number :
            del correl_imagelist[0]
            
    return correl_imagelist

# --------------------------------------------------
# model load

score_model = tf.keras.models.load_model('flp_score_predict001.h5')
angle_model = tf.keras.models.load_model('flp_horizon_correction003.h5')

# --------------------------------------------------
# title

# st.set_page_config(initial_sidebar_state = 'collapsed')

st.markdown('<h1 style = \'text-align : center;\'>???????????? ?????? \'?????????\' ?????????</h1>', unsafe_allow_html = True)
st.markdown('<h4 style = \'text-align : right\'>v0.0.2-alpha</h4>', unsafe_allow_html = True)

# --------------------------------------------------
# main page

def main_page() :
    
    print('main page on')

    st.text('\n')
    st.text('\n')

    st.markdown(
    '''
    ???????????? ????????? ?????? ????????? ????????? ?????? ????????? ???????????????????\n
    ?????? ??? ?????? ????????? ???????????? ???????????? ?????? ????????? ?????? ??? ???????????? ???????????? ???????????????????\n
    '''
    )

    st.text('\n')

    st.markdown(
    '''
    ????????? ??????, ????????? ???????????????????????????!\n
    ??? ???????????? ????????? ????????????????????? ???????????? ?????? ??? ?????? ???????????? ??????????????? ????????????\n
    ????????? ????????? ????????? ????????? ??? ????????? ????????? ???????????? ????????????,\n
    ?????? ??????????????? ?????? ?????? '?????????'????????? ???????????? ???????????? ?????????????????????.\n
    ????????? ?????? ????????? ????????? ????????? ????????? ???????????? ??????????????????!\n
    '''
    )

    st.text('\n')
    st.text('\n')

    st.text(
    '''
    ????????????????????? AI?????? 7??? (2022.04.25 ~ 2022.10.05)
    ??? ???????????? (?????????, ?????????, ?????????, ?????????, ?????????)
    '''
    )
    st.text(
    '''
    Project 001 ??? ????????? ????????? ?????? ?????????!
    - Project Manager : ?????????
    - Backend Developer : ?????????, ?????????
    - Frontend Developer : ?????????
    - Data Manager : ?????????, ?????????
    '''
    )
    st.text('Copyright 2022. Team YYJG. All rights reserved.')
    
    print('main page end')
    
# --------------------------------------------------
# page 1 webcam
    
def sub_page_1() :
    
    print('page 1 on')
    
    global correl_save_number, picture_save_number
    
    st.markdown('<h3 style = \'text-align : center;\'>?????? ??? ?????????</h3>', unsafe_allow_html = True)
    st.info('??? ???????????? ????????? ????????? ????????? ??????????????????.')
    
    mp_drawing = mp.solutions.drawing_utils
    mp_drawing_styles = mp.solutions.drawing_styles
    mp_holistic = mp.solutions.holistic
    count = 0
    BG_COLOR = (0, 0, 0)
    MASK_COLOR = (1, 1, 1)

    cap = cv2.VideoCapture(0)

    cap_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    cap_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap.get(cv2.CAP_PROP_FPS) * 0.8)

    print(cap_w, cap_h)

    cols_cam = st.columns(2)
    frame_window_ori = cols_cam[0].image([])
    frame_window = cols_cam[1].image([])
    st.text('Good Photos (?????? ??????????????? ?????? ??????????????? ?????? ????????? ????????? ???????????????.)')
    count_col = 0
    cols_photo = st.columns(4)
    
    prev_time = 0
    FPS = 10
    prescore = 0
    idx = 0
    datacompare = 0

    picture_save_number = 30
    correl_save_number = 5

    imagelist = []
    correl_imagelist = []

    with mp_holistic.Holistic(
        min_detection_confidence = 0.5,
        min_tracking_confidence = 0.5) as holistic :
        
        while cap.isOpened() :
            
            idx += 1
            success, image = cap.read()
            black_window = np.zeros([cap_h, cap_w, 3], np.uint8)
            
            if not success :
                print('Ignoring empty camera frame.')
                break

            image.flags.writeable = False
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            results = holistic.process(image)

            n=[]
            visibility =[]
            
            if results.pose_landmarks :
                for data_point in results.pose_landmarks.landmark :
                    n.append(data_point.x)
                    n.append(data_point.y)
                    n.append(data_point.z)
                    visibility.append(data_point.visibility)
            else :
                for _ in range(99) :
                    n.append(0)

            nowdata = [n]

            if datacompare == 0 :
                predata = [[0 for _ in range(99)]]

            datacompare += 1

            xyzd = 0
            
            for i in range(99) :
                xyzd += (nowdata[0][i]-predata[0][i]) ** 2

            lifescore = get_score(nowdata)
            lifeangle = get_angle(nowdata)

            allscore = lifescore
            predata = nowdata

            text1 = 'score : {}'.format(round(lifescore, 2))
            text2 = 'angle : {}'.format(round(lifeangle, 2))
            org1 = (30, 30)
            org2 = (30, 60)
            font=cv2.FONT_HERSHEY_SIMPLEX

            image.flags.writeable = True
            save_image = image.copy()

            mp_drawing.draw_landmarks(
                black_window,
                results.pose_landmarks,
                mp_holistic.POSE_CONNECTIONS,
                landmark_drawing_spec = mp_drawing_styles.get_default_pose_landmarks_style())
            
            image = cv2.flip(image, 1)
            black_window = cv2.flip(black_window, 1)
            
            cv2.putText(black_window, text1, org1, font, 1, (255, 0, 0) ,2)
            cv2.putText(black_window, text2, org2, font, 1, (255, 0, 0) ,2)
            
            frame_window_ori.image(image)
            frame_window.image(black_window)
            
            if abs(lifeangle) < 10 :
                if count_col == 4 :
                    count_col = 0
                    cols_photo = st.columns(4)
                correl_imagelist.append([save_image, allscore])
                cols_photo[count_col].image(save_image, width = 160)
                count_col += 1
                continue

            correl_imagelist = cor_histogram(correl_imagelist)
            prescore = lifescore

            if cv2.waitKey(10) & 0xFF == 27 :
                break
            
    cap.release()
    
    print('page 1 end')
    
# --------------------------------------------------
# page 2 video
    
def sub_page_2() :
    
    print('page 2 on')
    
    global correl_save_number, picture_save_number, correl_imagelist
    
    st.markdown('<h3 style = \'text-align : center;\'>?????? ?????? (mp4 ??????)</h3>', unsafe_allow_html = True)   
    
    mp_drawing = mp.solutions.drawing_utils
    mp_drawing_styles = mp.solutions.drawing_styles
    mp_holistic = mp.solutions.holistic
    count = 0
    BG_COLOR = (0, 0, 0)
    MASK_COLOR = (1, 1, 1)
    
    video_file = st.file_uploader('?????? ????????? ?????????????????????.', type=['mp4'])
    
    if video_file is not None :      
        
        vid = video_file.name
        
        with open(vid, mode = 'wb') as f :
            f.write(video_file.read())
            
        st.markdown(f'''
        ##### ?????? ?????? ???...
        - {vid}
        ''',
        unsafe_allow_html = True)
        
        st.info('?????? ????????? ???????????? ?????? ????????? ??????????????????.')

        vidcap = cv2.VideoCapture(vid)
        
        cap_w = int(vidcap.get(cv2.CAP_PROP_FRAME_WIDTH))
        cap_h = int(vidcap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(vidcap.get(cv2.CAP_PROP_FPS) * 0.8) 
        
        print(cap_w, cap_h)

        cols_cam = st.columns(2)
        frame_window_ori = cols_cam[0].image([])
        frame_window = cols_cam[1].image([])
#         st.text('Good Photos (?????? ??????????????? ?????? ???????????? ?????? ????????? ????????? ???????????????.)')
#         count_col = 0
#         cols_photo = st.columns(4)

        prev_time = 0
        FPS = 10
        prescore = 0
        idx = 0
        datacompare = 0

        picture_save_number = 30
        correl_save_number = 5

        imagelist = []
        correl_imagelist = []       

        with mp_holistic.Holistic(
            min_detection_confidence = 0.5,
            min_tracking_confidence = 0.5) as holistic :

            while vidcap.isOpened() :

                idx += 1
                success, image = vidcap.read()
                black_window = np.zeros([cap_h, cap_w, 3], np.uint8)

                if not success :
                    print('Ignoring empty camera frame.')
                    break

                image.flags.writeable = False
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                results = holistic.process(image)

                n=[]
                visibility =[]

                if results.pose_landmarks :
                    for data_point in results.pose_landmarks.landmark :
                        n.append(data_point.x)
                        n.append(data_point.y)
                        n.append(data_point.z)
                        visibility.append(data_point.visibility)
                else :
                    for _ in range(99) :
                        n.append(0)

                nowdata = [n]

                if datacompare == 0 :
                    predata = [[0 for _ in range(99)]]

                datacompare += 1

                xyzd = 0

                for i in range(99) :
                    xyzd += (nowdata[0][i]-predata[0][i]) ** 2

                lifescore = get_score(nowdata)
                lifeangle = get_angle(nowdata)

                allscore = lifescore
                predata = nowdata

                text1 = 'score : {}'.format(round(lifescore, 2))
                text2 = 'angle : {}'.format(round(lifeangle, 2))
                org1 = (30, 30)
                org2 = (30, 60)
                font=cv2.FONT_HERSHEY_SIMPLEX

                image.flags.writeable = True
                save_image = image.copy()

                mp_drawing.draw_landmarks(
                    black_window,
                    results.pose_landmarks,
                    mp_holistic.POSE_CONNECTIONS,
                    landmark_drawing_spec = mp_drawing_styles.get_default_pose_landmarks_style())

                cv2.putText(black_window, text1, org1, font, 1, (255, 0, 0) ,2)
                cv2.putText(black_window, text2, org2, font, 1, (255, 0, 0) ,2)

                frame_window_ori.image(image)
                frame_window.image(black_window)

                if (abs(lifeangle) < 10) and (xyzd < 0.002) :
#                     if count_col == 4 :
#                         count_col = 0
#                         cols_photo = st.columns(4)
                    correl_imagelist.append([save_image, allscore])
#                     cols_photo[count_col].image(save_image, width = 160)
#                     count_col += 1
#                     continue

                correl_imagelist = cor_histogram(correl_imagelist)
                prescore = lifescore

                if cv2.waitKey(10) & 0xFF == 27 :
                    break

        vidcap.release()
        
        st.text('Best Photos (?????? ??????????????? ?????? ??????????????? ?????? ??? ?????? 30?????? ????????? ??????????????????.)')
        count2 = 0
        count_col_2 = 0
        cols_photo_2 = st.columns(4)
        for bestpicture in correl_imagelist :
            if count_col_2 == 4 :
                count_col_2 = 0
                cols_photo_2 = st.columns(4)
            count2 += 1
            cols_photo_2[count_col_2].image(bestpicture[0], width = 160)
            bestpicture[0] = cv2.cvtColor(bestpicture[0], cv2.COLOR_BGR2RGB)
            cv2.imwrite('saved_image/best_image{:0>4}_s{}'.format(count2, int(bestpicture[1])) + '.png', bestpicture[0])
            count_col_2 += 1

    print('page 2 end')

# --------------------------------------------------
# page 3 image
    
def sub_page_3() :
    
    print('page 3 on')
    
    st.markdown('<h3 style = \'text-align : center;\'>?????? ?????? (jpg ??????)</h3>', unsafe_allow_html = True)
    st.subheader('Coming soon!')
    
    print('page 3 end')
    
# --------------------------------------------------
# main page select box

page_names_to_funcs = {
    'Default (??? ????????? ????????? ??? ?????? ???????????? ???????????????.)' : main_page,
    '?????? ??? ????????? - alpha test' : sub_page_1,
    '?????? ?????? (mp4 ??????) - alpha test' : sub_page_2,
    '?????? ?????? (jpg ??????) - coming soon!' : sub_page_3
}

selected_page = st.selectbox('????????? ?????? ????????? ??????????????????.', page_names_to_funcs.keys())
page_names_to_funcs[selected_page]()

# --------------------------------------------------
# program end

print('program execution complited')

# --------------------------------------------------