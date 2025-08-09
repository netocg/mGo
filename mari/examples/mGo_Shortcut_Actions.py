# ------------------------------------------------------------------------------
#    SCRIPT            mGo_Shortcut_Actions.py
#
#    AUTHOR            Antonio Lisboa M. Neto
#                      netocg.fx@gmail.com
#
#    DATE:             November, 2014 - July 2015
#
#    DESCRIPTION:      Custom Shortcuts for Mari mGo and to speed up the workflow with their custom shaders
#
#    VERSION:          3.1
#
#-----------------------------------------------------------------

import mari
from . import mGo

def reload_mGo():
    try:
        import importlib
        importlib.reload(mGo)
    except AttributeError:
        reload(mGo)

reload_mGo()

# Launches mGo palette from the (Shift+4) Shortcut
def starts_mGo():
	reload_mGo()
	mari.examples.mGo.run_mGo()

# ------------------------------------------------------------------------------
	
# Check every input name and it's content from the selected shader.
def checkInputs(curShader, curChannel):
	"Check every input name and it's content from the selected shader."

	_inputName = []
	for input_channel in curShader.inputList():
		# channel assigned to the current input on the loop iteration
		try:
			channel_content = input_channel[1]
			
			# Check if the Channel assigned to the current input iteration in the loop match the current selected channel.
			if channel_content.name() == curChannel:
				
				# If 'yes', store the input name.
				_inputName = input_channel[0]
				print("The current selected channel: '" +curChannel+ "' from the geo: '" +mari.geo.current().name()+ "' is assigned to the Input:'" +_inputName+ "' of the shader: '" +curShader.name()+ "'")
				return _inputName;
				
		except:
			pass

	return _inputName;

	
# Check the current selected shader from the current selected Geo.	
def checkShader(curShader):
	"Check the current selected shader from the current selected Geo."

	# Get the current selected shader inside of the Layered Shader list.
	_curShader = None 
	if curShader and curShader.isLayeredShader():
		shaderList = curShader.channelList()[0].layerList()
		for shader_interation in shaderList:
			if shader_interation.isSelected():
				_curShader = shader_interation.shader()
				break	
	
	else:
		_curShader = curShader
	
	if _curShader:    
		_curShader.makeCurrent()	
	return _curShader;

	
# Main function responsible in try to synchronize all the channels selected from all the geos in the project, based on the Input that has the current selected channel assign to it.	
def syncChannels():
	"Main function responsible in try to synchronize all the channels selected from all the geos in the project, based on the Input that has the current selected channel assign to it."

	print("--------------------------------------------------------------------")
	print("Synchronize Channels Selected - Shortcut Action(Shift+1)")
	geo = mari.geo.current()
	old_curShader = geo.currentShader()
	curChannel = geo.currentChannel().name()	

	# Call the def that checks the current selected shader from the current selected Geo.
	curShader = checkShader(geo.currentShader())
	if curShader is None:
		print("Cannot sync channels without the current shader")
		return
	
	print("Current selected shader: '" +curShader.name()+ "'")
	
	# Call the def that checks every input name and it's content from the selected shader.
	inputName = checkInputs(curShader, curChannel)
	if inputName == []:
		print("---------------")
		print("Process Failed - Can't find an Input that is using the selected channel from the current selected shader, on the current selected geo!")
		old_curShader.makeCurrent()
		return
	
	# Go on each geo on the project.
	for curGeoIteration in mari.geo.list():
		print("---------------")
		# Select the current Geo Iteration from the Loop, and check/select the current selected shader from that geo.
		curGeoIteration.setSelected(True)		
		
		# Call the def that checks the current selected shader from the current selected Geo.
		curShader = checkShader(curGeoIteration.currentShader())		
		print("Looking for a correspondent Input name in the shader: '" +curShader.name()+ "' from the geo: '" +curGeoIteration.name()+ "'")
		
		# little trigger to return a msg of alert in case of not find an Input with that name in the current shader from the current geo in the loop iteration.
		input_found = []
		
		# Check every input name and content from the selected shader.
		for input_channel in curShader.inputList():
			
			# Check if the current input name on the loop iteration match the stored input name.
			if inputName == input_channel[0]:				
				
				# if yes select the channel that is assign to that input.
				try:
					channel_content = input_channel[1]
					channel_content.makeCurrent()
					print("Input: '" +inputName+ "' has the channel: '" +channel_content.name()+ "' assigned to it!")
					print("Selecting that channel.")
					input_found = "True"
				except:
					print("Didn't find any channel assigned to the Input: '" +inputName+ "' of the correspondent geo/shader")
				break			
		
		# Trigger that returns a msg in case of not find an Input in the with the name we are looking for in the current selected shader.
		if input_found != "True":
			print("Didn't find any input with the name: '" +inputName+ "' to the correspondent geo/shader")		
		
	# Ensures to selected back the geo that was selected in the begging of the process.
	geo.setSelected(True)
	print("Channels synchronized as possible across all the geometries!")
	
	return	

# ------------------------------------------------------------------------------

_RESET_SHADERS = {}

