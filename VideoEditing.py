import os
import moviepy.editor as mpy
import http.client as httplib
import httplib2
import os
import random
import sys
import time
from apiclient.discovery import build
from apiclient.errors import HttpError
from apiclient.http import MediaFileUpload
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import argparser, run_flow

Videos = []
Track = []
vcodec = "libx264"
videoquality = "24"
# compression type
compression = "fast"

# Explicitly tell the underlying HTTP transport library not to retry, since we are handling retry logic ourselves.
httplib2.RETRIES = 1
# Maximum number of times to retry before giving up.
MAX_RETRIES = 10
# Always retry when these exceptions are raised.
RETRIABLE_EXCEPTIONS = (httplib2.HttpLib2Error, IOError, httplib.NotConnected,
                        httplib.IncompleteRead, httplib.ImproperConnectionState,
                        httplib.CannotSendRequest, httplib.CannotSendHeader,
                        httplib.ResponseNotReady, httplib.BadStatusLine)
# Always retry when an apiclient.errors.HttpError with one of these status codes is raised.
RETRIABLE_STATUS_CODES = [500, 502, 503, 504]

CLIENT_SECRETS_FILE = "client_secrets.json"

YOUTUBE_UPLOAD_SCOPE = "https://www.googleapis.com/auth/youtube.upload"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

# This variable defines a message to display if the CLIENT_SECRETS_FILE is missing.
MISSING_CLIENT_SECRETS_MESSAGE = """
WARNING: Please configure OAuth 2.0

To make this sample run you will need to populate the client_secrets.json file
found at:

   %s

with information from the API Console
https://console.developers.google.com/

For more information about the client_secrets.json file format, please visit:
https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
""" % os.path.abspath(os.path.join(os.path.dirname(__file__),
                                   CLIENT_SECRETS_FILE))

VALID_PRIVACY_STATUSES = ("public", "private", "unlisted")


