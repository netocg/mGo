#-----------------------------------------------------------------
#    SCRIPT            mGo_Maya.py
#
#    AUTHOR            Stuart Tozer
#                      stutozer@gmail.com
#
#	 CONTRIBUTOR	   Antonio Lisboa M. Neto
#					   netocg.fx@gmail.com
#
#    DATE:             September 2014 - September 2015
#
#    DESCRIPTION:      Auto Shading Network Creator For Use With Custom Mari OpenGL Shaders
#
#    VERSION:          3.0
#
#-----------------------------------------------------------------


import maya.cmds as cmds
from pymel.core import *
import math
import os
import glob
import pickle


def createTextureNode(name=None):
    """Creates a shading file node with the option asTexture as True,
    		then attempts to connect the global colour management node to it.
    
		Keyword Args:
			name (str): Name of new node.

		Returns:
			str. Path to Maya File node. 
	"""
	fileNodePath = cmds.shadingNode("file", asTexture=True, name=name or "fileNode")
	colorGlobals = cmds.ls(type="colorManagementGlobals")
	if colorGlobals:
		try:
			for sourceAttr, targetAttr in (
				("cmEnabled", "colorManagementEnabled"),
				("configFileEnabled", "colorManagementConfigFileEnabled"),
				("configFilePath", "colorManagementConfigFilePath"),
				("workingSpaceName", "workingSpace")
			):
				cmds.connectAttr(
					".".join((colorGlobals[0], sourceAttr)),
					".".join((fileNodePath, targetAttr)),
					force=True
				)
		except RuntimeError:
			print("Failed to connect file node (%s) to color management globals" % fileNodePath)
	else:
		print("Failed to enable file node color management: Could not find color management globals")
	
	return fileNodePath


