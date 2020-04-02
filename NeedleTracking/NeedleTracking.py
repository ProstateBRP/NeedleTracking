import os
import unittest
import time
from __main__ import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
from NeedleTrackingUtils.trackingdata import *
from NeedleTrackingUtils.connector import *
from NeedleTrackingUtils.reslice import *
#from NeedleTrackingUtils.registration import *
import numpy
import functools

#------------------------------------------------------------
#
# NeedleTracking
#
class NeedleTracking(ScriptedLoadableModule):
  """MRTrakcing module is available at:
  https://github.com/ProstateBRP/NeedleTracking
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "NeedleTracking" # TODO make this more human readable by adding spaces
    self.parent.categories = ["IGT"]
    self.parent.dependencies = []
    self.parent.contributors = ["Junichi Tokuda (BWH)"]
    self.parent.helpText = """
    Visualization of shape-sensing needle 
    """
    self.parent.acknowledgementText = """
    This work is supported by NIH (P41EB015898, R01EB020667).
    """ 


#------------------------------------------------------------
#
# NeedleTrackingWidget
#
class NeedleTrackingWidget(ScriptedLoadableModuleWidget):
  
  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)
    # Instantiate and connect widgets ...

    self.logic = NeedleTrackingLogic(None)
    self.logic.setWidget(self)

    #--------------------------------------------------
    # For debugging
    #
    # Reload and Test area
    reloadCollapsibleButton = ctk.ctkCollapsibleButton()
    reloadCollapsibleButton.text = "Reload && Test"
    self.layout.addWidget(reloadCollapsibleButton)
    reloadFormLayout = qt.QFormLayout(reloadCollapsibleButton)

    reloadCollapsibleButton.collapsed = True
    
    # reload button
    # (use this during development, but remove it when delivering
    #  your module to users)
    self.reloadButton = qt.QPushButton("Reload")
    self.reloadButton.toolTip = "Reload this module."
    self.reloadButton.name = "Reload"
    reloadFormLayout.addWidget(self.reloadButton)
    self.reloadButton.connect('clicked()', self.onReload)
    #
    #--------------------------------------------------

    self.nCath = 1      # Number of catheters

    #--------------------------------------------------
    # GUI components
    
    #
    # Connection Area
    #
    connectionCollapsibleButton = ctk.ctkCollapsibleButton()
    connectionCollapsibleButton.text = "Connection (OpenIGTLink)"
    self.layout.addWidget(connectionCollapsibleButton)

    # Layout within the dummy collapsible button
    connectionFormLayout = qt.QFormLayout(connectionCollapsibleButton)

    #--------------------------------------------------
    # Connector Selector
    #--------------------------------------------------

    self.igtlConnector1 = NeedleTrackingIGTLConnector("Connector 1")
    self.igtlConnector1.port = 18944
    self.igtlConnector1.buildGUI(connectionFormLayout)

    #--------------------------------------------------
    # Catheter
    #--------------------------------------------------

    catheterCollapsibleButton = ctk.ctkCollapsibleButton()
    catheterCollapsibleButton.text = "Tracking Node"
    self.layout.addWidget(catheterCollapsibleButton)

    catheterFormLayout = qt.QFormLayout(catheterCollapsibleButton)

    #--------------------------------------------------
    # Tracking node selector

    trackingNodeGroupBox = ctk.ctkCollapsibleGroupBox()
    trackingNodeGroupBox.title = "Tracking Node"
    catheterFormLayout.addWidget(trackingNodeGroupBox)
    trackingNodeFormLayout = qt.QFormLayout(trackingNodeGroupBox)
    
    self.trackingDataSelector = slicer.qMRMLNodeComboBox()
    self.trackingDataSelector.nodeTypes = ( ("vtkMRMLIGTLTrackingDataBundleNode"), "" )
    self.trackingDataSelector.selectNodeUponCreation = True
    self.trackingDataSelector.addEnabled = True
    self.trackingDataSelector.removeEnabled = False
    self.trackingDataSelector.noneEnabled = False
    self.trackingDataSelector.showHidden = True
    self.trackingDataSelector.showChildNodeTypes = False
    self.trackingDataSelector.setMRMLScene( slicer.mrmlScene )
    self.trackingDataSelector.setToolTip( "Incoming tracking data" )
    trackingNodeFormLayout.addRow("TrackingData: ", self.trackingDataSelector)

    #
    # check box to trigger transform conversion
    #
    self.activeTrackingCheckBox = qt.QCheckBox()
    self.activeTrackingCheckBox.checked = 0
    self.activeTrackingCheckBox.enabled = 1
    self.activeTrackingCheckBox.setToolTip("Activate Tracking")
    trackingNodeFormLayout.addRow("Active: ", self.activeTrackingCheckBox)
    
    #--------------------------------------------------
    # Catheter Configuration

    configGroupBox = ctk.ctkCollapsibleGroupBox()
    configGroupBox.title = "Catheter Configuration"
    configGroupBox.collapsed = True

    catheterFormLayout.addWidget(configGroupBox)
    configFormLayout = qt.QFormLayout(configGroupBox)


    self.tipLengthSliderWidget = [None] * self.nCath
    self.catheterDiameterSliderWidget = [None] * self.nCath
    self.catheterOpacitySliderWidget = [None] * self.nCath
    
    for cath in range(self.nCath):
      
      #
      # Tip Length (legnth between the catheter tip and the first coil)
      #
      self.tipLengthSliderWidget[cath] = ctk.ctkSliderWidget()
      self.tipLengthSliderWidget[cath].singleStep = 0.5
      self.tipLengthSliderWidget[cath].minimum = 0.0
      self.tipLengthSliderWidget[cath].maximum = 100.0
      self.tipLengthSliderWidget[cath].value = 10.0
      self.tipLengthSliderWidget[cath].setToolTip("Set the length of the catheter tip.")
      configFormLayout.addRow("Cath %d Tip Length (mm): " % cath, self.tipLengthSliderWidget[cath])
      
      #
      # Catheter #1 Catheter diameter
      #
      self.catheterDiameterSliderWidget[cath] = ctk.ctkSliderWidget()
      self.catheterDiameterSliderWidget[cath].singleStep = 0.1
      self.catheterDiameterSliderWidget[cath].minimum = 0.1
      self.catheterDiameterSliderWidget[cath].maximum = 10.0
      self.catheterDiameterSliderWidget[cath].value = 1.0
      self.catheterDiameterSliderWidget[cath].setToolTip("Set the diameter of the catheter")
      configFormLayout.addRow("Cath %d Diameter (mm): " % cath, self.catheterDiameterSliderWidget[cath])
      
      #
      # Catheter #1 Catheter opacity
      #
      self.catheterOpacitySliderWidget[cath] = ctk.ctkSliderWidget()
      self.catheterOpacitySliderWidget[cath].singleStep = 0.1
      self.catheterOpacitySliderWidget[cath].minimum = 0.0
      self.catheterOpacitySliderWidget[cath].maximum = 1.0
      self.catheterOpacitySliderWidget[cath].value = 1.0
      self.catheterOpacitySliderWidget[cath].setToolTip("Set the opacity of the catheter")
      configFormLayout.addRow("Cath %d Opacity: " % cath, self.catheterOpacitySliderWidget[cath])

    #
    # Check box to show/hide coil labels 
    #
    self.showCoilLabelCheckBox = qt.QCheckBox()
    self.showCoilLabelCheckBox.checked = 0
    self.showCoilLabelCheckBox.setToolTip("Show/hide coil labels")
    configFormLayout.addRow("Show Coil Labels: ", self.showCoilLabelCheckBox)
    

    #--------------------------------------------------
    # Coordinate System
    #
    coordinateGroupBox = ctk.ctkCollapsibleGroupBox()
    coordinateGroupBox.title = "Coordinate System"
    coordinateGroupBox.collapsed = True
    
    catheterFormLayout.addWidget(coordinateGroupBox)
    coordinateLayout = qt.QFormLayout(coordinateGroupBox)
    
    self.coordinateRPlusRadioButton = qt.QRadioButton("+X")
    self.coordinateRMinusRadioButton = qt.QRadioButton("-X")
    self.coordinateRPlusRadioButton.checked = 1
    self.coordinateRBoxLayout = qt.QHBoxLayout()
    self.coordinateRBoxLayout.addWidget(self.coordinateRPlusRadioButton)
    self.coordinateRBoxLayout.addWidget(self.coordinateRMinusRadioButton)
    self.coordinateRGroup = qt.QButtonGroup()
    self.coordinateRGroup.addButton(self.coordinateRPlusRadioButton)
    self.coordinateRGroup.addButton(self.coordinateRMinusRadioButton)
    coordinateLayout.addRow("Right:", self.coordinateRBoxLayout)

    self.coordinateAPlusRadioButton = qt.QRadioButton("+Y")
    self.coordinateAMinusRadioButton = qt.QRadioButton("-Y")
    self.coordinateAPlusRadioButton.checked = 1
    self.coordinateABoxLayout = qt.QHBoxLayout()
    self.coordinateABoxLayout.addWidget(self.coordinateAPlusRadioButton)
    self.coordinateABoxLayout.addWidget(self.coordinateAMinusRadioButton)
    self.coordinateAGroup = qt.QButtonGroup()
    self.coordinateAGroup.addButton(self.coordinateAPlusRadioButton)
    self.coordinateAGroup.addButton(self.coordinateAMinusRadioButton)
    coordinateLayout.addRow("Anterior:", self.coordinateABoxLayout)

    self.coordinateSPlusRadioButton = qt.QRadioButton("+Z")
    self.coordinateSMinusRadioButton = qt.QRadioButton("-Z")
    self.coordinateSPlusRadioButton.checked = 1
    self.coordinateSBoxLayout = qt.QHBoxLayout()
    self.coordinateSBoxLayout.addWidget(self.coordinateSPlusRadioButton)
    self.coordinateSBoxLayout.addWidget(self.coordinateSMinusRadioButton)
    self.coordinateSGroup = qt.QButtonGroup()
    self.coordinateSGroup.addButton(self.coordinateSPlusRadioButton)
    self.coordinateSGroup.addButton(self.coordinateSMinusRadioButton)
    coordinateLayout.addRow("Superior:", self.coordinateSBoxLayout)

    #--------------------------------------------------
    # Reslice
    #
    resliceCollapsibleButton = ctk.ctkCollapsibleButton()
    resliceCollapsibleButton.text = "Image Reslice"
    self.layout.addWidget(resliceCollapsibleButton)

    #resliceLayout = qt.QFormLayout(resliceCollapsibleButton)

    self.reslice = NeedleTrackingReslice("Image Reslice")
    self.reslice.nCath = self.nCath
    self.reslice.buildGUI(resliceCollapsibleButton)
    
    #--------------------------------------------------
    # Connections
    #--------------------------------------------------
    self.trackingDataSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onTrackingDataSelected)
    self.activeTrackingCheckBox.connect('toggled(bool)', self.onActiveTracking)

    for cath in range(self.nCath):
      self.tipLengthSliderWidget[cath].connect("valueChanged(double)", functools.partial(self.onTipLengthChanged, cath))
      self.catheterDiameterSliderWidget[cath].connect("valueChanged(double)", functools.partial(self.onCatheterDiameterChanged, cath))
      self.catheterOpacitySliderWidget[cath].connect("valueChanged(double)", functools.partial(self.onCatheterOpacityChanged, cath))

    self.showCoilLabelCheckBox.connect('toggled(bool)', self.onCoilLabelChecked)

    self.coordinateRPlusRadioButton.connect('clicked(bool)', self.onSelectCoordinate)
    self.coordinateRMinusRadioButton.connect('clicked(bool)', self.onSelectCoordinate)
    self.coordinateAPlusRadioButton.connect('clicked(bool)', self.onSelectCoordinate)
    self.coordinateAMinusRadioButton.connect('clicked(bool)', self.onSelectCoordinate)
    self.coordinateSPlusRadioButton.connect('clicked(bool)', self.onSelectCoordinate)
    self.coordinateSMinusRadioButton.connect('clicked(bool)', self.onSelectCoordinate)
    
    # Add vertical spacer
    self.layout.addStretch(1)


  def cleanup(self):
    pass

  def onActiveTracking(self):
    if self.activeTrackingCheckBox.checked == True:
      self.logic.activateTracking()
    else:
      self.logic.deactivateTracking()

    
  def onTrackingDataSelected(self):
    tdnode = self.trackingDataSelector.currentNode()    
    tdata = self.logic.switchCurrentTrackingData(tdnode)
    self.updateTrackingDataGUI(tdata)

    if tdata.eventTag != '':
      self.activeTrackingCheckBox.checked == True
    else:
      self.activeTrackingCheckBox.checked == False
      
      
  def onTipLengthChanged(self, cath, checked):
    print("onTipLengthChanged(%d)" % cath)
    self.logic.setTipLength(self.tipLengthSliderWidget[cath].value, cath)
  
    
  def onCatheterDiameterChanged(self, cath, checked):
    self.logic.setCatheterDiameter(self.catheterDiameterSliderWidget[cath].value, cath)
    
  
  def onCatheterOpacityChanged(self, cath, checked):
    self.logic.setCatheterOpacity(self.catheterOpacitySliderWidget[cath].value, cath)

  def onCoilLabelChecked(self):
    self.logic.setShowCoilLabel(self.showCoilLabelCheckBox.checked)


  def onSelectCoordinate(self):

    rPositive = self.coordinateRPlusRadioButton.checked
    aPositive = self.coordinateAPlusRadioButton.checked
    sPositive = self.coordinateSPlusRadioButton.checked
    
    self.logic.setAxisDirections(rPositive, aPositive, sPositive)
    
      
  def onReload(self, moduleName="NeedleTracking"):
    # Generic reload method for any scripted module.
    # ModuleWizard will subsitute correct default moduleName.

    globals()[moduleName] = slicer.util.reloadScriptedModule(moduleName)


  def updateTrackingDataGUI(self, tdata):
    # Enable/disable GUI components based on the state machine
    
    if self.logic.isTrackingActive():
      self.activeTrackingCheckBox.checked = True
    else:
      self.activeTrackingCheckBox.checked = False


    for cath in range(self.nCath):
      self.tipLengthSliderWidget[cath].value = tdata.tipLength[cath]
      self.catheterDiameterSliderWidget[cath].value = tdata.radius[cath] * 2
      self.catheterOpacitySliderWidget[cath].value = tdata.opacity[cath]
      
    self.showCoilLabelCheckBox.checked = tdata.showCoilLabel

    if tdata.axisDirection[0] > 0.0:
      self.coordinateRPlusRadioButton.checked = 1
    else:
      self.coordinateRMinusRadioButton.checked = 1
      
    if tdata.axisDirection[1] > 0.0:
      self.coordinateAPlusRadioButton.checked = 1
    else:
      self.coordinateAMinusRadioButton.checked = 1

    if tdata.axisDirection[2] > 0.0:
      self.coordinateSPlusRadioButton.checked = 1
    else:
      self.coordinateSMinusRadioButton.checked = 1

      
#------------------------------------------------------------
#
# NeedleTrackingLogic
#
class NeedleTrackingLogic(ScriptedLoadableModuleLogic):

  def __init__(self, parent):
    ScriptedLoadableModuleLogic.__init__(self, parent)

    self.scene = slicer.mrmlScene
    self.scene.AddObserver(slicer.vtkMRMLScene.NodeRemovedEvent, self.onNodeRemovedEvent)

    self.widget = None

    self.eventTag = {}

    self.currentTrackingDataNodeID = ''
    self.TrackingData = {}


  def addNewTrackingData(self, tdnode):
    if not tdnode:
      return
    
    if tdnode.GetID() in self.TrackingData:
      print('TrackingData "%s" has already been registered.' % tdnode.GetID())
    else:
      td = TrackingData()
      self.TrackingData[tdnode.GetID()] = td
      
      self.setupFiducials(tdnode, 0)
      self.setupFiducials(tdnode, 1)

      
  def switchCurrentTrackingData(self, tdnode):
    if not tdnode:
      return

    if not (tdnode.GetID() in self.TrackingData):
      self.addNewTrackingData(tdnode)

    self.currentTrackingDataNodeID = tdnode.GetID()
    return self.TrackingData[tdnode.GetID()]
  

  def getCurrentTrackingData(self):
    return self.TrackingData[self.currentTrackingDataNodeID]
  

  def setWidget(self, widget):
    self.widget = widget


  def setTipLength(self, length, index):
    nodeID = self.currentTrackingDataNodeID
    if nodeID:
      td = self.TrackingData[nodeID]
      if td:
        td.tipLength[index] = length
        tnode = slicer.mrmlScene.GetNodeByID(nodeID)
        self.updateCatheter(tnode, index)


  def setCatheterDiameter(self, diameter, index):
    nodeID = self.currentTrackingDataNodeID
    if nodeID:
      td = self.TrackingData[nodeID]
      if td:
        td.radius[index] = diameter / 2.0
        tnode = slicer.mrmlScene.GetNodeByID(nodeID)
        self.updateCatheter(tnode, index)
    

  def setCatheterOpacity(self, opacity, index):
    nodeID = self.currentTrackingDataNodeID
    if nodeID:
      td = self.TrackingData[nodeID]
      if td:
        td.opacity[index] = opacity
        tnode = slicer.mrmlScene.GetNodeByID(nodeID)
        self.updateCatheter(tnode, index)

        
  def setShowCoilLabel(self, show):
    nodeID = self.currentTrackingDataNodeID
    if nodeID:
      td = self.TrackingData[nodeID]
      if td:
        td.showCoilLabel = show
        tnode = slicer.mrmlScene.GetNodeByID(nodeID)
        self.updateCatheter(tnode, 0)
        self.updateCatheter(tnode, 1)

        
  def isStringInteger(self, s):
    try:
        int(s)
        return True
    except ValueError:
        return False

  def setAxisDirections(self, rPositive, aPositive, sPositive):
    
    nodeID = self.currentTrackingDataNodeID
    if nodeID:
      td = self.TrackingData[nodeID]
      if td:
        if rPositive:
          td.axisDirection[0] = 1.0
        else:
          td.axisDirection[0] = -1.0
          
        if aPositive:
          td.axisDirection[1] = 1.0
        else:
          td.axisDirection[1] = -1.0
          
        if sPositive:
          td.axisDirection[2] = 1.0
        else:
          td.axisDirection[2] = -1.0

        tnode = slicer.mrmlScene.GetNodeByID(nodeID)
        self.updateCatheter(tnode, 0)
        self.updateCatheter(tnode, 1)
   
    
  def setupFiducials(self, tdnode, index):

    if not tdnode:
      return
    
    # Set up markups fiducial node, if specified in the connector node
    curveNodeID = tdnode.GetAttribute('NeedleTracking.CurveNode%d' % index)
    curveNode = None

    #cathName = 'Catheter_%d' % index
    
    if curveNodeID != None:
      curveNode = self.scene.GetNodeByID(curveNodeID)
    else:
      curveNode = self.scene.AddNewNodeByClass('vtkMRMLMarkupsCurveNode')
      ## TODO: Name?
      tdnode.SetAttribute('NeedleTracking.CurveNode%d' % index, curveNode.GetID())

    td = self.TrackingData[tdnode.GetID()]
    
    # Set up tip model node
    tipModelID = tdnode.GetAttribute('NeedleTracking.tipModel%d' % index)
    if tipModelID != None:
      td.tipModelNode[index] = self.scene.GetNodeByID(tipModelID)
    else:
      td.tipModelNode[index] = None

    tipTransformNodeID = tdnode.GetAttribute('NeedleTracking.tipTransform%d' % index)
    if tipTransformNodeID != None:
      td.tipTransformNode[index] = self.scene.GetNodeByID(tipTransformNodeID)
    else:
      td.tipTransformNode[index] = None


  def onIncomingNodeModifiedEvent(self, caller, event):

    parentID = caller.GetAttribute('NeedleTracking.parent')
    
    if parentID == '':
      return

    tdnode = slicer.mrmlScene.GetNodeByID(parentID)
    
    if tdnode and tdnode.GetClassName() == 'vtkMRMLIGTLTrackingDataBundleNode':
      self.updateCatheterNode(tdnode, 0)
      self.updateCatheterNode(tdnode, 1)

      
  def updateCatheterNode(self, tdnode, index):
    #print("updateCatheterNode(%s, %d) is called" % (tdnode.GetID(), index) )
    # node shoud be vtkMRMLIGTLTrackingDataBundleNode

    curveNodeID = tdnode.GetAttribute('NeedleTracking.CurveNode%d' % index)
    curveNode = None
    if curveNodeID != None:
      curveNode = self.scene.GetNodeByID(curveNodeID)

    if curveNode == None:
      curveNode = self.scene.AddNewNodeByClass('vtkMRMLMarkupsCurveNode')
      tdnode.SetAttribute('NeedleTracking.CurveNode%d' % index, curveNode.GetID())
    
    prevState = curveNode.StartModify()
    
    
    # Update coordinates in the fiducial node.
    nCoils = tdnode.GetNumberOfTransformNodes()

    td = self.TrackingData[tdnode.GetID()]
    
    if curveNode.GetNumberOfControlPoints() != nCoils:
      curveNode.RemoveAllControlPoints()
      for i in range(nCoils):
        p = vtk.vtkVector3d()
        p.SetX(0.0)
        p.SetY(0.0)
        p.SetZ(0.0)
        curveNode.AddControlPoint(p, "P_%d" % i)
        
    lastCoil = nCoils - 1

    for i in range(nCoils):
      tnode = tdnode.GetTransformNode(i)
      trans = tnode.GetTransformToParent()
      v = trans.GetPosition()
      curveNode.SetNthControlPointPosition(i, v[0] * td.axisDirection[0], v[1] * td.axisDirection[1], v[2] * td.axisDirection[2])

    curveNode.EndModify(prevState)
    
    self.updateCatheter(tdnode, index)

    
  def updateCatheter(self, tdnode, index):

    if tdnode == None:
      return
    
    curveNode = None
    curveNodeID = tdnode.GetAttribute('NeedleTracking.CurveNode%d' % index)
    if curveNodeID != None:
      curveNode = self.scene.GetNodeByID(curveNodeID)

    if curveNode == None:
      return

    td = self.TrackingData[tdnode.GetID()]

    curveDisplayNode = curveNode.GetDisplayNode()
    if curveDisplayNode:
      prevState = curveDisplayNode.StartModify()
      curveDisplayNode.SetSelectedColor(td.modelColor[index])
      curveDisplayNode.SetColor(td.modelColor[index])
      curveDisplayNode.SetOpacity(td.opacity[index])
      curveDisplayNode.SliceIntersectionVisibilityOn()
      curveDisplayNode.EndModify(prevState)
      # Show/hide labels for coils
      curveDisplayNode.SetPointLabelsVisibility(td.showCoilLabel);
      curveDisplayNode.SetUseGlyphScale(False)
      curveDisplayNode.SetGlyphSize(td.radius[index]*4.0)
      curveDisplayNode.SetLineThickness(0.5)  # Thickness is defined as a scale from the glyph size.
    
    # Add a extended tip
    # make sure that there is more than one points
    if curveNode.GetNumberOfControlPoints() < 2:
      return

    if td.tipPoly[index]==None:
      td.tipPoly[index] = vtk.vtkPolyData()
    
    if td.tipModelNode[index] == None:
      td.tipModelNode[index] = self.scene.AddNewNodeByClass('vtkMRMLModelNode')
      td.tipModelNode[index].SetName('Tip')
      tdnode.SetAttribute('NeedleTracking.tipModel%d' % index, td.tipModelNode[index].GetID())
        
    if td.tipTransformNode[index] == None:
      td.tipTransformNode[index] = self.scene.AddNewNodeByClass('vtkMRMLLinearTransformNode')
      td.tipTransformNode[index].SetName('TipTransform')
      tdnode.SetAttribute('NeedleTracking.tipTransform%d' % index, td.tipTransformNode[index].GetID())

    ## The 'curve end point matrix' (normal vectors + the curve end position)
    matrix = vtk.vtkMatrix4x4()
    
    ## Assuming that the tip is at index=0 
    n10 = [0.0, 0.0, 0.0]
    p0  = [0.0, 0.0, 0.0]
    cpi = curveNode.GetCurvePointIndexFromControlPointIndex(0)

    curveNode.GetNthControlPointPosition(0, p0)
    curveNode.GetCurvePointToWorldTransformAtPointIndex(cpi, matrix)
    n10[0] = matrix.GetElement(0, 2)
    n10[1] = matrix.GetElement(1, 2)
    n10[2] = matrix.GetElement(2, 2)

    # Tip location
    # The sign for the normal vector is '-' because the normal vector point toward points
    # with larger indecies.
    pe = numpy.array(p0) - numpy.array(n10) * td.tipLength[index]
  
    self.updateTipModelNode(td.tipModelNode[index], td.tipPoly[index], p0, pe, td.radius[index], td.modelColor[index], td.opacity[index])

    ## Update the 'catheter tip matrix' (normal vectors + the catheter tip position)
    ## Note that the catheter tip matrix is different from the curve end matrix
    matrix.SetElement(0, 3, pe[0])
    matrix.SetElement(1, 3, pe[1])
    matrix.SetElement(2, 3, pe[2])
    td.tipTransformNode[index].SetMatrixTransformToParent(matrix)
    
    #matrix = vtk.vtkMatrix4x4()
    #matrix.DeepCopy((t[0], s[0], n10[0], pe[0],
    #                 t[1], s[1], n10[1], pe[1],
    #                 t[2], s[2], n10[2], pe[2],
    #                 0, 0, 0, 1))

    
  def updateTipModelNode(self, tipModelNode, poly, p0, pe, radius, color, opacity):

    points = vtk.vtkPoints()
    cellArray = vtk.vtkCellArray()
    points.SetNumberOfPoints(2)
    cellArray.InsertNextCell(2)
    
    points.SetPoint(0, p0)
    cellArray.InsertCellPoint(0)
    points.SetPoint(1, pe)
    cellArray.InsertCellPoint(1)

    poly.Initialize()
    poly.SetPoints(points)
    poly.SetLines(cellArray)

    tubeFilter = vtk.vtkTubeFilter()
    tubeFilter.SetInputData(poly)
    tubeFilter.SetRadius(radius)
    tubeFilter.SetNumberOfSides(20)
    tubeFilter.CappingOn()
    tubeFilter.Update()

    # Sphere represents the locator tip
    sphere = vtk.vtkSphereSource()
    sphere.SetRadius(radius*2.0)
    sphere.SetCenter(pe)
    sphere.Update()

    apd = vtk.vtkAppendPolyData()

    if vtk.VTK_MAJOR_VERSION <= 5:
      apd.AddInput(sphere.GetOutput())
      apd.AddInput(tubeFilter.GetOutput())
    else:
      apd.AddInputConnection(sphere.GetOutputPort())
      apd.AddInputConnection(tubeFilter.GetOutputPort())
    apd.Update()
    
    tipModelNode.SetAndObservePolyData(apd.GetOutput())
    tipModelNode.Modified()

    tipDispID = tipModelNode.GetDisplayNodeID()
    if tipDispID == None:
      tipDispNode = self.scene.AddNewNodeByClass('vtkMRMLModelDisplayNode')
      tipDispNode.SetScene(self.scene)
      tipModelNode.SetAndObserveDisplayNodeID(tipDispNode.GetID());
      tipDispID = tipModelNode.GetDisplayNodeID()
      
    tipDispNode = self.scene.GetNodeByID(tipDispID)

    prevState = tipDispNode.StartModify()
    tipDispNode.SetColor(color)
    tipDispNode.SetOpacity(opacity)
    tipDispNode.SliceIntersectionVisibilityOn()
    tipDispNode.SetSliceDisplayModeToIntersection()
    tipDispNode.EndModify(prevState)
    

  def onNodeRemovedEvent(self, caller, event, obj=None):
    delkey = ''
    if obj == None:
      for k in self.eventTag:
        node = self.scene.GetNodeByID(k)
        if node == None:
          delkey = k
          break

    if delkey != '':
      del self.eventTag[delkey]

  def activateTracking(self):
    td = self.TrackingData[self.currentTrackingDataNodeID]
    tdnode = slicer.mrmlScene.GetNodeByID(self.currentTrackingDataNodeID)
    
    if tdnode:
      print("Observer added.")
      # Since TrackingDataBundle does not invoke ModifiedEvent, obtain the first child node
      if tdnode.GetNumberOfTransformNodes() > 0:
        childNode = tdnode.GetTransformNode(0)
        childNode.SetAttribute('NeedleTracking.parent', tdnode.GetID())
        td.eventTag = childNode.AddObserver(vtk.vtkCommand.ModifiedEvent, self.onIncomingNodeModifiedEvent)
        return True
      else:
        return False  # Could not add observer.

  
  def deactivateTracking(self):
    td = self.TrackingData[self.currentTrackingDataNodeID]
    tdnode = slicer.mrmlScene.GetNodeByID(self.currentTrackingDataNodeID)
    if tdnode:
      if tdnode.GetNumberOfTransformNodes() > 0 and td.eventTag != '':
        childNode = tdnode.GetTransformNode(0)
        childNode.RemoveObserver(td.eventTag)
        td.eventTag = ''
        return True
      else:
        return False

  def isTrackingActive(self):
    td = self.TrackingData[self.currentTrackingDataNodeID]
    return td.isActive()
    
      