class Clips():
    def __init__(self, origVideoClip, currentVideoClip):
        # initialising attributes of clip
        self.origVideoClip = origVideoClip
        self.videoClip = currentVideoClip

        # initially no media element is added to clip
        self.audioList = []
        self.textList = []
        self.imageList = []
        self.textEffectList = []
        self.imageEffectList = []

    def getDuration(self):
        return self.videoClip.duration

    def getSize(self):
        return self.videoClip.size
    
    def setTextList(self, textList):
        self.textList = textList.copy()

    def setAudioList(self, audioList):
        self.audioList = audioList.copy()

    def setImageList(self, imageList):
        self.imageList = imageList.copy()

    def setTextEffectList(self, textEffectList):
        self.textEffectList = textEffectList.copy()

    def setImageEffectList(self, imageEffectList):
        self.imageEffectList = imageEffectList.copy()

    def addText(self, textClip, content) -> bool:
        # combine text clip with video clip
        self.videoClip = mpy.CompositeVideoClip([self.videoClip, textClip])
        # add to text list
        self.textList.append((textClip, content))
        return True

    def addImage(self, imageClip, filePath) -> bool:
        # combine image clip with video clip
        self.videoClip = mpy.CompositeVideoClip([self.videoClip, imageClip])
        # add to image list
        self.imageList.append((imageClip, filePath))
        return True

    def addAudio(self, audioClip,filePath, startPosition=None, endPosition=None) -> bool:
        clipLength = self.videoClip.duration
        if startPosition == None:
            # if start is not specified, take it as start of clip
            startPosition = 0
        if endPosition == None:
            # if end is not specified, take it as end of the clip
            endPosition = clipLength

        # set attributes of audio clip
        audioClip = audioClip.set_start(startPosition)
        audioClip = audioClip.set_duration(endPosition - startPosition)

        # set audio
        self.videoClip = self.videoClip.set_audio(audioClip)
        # add audio clip along with its start and end to audio list
        self.audioList.append((audioClip, startPosition, endPosition,filePath))
        return True

    def addEffectOnText(self, textListIndex, effectName, effectDuration) -> bool:
        if textListIndex > len(self.textList) or textListIndex < 0:
            print("Error: specified text index out of range")
            return False
        if effectName != "crossfadein" and effectName != "crossfadeout":
            print("Error: specified effect does not exist")
            return False
        if effectDuration > self.textList[textListIndex][0].duration:
            print("Error: specified time stamps not in clip range")
            return False

        # retrieve the currentTextClip and remove it from the video
        currentTextClip = self.textList[textListIndex][0] 
        currentTextName = self.textList[textListIndex][1]
        self.removeText(textListIndex)

        # modify the current text clip by adding the required effect to the text clip
        if effectName == "crossfadein":
            currentTextClip = currentTextClip.crossfadein(effectDuration)
        if effectName == "crossfadeout":
            currentTextClip = currentTextClip.crossfadeout(effectDuration)
        
        # add the modified textclip to the video
        final_clip = mpy.CompositeVideoClip([self.videoClip, currentTextClip])
        self.videoClip = final_clip
        # add the modified textclip to the list of textclips and add the effect to the list of applied effects
        self.textList.append((currentTextClip,currentTextName))
        currentIndex = len(self.textList)
        self.textEffectList.append((currentIndex-1, effectName, effectDuration))
        return True

    def addEffectOnImage(self, imageListIndex, effectName, effectDuration) -> bool:
        if imageListIndex > len(self.textList) or imageListIndex < 0:
            print("Error: specified image index out of range")
            return False
        if effectName != "crossfadein" and effectName != "crossfadeout":
            print("Error: specified effect does not exist")
            return False
        if effectDuration > self.textList[imageListIndex][0].duration:
            print("Error: specified time stamps not in clip range")
            return False
            
        # retrieve the current image clip and remove it from the video
        currentImageClip = self.imageList[imageListIndex][0] 
        currentImageName = self.imageList[imageListIndex][1]
        self.removeImage(imageListIndex)

        # modify the current image clip by adding the required effect to the image clip
        if effectName == "crossfadein":
            currentImageClip = currentImageClip.crossfadein(effectDuration)
        if effectName == "crossfadeout":
            currentImageClip = currentImageClip.crossfadeout(effectDuration)
        
        # add the modified image clip to the video
        final_clip = mpy.CompositeVideoClip([self.videoClip, currentImageClip])
        self.videoClip = final_clip
        # add the modified imageclip to the list of imageclips and add the effect to the list of applied effects.
        self.imageList.append((currentImageClip,currentImageName))
        currentIndex = len(self.imageList)
        self.imageEffectList.append((currentIndex-1, effectName, effectDuration))

    def removeText(self, index):
        # delete text from text list
        del self.textList[index]
        effectIndex = -1
        # retrieve the starting video clip with no media elements and effects added, create a temporary clip object using this video clip
        temporaryClip = Clips(self.origVideoClip, self.origVideoClip)
        # add back media elements to original video clip
        for audios in self.audioList:
            temporaryClip.addAudio(audios[0],audios[3], startPosition=audios[1], endPosition=audios[2])
        for imageClip in self.imageList:
            temporaryClip.addImage(imageClip[0],imageClip[1])
        for textClip in self.textList:
            temporaryClip.addText(textClip[0],textClip[1])
        # if there exists an effect associated with the text clip, do not apply this effect, instead store its index and remove it from the list of text effects
        for effects in self.textEffectList:
            if effects[0] != index:
                temporaryClip.addEffectOnText(effects[0], effects[1], effects[2])
            else:
                effectIndex = index
        for effects in self.imageEffectList:
            temporaryClip.addEffectOnImage(effects[0], effects[1], effects[2])

        if effectIndex != -1:
            del self.textEffectList[effectIndex]

        self.videoClip = temporaryClip.output().copy()

    def removeImage(self, index):
        # delete image from image list
        del self.imageList[index]
        effectIndex = -1
        # retrieve the starting video clip with no media elements and effects added, create a temporary clip object using this video clip
        temporaryClip = Clips(self.origVideoClip, self.origVideoClip)
        # add back media elements to original video clip
        for audios in self.audioList:
            temporaryClip.addAudio(audios[0],audios[3], startPosition=audios[1], endPosition=audios[2])
        for imageClip in self.imageList:
            temporaryClip.addImage(imageClip[0],imageClip[1])
        for textClip in self.textList:
            temporaryClip.addText(textClip[0],textClip[1])
        for effects in self.textEffectList:
            temporaryClip.addEffectOnText(effects[0], effects[1], effects[2])
        # if there exists an effect associated with the image clip, do not apply this effect, instead store its index and remove it from the list of image effects
        for effects in self.imageEffectList:
            if effects[0] != index:
                temporaryClip.addEffectOnImage(effects[0], effects[1], effects[2])
            else:
                effectIndex = index

        if effectIndex != -1:
            del self.imageEffectList[effectIndex]

        self.videoClip = temporaryClip.output().copy()

    def removeAudio(self, index):
        # delete audio from audio list
        del self.audioList[index]
        # retrieve the starting video clip with no media elements and effects added, create a temporary clip object using this video clip
        temporaryClip = Clips(self.origVideoClip, self.origVideoClip)
        # add back media elements to original video clip
        for audios in self.audioList:
            temporaryClip.addAudio(audios[0],audios[3], startPosition=audios[1], endPosition=audios[2])
        for imageClip in self.imageList:
            temporaryClip.addImage(imageClip[0],imageClip[1])
        for textClip in self.textList:
            temporaryClip.addText(textClip[0],textClip[1])
        for effects in self.textEffectList:
            temporaryClip.addEffectOnText(effects[0], effects[1], effects[2])
        for effects in self.imageEffectList:
            temporaryClip.addEffectOnImage(effects[0], effects[1], effects[2])

        self.videoClip = temporaryClip.output().copy()

    def removeTextEffect(self, index):
        # delete the textEffect from the list of applied text effects
        del self.textEffectList[index]
        # retrieve the starting video clip with no media elements and effects added, create a temporary clip object using this video clip
        temporaryClip = Clips(self.origVideoClip, self.origVideoClip)
        # add all the media elements and apply the effects to this temporary clip
        for audios in self.audioList:
            temporaryClip.addAudio(audios[0],audios[3], startPosition=audios[1], endPosition=audios[2])
        for imageClip in self.imageList:
            temporaryClip.addImage(imageClip[0],imageClip[1])
        for textClip in self.textList:
            temporaryClip.addText(textClip[0],textClip[1])
        for effects in self.textEffectList:
            temporaryClip.addEffectOnText(effects[0], effects[1], effects[2])
        for effects in self.imageEffectList:
            temporaryClip.addEffectOnImage(effects[0], effects[1], effects[2])
        self.videoClip = temporaryClip.output().copy()

    def removeImageEffect(self, index):
        # delete the imageEffect from the list of applied image effects
        del self.imageEffectList[index]
        # retrieve the starting video clip with no media elements and effects added, create a temporary clip object using this video clip
        temporaryClip = Clips(self.origVideoClip, self.origVideoClip)
        # add all the media elements and apply the effects to this temporary clip
        for audios in self.audioList:
            temporaryClip.addAudio(audios[0],audios[3], startPosition=audios[1], endPosition=audios[2])
        for imageClip in self.imageList:
            temporaryClip.addImage(imageClip[0],imageClip[1])
        for textClip in self.textList:
            temporaryClip.addText(textClip[0],textClip[1])
        for effects in self.textEffectList:
            temporaryClip.addEffectOnText(effects[0], effects[1], effects[2])
        for effects in self.imageEffectList:
            temporaryClip.addEffectOnImage(effects[0], effects[1], effects[2])
        self.videoClip = temporaryClip.output().copy()

    def constructVideoClip(self):
        # construct video clip by adding all media elements and effects
        # retrieve the starting video clip with no media elements and effects added, create a temporary clip object using this video clip
        temporaryClip = Clips(self.origVideoClip, self.origVideoClip)
        # add all the media elements and apply the effects to this temporary clip
        for audios in self.audioList:
            temporaryClip.addAudio(audios[0],audios[3], startPosition=audios[1], endPosition=audios[2])
        for imageClip in self.imageList:
            temporaryClip.addImage(imageClip[0],imageClip[1])
        for textClip in self.textList:
            temporaryClip.addText(textClip[0],textClip[1])
        for effects in self.textEffectList:
            temporaryClip.addEffectOnText(effects[0], effects[1], effects[2])
        for effects in self.imageEffectList:
            temporaryClip.addEffectOnImage(effects[0], effects[1], effects[2])
        self.videoClip = temporaryClip.output().copy()

    
    def addSubtitles(self, subtitlesFile) -> bool:
        generator = lambda txt: mpy.TextClip(txt, font='Georgia-Regular', fontsize=24, color='white')
        sub = mpy.SubtitlesClip(subtitlesFile, generator)
        myvideo = mpy.VideoFileClip("myvideo.avi")
        self.videoClip = mpy.CompositeVideoClip([self.videoClip, sub])
        return True
    
    def output(self):
        # returns the edited video clip
        return self.videoClip


