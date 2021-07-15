"""
MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import c4d
from c4d import utils
from c4d.modules import mograph
import math
import random
ID_NETWORK = 1057291

ID_NETWORK_INPUTLINKLIST = 1000
ID_NETWORK_MAXDISTANCE = 1001
ID_NETWORK_MAXCONNECTIONS = 1002
ID_NETWORK_FIELD = 1003
ID_NETWORK_FIELDGROUP = 1004
ID_NETWORK_SCRAMBLER = 1005
ID_NETWORK_SCRAMBLESEED = 1006

def CheckSelfReferencing(startObject, op):
    objectStack = []
    objectStack.append(startObject)

    firstObject = True

    while objectStack:
        currentObject = objectStack.pop()
        if currentObject == op:
            return True

        downObject = currentObject.GetDown()
        if downObject is not None:
            objectStack.append(downObject)

        if not firstObject:
            nextObject = currentObject.GetNext()
            if nextObject is not None:
                objectStack.append(nextObject)
        
        firstObject = False
        
    return False

def CollectChildDirty(startObject, op, ignoreFirst):
    objectStack = []
    objectStack.append(startObject)

    firstObject = True
    dirtyCount = 0
    while objectStack:
        currentObject = objectStack.pop()

        downObject = currentObject.GetDown()
        if downObject is not None and downObject != op:
            objectStack.append(downObject)

        cacheObject = currentObject.GetCache()
        if cacheObject is not None:
            objectStack.append(cacheObject)

        deformCacheObject = currentObject.GetDeformCache()
        if deformCacheObject is not None:
            objectStack.append(deformCacheObject)

        if not firstObject:
            nextObject = currentObject.GetNext()
            if nextObject is not None and nextObject != op:
                objectStack.append(nextObject)

        if ignoreFirst and firstObject:
            firstObject = False
            continue

        dirtyCount += currentObject.GetDirty(c4d.DIRTYFLAGS_DATA | c4d.DIRTYFLAGS_MATRIX | c4d.DIRTYFLAGS_CACHE)

        firstObject = False

    return dirtyCount

class NetworkObjectData(c4d.plugins.ObjectData):

    def __init__(self):
        self.inputLinkMatrixDirty = 0
        self.selfDirtyCount = 0
        self.prevChildDirty = 0
        self.fieldInputDirty = 0
        self.points = []
        self.dummyObject = c4d.BaseObject(c4d.Onull)

    def Init(self, node):   
        node[ID_NETWORK_MAXDISTANCE] = 10.0
        node[ID_NETWORK_MAXCONNECTIONS] = 6
        node[ID_NETWORK_SCRAMBLESEED] = 12345
        node[ID_NETWORK_SCRAMBLER] = True
        """set a generator like color override for the icon"""
        node[c4d.ID_BASELIST_ICON_COLORIZE_MODE] = c4d.ID_BASELIST_ICON_COLORIZE_MODE_CUSTOM
        node[c4d.ID_BASELIST_ICON_COLOR] = c4d.Vector(153.0 / 255.0, 1.0 , 173.0 / 255.0)
        return True

    def GetDDescription(self, node, description, flags):
        # Before adding dynamic parameters, load the parameters from the description resource
        if not description.LoadDescription(node.GetType()):
            return False
        # After parameters have been loaded and added successfully, return True and DESCFLAGS_DESC_LOADED with the input flags
        return (True, flags | c4d.DESCFLAGS_DESC_LOADED)

    def GetDEnabling(self, node, id, t_data, flags, itemdesc):
        if id[0].id == ID_NETWORK_SCRAMBLESEED:
            return node[ID_NETWORK_SCRAMBLER] == True
        return True

    def CheckDirty(self, op, doc):
        inputLinks = op[ID_NETWORK_INPUTLINKLIST]
        newDirty = 0
        inputCount = inputLinks.GetObjectCount()
        for x in range(inputCount):
            listInputObject = inputLinks.ObjectFromIndex(doc, x)
            if listInputObject is None:
                continue

            newDirty += CollectChildDirty(listInputObject, op, False)

        newDirty += self.CheckFieldListDirty(op, doc)

        if self.prevChildDirty != newDirty:
            self.prevChildDirty = newDirty
            op.SetDirty(c4d.DIRTYFLAGS_DATA)

    def ParseObjects(self, op, startObject, pointObjList):
        objectStack = []
        objectStack.append(startObject)
        firstObject = True
        dirtyCount = 0
        while objectStack:
            currentObject = objectStack.pop()

            downObject = currentObject.GetDown()
            if downObject is not None and downObject != op:
                objectStack.append(downObject)

            if not firstObject:
                nextObject = currentObject.GetNext()
                if nextObject is not None and nextObject != op:
                    objectStack.append(nextObject)
 
            cacheObject = currentObject.GetCache()
            if cacheObject is not None:
                objectStack.append(cacheObject)

            deformcacheObject = currentObject.GetDeformCache()
            if deformcacheObject is not None:
                objectStack.append(deformcacheObject)

            if not currentObject.GetBit(c4d.BIT_CONTROLOBJECT) and currentObject.IsInstanceOf(c4d.Opoint) and deformcacheObject is None:
                pointObjList.append(currentObject)

            firstObject = False

    def GeneratePoints(self, op, doc):
        self.points = []
        inputLinks = op[ID_NETWORK_INPUTLINKLIST]
        if inputLinks is None:
            return

        pointObjects = []
        matrixObjects = []
        inputCount = inputLinks.GetObjectCount()
        for x in range(inputCount):
            listInputObject = inputLinks.ObjectFromIndex(doc, x)
            if listInputObject is None:
                continue
            flags = inputLinks.GetFlags(x)
            if flags == 0:
                continue
            if listInputObject.IsInstanceOf(1018545): # matrix obj id
                matrixObjects.append(listInputObject)
            else:
                self.ParseObjects(op, listInputObject, pointObjects)

        for matrixObject in matrixObjects:
            matrixMatrixhehe = matrixObject.GetMg()
            moData = mograph.GeGetMoData(matrixObject)
            if moData is not None:
                matrixArray = moData.GetArray(c4d.MODATA_MATRIX)
                if matrixArray is not None:
                    flags = moData.GetArray(c4d.MODATA_FLAGS)
                    for entryIndex in range(len(matrixArray)):
                        if not flags[entryIndex]&c4d.MOGENFLAG_CLONE_ON or flags[entryIndex]&c4d.MOGENFLAG_DISABLE:
                            continue
                        self.points.append(matrixMatrixhehe * matrixArray[entryIndex].off)
        # collect all points from point objects
        for pointObj in pointObjects:
            self.points.extend(pointObj.GetAllPoints())
            pointCount = pointObj.GetPointCount()
            newLen = len(self.points)
            objectMat = pointObj.GetMg()
            # bring new points into world space
            for newPointIndex in range(newLen - pointCount, newLen):
                self.points[newPointIndex] = objectMat * self.points[newPointIndex]

    def GenerateSplines(self, op):
        maxDist = op[ID_NETWORK_MAXDISTANCE]
        maxDistSquared = maxDist * maxDist
        maxConns = op[ID_NETWORK_MAXCONNECTIONS]
        scramble = list(range(len(self.points)))
        if op[ID_NETWORK_SCRAMBLER]:
            random.seed(op[ID_NETWORK_SCRAMBLESEED])
            random.shuffle(scramble)

        pointActive = [True] * len(self.points)
        fieldList = op[ID_NETWORK_FIELD]
        if fieldList is not None and self.CheckFieldListContent(fieldList, op.GetDocument()) and len(self.points) > 0:
            fieldInput = mograph.FieldInput(self.points, len(self.points))
            output = fieldList.SampleListSimple(op, fieldInput,c4d.FIELDSAMPLE_FLAG_VALUE)
            if len(output._value) == len(pointActive):
                for pointIndex in range(len(pointActive)):
                    pointActive[pointIndex] = output._value[pointIndex] >= 0.5

        connections = [0] * len(self.points)
        splinePoints = []
        segmentCount = 0
        pointCount = len(self.points)
        for active in range(pointCount):
            indexOne = scramble[active]
            if not pointActive[indexOne]:
                continue

            for other in range(active + 1, pointCount):
                
                indexTwo = scramble[other]
                if connections[indexOne] >= maxConns:
                    break
                if not pointActive[indexTwo] or connections[indexTwo] >= maxConns:
                    continue

                if (self.points[indexOne] - self.points[indexTwo]).GetLengthSquared() < maxDistSquared:
                    splinePoints.append(self.points[indexOne])
                    splinePoints.append(self.points[indexTwo])
                    segmentCount += 1
                    connections[indexOne] += 1
                    connections[indexTwo] += 1
        if segmentCount == 0:
            return c4d.SplineObject(0, 0)    
        newSpline = c4d.SplineObject(segmentCount * 2, c4d.SPLINETYPE_LINEAR)
        newSpline.ResizeObject(segmentCount * 2, segmentCount)
        newSpline.SetAllPoints(splinePoints)
        for segIndex in range(segmentCount):
            newSpline.SetSegment(segIndex, 2, False)

        return newSpline

    def CheckFieldListDirty(self, op, doc):
        fieldList = op[ID_NETWORK_FIELD]
        if fieldList is None or fieldList.HasContent() == False:
            return 0
        root = fieldList.GetLayersRoot()
        if root is None or root.GetDown() is None:
            return fieldList.GetDirty(doc)
        fieldDirty = fieldList.GetDirty(doc)
        iterateList = []
        iterateList.append(root.GetDown())
        while len(iterateList) > 0:
            currentLayer = iterateList.pop()

            if currentLayer.GetNext() is not None:
                iterateList.append(currentLayer.GetNext())

            if currentLayer.GetDown() is not None:
                iterateList.append(currentLayer.GetDown())

            objectField = currentLayer.GetLinkedObject(doc)
            if objectField is not None:
                fieldDirty += objectField.GetDirty(c4d.DIRTYFLAGS_MATRIX | c4d.DIRTYFLAGS_DATA)
        return fieldDirty
            
    def CheckFieldListContent(self, fieldList, doc):
        if fieldList is None or fieldList.HasContent() == False:
            return False
        root = fieldList.GetLayersRoot()
        if root is None or root.GetDown() is None:
            return fieldList.GetDirty(doc)
        fieldDirty = fieldList.GetDirty(doc)
        iterateList = []
        iterateList.append(root.GetDown())
        while len(iterateList) > 0:
            currentLayer = iterateList.pop()

            if currentLayer.GetNext() is not None:
                iterateList.append(currentLayer.GetNext())

            if currentLayer.GetDown() is not None:
                iterateList.append(currentLayer.GetDown())

            objectField = currentLayer.GetLinkedObject(doc)
            if objectField is not None:
                return True
        return False

    def GetVirtualObjects(self, op, hh):
        inputLinks = op[ID_NETWORK_INPUTLINKLIST]
        if inputLinks is None:
            return c4d.BaseObject(c4d.Onull)

        settingsDirty = False
        newDirty = op.GetDirty(c4d.DIRTYFLAGS_DATA | c4d.DIRTYFLAGS_MATRIX)

        if newDirty != self.selfDirtyCount:
            self.selfDirtyCount = newDirty
            settingsDirty = True

        inputDirty = False
        doc = op.GetDocument()
        inputCount = inputLinks.GetObjectCount()
        self.dummyObject.NewDependenceList()
        inputLinkMatrixDirtyNew = 0
        for x in range(inputCount):
            listInputObject = inputLinks.ObjectFromIndex(doc, x)
            if listInputObject is None:
                continue
            flags = inputLinks.GetFlags(x)
            if flags == 0:
                continue
            selfReferencing = CheckSelfReferencing(listInputObject, op)
            if not selfReferencing:
                self.dummyObject.GetHierarchyClone(hh, listInputObject, c4d.HIERARCHYCLONEFLAGS_ASLINE | c4d.HIERARCHYCLONEFLAGS_ASPOLY, inputDirty, None, c4d.DIRTYFLAGS_DATA | c4d.DIRTYFLAGS_MATRIX | c4d.DIRTYFLAGS_CACHE)
                if not inputDirty:
                    inputLinkMatrixDirtyNew += CollectChildDirty(listInputObject, op, False)
                    # inputLinkMatrixDirtyNew += listInputObject.GetDirty(c4d.DIRTYFLAGS_MATRIX | c4d.DIRTYFLAGS_DATA | c4d.DIRTYFLAGS_CACHE) + listInputObject.GetHDirty(c4d.HDIRTYFLAGS_OBJECT_MATRIX | c4d.HDIRTYFLAGS_OBJECT)
        if inputLinkMatrixDirtyNew != self.inputLinkMatrixDirty:
            inputDirty = True
            self.inputLinkMatrixDirty = inputLinkMatrixDirtyNew

        newFieldInputDirty = self.CheckFieldListDirty(op, doc)
        if self.fieldInputDirty != newFieldInputDirty:
            self.fieldInputDirty = newFieldInputDirty
            settingsDirty = True

        if not settingsDirty and not inputDirty:
            return op.GetCache(hh)
        
        if inputDirty:
            self.GeneratePoints(op, doc)

        returnObject = self.GenerateSplines(op)
        
        self.TranformPoints(op, returnObject)
        if returnObject is not None:
            op.SetDirty(c4d.DIRTYFLAGS_DATA)
            self.selfDirtyCount =  self.selfDirtyCount + 1

            return returnObject

        # nothing was done. Output a dummy nullobj
        return c4d.BaseObject(c4d.Onull)

    def TranformPoints(self, op, spline):
        if spline is not None:
            matrix = ~op.GetMg() * spline.GetMg()
            pointCount = spline.GetPointCount()
            for pointIndex in range(0, pointCount):
                spline.SetPoint(pointIndex, matrix * spline.GetPoint(pointIndex))

            spline.SetMg(c4d.Matrix())

    def GetContour(self, op, doc, lod, bt):
        if op.GetDeformMode() == False:
            return None

        self.GeneratePoints(op, doc)
        returnObject = self.GenerateSplines(op)
        self.TranformPoints(op, returnObject)
        if returnObject is not None:
            returnObject.SetName(op.GetName())
        return returnObject

    def GetBubbleHelp(self, node):
        return "Creates a Network on the points of the input"


if __name__ == "__main__":
    c4d.plugins.RegisterObjectPlugin(id=ID_NETWORK,
                                     str="Network",
                                     g=NetworkObjectData,
                                     description="opynetwork",
                                     icon=c4d.bitmaps.InitResourceBitmap(14004),
                                     info=c4d.OBJECT_GENERATOR | c4d.OBJECT_ISSPLINE)
