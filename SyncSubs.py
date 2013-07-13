import os
import os.path
import string
import re
import sys
import traceback
import shutil

rePatterns = ["[Ss](?P<season>\d{1,3}).*[Ee](?P<episode>\d{1,3})",
               "(?P<season>\d{1,3})[x-](?P<episode>\d{1,3})",
               "(?P<season>\d{1,2})?(?P<episode>\d{2})",
               "[Ee](?P<episode>\d{2})"]
       
reExpressions = [re.compile(rePattern) for rePattern in rePatterns]

ZIP_APP_PATH = r"c:\Program Files\7-zip"
#UNPACK_COMMAND_INTERNAL_ZIPS = ("%s" % ZIP_APP_PATH) + " e -y -ozips '%s' *.zip"
UNPACK_COMMAND_INTERNAL_ZIPS = '7z.exe e -y -ozips "%s" *.zip'
UNPACK_COMMAND_SUBS = '7z.exe e -y \"%s\" *.srt *.sub'


class MediaObj():
    def __init__(self):
        self.MediaName = None
        self.SubtitleName = None

class EpisodeInfo():
    def __init__(self):
        self.Season = 0
        self.Episode = 0
    def Id(self):
        return "%d-%d" % (self.Season, self.Episode)

def IsMediaFile(fileName):
    mediaExtensions = ["avi", "mp4", "wmv", "mkv"]
    for extension in mediaExtensions:
        if fileName.endswith("." + extension):
            return True
    return False

def IsSubtitleFile(fileName):
    subtitleExtensions = ["srt", "sub"]
    for extension in subtitleExtensions:
        if fileName.endswith("." + extension):
            return True
    return False

def GetExtension(fileName):
    dotIndex = fileName.rfind('.')
    if dotIndex == None:
        return None
    return fileName[dotIndex+1:]

def GetFileNameWithoutExt(fileName):
    dotIndex = fileName.rfind('.')
    if dotIndex == None:
        return fileName
    return fileName[:dotIndex]
    
def GetSeasonFromFolderName(folderName):
    return 3

def GetSeasonAndEpisode(fileName):
    match = None
    for reExp in reExpressions:
        match = reExp.search(fileName)
        if match != None:
            break
    
    if match == None:
        return None
    
    info = EpisodeInfo()
    episode = match.group('episode')
    season = match.group('season')
    
    if season == None:
        season = '1'

    info.Episode = int(episode)
    info.Season = int(season)
    
    return info

def RenameSubtitleFiles(path, matchDict):
    for mediaObj in matchDict.values():
        if mediaObj.MediaName != None and mediaObj.SubtitleName == None:
            print "Missing subtitle for media file: %s" % mediaObj.MediaName
            continue
        elif mediaObj.MediaName == None and mediaObj.SubtitleName != None:
            print "Missing media file for subtitle: %s" % mediaObj.SubtitleName
            continue
        
        newSubtitleName = GetFileNameWithoutExt(mediaObj.MediaName) + "." + GetExtension(mediaObj.SubtitleName)
        if mediaObj.SubtitleName == newSubtitleName:
            print "Nothing to do for: %s" % mediaObj.SubtitleName
            continue
        
        print "%s\n==> %s" % (mediaObj.SubtitleName, newSubtitleName)
        if os.path.exists(path + "/" + newSubtitleName):
            print "Subtitle file already exists: %s" % newSubtitleName
            continue		

        os.rename(path + "/" + mediaObj.SubtitleName, path + "/" + newSubtitleName)

def ExtractSubtitleFiles(folderName):
    if not os.path.exists(ZIP_APP_PATH):
        print "Install 7-zip to automatically extract subs"
        return
    
    print os.environ['path']
    os.environ['path'] += ';' + ZIP_APP_PATH
    
    os.mkdir('zips')
    
    #os.system("path=%s" % ZIP_APP_PATH)
    zipList = [fileName for fileName in os.listdir(folderName) if fileName.endswith(".zip")]
    for zipFile in zipList:
        print "trying to extract zips files from zip file: %s" % zipFile
                
        print UNPACK_COMMAND_INTERNAL_ZIPS % zipFile
        os.system(UNPACK_COMMAND_INTERNAL_ZIPS % zipFile)
        shutil.copyfile(zipFile, "zips/" + zipFile)
        
    internalZipList = [fileName for fileName in os.listdir("zips") if fileName.endswith(".zip")]
    for zipFile in internalZipList:
        print "trying to extract subs from zip file: zips/%s" % zipFile
        print UNPACK_COMMAND_SUBS % ("zips/" + zipFile)
        os.system(UNPACK_COMMAND_SUBS % ("zips/" + zipFile))
    
    shutil.rmtree("zips", True)
        
def SyncFolder(folderName):
    folderInfo = {}
    fileList = os.listdir(folderName)
   
    for fileName in fileList:
        episodeInfo = GetSeasonAndEpisode(fileName)
        if episodeInfo is None:
            print "No episode info for: %s" % fileName
            continue
        
        if episodeInfo.Season == 0:
            episodeInfo.Season = GetSeasonFromFolderName(folderName)

        mediaObj = None
        if episodeInfo.Id() in folderInfo.keys():
            mediaObj = folderInfo[episodeInfo.Id()]
        else:
            mediaObj = MediaObj()
        
        if IsMediaFile(fileName.lower()):
            if mediaObj.MediaName != None:
                msg = "Error: Found 2 media files with same season and episode number: %d, %d\n %s\n %s" % (episodeInfo.Season, episodeInfo.Episode, fileName, mediaObj.MediaName)
                #print msg
                raise Exception(msg)
            mediaObj.MediaName = fileName
        elif IsSubtitleFile(fileName.lower()):
            if mediaObj.SubtitleName != None:
                print("Found 2 subtitle files with same season and episode number: %d, %d\
    \n %s\n %s" % (episodeInfo.Season, episodeInfo.Episode, fileName, mediaObj.SubtitleName))
                continue
            mediaObj.SubtitleName = fileName
        else:
            print "Ignoring file: %s" % fileName
            continue
        
        folderInfo[episodeInfo.Id()] = mediaObj

       
    RenameSubtitleFiles(folderName, folderInfo)
    print "Sync complete."
    return

if __name__ == '__main__':
    try:
        folderName = os.getcwd()
        ExtractSubtitleFiles(folderName)
        SyncFolder(folderName)
    except Exception, e:
        exceptionType, exceptionValue, exceptionTraceback = sys.exc_info()
        print e
        traceback.print_tb(exceptionTraceback, limit=5, file=sys.stdout)
    finally:
        print "press any key..."
        ch = sys.stdin.read(1)
