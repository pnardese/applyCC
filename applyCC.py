#!/usr/bin/env python

import DaVinciResolveScript as dvr_script
import xml.etree.ElementTree as ET
import os
import sys

# Tested with Davinci Resolve 17.4 Build 12 and python 3.6.13 
# virtual env activated with conda: 
# > conda activate davinci_virtual_env
# > conda develop /PATH/TO/YOUR/FOLDER/WITH/MODULES
# ex. conda develop "/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/Modules"
# Define a node tree in Color Tab with two nodes, ASC-CDLs and LUTs must contain the same name of the clips

# Read an ASC-CDL file and produce a list of dict

def GetCDL(cdl):
    CDLdataList = []
    tree = ET.parse(cdl)
    root = tree.getroot()
    slope = root[0][0][0][1].text
    offset = root[0][0][0][2].text
    power = root[0][0][0][3].text
    sat = root[0][0][1][0].text
    filename = os.path.basename(cdl)
    CDLdataList.append({"Clip": os.path.splitext(filename)[0], "NodeIndex" : "1", "Slope": str(slope), "Offset": str(offset), "Power": str(power), "Saturation": str(sat)})
    return CDLdataList

if __name__ == "__main__":
    # script init
    resolve = dvr_script.scriptapp("Resolve")

    projectmanager = resolve.GetProjectManager()
    project = projectmanager.GetCurrentProject()
    mediapool = project.GetMediaPool()
    currentbin = mediapool.GetCurrentFolder()
    timeline = project.GetCurrentTimeline()
    Clips = timeline.GetItemListInTrack("video", 1)
    
    # absolute CDL folder path
    cdlPath = '/path/to/CDL'
    
    # LUT folder (must be in DaVinci LUT path) 
    LUTPath = '/Library/Application Support/Blackmagic Design/DaVinci Resolve/LUT/LUT_FROM_DIT'
    
    # exclude hidden files on Mac
    LUTFileList = [f for f in os.listdir(LUTPath) if not f.startswith('.')]

    # CDL file list in cdlPath
    cdlFileList = [f for f in os.listdir(cdlPath) if not f.startswith('.')]

    cdlMaps =[]
    LUTList =[]

    # read CDLs, produce a list of CDLs made of dicts (cdlMaps)
    for item in cdlFileList:
            extension = os.path.splitext(item)[1]
            if extension == ".cdl":
                cdlFileName = cdlPath + "/" + item
                cdlMaps.append(GetCDL(cdlFileName))

    # read LUTs, produce a list of dicts (LUTList)
    for item in LUTFileList:
        extension = os.path.splitext(item)[1]
        clip = os.path.splitext(item)[0]
        if extension == ".dat":
            LUTFilePath = LUTPath + "/" + item
            LUTList.append({"Clip" : clip, "LUT" : LUTFilePath})
    
    # Apply the CDL Maps to clips at NodeIndex = 1, then apply LUTs at NodeIndex = 2 
    for clip in Clips:
        for cdl in cdlMaps:
            if clip.GetName() in cdl[0]["Clip"]:
                Map = dict([(x,cdl[0][x]) for x in ['NodeIndex', 'Slope', 'Offset', 'Power', 'Saturation']])
                print("Clip Name: " + cdl[0]["Clip"] + " -> " + "CDL: " + str(Map))
                clip.SetCDL(Map)
        for lut in LUTList:
            if clip.GetName() in lut["Clip"]:
                print("Clip Name: " + lut['Clip'] + " -> " + "LUT: " + lut["LUT"])
                # Two nodes must be created in Color Tab for each clip (create powergrade and apply to all clips)
                clip.SetLUT(2, lut["LUT"])
	