def runConfig(sceneDescriptionFile, filePath):
	# <------------- delete previous shaders/textures and connections? ------------->
	def deleteShaderNodes(shaderType, curShaderStr):
		if shaderType == "LayeredShader":
			matName = nameSpace+"mGo_" + curShaderStr + "_Blend_mat"
		elif shaderType == "none":
			matName = nameSpace+"mGo_"+curShaderStr+"_Channels_Container"
		else:
			matName = nameSpace+"mGo_" + curShaderStr + "_mat"
		
		
		print(matName)
		try:
			#get downnodes
			downNodes=cmds.listHistory(matName)
			check=cmds.ls(downNodes, type='file')
			check+=cmds.ls(downNodes, type='gammaCorrect')
			check+=cmds.ls(downNodes, tex=True)
			# delete them
			try:
				cmds.delete(check)
				print("deleted old file, utility nodes")	
			except TypeError:
				pass
				
		except ValueError:
			print("Trying to delete old shader nodes.") 
			#print a msg in case the shader exists but the delete process failed.
			if cmds.objExists( matName ) == True:
				print("Could not find any node connected to the shader: '" +matName+ "' make sure the shader exists.")
			
		#try to delete any possible remain shader network left just one time for each obj.
		global shaderNetworkDel
		if shaderNetworkDel != True:
			shaderNetworkDel = True
			try:
				cmds.delete(nameSpace+str(geoName)+"_samplerInfo")
				cmds.delete(nameSpace+str(geoName)+"_samplerInfo_reverse")
			except:
				pass
			#delete displacement node and texture
			try:
				dispNode = nameSpace+"mGo_" + curShaderStr + "_dispNode"
				downNodes=cmds.listHistory(dispNode)
				check=cmds.ls(downNodes)
				cmds.delete(check)
			except:
				pass
		
		return
	# <------------- Finish delete previous shaders/textures and connections! ------------->
		
	#Create Nested Shader Network =============================================================================
	def layerInfo2Nodes(channel_input, fileNode):
		channel_input = channel_input.split(',')			
		
		# <--- Start of the creation of the Falloff Curve into the samplerInfo + ramp nodes shader network in Maya! --->
		if channel_input[0] == "Falloff Curve":
			# use the filneNode name as a prefix for the nodes in the shader network below.
			network_name = fileNode									
			print(str(channel_input[0]) + " identified")	
					
			if channel_input[1] != "hidden":
				# Create and connect the falloff and the reverse nodes. If they already exist, just pass their names as vars, this allows to have just one of those nodes for all the shader network, since their function doesn't change, this would avoid crowding and repeatable node doing the same thing!
				falloff = nameSpace+str(geoName)+"_samplerInfo"
				reverse = nameSpace+str(geoName)+"_samplerInfo_reverse"
				if cmds.objExists( nameSpace+str(geoName)+"_samplerInfo" ) != True:
					falloff = cmds.shadingNode("samplerInfo", asUtility=True, n = nameSpace+str(geoName)+"_samplerInfo" )
				if cmds.objExists( nameSpace+str(geoName)+"_samplerInfo_reverse" ) != True:	
					reverse = cmds.shadingNode("reverse", asUtility=True, n = nameSpace+str(geoName)+"_samplerInfo_reverse" )						
				try:	
					cmds.connectAttr('%s.facingRatio' %falloff, '%s.inputX' %reverse)
				except:
					pass
							
				# Create the Falloff_mask node as a layered texture so the artist could use mask to blend tha ramps with any texture that was below the Falloff Curve adjusment layer in Mari.
				Falloff_mask = network_name+"_Falloff_mask"
				if cmds.objExists( network_name+"_Falloff_mask" ) != True:
					Falloff_mask = cmds.shadingNode("layeredTexture", asTexture=True, n = network_name+"_Falloff_mask" )
				cmds.setAttr(Falloff_mask + ".alphaIsLuminance", 1)
				cmds.setAttr(Falloff_mask + ".inputs[0].blendMode", 4)
				cmds.setAttr(Falloff_mask + ".inputs[0].alpha", float(channel_input[5]) )	
					
				# Switch case for the different Operation Modes of the Falloff Curve in Mari. This will create specific ramps for each case.
				if channel_input[1] == "Luma Curve":						
					# Create the ramp for the Luma Curve
					lumaCurve = network_name+"_luma"
					if cmds.objExists( network_name+"_luma" ) != True:
						lumaCurve = cmds.shadingNode("ramp", asTexture=True, n = network_name+"_luma" )
						# Connect the reverse node to the ramp.
						cmds.connectAttr('%s.outputX' %reverse, '%s.vCoord' %lumaCurve)
						# Set the interpolation of the ramps to exponential down.
						cmds.setAttr(lumaCurve + ".interpolation", 4)
						# Connect the Ramp to the Falloff_mask node.						
						cmds.connectAttr('%s.outColor' %lumaCurve, '%s.inputs[0].color' %Falloff_mask)						
							
					# identify where the parameters for the ramp starts and where it ends!
					index_lumaEnd = channel_input.index(channel_input[-1])							
					layer_params1 = channel_input[7:index_lumaEnd]
					i = 0						
					# Start the loop to assign all the values for the green ramp.
					while i < len(layer_params1):					
						value = float(layer_params1[i+1])						
						cmds.setAttr(lumaCurve +".colorEntryList["+str(i)+"].color", value,value,value, type='double3')											
						value = float(layer_params1[i])
						cmds.setAttr(lumaCurve +".colorEntryList["+str(i)+"].position", value)							
						i += 2			
				else:
					redCurve = network_name+"_red"
					if cmds.objExists( network_name+"_red" ) != True:
						redCurve = cmds.shadingNode("ramp", asTexture=True, n = network_name+"_red" )							
						# Connect the reverse nodes to the ramps.							
						cmds.connectAttr('%s.outputX' %reverse, '%s.vCoord' %redCurve)
						# Set the interpolation of the ramps to exponential down.
						cmds.setAttr(redCurve + ".interpolation", 4)
						# Connect the Ramps to the Falloff_mask node.
						cmds.connectAttr('%s.outColorR' %redCurve, '%s.inputs[0].colorR' %Falloff_mask)								
					# identify where the parameters for the red ramp starts and where it ends!
					index_redEnd = channel_input.index("greenCurve")					
					layer_params1 = channel_input[7:index_redEnd]					
					i = 0
					# Start the loop to assign all the values for the red ramp.
					while i < len(layer_params1):				
						value = float(layer_params1[i+1])						
						cmds.setAttr(redCurve +".colorEntryList["+str(i)+"].color", value,0,0, type='double3')											
						value = float(layer_params1[i])
						cmds.setAttr(redCurve +".colorEntryList["+str(i)+"].position", value)											
						i += 2	
							
					greenCurve = network_name+"_green"
					if cmds.objExists( network_name+"_green" ) != True:
						greenCurve = cmds.shadingNode("ramp", asTexture=True, n = network_name+"_green" )
						# Connect the reverse nodes to the ramps.							
						cmds.connectAttr('%s.outputX' %reverse, '%s.vCoord' %greenCurve)
						# Set the interpolation of the ramps to exponential down.							
						cmds.setAttr(greenCurve + ".interpolation", 4)
						# Connect the Ramps to the Falloff_mask node.							
						cmds.connectAttr('%s.outColorG' %greenCurve, '%s.inputs[0].colorG' %Falloff_mask)	
					# identify where the parameters for the green ramp starts and where it ends!
					index_greenEnd = channel_input.index("blueCurve")					
					layer_params2 = channel_input[index_redEnd+1:index_greenEnd]					
					i = 0
					# Start the loop to assign all the values for the green ramp.
					while i < len(layer_params2):					
						value = float(layer_params2[i+1])						
						cmds.setAttr(greenCurve +".colorEntryList["+str(i)+"].color", 0,value,0, type='double3')											
						value = float(layer_params2[i])
						cmds.setAttr(greenCurve +".colorEntryList["+str(i)+"].position", value)							
						i += 2
								
					blueCurve = network_name+"_blue"
					# Create the ramps for Red, Blue, Green
					if cmds.objExists( network_name+"_blue" ) != True:
						blueCurve = cmds.shadingNode("ramp", asTexture=True, n = network_name+"_blue" )
						# Connect the reverse nodes to the ramps.
						cmds.connectAttr('%s.outputX' %reverse, '%s.vCoord' %blueCurve)
						# Set the interpolation of the ramps to exponential down.							
						cmds.setAttr(blueCurve + ".interpolation", 4)
						# Connect the Ramps to the Falloff_mask node.							
						cmds.connectAttr('%s.outColorB' %blueCurve, '%s.inputs[0].colorB' %Falloff_mask)							
					# identify where the parameters for the blue ramp starts and where it ends!
					index_blueEnd = channel_input.index(channel_input[-1])					
					layer_params3 = channel_input[index_greenEnd+1:index_blueEnd]					
					i = 0
					# Start the loop to assign all the values for the green ramp.
					while i < len(layer_params3):					
						value = float(layer_params3[i+1])						
						cmds.setAttr(blueCurve +".colorEntryList["+str(i)+"].color", 0,0,value, type='double3')											
						value = float(layer_params3[i])
						cmds.setAttr(blueCurve +".colorEntryList["+str(i)+"].position", value)							
						i += 2																	
				
				
				Falloff_blend_layers = network_name+"_Falloff_blend_layers"
				# Pass the blend amount value to the layered texture node.
				if cmds.objExists( network_name+"_Falloff_blend_layers" ) != True:
					Falloff_blend_layers = cmds.shadingNode("layeredTexture", asTexture=True, n = network_name+"_Falloff_blend_layers" )
					
					# If a Global Gamma Ctrl Node already exist just pass it's name as var.
					Global_gammaCtrlNode = nameSpace+"Global_GammaCtrl"
					if cmds.objExists( Global_gammaCtrlNode ) != True:	
						Global_gammaCtrlNode = cmds.shadingNode("multiplyDivide", asUtility=True, n = Global_gammaCtrlNode )
						cmds.setAttr(Global_gammaCtrlNode + '.input1X', 0.454)
						cmds.setAttr(Global_gammaCtrlNode + '.input1Y', 0.454)
						cmds.setAttr(Global_gammaCtrlNode + '.input1Z', 0.454)
					
					# If a gammaNode with this name already exist just pass it's name as var.
					_gammaNode = network_name+"_Falloff_blend_layers_gamma"
					if cmds.objExists( _gammaNode ) != True:	
						_gammaNode = cmds.shadingNode("gammaCorrect", asUtility=True, n = _gammaNode )
						cmds.connectAttr('%s.output' %Global_gammaCtrlNode, '%s.gamma' %_gammaNode)					
						
					#connect the _fileNode to the _gammaNode.
					cmds.connectAttr('%s.outColor' %Falloff_mask, '%s.value' %_gammaNode)
					cmds.connectAttr('%s.outValue' %_gammaNode, '%s.inputs[0].color' %Falloff_blend_layers)						
					
					#try to connected the fileNode or gammaNode.
					try:
						cmds.connectAttr('%s.outColor' %fileNode, '%s.inputs[1].color' %Falloff_blend_layers)
					except:
						cmds.connectAttr('%s.outValue' %fileNode, '%s.inputs[1].color' %Falloff_blend_layers)
				cmds.setAttr(Falloff_blend_layers + ".alphaIsLuminance", 1)						
				cmds.setAttr(Falloff_blend_layers + ".inputs[1].blendMode", 0)
				if channel_input[3] == "Normal":
					cmds.setAttr(Falloff_blend_layers + ".inputs[0].blendMode", 1)
				elif channel_input[3] == "Add":
					cmds.setAttr(Falloff_blend_layers + ".inputs[0].blendMode", 4)					
				elif channel_input[3] == "Darken":
					cmds.setAttr(Falloff_blend_layers + ".inputs[0].blendMode", 9)
				elif channel_input[3] == "Difference":
					cmds.setAttr(Falloff_blend_layers + ".inputs[0].blendMode", 7)
				elif channel_input[3] == "Lighten":
					cmds.setAttr(Falloff_blend_layers + ".inputs[0].blendMode", 8)					
				elif channel_input[3] == "Multiply":
					cmds.setAttr(Falloff_blend_layers + ".inputs[0].blendMode", 6)						
				else:
					print("Color, Hue, Inverse difference, Luminance, and Saturation Blending modes in Mari does not translate well to Maya. We are hiding the " +str(Falloff_blend_layers)+ ".inputs[0]")
					cmds.setAttr(Falloff_blend_layers + ".inputs[0].isVisible", 0)
					
				
				if channel_input[-1] != "none":
					print("Importing a Falloff Mask")							
					_channelDepth = channel_input[-1].rsplit("#", 1)[1]
					_channelName = channel_input[-1].rsplit("#", 1)[0]							
					
					if _channelDepth == "8":
						_channel_path = str(exportDir+geoName+'_'+_channelName+setUdim+"."+ext8)
					elif _channelDepth == "16" or _channelDepth == "32":
						_channel_path = str(exportDir+geoName+'_'+_channelName+setUdim+"."+ext32)
						
					_fileNode = nameSpace+str(geoName)+"_"+_channelName
					if cmds.objExists( nameSpace+str(geoName)+"_"+_channelName ) != True:
						_fileNode = createTextureNode(name=nameSpace+str(geoName)+"_"+_channelName)
						cmds.connectAttr('%s.outAlpha' %_fileNode, '%s.inputs[0].alpha' %Falloff_blend_layers)
					cmds.setAttr( '%s.fileTextureName' %_fileNode, _channel_path, type = "string")								
					
				print(str(channel_input[0]) + " created in Maya as a shading network!")				
				return Falloff_blend_layers;
			else:
				return "none";
	# <--- End of the creation of the Falloff Curve into the samplerInfo + ramp nodes shader network in Maya! --->
		
	#Create the file node texture and return it to be assigned to the shader.
	def setTextureChannels(_shaderConfig_data):
		# separate the data and get what is after @ charecter, which is data responsible for recreate shader network from Mari. 
		channel_input = _shaderConfig_data.rsplit("@", 1)[1]
		# separate the data related to channel name and bit depth of the texture file.
		_shaderConfig_data = _shaderConfig_data.rsplit("@", 1)[0]
				
		channelDepth = _shaderConfig_data.rsplit("#", 1)[1]				
		channelName = _shaderConfig_data.rsplit("#", 1)[0]
		
		if channelDepth == "8":
			channel_path = str(exportDir+geoName+'_'+channelName+setUdim+"."+ext8)			
		else:
			channel_path = str(exportDir+geoName+'_'+channelName+setUdim+"."+ext32)
		
			
		# If a fileNode with this name already exist just pass it's name as var.
		_fileNode = nameSpace+str(geoName)+"_"+channelName
		if cmds.objExists( nameSpace+str(geoName)+"_"+channelName ) != True:	
			_fileNode = createTextureNode(name=nameSpace + str(geoName) + "_" + channelName)
			
		cmds.setAttr( '%s.fileTextureName' %_fileNode, channel_path, type = "string")
		
		#filtering settings
		cmds.setAttr(_fileNode + '.alphaIsLuminance', 1)			
		if filtering == "Off":			
			cmds.setAttr(_fileNode + '.filterType', 0)
		elif filtering == "Mipmap":
			cmds.setAttr(_fileNode + '.filterType', 1)
		
		#Set UV Tiling Mode to MARI UDIM (Maya 2015+)
		try:
			if udim == "True":
				cmds.setAttr(_fileNode + '.uvTilingMode', 3)
				mel.eval("generateUvTilePreview %s" % _fileNode)
		except:
			pass

		#Set File Color Space to Raw (Maya 2015+). Considering it was already gamma corrected in Mari.
		try:
			if channelDepth == "8":
				cmds.setAttr(_fileNode + '.colorSpace', "sRGB", type='string')
			else:
				cmds.setAttr(_fileNode + '.colorSpace', "Raw", type='string')							
		except:
			if channelDepth == "8":
				#You have to manage the 8bit gamma for the Arnold and Vray Renderers.
				if (shaderType != "Redshift Architectural"):
					# If a Global Gamma Ctrl Node already exist just pass it's name as var.
					Global_gammaCtrlNode = nameSpace+"Global_GammaCtrl"
					if cmds.objExists( Global_gammaCtrlNode ) != True:	
						Global_gammaCtrlNode = cmds.shadingNode("multiplyDivide", asUtility=True, n = nameSpace+Global_gammaCtrlNode )
						cmds.setAttr(Global_gammaCtrlNode + '.input1X', 0.454)
						cmds.setAttr(Global_gammaCtrlNode + '.input1Y', 0.454)
						cmds.setAttr(Global_gammaCtrlNode + '.input1Z', 0.454)
					
					# If a gammaNode with this name already exist just pass it's name as var.
					_gammaNode = nameSpace+str(geoName)+"_"+channelName+"_gamma"
					if cmds.objExists( _gammaNode ) != True:	
						_gammaNode = cmds.shadingNode("gammaCorrect", asUtility=True, n = nameSpace+_gammaNode )
						cmds.connectAttr('%s.output' %Global_gammaCtrlNode, '%s.gamma' %_gammaNode)					
						#connect the _fileNode to the _gammaNode.
						cmds.connectAttr('%s.outColor' %_fileNode, '%s.value' %_gammaNode)
					
					_fileNode = _gammaNode
			
		# check if there is data for create a shader network. If there is pass the last node name of the network created to the _fileNode var that will be connected to the final shader. 
		if channel_input != "None":					
			shaderNodes = layerInfo2Nodes(channel_input, _fileNode)
			if shaderNodes != "none":
				_fileNode = shaderNodes
					
		return _fileNode;
	# <--- End of the set the textures file nodes in Maya! --->
	
	#Create the Gamma node for the Shader Color Swatches 
	#return it to be assigned to the shader. 
	#Mari manage this automatically coverting the Shader's Color Swatches values to linear.
	def setGammaNode(_shaderConfig_data, shader, channelName):
		# If a Global Gamma Ctrl Node already exist just pass it's name as var.
		Global_gammaCtrlNode = nameSpace+"Global_GammaCtrl"
		if cmds.objExists( Global_gammaCtrlNode ) != True:	
			Global_gammaCtrlNode = cmds.shadingNode("multiplyDivide", asUtility=True, n = nameSpace+Global_gammaCtrlNode )
			cmds.setAttr(Global_gammaCtrlNode + '.input1X', 0.454)
			cmds.setAttr(Global_gammaCtrlNode + '.input1Y', 0.454)
			cmds.setAttr(Global_gammaCtrlNode + '.input1Z', 0.454)
		
		# If a gammaNode with this name already exist just pass it's name as var.
		_gammaNode = nameSpace+str(geoName)+"_"+shader+"_"+channelName
		if cmds.objExists( _gammaNode ) != True:	
			_gammaNode = cmds.shadingNode("gammaCorrect", asUtility=True, n = _gammaNode )
			cmds.connectAttr('%s.output' %Global_gammaCtrlNode, '%s.gamma' %_gammaNode)
				
		_shaderConfig_data = _shaderConfig_data.translate(None, '[]')
		_shaderConfig_data = _shaderConfig_data.split(',', 2)
		val1=float(_shaderConfig_data[0])
		val2=float(_shaderConfig_data[1])
		val3=float(_shaderConfig_data[2])		
		cmds.setAttr(_gammaNode + '.value', val1, val2, val3, type='double3')
					
		return _gammaNode
	# <--- End of the set the textures file nodes in Maya! --->
	
	print("------------- running -------------")
	
	update=[]
	
	f = open(sceneDescriptionFile, 'r')
	config = pickle.load(f)
	f.close()
	
	# Scene Description Config
	shaderType = config[0]
	geoName = config[1]
	objPath = config[2]
	exportDir = config[3]
	exportObj = config[4]
	ext8 = config[5]
	ext32 = config[6]
	udim = config[7]
	filtering = config[8]
	exportAttri = config[9]
	exportChannel = config[10]
	curShaderStr = config[11]
	exportCam = config[12]
	cam_data = config[13]
	exportLights = config[14]
	envLight_data = config[15]
	light_data1 = config[16]
	light_data2 = config[17]
	light_data3 = config[18]
	light_data4 = config[19]
	extMipmap = config[20]
	exportSubfolder = config[21]
	nameSpace = config[22]

	print("----- Scene Description data -----")
	number = 0
	for all in config:
		print(str(number) + " " + all)
		number = number + 1
	print("----------------------------------")
		
	shaderIndex = 0
	layeredShader = "none"
	layeredShaderStr = curShaderStr
	#Remove any mGo_ prefix from shaders name, so it will not be double.
	curShaderStr = curShaderStr.lstrip("mGo_")
	# Split the data from shaderType that is in the Scene Description.
	try:
		layeredShader = shaderType.rsplit("@",1)[1]
		shaderType = shaderType.rsplit("@",1)[0]
		shaderIndex = int(shaderType.rsplit("#",1)[1]) -1 #to get index=0 for shaders inside of the layeredShader...
		shaderType = shaderType.rsplit("#",1)[0]
		print("Found:'" +str(layeredShader)+ "' with #" +str(shaderIndex+1)+ " " +str(shaderType)+ " shaders")
	except:
		pass
	
	# Load the plugins and set render globals
	if shaderType == "Ai Standard":
		#load Arnold plug-in?
		if not cmds.pluginInfo('mtoa', q=True, l=True):
			cmds.loadPlugin('mtoa')
		# change render drop down to Arnold
		if cmds.getAttr("defaultRenderGlobals.ren") != 'arnold':
			cmds.setAttr('defaultRenderGlobals.ren', 'arnold', type='string')
		cmds.callbacks(executeCallbacks=True, hook='updateMayaRenderingPreferences')
		print("Arnold import begun")

	elif shaderType == "VRay Mtl":
		#Load Vray plug-in?
		if not cmds.pluginInfo('vrayformaya', q=True, l=True):
			cmds.loadPlugin('vrayformaya')
		# change render drop down to vray
		if cmds.getAttr("defaultRenderGlobals.ren") != 'vray':
			cmds.setAttr('defaultRenderGlobals.ren', 'vray', type='string')
			
		print("V-Ray import begun")
				
	elif shaderType == "Redshift Architectural":
		#Load Redshift?
		if not cmds.pluginInfo('redshift4maya', q=True, l=True):
			cmds.loadPlugin('redshift4maya')
		# change render drop down to redshift
		if cmds.getAttr("defaultRenderGlobals.ren") != 'redshift':
			cmds.setAttr('defaultRenderGlobals.ren', 'redshift', type='string')

		print("Redshift import begun")
	
	#import obj?
	if exportObj == "True":
		print("obj export is true")
		getT=cmds.ls(tr=True)
		getObjB=[]

		for x in getT:
			if geoName in x:
				getObjB.append(x)
		try:
			getObjB = getObjB[-1]
			print("Object is already in the scene")
			print(getObjB)
		except IndexError:
			print("importing obj")
			try:
				obj_extension = objPath.split(".")
				file_name = obj_extension[0].split("/")[-1]
				if(obj_extension[-1] == "obj"):
					#Avoid namespace issues
					getObjA = cmds.file(objPath, i=True, f=True, rnn = True, namespace=file_name+"_obj", options='mo=0')
					getObjA = cmds.rename(file_name+"_obj:polySurface1", geoName)
				else:
					getObjA = cmds.file(objPath, i=True, f=True, options='mo=0')
					
				print("Object imported")
				cmds.inViewMessage( amg='Object imported', pos='botCenter', fade=True, fadeOutTime=500)
			except:
				print("Failed to imported the Object! (it has most likely been moved from the original Mari Import location)") 
				print("Mari Geo path: " + objPath)

	#check if incoming namespace exists in the current maya project. Otherwise clean it just for safety reasons.
	if cmds.namespace(exists=nameSpace) != True:
		nameSpace=""
	else:
		#if does exists add the ":" character so it can concatenate with the strings correctly during the process of test/matching names with mGo here in maya. 
		nameSpace = nameSpace +":"
		
		
	#import Camera?	
	if exportCam == "True":
		print("camera export is true")
		cam_data = cam_data.translate(None, '()')
		cam_data = cam_data.split(',')
		if cam_data[0] != "none":
			# Check if the camera exists, if not create one.
			if cmds.objExists('MARI_Cam_group') != True:
				# Create the camera and set to overscan with display resolution gate enabled if the group node doesn't exists.	
				cmds.camera(displayResolution=True, filmFit="overscan")
				cmds.rename(cam_data[0])
				cmds.setAttr(".renderable", 1)
				# Set the camera to be a group with aim and cameraShape.
				mel.eval('cameraMakeNode 2 ""')
				# Set the overscan.
				cmds.setAttr("MARI_CamShape.overscan", 1.3, float)
					
			# Set the Angle of View.
			mari_cam_angleView = math.radians(float(cam_data[1]))
			mari_cam_angleView = 1*(0.5 * 1) / (0.03937* math.tan(mari_cam_angleView/2) )
			"""
			mari_cam_angleView = 0.75188*(0.5 * 0.980) / (0.03937* math.tan(mari_cam_angleView/2) )	# the 0.75188 is a conversion factor to match the leans in a 35mm Full aperture Film Gate. 0.03937 is to convert from mm to inchs.
			cmds.setAttr("MARI_CamShape.focalLength", mari_cam_angleView, float)			
			# 35mm Full Aperture - Film Gate settings.
			cmds.setAttr("MARI_CamShape.horizontalFilmAperture", 0.980, float)
			cmds.setAttr("MARI_CamShape.verticalFilmAperture", 0.735, float)				
			cmds.setAttr("MARI_CamShape.focalLength", mari_cam_angleView, float)
			"""
			cmds.setAttr("MARI_CamShape.horizontalFilmAperture", 1.0, float)
			cmds.setAttr("MARI_CamShape.verticalFilmAperture", float(cam_data[11]), float)
			cmds.setAttr("MARI_CamShape.focalLength", mari_cam_angleView, float)
			# Set the camera translation.
			cmds.setAttr("MARI_Cam.tx", float(cam_data[2]), float)
			cmds.setAttr("MARI_Cam.ty", float(cam_data[3]), float)
			cmds.setAttr("MARI_Cam.tz", float(cam_data[4]), float)	
			# Set the camera aim.
			cmds.setAttr("MARI_Cam_aim.tx", float(cam_data[5]), float)
			cmds.setAttr("MARI_Cam_aim.ty", float(cam_data[6]), float)
			cmds.setAttr("MARI_Cam_aim.tz", float(cam_data[7]), float)
			# Set the camera world up vector.			
			cmds.setAttr("MARI_Cam_group.worldUpVectorX", float(cam_data[8]), float)
			cmds.setAttr("MARI_Cam_group.worldUpVectorY", float(cam_data[9]), float)
			cmds.setAttr("MARI_Cam_group.worldUpVectorZ", float(cam_data[10]), float)
			# Set viewport to be looking though the new camera.				
			cmds.lookThru(cam_data[0])
			print("Camera imported")
			#message complete			
			cmds.inViewMessage( amg='Camera imported', pos='botCenter', fade=True, fadeOutTime=500)
		else:
			print("Failed in create the Mari's Camera. Please select a perspective camera in Mari!")


	#import Lights?			
	if 	exportLights == "True":
		print("Lights export is true")		
		# Starts the organization of the light datas variables and put them into a list.
		envLight_data = envLight_data.translate(None, '[]').translate(None, '()')
		envLight_data = envLight_data.split(',')
		light_data1 = light_data1.translate(None, '[]').translate(None, '()')
		light_data1 = light_data1.split(',')		
		light_data2 = light_data2.translate(None, '[]').translate(None, '()')
		light_data2 = light_data2.split(',')		
		light_data3 = light_data3.translate(None, '[]').translate(None, '()')
		light_data3 = light_data3.split(',')
		light_data4 = light_data4.translate(None, '[]').translate(None, '()')
		light_data4 = light_data4.split(',')
		light_list = [light_data1, light_data2, light_data3, light_data4]		
		
		# Create the light group if at least one of the lights are turned "ON" in Mari, else, delete if there is any group with lights in Maya!
		if (light_data1[-1] != "none") or (light_data2[-1] != "none") or (light_data3[-1] != "none") or (light_data4[-1] != "none"):
			# Create or Pass the light_group MARI_Light_Set name/group node
			if cmds.objExists('MARI_Light_Set'):
				light_group = "MARI_Light_Set"
			else:
				light_group = cmds.group(em=True, n='MARI_Light_Set')
				# Create an attribute to control the Lights Intensity of all lights created.
				cmds.addAttr(light_group, longName='Global_Light_Intensity_Multiplier', shortName='lightIntensity_Mult', attributeType='float', defaultValue=1.0, keyable=True)
				# Create an attribute to control the Lights scale of all lights created.
				cmds.addAttr(light_group, longName='Global_Light_Scale_Multiplier', shortName='lightScale_Mult', attributeType='float', defaultValue=1.0, keyable=True)	
		else:
			if cmds.objExists('MARI_Light_Set'):
				cmds.delete("MARI_Light_Set")
		
		# Compensates the light intensity based on shader falloff and decay attributes of each shader.
		def light_intensity_adjust(light_params):
			intensity_adjusted = float(light_params[6])			
			if shaderType == "Ai Standard":
				if light_params[11] == "Constant":
					intensity_adjusted = intensity_adjusted*200				
				else:
					intensity_adjusted = intensity_adjusted*4/(float(light_params[12])*float(light_params[12]))					
			elif shaderType == "VRay Mtl":
				if light_params[11] == "Linear":
					intensity_adjusted = intensity_adjusted *200
				elif light_params[11] == "Inverse":
					intensity_adjusted = intensity_adjusted*3/(float(light_params[12]))
				else:
					intensity_adjusted = intensity_adjusted*4/(float(light_params[12])*float(light_params[12]))					
			elif shaderType == "Redshift Architectural":					
				if light_params[11] == "None":
					intensity_adjusted = intensity_adjusted *100
				elif light_params[11] == "Linear":
					intensity_adjusted = intensity_adjusted*450/(float(light_params[12]))
				else:
					intensity_adjusted = intensity_adjusted*500/(float(light_params[12])*float(light_params[12]))					
			return intensity_adjusted;
		
		# Base function to set light position and scale.	
		def light_shape_attr(light, light_params, light_group, light_update):
			cmds.setAttr(light + '.translateX', float(light_params[7]), float)
			cmds.setAttr(light + '.translateY', float(light_params[8]), float)
			cmds.setAttr(light + '.translateZ', float(light_params[9]), float)
			
			# If the light is not been updated but instead it's in the creation process, then add the attributes and create the expression.
			if light_update == "False":
				# Create an attribute to control each Lights Intensity individually.
				cmds.addAttr(light_group, longName=str(light)+'_Intensity_Multiplier', shortName=str(light)+'_Intensity_Mult', attributeType='float', defaultValue=1.0, keyable=True)
				# Create an attribute to control each Lights scale individually.
				cmds.addAttr(light_group, longName=str(light)+'_Scale_Multiplier', shortName=str(light)+'_Scale_Mult', attributeType='float', defaultValue=1.0, keyable=True)
					
				# Create an expression to control the Lights scale using a Global Attribute in the group node  as well individual controllers for each light.
				cmds.expression(name="exp_"+str(light)+"_scale", s=str(light)+'.scaleX = ' + str(light_params[10]) + ' * '  + str(light_group) + '.Global_Light_Scale_Multiplier' + ' * ' + str(light_group)+'.'+str(light)+'_Scale_Multiplier;\n'+str(light)+'.scaleY = ' + str(light_params[10]) + '*' + str(light_group) + '.Global_Light_Scale_Multiplier' + ' * '  + str(light_group)+'.'+str(light)+'_Scale_Multiplier;\n'+str(light)+'.scaleZ = ' + str(light_params[10]) + ' * ' + str(light_group) + '.Global_Light_Scale_Multiplier' + '*' + str(light_group)+'.'+str(light)+'_Scale_Multiplier;', o=light, ae=1, uc='all')
			
			return
						
		# ============= Create Arnold Lights ===============================================================================================================================
		if shaderType == "Ai Standard":
			# <-----------Starts the process to create Arnold Sky and Sky Dome Lights----------->
			if envLight_data[-1] != "hidden":				
				# Create the file node and assign the texture path for the HDR
				if cmds.objExists('MARI_HDR_envLight') != True:
					fileNode_HDRimage = createTextureNode(name="MARI_HDR_envLight")
				cmds.setAttr( '%s.fileTextureName' %'MARI_HDR_envLight', envLight_data[1], type = "string")
				cmds.setAttr('MARI_HDR_envLight.filterType', 0)
								
				#create the aiSkyDomeLight node
				if cmds.objExists('MARI_aiSkyDomeLight') != True:	
					aiSkyDomeLight = cmds.shadingNode("aiSkyDomeLight",asLight=True, n="MARI_aiSkyDomeLightShape")					
					cmds.connectAttr('%s.outColor' %'MARI_HDR_envLight', '%s.color' %'MARI_aiSkyDomeLightShape')			
				cmds.setAttr('MARI_aiSkyDomeLightShape.intensity', float(envLight_data[2]), float)
				cmds.setAttr('MARI_aiSkyDomeLightShape.resolution', float(envLight_data[4]), float)			
				cmds.setAttr('MARI_aiSkyDomeLight.rotateY', float(envLight_data[3])-90, float)
				
				# There is no HDR path in Mari, so Environment lights is turned off!
				if envLight_data[1] != " ":
					try:
						cmds.connectAttr('MARI_aiSkyDomeLight.instObjGroups[0]', 'defaultLightSet.dagSetMembers[0]')
					except:
						pass
				else:	
					cmds.disconnectAttr('MARI_aiSkyDomeLight.instObjGroups[0]', 'defaultLightSet.dagSetMembers[0]')
					print("There is no HDR assigned in Mari, so the Environment light will be disabled in the Maya Scene")

				# Create the aiSky node
				if cmds.objExists('MARI_aiSky') != True:	
					aiSky = cmds.shadingNode("aiSky",asLight=True, n="MARI_aiSkyShape")
					cmds.connectAttr('%s.outColor' %'MARI_HDR_envLight', '%s.color' %'MARI_aiSkyShape')
					# Maya takes some time to refresh the render UI, so it may not be possible to connect the aiSky to the background in the render settings.							
					if cmds.objExists('defaultArnoldRenderOptions') !=True:					
						cmds.evalDeferred("cmds.connectAttr('%s.message' %'MARI_aiSkyShape', '%s.background' %'defaultArnoldRenderOptions')", lp=True)
					else:
						cmds.connectAttr('%s.message' %'MARI_aiSkyShape', '%s.background' %'defaultArnoldRenderOptions')
				cmds.setAttr('MARI_aiSkyShape.intensity', float(envLight_data[2]), float)
				cmds.setAttr('MARI_aiSkyShape.castsShadows', 0)
				cmds.setAttr('MARI_aiSkyShape.primaryVisibility', 1)
				cmds.setAttr('MARI_aiSkyShape.aiVisibleInDiffuse', 0)
				cmds.setAttr('MARI_aiSkyShape.aiVisibleInGlossy', 0)
				cmds.setAttr('MARI_aiSkyShape.visibleInReflections', 1)
				cmds.setAttr('MARI_aiSkyShape.visibleInRefractions', 1)			
				cmds.setAttr('MARI_aiSky.rotateY', float(envLight_data[3])-90, float)
				
				print("Arnold Dome Light and Sky imported.")	
			else:
				# In case there is no env light data, check if the Mari aiSky, aiSkyDomeLight and the File node with the HDR exists, if so delete them!
				if cmds.objExists('MARI_aiSkyDomeLight'):
					cmds.delete('MARI_aiSkyDomeLight')
				if cmds.objExists('MARI_aiSky'):
					cmds.delete('MARI_aiSky')				
				if cmds.objExists('MARI_HDR_envLight'):
					cmds.delete('MARI_HDR_envLight')
				print("Environment Light in Mari is turned off.")	
			# <-----------Finished the process of creating the Arnold Sky and Sky Dome Lights----------->
			
			# <-----------Start the process to create Arnold Light Sources----------->			
			
			# Create the light group if at least one of the lights are turned "ON" in Mari, else, delete if there is any group with lights in Maya!
			if (light_data1[-1] != "none") or (light_data2[-1] != "none") or (light_data3[-1] != "none") or (light_data4[-1] != "none"):
								
				# Starts to loop and check if there is data inside the list.				
				for light_params in light_list:	
					# Call a function to compensates the light intensity based on the shader falloff and decay attributes.
					intensity = light_intensity_adjust(light_params);					
					if light_params[1] == "PointLight":
						# Create the Lights and their expressions or keep the variable with their light name on it.
						light = "ARND_Light_" + str(light_params[2])
						light_update = "False"
						if cmds.objExists( light ):						
							light_update = "True"
							# Call a function that will set the light attributes for position and scale.							
							light_shape_attr(light, light_params, light_group, light_update)
							# Update Light Intesity Expression
							cmds.expression('exp_'+str(light)+'_intensity', edit=True, s=str(light)+'.intensity = ' + str(intensity) + ' * '  + str(light_group)+'.Global_Light_Intensity_Multiplier' + ' *' + str(light_group)+'.'+str(light)+'_Intensity_Multiplier', o=light, ae=1, uc='all')
							# Update Light Radius Expression
							cmds.expression('exp_'+str(light)+'_Radius', edit=True, s=str(light)+'.aiRadius = ' + str(light_params[10]) + ' * '  + str(light_group)+'.Global_Light_Scale_Multiplier' + ' *' + str(light_group)+'.'+str(light)+'_Scale_Multiplier', o=light, ae=1, uc='all')						
						else:
							# Create Lights that could be spherical so it could match better the way a point light would illuminates a scene(all directions).							
							light = cmds.shadingNode("pointLight", asLight=True, n="ARND_Light_" + str(light_params[2]) + "Shape")
							# Call a function that will set the light attributes for position and scale.
							light_shape_attr(light, light_params, light_group, light_update)
							# Create an expression to control the Lights Intensity using a Global Attribute in the group node.
							cmds.expression(name="exp_"+str(light)+"_intensity", s=str(light)+'.intensity = ' + str(intensity) + ' * '  + str(light_group)+'.Global_Light_Intensity_Multiplier' + ' *' + str(light_group)+'.'+str(light)+'_Intensity_Multiplier', o=light, ae=1, uc='all')
							# Create an expression to control the Lights scale using a Global Attribute in the group node as well individual controllers for each light.
							cmds.expression(name="exp_"+str(light)+"_Radius", s=str(light)+'.aiRadius = ' + str(light_params[10]) + ' * '  + str(light_group)+'.Global_Light_Scale_Multiplier' + ' *' + str(light_group)+'.'+str(light)+'_Scale_Multiplier', o=light, ae=1, uc='all')						
							cmds.parent(light, light_group)
						
						cmds.setAttr(light + '.color', float(light_params[3]),float(light_params[4]),float(light_params[5]), type='double3')						
																							
						cmds.setAttr(light + '.aiNormalize', 0)										
						# Light is turned "OFF" in Mari!
						if light_params[-1] == "hidden":
							cmds.setAttr(light + '.emitDiffuse', 0)
							cmds.setAttr(light + '.emitSpecular', 0)
						else:
							cmds.setAttr(light + '.emitDiffuse', 1)
							cmds.setAttr(light + '.emitSpecular', 1)
					else:
						print("Unknown Light Type!")				
				
				cmds.select(light_group)	
				print("Imported Arnold Light Sources")
			# <-----------Finished the process of creating Arnold Light Sources----------->
			
			#message complete
			cmds.inViewMessage( amg='<hl>Arnold</hl> Lights Transfer Completed', pos='midCenter', fade=True )
		
		# ======== Create VRay Lights ===============================================================================================================================
		elif shaderType == "VRay Mtl":
			# <-----------Starts the process to create the VRay Light Dome----------->
			if envLight_data[-1] != "hidden":
				# Create the file node and assign the texture path for the HDR
				if cmds.objExists('MARI_HDR_envLight') != True:					
					createTextureNode(name="MARI_HDR_envLight")
				cmds.setAttr( '%s.fileTextureName' %'MARI_HDR_envLight', envLight_data[1], type = "string")
				cmds.setAttr('MARI_HDR_envLight.filterType', 0)
				
				# Create the VRayPlaceEnvTex that controls the coordinates of the file node texture of the HDR
				if cmds.objExists('MARI_VRayPlaceEnvTex') != True:					
					cmds.shadingNode("VRayPlaceEnvTex",asUtility=True, n ="MARI_VRayPlaceEnvTex" )
					cmds.connectAttr('%s.outUV' %'MARI_VRayPlaceEnvTex', '%s.uvCoord' %'MARI_HDR_envLight')
				cmds.setAttr('MARI_VRayPlaceEnvTex.mappingType', 2)	
				cmds.setAttr('MARI_VRayPlaceEnvTex.horRotation', 360-float(envLight_data[3]), float)	
				
				# Create the VrayLightDome node 
				if cmds.objExists('MARI_VRayLightDome') != True:
					cmds.shadingNode("VRayLightDomeShape",asLight=True, n="MARI_VRayLightDomeShape")					
					cmds.connectAttr('%s.outColor' %'MARI_HDR_envLight', '%s.domeTex' %'MARI_VRayLightDomeShape')			
				cmds.setAttr('MARI_VRayLightDomeShape.intensityMult', float(envLight_data[2]), float)
				cmds.setAttr('MARI_VRayLightDomeShape.domeSpherical', 1)
				cmds.setAttr('MARI_VRayLightDomeShape.useDomeTex', 1)
				cmds.setAttr('MARI_VRayLightDomeShape.texResolution', float(envLight_data[4]), float)
				
				# There is no HDR path in Mari, so Environment lights is turned off!
				if envLight_data[1] != " ":
					cmds.setAttr('%s.enabled' %'MARI_VRayLightDome', 1)
				else:
					cmds.setAttr('%s.enabled' %'MARI_VRayLightDome', 0)
					print("There is no HDR assigned in Mari, so the Environment light will be disabled in the Maya Scene")
				
				print("VRay Dome Light imported.")	
			else:
				# In case there is no env light data, check if the Mari VraytDomeLight and their dependencies exists, if so delete them!
				if cmds.objExists('MARI_VRayLightDome'):
					cmds.delete('MARI_VRayLightDome')
				if cmds.objExists('MARI_VRayPlaceEnvTex'):
					cmds.delete('MARI_VRayPlaceEnvTex')	
				if cmds.objExists('MARI_HDR_envLight'):
					cmds.delete('MARI_HDR_envLight')				
				print("Environment Light in Mari is turned off.")		
			# <-----------Finished the process of creating the VRay Light Dome----------->
			
			# <-----------Start the process to create VRay Light Sources----------->			
			
			# Create the light group if at least one of the lights are turned "ON" in Mari, else, delete if there is any group with lights in Maya!
			if (light_data1[-1] != "none") or (light_data2[-1] != "none") or (light_data3[-1] != "none") or (light_data4[-1] != "none"):
								
				# Starts to loop and check if there is data inside the list.				
				for light_params in light_list:	
					# Call a function to compensates the light intensity based on the shader falloff and decay attributes.
					intensity = light_intensity_adjust(light_params);					
					if light_params[1] == "PointLight":
						# Create the Lights and their expressions or keep the variable with their light name on it.
						light = "VRay_Light_" + str(light_params[2])
						light_update = "False"
						if cmds.objExists( light ):						
							light_update = "True"
							# Call a function that will set the light attributes for position and scale.							
							light_shape_attr(light, light_params, light_group, light_update)
							# Update the Light Intensity expression													
							cmds.expression('exp_'+str(light)+'_intensity', edit=True, s=str(light)+'.intensityMult = ' + str(intensity) + ' * '  + str(light_group) + '.Global_Light_Intensity_Multiplier' + ' *' + str(light_group)+'.'+str(light)+'_Intensity_Multiplier', o=light, ae=1, uc='all')		
						else:
							# Create Lights that could be spherical so it could match better the way a point light would illuminates a scene(all directions).							
							light = cmds.shadingNode("VRayLightSphereShape", asLight=True, n="VRay_Light_" + str(light_params[2]) + "Shape")
							# Call a function that will set the light attributes for position and scale.
							light_shape_attr(light, light_params, light_group, light_update)
							# Create an expression to control the Lights Intensity using a Global Attribute in the group node as well using individual controllers for each light.
							cmds.expression(name="exp_"+str(light)+"_intensity", s=str(light)+'.intensityMult = ' + str(intensity) + ' * '  + str(light_group) + '.Global_Light_Intensity_Multiplier' + ' *' + str(light_group)+'.'+str(light)+'_Intensity_Multiplier', o=light, ae=1, uc='all')		
							cmds.parent(light, light_group)
						
						cmds.setAttr(light + '.lightColor', float(light_params[3]),float(light_params[4]),float(light_params[5]), type='double3')						
																							
						cmds.setAttr(light + '.invisible', 1)														
						# Light is turned "OFF" in Mari!
						if light_params[-1] == "hidden":
							cmds.setAttr(light + '.enabled', 0)						
						else:
							cmds.setAttr(light + '.enabled', 1)
							
					else:
						print("Unknown Light Type!")				
				
				cmds.select(light_group)				
				print("Imported VRay Light Sources")
			# <-----------Finished the process of creating the VRay Light Sources----------->
			
			#message complete
			cmds.inViewMessage( amg='<hl>VRay</hl> Lights Transfer Completed', pos='midCenter', fade=True )
		
		# ================= Create Redshift Lights ===============================================================================================================================
		elif shaderType == "Redshift Architectural":
			# <-----------Starts the process to create the Redshift Dome Light----------->
			if envLight_data[-1] != "hidden":
				# Check if the Mari redshiftDomeLight exists, if not create one.				
				if cmds.objExists('MARI_RS_DomeLight') != True:					
					cmds.shadingNode("RedshiftDomeLight", asLight=True, n="MARI_RS_DomeLightShape")			
				
				# add the file_path directory to his attribute.
				# There is no HDR path in Mari, so Environment lights is turned off!
				if envLight_data[1] != " ":
					cmds.setAttr('%s.tex0' %'MARI_RS_DomeLight', envLight_data[1], type="string")
					cmds.setAttr('%s.on' %'MARI_RS_DomeLight', 1)
				else:
					cmds.setAttr('%s.on' %'MARI_RS_DomeLight', 0)
					print("There is no HDR assigned in Mari, so the Environment light will be disabled in the Maya Scene")
					
				# Convert Intensity in Exposure
				envLight_intensity	= float(envLight_data[2])
				envLight_intensity -= 1.0
				if envLight_intensity >= 1.0:				
					envLight_intensity = math.sqrt(envLight_intensity)	
				else:	
					envLight_intensity = -math.pow(envLight_intensity, 2)
					
				cmds.setAttr('MARI_RS_DomeLightShape.exposure0', envLight_intensity, float)
				cmds.setAttr('MARI_RS_DomeLight.rotateY', 180+float(envLight_data[3]), float)				
				print("Redshift Dome Light imported.")	
			else:
				# In case there is no env light data, check if the Mari redshiftDomeLight exists, if so delete it!
				if cmds.objExists('MARI_RS_DomeLight'):
					cmds.delete('MARI_RS_DomeLight')					
				print("Environment Light in Mari is turned off.")	
			# <-----------Finished the process of creating the Redshift Dome Light----------->
			
			# <-----------Start the process to create Redshift Physical Light Sources---------->			
			
			# Create the light group if at least one of the lights are turned "ON" in Mari, else, delete if there is any group with lights in Maya!
			if (light_data1[-1] != "none") or (light_data2[-1] != "none") or (light_data3[-1] != "none") or (light_data4[-1] != "none"):
			
				# Starts to loop and check if there is data inside the list.	
				for light_params in light_list:	
					# Call a function to compensates the light intensity based on the shader falloff and decay attributes.
					intensity = light_intensity_adjust(light_params);					
					if light_params[1] == "PointLight":
						# Create the Lights and their expressions or keep the variable with their light name on it.
						light = "RS_Light_" + str(light_params[2])
						light_update = "False"
						if cmds.objExists( light ):						
							light_update = "True"
							# Call a function that will set the light attributes for position and scale.
							light_shape_attr(light, light_params, light_group, light_update)
							# Update the Light Intensity Expression
							cmds.expression('exp_'+str(light)+'_intensity', edit=True, s=str(light)+'.intensity = ' + str(intensity) + ' * '  + str(light_group) + '.Global_Light_Intensity_Multiplier' + ' *' + str(light_group)+'.'+str(light)+'_Intensity_Multiplier', o=light, ae=1, uc='all')
						else:
							# Create Lights that could be spherical so it could match better the way a point light would illuminates a scene(all directions).							
							light = cmds.shadingNode("RedshiftPhysicalLight", asLight=True, n="RS_Light_" + str(light_params[2]) + "Shape")
							# Call a function that will set the light attributes for position and scale.
							light_shape_attr(light, light_params, light_group, light_update)
							# Create an expression to control the Lights Intensity using a Global Attribute in the group node as well using individual controllers for each light.
							cmds.expression(name="exp_"+str(light)+"_intensity", s=str(light)+'.intensity = ' + str(intensity) + ' * '  + str(light_group) + '.Global_Light_Intensity_Multiplier' + ' *' + str(light_group)+'.'+str(light)+'_Intensity_Multiplier', o=light, ae=1, uc='all')
							cmds.parent(light, light_group)
						
						cmds.setAttr(light + '.color', float(light_params[3]),float(light_params[4]),float(light_params[5]), type='double3')							
																							
						cmds.setAttr(light + '.areaShape', 2)
						cmds.setAttr(light + '.areaVisibleInRender', 0)														
						# Light is turned "OFF" in Mari!
						if light_params[-1] == "hidden":
							cmds.setAttr(light + '.on', 0)						
						else:
							cmds.setAttr(light + '.on', 1)
							
					else:
						print("Unknown Light Type!")				
				
				cmds.select(light_group)				
				print("Imported Redshift Physical Light Sources")
			# <-----------Finished the process of creating the Redshift Physical Light Sources----------->
			
			#message complete
			cmds.inViewMessage( amg='<hl>Redshift</hl> Lights Transfer Completed', pos='midCenter', fade=True )

			
	#got Udim?
	setUdim = "_" + udim
	if udim == "True":
		if shaderType == "Ai Standard":		
			setUdim = "_<udim>"			
		elif shaderType == "VRay Mtl":
			setUdim = "_<UDIM>"			
		elif shaderType == "Redshift Architectural":
			setUdim = "_<UDIM>"		
		#Non-shader support!
		else:
			setUdim = "_<UDIM>"	
		
	#Mipmap Conversion?
	if extMipmap != "none":
		ext8 = ext32 = extMi2pmap
		if exportSubfolder != "none":
			exportDir += exportSubfolder
		
	
	# <----------------------- Creates the Blend Shader and his Shading Group ----------------------->
	sgName = []
	shading_group = []
	selectObjs_shaded = []
	#Variable to be triggered to delete "special" nodes of the shader network!
	global shaderNetworkDel
	shaderNetworkDel = False	
	if layeredShader != "none":		
		if shaderType == "Ai Standard":							
			if cmds.objExists(nameSpace+"mGo_" + curShaderStr + "_Blend_mat") ==True:
				deleteShaderNodes("LayeredShader", curShaderStr)
				layeredShader = nameSpace+"mGo_" + curShaderStr + "_Blend_mat"
				sgName = layeredShader + "_SG"
				shading_group = sgName
				print("updating previous Layered Shader for arnold materials")
			else:				
				# We have to use the LayeredShader from Maya for Arnold, since he does not have a specific Blend Shader!				
				layeredShader = cmds.shadingNode("layeredShader",asShader=True, n=nameSpace+"mGo_" + curShaderStr + "_Blend_mat")
				sgName = layeredShader + "_SG"
				shading_group = cmds.sets(n=sgName, renderable=True,noSurfaceShader=True,empty=True)
				cmds.connectAttr('%s.outColor' %layeredShader, '%s.surfaceShader' %shading_group)
				print("created Layered Shader for arnold materials")			
			
		if shaderType == "VRay Mtl":			
			if cmds.objExists(nameSpace+"mGo_" + curShaderStr + "_Blend_mat") ==True:
				deleteShaderNodes("LayeredShader", curShaderStr)
				layeredShader = nameSpace+"mGo_" + curShaderStr + "_Blend_mat"
				sgName = layeredShader + "_SG"
				shading_group = sgName
				print("updating previous Layered Shader for vray materials")
			else:				
				layeredShader = cmds.shadingNode("VRayBlendMtl",asShader=True, n=nameSpace+"mGo_" + curShaderStr + "_Blend_mat")
				sgName = layeredShader + "_SG"
				shading_group = cmds.sets(n=sgName, renderable=True,noSurfaceShader=True,empty=True)
				cmds.connectAttr('%s.outColor' %layeredShader, '%s.surfaceShader' %shading_group)
				print("created Layered Shader for vray materials")					
				
		elif shaderType == "Redshift Architectural":
			if cmds.objExists(nameSpace+"mGo_" + curShaderStr + "_Blend_mat") ==True:
				deleteShaderNodes("LayeredShader", curShaderStr)
				layeredShader = nameSpace+"mGo_" + curShaderStr + "_Blend_mat"
				sgName = layeredShader + "_SG"
				shading_group = sgName
				print("updating previous Layered Shader for Redshift materials")
			else:				
				layeredShader = cmds.shadingNode("RedshiftMaterialBlender",asShader=True, n=nameSpace+"mGo_" + curShaderStr + "_Blend_mat")
				sgName = layeredShader + "_SG"	
				shading_group = cmds.sets(n=sgName, renderable=True,noSurfaceShader=True,empty=True)
				cmds.connectAttr('%s.outColor' %layeredShader, '%s.surfaceShader' %shading_group)
				print("created Layered Shader for Redshift materials")			
				
	# <----------- Finishes the creation process of the Blend Shader and its Shading Group ----------->			
	
		
	#Open Shader Config file
	shader = []
	shaderCount = 0
	shaderPathfile = []
	while (shaderCount <= int(shaderIndex) and exportLights != "True"):
		shaderPathfile = filePath+geoName+"_"+layeredShaderStr+"_data#"+str(shaderCount)+".mgd"			
		
		print(str(shaderPathfile))
		f = open(shaderPathfile, 'r')		
		shaderConfig = pickle.load(f)				
		f.close()
			
		
		# <----------------------------------- Get the Config Info from the Shader file ----------------------------------->		
		if (exportAttri == "True" or exportChannel == "True"):	
			#get ARNOLD shader config info =====================================================
			if shaderType == "Ai Standard":			
				print("Arnold shader import begun")		
				
				shaderType = shaderConfig[0]
				curShaderStr = shaderConfig[1]
				blend_params = shaderConfig[2].split(',')	
				
				DiffuseColor = shaderConfig[3]
				DiffuseWeight = shaderConfig[4]
				DiffuseRoughness = shaderConfig[5]
				Backlighting = shaderConfig[6]
				SpecularColor = shaderConfig[7]
				SpecularWeight = shaderConfig[8]
				SpecularRoughness = shaderConfig[9]
				Anisotropy = shaderConfig[10]
				Rotation = shaderConfig[11]			
				specReflectance = shaderConfig[12]			
				ReflectionColor = shaderConfig[13]
				ReflectionWeight = shaderConfig[14]
				reflReflectance = shaderConfig[15]			
				RefractionColor = shaderConfig[16]
				RefractionWeight = shaderConfig[17]
				IOR = shaderConfig[18]				
				RefractionRoughness = shaderConfig[19]				
				Transmittance = shaderConfig[20]
				Opacity = shaderConfig[21]
				SSSColor = shaderConfig[22]
				SSSWeight = shaderConfig[23]
				SSSRadius = shaderConfig[24]
				EmissionColor = shaderConfig[25]
				Bump = shaderConfig[26]
				Normal = shaderConfig[27]
				Displacement = shaderConfig[28]				

				aDiffuseColor = shaderConfig[29]
				aDiffuseWeight = shaderConfig[30]
				aDiffuseRoughness = shaderConfig[31]
				aBacklighting = shaderConfig[32]
				aDiffuseFresnel = shaderConfig[33]
				aSpecularColor = shaderConfig[34]
				aSpecularWeight = shaderConfig[35]
				aSpecularRoughness = shaderConfig[36]
				aAnisotropy = shaderConfig[37]
				aRotation = shaderConfig[38]
				aFresnel_On = shaderConfig[39]
				aReflectance = shaderConfig[40]
				aReflectionColor = shaderConfig[41]
				aReflectionWeight = shaderConfig[42]
				aFresnel_On_Ref = shaderConfig[43]
				areflReflectance = shaderConfig[44]
				aRefractionColor = shaderConfig[45]
				aRefractionWeight = shaderConfig[46]
				aRefractionRoughness = shaderConfig[47]
				aIOR = shaderConfig[48]
				aFresnel_useIOR = shaderConfig[49]
				aTransmittance = shaderConfig[50]
				aOpacity = shaderConfig[51]
				aSSSColor = shaderConfig[52]
				aSSSWeight = shaderConfig[53]
				aSSSRadius = shaderConfig[54]
				aEmissionColor = shaderConfig[55]
				aEmission = shaderConfig[56]
				
				aBumpWeight = shaderConfig[57]
				aDisplacementBias = shaderConfig[58]
				aDisplacementScale = shaderConfig[59]
				aDisplacementRange = shaderConfig[60]
				
				#print data
				print("------- Shader Parameters -------")
				allInfo = DiffuseColor, DiffuseWeight, DiffuseRoughness, Backlighting, SpecularColor, SpecularWeight, SpecularRoughness, Anisotropy, Rotation, specReflectance, ReflectionColor, ReflectionWeight, reflReflectance, RefractionColor, RefractionWeight, RefractionRoughness, Transmittance, Opacity, SSSColor, SSSWeight, SSSRadius, EmissionColor, Bump, Normal, Displacement, aDiffuseColor, aDiffuseWeight, aDiffuseRoughness, aBacklighting, aDiffuseFresnel, aSpecularColor, aSpecularWeight, aSpecularRoughness, aAnisotropy, aRotation, aFresnel_On, aReflectance, aReflectionColor, aReflectionWeight, aFresnel_On_Ref, areflReflectance, aRefractionColor, aRefractionWeight, aRefractionRoughness, aIOR, aFresnel_useIOR, aTransmittance, aOpacity, aSSSColor, aSSSWeight, aSSSRadius, aEmissionColor, aEmission, aBumpWeight, aDisplacementScale, aDisplacementBias, aDisplacementScale, aDisplacementRange
				number = 0		
				for all in allInfo:
					print(str(number) + " " + all)
					number = number + 1
				print("---------------------------------")		


			#get VRAY shader config info =====================================================
			elif shaderType == "VRay Mtl":		
				print("Vray shader import begun")
				
				shaderType = shaderConfig[0]
				curShaderStr = shaderConfig[1]
				blend_params = shaderConfig[2].split(',')
				
				DiffuseColor = shaderConfig[3]
				DiffuseAmount = shaderConfig[4]
				Opacity_Map = shaderConfig[5]
				DiffuseRoughness = shaderConfig[6]
				Self_Illumination = shaderConfig[7]
				ReflectionColor = shaderConfig[8]
				ReflectionAmount = shaderConfig[9]
				HighlightGlossiness = shaderConfig[10]
				ReflectionGlossiness = shaderConfig[11]
				Reflection_IOR = shaderConfig[12]
				Anisotropy = shaderConfig[13]
				Rotation = shaderConfig[14]
				RefractionColor = shaderConfig[15]
				RefractionAmount = shaderConfig[16]
				RefractionGlossiness = shaderConfig[17]
				IOR = shaderConfig[18]
				Fog_Color = shaderConfig[19]
				Translucency_Color = shaderConfig[20]
				Bump = shaderConfig[21]
				Normal = shaderConfig[22]
				Displacement = shaderConfig[23]
				
				aDiffuseColor = shaderConfig[24]
				aDiffuseAmount = shaderConfig[25]
				aOpacity_Map = shaderConfig[26]
				aDiffuseRoughness = shaderConfig[27]
				aSelf_Illumination = shaderConfig[28]
				aBRDF_Model = shaderConfig[29]
				aReflectionColor = shaderConfig[30]
				aReflectionAmount = shaderConfig[31]
				aLock_Highlight_Refle_gloss = shaderConfig[32]
				aHighlightGlossiness = shaderConfig[33]
				aReflectionGlossiness = shaderConfig[34]
				aFresnel_On = shaderConfig[35]
				aFresnel_useIOR = shaderConfig[36]
				aReflection_IOR = shaderConfig[37]
				aggxTailFalloff = shaderConfig[38]
				aAnisotropy = shaderConfig[39]
				aRotation = shaderConfig[40]
				aRefractionColor = shaderConfig[41]
				aRefractionAmount = shaderConfig[42]
				aRefractionGlossiness = shaderConfig[43]
				aIOR = shaderConfig[44]
				aFog_Color = shaderConfig[45]
				aFog_multiplier = shaderConfig[46]
				aFog_bias = shaderConfig[47]
				aSSS_On = shaderConfig[48]
				aTranslucency_Color = shaderConfig[49]
				aFwd_back_coeff = shaderConfig[50]
				aScatt_coeff = shaderConfig[51]
				
				aBump = shaderConfig[52]
				aDisplacementScale = shaderConfig[53]
				
				#print data
				print("------- Shader Parameters -------")	
				allInfo = DiffuseColor, DiffuseAmount, Opacity_Map, DiffuseRoughness, Self_Illumination, ReflectionColor, ReflectionAmount, HighlightGlossiness, ReflectionGlossiness, Reflection_IOR, Anisotropy, Rotation, RefractionColor, RefractionAmount, RefractionGlossiness, IOR, Fog_Color, Translucency_Color, Bump, Normal, Displacement, aDiffuseColor, aDiffuseAmount, aOpacity_Map, aDiffuseRoughness, aSelf_Illumination, aBRDF_Model, aReflectionColor, aReflectionAmount, aLock_Highlight_Refle_gloss, aHighlightGlossiness, aReflectionGlossiness, aFresnel_On, aFresnel_useIOR, aReflection_IOR, aggxTailFalloff, aAnisotropy, aRotation, aRefractionColor, aRefractionAmount, aRefractionGlossiness, aIOR, aFog_Color, aFog_multiplier, aFog_bias, aSSS_On, aTranslucency_Color, aFwd_back_coeff, aScatt_coeff, aBump, aDisplacementScale               
				number = 0		
				for all in allInfo:
					print(str(number) + " " + all)
					number = number + 1
				print("---------------------------------")		


			#get REDSHIFT shader config info =====================================================
			elif shaderType == "Redshift Architectural":
				print("Redshift shader import begun")

				shaderType = shaderConfig[0]
				curShaderStr = shaderConfig[1]
				blend_params = shaderConfig[2].split(',')
				
				diffuse_color = shaderConfig[3]
				diffuse_weight = shaderConfig[4]
				diffuse_roughness = shaderConfig[5]
				refr_trans_color = shaderConfig[6]
				refr_trans_weight = shaderConfig[7]
				refl_weight = shaderConfig[8]
				refl_color = shaderConfig[9]
				refl_gloss = shaderConfig[10]
				brdf_0_degree_refl = shaderConfig[11]
				refl_base_weight = shaderConfig[12]
				refl_base_color = shaderConfig[13]
				refl_base_gloss = shaderConfig[14]
				brdf_base_0_degree_refl = shaderConfig[15]
				anisotropy = shaderConfig[16]
				anisotropy_rotation = shaderConfig[17]
				transparency = shaderConfig[18]
				refr_color = shaderConfig[19]
				refr_gloss = shaderConfig[20]
				refr_ior = shaderConfig[21]
				refr_falloff_color = shaderConfig[22]
				cutout_opacity = shaderConfig[23]
				additional_color = shaderConfig[24]
				Bump = shaderConfig[25]
				Normal = shaderConfig[26]
				Displacement = shaderConfig[27]
				
				adiffuse_color = shaderConfig[28]
				adiffuse_weight = shaderConfig[29]
				adiffuse_roughness = shaderConfig[30]
				arefr_translucency = shaderConfig[31]
				arefr_trans_color = shaderConfig[32]
				arefr_trans_weight = shaderConfig[33]
				arefl_weight = shaderConfig[34]
				arefl_color = shaderConfig[35]
				arefl_gloss = shaderConfig[36]
				abrdf_fresnel = shaderConfig[37]
				abrdf_fresnel_type = shaderConfig[38]
				abrdf_extinction_coeff = shaderConfig[39]
				abrdf_0_degree_refl = shaderConfig[40]
				abrdf_90_degree_refl = shaderConfig[41]
				abrdf_Curve = shaderConfig[42]
				arefl_base_weight = shaderConfig[43]
				arefl_base_color = shaderConfig[44]
				arefl_base_gloss = shaderConfig[45]
				abrdf_base_fresnel = shaderConfig[46]
				abrdf_base_fresnel_type = shaderConfig[47]
				abrdf_base_extinction_coeff = shaderConfig[48]
				abrdf_base_0_degree_refl = shaderConfig[49]
				abrdf_base_90_degree_refl = shaderConfig[50]
				abrdf_base_Curve = shaderConfig[51]
				arefl_is_metal = shaderConfig[52]
				ahl_vs_refl_balance = shaderConfig[53]
				aanisotropy = shaderConfig[54]
				aanisotropy_rotation = shaderConfig[55]
				aanisotropy_orientation = shaderConfig[56]
				atransparency = shaderConfig[57]
				arefr_color = shaderConfig[58]
				arefr_gloss = shaderConfig[59]
				arefr_ior = shaderConfig[60]
				arefr_falloff_on = shaderConfig[61]
				arefr_falloff_dist = shaderConfig[62]
				arefr_falloff_color_on = shaderConfig[63]
				arefr_falloff_color = shaderConfig[64]
				aao_on = shaderConfig[65]
				aao_combineMode = shaderConfig[66]
				aao_dark = shaderConfig[67]
				aao_ambient = shaderConfig[68]
				acutout_opacity = shaderConfig[69]
				aadditional_color = shaderConfig[70]
				aIncandescent_Scale = shaderConfig[71] 
				
				aBump = shaderConfig[72]
				aDisplacementScale = shaderConfig[73]
				
				#print data
				print("------- Shader Parameters -------")			
				allInfo = diffuse_color, diffuse_weight, diffuse_roughness, refr_trans_color, refr_trans_weight, refl_weight, refl_color, refl_gloss, brdf_0_degree_refl, refl_base_weight, refl_base_color, refl_base_gloss, brdf_base_0_degree_refl, anisotropy, anisotropy_rotation, transparency, refr_color, refr_gloss, refr_falloff_color, refr_ior, cutout_opacity, additional_color, Bump, Normal, Displacement, adiffuse_color, adiffuse_weight, adiffuse_roughness, arefr_translucency, arefr_trans_color, arefr_trans_weight, arefl_weight, arefl_color, arefl_gloss, abrdf_fresnel, abrdf_fresnel_type, abrdf_extinction_coeff, abrdf_0_degree_refl, abrdf_90_degree_refl, abrdf_Curve, arefl_base_weight, arefl_base_color, arefl_base_gloss, abrdf_base_fresnel, abrdf_base_fresnel_type, abrdf_base_extinction_coeff, abrdf_base_0_degree_refl, abrdf_base_90_degree_refl, abrdf_base_Curve, arefl_is_metal, ahl_vs_refl_balance, aanisotropy, aanisotropy_rotation, aanisotropy_orientation, atransparency, arefr_color, arefr_gloss, arefr_ior, arefr_falloff_on, arefr_falloff_dist, arefr_falloff_color_on, arefr_falloff_color, aao_on, aao_combineMode, aao_dark, aao_ambient, acutout_opacity, aadditional_color, aIncandescent_Scale, aBump, aDisplacementScale
				number = 0		
				for all in allInfo:
					print(str(number) + " " + all)
					number = number + 1
				print("---------------------------------")	
					
			
			#Non-shader config support in one go! =====================================================
			else:
				#delete nodes firts!
				deleteShaderNodes(shaderType, geoName)
				
				#creates a Layered Texture for container purpose only!
				shader = nameSpace+"mGo_"+geoName+"_Channels_Container"
				if cmds.objExists( nameSpace+"mGo_"+geoName+"_Channels_Container" ) != True:
					shader = cmds.shadingNode("layeredShader", asShader=True, n = nameSpace+"mGo_"+geoName+"_Channels_Container" )
				
				#Load each channel from the Config file in a loop setting it up in sequence.
				i = 0
				for config in shaderConfig:
					print(config)
					channelConfig = config
					
					#Send the data inside of this shaderConfig var to a def that will be responsible to create the fileNode with texture.				
					fileNode = setTextureChannels(channelConfig)
					print(fileNode)
					#Assign the fileNode texture to the specific shader slot.
					_attribute = '%s.inputs['+str(i)+'].color' #some bug naming in maya, has to do this way to work.
					#try to connected the fileNode or gammaNode.
					try:
						cmds.connectAttr('%s.outColor' %fileNode, str(_attribute) %shader)
					except:
						cmds.connectAttr('%s.outValue' %fileNode, str(_attribute) %shader)
					i +=1						
			
			#Remove any mGo_ prefix from shaders name, so it will not be double.
			curShaderStr = curShaderStr.lstrip("mGo_")		
		# <----------------------------------- Finish collecting the Config Info from the Shader file ----------------------------------->
		
		# <----------------------------------- Creates the Shader and Shading Group ----------------------------------->
		#create the shader and textures only if Attributes or Channels checkbox have been ticked for exporting.
		if (exportAttri == "True" or exportChannel == "True"):
			
			# but before you create or update the shaders you have to delete any old shaders/textures and connections first!
			deleteShaderNodes(shaderType, curShaderStr)				
			
			#creating arnold material
			if shaderType == "Ai Standard":
				# This allows use to keep the previous shader in case of only been updating the channels!
				if cmds.objExists(nameSpace+"mGo_" + curShaderStr + "_mat") ==True:			
					shader = nameSpace+"mGo_" + curShaderStr + "_mat"
					print("updating previous arnold material.")
				else:
					shader = cmds.shadingNode("aiStandard",asShader=True, n=nameSpace+ "mGo_" + curShaderStr + "_mat")
					print("created arnold material")				
					
					
			#creating vray material
			elif shaderType == "VRay Mtl":
				# This allows use to keep shader in case of only been updating the channels!
				if cmds.objExists(nameSpace+"mGo_" + curShaderStr + "_mat") ==True:			
					shader = nameSpace+"mGo_" + curShaderStr + "_mat"
					print("updating previous vray material.")
				else:
					shader = cmds.shadingNode("VRayMtl",asShader=True, n=nameSpace+ "mGo_" + curShaderStr + "_mat")
					print("created vray material")					
					
				# Reset the shaderbump var, to prevent that in a layered shader case the loop does not connect the shader wrong in the final layered shader!
				shaderBump = []				
				if (Bump != "none") and (Normal != "none"):
					# This allows use to keep shader in case of only been updating the channels!
					if cmds.objExists(nameSpace+"mGo_" + curShaderStr + "_Bump_mat") ==True:
						deleteShaderNodes(shaderType, curShaderStr+"_Bump")
						shaderBump = nameSpace+"mGo_" + curShaderStr + "_Bump_mat"						
						print("updating previous vray bump material.")							
					else:							
						shaderBump = cmds.shadingNode("VRayBumpMtl",asShader=True, n=nameSpace+ "mGo_" + curShaderStr + "_Bump_mat")
						cmds.connectAttr('%s.outColor' %shader, '%s.base_material' %shaderBump)					
						print("created vray bump material")									
				
				else:
					# In case there was a previous bump material left!
					if cmds.objExists(nameSpace+"mGo_" + curShaderStr + "_Bump_mat") ==True:
						deleteShaderNodes(shaderType, nameSpace+"mGo_" + curShaderStr + "_Bump")
						cmds.delete(nameSpace+"mGo_" + curShaderStr + "_Bump_mat")
						print("deleted old Bump material")
						

			#creating redshift material
			elif shaderType == "Redshift Architectural":
				# This allows use to keep shader in case of only been updating the channels!
				if cmds.objExists(nameSpace+"mGo_" + curShaderStr + "_mat") ==True:			
					shader = nameSpace+"mGo_" + curShaderStr + "_mat"
					print("updating previous redshift material.")
				else:
					shader = cmds.shadingNode("RedshiftArchitectural",asShader=True, n=nameSpace+ "mGo_" + curShaderStr + "_mat")
					print("created redshift material")					
							
			
			
			#create the shading_group for non-Blended "single" Shaders
			if layeredShader == "none":
				# This allows use to keep the previous shading groups in case of only been updating the channels!
				if cmds.objExists(nameSpace+"mGo_" + curShaderStr + "_SG") ==True:
					sgName = nameSpace+"mGo_" + curShaderStr + "_SG"	
					shading_group = sgName
				else:
					sgName = nameSpace+"mGo_" + curShaderStr + "_SG"	
					shading_group = cmds.sets(n=nameSpace+sgName, renderable=True,noSurfaceShader=True,empty=True)
					print("Created the Shading Group")	
				
						
			#Assign Inputs for Arnold ===============================================================================================================================
			if shaderType == "Ai Standard":			
				
				#Diffuse Color
				if DiffuseColor != "none":
					#Send the data inside of this shaderConfig var to a def that will be responsible to create the fileNode with texture.				
					fileNode = setTextureChannels(DiffuseColor)					
					#Assign the fileNode texture to the specific shader slot.
					#try to connected the fileNode or gammaNode.
					try:
						cmds.connectAttr('%s.outColor' %fileNode, '%s.color' %shader)
					except:
						cmds.connectAttr('%s.outValue' %fileNode, '%s.color' %shader)
				#as attribute
				elif exportAttri == "True":				
					aDiffuseColor = aDiffuseColor.translate(None, '[]')
					aDiffuseColor = aDiffuseColor.split(',', 2)
					val1=float(aDiffuseColor[0])
					val2=float(aDiffuseColor[1])
					val3=float(aDiffuseColor[2])
					cmds.setAttr(shader + '.color', val1, val2, val3 ,type='double3')
				
				
				#Diffuse Weight
				if DiffuseWeight != "none":					
					#Send the data inside of this shaderConfig var to a def that will be responsible to create the fileNode with texture.				
					fileNode = setTextureChannels(DiffuseWeight)					
					#Assign the fileNode texture to the specific shader slot.					
					cmds.connectAttr('%s.outAlpha' %fileNode, '%s.Kd' %shader)				
				#as attribute
				elif exportAttri == "True":
					cmds.setAttr(shader + '.Kd', float(aDiffuseWeight))

				
				#Diffuse Roughness
				if DiffuseRoughness != "none":					
					#Send the data inside of this shaderConfig var to a def that will be responsible to create the fileNode with texture.				
					fileNode = setTextureChannels(DiffuseRoughness)					
					#Assign the fileNode texture to the specific shader slot.					
					cmds.connectAttr('%s.outAlpha' %fileNode, '%s.diffuseRoughness' %shader)				
				#as attribute
				elif exportAttri == "True":
					cmds.setAttr(shader + '.diffuseRoughness', float(aDiffuseRoughness))
				
				
				#Backlighting
				if Backlighting != "none":					
					#Send the data inside of this shaderConfig var to a def that will be responsible to create the fileNode with texture.				
					fileNode = setTextureChannels(Backlighting)					
					#Assign the fileNode texture to the specific shader slot.					
					cmds.connectAttr('%s.outAlpha' %fileNode, '%s.Kb' %shader)				
				#as attribute
				elif exportAttri == "True":
					cmds.setAttr(shader + '.Kb', float(aBacklighting))
				

				#Specular Colour
				if SpecularColor != "none":
					#Send the data inside of this shaderConfig var to a def that will be responsible to create the fileNode with texture.				
					fileNode = setTextureChannels(SpecularColor)					
					#Assign the fileNode texture to the specific shader slot.
					#try to connected the fileNode or gammaNode.
					try:
						cmds.connectAttr('%s.outColor' %fileNode,'%s.KsColor' %shader)
					except:
						cmds.connectAttr('%s.outValue' %fileNode,'%s.KsColor' %shader)		
				#as attribute
				elif exportAttri == "True":				
					aSpecularColor = aSpecularColor.translate(None, '[]')
					aSpecularColor=aSpecularColor.split(',', 2)
					val1=float(aSpecularColor[0])
					val2=float(aSpecularColor[1])
					val3=float(aSpecularColor[2])
					cmds.setAttr(shader + '.KsColor', val1, val2, val3 ,type='double3')
				
				
				#Specular Weight
				if SpecularWeight != "none":
					#Send the data inside of this shaderConfig var to a def that will be responsible to create the fileNode with texture.				
					fileNode = setTextureChannels(SpecularWeight)					
					#Assign the fileNode texture to the specific shader slot.
					cmds.connectAttr('%s.outAlpha' %fileNode, '%s.Ks' %shader)				
				#as attribute
				elif exportAttri == "True":
					cmds.setAttr(shader + '.Ks', float(aSpecularWeight))
				

				#Specular Roughness
				if SpecularRoughness != "none":
					#Send the data inside of this shaderConfig var to a def that will be responsible to create the fileNode with texture.				
					fileNode = setTextureChannels(SpecularRoughness)					
					#Assign the fileNode texture to the specific shader slot.
					cmds.connectAttr('%s.outAlpha' %fileNode, '%s.specularRoughness' %shader)				
				#as attribute
				elif exportAttri == "True":
					cmds.setAttr(shader + '.specularRoughness', float(aSpecularRoughness))


				# The present version of Arnold allow the anisotropy to be mapped at any time!
				if Anisotropy != "none":
					#Send the data inside of this shaderConfig var to a def that will be responsible to create the fileNode with texture.				
					fileNode = setTextureChannels(Anisotropy)					
					#Assign the fileNode texture to the specific shader slot.						
					cmds.connectAttr('%s.outAlpha' %fileNode, '%s.specularAnisotropy' %shader)						
				#as attribute
				elif exportAttri == "True":
					cmds.setAttr(shader + '.specularAnisotropy', float(aAnisotropy))


				#Rotation
				if Rotation != "none":
					#Send the data inside of this shaderConfig var to a def that will be responsible to create the fileNode with texture.				
					fileNode = setTextureChannels(Rotation)					
					#Assign the fileNode texture to the specific shader slot.
					cmds.connectAttr('%s.outAlpha' %fileNode, '%s.specularRotation' %shader)					
				#as attribute
				elif exportAttri == "True":
					cmds.setAttr(shader + '.specularRotation', float(aRotation))

				
				#Fresnel on Specular					
				if aFresnel_On == "True":
					cmds.setAttr(shader + '.specularFresnel', 1)
					#specReflectance - Reflectance at Normal (Specular)
					if specReflectance != "none":
						#Send the data inside of this shaderConfig var to a def that will be responsible to create the fileNode with texture.				
						fileNode = setTextureChannels(specReflectance)					
						#Assign the fileNode texture to the specific shader slot.
						cmds.connectAttr('%s.outAlpha' %fileNode, '%s.Ksn' %shader)					
					#as attribute
					elif exportAttri == "True":
						cmds.setAttr(shader + '.Ksn', float(aReflectance))	
				else:
					cmds.setAttr(shader + '.specularFresnel', 0)				
				
				
				#Reflection Colour
				if ReflectionColor != "none":
					#Send the data inside of this shaderConfig var to a def that will be responsible to create the fileNode with texture.				
					fileNode = setTextureChannels(ReflectionColor)					
					#Assign the fileNode texture to the specific shader slot.
					#try to connected the fileNode or gammaNode.
					try:
						cmds.connectAttr('%s.outColor' %fileNode,'%s.KrColor' %shader)
					except:
						cmds.connectAttr('%s.outValue' %fileNode,'%s.KrColor' %shader)
				#as attribute
				elif exportAttri == "True":				
					aReflectionColor = aReflectionColor.translate(None, '[]')
					aReflectionColor=aReflectionColor.split(',', 2)
					val1=float(aReflectionColor[0])
					val2=float(aReflectionColor[1])
					val3=float(aReflectionColor[2])
					cmds.setAttr(shader + '.KrColor', val1, val2, val3 ,type='double3')
				
				
				#Reflection Weight
				if ReflectionWeight != "none":
					#Send the data inside of this shaderConfig var to a def that will be responsible to create the fileNode with texture.				
					fileNode = setTextureChannels(ReflectionWeight)					
					#Assign the fileNode texture to the specific shader slot.
					cmds.connectAttr('%s.outAlpha' %fileNode, '%s.Kr' %shader)				
				#as attribute
				elif exportAttri == "True":
					cmds.setAttr(shader + '.Kr', float(aReflectionWeight))	
				
				
				#Fresnel on Reflection
				if aFresnel_On_Ref == "True":
					cmds.setAttr(shader + '.Fresnel', 1)
					#reflReflectance - Reflectance at Normal (Reflection)
					if reflReflectance != "none":
						#Send the data inside of this shaderConfig var to a def that will be responsible to create the fileNode with texture.				
						fileNode = setTextureChannels(reflReflectance)					
						#Assign the fileNode texture to the specific shader slot.
						cmds.connectAttr('%s.outAlpha' %fileNode, '%s.Krn' %shader)						
					#as attribute
					elif exportAttri == "True":
						cmds.setAttr(shader + '.Krn', float(areflReflectance))		
				else:
					cmds.setAttr(shader + '.Fresnel', 0)			

					
				#Refraction Colour
				if RefractionColor != "none":
					#Send the data inside of this shaderConfig var to a def that will be responsible to create the fileNode with texture.				
					fileNode = setTextureChannels(RefractionColor)					
					#Assign the fileNode texture to the specific shader slot.
					#try to connected the fileNode or gammaNode.
					try:
						cmds.connectAttr('%s.outColor' %fileNode, '%s.KtColor' %shader)
					except:
						cmds.connectAttr('%s.outValue' %fileNode, '%s.KtColor' %shader)						
				#as attribute
				elif exportAttri == "True":				
					aRefractionColor = aRefractionColor.translate(None, '[]')
					aRefractionColor=aRefractionColor.split(',', 2)
					val1=float(aRefractionColor[0])
					val2=float(aRefractionColor[1])
					val3=float(aRefractionColor[2])
					cmds.setAttr(shader + '.KtColor', val1, val2, val3 ,type='double3')
				
				
				#Refraction Weight
				if RefractionWeight != "none":
					#Send the data inside of this shaderConfig var to a def that will be responsible to create the fileNode with texture.				
					fileNode = setTextureChannels(RefractionWeight)					
					#Assign the fileNode texture to the specific shader slot.
					cmds.connectAttr('%s.outAlpha' %fileNode, '%s.Kt' %shader)				
				#as attribute
				elif exportAttri == "True":
					cmds.setAttr(shader + '.Kt', float(aRefractionWeight))
				
				
				#IOR
				if IOR != "none":
					#Send the data inside of this shaderConfig var to a def that will be responsible to create the fileNode with texture.				
					fileNode = setTextureChannels(IOR)					
					#Assign the fileNode texture to the specific shader slot.
					cmds.connectAttr('%s.outAlpha' %fileNode, '%s.IOR' %shader)				
				#as attribute
				elif exportAttri == "True":
					cmds.setAttr(shader + '.IOR', float(aIOR))	

				
				#Refraction Rough
				if RefractionRoughness != "none":
					#Send the data inside of this shaderConfig var to a def that will be responsible to create the fileNode with texture.				
					fileNode = setTextureChannels(RefractionRoughness)					
					#Assign the fileNode texture to the specific shader slot.
					cmds.connectAttr('%s.outAlpha' %fileNode, '%s.refractionRoughness' %shader)				
				#as attribute
				elif exportAttri == "True":
					cmds.setAttr(shader + '.refractionRoughness', float(aRefractionRoughness))


				#Transmission
				if Transmittance != "none":
					#Send the data inside of this shaderConfig var to a def that will be responsible to create the fileNode with texture.				
					fileNode = setTextureChannels(Transmittance)					
					#Assign the fileNode texture to the specific shader slot.
					#try to connected the fileNode or gammaNode.
					try:
						cmds.connectAttr('%s.outColor' %fileNode,'%s.transmittance' %shader)
					except:
						cmds.connectAttr('%s.outValue' %fileNode,'%s.transmittance' %shader)
				#as attribute
				elif exportAttri == "True":
					aTransmittance = aTransmittance.translate(None, '[]')
					aTransmittance=aTransmittance.split(',', 2)
					val1=float(aTransmittance[0])
					val2=float(aTransmittance[1])
					val3=float(aTransmittance[2])
					cmds.setAttr(shader + '.transmittance', val1, val2, val3 ,type='double3')


				#Opacity
				if Opacity != "none":
					#Send the data inside of this shaderConfig var to a def that will be responsible to create the fileNode with texture.				
					fileNode = setTextureChannels(Opacity)					
					#Assign the fileNode texture to the specific shader slot.
					#try to connected the fileNode or gammaNode.
					try:
						cmds.connectAttr('%s.outColor' %fileNode,'%s.opacity' %shader)
					except:
						cmds.connectAttr('%s.outValue' %fileNode,'%s.opacity' %shader)
				#as attribute
				elif exportAttri == "True":
					aOpacity = aOpacity.translate(None, '[]')
					aOpacity=aOpacity.split(',', 2)
					val1=float(aOpacity[0])
					val2=float(aOpacity[1])
					val3=float(aOpacity[2])
					cmds.setAttr(shader + '.opacity', val1, val2, val3 ,type='double3')


				#SSS Colour
				if SSSColor != "none":
					#Send the data inside of this shaderConfig var to a def that will be responsible to create the fileNode with texture.				
					fileNode = setTextureChannels(SSSColor)					
					#Assign the fileNode texture to the specific shader slot.
					#try to connected the fileNode or gammaNode.
					try:
						cmds.connectAttr('%s.outColor' %fileNode,'%s.KsssColor' %shader)
					except:
						cmds.connectAttr('%s.outValue' %fileNode,'%s.KsssColor' %shader)
				#as attribute
				elif exportAttri == "True":				
					aSSSColor = aSSSColor.translate(None, '[]')
					aSSSColor=aSSSColor.split(',', 2)
					val1=float(aSSSColor[0])
					val2=float(aSSSColor[1])
					val3=float(aSSSColor[2])
					cmds.setAttr(shader + '.KsssColor', val1, val2, val3 ,type='double3')

				
				#SSS Weight
				if SSSWeight != "none":
					#Send the data inside of this shaderConfig var to a def that will be responsible to create the fileNode with texture.				
					fileNode = setTextureChannels(SSSWeight)					
					#Assign the fileNode texture to the specific shader slot.
					cmds.connectAttr('%s.outAlpha' %fileNode, '%s.Ksss' %shader)				
				#as attribute
				elif exportAttri == "True":
					cmds.setAttr(shader + '.Ksss', float(aSSSWeight))
					
					
				#SSS Radius
				if SSSRadius != "none":
					#Send the data inside of this shaderConfig var to a def that will be responsible to create the fileNode with texture.				
					fileNode = setTextureChannels(SSSRadius)					
					#Assign the fileNode texture to the specific shader slot.
					cmds.connectAttr('%s.outColor' %fileNode,'%s.sssRadius' %shader)				
				#as attribute
				elif exportAttri == "True":				
					aSSSRadius = aSSSRadius.translate(None, '[]')
					aSSSRadius=aSSSRadius.split(',', 2)
					val1=float(aSSSRadius[0])
					val2=float(aSSSRadius[1])
					val3=float(aSSSRadius[2])
					cmds.setAttr(shader + '.sssRadius', val1, val2, val3 ,type='double3')


				#Emission
				if EmissionColor != "none":
					#Send the data inside of this shaderConfig var to a def that will be responsible to create the fileNode with texture.				
					fileNode = setTextureChannels(EmissionColor)					
					#Assign the fileNode texture to the specific shader slot.
					#try to connected the fileNode or gammaNode.
					try:
						cmds.connectAttr('%s.outColor' %fileNode,'%s.emissionColor' %shader)
					except:
						cmds.connectAttr('%s.outValue' %fileNode,'%s.emissionColor' %shader)
				#as attribute
				elif exportAttri == "True":
					aEmissionColor = aEmissionColor.translate(None, '[]')
					aEmissionColor=aEmissionColor.split(',', 2)
					val1=float(aEmissionColor[0])
					val2=float(aEmissionColor[1])
					val3=float(aEmissionColor[2])
					cmds.setAttr(shader + '.emissionColor', val1, val2, val3 ,type='double3')


				#Normal Map
				normalNode = [] # Could be used latter on below to create normal+bump shader.
				if Normal != "none": 
					#Send the data inside of this shaderConfig var to a def that will be responsible to create the fileNode with texture.				
					fileNode_Normal = setTextureChannels(Normal)
					
					channelName = Normal.rsplit("#", 1)[0]
					normalNode=cmds.shadingNode("bump2d",asTexture=True, n=nameSpace+str(geoName)+"_"+channelName+"_normalNode")
					if Bump == "none":
						cmds.connectAttr('%s.outNormal' %normalNode,'%s.normalCamera' %shader)
					cmds.connectAttr('%s.outAlpha' %fileNode_Normal,'%s.bumpValue' %normalNode)
					cmds.setAttr(normalNode + '.bumpInterp', 1)


				#Bump
				if Bump != "none":
					#Send the data inside of this shaderConfig var to a def that will be responsible to create the fileNode with texture.				
					fileNode_Bump = setTextureChannels(Bump)					
					
					channelName = Bump.rsplit("#", 1)[0]
					bumpNode=cmds.shadingNode("bump2d",asTexture=True, n=nameSpace+str(geoName)+"_"+channelName+"_bumpNode")					
					if Normal != "none":
						cmds.connectAttr('%s.outNormal' %normalNode,'%s.normalCamera' %bumpNode)
						
					cmds.connectAttr('%s.outNormal' %bumpNode,'%s.normalCamera' %shader)
					cmds.connectAttr('%s.outAlpha' %fileNode_Bump,'%s.bumpValue' %bumpNode)

					if exportAttri == "True":
						aBumpWeight = float(aBumpWeight)
						aBumpWeight = aBumpWeight / 5.0
						cmds.setAttr(bumpNode + '.bumpDepth', aBumpWeight)


				#Displacement
				if Displacement != "none":
					#Send the data inside of this shaderConfig var to a def that will be responsible to create the fileNode with texture.				
					fileNode_Displacement = setTextureChannels(Displacement)
					
					dispNode = cmds.shadingNode("displacementShader",asTexture=True, n=nameSpace+"mGo_"+curShaderStr+"_dispNode")
					cmds.setAttr( dispNode+'.scale', float(aDisplacementScale) )
					cmds.setAttr( dispNode+'.aiDisplacementZeroValue', float(aDisplacementBias) )
					cmds.setAttr( dispNode+'.aiDisplacementPadding', float(aDisplacementRange) )
					if Bump != "none":
						cmds.setAttr( dispNode+'.aiDisplacementAutoBump', 0)
					else:
						cmds.setAttr( dispNode+'.aiDisplacementAutoBump', 1)
					
					cmds.connectAttr('%s.outAlpha' %fileNode_Displacement,'%s.displacement' %dispNode)
					cmds.connectAttr('%s.displacement' %dispNode,'%s.displacementShader' %sgName)


				print("All Arnold inputs assigned")

				#all other attributes ========================================================================================


				if exportAttri == "True":

					#fresnel affects diffuse
					if aDiffuseFresnel == "False":
						cmds.setAttr(shader + '.FresnelAffectDiff', 0)
					else:
						cmds.setAttr(shader + '.FresnelAffectDiff', 1)

					#Fresnel
					if aFresnel_useIOR == "True":
						cmds.setAttr(shader + '.FresnelUseIOR', 1)
					else:
						cmds.setAttr(shader + '.FresnelUseIOR', 0)

					#Emission Scale
					cmds.setAttr(shader + '.emission', float(aEmission))


				#message complete
				cmds.inViewMessage( amg='<hl>Arnold</hl> Shader Transfer Completed', pos='midCenter', fade=True )


			#Assign Inputs for Vray ===============================================================================================================================
			elif shaderType == "VRay Mtl":
				
				#Diffuse Color
				if DiffuseColor != "none":
					#Send the data inside of this shaderConfig var to a def that will be responsible to create the fileNode with texture.				
					fileNode = setTextureChannels(DiffuseColor)					
					#Assign the fileNode texture to the specific shader slot.
					#try to connected the fileNode or gammaNode.
					try:
						cmds.connectAttr('%s.outColor' %fileNode,'%s.color' %shader)
					except:
						cmds.connectAttr('%s.outValue' %fileNode,'%s.color' %shader)
				#as attribute
				elif exportAttri == "True":
					aDiffuseColor = aDiffuseColor.translate(None, '[]')
					aDiffuseColor=aDiffuseColor.split(',', 2)
					val1=float(aDiffuseColor[0])
					val2=float(aDiffuseColor[1])
					val3=float(aDiffuseColor[2])
					cmds.setAttr(shader + '.color', val1, val2, val3 ,type='double3')
					#gammaNode = setGammaNode(aDiffuseColor, shader, "DiffuseColor")
					#cmds.connectAttr('%s.outValue' %gammaNode,'%s.color' %shader)
					
					
				#Diffuse Amount
				if DiffuseAmount != "none":
					#Send the data inside of this shaderConfig var to a def that will be responsible to create the fileNode with texture.				
					fileNode = setTextureChannels(DiffuseAmount)					
					#Assign the fileNode texture to the specific shader slot.
					cmds.connectAttr('%s.outAlpha' %fileNode,'%s.diffuseColorAmount' %shader)				
				#as attribute
				elif exportAttri == "True":
					cmds.setAttr(shader + '.diffuseColorAmount', float(aDiffuseAmount))	


				#Opacity Map
				if Opacity_Map != "none":
					#Send the data inside of this shaderConfig var to a def that will be responsible to create the fileNode with texture.				
					fileNode = setTextureChannels(Opacity_Map)					
					#Assign the fileNode texture to the specific shader slot.
					#try to connected the fileNode or gammaNode.
					try:
						cmds.connectAttr('%s.outColor' %fileNode,'%s.opacityMap' %shader)
					except:
						cmds.connectAttr('%s.outValue' %fileNode,'%s.opacityMap' %shader)
				#as attribute
				elif exportAttri == "True":
					aOpacity_Map = aOpacity_Map.translate(None, '[]')
					aOpacity_Map=aOpacity_Map.split(',', 2)
					val1=float(aOpacity_Map[0])
					val2=float(aOpacity_Map[1])
					val3=float(aOpacity_Map[2])
					cmds.setAttr(shader + '.opacityMap', val1, val2, val3 ,type='double3')
					#gammaNode = setGammaNode(aOpacity_Map, shader, "Opacity_Map")
					#cmds.connectAttr('%s.outValue' %gammaNode,'%s.opacityMap' %shader)


				#Diffuse Roughness
				if DiffuseRoughness != "none":
					#Send the data inside of this shaderConfig var to a def that will be responsible to create the fileNode with texture.				
					fileNode = setTextureChannels(DiffuseRoughness)					
					#Assign the fileNode texture to the specific shader slot.
					cmds.connectAttr('%s.outAlpha' %fileNode,'%s.roughnessAmount' %shader)				
				#as attribute
				elif exportAttri == "True":
					cmds.setAttr(shader + '.roughnessAmount', float(aDiffuseRoughness))


				#Self-Illumination
				if Self_Illumination != "none":
					#Send the data inside of this shaderConfig var to a def that will be responsible to create the fileNode with texture.				
					fileNode = setTextureChannels(Self_Illumination)					
					#Assign the fileNode texture to the specific shader slot.
					#try to connected the fileNode or gammaNode.
					try:
						cmds.connectAttr('%s.outColor' %fileNode,'%s.illumColor' %shader)
					except:
						cmds.connectAttr('%s.outValue' %fileNode,'%s.illumColor' %shader)
				#as attribute
				elif exportAttri == "True":
					aSelf_Illumination = aSelf_Illumination.translate(None, '[]')
					aSelf_Illumination=aSelf_Illumination.split(',', 2)
					val1=float(aSelf_Illumination[0])
					val2=float(aSelf_Illumination[1])
					val3=float(aSelf_Illumination[2])
					cmds.setAttr(shader + '.illumColor', val1, val2, val3 ,type='double3')
					#gammaNode = setGammaNode(aSelf_Illumination, shader, "Self_Illumination")
					#cmds.connectAttr('%s.outValue' %gammaNode,'%s.illumColor' %shader)


				#Reflection Colour
				if ReflectionColor != "none":
					#Send the data inside of this shaderConfig var to a def that will be responsible to create the fileNode with texture.				
					fileNode = setTextureChannels(ReflectionColor)					
					#Assign the fileNode texture to the specific shader slot.
					#try to connected the fileNode or gammaNode.
					try:
						cmds.connectAttr('%s.outColor' %fileNode,'%s.reflectionColor' %shader)
					except:
						cmds.connectAttr('%s.outValue' %fileNode,'%s.reflectionColor' %shader)
				#as attribute
				elif exportAttri == "True":
					aReflectionColor = aReflectionColor.translate(None, '[]')
					aReflectionColor=aReflectionColor.split(',', 2)
					val1=float(aReflectionColor[0])
					val2=float(aReflectionColor[1])
					val3=float(aReflectionColor[2])
					cmds.setAttr(shader + '.reflectionColor', val1, val2, val3 ,type='double3')
					#gammaNode = setGammaNode(aReflectionColor, shader, "ReflectionColor")
					#cmds.connectAttr('%s.outValue' %gammaNode,'%s.reflectionColor' %shader)
					
				
				#Reflection Amount
				if ReflectionAmount != "none":
					#Send the data inside of this shaderConfig var to a def that will be responsible to create the fileNode with texture.				
					fileNode = setTextureChannels(ReflectionAmount)					
					#Assign the fileNode texture to the specific shader slot.
					cmds.connectAttr('%s.outAlpha' %fileNode,'%s.reflectionColorAmount' %shader)				
				#as attribute
				elif exportAttri == "True":
					cmds.setAttr(shader + '.reflectionColorAmount', float(aReflectionAmount))	


				#Highlight Glossiness
				if HighlightGlossiness != "none":
					#Send the data inside of this shaderConfig var to a def that will be responsible to create the fileNode with texture.				
					fileNode = setTextureChannels(HighlightGlossiness)					
					#Assign the fileNode texture to the specific shader slot.
					cmds.connectAttr('%s.outAlpha' %fileNode,'%s.hilightGlossiness' %shader)				
				#as attribute
				elif exportAttri == "True":
					cmds.setAttr(shader + '.hilightGlossiness', float(aHighlightGlossiness))


				#Reflection Glossiness
				if ReflectionGlossiness != "none":
					#Send the data inside of this shaderConfig var to a def that will be responsible to create the fileNode with texture.				
					fileNode = setTextureChannels(ReflectionGlossiness)					
					#Assign the fileNode texture to the specific shader slot.
					cmds.connectAttr('%s.outAlpha' %fileNode,'%s.reflectionGlossiness' %shader)				
				#as attribute
				elif exportAttri == "True":
					cmds.setAttr(shader + '.reflectionGlossiness', float(aReflectionGlossiness))

					
				#Reflection IOR
				if Reflection_IOR != "none":
					#Send the data inside of this shaderConfig var to a def that will be responsible to create the fileNode with texture.				
					fileNode = setTextureChannels(Reflection_IOR)					
					#Assign the fileNode texture to the specific shader slot.					
					cmds.connectAttr('%s.outAlpha' %fileNode,'%s.fresnelIOR' %shader)				
				#as attribute
				elif exportAttri == "True":
					cmds.setAttr(shader + '.fresnelIOR', float(aReflection_IOR))
					
					
				#Anisotropy
				if Anisotropy != "none":
					#Send the data inside of this shaderConfig var to a def that will be responsible to create the fileNode with texture.				
					fileNode = setTextureChannels(Anisotropy)					
					#Assign the fileNode texture to the specific shader slot.					
					cmds.connectAttr('%s.outAlpha' %fileNode,'%s.anisotropy' %shader)				
				#as attribute
				elif exportAttri == "True":
					cmds.setAttr(shader + '.anisotropy', float(aAnisotropy))


				#Rotation
				if Rotation != "none":
					#Send the data inside of this shaderConfig var to a def that will be responsible to create the fileNode with texture.				
					fileNode = setTextureChannels(Rotation)					
					#Assign the fileNode texture to the specific shader slot.
					cmds.connectAttr('%s.outAlpha' %fileNode,'%s.anisotropyRotation' %shader)				
				#as attribute
				elif exportAttri == "True":
					cmds.setAttr(shader + '.anisotropyRotation', float(aRotation))


				#Refraction Color
				if RefractionColor != "none":
					#Send the data inside of this shaderConfig var to a def that will be responsible to create the fileNode with texture.				
					fileNode = setTextureChannels(RefractionColor)					
					#Assign the fileNode texture to the specific shader slot.
					#try to connected the fileNode or gammaNode.
					try:
						cmds.connectAttr('%s.outColor' %fileNode,'%s.refractionColor' %shader)
					except:
						cmds.connectAttr('%s.outValue' %fileNode,'%s.refractionColor' %shader)
				#as attribute
				elif exportAttri == "True":
					aRefractionColor = aRefractionColor.translate(None, '[]')
					aRefractionColor=aRefractionColor.split(',', 2)
					val1=float(aRefractionColor[0])
					val2=float(aRefractionColor[1])
					val3=float(aRefractionColor[2])
					cmds.setAttr(shader + '.refractionColor', val1, val2, val3 ,type='double3')
					#gammaNode = setGammaNode(aRefractionColor, shader, "RefractionColor")
					#cmds.connectAttr('%s.outValue' %gammaNode,'%s.refractionColor' %shader)
					
					
				#Refraction Amount
				if RefractionAmount != "none":
					#Send the data inside of this shaderConfig var to a def that will be responsible to create the fileNode with texture.				
					fileNode = setTextureChannels(RefractionAmount)					
					#Assign the fileNode texture to the specific shader slot.
					cmds.connectAttr('%s.outAlpha' %fileNode,'%s.refractionColorAmount' %shader)				
				#as attribute
				elif exportAttri == "True":
					cmds.setAttr(shader + '.refractionColorAmount', float(aRefractionAmount))


				#Refraction Glossiness
				if RefractionGlossiness != "none":
					#Send the data inside of this shaderConfig var to a def that will be responsible to create the fileNode with texture.				
					fileNode = setTextureChannels(RefractionGlossiness)					
					#Assign the fileNode texture to the specific shader slot.
					cmds.connectAttr('%s.outAlpha' %fileNode,'%s.refractionGlossiness' %shader)				
				#as attribute
				elif exportAttri == "True":
					cmds.setAttr(shader + '.refractionGlossiness', float(aRefractionGlossiness))
					
					
				#IOR
				if IOR != "none":
					#Send the data inside of this shaderConfig var to a def that will be responsible to create the fileNode with texture.				
					fileNode = setTextureChannels(IOR)					
					#Assign the fileNode texture to the specific shader slot.
					cmds.connectAttr('%s.outAlpha' %fileNode,'%s.refractionIOR' %shader)				
				#as attribute
				elif exportAttri == "True":
					cmds.setAttr(shader + '.refractionIOR', float(aIOR))


				#Fog Color
				if Fog_Color != "none":
					#Send the data inside of this shaderConfig var to a def that will be responsible to create the fileNode with texture.				
					fileNode = setTextureChannels(Fog_Color)					
					#Assign the fileNode texture to the specific shader slot.
					#try to connected the fileNode or gammaNode.
					try:	
						cmds.connectAttr('%s.outColor' %fileNode,'%s.fogColor' %shader)
					except:
						cmds.connectAttr('%s.outValue' %fileNode,'%s.fogColor' %shader)
				#as attribute
				elif exportAttri == "True":
					aFog_Color = aFog_Color.translate(None, '[]')
					aFog_Color=aFog_Color.split(',', 2)
					val1=float(aFog_Color[0])
					val2=float(aFog_Color[1])
					val3=float(aFog_Color[2])
					cmds.setAttr(shader + '.fogColor', val1, val2, val3 ,type='double3')
					#gammaNode = setGammaNode(aFog_Color, shader, "Fog_Color")
					#cmds.connectAttr('%s.outValue' %gammaNode,'%s.fogColor' %shader)


				#Translucency Color
				if Translucency_Color != "none":
					#Send the data inside of this shaderConfig var to a def that will be responsible to create the fileNode with texture.				
					fileNode = setTextureChannels(Translucency_Color)					
					#Assign the fileNode texture to the specific shader slot.
					#try to connected the fileNode or gammaNode.
					try:
						cmds.connectAttr('%s.outColor' %fileNode,'%s.translucencyColor' %shader)
					except:
						cmds.connectAttr('%s.outValue' %fileNode,'%s.translucencyColor' %shader)
				#as attribute
				elif exportAttri == "True":
					aTranslucency_Color = aTranslucency_Color.translate(None, '[]')
					aTranslucency_Color=aTranslucency_Color.split(',', 2)
					val1=float(aTranslucency_Color[0])
					val2=float(aTranslucency_Color[1])
					val3=float(aTranslucency_Color[2])
					cmds.setAttr (shader + '.translucencyColor', val1, val2, val3 ,type='double3')
					#gammaNode = setGammaNode(aTranslucency_Color, shader, "Translucency_Color")
					#cmds.connectAttr('%s.outValue' %gammaNode,'%s.translucencyColor' %shader)


				#Normal Map
				if Normal != "none": 
					#Send the data inside of this shaderConfig var to a def that will be responsible to create the fileNode with texture.				
					fileNode_Normal = setTextureChannels(Normal)
					
					cmds.connectAttr('%s.outColor' %fileNode_Normal,'%s.bumpMap' %shader)					
					cmds.setAttr(shader + '.bumpMapType', 1)				


				#Bump
				if Bump != "none":
					#Send the data inside of this shaderConfig var to a def that will be responsible to create the fileNode with texture.				
					fileNode_Bump = setTextureChannels(Bump)
						
					# If using normal+bump maps
					if Normal != "none":					
						cmds.connectAttr('%s.outColor' %fileNode_Bump, '%s.bumpMap' %shaderBump)
						if exportAttri == "True":
							aBump = float(aBump)
							aBump = aBump / 2.5
							cmds.setAttr(shaderBump + '.bumpMult', float(aBump))
					else:					
						cmds.setAttr(shader + '.bumpMapType', 0)
						cmds.connectAttr('%s.outColor' %fileNode_Bump, '%s.bumpMap' %shader)
						if exportAttri == "True":
							aBump = float(aBump)
							aBump = aBump / 2.5
							cmds.setAttr(shader + '.bumpMult', float(aBump))
				

				#Displacement
				if Displacement != "none":
					#Send the data inside of this shaderConfig var to a def that will be responsible to create the fileNode with texture.				
					fileNode_Displacement = setTextureChannels(Displacement)

					dispNode = cmds.shadingNode("displacementShader",asTexture=True, n=nameSpace+"mGo_"+curShaderStr+"_dispNode")
					cmds.setAttr( dispNode+'.scale', float(aDisplacementScale) )
					
					cmds.connectAttr('%s.outAlpha' %fileNode_Displacement,'%s.displacement' %dispNode)
					cmds.connectAttr('%s.displacement' %dispNode,'%s.displacementShader' %sgName)


				print("All VRay inputs assigned")


				#all other attributes ========================================================================================

				if exportAttri == "True":

					#vBRDFModel
					if aBRDF_Model == "Blinn":
						cmds.setAttr(shader + '.brdfType', 1)
					elif aBRDF_Model == "Phong":
						cmds.setAttr(shader + '.brdfType', 0)
					elif aBRDF_Model == "Ward":
						cmds.setAttr(shader + '.brdfType', 2)					
					elif aBRDF_Model == "GGX":
						# only v3.0+
						try:
							cmds.setAttr(shader + '.brdfType', 3)	
						except:
							pass						
						
					#Lock Highlight to Reflection
					if aLock_Highlight_Refle_gloss == "True":
						cmds.setAttr(shader + '.hilightGlossinessLock', 1)
					else:
						cmds.setAttr(shader + '.hilightGlossinessLock', 0)									
					
					#Fresnel & IOR
					if aFresnel_On == "True":
						cmds.setAttr(shader + '.useFresnel', 1)
					else:
						cmds.setAttr(shader + '.useFresnel', 0)
					
					if aFresnel_useIOR == "True":
						cmds.setAttr(shader + '.lockFresnelIORToRefractionIOR', 1)
					else:
						cmds.setAttr(shader + '.lockFresnelIORToRefractionIOR', 0)
					
					#GGX Tail Falloff - only v3.0+
					try:	
						cmds.setAttr(shader + '.ggxTailFalloff', float(aggxTailFalloff))
					except:
						pass
						
					#Fog
					cmds.setAttr(shader + '.fogBias', float(aFog_bias))
					cmds.setAttr(shader + '.fogMult', float(aFog_multiplier))

					#SSS
					if aSSS_On == "True":
						cmds.setAttr(shader + '.sssOn', 1)
					else:
						cmds.setAttr(shader + '.sssOn', 0)

					cmds.setAttr(shader + '.scatterCoeff', float(aScatt_coeff))
					cmds.setAttr(shader + '.scatterDir', float(aFwd_back_coeff))


				#message complete
				cmds.inViewMessage( amg='<hl>VRay</hl> Shader Transfer Completed', pos='midCenter', fade=True )


			#====================================================================================================
			elif shaderType == "Redshift Architectural":
				
				#Diffuse Color
				if diffuse_color != "none":
					#Send the data inside of this shaderConfig var to a def that will be responsible to create the fileNode with texture.				
					fileNode = setTextureChannels(diffuse_color)					
					#Assign the fileNode texture to the specific shader slot.
					cmds.connectAttr('%s.outColor' %fileNode,'%s.diffuse' %shader)				
				#as attribute
				elif exportAttri == "True":				
					adiffuse_color = adiffuse_color.translate(None, '[]')
					adiffuse_color=adiffuse_color.split(',', 2)
					val1=float(adiffuse_color[0])
					val2=float(adiffuse_color[1])
					val3=float(adiffuse_color[2])
					cmds.setAttr(shader + '.diffuse', val1, val2, val3 ,type='double3')
				
				
				#Diffuse Weight
				if diffuse_weight != "none":
					#Send the data inside of this shaderConfig var to a def that will be responsible to create the fileNode with texture.				
					fileNode = setTextureChannels(diffuse_weight)					
					#Assign the fileNode texture to the specific shader slot.
					cmds.connectAttr('%s.outAlpha' %fileNode,'%s.diffuse_weight' %shader)				
				#as attribute
				elif exportAttri == "True":
					cmds.setAttr(shader + '.diffuse_weight', float(adiffuse_weight))

				
				#Diffuse Roughness
				if diffuse_roughness != "none":
					#Send the data inside of this shaderConfig var to a def that will be responsible to create the fileNode with texture.				
					fileNode = setTextureChannels(diffuse_roughness)					
					#Assign the fileNode texture to the specific shader slot.
					cmds.connectAttr('%s.outAlpha' %fileNode,'%s.diffuse_roughness' %shader)				
				#as attribute
				elif exportAttri == "True":
					cmds.setAttr(shader + '.diffuse_roughness', float(adiffuse_roughness))


				#Translucency Color
				if arefr_translucency == "True":
					cmds.setAttr(shader + '.refr_translucency', 1)
					if refr_trans_color != "none":
						#Send the data inside of this shaderConfig var to a def that will be responsible to create the fileNode with texture.				
						fileNode = setTextureChannels(refr_trans_color)					
						#Assign the fileNode texture to the specific shader slot.	
						cmds.connectAttr('%s.outColor' %fileNode, '%s.refr_trans_color' %shader)					
					#as attribute
					elif exportAttri == "True":				
						cmds.setAttr(shader + '.refr_translucency', 1)
						arefr_trans_color = arefr_trans_color.translate(None, '[]')
						arefr_trans_color=arefr_trans_color.split(',', 2)
						val1=float(arefr_trans_color[0])
						val2=float(arefr_trans_color[1])
						val3=float(arefr_trans_color[2])
						cmds.setAttr(shader + '.refr_trans_color', val1, val2, val3 ,type='double3')				
				# if translucency is not checked ZERO it out
				elif arefr_translucency == "False":
					cmds.setAttr(shader + '.refr_translucency', 0)
					
					
				#Translucency Weight
				if arefr_translucency == "True":
					if refr_trans_weight != "none": 
						#Send the data inside of this shaderConfig var to a def that will be responsible to create the fileNode with texture.				
						fileNode = setTextureChannels(refr_trans_weight)					
						#Assign the fileNode texture to the specific shader slot.
						cmds.connectAttr('%s.outAlpha' %fileNode,'%s.refr_trans_weight' %shader)				
					#as attribute
					elif exportAttri == "True":
						cmds.setAttr(shader + '.refr_trans_weight', float(arefr_trans_weight))
			
				
				#Reflection Weight
				if refl_weight != "none":
					#Send the data inside of this shaderConfig var to a def that will be responsible to create the fileNode with texture.				
					fileNode = setTextureChannels(refl_weight)					
					#Assign the fileNode texture to the specific shader slot.
					cmds.connectAttr('%s.outAlpha' %fileNode,'%s.reflectivity' %shader)				
				#as attribute
				elif exportAttri == "True":
					cmds.setAttr(shader + '.reflectivity', float(arefl_weight))
					
					
				#Reflection Colour
				if refl_color != "none":
					#Send the data inside of this shaderConfig var to a def that will be responsible to create the fileNode with texture.				
					fileNode = setTextureChannels(refl_color)					
					#Assign the fileNode texture to the specific shader slot.
					cmds.connectAttr('%s.outColor' %fileNode,'%s.refl_color' %shader)				
				#as attribute
				elif exportAttri == "True":
					arefl_color = arefl_color.translate(None, '[]')
					arefl_color=arefl_color.split(',', 2)
					val1=float(arefl_color[0])
					val2=float(arefl_color[1])
					val3=float(arefl_color[2])
					cmds.setAttr(shader + '.refl_color', val1, val2, val3 ,type='double3')


				#Reflection Glossiness
				if refl_gloss != "none":
					#Send the data inside of this shaderConfig var to a def that will be responsible to create the fileNode with texture.				
					fileNode = setTextureChannels(refl_gloss)					
					#Assign the fileNode texture to the specific shader slot.
					cmds.connectAttr('%s.outAlpha' %fileNode,'%s.refl_gloss' %shader)				
				#as attribute
				elif exportAttri == "True":
					cmds.setAttr(shader + '.refl_gloss', float(arefl_gloss))
					
					
				#brdf_0_degree_refl
				if abrdf_fresnel != "True":
					if brdf_0_degree_refl != "none":
						#Send the data inside of this shaderConfig var to a def that will be responsible to create the fileNode with texture.				
						fileNode = setTextureChannels(brdf_0_degree_refl)					
						#Assign the fileNode texture to the specific shader slot.
						cmds.connectAttr('%s.outAlpha' %fileNode,'%s.brdf_0_degree_refl' %shader)				
					#as attribute
					elif exportAttri == "True":
						cmds.setAttr(shader + '.brdf_0_degree_refl', float(abrdf_0_degree_refl))

					
				#refl_base_weight
				if refl_base_weight != "none":
					#Send the data inside of this shaderConfig var to a def that will be responsible to create the fileNode with texture.				
					fileNode = setTextureChannels(refl_base_weight)					
					#Assign the fileNode texture to the specific shader slot.
					cmds.connectAttr('%s.outAlpha' %fileNode,'%s.refl_base' %shader)				
				#as attribute
				elif exportAttri == "True":
					cmds.setAttr(shader + '.refl_base', float(arefl_base_weight))					


				#Reflection Colour (Secondary)
				if refl_base_color != "none":
					#Send the data inside of this shaderConfig var to a def that will be responsible to create the fileNode with texture.				
					fileNode = setTextureChannels(refl_base_color)					
					#Assign the fileNode texture to the specific shader slot.
					cmds.connectAttr('%s.outColor' %fileNode,'%s.refl_base_color' %shader)				
				#as attribute
				elif exportAttri == "True":
					arefl_base_color = arefl_base_color.translate(None, '[]')
					arefl_base_color=arefl_base_color.split(',', 2)
					val1=float(arefl_base_color[0])
					val2=float(arefl_base_color[1])
					val3=float(arefl_base_color[2])
					cmds.setAttr(shader + '.refl_base_color', val1, val2, val3 ,type='double3')


				#Reflection Glossiness (Secondary)
				if refl_base_gloss != "none":
					#Send the data inside of this shaderConfig var to a def that will be responsible to create the fileNode with texture.				
					fileNode = setTextureChannels(refl_base_gloss)					
					#Assign the fileNode texture to the specific shader slot.
					cmds.connectAttr('%s.outAlpha' %fileNode,'%s.refl_base_gloss' %shader)				
				#as attribute
				elif exportAttri == "True":
					cmds.setAttr(shader + '.refl_base_gloss', float(arefl_base_gloss))

					
				#brdf_base_0_degree_refl
				if abrdf_base_fresnel != "True":
					if brdf_base_0_degree_refl != "none":
						#Send the data inside of this shaderConfig var to a def that will be responsible to create the fileNode with texture.				
						fileNode = setTextureChannels(brdf_base_0_degree_refl)					
						#Assign the fileNode texture to the specific shader slot.
						cmds.connectAttr('%s.outAlpha' %fileNode,'%s.brdf_base_0_degree_refl' %shader)				
					#as attribute
					elif exportAttri == "True":
						cmds.setAttr(shader + '.brdf_base_0_degree_refl', float(abrdf_base_0_degree_refl))	

					
				#Anisotropy
				if anisotropy != "none":
					#Send the data inside of this shaderConfig var to a def that will be responsible to create the fileNode with texture.				
					fileNode = setTextureChannels(anisotropy)					
					#Assign the fileNode texture to the specific shader slot.
					cmds.connectAttr('%s.outAlpha' %fileNode,'%s.anisotropy' %shader)				
				#as attribute
				elif exportAttri == "True":
					cmds.setAttr(shader + '.anisotropy', float(aanisotropy))


				#Anisotropy Rotation
				if anisotropy_rotation != "none":
					#Send the data inside of this shaderConfig var to a def that will be responsible to create the fileNode with texture.				
					fileNode = setTextureChannels(anisotropy_rotation)					
					#Assign the fileNode texture to the specific shader slot.
					cmds.connectAttr('%s.outAlpha' %fileNode,'%s.anisotropy_rotation' %shader)				
				#as attribute
				elif exportAttri == "True":
					cmds.setAttr(shader + '.anisotropy_rotation', float(aanisotropy_rotation))

					
				#transparency
				if transparency != "none":
					#Send the data inside of this shaderConfig var to a def that will be responsible to create the fileNode with texture.				
					fileNode = setTextureChannels(transparency)					
					#Assign the fileNode texture to the specific shader slot.
					cmds.connectAttr('%s.outAlpha' %fileNode,'%s.transparency' %shader)				
				#as attribute
				elif exportAttri == "True":
					cmds.setAttr(shader + '.transparency', float(atransparency))
					
					
				#Refraction Color
				if refr_color != "none":
					#Send the data inside of this shaderConfig var to a def that will be responsible to create the fileNode with texture.				
					fileNode = setTextureChannels(refr_color)					
					#Assign the fileNode texture to the specific shader slot.
					cmds.connectAttr('%s.outColor' %fileNode,'%s.refr_color' %shader)				
				#as attribute
				elif exportAttri == "True":
					arefr_color = arefr_color.translate(None, '[]')
					arefr_color=arefr_color.split(',', 2)
					val1=float(arefr_color[0])
					val2=float(arefr_color[1])
					val3=float(arefr_color[2])
					cmds.setAttr(shader + '.refr_color', val1, val2, val3 ,type='double3')


				#Refraction Glossiness
				if refr_gloss != "none":
					#Send the data inside of this shaderConfig var to a def that will be responsible to create the fileNode with texture.				
					fileNode = setTextureChannels(refr_gloss)					
					#Assign the fileNode texture to the specific shader slot.
					cmds.connectAttr('%s.outAlpha' %fileNode,'%s.refr_gloss' %shader)				
				#as attribute
				elif exportAttri == "True":
					cmds.setAttr(shader + '.refr_gloss', float(arefr_gloss))
					
					
				#Refraction IOR
				if refr_ior != "none":
					#Send the data inside of this shaderConfig var to a def that will be responsible to create the fileNode with texture.				
					fileNode = setTextureChannels(refr_ior)					
					#Assign the fileNode texture to the specific shader slot.
					cmds.connectAttr('%s.outAlpha' %fileNode,'%s.refr_ior' %shader)				
				#as attribute
				elif exportAttri == "True":
					cmds.setAttr(shader + '.refr_ior', float(arefr_ior))	


				#End Color (Fog)
				if arefr_falloff_on == "True":
					cmds.setAttr(shader + '.refr_falloff_on', 1)
					cmds.setAttr(shader + '.refr_falloff_dist', float(arefr_falloff_dist))
					if arefr_falloff_color_on == "True":
						cmds.setAttr(shader + '.refr_falloff_color_on', 1)
						if refr_falloff_color != "none":
							#Send the data inside of this shaderConfig var to a def that will be responsible to create the fileNode with texture.				
							fileNode = setTextureChannels(refr_falloff_color)					
							#Assign the fileNode texture to the specific shader slot.	
							cmds.connectAttr('%s.outColor' %fileNode,'%s.refr_falloff_color' %shader)						
						#as attribute
						elif exportAttri == "True":
							arefr_falloff_color = arefr_falloff_color.translate(None, '[]')
							arefr_falloff_color=arefr_falloff_color.split(',', 2)
							val1=float(arefr_falloff_color[0])
							val2=float(arefr_falloff_color[1])
							val3=float(arefr_falloff_color[2])
							cmds.setAttr(shader + '.refr_falloff_color', val1, val2, val3 ,type='double3')					
					# ZERO out attributes that are not checked
					else:
						cmds.setAttr(shader + '.refr_falloff_color_on', 0)
				else:
					cmds.setAttr(shader + '.refr_falloff_on', 0)


				#Cutout Opacity
				if cutout_opacity != "none":
					#Send the data inside of this shaderConfig var to a def that will be responsible to create the fileNode with texture.				
					fileNode = setTextureChannels(cutout_opacity)					
					#Assign the fileNode texture to the specific shader slot.
					cmds.connectAttr('%s.outAlpha' %fileNode,'%s.cutout_opacity' %shader)				
				#as attribute
				elif exportAttri == "True":
					cmds.setAttr(shader + '.cutout_opacity', float(acutout_opacity))


				#Incandescent Color
				if additional_color != "none":
					#Send the data inside of this shaderConfig var to a def that will be responsible to create the fileNode with texture.				
					fileNode = setTextureChannels(additional_color)					
					#Assign the fileNode texture to the specific shader slot.
					cmds.connectAttr('%s.outColor' %fileNode,'%s.additional_color' %shader)				
				#as attribute
				elif exportAttri == "True":
					aadditional_color = aadditional_color.translate(None, '[]')
					aadditional_color=aadditional_color.split(',', 2)
					val1=float(aadditional_color[0])
					val2=float(aadditional_color[1])
					val3=float(aadditional_color[2])
					cmds.setAttr(shader + '.additional_color', val1, val2, val3 ,type='double3')


				# I can't delete this guys with the delete def, so have to do it manually, as well fix their name!
				if cmds.objExists(nameSpace+str(geoName)+"_"+curShaderStr+"_normalNode") ==True:
					cmds.delete(nameSpace+str(geoName)+"_"+curShaderStr+"_normalNode")
				if cmds.objExists(nameSpace+str(geoName)+"_"+curShaderStr+"_bumpNode") ==True:
					cmds.delete(nameSpace+str(geoName)+"_"+curShaderStr+"_bumpNode")
				if cmds.objExists(nameSpace+str(geoName)+"_"+curShaderStr+"_BumpBlender") ==True:
					cmds.delete(nameSpace+str(geoName)+"_"+curShaderStr+"_BumpBlender")
					
				#Normal Map
				normalNode = [] # Could be used latter on below to create normal+bump shader.
				if Normal != "none":
					
					channelDepth = Normal.rsplit("#", 1)[1]
					channelName = Normal.rsplit("#", 1)[0]

					if channelDepth == "8":
						channel_path = str(exportDir+geoName+'_'+channelName+setUdim+"."+ext8)
					else:
						channel_path = str(exportDir+geoName+'_'+channelName+setUdim+"."+ext32)
					
					
					normalNode=cmds.shadingNode("RedshiftNormalMap",asUtility=True, n=nameSpace+str(geoName)+"_"+curShaderStr+"_normalNode")
					cmds.setAttr('%s.tex0' %normalNode, channel_path, type="string")
					if Bump == "none":
						cmds.connectAttr('%s.outDisplacementVector' %normalNode, '%s.bump_input' %shader)


				#Bump
				if Bump != "none":
					#Send the data inside of this shaderConfig var to a def that will be responsible to create the fileNode with texture.				
					fileNode_Bump = setTextureChannels(Bump)
										
					bumpNode=cmds.shadingNode("RedshiftBumpMap", asUtility=True, n=nameSpace+str(geoName)+"_"+curShaderStr+"_bumpNode")
					cmds.connectAttr('%s.outColor' %fileNode_Bump, '%s.input' %bumpNode)
					if exportAttri == "True":
						aBump = float(aBump)
						aBump = aBump / 5.0
						cmds.setAttr(bumpNode + '.scale', aBump)
						
					if Normal != "none":
						blenderNode=cmds.shadingNode("RedshiftBumpBlender", asUtility=True, n=nameSpace+str(geoName)+"_"+curShaderStr+"_BumpBlender")					
						cmds.connectAttr('%s.outColor' %blenderNode, '%s.bump_input' %shader)
						cmds.connectAttr('%s.out' %bumpNode, '%s.baseInput' %blenderNode)
						cmds.connectAttr('%s.outDisplacementVector' %normalNode, '%s.bumpInput0' %blenderNode)
						cmds.setAttr(blenderNode+'.additive', 1)
						cmds.setAttr(blenderNode+'.bumpWeight0', 1)
						#cmds.setAttr(bumpNode+'.normalize', 1) This attribute has been removed from Redshift
					else:
						cmds.connectAttr('%s.out' %bumpNode, '%s.bump_input' %shader)


				#Displacement
				if Displacement != "none":
					#Send the data inside of this shaderConfig var to a def that will be responsible to create the fileNode with texture.				
					fileNode_Displacement = setTextureChannels(Displacement)
						
					dispNode = cmds.shadingNode("RedshiftDisplacement",asTexture=True, n=nameSpace+"mGo_"+curShaderStr+"_dispNode")
					cmds.setAttr( dispNode+'.scale', float(aDisplacementScale) )
					if Bump != "none":
						cmds.setAttr( dispNode+'.autoBump', 0)

					cmds.connectAttr('%s.outColor' %fileNode_Displacement,'%s.texMap' %dispNode)
					cmds.connectAttr('%s.out' %dispNode,'%s.rsDisplacementShader' %sgName)


				print("All Redshift inputs assigned")

				#all other attributes ========================================================================================

				if exportAttri == "True":
                                        #In case user is using the Redshift v2.0, the shader comes by default with the Beckmann(Cook-Torrance) selected!
                                        #Try to use Ashikhmin-Shirley (legacy), only current BRDF implemented in our Mari shader replica.
                                        try:
                                                cmds.setAttr(shader + '.refl_brdf', -1)
                                                cmds.setAttr(shader + '.refl_base_brdf', -1)
                                        except:
                                                #Exception handle, the RedshiftArchitectural shader in Redshift v1.0 does not have the brdf combobox...
                                                pass

				
					#Use IOR
					if abrdf_fresnel == "True":
						cmds.setAttr(shader + '.brdf_fresnel', 1)
						#Fresnel Type
						if abrdf_fresnel_type == "Dielectric":
							cmds.setAttr(shader + '.brdf_fresnel_type', 0)
						else:
							cmds.setAttr(shader + '.brdf_fresnel_type', 1)
							cmds.setAttr(shader + '.brdf_extinction_coeff', float(abrdf_extinction_coeff))
					else:
						cmds.setAttr(shader + '.brdf_fresnel', 0)
						cmds.setAttr(shader + '.brdf_90_degree_refl', float(abrdf_90_degree_refl))
						cmds.setAttr(shader + '.brdf_curve', float(abrdf_Curve))


					#Use IOR (Secondary)
					if abrdf_base_fresnel == "True":
						cmds.setAttr(shader + '.brdf_base_fresnel', 1)
						#Fresnel Type
						if abrdf_base_fresnel_type == "Dielectric":
							cmds.setAttr(shader + '.brdf_base_fresnel_type', 0)
						else:
							cmds.setAttr(shader + '.brdf_base_fresnel_type', 1)
							cmds.setAttr(shader + '.brdf_base_extinction_coeff', float(abrdf_base_extinction_coeff))
					else:
						cmds.setAttr(shader + '.brdf_base_fresnel', 0)
						cmds.setAttr(shader + '.brdf_base_90_degree_refl', float(abrdf_base_90_degree_refl))
						cmds.setAttr(shader + '.brdf_base_curve', float(abrdf_base_Curve))


					# Common Reflection Attributes
					if arefl_is_metal == "True":
						cmds.setAttr(shader + '.refl_is_metal', 1)
					else:
						cmds.setAttr(shader + '.refl_is_metal', 0)
					cmds.setAttr(shader + '.hl_vs_refl_balance', float(ahl_vs_refl_balance))


					#Anisotropy Orientation
					if aanisotropy_orientation == "None":
						cmds.setAttr(shader + '.anisotropy_orientation', 2)
					elif aanisotropy_orientation == "From Tangent Channel":
						cmds.setAttr(shader + '.anisotropy_orientation', 1)			
					
					
					#AO
					print(aao_on, aao_combineMode)
					if aao_on == "True":
						cmds.setAttr(shader + '.ao_on', 1)
						if aao_combineMode == "Add":
							cmds.setAttr(shader + '.ao_combineMode', 0)
						elif aao_combineMode == "Multiply":
							cmds.setAttr(shader + '.ao_combineMode', 1)							
						#AO Colour
						aao_dark = aao_dark.translate(None, '[]')
						aao_dark=aao_dark.split(',', 2)
						val1=float(aao_dark[0])
						val2=float(aao_dark[1])
						val3=float(aao_dark[2])
						cmds.setAttr(shader + '.ao_dark', val1, val2, val3 ,type='double3')
						aao_ambient = aao_ambient.translate(None, '[]')
						aao_ambient=aao_ambient.split(',', 2)
						val1=float(aao_ambient[0])
						val2=float(aao_ambient[1])
						val3=float(aao_ambient[2])
						cmds.setAttr(shader + '.ao_ambient', val1, val2, val3 ,type='double3')
					else:
						cmds.setAttr(shader + '.ao_on', 0)

					#Incandescent Scale
					cmds.setAttr(shader + '.incandescent_scale', float(aIncandescent_Scale))
						
				#message complete
				cmds.inViewMessage( amg='<hl>Redshift</hl> Shader Transfer Completed', pos='midCenter', fade=True )

			#===============================================================================================================================================================================

			def shaderMask(blend_params, val):
				#Workaround to combine Shader Mask and Falloff layer
				blend_paramsStr = ','.join(blend_params) 
				fileNode = setTextureChannels(blend_paramsStr)
				channelName = blend_paramsStr.rsplit("#", 1)[0]
				
				shader_maskNode = cmds.shadingNode("layeredTexture", asTexture=True, n = nameSpace+str(geoName)+"_"+channelName+"_shaderMask" )				
				cmds.connectAttr('%s.outColor' %fileNode, '%s.inputs[0].color' %shader_maskNode)
				cmds.setAttr(shader_maskNode + ".alphaIsLuminance", 1)
				cmds.setAttr(shader_maskNode + ".inputs[0].blendMode", 4)
				# Make possible update only channels without affecting attributes that could had been tweaked in Maya.
				if (exportAttri == "True"):
					cmds.setAttr(shader_maskNode + ".inputs[0].alpha", val)
				
				return shader_maskNode;
			
						
			#we got this far...				

			print("All Inputs and Attributes transferred")			
			
			# If a Blended Shader is our final goal, connect the shaders created to the Blended Shader. Use shaderIndex-shaderCount to match the order of layers, so they will be exactly the same as in Mari.	
			if layeredShader != "none":
				if shaderType == "Ai Standard":
					if (shaderCount <= shaderIndex):												
						_attribute = '%s.inputs['+str(shaderCount)+'].color' #some bug naming in maya, has to do this way to work.
						try:
							cmds.connectAttr('%s.outColor' %shader, str(_attribute) %layeredShader)
						except:
							print("Material already connected to the LayeredShader!")
							
						val= float(blend_params[3])
						# Shader Mask in case of Layered Shader Network			
						if blend_params[4] != "none":								
							shader_maskNode = shaderMask(blend_params[4:-1], val);
							_attribute = '%s.inputs['+str(shaderCount)+'].transparency'
							try:
								cmds.connectAttr('%s.outTransparency' %shader_maskNode, str(_attribute) %layeredShader)
							except:
								print("Shader Mask already connected to the LayeredShader!")
						else:
							# Make possible update only channels without affecting attributes that could had been tweaked in Maya.
							if (exportAttri == "True"):
								val= 1.0-float(blend_params[3]) #have to reverse the values for the LayeredShader in Maya works like in Mari.
								cmds.setAttr(layeredShader + '.inputs['+str(shaderCount)+'].transparency', val,val,val, type='double3')
						
						cmds.setAttr(layeredShader + '.compositingFlag', 1)						
					print("connected " +str(shader)+ " to " +str(layeredShader))
					
				# Connect VRay shaders to the VRayBlendMtl Shader.		
				if shaderType == "VRay Mtl":					
					if (shaderCount == shaderIndex):
						# In case the user is upgrading from the default shader to the bump+normal we have to try to disconnect any previous connection from the default shader to the layered shader!
						try:
							cmds.disconnectAttr('%s.outColor' %shader, '%s.base_material' %layeredShader)
						except:
							pass
						# Now you can connect the normal+bump shader to the layered shader
						try:	
							cmds.connectAttr('%s.outColor' %shaderBump, '%s.base_material' %layeredShader)
						except:
							# If that is not possible than it's because you are only dealing with the default shader.
							try:								
								cmds.connectAttr('%s.outColor' %shader, '%s.base_material' %layeredShader)
							except:
								print("Material already connected to the LayeredShader!")
						
					else:
						_attribute = '%s.coat_material_'+str(shaderIndex-shaderCount-1) # some bug naming in maya, has to do this way to work.
						# In case the user is upgrading from the default shader to the bump+normal we have to try to disconnect any previous connection from the default shader to the layered shader!
						try:
							cmds.disconnectAttr('%s.outColor' %shader, str(_attribute) %layeredShader)
						except:
							pass
						# Now you can connect the normal+bump shader to the layered shader	
						try:	
							cmds.connectAttr('%s.outColor' %shaderBump, str(_attribute) %layeredShader)
						except:
							# If that is not possible than it's because you are only dealing with the default shader.
							try:								
								cmds.connectAttr('%s.outColor' %shader, str(_attribute) %layeredShader)
							except:
								print("Material already connected to the LayeredShader!")
							
						val=float(blend_params[3])
						# Shader Mask in case of Layered Shader Network						
						if blend_params[4] != "none":								
							shader_maskNode = shaderMask(blend_params[4:-1], val);
							_attribute = '%s.blend_amount_'+str(shaderIndex-shaderCount-1)
							try:
								cmds.connectAttr('%s.outColor' %shader_maskNode, str(_attribute) %layeredShader)
							except:
								print("Shader Mask already connected to the LayeredShader!")
						else:
							# Make possible update only channels without affecting attributes that could had been tweaked in Maya.
							if (exportAttri == "True"):
								cmds.setAttr(layeredShader + '.blend_amount_'+str(shaderIndex-shaderCount-1), val,val,val, type='double3')
						if (exportAttri == "True"):
							if ( str(blend_params[1]) != "Normal" ):
								cmds.setAttr(layeredShader + '.additive_mode', 1)
							
					print("connected " +str(shader)+ " to " +str(layeredShader))
					
				elif shaderType == "Redshift Architectural":
					if (shaderCount == shaderIndex):
						try:
							cmds.connectAttr('%s.outColor' %shader, '%s.baseColor' %layeredShader)
						except:
							print("Material already connected to the LayeredShader!")	
					else:
						_attribute = '%s.layerColor'+str(shaderIndex-shaderCount) # some bug naming in maya, has to do this way to work.
						try:
							cmds.connectAttr('%s.outColor' %shader, str(_attribute) %layeredShader)
						except:
							print("Material already connected to the LayeredShader!")
						val=float(blend_params[3])
						# Shader Mask in case of Layered Shader Network						
						if blend_params[4] != "none":								
							shader_maskNode = shaderMask(blend_params[4:-1], val);
							_attribute = '%s.blendColor'+str(shaderIndex-shaderCount)
							try:
								cmds.connectAttr('%s.outColor' %shader_maskNode, str(_attribute) %layeredShader)
							except:
								print("Shader Mask already connected to the LayeredShader!")	
						else:
							# Make possible update only channels without affecting attributes that could had been tweaked in Maya.
							if (exportAttri == "True"):
								cmds.setAttr(layeredShader + '.blendColor'+str(shaderIndex-shaderCount), val,val,val, type='double3')
						if ( str(blend_params[1]) != "Normal" ):
							_attribute = '.additiveMode'+str(shaderIndex-shaderCount) # some bug naming in maya, has to do this way to work.
							cmds.setAttr(layeredShader + str(_attribute), 1)						
					print("connected " +str(shader)+ " to " +str(layeredShader))
				
				# If shader that was created in the loop is hidden in MARI, than you have to delete it and his connections!
				if blend_params[-1] == "hidden":
					# Cleanup any connection to the LayeredShader that is used for Arnold cases.
					try:						
						cmds.removeMultiInstance(str(layeredShader)+'.inputs['+str(shaderCount)+']', b=True)
						print("Tried to delete Layered_Blend_mat.inputs: "+str(shaderCount))	
					except:
						pass
					
					#get Mask node that is connected to the layered shader of hidden material
					try:						
						maskNodes=cmds.listHistory(nameSpace+geoName+"_"+curShaderStr+"_mask_layer")
						check=cmds.ls(maskNodes)
						# delete them			
						try:
							cmds.delete(check)
							print("deleted old mask Shader node that was used in the Mari hidden shader")	
						except TypeError:
							pass
					except:
						pass
					
					# Deletes the hidden material and the down nodes connected to it! 
					try:				
						#get downnodes from material that is hidden
						if cmds.objExists(nameSpace+"mGo_" + curShaderStr + "_Bump_mat") ==True:
							_curShader = nameSpace+"mGo_" + curShaderStr+"_Bump_mat"
						else:
							_curShader = nameSpace+"mGo_" + curShaderStr+"_mat"
							
						downNodes=cmds.listHistory(_curShader)						
						check=cmds.ls(downNodes)						
						# delete them			
						try:
							cmds.delete(check)
							print("deleted old file nodes and shader that in Mari is hidden")	
						except TypeError:
							pass	
						
					except ValueError:
						print("shader is not here")					
					
				# Pass the Blend Material as shader so it could be assigned to objects in scene after the loops end, as well all the file nodes could have their alpha luminance and filter set!					
				shader = layeredShader				
				
			# So layered shader is not our final goal. Assign the single shader to the SG instead.
			elif curShaderStr != "channels_list":
				# If the shaderBump is our final goal.
				if (Bump != "none") and (Normal != "none"):
					# Assign the VRay Shader Bump to the surfaceShader in the SG.
					if shaderType == "VRay Mtl":
						# In case the user is upgrading from the default shader to the bump+normal we have to try to disconnect any previous connection from the default shader to the SG!
						try:
							cmds.disconnectAttr('%s.outColor' %shader, '%s.surfaceShader' %sgName)
						except:
							pass	
						# Now you can connect the normal+bump shader to the Shading Group
						try:
							cmds.connectAttr('%s.outColor' %shaderBump ,'%s.surfaceShader' %sgName)
							shader = shaderBump
							print("connected material to SG")
						except:
							print("Material already connected to the Shading Group!")
							
					# if it's not vray, assign only the default shader.		
					else:					
						try:
							cmds.connectAttr('%s.outColor' %shader ,'%s.surfaceShader' %sgName)
							print("connected material to SG")
						except:
							print("Material already connected to the Shading Group!")
							
				# The normal+bump shader is not our goal! Assign only the default shader.
				else:
					try:
						cmds.connectAttr('%s.outColor' %shader ,'%s.surfaceShader' %sgName)
						print("connected material to SG")
					except:
						print("Material already connected to the Shading Group!")
			#Non-shader support!
			else:
				try:
					cmds.connectAttr('%s.outColor' %channelsContainer ,'%s.surfaceShader' %sgName)
					print("connected material to SG")
				except:
					print("Material already connected to the Shading Group!")
				
				
		shaderCount +=1
	# <------------------------- FINISH OF THE WHILE LOOP RESPONSIBLE FOR CREATE THE MANY SHADERS IN THE LAYERED SHADER ------------------------->	
	
	if (exportAttri == "True" or exportChannel == "True"):
		#print filtering settings
		if filtering == "Off":
			print("filter set to off")
		elif filtering == "Mipmap":
			print("filter set to mipmap")
		else:
			print("filter set to default")
	
	if exportObj == "True":
		#Select the object imported
		try:
			# In case we are using Arnold, uncheck the opaque option for the object we are importing with the arnold shader, so if he have properties such as refraction or anything related they will render correctly.
			if shaderType == "Ai Standard":
				cmds.setAttr(nameSpace+str(geoName)+'.aiOpaque', 0)
		except:
			pass
		if (exportAttri == "True" or exportChannel == "True"):
			#connect shader to object
			try:
				cmds.select(nameSpace+str(geoName))
				cmds.hyperShade(assign=shader)
				print("connected to object, only took 1 go")
			except NameError:
				# I think this is not necessary any more. The first try seams to be wide trust-able move.
				try:
					cmds.select(nameSpace+getObjB)
					cmds.hyperShade(assign=shader)
					print("ok, got it this time, took 2 goes")

				except NameError:
					print("object doesn't exist in scene so unable to assign shader")
					#create option to select object and assign material
	else:
		# Try to assign the shader to a Geo that has the same name as the Obj used in Mari. 
		# This would cover the case that you already have the Geo in your Maya scene, and just want to send the shader and have it assigned automatically by comparing the Geo and Obj names between Mari and Maya.
		if (exportAttri == "True" or exportChannel == "True"):
			#connect shader to object
			try:
				if cmds.objExists(nameSpace+str(geoName)) ==True:
					cmds.select(nameSpace+str(geoName))
					cmds.hyperShade(assign=shader)
					print("connected to object, only took 1 go")
			except NameError:
				pass
	
	
	if (exportAttri == "True" or exportChannel == "True"):
		cmds.select(shader)
	
	if shaderType == "Ai Standard":
		try:
			#mel.eval('updateRendererUI')
			#cmds.callbacks(executeCallbacks=True, hook='updateMayaRenderingPreferences')
			#Set linear workflow, so it matches Mari's workflow
			cmds.setAttr("defaultArnoldRenderOptions.light_gamma", 1)
			cmds.setAttr("defaultArnoldRenderOptions.shader_gamma", 1)
			cmds.setAttr("defaultArnoldRenderOptions.texture_gamma", 1)
			
			if envLight_data[-1] != "hidden":
				# In case we are using Arnold, try again to reconnect the aiSky to the background in the render settings. Sometimes the render tab does load up fast enough to allow the script to connect it.
				if envLight_data[0] != "none":
					cmds.connectAttr('MARI_aiSkyShape.message', 'defaultArnoldRenderOptions.background')
		except:
			pass
	
	print("Finished mGo import process.")
	