def checkFileExists(filename) -> bool:
    # check whether the file exists with the given filename
    return os.path.exists(filename)


def uploadVideo(inputVideos) -> bool:
    if len(inputVideos) == 0:
        # if no input video is selected
        print("Error: no input video is chosen")
        return False
    # add video as clip to Videos data store
    errorFlag = True
    for video in inputVideos:
        if checkFileExists(video) == False:
            # if file doesn't exist, show error
            print("Error: video file " + video + " doesn't exist")
            errorFlag = False
        else:
            Videos.append(mpy.VideoFileClip(video))
    return errorFlag


def addVideo(videoIndex, position) -> bool:
    if position > len(Track) or position < 0:
        # if position to insert is not valid
        print("Error: invalid position to insert into")
        return False
    if videoIndex >= len(Videos) or videoIndex < 0:
        # if video with given index is not present
        print("Error: invalid index of video")
        return False

    # create a clip of the video to add to track
    clip = Clips(Videos[videoIndex], Videos[videoIndex])
    Track.insert(position, clip)
    return True


def removeVideo(videoIndex) -> bool:
    del Videos[videoIndex]
    return True


def checkTrackIndex(trackIndex):
    # Check if the given track index exists in track
    if trackIndex >= len(Track) or trackIndex < 0:
        print("Error: no clip with such an index")
        return False
    return True

