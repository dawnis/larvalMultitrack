"""http://tech.groups.yahoo.com/group/OpenCV/message/87984"""
import cv2.cv as cv
import cv2
import numpy as np
import Image

#cv2array and array2cv convert images from OpenCV <-> numpy arrays

def cv2array(im):
    depth2dtype = {
    cv.IPL_DEPTH_8U: 'uint8',
    cv.IPL_DEPTH_8S: 'int8',
    cv.IPL_DEPTH_16U: 'uint16',
    cv.IPL_DEPTH_16S: 'int16',
    cv.IPL_DEPTH_32S: 'int32',
    cv.IPL_DEPTH_32F: 'float32',
    cv.IPL_DEPTH_64F: 'float64',
    }

    arrdtype=im.depth
    a = np.fromstring(
    im.tostring(),
    dtype=depth2dtype[im.depth],
    count=im.width*im.height*im.nChannels)
    a.shape = (im.height,im.width,im.nChannels)
    return a

def array2cv(a):
    dtype2depth = {
    'uint8': cv.IPL_DEPTH_8U,
    'int8': cv.IPL_DEPTH_8S,
    'uint16': cv.IPL_DEPTH_16U,
    'int16': cv.IPL_DEPTH_16S,
    'int32': cv.IPL_DEPTH_32S,
    'float32': cv.IPL_DEPTH_32F,
    'float64': cv.IPL_DEPTH_64F,
    }
    try:
        nChannels = a.shape[2]
    except:
        nChannels = 1
        cv_im = cv.CreateImageHeader((a.shape[1],a.shape[0]),
        dtype2depth[str(a.dtype)],
        nChannels)
        cv.SetData(cv_im, a.tostring(),
        a.dtype.itemsize*nChannels*a.shape[1])
    return cv_im

if __name__ == '__main__':
    capture = cv.CaptureFromFile('lAcquisition002.avi')
    count=0
    history = 500
    nGauss = 6
    bgThresh = 0.6
    noise = 1
    bgs = cv2.BackgroundSubtractorMOG(history,nGauss,bgThresh,noise) #Background Subtractor MOG Construct

    image = cv.QueryFrame(capture)
    cv.ShowImage('lAcquisition002.avi',image)

    mat = cv2array(image) #Convert to Numpy Array Format
    foremat = bgs.apply(mat) #Call the Function
    foreground = array2cv(foremat); #Convert back to OpenCV format

    cv.ShowImage('Foreground',foreground)
    cv.WaitKey(15)

    while (count < 1000):
        image = cv.QueryFrame(capture)
        cv.ShowImage('lAcquisition002.avi',image)

        mat = cv2array(image) #Convert to Numpy Array Format
        bgs.apply(mat,foremat,-1) #Call the Function
        foreground = array2cv(foremat); #Convert back to OpenCV format

        cv.ShowImage('Foreground',foreground)
        cv.WaitKey(15)
        count = count + 1