def autoLoad(projectDescriptionFilePath):
	try:
		print("------------- mGo Auto Load -------------")
		
		projectDescriptionFilePath = projectDescriptionFilePath.replace( "\\", "/" )
		print(projectDescriptionFilePath)
		if projectDescriptionFilePath.rsplit("/", 1)[-1] == "Project_description.mgo":
			f = open(projectDescriptionFilePath, 'r')
			config = pickle.load(f)
			f.close()
			
			# Load each Description found
			for sceneDescriptionFilePath in config:
				try:
					sceneDescriptionFilePath = sceneDescriptionFilePath
					print("Description Path: '" + sceneDescriptionFilePath.rsplit("/",1)[0] + "/'")
					filePath = sceneDescriptionFilePath.rsplit("/",1)[0] + "/"
					print("Description File name: '" + filePath + "'")
					runConfig(sceneDescriptionFilePath, filePath)
				except:
					pass
					
		else:
			#Path to where the file related to the shaders is located, which is the same folder where the Descriptions are saved.
			sceneDescriptionFilePath = projectDescriptionFilePath
			filePath = sceneDescriptionFilePath.rsplit("/",1)[0] + "/"
			runConfig(sceneDescriptionFilePath, filePath)
	
	except:
		pass

	
def loadSceneDesc(sceneDescriptionFilePath):
	try:	
		filePath = sceneDescriptionFilePath.rsplit("/",1)[0] + "/"
		print("Description File name: '" +sceneDescriptionFilePath.rsplit("/",1)[1] +"'")
		
		runConfig(sceneDescriptionFilePath, filePath)
	except:
		pass
