# larvaMultitrack
![alt text](https://raw.githubusercontent.com/dawnis/larvalMultitrack/Screenshots/lmultitrack_scrrenshot.png.png)

# A video object tracker for monitoring the behavior of larval zebrafish
This object tracker utilizes a gradual background update algorithm to seperate moving entities (such as larval zebrafish swimming around in a dish) from the background and allows tracking of multiple animals at video rate. The GUI allows modification of parameters used by the algorithm such as the tracking radius for each detected object, the number of dilations and erosions, and the threshold difference from the background. It is possible to see what the background, thresholded images, and tracking are doing by clicking the appropriate checkmarks, which will open up windows with the video data. 

# Dependencies
OpenCv
Munkres
cPickle
wx
cProfile
numpy
scipi

# How to Run
run larvalMultitrack_main.py with Python2. A demonstration video is included under demo_data
