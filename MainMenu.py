import VideoEditing
def displayVideos():  
    print("\nVideos -")
    if(len(VideoEditing.Videos) == 0 ): 
        print("No video available") 
    else:
        for index,vids in enumerate(VideoEditing.Videos): 
            print(f"index:{index}  video:{vids.filename}")  

def displayTrack():  
    print("\nTrack")
    if(len(VideoEditing.Track) == 0): 
        print("No video on track") 
    for index,clip in enumerate(VideoEditing.Track): 
        print(f"Clip {index}")  
        if(len(clip.textList) == 0): 
            print("No text in textList")  
        else:
            for index,textClip in enumerate(clip.textList): 
               print(f"index:{index}  content:{textClip[1]}  startTime:{textClip[0].start}  endTime:{textClip[0].start+textClip[0].duration}")  
        if(len(clip.imageList) == 0): 
            print("No image in imageList") 
        else: 
            for index,imageClip in enumerate(clip.imageList): 
               print(f"index:{index}  filename:{imageClip[1]}  startTime:{imageClip[0].start}  endTime:{imageClip[0].start+imageClip[0].duration}")   
        if(len(clip.audioList) == 0): 
            print("No audio in audioList") 
        else: 
            for index,audios in enumerate(clip.audioList): 
               print(f"index:{index}  filename:{audios[3]}  startTime:{audios[1]}  endTime:{audios[2]}")         
        if(len(clip.textEffectList) ==0): 
            print("No text effects added") 
        else: 
            for index,textEffect in enumerate(clip.textEffectList): 
                print(f"index:{index}  effect name:{textEffect[1]}  for duration:{textEffect[2]}  applied to text clip at index:{textEffect[0]}") 
        if(len(clip.imageEffectList) ==0): 
            print("No image effects added") 
        else: 
            for index,imageEffect in enumerate(clip.imageEffectList): 
                print(f"index:{index}  effect name:{imageEffect[1]}  for duration:{imageEffect[2]}  applied to image clip at index:{imageEffect[0]}") 
        
        
        
while(True): 
    print("Enter Q to exit") 
    print("Enter U to upload videos") 
    print("Enter A to add a video to track") 
    print("Enter AE to add an element to a clip")  
    print("Enter RE to remove an element from a video") 
    print("Enter RV to remove a video")
    print("Enter AEF to add an effect to an element") 
    print("Enter REF to remove an effect from an element")  
    print("Enter S to slice a clip") 
    print("Enter RO to reorder clips") 
    print("Enter RC to remove a clip")
    print("Enter DL to download locally") 
    print("Enter EY to export video to youtube") 
    displayVideos() 
    displayTrack()
    
    inpString = input() 
    if(inpString == "Q"): 
        break
    elif(inpString == "U"): 
        print("\nEnter the path of video you want to add") 
        pathName = input() 
        VideoEditing.uploadVideo([pathName]) 
    elif(inpString == "A"):  
        print("\nEnter the index of video you want to add followed by the position in the track you want to insert the clip at")
        videoIndex,position = input().split()    
        VideoEditing.addVideo(int(videoIndex),int(position)) 

    elif(inpString == "AE"):  
        print("\nenter 3 to add an Image Clip") 
        print("enter 2 to add a Text Clip")  
        print("enter 1 to add a Audio Clip ")
        inputElem = input() 
        if(inputElem == "3"):
            print("enter image path, start time, duration, x co-ordinate, y co-ordinate, trackIndex") 
            image,startTime,duration,x,y,trackIndex = input().split()
            VideoEditing.addMediaElements(3,image,int(startTime),int(duration),int(x),int(y),int(trackIndex))
        elif(inputElem == "2"): 
            print("enter text content, start time, duration, x co-ordinate, y co-ordinate, trackIndex")  
            image,startTime,duration,x,y,trackIndex = input().split()
            VideoEditing.addMediaElements(2,image,int(startTime),int(duration),int(x),int(y),int(trackIndex)) 
        else: 
            print("enter audioFilePath, trackIndex, startPosition, endPosition") 
            audioFilePath,trackIndex, startPosition, endPosition = input().split() 
            VideoEditing.addMediaElements(1,audioFilePath,int(trackIndex),int(startPosition) , int(endPosition))
    
    elif(inpString == "RE"): 
        print("\nenter 3 to remove an Image Clip") 
        print("enter 2 to remove a text clip")  
        print("enter 1 to remove an audio clip") 

        inputElem = input()
        if(inputElem == "3"): 
            print("enter trackIndex, imageListIndex") 
            trackIndex,imageListIndex = input().split()
            VideoEditing.removeMediaElements(3,int(trackIndex),int(imageListIndex))
        elif(inputElem == "2"): 
            print("enter trackIndex, textListIndex") 
            trackIndex,textListIndex = input().split()
            VideoEditing.removeMediaElements(2,int(trackIndex),int(textListIndex)) 
        else: 
            print("enter trackIndex, audioListIndex") 
            trackIndex,audioListIndex = input().split()
            VideoEditing.removeMediaElements(1,int(trackIndex),int(textListIndex)) 
    elif(inpString == "RV"):  
        print("\nEnter a video index") 
        videoIndex = input()
        VideoEditing.removeVideo(int(videoIndex)) 
    elif(inpString == "RC"): 
        print("\nEnter a track index") 
        trackIndex = input() 
        VideoEditing.removeClip(int(trackIndex))
    elif(inpString == "AEF"): 
        print("\nenter 2 to add effect to a Image Clip") 
        print("enter 1 to add effect to a Text clip") 
        inputElem = input()
        if(inputElem == "2"): 
            print("enter imageListIndex, effectName, effectDuration, trackListIndex") 
            imageListIndex,effectName,effectDuration,trackListIndex = input().split()
            VideoEditing.addEffect(2,int(imageListIndex),effectName,int(effectDuration),int(trackListIndex))
        else: 
            print("enter textListIndex, effectName, effectDuration, trackListIndex") 
            textListIndex,effectName,effectDuration,trackListIndex = input().split()
            VideoEditing.addEffect(1,int(textListIndex),effectName,int(effectDuration),int(trackListIndex)) 
    
    elif(inpString == "REF"): 
        print("\nenter 2 to remove image effect") 
        print("enter 1 to remove text effect") 
        inputElem = input()
        if(inputElem == "2"): 
            print("enter imageListIndex, trackListIndex") 
            imageListIndex,trackListIndex = input().split() 
            VideoEditing.removeEffect(2,int(imageListIndex) , int(trackListIndex)) 
        else: 
            print("enter textListIndex, trackListIndex") 
            textListIndex,trackListIndex = input().split() 
            VideoEditing.removeEffect(1,int(textListIndex) , int(trackListIndex))
    elif(inpString == "S"): 
        print("\nenter trackIndex and timeOfCut") 
        trackIndex,timeOfCut = input().split() 
        VideoEditing.sliceClip(int(trackIndex),int(timeOfCut)) 
    elif(inpString == "RO"): 
        print("\nenter the required permuted list")  
        permutedList = [int(x) for x in input().split()]
        VideoEditing.reorderClips(permutedList) 
    elif(inpString == "DL"): 
        print("\nEnter name of output file") 
        path = input() 
        VideoEditing.download(path) 
    elif(inpString == "EY"): 
        print("\nEnter name of output file") 
        path = input() 
        VideoEditing.exportToYouTube(path)
    else:
        print("Wrong code entered, re-enter") 

    print("\n\n")