# Add sound to specified clip
def addSound(audioFilePath, trackIndex, startPosition=None, endPosition=None) -> bool:
    if checkFileExists(audioFilePath) == False:
        print("Error: audio file doesn't exist")
        return False
    if checkTrackIndex(trackIndex) == False:
        return False

    # create audio clip from sound file
    audioClip = mpy.AudioFileClip(audioFilePath)
    # call add audio method for the clip
    Track[trackIndex].addAudio(audioClip,audioFilePath, startPosition, endPosition)
    return True

# Add textual content to specified clip
def addTextualContent(content, startTime, displayDuration, posX, posY, trackIndex) -> bool:
    # Check if specified clip exists
    if checkTrackIndex(trackIndex) == False:
        return False  
    # Check if specified time stamps are within clip length
    if startTime + displayDuration > Track[trackIndex].getDuration() or startTime < 0 or displayDuration < 0:
        print("Error: Specified time stamps are not in range of clip")
        return False
    # Check if text position falls within video size
    if posX > Track[trackIndex].getSize()[0] or posY > Track[trackIndex].getSize()[1]:
        print("Error: Specified text coordinates not in range")
        return False
    
    # create auto generated text clip
    textClip = mpy.TextClip(content)
    # set attributes for the text clip
    textClip = textClip.set_start(startTime)
    textClip = textClip.set_duration(displayDuration)
    textClip = textClip.set_position((posX, posY))
    # call add text method for the clip
    return Track[trackIndex].addText(textClip, content)


def addImage(image, startTime, displayDuration, posX, posY, trackIndex) -> bool:
    # Check if file exists at specified path
    if checkFileExists(image) == False:
        print("Error: image file doesn't exist")
        return False
    # Check if specified clip exists
    if checkTrackIndex(trackIndex) == False:
        return False  
    # Check if specified time stamps are within clip length
    if startTime + displayDuration > Track[trackIndex].getDuration() or startTime < 0 or displayDuration < 0:
        print("Error: Specified time stamps are not in range of clip")
        return False
    # Check if image position falls within video size
    if posX > Track[trackIndex].getSize()[0] or posY > Track[trackIndex].getSize()[1]:
        print("Error: Specified image coordinates not in range")
        return False

    # create non moving video clip
    imageClip = mpy.ImageClip(image)
    # set attributes for image clip
    imageClip = imageClip.set_start(startTime)
    imageClip = imageClip.set_duration(displayDuration)
    imageClip = imageClip.set_position((posX, posY))
    # call add image method for the clip
    return Track[trackIndex].addImage(imageClip,image)


def addMediaElements(mediaType, *args) -> bool:
    # passing a variable list of arguments depending on the type of element
    # If sound has to be added
    if mediaType == 1:
        return addSound(args[0], args[1], args[2], args[3])
    # If text has to be added
    elif mediaType == 2:
        return addTextualContent(args[0], args[1], args[2], args[3], args[4], args[5])
    # If image has to be added
    elif mediaType == 3:
        return addImage(args[0], args[1], args[2], args[3], args[4], args[5])
    # Report error if invalid type of media element
    else:
        print("Error: not a valid type of media element")
        return False


def addTextEffect(textListIndex, effectName, effectDuration, trackIndex) -> bool:
    if checkTrackIndex(trackIndex) == False:
        return False
    # add effect on text media element
    return Track[trackIndex].addEffectOnText(textListIndex, effectName, effectDuration)


def addImageEffect(imageListIndex, effectName, effectDuration, trackIndex) -> bool:
    if checkTrackIndex(trackIndex) == False:
        return False
    # add effect on image media element
    return Track[trackIndex].addEffectOnImage(imageListIndex, effectName, effectDuration)


