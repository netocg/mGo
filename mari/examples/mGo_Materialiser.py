# ------------------------------------------------------------------------------
#    SCRIPT            materialiser.py
#
#    AUTHOR	           Stuart Tozer
#                      stutozer@gmail.com
#					
#	 CONTRIBUTOR	   Antonio Lisboa M. Neto
#					   netocg.fx@gmail.com
#
#    DATE:             October, 2014 - July 2015
#
#    DESCRIPTION:      Mari import and export Custom OpenGL Shaders
#
#    VERSION:          3.0
#
#-----------------------------------------------------------------

import mari
import os
import pickle
import PySide2
from PySide2 import QtCore, QtGui, QtWidgets
	
widgets = PySide2.QtWidgets
gui = PySide2.QtGui
		
		
def runMaterialiser():
	# Mari Paths
	mariPath=mari.resources.path('MARI_USER_PATH')
	mariPath = mariPath.replace( "\\", "/" ).rstrip( "/" )
		
	userPath=mari.resources.path('MARI_USER_PATH')
	userPath = userPath.replace( "\\", "/" ).rstrip( "/" )
	materialiserDir = userPath + "/mGo/Presets"
		
	#create Preset folder if it doesn't exist
	if not os.path.exists(materialiserDir):
		os.makedirs(materialiserDir)
	#create shaderType folder if it doesn't exist
	shaderTypes = ['Arnold', 'Redshift', 'Vray']
	for shaderType in shaderTypes:	
		if not os.path.exists(materialiserDir+"/"+shaderType):
			os.makedirs(materialiserDir+"/"+shaderType)
			os.makedirs(materialiserDir+"/"+shaderType+"/example")
	
	
	# ------------------------------------------------------------------------------
	# Create main UI
	# ------------------------------------------------------------------------------
	
	global materialiser_window

        materialiser_window = widgets.QDialog()
        layout = widgets.QVBoxLayout()
	materialiser_window.setLayout(layout)
	materialiser_window.setWindowTitle("mGo! Materialiser")	
	
	
	#add Shader Type menu
        shaderType_layout = widgets.QHBoxLayout()
	
        shaderType_text = widgets.QLabel('Shader Type:')
        shaderType_combo = widgets.QComboBox()
	shaderType_combo.setMinimumWidth(140)
	shaderType_combo.setMaximumWidth(140)
	shaderType_combo.setToolTip("Choose a Shader Type that represents the materials you are going to create")
	
	shaderType_layout.addWidget(shaderType_text)
	shaderType_layout.addWidget(shaderType_combo)	
	
	#add Library menu
        library_layout = widgets.QHBoxLayout()
	
        library_text = widgets.QLabel('Library:')
        library_combo = widgets.QComboBox()
	library_combo.setMinimumWidth(140)
	library_combo.setMaximumWidth(140)

	library_combo.setToolTip("Choose a Library. Libraries are subFolders residing inside mGo/Presets Directory.")
	
	library_layout.addWidget(library_text)
	library_layout.addWidget(library_combo)	
	
	#add presets menu
        presets_layout = widgets.QHBoxLayout()
	
        presets_text = widgets.QLabel('Preset:')
        presets_combo = widgets.QComboBox()
	presets_combo.setMaximumWidth(140)
	presets_combo.setMinimumWidth(140)
	presets_combo.setToolTip("Choose the Material Preset")
	
	presets_layout.addWidget(presets_text)
	presets_layout.addWidget(presets_combo)
	
	
	#channel Res Options	
	chanResOptions = ['512', '1024', '2048', '4096', '8192']
	bitDepthOptions = ['8', '16']
	
	#New Channels Options
        channels_layout = widgets.QHBoxLayout()
	
        chanSize_text = widgets.QLabel('Chan Resolution:')
        chanSize_combo = widgets.QComboBox()
	chanSize_combo.setToolTip("Channel Resolution")
	
	for res in chanResOptions:
		chanSize_combo.addItem(res)
	
	chanSize_combo.setCurrentIndex(chanSize_combo.findText('2048'))
	
        bitDepth_text = widgets.QLabel('Bit Depth:')
        bitDepth_combo = widgets.QComboBox()
	bitDepth_combo.setToolTip("Channel Bit Depth")
	
	for bit in bitDepthOptions:
		bitDepth_combo.addItem(bit)
	
	channels_layout.addWidget(chanSize_text)
	channels_layout.addWidget(chanSize_combo)
	channels_layout.addWidget(bitDepth_text)
	channels_layout.addWidget(bitDepth_combo)
	
	#add Save/Preview/add_channels Button	
        button_layout = widgets.QHBoxLayout()
	
        save_button = widgets.QPushButton("Save")
        save_button_icon = gui.QIcon(mari.resources.path(mari.resources.ICONS) + '/SaveFile.png')
	save_button.setToolTip('Saves attributes of current shader to file. Choose or create a new folder (as a new Library) inside mGo/Presets Directory.')
	save_button.setIcon(save_button_icon)
	
	mari.utils.connect(save_button.clicked, lambda: saveFile())
	
        add_channels = widgets.QPushButton("Add Channels")
        add_channels_icon = gui.QIcon(mari.resources.path(mari.resources.ICONS) + '/AddChannel.png')
	add_channels.setIcon(add_channels_icon)
	add_channels.setToolTip("Select entries from the Inputs list that you would like to add as Channels. Channels are created with values taken from the relevant Attribute in the Preset.")
		
	add_channels.setEnabled(False)
	
	button_layout.addWidget(save_button)	
	button_layout.addWidget(add_channels)	

	#-------------------------- Add Channels UI--------------------------
        channel_label = widgets.QLabel('Inputs:')
        channel_header = widgets.QHBoxLayout()
	channel_header.addWidget(channel_label)
	
        inputs_layout = widgets.QHBoxLayout()
        inputs_list = widgets.QListWidget()
	inputs_list.setSelectionMode(inputs_list.ExtendedSelection)
	inputs_list.setToolTip("Select the Channels you would like to create.")
	inputs_layout.addWidget(inputs_list)


	#preview overwrite checkbox
        prevImport_layout = widgets.QHBoxLayout()
        prevImportCbox = widgets.QCheckBox()
	prevImport_layout.addWidget(prevImportCbox)
	
	#layout All Items
	layout.addLayout(shaderType_layout)
	layout.addLayout(library_layout)
	layout.addLayout(presets_layout)	
	layout.addLayout(channel_header)	
	layout.addLayout(inputs_layout)
	layout.addLayout(channels_layout)	
	layout.addLayout(button_layout)

	
	#------------------------------------------------
	
	shaderType_combo.clear()
	library_combo.clear()
	presets_combo.clear()
					
	
	# Load Materialiser config and set last used path
	try:
		logLastUsedDir = mariPath + "/mGo/Presets/Materialiser_log.txt"
		with open(logLastUsedDir, 'r') as f:
            config = pickle.load(f)
		
		lastUsedPath = config[:] # weird set but it work
		lastUsedSub_dir = lastUsedPath.rsplit('/', 1)[0]
		lastUsedDirectory = lastUsedSub_dir.rsplit('/', 1)[0]
		materialiserDir = lastUsedDirectory.rsplit('/', 1)[0]
		selected_sub_dir_path = os.listdir(lastUsedPath.rsplit('/', 1)[0])	
		lastUsedPath = lastUsedPath.split('/')
	except:
		pass	
		
	directories_path = os.listdir(materialiserDir)
	
	
	#Identify the directories that are named accordingly to the shaders type
	for directory in directories_path:
		#skip any file inside of the directory.
		checkDir = os.path.join(materialiserDir, directory)
		if os.path.isdir(checkDir):			
			shaderType_combo.addItem(directory)
			#Try to pick last used shaderType.
			try:
				shaderType_combo.setCurrentIndex( shaderType_combo.findText(lastUsedPath[-3]) )
			except:
				pass
				
	shaderTypeDir = shaderType_combo.currentText()
	selected_directory_path = os.listdir(materialiserDir +"/"+ shaderTypeDir)
	
	# Categorize the materials by Sub-directories inside of the Shader Type Directory
	for sub_dir in selected_directory_path:
		#skip any file inside of the diretory.
		checkDir = os.path.join(materialiserDir +"/"+ shaderTypeDir, sub_dir)

		if os.path.isdir(checkDir):
			library_combo.addItem(sub_dir)

			#Try to set last used library
			try:	
				library_combo.setCurrentIndex( library_combo.findText(lastUsedPath[-2]) )
			except:
				pass		
		
	libraryDir = library_combo.currentText()	
	selected_sub_dir_path = os.listdir(materialiserDir +"/"+ shaderTypeDir +"/"+ libraryDir)
	
	
	# List of possible prefix names that a preset could use, including his own home directory
	prefix_possibilities = [shaderTypeDir, "ARNOLD", "Arnold", "ARND", "Arnd", "arnd", "AR", "Ar", "ar", "VR", "Vr", "vr", "VRAY", "Vray", "vray", "V-RAY", "V-Ray", "V-ray", "v-ray", "RS", "Rs", "rs", "REDSHIFT", "Redshift", "redshift"]
		
	# first item of the presets list
	item_name = "--- Select Preset ---"
	presets_combo.addItem(item_name)
	
	# Get the Presets Items in for the library in the selected sub-directory
	for items in selected_sub_dir_path:
		item_name = items
		try:			
			# replace "_" to display nice names in the menu
			filename = items.replace("_", " ")			
			# In case the prefix is something like "V-ray - shader_name.pre" we replace the " - " by single " " space
			filename = filename.replace(" - ", " ", 1)
			item_name = filename
			# split the item name to separete any possible shader type defined in the begging of the item file name
			filename = filename.split(" ", 1)			
			# Get out the prefix name from the item file name, if it matchs the selected shader type name
			for prefix_test in prefix_possibilities:	
				if (filename[0] == prefix_test):					
					#skip the prefix[0]
					item_name = filename[1]					
					break	
				
			#get out of the sufix .pre
			item_name = item_name.rsplit('.', 1)
				
		except IndexError:
			pass
		
		# add each item interation to the combobox, avoid items that are not '.pre'
		if item_name[1] == "pre":	
			presets_combo.addItem(item_name[0])		
		
	
	# set function for combobox indexchange
	if mari.projects.current() != None:
		shaderType_combo.activated[int].connect(lambda: update_shaderType())
		library_combo.activated[int].connect(lambda: update_subDir())
		presets_combo.activated[int].connect(lambda: previewFile())
	else:
		print("Please open a project first.")
		
	# Display
	materialiser_window.show()
	
	#Start the preview checkbox empty
	presets_combo.setCurrentIndex(0)	
	prevImportCbox.setCheckState(QtCore.Qt.Unchecked)	
	print("----------- Materialiser Initiated -----------")	
	
	
	#------------------------------------------------------------------------------------------------
	# Initialize Variables that will be keep after each interaction.	
	shaderType = []
	curShader = []
	curShaderStr = []	
	newShader = []
	global geo
	geo = mari.geo.current()

	# Somtimes the layered Shader UI doesn't update, displaying the sliders of the newest current selected shader created.
	def layeredShader_update_UI_list():
		try:						
			if geo.currentShader().isLayeredShader():	
				shaderList = geo.currentShader().channelList()[0].layerList()				
				# Make sure you to unselect any shader from the list!
				#shaderList[0].shader().makeCurrent() This would skip the layered shader and create a new single shader outside of the Shader Layeres UI of the layered shader. 
				#shaderList[0].shader().makeCurrent() Could be useful for other things maybe later on, and skip any avoid if we frind some...
				for shader in shaderList:
					# select the top shader of the layered shader list.				
					if shader == shaderList[0]:
						shader.makeCurrent()
						shader.setSelected(True)				
					else:
						shader.setSelected(False)				
		except:
			pass
		
	# try to update the UI, just in case the user is been adding shaders too fast and opening and closing the materialiser.
	layeredShader_update_UI_list()	
	
	
	def update_subDir():	

		# clear presets combobox
		presets_combo.clear()		
		
		# first item of the presets list
		item_name = "--- Select Preset ---"
		presets_combo.addItem(item_name)
		
		shaderTypeDir = shaderType_combo.currentText()
		
		libraryDir = library_combo.currentText()	
		selected_sub_dir_path = os.listdir(materialiserDir +"/"+ shaderTypeDir +"/"+ libraryDir)
		
		# Update the Presets Items of the sub-directory from the new selected library in the combobox
		for items in selected_sub_dir_path:
			item_name = items
			try:			
				# replace "_" to display nice names in the menu
				filename = items.replace("_", " ")			
				# In case the prefix is something like "V-ray - shader_name.pre" we replace the " - " by single " " space
				filename = filename.replace(" - ", " ", 1)
				item_name = filename
				# split the item name to separete any possible shader type defined in the begging of the item file name
				filename = filename.split(" ", 1)
				# Get out the prefix name from the item file name, if it matchs the selected shader type name
				for prefix_test in prefix_possibilities:	
					if (filename[0] == prefix_test):					
						#skip the prefix[0]
						item_name = filename[1]
						break	
					
				#get out of the sufix .pre
				item_name = item_name.rsplit('.', 1)
					
			except IndexError:
				pass
				
			# add each item interation to the combobox, avoid items that are not '.pre'
			if item_name[1] == "pre":	
				presets_combo.addItem(item_name[0])
		
		prefix_possibilities.append(shaderTypeDir)
		
	
	def update_shaderType():
		# clear the library and presets comboboxes so it could get the new subdirectories and their items		
		library_combo.clear()
		presets_combo.clear()		
		
		# first item of the presets list
		item_name = "--- Select Preset ---"
		presets_combo.addItem(item_name)
		
		shaderTypeDir = shaderType_combo.currentText()	
		selected_directory_path = os.listdir(materialiserDir +"/"+ shaderTypeDir)
		
		# Update the library combobox accondingly to the sub-dir inside of the new selected shader type in the combobox
		for sub_dir in selected_directory_path:
			#skip any file inside of the diretory.
			checkDir = os.path.join(materialiserDir +"/"+ shaderTypeDir, sub_dir)
			if os.path.isdir(checkDir):
				library_combo.addItem(sub_dir)
		
		update_subDir();	
		
		
	def previewFile():
		# If you have just finished saving a shader, this text will be displayed at the Presets combobox. Get rid of it as soon as the user click on this combobox. 		
		msg = "--- Preset Saved ---"
		presets_combo.removeItem( presets_combo.findText(msg) )
		
		# First item of the presets list should not be selected.
		if presets_combo.currentText() == "--- Select Preset ---":
			return		
			
			
			
		update_previewShader=[]
		
		if prevImportCbox.isChecked() == False:
			print("--------------------------------------------")
			print("Creating a shader to preview the presets")
			update_previewShader = "False"			
		else:
			print("--------------------------------------------")
			print("Updating your shader to the selected presets")
			update_previewShader = "True"
			
		if update_previewShader == "True":
			layeredShader_update_UI_list()	
		
		prevImportCbox.setCheckState(QtCore.Qt.Checked)		
		
		shaderTypeDir = (shaderType_combo.currentText())
		libraryDir = (library_combo.currentText())
		currentPreset = (presets_combo.currentText())		
		
			
		file_paths = os.listdir(materialiserDir +"/"+ shaderTypeDir +"/"+ libraryDir)
		
		prefix_possibilities.append(shaderTypeDir)
		
		# Repeat the same steps again to find out what is the original item_name of the current preset displayed combobox
		original_item_name = []
		for items in file_paths:			
			try:			
				# replace "_" to display nice names in the menu
				filename = items.replace("_", " ")			
				# In case the prefix is something like "V-ray - shader_name.pre" we replace the " - " by single " " space
				filename = filename.replace(" - ", " ", 1)
				item_name = filename
				# split the item name to separete any possible shader type defined in the begging of the item file name
				filename = filename.split(" ", 1)
				# Get out the prefix name from the item file name, if it matchs the selected shader type name
				for prefix_test in prefix_possibilities:	
					if (filename[0] == prefix_test):					
						#skip the prefix[0]
						item_name = filename[1]
						break	
					
				#get out of the sufix .pre
				item_name = item_name.rsplit('.', 1)[0]
				
				# item_name identified it match the name in the preset combobox, pass this as var, so we can locate the file in the structure folders.
				if (item_name == currentPreset):
					original_item_name = items					
					print(original_item_name)
			
			except IndexError:				
				pass
		
		
		filename = materialiserDir + "/" + shaderTypeDir + "/" + libraryDir + "/" + original_item_name		
		filename = filename.replace( "\\", "/" ).rstrip( "/" )		
		
		# <------------------------ Log last path used ------------------------>
		#Use this to make materialiser always remember the last shaderType and library folder selected by the user.			
		configData = (filename)
		pathfile = mariPath + "/mGo/Presets/Materialiser_log.txt"
		with open(pathfile, 'w') as f:
            pickle.dump(configData, f)
		
		
		#Open the preset file select
		with open(filename, 'r') as f:
            config = pickle.load(f)		
		
		
		# Global configs load
		shaderType = config[0]
		# curShaderStr = config[1]
		curShaderStr = original_item_name.split(".pre")[0]
		curShaderStr = curShaderStr.replace(" ", "_")
		
		# Load config from file accondingly to the shaderType selected
		if shaderType == "Ai Standard":
			# Load config for Arnold Shaders
			shaderInternalName = config[1]	
			aDiffuseColor = config[2]
			aDiffuseWeight = config[3]
			aDiffuseRoughness = config[4]
			aBacklighting = config[5]
			aDiffuseFresnel = config[6]
			aSpecularColor = config[7]
			aSpecularWeight = config[8]
			aSpecularRoughness = config[9]
			aAnisotropy = config[10]
			aRotation = config[11]
			aFresnel_On = config[12]
			aReflectance = config[13]
			aReflectionColor = config[14]
			aReflectionWeight = config[15]
			aFresnel_On_Ref = config[16]
			areflReflectance = config[17]
			aRefractionColor = config[18]
			aRefractionWeight = config[19]
			aIOR = config[20]
			aRefractionRoughness = config[21]			
			aFresnel_useIOR = config[22]
			aTransmittance = config[23]
			aOpacity = config[24]
			aSSSColor = config[25]
			aSSSWeight = config[26]
			aSSSRadius = config[27]
			aEmissionColor = config[28]
			aEmission = config[29]
					
		elif shaderType == "VRay Mtl":
			# Load config for Vray Shaders
			shaderInternalName = config[1]	
			aDiffuseColor = config[2]
			aDiffuseAmount = config[3]
			aOpacity_Map = config[4]
			aDiffuseRoughness = config[5]
			aSelf_Illumination = config[6]
			aBRDF_Model = config[7]
			aReflectionColor = config[8]
			aReflectionAmount = config[9]
			aLock_Highlight_Refle_gloss = config[10]
			aHighlightGlossiness = config[11]
			aReflectionGlossiness = config[12]
			aFresnel_On = config[13]
			aFresnel_useIOR = config[14]
			aReflection_IOR = config[15]
			aggxTailFalloff = config[16]
			aAnisotropy = config[17]
			aRotation = config[18]
			aRefractionColor = config[19]
			aRefractionAmount = config[20]
			aRefractionGlossiness = config[21]
			aIOR = config[22]
			aFog_Color = config[23]
			aFog_multiplier = config[24]
			aFog_bias = config[25]
			aSSS_On = config[26]
			aTranslucency_Color = config[27]
			aFwd_back_coeff = config[28]
			aScatt_coeff = config[29]
					
		elif shaderType == "Redshift Architectural":
			# Load config for Redshift Shaders
			shaderInternalName = config[1]	
			adiffuse_color = config[2]
			adiffuse_weight = config[3]
			adiffuse_roughness = config[4]
			arefr_translucency = config[5]
			arefr_trans_color = config[6]
			arefr_trans_weight = config[7]
			arefl_weight = config[8]
			arefl_color = config[9]
			arefl_gloss = config[10]
			abrdf_fresnel = config[11]
			abrdf_fresnel_type = config[12]
			abrdf_extinction_coeff = config[13]
			abrdf_0_degree_refl = config[14]
			abrdf_90_degree_refl = config[15]
			abrdf_Curve = config[16]
			arefl_base_weight = config[17]
			arefl_base_color = config[18]
			arefl_base_gloss = config[19]
			abrdf_base_fresnel = config[20]
			abrdf_base_fresnel_type = config[21]
			abrdf_base_extinction_coeff = config[22]
			abrdf_base_0_degree_refl = config[23]
			abrdf_base_90_degree_refl = config[24]
			abrdf_base_Curve = config[25]
			arefl_is_metal = config[26]
			ahl_vs_refl_balance = config[27]
			aanisotropy = config[28]
			aanisotropy_rotation = config[29]
			aanisotropy_orientation = config[30]
			atransparency = config[31]
			arefr_color = config[32]
			arefr_gloss = config[33]
			arefr_ior = config[34]
			arefr_falloff_on = config[35]
			arefr_falloff_dist = config[36]
			arefr_falloff_color_on = config[37]
			arefr_falloff_color = config[38]
			aao_on = config[39]
			aao_combineMode = config[40]
			aao_dark = config[41]
			aao_ambient = config[42]
			acutout_opacity = config[43]
			aadditional_color = config[44]
			aIncandescent_Scale = config[45]	
			
		
		#Create the shaders accordingly to it's type.
		def create_newShader(shaderType):						            
			curShader = []			
				
			if geo.currentShader().isLayeredShader():        
				channels = geo.currentShader().channelList()				
				if shaderType == "Ai Standard":
					newShader = channels[0].createShaderLayer(curShaderStr, geo.createStandaloneShader(curShaderStr,"Lighting/Standalone/AiStandard"))				
				elif shaderType == "VRay Mtl":
					newShader = channels[0].createShaderLayer(curShaderStr, geo.createStandaloneShader(curShaderStr,"Lighting/Standalone/VRayMtl"))				
				elif shaderType == "Redshift Architectural":
					newShader = channels[0].createShaderLayer(curShaderStr, geo.createStandaloneShader(curShaderStr,"Lighting/Standalone/RedshiftArchitectural"))				
				
				curShader = newShader.shader()				
			else:
				if shaderType == "Ai Standard":
					newShader = geo.createStandaloneShader(curShaderStr,"Lighting/Standalone/AiStandard"); 
				elif shaderType == "VRay Mtl":
					newShader = geo.createStandaloneShader(curShaderStr,"Lighting/Standalone/VRayMtl"); 
				elif shaderType == "Redshift Architectural":
					newShader = geo.createStandaloneShader(curShaderStr,"Lighting/Standalone/RedshiftArchitectural");				
		
			if geo.currentShader().isLayeredShader():
				# While Mari is waiting to Load a shader in viewport this function will not work properly!
				#layeredShader_update_UI_list()
				pass
			else:
				# select the new single shader created.
				newShader.makeCurrent()
				curShader = geo.currentShader()
			
			print("Creating: '" +curShader.name()+ "' shader.")			
			return curShader;		
		
		
		# Definitions to rework the values from a color and reassign them back.
		def set_mariColor(attributeColor):
			invalid = ["(", ")", "[", "]"]
			replacement = ""
			for x in invalid:
			    attributeColor=attributeColor.replace(x, replacement)

			aColor= attributeColor.split(',', 2)
			
			val1=float(aColor[0])
			val2=float(aColor[1])
			val3=float(aColor[2])			
			aColor = mari.Color(val1, val2, val3)
			
			return aColor;
		
		
		def create_channels(curShader, input_channel, chanRes, bitDepth, aParameter, newShader_name, killed_curShaderStr):			
			# Maybe the user had switch the shader Type so we may have to compare old names in order to change the channel name accordingly.
			_ShaderName = []
			if geo.currentShader().isLayeredShader():
				_ShaderName = geo.currentShader().channelList()[0].layerList()[0].name()
			else:
				_ShaderName = geo.currentShader().name()
				
			if (update_previewShader == "True") and (shaderKilled == "True"):	
				_ShaderName = killed_curShaderStr				
			
			# If it's update, seeks the channel to avoid an error because you may already have a Channel with the same name
			if update_previewShader == "True":				
				for chan in geo.channelList():
					if chan.name() == (_ShaderName +"_"+ input_channel):
						chan.setName( newShader_name +"_"+ input_channel )					
						for layer in chan.layerList():
							chanColor = aParameter		
							layer.setProceduralParameter("Color", chanColor)							
						break				
			else:
				# We tried to combine those if/try into one shot, but without the if update things break in some cases! 
				# So we had to keep a bit more repeated code here.
				try:
					chan = geo.createChannel(_ShaderName +"_"+ input_channel, chanRes, chanRes, bitDepth)
					chanLayer = chan.createProceduralLayer("Reference_Colour", "Basic/Color")
					chanColor = aParameter		
					chanLayer.setProceduralParameter("Color", chanColor)
				except:
					# The geo may have a channel with the same name, even on the beginning if it does, just pass it's info					
					for chan in geo.channelList():
						if chan.name() == (_ShaderName +"_"+ input_channel):
							chan.setName( newShader_name +"_"+ input_channel )					
							for layer in chan.layerList():
								chanColor = aParameter		
								layer.setProceduralParameter("Color", chanColor)							
							break			
			
			geo.currentShader().setInput(input_channel, chan)
			
			#Convert Created Channels to Linear Colorspace.
			linearChannels = ['DiffuseAmount', 'DiffuseWeight', 'diffuse_weight', 'DiffuseRoughness', 'Backlighting', 'refr_trans_weight', 'SpecularWeight', 'SpecularRoughness', 'Anisotropy', 'Rotation', 'Reflectance', 'reflReflectance', 'Reflection_IOR', 'ReflectionAmount', 'RefractionRoughness', 'HighlightGlossiness', 'ReflectionGlossiness', 'RefractionAmount', 'transparency', 'RefractionGlossiness', 'SSSWeight', 'IOR', 'diffuse_roughness', 'refl_weight', 'refl_base_weight', 'brdf_0_degree_refl', 'brdf_base_0_degree_refl', 'refl_gloss', 'refl_base_gloss', 'anisotropy', 'anisotropy_rotation', 'refr_gloss', 'refr_ior', 'Bump', 'Normal', 'Displacement']
			for linearChannel in linearChannels:
				if input_channel == linearChannel:
					curChan = mari.current.channel()
					curConfig = curChan.colorspaceConfig()

					# MODIFYING OUTPUT STAGE OF CHANNELS COLOR SPACE CONFIG
					curConfig.setColorspace(mari.ColorspaceConfig.COLORSPACE_STAGE_NATIVE,'linear')

					curChan.setColorspaceConfig(curConfig)			
			
			return
		
		
		# Pass the signal that the old shader has to be Killed instead of just update!
		geo = mari.geo.current()
		curShader = geo.currentShader()
		# Avoid issues if you don't have any shader selected! It happen when you delete shaders too fast!!!
		killed_curShaderStr = []		
		try:
			killed_curShaderStr = curShader.name()
		except:			
			geo.setCurrentShader(geo.findShader("Current Channel"))
			
		old_shader = []
		shaderKilled = "False"
		if update_previewShader == "True":
			if geo.currentShader().isLayeredShader():
				# Old shader and his name from the layered shader list
				curShader = geo.currentShader().channelList()[0].layerList()[0].shader()
				killed_curShaderStr = geo.currentShader().channelList()[0].layerList()[0].name()
				try:
					channels = geo.currentShader().channelList()
					newShader = channels[0].layerList()				
					curShader = newShader[0].shader()
					if str(curShader.getParameter("shadingNode")) != shaderType:						
						old_shader = channels[0]
						# Kill the top shader from the layered shader list. The top shader is always the last shader created by the materialiser.
						channels[0].removeLayers(channels[0].layerList()[0:1])
						print("--------- Layered Shader detected ----------")
						print("Overwriting Shader from the Top of the stack")
						shaderKilled = "True"
						curShader = []
				except:
					pass
			else:
				try:
					if str(curShader.getParameter("shadingNode")) != shaderType:
						old_shader = curShader
						#geo.removeShader(curShader) The shader should only be Killed after creating a new one in order to avoid problems.						
						print("--ALERT-- Different Shader Type detected ---------")
						print("----------- Overwriting the old shader -----------")
						shaderKilled = "True"
						curShader = []	
				except:
					lastShaderName = geo.shaderList()[-1].name()
					geo.setCurrentShader( geo.findShader(lastShaderName) )
					old_shader = geo.currentShader()
					killed_curShaderStr = old_shader.name()
					print("--ALERT-- Different Shader Type detected ---------")
					print("----------- Overwriting the old shader -----------")
					shaderKilled = "True"
					curShader = []	
					pass	
		
		# Check if the Shader is just going to be update or if it need to be created. If the shader has been killed go create a new one!
		if (update_previewShader == "True") and (shaderKilled == "False"):
			#If the geo has changed in the middle of the process then update the variable 'geo' to the new geo selected
			if geo != mari.geo.current():
				geo = mari.geo.current()
				update_previewShader = "False"
				shaderKilled = "False"
				curShader = create_newShader(shaderType)
				
			# If the current Shader is a LayeredShader, get the top shader from it's list
			elif geo.currentShader().isLayeredShader():  
				try:
					channels = geo.currentShader().channelList()
					newShader = channels[0].layerList()				
					curShader = newShader[0].shader()
					if str(curShader.getParameter("shadingNode")) == shaderType:
						pass
				except:
					curShader = create_newShader(shaderType)
			#Single shader update!
			else:
				try:
					if str(curShader.getParameter("shadingNode")) == shaderType:
						pass
				except:						
					curShader = create_newShader(shaderType)
					
		#Not updating the shader preview but creating a new shader!
		else:				
			curShader = create_newShader(shaderType)
				
				
		# Set the Shader accordingly to the parameters loaded of the preset selected.
		if shaderType == "Ai Standard":
		
			
			#---------- Set the Shader Attributes ----------
			
			#DifCol
			aDiffuseColor = set_mariColor(aDiffuseColor)					
			curShader.setParameter("DiffuseColor", aDiffuseColor)	
						
			#aDiffuseWeight
			curShader.setParameter("DiffuseWeight", float(aDiffuseWeight))
			
			#aDiffuseRoughness
			curShader.setParameter("DiffuseRoughness", float(aDiffuseRoughness))
			
			#aBacklighting
			curShader.setParameter("Backlighting", float(aBacklighting))
			
			#aDiffuseFresnel
			if aDiffuseFresnel == "True":
				curShader.setParameter("DiffuseFresnel", True)
			else:
				curShader.setParameter("DiffuseFresnel", False)
			
			#aSpecularColor
			aSpecularColor = set_mariColor(aSpecularColor)					
			curShader.setParameter("SpecularColor", aSpecularColor)			
			
			#aSpecularWeight
			curShader.setParameter("SpecularWeight", float(aSpecularWeight))
			
			#aSpecularRoughness
			curShader.setParameter("SpecularRoughness", float(aSpecularRoughness))
			
			#aAnisotropy
			curShader.setParameter("Anisotropy", float(aAnisotropy))
			
			#aRotation
			curShader.setParameter("Rotation", float(aRotation))
			
			#aFresnel_On
			if aFresnel_On == "True":
				curShader.setParameter("Fresnel_On", True)
			else:
				curShader.setParameter("Fresnel_On", False)
			
			#aReflectance
			curShader.setParameter("Reflectance", float(aReflectance))
			
			#aReflectionColor
			aReflectionColor = set_mariColor(aReflectionColor)					
			curShader.setParameter("ReflectionColor", aReflectionColor)
			
			#aReflectionWeight
			curShader.setParameter("ReflectionWeight", float(aReflectionWeight))
			
			#aFresnel_On_Ref
			if aFresnel_On_Ref == "True":
				curShader.setParameter("Fresnel_On_Ref", True)
			else:
				curShader.setParameter("Fresnel_On_Ref", False)
				
			#areflReflectance
			curShader.setParameter("reflReflectance", float(areflReflectance))
			
			#aRefractionColor
			aRefractionColor = set_mariColor(aRefractionColor)					
			curShader.setParameter("RefractionColor", aRefractionColor)			
			
			#aRefractionWeight			
			curShader.setParameter("RefractionWeight", float(aRefractionWeight))
			
			#aIOR
			curShader.setParameter("IOR", float(aIOR))
			
			#aRefractionRoughness
			curShader.setParameter("RefractionRoughness", float(aRefractionRoughness))			
			
			#aFresnel_useIOR
			if aFresnel_useIOR == "True":
				curShader.setParameter("Fresnel_useIOR", True)
			else:
				curShader.setParameter("Fresnel_useIOR", False)
				
			#aTransmittance
			aTransmittance = set_mariColor(aTransmittance)					
			curShader.setParameter("Transmittance", aTransmittance)
			
			#aOpacity
			aOpacity = set_mariColor(aOpacity)					
			curShader.setParameter("Opacity", aOpacity)
						
			#aSSSColor
			aSSSColor = set_mariColor(aSSSColor)					
			curShader.setParameter("SSSColor", aSSSColor)			
			
			#aSSSWeight
			curShader.setParameter("SSSWeight", float(aSSSWeight))
			
			#aSSSRadius
			aSSSRadius = set_mariColor(aSSSRadius)					
			curShader.setParameter("SSSRadius", aSSSRadius)			
			
			#aEmissionColor
			aEmissionColor = set_mariColor(aEmissionColor)					
			curShader.setParameter("EmissionColor", aEmissionColor)
			
			#aEmission
			curShader.setParameter("Emission", float(aEmission))
				
		elif shaderType == "VRay Mtl":
			
			
			#---------- Set the Shader Attributes ----------
			
			#DifCol			
			aDiffuseColor = set_mariColor(aDiffuseColor)					
			curShader.setParameter("DiffuseColor", aDiffuseColor)			
			
			#aDiffuse Amount
			curShader.setParameter("DiffuseAmount", float(aDiffuseAmount))			
			
			#Opacity Map
			aOpacity_Map = set_mariColor(aOpacity_Map)					
			curShader.setParameter("Opacity_Map", aOpacity_Map)			
			
			#aRoughness Amount
			curShader.setParameter("DiffuseRoughness", float(aDiffuseRoughness))			
			
			#Self-Illumination
			aSelf_Illumination = set_mariColor(aSelf_Illumination)					
			curShader.setParameter("Self_Illumination", aSelf_Illumination)			
			
			#aBRDF_Model
			curShader.setParameter("BRDF_Model", aBRDF_Model)			
			
			#Reflection Color
			aReflectionColor = set_mariColor(aReflectionColor)					
			curShader.setParameter("ReflectionColor", aReflectionColor)
			
			#Reflection Amount
			curShader.setParameter("ReflectionAmount", float(aReflectionAmount))
			
			#Lock Highlight Reflection glossiness
			if aLock_Highlight_Refle_gloss == "True":
				curShader.setParameter("Lock_Highlight_Refle_gloss", True)
			else:
				curShader.setParameter("Lock_Highlight_Refle_gloss", False)
			
			#Highlight Glossiness 
			curShader.setParameter("HighlightGlossiness", float(aHighlightGlossiness))			
			
			#Reflection Glossiness
			curShader.setParameter("ReflectionGlossiness", float(aReflectionGlossiness))
			
			#Fresnel On
			if aFresnel_On == "True":
				curShader.setParameter("Fresnel_On", True)
			else:
				curShader.setParameter("Fresnel_On", False)
			
			#Lock Fresnel IOR to Refraction IOR
			if aFresnel_useIOR == "True":
				curShader.setParameter("Fresnel_useIOR", True)
			else:
				curShader.setParameter("Fresnel_useIOR", False)			
			
			#Use Reflection IOR
			curShader.setParameter("Reflection_IOR", float(aReflection_IOR))
			
			#GGX Tail Falloff
			curShader.setParameter("ggxTailFalloff", float(aggxTailFalloff))
			
			#Anisotropy
			curShader.setParameter("Anisotropy", float(aAnisotropy))
			
			#Rotation
			curShader.setParameter("Rotation", float(aRotation))
			
			#Refraction Color
			aRefractionColor = set_mariColor(aRefractionColor)					
			curShader.setParameter("RefractionColor", aRefractionColor)
						
			#RefractionAmount
			curShader.setParameter("RefractionAmount", float(aRefractionAmount))
						
			#Refraction Glossiness
			curShader.setParameter("RefractionGlossiness", float(aRefractionGlossiness))
						
			#IOR Value
			curShader.setParameter("IOR", float(aIOR))
						
			#Refraction Color
			aFog_Color = set_mariColor(aFog_Color)					
			curShader.setParameter("Fog_Color", aFog_Color)
						
			#Fog multiplier
			curShader.setParameter("Fog_multiplier", float(aFog_multiplier))
						
			#Fog bias
			curShader.setParameter("Fog_bias", float(aFog_bias))
						
			#SSS Checkbox
			if aSSS_On == "True":
				curShader.setParameter("SSS_On", True)
			else:
				curShader.setParameter("SSS_On", False)
						
			#Refraction Color
			aTranslucency_Color = set_mariColor(aTranslucency_Color)					
			curShader.setParameter("Translucency_Color", aTranslucency_Color)
						
			#Fwd back coeff
			curShader.setParameter("Fwd_back_coeff", float(aFwd_back_coeff))			
						
			#Scatt coeff
			curShader.setParameter("Scatt_coeff", float(aScatt_coeff))
						
		elif shaderType == "Redshift Architectural":
			
			
			#---------- Set the Shader Attributes ----------
			
			#Diffuse Colour	
			adiffuse_color = set_mariColor(adiffuse_color)	
			curShader.setParameter("diffuse_color", adiffuse_color)
			
			#Diffuse Weight
			curShader.setParameter("diffuse_weight", float(adiffuse_weight))
			
			#Roughness Amount
			curShader.setParameter("diffuse_roughness", float(adiffuse_roughness))
			
			#Translucency
			if arefr_translucency == "True":
				curShader.setParameter("refr_translucency", True)
			else:
				curShader.setParameter("refr_translucency", False)

			#Translucency Colour
			arefr_trans_color = set_mariColor(arefr_trans_color)	
			curShader.setParameter("refr_trans_color", arefr_trans_color)	

			#Translucency Weight
			curShader.setParameter("refr_trans_weight", float(arefr_trans_weight))

			#Reflection Weight
			curShader.setParameter("refl_weight", float(arefl_weight))	

			#Reflection Color	
			arefl_color = set_mariColor(arefl_color)	
			curShader.setParameter("refl_color", arefl_color)	

			#Reflection Gloss
			curShader.setParameter("refl_gloss", float(arefl_gloss))

			#Brdf Fresnel
			if abrdf_fresnel == "True":
				curShader.setParameter("brdf_fresnel", True)
			else:
				curShader.setParameter("brdf_fresnel", False)

			#Fresnel type
			curShader.setParameter("brdf_fresnel_type", (abrdf_fresnel_type))	

			#BRDF extinction coefficient
			curShader.setParameter("brdf_extinction_coeff", float(abrdf_extinction_coeff))	

			#BRDF 0 degree reflection
			curShader.setParameter("brdf_0_degree_refl", float(abrdf_0_degree_refl))

			#BRDF 90 degree reflection
			curShader.setParameter("brdf_90_degree_refl", float(abrdf_90_degree_refl))

			#BRDF Curve
			curShader.setParameter("brdf_Curve", float(abrdf_Curve))

			#Reflection base weight
			curShader.setParameter("refl_base_weight", float(arefl_base_weight))

			#Reflection base Colour
			arefl_base_color = set_mariColor(arefl_base_color)	
			curShader.setParameter("refl_base_color", arefl_base_color)	

			#Reflection base Glossiness
			curShader.setParameter("refl_base_gloss", float(arefl_base_gloss))

			#BRDF base fresnel
			if abrdf_base_fresnel == "True":
				curShader.setParameter("brdf_base_fresnel", True)
			else:
				curShader.setParameter("brdf_base_fresnel", False)	
			
			#BRDF base fresnel type
			curShader.setParameter("brdf_base_fresnel_type", (abrdf_base_fresnel_type))

			#BRDF base extinction coefficient
			curShader.setParameter("brdf_base_extinction_coeff", float(abrdf_base_extinction_coeff))	

			#BRDF Curve at 0 degree
			curShader.setParameter("brdf_base_0_degree_refl", float(abrdf_base_0_degree_refl))

			#BRDF Curve at 90 degree
			curShader.setParameter("brdf_base_90_degree_refl", float(abrdf_base_90_degree_refl))

			#BRDF Curve
			curShader.setParameter("brdf_base_Curve", float(abrdf_base_Curve))
			
			#Reflection is metal	
			if arefl_is_metal == "True":
				curShader.setParameter("refl_is_metal", True)
			else:
				curShader.setParameter("refl_is_metal", False)
			
			#Highlight vs Reflection Balanace
			curShader.setParameter("hl_vs_refl_balance", float(ahl_vs_refl_balance))	
			
			#Anisotropy
			curShader.setParameter("anisotropy", float(aanisotropy))

			#Anisotropy Rotation
			curShader.setParameter("anisotropy_rotation", float(aanisotropy_rotation))
			
			#Anisotropy Orientation
			curShader.setParameter("anisotropy_orientation", (aanisotropy_orientation))
			
			#Transparency
			curShader.setParameter("transparency", float(atransparency))

			#Refraction Color
			arefr_color = set_mariColor(arefr_color)	
			curShader.setParameter("refr_color", arefr_color)

			#Refraction Gloss
			curShader.setParameter("refr_gloss", float(arefr_gloss))

			#Refraction IOR
			curShader.setParameter("refr_ior", float(arefr_ior))

			#Refraction Falloff On
			if arefr_falloff_on == "True":
				curShader.setParameter("refr_falloff_on", True)
			else:
				curShader.setParameter("refr_falloff_on", False)

			#Refraction Falloff Distance
			curShader.setParameter("refr_falloff_dist", float(arefr_falloff_dist))
			
			#Refraction Falloff Color On	
			if arefr_falloff_color_on == "True":
				curShader.setParameter("refr_falloff_color_on", True)
			else:
				curShader.setParameter("refr_falloff_color_on", False)

			#Refraction Falloff Color
			arefr_falloff_color = set_mariColor(arefr_falloff_color)	
			curShader.setParameter("refr_color", arefr_falloff_color)			
			
			#AO On	
			if aao_on == "True":
				curShader.setParameter("ao_on", True)
			else:
				curShader.setParameter("ao_on", False)
				
			#AO Combine Mode
			curShader.setParameter("ao_combineMode", (aao_combineMode))
			
			#AO dark
			aao_dark = set_mariColor(aao_dark)	
			curShader.setParameter("ao_dark", aao_dark)
			
			#AO dark
			aao_ambient = set_mariColor(aao_ambient)	
			curShader.setParameter("ao_ambient", aao_ambient)
			
			#Cutout Opacity
			curShader.setParameter("cutout_opacity", float(acutout_opacity))
			
			#Additional Color
			aadditional_color = set_mariColor(aadditional_color)	
			curShader.setParameter("additional_color", aadditional_color)
			
			#Incandescent Scale
			curShader.setParameter("Incandescent_Scale", float(aIncandescent_Scale))
		
		
		# Kill a shader if the user switches to a different shaderType during an update iteration. 
		# Only in case of single shaders, we have to take care and do this after the creation of the new shader
		if (shaderKilled == "True"):
			if True != geo.currentShader().isLayeredShader():			
				geo.removeShader(old_shader)
				remainShader = geo.shaderList()[-1]
				remainShader.makeCurrent()	
			
				
		chanRes = int(chanSize_combo.currentText())
		bitDepth = int(bitDepth_combo.currentText())		
		
		# Set/Update the current shader name.
		if update_previewShader == "True":			
			# have to go up one step on the layeredShader stream to set a new name of a shader inside of it.
			if geo.currentShader().isLayeredShader(): 				
				newShader = geo.currentShader().channelList()[0].layerList()[0]
			else:
				newShader = curShader
			newShader.setName(curShaderStr)
			curShaderStr = newShader.name()
			print("Update the preview to: '" +curShaderStr+ "' shader.")		
		
		# Try to force the layered shader UI to update the sliders to the newest current selected shader that has been created.
		#layeredShader_update_UI_list()	While Mari is waiting to Load a shader in viewport this function will not work properly!
		
		#---------------------- update channelList ----------------------
		
		inputs_list.clear()
		
		#add current inputs to inputs_list	
		shaderInputs=curShader.inputNameList()
		for input in shaderInputs:
			if (input != "ThicknessMap") and (input != "Normal") and (input != "Displacement") and (input != "Vector"):
				inputs_list.addItem(input)			

		
		#Enable add_channels Button
		mari.utils.connect(add_channels.clicked, lambda: add_channels_toShader())
		mari.utils.connect(inputs_list.clicked, lambda: check_inputSelected())
		# Enable the add_channels button if there is at least 1 item selected in the list. Else disable it.
		def check_inputSelected():
			selected_itemsCount = 0
			for items in inputs_list.selectedItems():
				selected_itemsCount += 1
			if selected_itemsCount >= 1:
				add_channels.setEnabled(True)
			else:
				add_channels.setEnabled(False)
				
		
		# Create Channels from RGB Values of the preset and assign it to the current selected shader.
		def add_channels_toShader():
			# Make sure the current shader selected is the last shader the preview def had created.
			if geo.currentShader().isLayeredShader():
				curShader = geo.currentShader().channelList()[0].layerList()[0].shader()
				curShaderStr = geo.currentShader().channelList()[0].layerList()[0]
				shaderList = geo.currentShader().channelList()[0].layerList()
				# Make sure you to unselect any shader from the list!
				for shader in shaderList:
					if shader == shaderList[0]:
						shader.setSelected(True)
					else:
						shader.setSelected(False)
				# select the top shader of the layered shader list.
				shaderList[0].makeCurrent()
			else:
				curShader = geo.shaderList()[-1]
				curShaderStr = geo.currentShader().name()
				curShader.makeCurrent()
			
			
			selected_items = inputs_list.selectedItems()
			curShaderType = str(curShader.getParameter("shadingNode"))
			# ---------- Create the Channels for the selected shader type by calling the create_channels def. ----------
			if (curShaderType == "Ai Standard") or (curShaderType == "VRay Mtl") or (curShaderType == "Redshift Architectural"):
				chanRes = int(chanSize_combo.currentText())
				bitDepth = int(bitDepth_combo.currentText())
				
				for item in selected_items:
					try:
						# get the value from the RGB Color Swatch or an attribute slider
						aParameter = curShader.getParameter(item.text())
						# Convert the float slider into RGB Color attribute
						aParameter = mari.Color(aParameter, aParameter, aParameter)
					except:
						pass
						
					try:
						geo.removeChannel(geo.channel(curShaderStr+"_Bump"))												
					except:
						pass	
					
					# We have to give the parameters for Bump Manually. The Input name Bump does not correlate to any shader slider parameter.
					if item.text() == "Bump":						
						aParameter = mari.Color(0.5, 0.5, 0.5)						
					
					# Call a definition that is responsible to create the channels with base colors layers					
					create_channels(curShader, item.text(), chanRes, bitDepth, aParameter, curShaderStr, killed_curShaderStr)
					print("Creating a channel for the Input: '" +item.text()+ "'")
			else:
				print("ERROR - The current shader you have selected '" +curShader.name()+ "' is not supported!")
				
			
			#resetting UI
			inputs_list.clear()	
			presets_combo.setCurrentIndex(0)
			prevImportCbox.setCheckState(QtCore.Qt.Unchecked)
			
			#Enable add_channels Button
			add_channels.setEnabled(False)
			
			update_previewShader = "False"
			
			# Try to force the layered shader UI to update the sliders to the newest current selected shader that has been created.
			#layeredShader_update_UI_list()
			
			print("------------- Channels Created -------------")
		
		
	def saveFile():
		curShaderStr = []
		# Export the current selected shader from the Layered Shader list.				
		if geo.currentShader().isLayeredShader():
			shaderList = geo.currentShader().channelList()[0].layerList()
			for shader_interation in shaderList:
				if shader_interation.isSelected():
					curShader = shader_interation.shader()
					curShaderStr = shader_interation.name()
					break			
		else:
			curShader = geo.currentShader()
			curShaderStr = curShader.name()
		
		#If we can't get the shaderType of the current selected shader, it is because it's not supported by mGo, therefore cant be exported
		try:
			shaderType=str(curShader.getParameter("shadingNode"))
		except:
			print("ERROR - mGo doesn't support export of the current selected shader type")
			print("------- Current Selected shader: '" +curShaderStr+ "' -------")
			return
		
		
		reserved = "none"		


		#Set the Material Presets Directory
		shaderTypeDir = shaderType_combo.currentText()
		libraryDir = library_combo.currentText()
		presetsDir = mariPath + "/mGo/Presets/" + shaderTypeDir +"/"+ libraryDir

		
                dirname = str(widgets.QFileDialog.getSaveFileName(caption="Save Preset", dir=presetsDir, option=0)[0])
		print("------------- Directory Path -------------")
		print(dirname)

		
		if dirname:
			#ARNOLD ============================================================================================
			if shaderType == "Ai Standard":
				#Attributes
				aDiffuseColor=(curShader.getParameter("DiffuseColor"))
				aDiffuseColor=str(aDiffuseColor.rgb())
				
				aDiffuseWeight=str(curShader.getParameter("DiffuseWeight"))
				aDiffuseRoughness=str(curShader.getParameter("DiffuseRoughness"))
				aBacklighting=str(curShader.getParameter("Backlighting"))
				aDiffuseFresnel=str(curShader.getParameter("DiffuseFresnel"))
				
				aSpecularColor=(curShader.getParameter("SpecularColor"))
				aSpecularColor=str(aSpecularColor.rgb())
				
				aSpecularWeight=str(curShader.getParameter("SpecularWeight"))
				aSpecularRoughness=str(curShader.getParameter("SpecularRoughness"))
				aAnisotropy=str(curShader.getParameter("Anisotropy"))
				aRotation=str(curShader.getParameter("Rotation"))
				aFresnel_On=str(curShader.getParameter("Fresnel_On"))
				aReflectance=str(curShader.getParameter("Reflectance"))
				
				aReflectionColor=(curShader.getParameter("ReflectionColor"))
				aReflectionColor=str(aReflectionColor.rgb())
				
				aReflectionWeight=str(curShader.getParameter("ReflectionWeight"))
				aFresnel_On_Ref=str(curShader.getParameter("Fresnel_On_Ref"))
				areflReflectance=str(curShader.getParameter("reflReflectance"))
				
				aRefractionColor=(curShader.getParameter("RefractionColor"))
				aRefractionColor=str(aRefractionColor.rgb())
				
				aRefractionWeight=str(curShader.getParameter("RefractionWeight"))
				aIOR=str(curShader.getParameter("IOR"))
				aRefractionRoughness=str(curShader.getParameter("RefractionRoughness"))				
				aFresnel_useIOR=str(curShader.getParameter("Fresnel_useIOR"))
				
				aTransmittance=(curShader.getParameter("Transmittance"))
				aTransmittance=str(aTransmittance.rgb())
				
				aOpacity=(curShader.getParameter("Opacity"))
				aOpacity=str(aOpacity.rgb())
				
				aSSSColor=(curShader.getParameter("SSSColor"))
				aSSSColor=str(aSSSColor.rgb())
				
				aSSSWeight=str(curShader.getParameter("SSSWeight"))
				
				aSSSRadius=(curShader.getParameter("SSSRadius"))
				aSSSRadius=str(aSSSRadius.rgb())
				
				aEmissionColor=(curShader.getParameter("EmissionColor"))
				aEmissionColor=str(aEmissionColor.rgb())
				aEmission=str(curShader.getParameter("Emission"))
								
				
				print("---------- Attributes parameters ----------")
				for parameter_name in curShader.parameterNameList():
					try:
						print("Parameter:'" + parameter_name + "' '" + str( curShader.getParameter( parameter_name).rgb() ) + "'")
					except:
						print("Parameter:'" + parameter_name + "' '" + str( curShader.getParameter( parameter_name)) + "'")
				print("-------------------------------------------")
					
				configShaderData = (shaderType, curShaderStr, aDiffuseColor, aDiffuseWeight, aDiffuseRoughness, aBacklighting, aDiffuseFresnel, aSpecularColor, aSpecularWeight, aSpecularRoughness, aAnisotropy, aRotation, aFresnel_On, aReflectance, aReflectionColor, aReflectionWeight, aFresnel_On_Ref, areflReflectance, aRefractionColor, aRefractionWeight, aIOR, aRefractionRoughness, aFresnel_useIOR, aTransmittance, aOpacity, aSSSColor, aSSSWeight, aSSSRadius, aEmissionColor, aEmission)
				

			#VRAY ============================================================================================
			elif shaderType == "VRay Mtl":
				#Attributes
				aDiffuseColor=(curShader.getParameter("DiffuseColor"))
				aDiffuseColor=str(aDiffuseColor.rgb())

				aDiffuseAmount=str(curShader.getParameter("DiffuseAmount"))

				aOpacity_Map=(curShader.getParameter("Opacity_Map"))
				aOpacity_Map=str(aOpacity_Map.rgb())

				aDiffuseRoughness=str(curShader.getParameter("DiffuseRoughness"))

				aSelf_Illumination=(curShader.getParameter("Self_Illumination"))
				aSelf_Illumination=str(aSelf_Illumination.rgb())

				aBRDF_Model=str(curShader.getParameter("BRDF_Model"))

				aReflectionColor=(curShader.getParameter("ReflectionColor"))
				aReflectionColor=str(aReflectionColor.rgb())

				aReflectionAmount=str(curShader.getParameter("ReflectionAmount"))
				aLock_Highlight_Refle_gloss=str(curShader.getParameter("Lock_Highlight_Refle_gloss"))
				aHighlightGlossiness=str(curShader.getParameter("HighlightGlossiness"))
				aReflectionGlossiness=str(curShader.getParameter("ReflectionGlossiness"))
				aFresnel_On=str(curShader.getParameter("Fresnel_On"))
				aFresnel_useIOR=str(curShader.getParameter("Fresnel_useIOR"))
				aReflection_IOR=str(curShader.getParameter("Reflection_IOR"))
				aggxTailFalloff=str(curShader.getParameter("ggxTailFalloff"))
				aAnisotropy=str(curShader.getParameter("Anisotropy"))
				aRotation=str(curShader.getParameter("Rotation"))

				aRefractionColor=(curShader.getParameter("RefractionColor"))
				aRefractionColor=str(aRefractionColor.rgb())

				aRefractionAmount=str(curShader.getParameter("RefractionAmount"))
				aRefractionGlossiness=str(curShader.getParameter("RefractionGlossiness"))
				aIOR=str(curShader.getParameter("IOR"))

				aFog_Color=(curShader.getParameter("Fog_Color"))
				aFog_Color=str(aFog_Color.rgb())

				aFog_multiplier=str(curShader.getParameter("Fog_multiplier"))
				aFog_bias=str(curShader.getParameter("Fog_bias"))
				aSSS_On=str(curShader.getParameter("SSS_On"))

				aTranslucency_Color=(curShader.getParameter("Translucency_Color"))
				aTranslucency_Color=str(aTranslucency_Color.rgb())

				aFwd_back_coeff=str(curShader.getParameter("Fwd_back_coeff"))
				aScatt_coeff=str(curShader.getParameter("Scatt_coeff"))
				
				
				print("---------- Attributes parameters ----------")
				for parameter_name in curShader.parameterNameList():
					try:				
						print("Parameter:'" + parameter_name + "' '" + str( curShader.getParameter( parameter_name).rgb() ) + "'")
					except:
						print("Parameter:'" + parameter_name + "' '" + str( curShader.getParameter( parameter_name)) + "'")
				print("-------------------------------------------")
				
				configShaderData = (shaderType, curShaderStr, aDiffuseColor, aDiffuseAmount, aOpacity_Map, aDiffuseRoughness, aSelf_Illumination, aBRDF_Model, aReflectionColor, aReflectionAmount, aLock_Highlight_Refle_gloss, aHighlightGlossiness, aReflectionGlossiness, aFresnel_On, aFresnel_useIOR, aReflection_IOR, aggxTailFalloff, aAnisotropy, aRotation, aRefractionColor, aRefractionAmount, aRefractionGlossiness, aIOR, aFog_Color, aFog_multiplier, aFog_bias, aSSS_On, aTranslucency_Color, aFwd_back_coeff, aScatt_coeff)                                     
				

			#REDSHIFT ============================================================================================
			elif shaderType == "Redshift Architectural":
				#Attributes
				adiffuse_color=(curShader.getParameter("diffuse_color"))
				adiffuse_color=str(adiffuse_color.rgb())

				adiffuse_weight=str(curShader.getParameter("diffuse_weight"))
				adiffuse_roughness=str(curShader.getParameter("diffuse_roughness"))
				arefr_translucency=str(curShader.getParameter("refr_translucency"))

				arefr_trans_color=(curShader.getParameter("refr_trans_color"))
				arefr_trans_color=str(arefr_trans_color.rgb())

				arefr_trans_weight=str(curShader.getParameter("refr_trans_weight"))
				arefl_weight=str(curShader.getParameter("refl_weight"))

				arefl_color=(curShader.getParameter("refl_color"))
				arefl_color=str(arefl_color.rgb())

				arefl_gloss=str(curShader.getParameter("refl_gloss"))
				abrdf_fresnel=str(curShader.getParameter("brdf_fresnel"))
				abrdf_fresnel_type=str(curShader.getParameter("brdf_fresnel_type"))
				abrdf_extinction_coeff=str(curShader.getParameter("brdf_extinction_coeff"))
				abrdf_0_degree_refl=str(curShader.getParameter("brdf_0_degree_refl"))
				abrdf_90_degree_refl=str(curShader.getParameter("brdf_90_degree_refl"))
				abrdf_Curve=str(curShader.getParameter("brdf_Curve"))
				arefl_base_weight=str(curShader.getParameter("refl_base_weight"))

				arefl_base_color=(curShader.getParameter("refl_base_color"))
				arefl_base_color=str(arefl_base_color.rgb())

				arefl_base_gloss=str(curShader.getParameter("refl_base_gloss"))
				abrdf_base_fresnel=str(curShader.getParameter("brdf_base_fresnel"))
				abrdf_base_fresnel_type=str(curShader.getParameter("brdf_base_fresnel_type"))
				abrdf_base_extinction_coeff=str(curShader.getParameter("brdf_base_extinction_coeff"))
				abrdf_base_0_degree_refl=str(curShader.getParameter("brdf_base_0_degree_refl"))
				abrdf_base_90_degree_refl=str(curShader.getParameter("brdf_base_90_degree_refl"))
				abrdf_base_Curve=str(curShader.getParameter("brdf_base_Curve"))
				arefl_is_metal=str(curShader.getParameter("refl_is_metal"))
				ahl_vs_refl_balance=str(curShader.getParameter("hl_vs_refl_balance"))
				aanisotropy=str(curShader.getParameter("anisotropy"))
				aanisotropy_rotation=str(curShader.getParameter("anisotropy_rotation"))
				aanisotropy_orientation=str(curShader.getParameter("anisotropy_orientation"))
				atransparency=str(curShader.getParameter("transparency"))

				arefr_color=(curShader.getParameter("refr_color"))
				arefr_color=str(arefr_color.rgb())

				arefr_gloss=str(curShader.getParameter("refr_gloss"))
				arefr_ior=str(curShader.getParameter("refr_ior"))
				arefr_falloff_on=str(curShader.getParameter("refr_falloff_on"))
				arefr_falloff_dist=str(curShader.getParameter("refr_falloff_dist"))
				arefr_falloff_color_on=str(curShader.getParameter("refr_falloff_color_on"))

				arefr_falloff_color=(curShader.getParameter("refr_falloff_color"))
				arefr_falloff_color=str(arefr_falloff_color.rgb())

				aao_on=str(curShader.getParameter("ao_on"))
				aao_combineMode=str(curShader.getParameter("ao_combineMode"))

				aao_dark=(curShader.getParameter("ao_dark"))
				aao_dark=str(aao_dark.rgb())

				aao_ambient=(curShader.getParameter("ao_ambient"))
				aao_ambient=str(aao_ambient.rgb())

				acutout_opacity=str(curShader.getParameter("cutout_opacity"))

				aadditional_color=(curShader.getParameter("additional_color"))
				aadditional_color=str(aadditional_color.rgb())

				aIncandescent_Scale=str(curShader.getParameter("Incandescent_Scale"))	
								
				
				print("---------- Attributes parameters ----------")
				for parameter_name in curShader.parameterNameList():
					try:				
						print("Parameter:'" + parameter_name + "' '" + str( curShader.getParameter( parameter_name).rgb() ) + "'")
					except:
						print("Parameter:'" + parameter_name + "' '" + str( curShader.getParameter( parameter_name)) + "'")
				print("-------------------------------------------")
				
				configShaderData = (shaderType, curShaderStr, adiffuse_color, adiffuse_weight, adiffuse_roughness, arefr_translucency, arefr_trans_color, arefr_trans_weight, arefl_weight, arefl_color, arefl_gloss, abrdf_fresnel, abrdf_fresnel_type, abrdf_extinction_coeff, abrdf_0_degree_refl, abrdf_90_degree_refl, abrdf_Curve, arefl_base_weight, arefl_base_color, arefl_base_gloss, abrdf_base_fresnel, abrdf_base_fresnel_type, abrdf_base_extinction_coeff, abrdf_base_0_degree_refl, abrdf_base_90_degree_refl, abrdf_base_Curve, arefl_is_metal, ahl_vs_refl_balance, aanisotropy, aanisotropy_rotation, aanisotropy_orientation, atransparency, arefr_color, arefr_gloss, arefr_ior, arefr_falloff_on, arefr_falloff_dist, arefr_falloff_color_on, arefr_falloff_color, aao_on, aao_combineMode, aao_dark, aao_ambient, acutout_opacity, aadditional_color, aIncandescent_Scale)                
			


			#add the .pre format suffix if user hasn't added it
			
			if ".pre" in dirname:
				dirname.replace(".pre","",1)
				path = dirname				
			else:
				path = dirname + ".pre"
			
			with open(path, 'w') as f:
                pickle.dump(configShaderData, f)
			

			#update the Preset List
			update_subDir()


			#Preset Exported messagse			
			msg = "--- Preset Saved ---"
			print(msg)

			presets_combo.addItem(msg)	
			presets_combo.setCurrentIndex(presets_combo.findText(msg))



			#reset Preview Checkbox

			prevImportCbox.setCheckState(QtCore.Qt.Unchecked)
			
			
			# <------------------------ Log last path used ------------------------>
			#Use this to make materialiser always remember the last shaderType and library folder selected by the user.			
			configData = (path)
			pathfile = mariPath + "/mGo/Presets/Materialiser_log.txt"
			with open(pathfile, 'w') as f:
                pickle.dump(configData, f)