def isolateCurrentShader():
	global _RESET_SHADERS
	
	geo = mari.geo.current()
	
	# Avoid overwritten the var registers if it has some info different from it's default value. 
	if _RESET_SHADERS != {}:
		print("You already have Isolate Shader registered in memory.") 
		print("Please use the Isolate Reset - Shortcut Action(Shift+3) in order to bring back the registered value and enable back the (Shift+2) Shortcut Action!")
		return
 
	if geo.currentShader() and geo.currentShader().isLayeredShader():
		print("-----------------------------------------------")
		print("Isolate Current Shader(Layered) - Shortcut Action(Shift+2)")
		shaderList = geo.currentShader().channelList()[0].layerList()
		for shader_interation in shaderList:         
			# register the visibility, blend mode and blend amount, to later on use as backup when the isolateReset def gets called.
			shaderVisibility = ( shader_interation.isVisible() )
			blendMode = ( shader_interation.blendMode() )
			blendAmount = ( shader_interation.blendAmount() )
			_RESET_SHADERS[shader_interation] = (shaderVisibility, blendMode, blendAmount)
			
			print("Shader: '" +shader_interation.name()+ "'")
			print("Visibility: '" + str(shaderVisibility)+ "'")
			print("Blend Mode: '" +mari.Layer.blendModeName(blendMode)+ "'")
			print("Blend Amount: '" + str(blendAmount)+ "'")			
			
			# Turn of any shader in the layered shader list that is not selected
			if True != shader_interation.isSelected():
				shader_interation.setVisibility(False)
				print("Turning him off!")
			else:
				# Set the selected shader to normal, and blend amount 1.0 in order to easily work with him whithout any blending effect.
				shader_interation.setBlendMode(mari.Layer.MIX)
				shader_interation.setBlendAmount(1.0)
				print("Set the Blend Mode to Normal, and Blend Amount to 1.0")
			
			print("---------------")
			
	else:
		print("Please select a shader inside of a Layered Shader list in order to isolate it!")
			 	
				
def isolateReset():
	global _RESET_SHADERS
	
	# Print out some msg in case the user didn't had call yet the isolateCurrentShader shortcut action!
	if _RESET_SHADERS != {}:
		print("------------------------------------------------------")
		print("Isolate Reset Shaders(Layered) - Shortcut Action(Shift+3)")
	else:
		print("Before call this Shortcut Action(Shift+3) you should first call Isolate Current Shader - Shortcut Action(Alt+2) in order to store shaders values.")
		return

	# Reset the visibilities, blendmode, and blend amount of every shader in that Layered Shader
	for shader in _RESET_SHADERS:
		shader.setVisibility(_RESET_SHADERS[shader][0])
		shader.setBlendMode(_RESET_SHADERS[shader][1])
		shader.setBlendAmount(_RESET_SHADERS[shader][2])
	# Reset the var to their default value.
	_RESET_SHADERS = {}
	print("Shaders parameters has been restored.")
	
# ------------------------------------------------------------------------------	

# Launches mGo documentation from the (Shift+8) Shortcut
def mGoHelp():
	"Launches mGo documentation"

	filePath = mari.resources.path(mari.resources.HELP) + '/mGoManual.pdf'
	mari.resources.showPDF(filePath)

# Only set up menu entries and connections is the application is running.
def _createMenu():
	# Register new Shortcut actions with the action manager, and add it to a Python Menu under the mGo group
	UI_path = 'MainWindow/P&ython/&Examples/mGo'

	action1 = mari.actions.create('Open mGo Palette             Shift+4', "mari.examples.mGo_Shortcut_Actions.starts_mGo()")
	mari.menus.addAction(action1, UI_path)
	action1.setShortcut('Shift+4')
	action1.setShortcut('Shift+$') #linux compatibility

	action2 = mari.actions.create('Synchronize Channels Selected', "mari.examples.mGo_Shortcut_Actions.syncChannels()")
	mari.menus.addAction(action2, UI_path)
	action2.setShortcut('Shift+5') #win
	action2.setShortcut('Shift+%') #linux compatibility

	action3 = mari.actions.create('Isolate Current Shader(Layered)', "mari.examples.mGo_Shortcut_Actions.isolateCurrentShader()")
	mari.menus.addAction(action3, UI_path)
	action3.setShortcut('Shift+6') #win can't have the linux compatibility here because that would fall into a character that python recognize as a symbol so the script would not be compiled.

	action4 = mari.actions.create('Isolate Reset Shaders(Layered)', "mari.examples.mGo_Shortcut_Actions.isolateReset()")
	mari.menus.addAction(action4, UI_path)
	action4.setShortcut('Shift+7') #win
	action4.setShortcut('Shift+&') #linux compatibility

	action5 = mari.actions.create('mGo Manual - pdf         Shift+8', "mari.examples.mGo_Shortcut_Actions.mGoHelp()")
	mari.menus.addAction(action5, UI_path)
	action5.setShortcut('Shift+8') #win
	action5.setShortcut('Shift+*') #linux compatibility

if mari.app.isRunning():
	_createMenu()