def addEffect(effectType, *args) -> bool:
    # passing a variable list of arguments depending on the type of element to add effect to
    # To add effect to text
    if effectType == 1:
        return addTextEffect(args[0], args[1], args[2], args[3])
    # To add effect to image
    elif effectType == 2:
        return addImageEffect(args[0], args[1], args[2], args[3])
    # Invalid type of effect
    else:
        print("Error: not a valid type of effect")
        return False


def addSubtitles(subtitlesFile, trackIndex) -> bool:
    return Track[trackIndex].addSubtitles(subtitlesFile)


def removeSound(trackIndex, audioListIndex) -> bool:
    # Remove sound from specified track clip
    return Track[trackIndex].removeAudio(audioListIndex)


def removeTextualContent(trackIndex, textListIndex) -> bool:
    # Remove text from specified track clip
    return Track[trackIndex].removeText(textListIndex)


def removeImage(trackIndex, imageListIndex) -> bool:
    # Remove image from specified track clip
    return Track[trackIndex].removeImage(imageListIndex)


def removeMediaElements(mediaType, trackIndex, mediaListIndex) -> bool:
    # If sound has to be removed
    if mediaType == 1:
        return removeSound(trackIndex, mediaListIndex)
    # If text has to be removed
    elif mediaType == 2:
        return removeTextualContent(trackIndex, mediaListIndex)
    # If image has to be removed
    elif mediaType == 3:
        return removeImage(trackIndex, mediaListIndex)
    # Report error if invalid type of media element
    else:
        print("Error: not a valid type of media element")
        return False


def removeTextEffect(trackIndex, textListIndex) -> bool:
    return Track[trackIndex].removeTextEffect(textListIndex)


def removeImageEffect(trackIndex, imageListIndex) -> bool:
    return Track[trackIndex].removeImageEffect(imageListIndex)


def removeEffect(mediaType, trackIndex, mediaListIndex) -> bool:
    # If text effect has to be removed
    if mediaType == 1:
        return removeTextEffect(trackIndex, mediaListIndex)
    # If image effect has to be removed
    elif mediaType == 2:
        return removeImageEffect(trackIndex, mediaListIndex)
    # Report error if invalid type of media element
    else:
        print("Error: not a valid type of media element")
        return False


def modifyAudioClip(origAudio, startTime, duration):
    # create a new audio clip and set its attributes appropriately
    modifiedAudio = origAudio.copy()
    modifiedAudio = modifiedAudio.set_start(startTime)
    modifiedAudio = modifiedAudio.set_duration(duration)
    return modifiedAudio


def handleAudio(clip, subClip1, subClip2, splitTime):
    # retrieve the current audio list and initialize the audioLists of the subclips
    currentAudioList = clip.audioList
    subClip1AudioList = []
    subClip2AudioList = []
    # initialize two temporary clips which will be used later
    audioClip1 = None
    audioClip2 = None
    for audio in currentAudioList:
        # retrieve start and end time of current audio clip
        startTime = audio[1]
        endTime = audio[2]
        if(endTime <= splitTime):
            # Complete audio clip is inserted in subClip1's audio list
            subClip1AudioList.append(audio)
        elif(startTime >= splitTime):
            # startTime of audio clip is modified and then it is inserted in subClip2's audio list
            audioClip2 = modifyAudioClip(audio[0], startTime-splitTime, endTime-startTime)
            subClip2AudioList.append((audioClip2, startTime - splitTime, endTime - splitTime))
        else:
            # this is is the case where the current audioClip needs to be split
            # the startTime and duration of the two parts into which the audioClip is split is initialized and then the parts are added into the appropriate list.
            audioClip1 = modifyAudioClip(audio[0], startTime, splitTime-startTime)
            audioClip2 = modifyAudioClip(audio[0], 0, endTime-splitTime)
            subClip1AudioList.append((audioClip1, startTime, splitTime))
            subClip2AudioList.append((audioClip2, splitTime, endTime))

    # the audioLists of both the subClips are set appropriately
    subClip1.setAudioList(subClip1AudioList)
    subClip2.setAudioList(subClip2AudioList)


def modifyTextClip(origTextClip, startTime, duration):
    # create a new text clip and set it's attributes appropriately
    modifiedTextClip = origTextClip.copy()
    modifiedTextClip = modifiedTextClip.set_start(startTime)
    modifiedTextClip = modifiedTextClip.set_duration(duration)
    return modifiedTextClip