def importShader(myFileName, shader_file, sendMode):
	try:
		mari.geo.setCurrent(myFileName)
	except:
		print("You are trying to update a shader of a mesh which doesn't exist in the project. No '" +myFileName+ "' found.")
		return
	geo = mari.geo.current()
	pathfile = shader_file
	#Open the preset file select
	with open(pathfile, 'r') as f:
        config = pickle.load(f)
	
	# Global configs load
	shaderType = config[0]
	curShaderStr = config[1]
	curShader = geo.currentShader()
	
	# Load config from file accondingly to the shaderType selected
	if shaderType == "Ai Standard":
		# Load config for Arnold Shaders
		shaderInternalName = config[1]	
		aDiffuseColor = config[2]
		aDiffuseWeight = config[3]
		aDiffuseRoughness = config[4]
		aBacklighting = config[5]
		aDiffuseFresnel = config[6]
		aSpecularColor = config[7]
		aSpecularWeight = config[8]
		aSpecularRoughness = config[9]
		aAnisotropy = config[10]
		aRotation = config[11]
		aFresnel_On = config[12]
		aReflectance = config[13]
		aReflectionColor = config[14]
		aReflectionWeight = config[15]
		aFresnel_On_Ref = config[16]
		areflReflectance = config[17]
		aRefractionColor = config[18]
		aRefractionWeight = config[19]
		aIOR = config[20]
		aRefractionRoughness = config[21]			
		aFresnel_useIOR = config[22]
		aTransmittance = config[23]
		aOpacity = config[24]
		aSSSColor = config[25]
		aSSSWeight = config[26]
		aSSSRadius = config[27]
		aEmissionColor = config[28]
		aEmission = config[29]
				
	elif shaderType == "VRay Mtl":
		# Load config for Vray Shaders
		shaderInternalName = config[1]	
		aDiffuseColor = config[2]
		aDiffuseAmount = config[3]
		aOpacity_Map = config[4]
		aDiffuseRoughness = config[5]
		aSelf_Illumination = config[6]
		aBRDF_Model = config[7]
		aReflectionColor = config[8]
		aReflectionAmount = config[9]
		aLock_Highlight_Refle_gloss = config[10]
		aHighlightGlossiness = config[11]
		aReflectionGlossiness = config[12]
		aFresnel_On = config[13]
		aFresnel_useIOR = config[14]
		aReflection_IOR = config[15]
		aggxTailFalloff = config[16]
		aAnisotropy = config[17]
		aRotation = config[18]
		aRefractionColor = config[19]
		aRefractionAmount = config[20]
		aRefractionGlossiness = config[21]
		aIOR = config[22]
		aFog_Color = config[23]
		aFog_multiplier = config[24]
		aFog_bias = config[25]
		aSSS_On = config[26]
		aTranslucency_Color = config[27]
		aFwd_back_coeff = config[28]
		aScatt_coeff = config[29]
				
	elif shaderType == "Redshift Architectural":
		# Load config for Redshift Shaders
		shaderInternalName = config[1]	
		adiffuse_color = config[2]
		adiffuse_weight = config[3]
		adiffuse_roughness = config[4]
		arefr_translucency = config[5]
		arefr_trans_color = config[6]
		arefr_trans_weight = config[7]
		arefl_weight = config[8]
		arefl_color = config[9]
		arefl_gloss = config[10]
		abrdf_fresnel = config[11]
		abrdf_fresnel_type = config[12]
		abrdf_extinction_coeff = config[13]
		abrdf_0_degree_refl = config[14]
		abrdf_90_degree_refl = config[15]
		abrdf_Curve = config[16]
		arefl_base_weight = config[17]
		arefl_base_color = config[18]
		arefl_base_gloss = config[19]
		abrdf_base_fresnel = config[20]
		abrdf_base_fresnel_type = config[21]
		abrdf_base_extinction_coeff = config[22]
		abrdf_base_0_degree_refl = config[23]
		abrdf_base_90_degree_refl = config[24]
		abrdf_base_Curve = config[25]
		arefl_is_metal = config[26]
		ahl_vs_refl_balance = config[27]
		aanisotropy = config[28]
		aanisotropy_rotation = config[29]
		aanisotropy_orientation = config[30]
		atransparency = config[31]
		arefr_color = config[32]
		arefr_gloss = config[33]
		arefr_ior = config[34]
		arefr_falloff_on = config[35]
		arefr_falloff_dist = config[36]
		arefr_falloff_color_on = config[37]
		arefr_falloff_color = config[38]
		aao_on = config[39]
		aao_combineMode = config[40]
		aao_dark = config[41]
		aao_ambient = config[42]
		acutout_opacity = config[43]
		aadditional_color = config[44]
		aIncandescent_Scale = config[45]	
	
	
	#Create the shaders accordingly to it's type.
	def create_newShader(shaderType):
		curShader = []
		if shaderType == "Ai Standard":
			newShader = geo.createStandaloneShader(curShaderStr,"Lighting/Standalone/AiStandard"); 
		elif shaderType == "VRay Mtl":
			newShader = geo.createStandaloneShader(curShaderStr,"Lighting/Standalone/VRayMtl"); 
		elif shaderType == "Redshift Architectural":
			newShader = geo.createStandaloneShader(curShaderStr,"Lighting/Standalone/RedshiftArchitectural");

		newShader.makeCurrent()
		curShader = geo.currentShader()
		
		print("Creating: '" +curShader.name()+ "' shader.")
		return curShader;
	
	# Definitions to rework the values from a color and reassign them back.
	def set_mariColor(attributeColor):
		invalid = ["(", ")", "[", "]"]
		replacement = ""
		for x in invalid:
			attributeColor=attributeColor.replace(x, replacement)

		aColor= attributeColor.split(',', 2)
		
		val1=float(aColor[0])
		val2=float(aColor[1])
		val3=float(aColor[2])			
		aColor = mari.Color(val1, val2, val3)
		
		return aColor;
	
	# just updating the mesh?
	if sendMode == "3":
		shaderExists = False
		shaderList = geo.shaderList()
		for shader in shaderList:
			if shader.name() == curShaderStr:
				shaderExists = True
				geo.setCurrentShader(shader)
				curShader = geo.currentShader()
		#check if the shader exists, otherwise create a new one.
		if shaderExists != True:
			curShader = create_newShader(shaderType)
	else:
		curShader = create_newShader(shaderType)
	
	# Set the Shader accordingly to the parameters loaded of the preset selected.
	if shaderType == "Ai Standard":
	
		
		#---------- Set the Shader Attributes ----------
		
		#DifCol
		aDiffuseColor = set_mariColor(aDiffuseColor)					
		curShader.setParameter("DiffuseColor", aDiffuseColor)	
					
		#aDiffuseWeight
		curShader.setParameter("DiffuseWeight", float(aDiffuseWeight))
		
		#aDiffuseRoughness
		curShader.setParameter("DiffuseRoughness", float(aDiffuseRoughness))
		
		#aBacklighting
		curShader.setParameter("Backlighting", float(aBacklighting))
		
		#aDiffuseFresnel
		if aDiffuseFresnel == "True":
			curShader.setParameter("DiffuseFresnel", True)
		else:
			curShader.setParameter("DiffuseFresnel", False)
		
		#aSpecularColor
		aSpecularColor = set_mariColor(aSpecularColor)					
		curShader.setParameter("SpecularColor", aSpecularColor)			
		
		#aSpecularWeight
		curShader.setParameter("SpecularWeight", float(aSpecularWeight))
		
		#aSpecularRoughness
		curShader.setParameter("SpecularRoughness", float(aSpecularRoughness))
		
		#aAnisotropy
		curShader.setParameter("Anisotropy", float(aAnisotropy))
		
		#aRotation
		curShader.setParameter("Rotation", float(aRotation))
		
		#aFresnel_On
		if aFresnel_On == "True":
			curShader.setParameter("Fresnel_On", True)
		else:
			curShader.setParameter("Fresnel_On", False)
		
		#aReflectance
		curShader.setParameter("Reflectance", float(aReflectance))
		
		#aReflectionColor
		aReflectionColor = set_mariColor(aReflectionColor)					
		curShader.setParameter("ReflectionColor", aReflectionColor)
		
		#aReflectionWeight
		curShader.setParameter("ReflectionWeight", float(aReflectionWeight))
		
		#aFresnel_On_Ref
		if aFresnel_On_Ref == "True":
			curShader.setParameter("Fresnel_On_Ref", True)
		else:
			curShader.setParameter("Fresnel_On_Ref", False)
			
		#areflReflectance
		curShader.setParameter("reflReflectance", float(areflReflectance))
		
		#aRefractionColor
		aRefractionColor = set_mariColor(aRefractionColor)					
		curShader.setParameter("RefractionColor", aRefractionColor)			
		
		#aRefractionWeight			
		curShader.setParameter("RefractionWeight", float(aRefractionWeight))
		
		#aIOR
		curShader.setParameter("IOR", float(aIOR))
		
		#aRefractionRoughness
		curShader.setParameter("RefractionRoughness", float(aRefractionRoughness))			
		
		#aFresnel_useIOR
		if aFresnel_useIOR == "True":
			curShader.setParameter("Fresnel_useIOR", True)
		else:
			curShader.setParameter("Fresnel_useIOR", False)
			
		#aTransmittance
		aTransmittance = set_mariColor(aTransmittance)					
		curShader.setParameter("Transmittance", aTransmittance)
		
		#aOpacity
		aOpacity = set_mariColor(aOpacity)					
		curShader.setParameter("Opacity", aOpacity)
					
		#aSSSColor
		aSSSColor = set_mariColor(aSSSColor)					
		curShader.setParameter("SSSColor", aSSSColor)			
		
		#aSSSWeight
		curShader.setParameter("SSSWeight", float(aSSSWeight))
		
		#aSSSRadius
		aSSSRadius = set_mariColor(aSSSRadius)					
		curShader.setParameter("SSSRadius", aSSSRadius)			
		
		#aEmissionColor
		aEmissionColor = set_mariColor(aEmissionColor)					
		curShader.setParameter("EmissionColor", aEmissionColor)
		
		#aEmission
		curShader.setParameter("Emission", float(aEmission))
			
	elif shaderType == "VRay Mtl":
		
		
		#---------- Set the Shader Attributes ----------
		
		#DifCol			
		aDiffuseColor = set_mariColor(aDiffuseColor)					
		curShader.setParameter("DiffuseColor", aDiffuseColor)			
		
		#aDiffuse Amount
		curShader.setParameter("DiffuseAmount", float(aDiffuseAmount))			
		
		#Opacity Map
		aOpacity_Map = set_mariColor(aOpacity_Map)					
		curShader.setParameter("Opacity_Map", aOpacity_Map)			
		
		#aRoughness Amount
		curShader.setParameter("DiffuseRoughness", float(aDiffuseRoughness))			
		
		#Self-Illumination
		aSelf_Illumination = set_mariColor(aSelf_Illumination)					
		curShader.setParameter("Self_Illumination", aSelf_Illumination)			
		
		#aBRDF_Model
		curShader.setParameter("BRDF_Model", aBRDF_Model)			
		
		#Reflection Color
		aReflectionColor = set_mariColor(aReflectionColor)					
		curShader.setParameter("ReflectionColor", aReflectionColor)
		
		#Reflection Amount
		curShader.setParameter("ReflectionAmount", float(aReflectionAmount))
		
		#Lock Highlight Reflection glossiness
		if aLock_Highlight_Refle_gloss == "True":
			curShader.setParameter("Lock_Highlight_Refle_gloss", True)
		else:
			curShader.setParameter("Lock_Highlight_Refle_gloss", False)
		
		#Highlight Glossiness 
		curShader.setParameter("HighlightGlossiness", float(aHighlightGlossiness))			
		
		#Reflection Glossiness
		curShader.setParameter("ReflectionGlossiness", float(aReflectionGlossiness))
		
		#Fresnel On
		if aFresnel_On == "True":
			curShader.setParameter("Fresnel_On", True)
		else:
			curShader.setParameter("Fresnel_On", False)
		
		#Lock Fresnel IOR to Refraction IOR
		if aFresnel_useIOR == "True":
			curShader.setParameter("Fresnel_useIOR", True)
		else:
			curShader.setParameter("Fresnel_useIOR", False)			
		
		#Use Reflection IOR
		curShader.setParameter("Reflection_IOR", float(aReflection_IOR))
		
		#GGX Tail Falloff
		curShader.setParameter("ggxTailFalloff", float(aggxTailFalloff))
		
		#Anisotropy
		curShader.setParameter("Anisotropy", float(aAnisotropy))
		
		#Rotation
		curShader.setParameter("Rotation", float(aRotation))
		
		#Refraction Color
		aRefractionColor = set_mariColor(aRefractionColor)					
		curShader.setParameter("RefractionColor", aRefractionColor)
					
		#RefractionAmount
		curShader.setParameter("RefractionAmount", float(aRefractionAmount))
					
		#Refraction Glossiness
		curShader.setParameter("RefractionGlossiness", float(aRefractionGlossiness))
					
		#IOR Value
		curShader.setParameter("IOR", float(aIOR))
					
		#Refraction Color
		aFog_Color = set_mariColor(aFog_Color)					
		curShader.setParameter("Fog_Color", aFog_Color)
					
		#Fog multiplier
		curShader.setParameter("Fog_multiplier", float(aFog_multiplier))
					
		#Fog bias
		curShader.setParameter("Fog_bias", float(aFog_bias))
					
		#SSS Checkbox
		if aSSS_On == "True":
			curShader.setParameter("SSS_On", True)
		else:
			curShader.setParameter("SSS_On", False)
					
		#Refraction Color
		aTranslucency_Color = set_mariColor(aTranslucency_Color)					
		curShader.setParameter("Translucency_Color", aTranslucency_Color)
					
		#Fwd back coeff
		curShader.setParameter("Fwd_back_coeff", float(aFwd_back_coeff))			
					
		#Scatt coeff
		curShader.setParameter("Scatt_coeff", float(aScatt_coeff))
					
	elif shaderType == "Redshift Architectural":
		
		
		#---------- Set the Shader Attributes ----------
		
		#Diffuse Colour	
		adiffuse_color = set_mariColor(adiffuse_color)	
		curShader.setParameter("diffuse_color", adiffuse_color)
		
		#Diffuse Weight
		curShader.setParameter("diffuse_weight", float(adiffuse_weight))
		
		#Roughness Amount
		curShader.setParameter("diffuse_roughness", float(adiffuse_roughness))
		
		#Translucency
		if arefr_translucency == "True":
			curShader.setParameter("refr_translucency", True)
		else:
			curShader.setParameter("refr_translucency", False)

		#Translucency Colour
		arefr_trans_color = set_mariColor(arefr_trans_color)	
		curShader.setParameter("refr_trans_color", arefr_trans_color)	

		#Translucency Weight
		curShader.setParameter("refr_trans_weight", float(arefr_trans_weight))

		#Reflection Weight
		curShader.setParameter("refl_weight", float(arefl_weight))	

		#Reflection Color	
		arefl_color = set_mariColor(arefl_color)	
		curShader.setParameter("refl_color", arefl_color)	

		#Reflection Gloss
		curShader.setParameter("refl_gloss", float(arefl_gloss))

		#Brdf Fresnel
		if abrdf_fresnel == "True":
			curShader.setParameter("brdf_fresnel", True)
		else:
			curShader.setParameter("brdf_fresnel", False)

		#Fresnel type
		curShader.setParameter("brdf_fresnel_type", (abrdf_fresnel_type))	

		#BRDF extinction coefficient
		curShader.setParameter("brdf_extinction_coeff", float(abrdf_extinction_coeff))	

		#BRDF 0 degree reflection
		curShader.setParameter("brdf_0_degree_refl", float(abrdf_0_degree_refl))

		#BRDF 90 degree reflection
		curShader.setParameter("brdf_90_degree_refl", float(abrdf_90_degree_refl))

		#BRDF Curve
		curShader.setParameter("brdf_Curve", float(abrdf_Curve))

		#Reflection base weight
		curShader.setParameter("refl_base_weight", float(arefl_base_weight))

		#Reflection base Colour
		arefl_base_color = set_mariColor(arefl_base_color)	
		curShader.setParameter("refl_base_color", arefl_base_color)	

		#Reflection base Glossiness
		curShader.setParameter("refl_base_gloss", float(arefl_base_gloss))

		#BRDF base fresnel
		if abrdf_base_fresnel == "True":
			curShader.setParameter("brdf_base_fresnel", True)
		else:
			curShader.setParameter("brdf_base_fresnel", False)	
		
		#BRDF base fresnel type
		curShader.setParameter("brdf_base_fresnel_type", (abrdf_base_fresnel_type))

		#BRDF base extinction coefficient
		curShader.setParameter("brdf_base_extinction_coeff", float(abrdf_base_extinction_coeff))	

		#BRDF Curve at 0 degree
		curShader.setParameter("brdf_base_0_degree_refl", float(abrdf_base_0_degree_refl))

		#BRDF Curve at 90 degree
		curShader.setParameter("brdf_base_90_degree_refl", float(abrdf_base_90_degree_refl))

		#BRDF Curve
		curShader.setParameter("brdf_base_Curve", float(abrdf_base_Curve))
		
		#Reflection is metal	
		if arefl_is_metal == "True":
			curShader.setParameter("refl_is_metal", True)
		else:
			curShader.setParameter("refl_is_metal", False)
		
		#Highlight vs Reflection Balanace
		curShader.setParameter("hl_vs_refl_balance", float(ahl_vs_refl_balance))	
		
		#Anisotropy
		curShader.setParameter("anisotropy", float(aanisotropy))

		#Anisotropy Rotation
		curShader.setParameter("anisotropy_rotation", float(aanisotropy_rotation))
		
		#Anisotropy Orientation
		curShader.setParameter("anisotropy_orientation", (aanisotropy_orientation))
		
		#Transparency
		curShader.setParameter("transparency", float(atransparency))

		#Refraction Color
		arefr_color = set_mariColor(arefr_color)	
		curShader.setParameter("refr_color", arefr_color)

		#Refraction Gloss
		curShader.setParameter("refr_gloss", float(arefr_gloss))

		#Refraction IOR
		curShader.setParameter("refr_ior", float(arefr_ior))

		#Refraction Falloff On
		if arefr_falloff_on == "True":
			curShader.setParameter("refr_falloff_on", True)
		else:
			curShader.setParameter("refr_falloff_on", False)

		#Refraction Falloff Distance
		curShader.setParameter("refr_falloff_dist", float(arefr_falloff_dist))
		
		#Refraction Falloff Color On	
		if arefr_falloff_color_on == "True":
			curShader.setParameter("refr_falloff_color_on", True)
		else:
			curShader.setParameter("refr_falloff_color_on", False)

		#Refraction Falloff Color
		arefr_falloff_color = set_mariColor(arefr_falloff_color)	
		curShader.setParameter("refr_color", arefr_falloff_color)			
		
		#AO On	
		if aao_on == "True":
			curShader.setParameter("ao_on", True)
		else:
			curShader.setParameter("ao_on", False)
			
		#AO Combine Mode
		curShader.setParameter("ao_combineMode", (aao_combineMode))
		
		#AO dark
		aao_dark = set_mariColor(aao_dark)	
		curShader.setParameter("ao_dark", aao_dark)
		
		#AO dark
		aao_ambient = set_mariColor(aao_ambient)	
		curShader.setParameter("ao_ambient", aao_ambient)
		
		#Cutout Opacity
		curShader.setParameter("cutout_opacity", float(acutout_opacity))
		
		#Additional Color
		aadditional_color = set_mariColor(aadditional_color)	
		curShader.setParameter("additional_color", aadditional_color)
		
		#Incandescent Scale
		curShader.setParameter("Incandescent_Scale", float(aIncandescent_Scale))