def handleTextClipSplit(startTime, endTime, effectListIndex, splitTime, index, currentTextClip, effectListToTextListMapping, currentTextEffectList, subClip1TextList, subClip2TextList, subClip1TextEffectList, subClip2TextEffectList):
    textClip1 = modifyTextClip(currentTextClip, startTime, splitTime-startTime)
    textClip2 = modifyTextClip(currentTextClip, 0, endTime-splitTime)
    subClip1TextList.append(textClip1)
    subClip2TextList.append(textClip2)

    # The text clip is set into two parts, these parts are added to the appropriate textList
    if(effectListIndex != -1):
        if(currentTextEffectList[effectListIndex] == "crossfadein"):
            subClip1TextEffectList.append(
                (len(subClip1TextList)-1, currentTextEffectList[effectListIndex][1], currentTextEffectList[effectListIndex][2]))
        else:
            subClip2TextEffectList.append(
                (len(subClip2TextList)-1, currentTextEffectList[effectListIndex][1], currentTextEffectList[effectListIndex][2]))


def modifySubClipTextList(splitTime, index, currentTextClip, effectListToTextListMapping, currentTextEffectList, subClip1TextList, subClip2TextList, subClip1TextEffectList, subClip2TextEffectList):
    # temporary textCips that will be used later.
    textClip1 = None
    textClip2 = None
    # find the startTime, endTime and corresponding effectListIndex
    startTime = currentTextClip.start
    endTime = currentTextClip.start + currentTextClip.duration
    if(index in effectListToTextListMapping):
        effectListIndex = effectListToTextListMapping[index]
    else:
        effectListIndex = -1
    if endTime <= splitTime:
        subClip1TextList.append(currentTextClip)
        if(effectListIndex != -1):
            subClip1TextEffectList.append(
                (len(subClip1TextList)-1, currentTextEffectList[effectListIndex][1], currentTextEffectList[effectListIndex][2]))
        # Complete text clip is inserted in subClip1's text list
    elif startTime >= splitTime:

        textClip2 = modifyTextClip(
            currentTextClip, startTime-splitTime, endTime-startTime)

        subClip2TextList.append(textClip2)
        if effectListIndex != -1:
            subClip2TextEffectList.append(
                (len(subClip2TextList)-1, currentTextEffectList[effectListIndex][1], currentTextEffectList[effectListIndex][2]))
        # Complete text clip is inserted in subClip2's text list
    else:
        handleTextClipSplit(startTime, endTime, effectListIndex, splitTime, index, currentTextClip, effectListToTextListMapping,
                            currentTextEffectList, subClip1TextList, subClip2TextList, subClip1TextEffectList, subClip2TextEffectList)


def handleText(clip, subClip1, subClip2, splitTime):
    #print("handling text")
    currentTextList = clip.textList
    currentTextEffectList = clip.textEffectList
    subClip1TextList = []
    subClip2TextList = []
    # retrieve the currentTextList and currentTextEffectList and initialize subClip1's and subClip2's textList appropriately
    subClip1TextEffectList = []
    subClip2TextEffectList = []
    effectListToTextListMapping = dict()
    for index, effects in enumerate(currentTextEffectList):
        effectListToTextListMapping[effects[0]] = index
    # store the index of the effect that corresponds to a particular textClip

    for index, currentTextClip in enumerate(currentTextList):
        modifySubClipTextList(splitTime, index, currentTextClip, effectListToTextListMapping, currentTextEffectList,
                              subClip1TextList, subClip2TextList, subClip1TextEffectList, subClip2TextEffectList)

    subClip1.setTextList(subClip1TextList)
    subClip2.setTextList(subClip2TextList)
    subClip1.setTextEffectList(subClip1TextEffectList)
    subClip2.setTextEffectList(subClip2TextEffectList)
    # The text list and text effect lists of subClip1 and subClip2 are initialized appropriately.


def modifyImageClip(origImageClip, startTime, duration):
    # create a new image clip and set it's attributes appropriately
    modifiedImageClip = origImageClip.copy()
    modifiedImageClip = modifiedImageClip.set_start(startTime)
    modifiedImageClip = modifiedImageClip.set_duration(duration)
    return modifiedImageClip


def handleImageClipSplit(startTime, endTime, effectListIndex, splitTime, index, currentImageClip, effectListToImageListMapping, currentImageEffectList, subClip1ImageList, subClip2ImageList, subClip1ImageEffectList, subClip2ImageEffectList):
    # temporary imageCips that will be used later.
    imageClip1 = None
    imageClip2 = None
    # The image clip is set into two parts, these parts are added to the appropriate imageList
    imageClip1 = modifyImageClip(currentImageClip, startTime, splitTime-startTime)
    imageClip2 = modifyImageClip(currentImageClip, 0, endTime-splitTime)
    subClip1ImageList.append(imageClip1)
    subClip2ImageList.append(imageClip2)
    if(effectListIndex != -1):
        if(currentImageEffectList[effectListIndex] == "crossfadein"):
            subClip1ImageEffectList.append((len(subClip1ImageList)-1, currentImageEffectList[effectListIndex][1], currentImageEffectList[effectListIndex][2]))
        else:
            subClip2ImageEffectList.append((len(subClip2ImageList)-1, currentImageEffectList[effectListIndex][1], currentImageEffectList[effectListIndex][2]))


def modifySubClipImageList(splitTime, index, currentImageClip, effectListToImageListMapping, currentImageEffectList, subClip1ImageList, subClip2ImageList, subClip1ImageEffectList, subClip2ImageEffectList):
    imageClip1 = None
    imageClip2 = None
    # temporary imageCips that will be used later.
    startTime = currentImageClip.start
    endTime = currentImageClip.start + currentImageClip.duration
    if(index in effectListToImageListMapping):
        effectListIndex = effectListToImageListMapping[index]
    else:
        effectListIndex = -1
    # find the startTime, endTime and corresponding effectListIndex,
    if(endTime <= splitTime):
        subClip1ImageList.append(currentImageClip)
        if(effectListIndex != -1):
            subClip1ImageEffectList.append(
                (len(subClip1ImageList)-1, currentImageEffectList[effectListIndex][1], currentImageEffectList[effectListIndex][2]))
        # Complete image clip is inserted in subClip1's image list
    elif(startTime >= splitTime):
        imageClip2 = modifyImageClip(
            currentImageClip, startTime-splitTime, endTime-startTime)
        subClip2ImageList.append(imageClip2)
        if(effectListIndex != -1):
            subClip2ImageEffectList.append(
                (len(subClip2ImageList)-1, currentImageEffectList[effectListIndex][1], currentImageEffectList[effectListIndex][2]))
        # Complete image clip is inserted in subClip2's image list
    else:
        handleImageClipSplit(startTime, endTime, effectListIndex, splitTime, index, currentImageClip, effectListToImageListMapping,
                             currentImageEffectList, subClip1ImageList, subClip2ImageList, subClip1ImageEffectList, subClip2ImageEffectList)


def handleImage(clip, subClip1, subClip2, splitTime):
    # retrieve the currentImageList and currentImageEffectList and initialize subClip1's and subClip2's imageList appropriately
    currentImageList = clip.imageList
    currentImageEffectList = clip.imageEffectList
    # initialize two temporary imageClip objects which will be used later.
    subClip1ImageList = []
    subClip2ImageList = []
    subClip1ImageEffectList = []
    subClip2ImageEffectList = []
    effectListToImageListMapping = dict()
    # store the index of the effect that corresponds to a particular imageClip
    for index, effects in enumerate(currentImageEffectList):
        effectListToImageListMapping[effects[0]] = index
    for index, currentImageClip in enumerate(currentImageList):
        modifySubClipImageList(splitTime, index, currentImageClip, effectListToImageListMapping, currentImageEffectList,
                               subClip1ImageList, subClip2ImageList, subClip1ImageEffectList, subClip2ImageEffectList)
    # The image list and image effect lists of subClip1 and subClip2 are initialized appropriately.
    subClip1.setImageList(subClip1ImageList)
    subClip2.setImageList(subClip2ImageList)
    subClip1.setImageEffectList(subClip1ImageEffectList)
    subClip2.setImageEffectList(subClip2ImageEffectList)


def sliceClip(trackIndex, splitTime) -> bool:
    # retrieve original Clip and store the length of the original video clip
    clip = Track[trackIndex]
    origVideoClip = clip.output()
    umVideoClip = clip.origVideoClip
    startTime = origVideoClip.start
    duration = origVideoClip.duration

    # delete original clip and create the necessary subclips
    del Track[trackIndex]
    subClip1 = Clips(umVideoClip.subclip(startTime, splitTime),origVideoClip.subclip(startTime, splitTime))
    subClip2 = Clips(umVideoClip.subclip(splitTime, duration),origVideoClip.subclip(splitTime, duration))
    # Splitting audio Clips
    handleAudio(clip, subClip1, subClip2, splitTime)
    # Splitting textClips and textEffects
    handleText(clip, subClip1, subClip2, splitTime)
    # Splitting imageClips and imageEffects
    handleImage(clip, subClip1, subClip2, splitTime)
    subClip1.constructVideoClip()
    subClip2.constructVideoClip()
    # place the subclips at the appropriate position in the Track.
    Track.insert(trackIndex, subClip1)
    Track.insert(trackIndex+1, subClip2)
    return True


def reorderClips(positions) -> bool:
    if len(positions) != len(Track):
        # length of positions given is not equal to number of clips
        print("Error: length of positions given is not equal to number of clips")
        return False
    changedTrack = Track.copy()
    # move clip at mentioned position 
    for i in range(positions):
        changedTrack[positions[i]] = Track[i]
    Track = changedTrack.copy()
    return True


def removeClip(trackIndex) -> bool:
    # delete the clip located at the mentioned index 
    del Track[trackIndex]
    return True


def download(outputFileName) -> bool:
    clips = []
    for clip in Track:
        # add modified clip output in list 
        clips.append(clip.output())
    if len(clips) == 0:
        # if Track is empty
        print("Error: no clip on track")
        return False
    # combine all clips into a single video clip
    finalClip = mpy.concatenate_videoclips(clips)
    # write clip to a video file
    finalClip.write_videofile(outputFileName, threads=4, fps=24, codec=vcodec, preset=compression, ffmpeg_params=["-crf", videoquality])
    return True


def get_authenticated_service(args):
    flow = flow_from_clientsecrets(CLIENT_SECRETS_FILE,
                                   scope=YOUTUBE_UPLOAD_SCOPE,
                                   message=MISSING_CLIENT_SECRETS_MESSAGE)

    storage = Storage("%s-oauth2.json" % sys.argv[0])
    credentials = storage.get()

    if credentials is None or credentials.invalid:
        credentials = run_flow(flow, storage, args)

    return build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
                 http=credentials.authorize(httplib2.Http()))


def initialize_upload(youtube, options):
    tags = None
    if options.keywords:
        tags = options.keywords.split(",")

    body = dict(
        snippet=dict(
            title=options.title,
            description=options.description,
            tags=tags,
            categoryId=options.category
        ),
        status=dict(
            privacyStatus=options.privacyStatus
        )
    )

    # Call the API's videos.insert method to create and upload the video.
    insert_request = youtube.videos().insert(
        part=",".join(body.keys()),
        body=body,
        # The chunksize parameter specifies the size of each chunk of data, in bytes
        media_body=MediaFileUpload(options.file, chunksize=-1, resumable=True)
    )

    resumable_upload(insert_request)


def resumable_upload(insert_request):
    response = None
    error = None
    retry = 0
    while response is None:
        try:
            print("Uploading file...")
            status, response = insert_request.next_chunk()
            if response is not None:
                if 'id' in response:
                    print("Video id '%s' was successfully uploaded." %
                          response['id'])
                else:
                    exit("The upload failed with an unexpected response: %s" % response)
        except HttpError as e:
            if e.resp.status in RETRIABLE_STATUS_CODES:
                error = "A retriable HTTP error %d occurred:\n%s" % (e.resp.status,
                                                                     e.content)
            else:
                raise
        except RETRIABLE_EXCEPTIONS as e:
            error = "A retriable error occurred: %s" % e

        if error is not None:
            print(error)
            retry += 1
            if retry > MAX_RETRIES:
                exit("No longer attempting to retry.")

            max_sleep = 2 ** retry
            sleep_seconds = random.random() * max_sleep
            print("Sleeping %f seconds and then retrying..." % sleep_seconds)
            time.sleep(sleep_seconds)


def exportToYouTube(outputFileName) -> bool:
    # first download the file locally
    download(outputFileName)
    # if file is not downloaded
    if not os.path.exists(outputFileName):
        print("Error: output file not downloaded")
        return False

    # passing output file name to upload in file argument
    argparser.add_argument("--file", help="Video file to upload", default=outputFileName)
    # adding other parameters to arguments
    argparser.add_argument("--title", help="Video title", default="Test Title")
    argparser.add_argument("--description", help="Video description", default="Test Description")
    argparser.add_argument("--category", default="22", help="Numeric video category. " + "See https://developers.google.com/youtube/v3/docs/videoCategories/list")
    argparser.add_argument("--keywords", help="Video keywords, comma separated", default="")
    argparser.add_argument("--privacyStatus", choices=VALID_PRIVACY_STATUSES, default=VALID_PRIVACY_STATUSES[0], help="Video privacy status.")
    # parse the arguments
    args = argparser.parse_args()
    
    # get authenticated service of youtube
    youtube = get_authenticated_service(args)
    try:
        # insert video to youtube's video list
        initialize_upload(youtube, args)
    except HttpError as e:
        print("An HTTP error %d occurred:\n%s" % (e.resp.status, e.content))
    return True