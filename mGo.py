#-----------------------------------------------------------------
#    SCRIPT            mGo.py
#
#    AUTHOR            Stuart Tozer
#                      stutozer@gmail.com
#
#    CONTRIBUTOR       Antonio Lisboa M. Neto
#                      netocg.fx@gmail.com
#
#    DATE:             September 2014 - September 2015
#
#    DESCRIPTION:      Mari OpenGL Shader Transfer Utility to Maya
#
#    VERSION:          3.0
#
#-----------------------------------------------------------------

#REMEMBER in Maya to place the the mGo_Maya scripts in the mayas/scripts folder and run them with the following code as command line (python)...
"""
import mGo_MayaUI; mGo_MayaUI.UI()
"""

import mari
import os
import threading
import subprocess
import shutil
import socket
import pickle
import hashlib
import PySide2
from PySide2 import QtGui, QtCore, QtWidgets

gui = PySide2.QtGui
widgets = PySide2.QtWidgets

def printMessage(Str):
    # This method prints to the python console as well as the verbose log
    print(Str)
    mari.app.log(Str)

def run_mGo():
    #External Network Address. Work in any OS!!
    def get_ip():
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # doesn't even have to be reachable
            s.connect(('10.255.255.255', 0))
            _ip = s.getsockname()[0]
        except:
            _ip = '127.0.0.1'
        finally:
            s.close()
        return _ip

    #Machines could have multiple IPs - Wifi, Wired etc...
    IPS = []
    #Prioritize WIRED Network Address! OS dependent solution...
    import platform
    platform = str(platform.system())
    if platform == "Windows":
        #WINDOWS ONLY
        wired_ip = '127.0.0.1'
        try:
            wired_ip = str(socket.gethostbyname(socket.gethostname()))
        except:
            wired_ip = get_ip()
        IPS = [wired_ip, get_ip()]
    else:
        #Linux Only
        wired_ip = '127.0.0.1'
        try:
            co = subprocess.Popen(['ifconfig'], stdout = subprocess.PIPE)
            #read the ifconfig file
            ifconfig = co.stdout.read()

            i=0
            _ips=[]
            #look for the IP number that comes right after the inet string.
            ifconfig_spaceless = ifconfig.split(" ")
            for ifconfig_strings in ifconfig_spaceless:
                if 	ifconfig_strings == "inet":
                    if ifconfig_spaceless[i+1] != "127.0.0.1":
                        _ips.append(ifconfig_spaceless[i+1])
                i+=1

            wired_ip = ext_ip = get_ip()
            for _ip in _ips:
                if _ip != ext_ip:
                    wired_ip = _ip
        except:
            wired_ip = get_ip()
        IPS = [wired_ip, get_ip()]


    # <------------------------ mGo UI start ------------------------>
    printMessage("------------- mGo Toolkit ver 3.0 -------------")
    printMessage("Author: Stuart Tozer - stutozer@gmail.com")
    printMessage("Contributor: Antonio Neto - netocg.fx@gmail.com")
    printMessage("-----------------------------------------------")

    #Delete existing palette
    try:
        mari.palettes.remove("mGo "+IPS[0])
    except ValueError:
        pass

    global mGoWindow

    #Create mGo palette, etc
    label = PySide2.QtWidgets.QLabel("mGo "+IPS[0])
    mGo_palette = mari.palettes.create("mGo "+IPS[0], label)

    mGoWindow = widgets.QDialog()
    mGo_palette.setBodyWidget(mGoWindow)

    layout = widgets.QFormLayout()
    layout.setContentsMargins(3,3,3,3)
    layout.setLabelAlignment(PySide2.QtCore.Qt.AlignRight)
    mGoWindow.setLayout(layout)

    #Check for mGo folder and create if necessary
    mariPath=mari.resources.path('MARI_USER_PATH')
    mariPath = mariPath.replace( "\\", "/" ).rstrip( "/" )
    mGoDir = mariPath + "/mGo/"

    #Create mGo Directory if does not exists
    if not os.path.exists(mGoDir):
        os.makedirs(mGoDir)

    #Copy Presets Folder and it's files from Mari/examples/mGo/ to mGoDir
    if not os.path.exists(mGoDir+"Presets"):
        src = mari.resources.path(mari.resources.EXAMPLES) + "/mGo"
        from distutils.dir_util import copy_tree
        copy_tree(src, mariPath+"/mGo")

    #Menu Options
    fformat = ['bmp', 'jpg', 'jpeg', 'png', 'ppm', 'psd', 'tga', 'tif', 'tiff', 'xbm', 'xpm']
    fformat32 = ['exr', 'psd', 'tif', 'tiff']
    filtering = ['Default', 'Off', 'Mipmap']

    #Top layout
    top_layout = widgets.QHBoxLayout()

    #Add IP  Button
    addIP_button = widgets.QPushButton()
    addIP_button.setFixedSize(20,20)
    addIPIcon = gui.QIcon(mari.resources.path(mari.resources.ICONS) + '/Add.16x16.png')
    addIP_button.setIcon(addIPIcon)
    addIP_button.setToolTip("Add New Address")
    mari.utils.connect(addIP_button.clicked, lambda: addIP())

    #IP Combobox
    IP_combo = widgets.QComboBox()
    IP_combo.setMinimumWidth(94)
    IP_combo.setToolTip("Network Address to connect with mGo - Maya")
    IP_combo.setSizePolicy(PySide2.QtWidgets.QSizePolicy.Expanding, PySide2.QtWidgets.QSizePolicy.Fixed)

    #Populate IP Combobox
    IP_combo.addItem('Local Host Only')
    IP_combo.addItem('Network Host')
    try:
        pathfileHosts = mGoDir + "mayaHosts.txt"
        with open(pathfileHosts) as rd:
            items = rd.readlines()

        #getting rid of '\n'
        items = [s.strip() for s in items]

        #alphabetiselist
        items.sort()

        #put projects in list
        for i in items:
            IP_combo.addItem(i)
    except:
        pass

    mari.prefs.set('Scripts/Mari Command Port/port', 6100)
    if not mari.app.commandPortEnabled():
        mari.app.enableCommandPort(True)

    #For safety reasosn start mGo without Network be enabled!
    mari.prefs.set('Scripts/Mari Command Port/localhostOnly', True)

    #Check if network got enabled. If not python command above still broken.
    if mari.prefs.get('Scripts/Mari Command Port/localhostOnly') == True:
        printMessage("MARI local host Only enabled.")
        IP_combo.setCurrentIndex(IP_combo.findText('Local Host Only'))
    else:
        printMessage("MARI Network Command Port activated.")
        IP_combo.setCurrentIndex(IP_combo.findText('Network Host'))

    IP_combo.setToolTip("Network Address list: "+pathfileHosts)
    mari.utils.connect(IP_combo.currentIndexChanged['QString'], lambda: NETWORK_Switch())

    #Materialiser Presets Button
    presets_button = widgets.QPushButton()
    presets_button.setFixedSize(28,28)
    presetsIcon = gui.QIcon(mari.resources.path(mari.resources.ICONS) + '/shaderPresets.png')
    presets_button.setIcon(presetsIcon)
    presets_button.setToolTip("Open Materialiser (Load/Save Material Preset)")
    mari.utils.connect(presets_button.clicked, lambda: loadMaterialiser())

    top_layout.addWidget(IP_combo)
    top_layout.addWidget(addIP_button)
    top_layout.addWidget(presets_button)


    #Middle layout
    middle_Layout = widgets.QHBoxLayout()

    browse_line = widgets.QLineEdit()
    browse_line.setToolTip("Directory Location for saving out mGo data")

    browse_line.setMinimumWidth(200)
    browse_line.setSizePolicy(PySide2.QtWidgets.QSizePolicy.Expanding, PySide2.QtWidgets.QSizePolicy.Fixed)
    browse_button = widgets.QPushButton()
    browse_button.setFixedSize(28,28)

    bIcon = gui.QIcon(mari.resources.path(mari.resources.ICONS) + '/Folder.png')
    browse_button.setIcon(bIcon)

    middle_Layout.addWidget(browse_line)
    middle_Layout.addWidget(browse_button)
    mari.utils.connect(browse_button.clicked, lambda: browseForFolder())
    browse_button.setToolTip("Set Project Folder (for Export of Textures and mGo Description File)")

    #Middle layout 2
    middle_Layout2 = widgets.QHBoxLayout()

    Tfformat_combo_text = widgets.QLabel('File Formats')

    #8-bits Widget
    fformat_combo = widgets.QComboBox()
    fformat_combo.setMinimumWidth(47)
    fformat_combo.setSizePolicy(PySide2.QtWidgets.QSizePolicy.Expanding, PySide2.QtWidgets.QSizePolicy.Fixed)
    fformat_combo.setToolTip("Choose file extension for 8-bit files")

    for filetype in fformat :
        fformat_combo.addItem(filetype)

    fformat_combo.setCurrentIndex(fformat_combo.findText('tif'))

    #16/32-bits Widget
    fformat32_combo_text = widgets.QLabel('16/32-bit')
    fformat32_combo = widgets.QComboBox()
    fformat32_combo.setMinimumWidth(47)
    fformat32_combo.setSizePolicy(PySide2.QtWidgets.QSizePolicy.Expanding, PySide2.QtWidgets.QSizePolicy.Fixed)
    fformat32_combo.setToolTip("Choose file extension for 16/32-bit files")

    for filetype in fformat32 :
        fformat32_combo.addItem(filetype)

    fformat32_combo.setCurrentIndex(fformat32_combo.findText('exr'))

    #Filter Widget
    filter_combo_text = widgets.QLabel('Filter')
    filter_combo = widgets.QComboBox()
    filter_combo.setMinimumWidth(60)
    filter_combo.setSizePolicy(PySide2.QtWidgets.QSizePolicy.Expanding, PySide2.QtWidgets.QSizePolicy.Fixed)
    filter_combo.setToolTip("Determines texture filtering type in Maya file nodes")

    for f in filtering:
        filter_combo.addItem(f)

    filter_combo.setCurrentIndex(filter_combo.findText('Off'))
    mari.utils.connect(filter_combo.currentIndexChanged['QString'], lambda: showMipmapToolSettings())

    middle_Layout2.addWidget(fformat_combo)
    middle_Layout2.addWidget(fformat32_combo_text)
    middle_Layout2.addWidget(fformat32_combo)
    middle_Layout2.addWidget(filter_combo_text)
    middle_Layout2.addWidget(filter_combo)

    #Bottom layout
    bottom_layout = widgets.QHBoxLayout()

    export_text = widgets.QLabel('Export:')
    attExportCbox = widgets.QCheckBox()
    attExportCbox.setToolTip("Export shader ATTRIBUTES")

    attExportCbox.setCheckState(PySide2.QtCore.Qt.Checked)
    attIcon = gui.QIcon(mari.resources.path(mari.resources.ICONS) + '/Attributes.png')
    attExportCbox.setIcon(attIcon)

    chansExportCbox = widgets.QCheckBox()
    chansExportCbox.setToolTip("Export Texture CHANNELS")

    chansExportCbox.setCheckState(PySide2.QtCore.Qt.Checked)
    chansIcon = gui.QIcon(mari.resources.path(mari.resources.ICONS) + '/Channel.png')
    chansExportCbox.setIcon(chansIcon)

    objExportCbox = widgets.QCheckBox()
    objExportCbox.setToolTip("Export object GEOMETRY")

    objIcon = gui.QIcon(mari.resources.path(mari.resources.ICONS) + '/Geo.png')
    objExportCbox.setIcon(objIcon)

    camExportCbox = widgets.QCheckBox()
    camExportCbox.setToolTip("Export Mari Perspective CAMERA")

    camIcon = gui.QIcon(mari.resources.path(mari.resources.ICONS) + '/Camera.png')
    camExportCbox.setIcon(camIcon)

    lightsExportCbox = widgets.QCheckBox()
    lightsExportCbox.setToolTip("Export active LIGHTS to Maya scene")

    lightsIcon = gui.QIcon(mari.resources.path(mari.resources.ICONS) + '/Lights.png')
    lightsExportCbox.setIcon(lightsIcon)
    multiExportOptions = ['Selected OBJ', 'Visible OBJ', 'All OBJ', 'Env & Cam']

    multiExport_combo_text = widgets.QLabel('Export:')
    multiExport_combo = widgets.QComboBox()
    multiExport_combo.setMinimumWidth(93)
    multiExport_combo.setSizePolicy(PySide2.QtWidgets.QSizePolicy.Expanding, PySide2.QtWidgets.QSizePolicy.Fixed)
    multiExport_combo.setToolTip("Export Method:\nSelected Object - Exports checked data associated with currently selected object\nVisible Objects - Exports checked data associated with all visible objects\nAll Objects - Exports checked data associated with all objects\nEnv & Cam - Exports Perspective Viewport Camera and Environment Light as an HDRI dome/sky light")

    for multiExportOption in multiExportOptions:
        multiExport_combo.addItem(multiExportOption)

    multiExport_combo.setCurrentIndex(multiExport_combo.findText('Selected OBJ'))

    #Description Export
    descBtn = widgets.QPushButton()
    descBtn.setFixedSize(28,28)
    descIcon = gui.QIcon(mari.resources.path(mari.resources.ICONS) + '/script.png')
    descBtn.setIcon(descIcon)
    descBtn.setToolTip("Export as mGo Description to Project Folder")

    mari.utils.connect(descBtn.clicked, lambda: sceneExport(multiExport_combo.currentText(), "exportDescriptionOnly"))

    #Maya Export
    main_ok_button = widgets.QPushButton()
    main_ok_button.setFixedSize(28,28)
    main_ok_button.setToolTip("Export Checked Items to Maya Scene")

    mari.utils.connect(main_ok_button.clicked, lambda: sceneExport(multiExport_combo.currentText(), "exportLive2Maya"))

    okIcon = gui.QIcon(mari.resources.path(mari.resources.ICONS) + '/Forward.png')
    main_ok_button.setIcon(okIcon)

    #bottom_layout.addWidget(camExportCbox)
    #bottom_layout.addWidget(lightsExportCbox)
    #bottom_layout.addWidget(export_text)
    bottom_layout.addWidget(chansExportCbox)
    bottom_layout.addWidget(attExportCbox)
    bottom_layout.addWidget(objExportCbox)
    bottom_layout.addWidget(multiExport_combo)
    bottom_layout.addWidget(descBtn)
    bottom_layout.addWidget(main_ok_button)


    #Layout all layouts
    layout.addRow('MAYA Host', top_layout)
    layout.addRow('Output Folder', middle_Layout)
    layout.addRow('8-bit', middle_Layout2)
    layout.addRow(bottom_layout)

    #Default mari export path
    texPath = mari.resources.path('MARI_DEFAULT_EXPORT_PATH')
    texPath = texPath.replace( "\\", "/" )

    browse_line.setText(texPath)

    #Show the palette
    mGo_palette.show()
    # <------------------------ mGo UI end ------------------------>
    # <------------------------ mipmapToolSettings UI Start ------------------------>
    #Delete existing palette
    try:
        mari.palettes.remove("Mipmap Tool Settings")
    except ValueError:
        pass

    global mipmapToolSettingsWindow
    #Create Tool Settings palette, etc
    label = PySide2.QtWidgets.QLabel("Mipmap Tool Settings")
    mipmapToolSettings_palette = mari.palettes.create("Mipmap Tool Settings", label)

    mipmapToolSettingsWindow = widgets.QDialog()
    mipmapToolSettings_palette.setBodyWidget(mipmapToolSettingsWindow)

    layout = widgets.QFormLayout()
    layout.setContentsMargins(3,3,3,3)
    layout.setLabelAlignment(PySide2.QtCore.Qt.AlignRight)
    mipmapToolSettingsWindow.setLayout(layout)

    #Top layout
    top_layout = widgets.QHBoxLayout()
    top_layout.setAlignment(PySide2.QtCore.Qt.AlignLeft)

    #Add Tool/Settings Button
    addNewToolSettings_button = widgets.QPushButton()
    addNewToolSettings_button.setFixedSize(20,20)
    addNewToolSettingsIcon = gui.QIcon(mari.resources.path(mari.resources.ICONS) + '/Add.16x16.png')
    addNewToolSettings_button.setIcon(addNewToolSettingsIcon)
    addNewToolSettings_button.setToolTip("Add a New Settings")
    mari.utils.connect(addNewToolSettings_button.clicked, lambda: addNewToolSettings())

    #toolSettings Combobox
    toolSettings_combo = widgets.QComboBox()
    toolSettings_combo.setMinimumWidth(105)
    toolSettings_combo.setSizePolicy(PySide2.QtWidgets.QSizePolicy.Expanding, PySide2.QtWidgets.QSizePolicy.Fixed)
    toolSettings_combo.setToolTip("img2tiledexr for Vray - file format exr.\nmaketx for Arnold - file format tx.")

    #have to start empty and leave it the setup to initialToolSettings function.
    toolSettings_combo.setCurrentIndex(toolSettings_combo.findText(''))
    toolSettings_combo.setToolTip("Switch between any registered Settings.")

    top_layout.addWidget(toolSettings_combo)
    top_layout.addWidget(addNewToolSettings_button)

    #Middle layout
    middle_Layout = widgets.QHBoxLayout()

    toolPath_line = widgets.QLineEdit()
    toolPath_line.setToolTip("Path to where the texture conversion application is installed")
    toolPath_line.setSizePolicy(PySide2.QtWidgets.QSizePolicy.Expanding, PySide2.QtWidgets.QSizePolicy.Fixed)

    browseMipmapTool_button = widgets.QPushButton()
    browseMipmapTool_button.setFixedSize(28,28)

    btIcon = gui.QIcon(mari.resources.path(mari.resources.ICONS) + '/Lookup.png')
    browseMipmapTool_button.setIcon(btIcon)
    browseMipmapTool_button.setToolTip("Set the path to the texture conversion application")

    mari.utils.connect(browseMipmapTool_button.clicked, lambda: browseMipmapTool())

    middle_Layout.addWidget(toolPath_line)
    middle_Layout.addWidget(browseMipmapTool_button)

    #Middle layout 2
    middle_Layout2 = widgets.QHBoxLayout()

    options_line = widgets.QLineEdit()
    options_line.setToolTip("Type in extra flags related to how the texture will be processed during the conversion")
    options_line.setSizePolicy(PySide2.QtWidgets.QSizePolicy.Expanding, PySide2.QtWidgets.QSizePolicy.Fixed)

    middle_Layout2.addWidget(options_line)

    #Bottom layout
    bottom_layout = widgets.QHBoxLayout()

    subFolder_line = widgets.QLineEdit()
    subFolder_line.setToolTip("Enter a name of the folder where the converted textures will be saved out (Optional)\n*Note: This Subfolder will be created inside the previusly path defined by 'Output Folder' at the 'mGo' UI.\n  Output Folder: "+browse_line.text())
    subFolder_line.setSizePolicy(PySide2.QtWidgets.QSizePolicy.Expanding, PySide2.QtWidgets.QSizePolicy.Fixed)
    subFolder_line.setText("converted")

    extMipmap_Combo = widgets.QComboBox()
    extMipmap_Combo.setMinimumWidth(47)
    extMipmap_Combo.addItem('exr')
    extMipmap_Combo.addItem('tx')
    extMipmap_Combo.setCurrentIndex(extMipmap_Combo.findText('exr'))
    extMipmap_Combo.setToolTip("Chose the file format for your converted texture")

    #Save Tool Settings
    saveSettings = widgets.QPushButton("Save Settings")
    saveSettings.setToolTip("Save current settings")
    saveSettingsIcon = gui.QIcon(mari.resources.path(mari.resources.ICONS) + '/Preference.png')
    saveSettings.setIcon(saveSettingsIcon)

    mari.utils.connect(saveSettings.clicked, lambda: saveToolSettings(""))

    bottom_layout.addWidget(subFolder_line)
    bottom_layout.addWidget(extMipmap_Combo)
    bottom_layout.addWidget(saveSettings)

    #Layout all layouts
    layout.addRow("Settings", top_layout)
    layout.addRow("Tool path", middle_Layout)
    layout.addRow("Options", middle_Layout2)
    layout.addRow("Subfolder", bottom_layout)
    #In case you restart mGo!
    try:
        mipmapToolSettings_palette.hide()
    except:
        pass
    # <------------------------ mipmapToolSettings UI end ------------------------>
    # <------------------------ Mipmap Tool Settings UI Functions start ------------------------>
    #Populate toolSettings Combobox
    def populateToolSettings_Combobox():
        toolSettings_pathfile = mGoDir + "mipmap_tool_settings.txt"
        with open(toolSettings_pathfile) as rd:
            #read each line
            for line in rd:
                projectName_line = line.split("Project name:", 1)[1].split(",", 1)[0]
                #only add to the combobox settings with empty projects(think this as a 'default preset').
                if projectName_line == "":
                    settingsName = line.split("Settings:", 1)[1].split(",", 1)[0]
                    toolSettings_combo.addItem(settingsName)

    #Function to add new settings name for the 'Mipmap Tool Settings' UI
    def addNewToolSettings():
        global Add_NewToolSettings
        #UI Window
        Add_NewToolSettings = widgets.QDialog()
        Add_NewToolSettings.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        layout = widgets.QVBoxLayout()
        Add_NewToolSettings.setLayout(layout)
        Add_NewToolSettings.setWindowTitle("Add New Settings")

        text_layout = widgets.QHBoxLayout()
        settingsName_label = widgets.QLabel('Enter a name for your Settings:')

        #Settings Text Field
        addSettings_Layout = widgets.QHBoxLayout()
        settingsName_line = widgets.QLineEdit()
        settingsName_line.setFixedSize(159,20)
        settingsName_line.setSizePolicy(PySide2.QtWidgets.QSizePolicy.Fixed, PySide2.QtWidgets.QSizePolicy.Fixed)
        settingsName_line.setToolTip("Enter a name for a new settings")

        #Define the layout for buttons
        buttons_layout = widgets.QHBoxLayout()

        #Confirm Button
        confirmToolNameButton = widgets.QPushButton("OK")
        confirmToolNameButton.setToolTip("Confirm entered name")
        mari.utils.connect(confirmToolNameButton.clicked, lambda: confirmToolName())

        #Cancel Button
        cancelToolName = widgets.QPushButton("Cancel")
        mari.utils.connect(cancelToolName.clicked, lambda: Add_NewToolSettings.close())

        #Add the widgets to the layouts
        text_layout.addWidget(settingsName_label)

        addSettings_Layout.addWidget(settingsName_line)
        buttons_layout.addWidget(confirmToolNameButton)
        buttons_layout.addWidget(cancelToolName)

        #Finish the layout
        layout.addLayout(text_layout)
        layout.addLayout(addSettings_Layout)
        layout.addLayout(buttons_layout)

        #Display Floating Window
        Add_NewToolSettings.show()

        def confirmToolName():
            if settingsName_line.text() != "":
                settingsName = str(settingsName_line.text())

                toolSettings_pathfile = mGoDir + "mipmap_tool_settings.txt"
                with open(toolSettings_pathfile) as rd:
                    lines = rd.readlines()
                    #getting rid of '\n'
                    lines = [s.strip() for s in lines]

                    #seek the entered registered settings names with same name
                    i = 0
                    count = 0
                    settingsCounted = toolSettings_combo.count()
                    while i < settingsCounted:
                        if settingsName == toolSettings_combo.itemText(i) or settingsName == toolSettings_combo.itemText(i)[:-1]:
                            count +=1
                        i +=1

                    #If count is !=0 popup msg asking for name incrementation or for close the 'add' function completly!
                    if count != 0:
                        titleTXT = "Entered Settings WARNING"
                        messageTXT = "Enter a unique name for your Settings."
                        mymessage = widgets.QMessageBox()
                        Add_NewToolSettings.setWindowFlags(QtCore.Qt.WindowStaysOnBottomHint)
                        mymessage.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
                        if mymessage.warning(None, titleTXT, messageTXT, widgets.QMessageBox.Ok | widgets.QMessageBox.Close) != widgets.QMessageBox.Close:
                            Add_NewToolSettings.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
                            Add_NewToolSettings.show()
                            #if you have settingsName1 or settingsName2...
                            if count > 1:
                                settingsName_line.setText(settingsName[:-1]+str(count))
                            else:
                                settingsName_line.setText(settingsName+str(count))
                            return
                        else:
                            printMessage("Couldn't add a new Settings! Please add a Settings with a unique name.")
                            Add_NewToolSettings.close()
                            return

                #disconnect to avoid spawning msg during populate menu function!
                mari.utils.disconnect(toolSettings_combo.activated[str], lambda: toolSettings_Switch())

                toolSettings_combo.addItem(settingsName)
                toolSettings_combo.setCurrentIndex( toolSettings_combo.findText(settingsName) )
                toolPath_line.clear()
                options_line.clear()
                printMessage("New Settings added.")
                #print "Remember to Save Settings after complete the parameters setup."

                #only make this avaliable after populate the menu, cause not, it will spawn twice the switch function!
                mari.utils.connect(toolSettings_combo.activated[str], lambda: toolSettings_Switch())

            #close the popup window
            Add_NewToolSettings.close()

    #Function to save to a file the settings for the 'Mipmap Tool Settings' UI
    def saveToolSettings(projectName):
        #write to a txt file the initial settings
        toolSettings_pathfile = mGoDir + "mipmap_tool_settings.txt"

        settingsName = str(toolSettings_combo.currentText())
        toolPath = str(toolPath_line.text()).replace( "\\", "/" )
        options = str(options_line.text())
        Subfolder = str(subFolder_line.text())
        extMipmap = str(extMipmap_Combo.currentText())
        toolSettings = "Project name:"+projectName+", Settings:"+settingsName+", Tool path:"+toolPath+", Options:"+options+", Subfolder:"+Subfolder+", Mipmap File Extension:"+extMipmap

        newToolSettings = []
        with open(toolSettings_pathfile) as rd:
            lines = rd.readlines()
            #getting rid of '\n'
            lines = [s.strip() for s in lines]
            #If projectName == "", save new settings
            if projectName == "":
                #seek the registered settings for tools with same name
                for line in lines:
                    projectNameRegistered = line.split("Project name:", 1)[1].split(",", 1)[0]
                    settingsNameRegistered = line.split("Settings:", 1)[1].split(",", 1)[0]
                    #check if the settingsName now is unique like settingsName1, settingsName2, settingsName3...
                    if settingsName == settingsNameRegistered and projectNameRegistered == "":
                        titleTXT = "Save Settings WARNING"
                        messageTXT = "Found a Settings with the same name, want to Overwrite it?"
                        mymessage = widgets.QMessageBox()
                        mymessage.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
                        if mymessage.warning(None, titleTXT, messageTXT, widgets.QMessageBox.Ok | widgets.QMessageBox.Close) == widgets.QMessageBox.Close:
                            return
                    else:
                        newToolSettings.append(line)
                #After the loop, If you got here it means the settingsName is unique, so append it to the settings.
                newToolSettings.append(toolSettings)

            #Else projectName != "", save settings for this opened project
            else:
                #seek the registered settings for project names
                for line in lines:
                    projectNameRegistered = line.split("Project name:", 1)[1].split(",", 1)[0]
                    #append the read line to the new settings avoding any existing registered project found.
                    if projectName != projectNameRegistered:
                        newToolSettings.append(line)
                #after loop append the current settings to the new settings, so it will update any existing registered project found.
                newToolSettings.append(toolSettings)

        #Overwrite the file with the updated settings.
        f = open(toolSettings_pathfile, 'w')
        for settings in newToolSettings:
            f.write(settings+"\n")
        f.close()
        printMessage("Tool Settings saved.")

        # populate only when the user is Save Settings manually by pressed the Save button after the user had added a new tool through the plus button...
        if projectName == "":
            #disconnect to avoid spawning msg during populate menu function!
            mari.utils.disconnect(toolSettings_combo.activated[str], lambda: toolSettings_Switch())
            #update the toolSettings combobox
            toolSettings_combo.clear()
            populateToolSettings_Combobox()
            toolSettings_combo.setCurrentIndex( toolSettings_combo.findText(settingsName) )
            #only make this avaliable after populate the menu, cause not, it will spawn twice the switch function!
            mari.utils.connect(toolSettings_combo.activated[str], lambda: toolSettings_Switch())

    #Function to update the UI accordingly to the readed settings for the 'Mipmap Tool Settings' UI
    def toolSettings_Switch():
        toolSettings_pathfile = mGoDir + "mipmap_tool_settings.txt"
        with open(toolSettings_pathfile) as rd:
            #read each line
            for line in rd:
                projectName_line = line.split("Project name:", 1)[1].split(",", 1)[0]
                settingsName = line.split("Settings:", 1)[1].split(",", 1)[0]
                #Load the default tool settings that starts with mGo, so the user could always start fresh if he switch combobox to default entries...
                if str(toolSettings_combo.currentText()) == settingsName and projectName_line == "":
                    toolPath_line.setText( line.split("Tool path:", 1)[1].split(",", 1)[0] )
                    options_line.setText( line.split("Options:", 1)[1].split(",", 1)[0] )
                    subFolder_line.setText( line.split("Subfolder:", 1)[1].split(",", 1)[0] )
                    #get rid of '\n' in the end of the line
                    extMipmap = str(line.split("Mipmap File Extension:", 1)[1])[:-1]
                    extMipmap_Combo.setCurrentIndex( extMipmap_Combo.findText(extMipmap) )
                    return

    #Function to read the settings from a file for the 'Mipmap Tool Settings' UI
    def readToolSettings():
        #try to load one of the settings accordingly to the current shader.
        shaderType = []
        try:
            geo = mari.geo.current()
            if geo.currentShader().isLayeredShader():
                channels = geo.currentShader().channelList()
                newShader = channels[0].layerList()
                curShader = newShader[0].shader()
                shaderType = str(curShader.getParameter("shadingNode"))
            else:
                curShader = geo.currentShader()
                shaderType = str(curShader.getParameter("shadingNode"))
        except:
            pass

        toolSettings_pathfile = mGoDir + "mipmap_tool_settings.txt"

        #the current opened project in Mari does exists it's not registered in the log, see if at least they are using one of the supported shaders.
        printMessage("Project is new trying to load settings accordingly to the current selected shader.")
        with open(toolSettings_pathfile) as rd:
            #read each line
            for line in rd:
                if shaderType == "Ai Standard":
                    #if the shader is 'Ai Standard', find the tool named: 'maketx'
                    settingsName = line.split("Settings:", 1)[1].split(",", 1)[0]
                    line = line.split("Settings:", 1)[1].split(",", 1)[1]
                    if settingsName == "maketx":
                        printMessage("Detected shader: '"+shaderType+"'")
                        printMessage("Loading " +settingsName+ " settings")
                        #Changing the combobox will call the function to load their settings
                        toolSettings_combo.setCurrentIndex( toolSettings_combo.findText(settingsName) )
                        return
                elif shaderType == "VRay Mtl":
                    #if the shader is 'VRay Mtl', find the tool named: 'img2tiledexr'
                    settingsName = line.split("Settings:", 1)[1].split(",", 1)[0]
                    line = line.split("Settings:", 1)[1].split(",", 1)[1]
                    if settingsName == "img2tiledexr":
                        printMessage("Detected shader: '"+shaderType+"'")
                        printMessage("Loading " +settingsName+ " settings")
                        #Changing the combobox will call the function to load their settings
                        toolSettings_combo.setCurrentIndex( toolSettings_combo.findText(settingsName) )
                        return
                else:
                    toolSettings_combo.setCurrentIndex( toolSettings_combo.findText("") )
                    printMessage("Warning - Couldn't detect what shader type you are using!")
                    return


    #Function to select the path to where the conversion tool application is instaled for the 'Mipmap Tool Settings' UI.
    def browseMipmapTool():
        dirname = str(widgets.QFileDialog.getOpenFileName(dir=toolPath_line.text(), caption="Select Directory where the tool application is located")[0])
        if dirname:
            dirname = dirname.replace( "\\", "/" )
            toolPath_line.setText(dirname)

    #Function to initalize the settings for 'Mipmap Tool Settings' UI
    def initialToolSettings():
        #workaround if there is no project opened!
        try:
            projNameStr = str(mari.projects.current().name())
        except:
            projNameStr = "none"

        toolSettings_pathfile = mGoDir + "mipmap_tool_settings.txt"
        #first time here, create the file Tool Settings with some initial settings
        if not os.path.exists(toolSettings_pathfile):
            arnold_tool_envpath = ""
            vray_tool_envPath = ""

            import platform
            platform = str(platform.system())
            #try to find environment path for Arnold maketx
            arnoldEnvPaths = ['ARNOLD_PLUGIN_PATH', 'maketx']
            for arnoldEnvPath in arnoldEnvPaths:
                try:
                    arnold_tool_envpath = os.environ[arnoldEnvPath]
                    arnold_tool_envpath = arnold_tool_envpath.replace( "\\", "/" )
                    if platform == "Windows":
                        if arnold_tool_envpath.rsplit("/", 1)[1] != "maketx.exe":
                            arnold_tool_envpath +="/maketx.exe"
                    elif platform == "darwin":
                        if arnold_tool_envpath.rsplit("/", 1)[1] != "maketx":
                            arnold_tool_envpath +="/maketx.app"
                    else:
                        if arnold_tool_envpath.rsplit("/", 1)[1] != "maketx":
                            arnold_tool_envpath +="/maketx"
                except:
                    pass

            #try to find environment path for Vray img2tiledexr
            i = 9
            while i >= 1: #Loop through Maya 2019-2011
                try:
                    vray_tool_envPath = os.environ['VRAY_TOOLS_MAYA201'+str(i)+'_x64']
                    vray_tool_envPath = vray_tool_envPath.replace( "\\", "/" )
                    if platform == "Windows":
                        if vray_tool_envPath.rsplit("/", 1)[1] != "img2tiledexr.exe":
                            vray_tool_envPath +="/img2tiledexr.exe"
                    elif platform == "darwin":
                        if vray_tool_envPath.rsplit("/", 1)[1] != "img2tiledexr.exe":
                            vray_tool_envPath +="/img2tiledexr.app"
                    else:
                        if vray_tool_envPath.rsplit("/", 1)[1] != "img2tiledexr":
                            vray_tool_envPath +="/img2tiledexr"
                    break
                except:
                    pass
                i = i-1

            vraySettings = "Project name:, Settings:img2tiledexr, Tool path:"+vray_tool_envPath+", Options:-linear auto -tileSize 64, Subfolder:converted, Mipmap File Extension:exr"
            arnoldSettings = "Project name:, Settings:maketx, Tool path:"+arnold_tool_envpath+", Options:--oiio --tile 64 64, Subfolder:converted, Mipmap File Extension:tx"
            toolSettings = [vraySettings, arnoldSettings]

            #write to a txt file the initial settings
            f = open(toolSettings_pathfile, 'a+')
            for	settings in toolSettings:
                f.write(settings+"\n")
            f.close()

            #call the function to populate the combobox first
            populateToolSettings_Combobox()
            #call the function to read the file with default tool settings
            readToolSettings()
            #only make this avaliable after populate the menu, cause not, it will spawn twice the switch function!
            mari.utils.connect(toolSettings_combo.activated[str], lambda: toolSettings_Switch())
        else:
            #call the function to populate the combobox first
            populateToolSettings_Combobox()
            #open the tool settings file
            with open(toolSettings_pathfile) as rd:
                #read each line
                for line in rd:
                    #seek the registered settings for project names
                    projectName_line = line.split("Project name:", 1)[1].split(",", 1)[0]
                    #compare any found project name with the current opened project
                    if projectName_line == projNameStr:
                        #Project name founded in the logged of the file 'toolSettings'
                        settingsName = line.split("Settings:", 1)[1].split(",", 1)[0]
                        line = line.split("Settings:", 1)[1].split(",", 1)[1]
                        printMessage("Loading " +settingsName+ " settings")
                        #Changing the combobox will call the function to load their settings
                        toolSettings_combo.setCurrentIndex( toolSettings_combo.findText(settingsName) )
                        toolPath_line.setText( line.split("Tool path:", 1)[1].split(",", 1)[0] )
                        options_line.setText( line.split("Options:", 1)[1].split(",", 1)[0] )
                        subFolder_line.setText( line.split("Subfolder:", 1)[1].split(",", 1)[0] )
                        #get rid of '\n' in the end of the line
                        extMipmap = str(line.split("Mipmap File Extension:", 1)[1])[:-1]
                        extMipmap_Combo.setCurrentIndex( extMipmap_Combo.findText(extMipmap) )
                        #only make this avaliable after populate the menu, cause not, it will spawn twice the switch function!
                        #comboBox.connect(comboBox,SIGNAL("currentIndexChanged(int)"), window,SLOT("onIndexChange(int)"))
                        mari.utils.connect(toolSettings_combo.activated[str], lambda: toolSettings_Switch())
                        return

            #if after the loop couldn't find a project name in the log of the 'toolSettings' file that matches the current project opened,
            #call the function to read the file with default tool settings
            readToolSettings()
            #only make this avaliable after populate the menu, cause not, it will spawn twice the switch function!
            mari.utils.connect(toolSettings_combo.activated[str], lambda: toolSettings_Switch())

    #Function to show the 'Mipmap Tool Settings' UI
    def showMipmapToolSettings():
        #If Mipmap get selected in the filter combo, Show the palette
        if str(filter_combo.currentText()) == "Mipmap":
            initialToolSettings()
            mipmapToolSettings_palette.show()
        else:
            try:
                mipmapToolSettings_palette.hide()
                #this is for get rid of any non-saved toolSettings added
                toolSettings_combo.clear()
            except ValueError:
                pass
    # <------------------------ Mipmap Tool Settings UI Functions end ------------------------>
    # <------------------------ mGo UI Functions start ------------------------>
    #Function switch IP_combo at 'mGo' UI
    def NETWORK_Switch():
        mayaHost = 'localhost'
        #Interpreting IP Menu
        if str(IP_combo.currentText()) == "Local Host Only":
            mayaHost = 'localhost'
        elif str(IP_combo.currentText()) == "Network Host":
            mayaHost = IPS[0]
        else:
            mayaHost = str(IP_combo.currentText())

        #print "Trying to switch to Address: '" + mayaHost + "'"
        #Set port 6100 just for sake and enable the Command Port
        mari.prefs.set('Scripts/Mari Command Port/port', 6100)
        if not mari.app.commandPortEnabled():
            mari.app.enableCommandPort(True)

        #Check Network Statement
        if str(IP_combo.currentText()) == "Local Host Only":
            #Tick the localhostOnly option to disable the Network Connection
            mari.prefs.set('Scripts/Mari Command Port/localhostOnly', True)
            printMessage("MARI local host Only enabled.")

        elif str(IP_combo.currentText()) == "Network Host":
            #Untick the localhostOnly option to disable the Network Connection
            mari.prefs.set('Scripts/Mari Command Port/localhostOnly', False)
            printMessage("MARI Network Command Port activated.")

        else:
            #Untick the localhostOnly option to disable the Network Connection
            mari.prefs.set('Scripts/Mari Command Port/localhostOnly', False)
            #Check if it worked. Else python command above still broken, report to the user.
            printMessage("MARI Network Command Port activated.")

    #Function add IP to the 'mGo' UI
    def addIP():
        global Add_IP
        #UI Window
        Add_IP = widgets.QDialog()
        Add_IP.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        layout = widgets.QVBoxLayout()
        Add_IP.setLayout(layout)
        Add_IP.setWindowTitle("Add IP")

        text_layout = widgets.QHBoxLayout()
        address_text = widgets.QLabel('Enter New Address:')

        #IP Text Field
        middle_IP_Layout = widgets.QHBoxLayout()
        IP_line = widgets.QLineEdit()
        IP_line.setFixedSize(159,20)
        IP_line.setSizePolicy(PySide2.QtWidgets.QSizePolicy.Fixed, PySide2.QtWidgets.QSizePolicy.Fixed)
        IP_line.setToolTip("Enter the Network Adress of the other machine")

        #Define the layout for buttons
        buttons_layout = widgets.QHBoxLayout()

        #Confirm Button
        confirmAddressButton = widgets.QPushButton("OK")
        confirmAddress_icon = gui.QIcon(mari.resources.path(mari.resources.ICONS) + '/CommandPort.png')
        confirmAddressButton.setIcon(confirmAddress_icon)
        confirmAddressButton.setToolTip("Confirm entered address")
        mari.utils.connect(confirmAddressButton.clicked, lambda: confirmAddress())

        #Cancel Button
        cancelAddress = widgets.QPushButton("Cancel")
        cancelAddress.setFixedSize(77,28)
        mari.utils.connect(cancelAddress.clicked, lambda: Add_IP.close())

        #Add the widgets to the layouts
        text_layout.addWidget(address_text)

        middle_IP_Layout.addWidget(IP_line)
        buttons_layout.addWidget(confirmAddressButton)
        buttons_layout.addWidget(cancelAddress)

        #Finish the layout
        layout.addLayout(text_layout)
        layout.addLayout(middle_IP_Layout)
        layout.addLayout(buttons_layout)

        #Display Floating Window
        Add_IP.show()

        #Function to pass the entered address
        def confirmAddress():
            printMessage("Entered Address: '" + IP_line.text() + "'")

            #Write to the file the entered address
            pathfileHosts = mGoDir + "mayaHosts.txt"

            #Try read the file and see if the address already exists in the file
            addressExist = False
            try:
                with open(pathfileHosts) as rd:
                    items = rd.readlines()

                #getting rid of '\n'
                items = [s.strip() for s in items]

                for i in items:
                    if i == IP_line.text():
                        addressExist = True
            except:
                pass

            #If address does not exists then do what it is needed
            if addressExist == False:
                f = open(pathfileHosts, 'a+')
                f.write(IP_line.text() +'\n')
                f.close()

                with open(pathfileHosts) as rd:
                    items = rd.readlines()

                #getting rid of '\n'
                items = [s.strip() for s in items]

                #alphabetiselist
                items.sort()

                #put projects in list
                for i in items:
                    IP_combo.removeItem(IP_combo.findText(i))
                    IP_combo.addItem(i)

            #Close Window
            Add_IP.close()

            #Set the IP combobox to the entered address which will also call the function NETWORK_Switch
            newIP = IP_line.text()
            IP_combo.setCurrentIndex( IP_combo.findText(newIP) )

    #Function to select the Ouput Folder in 'mGo' UI
    def browseForFolder():
        dirname = str(widgets.QFileDialog.getExistingDirectory(dir=browse_line.text(), caption="Select Directory for Channels Export and mGo Description File"))
        if dirname:
            dirname = dirname.replace( "\\", "/" )
            browse_line.setText(dirname)
    # <------------------------ mGo UI Functions end ------------------------>
    # <------------------------ Load mGo Settings in a project basis...	start ------------------------>
    #it needs to be after the Mipmap Tool Settings UI get loaded!
    try:
        log_pathfile = mGoDir + "mGo_Settings.txt"
        log_pathfile = log_pathfile.replace('\\', '/').rstrip( "/" )
        with open(log_pathfile) as rd:
            for line in rd:
                projNameLog = line.split("Project Name:", 1)[1].split(",", 1)[0]
                if projNameLog == mari.projects.current().name():
                    mayaHostLog = line.split("MAYA Host:", 1)[1].split(",", 1)[0]
                    IP_combo.setCurrentIndex( IP_combo.findText(mayaHostLog) )

                    outputFolderLog = line.split("Output Folder:", 1)[1].split(",", 1)[0]
                    browse_line.setText(outputFolderLog[:-1]) #take of the last char '/'

                    bits8Log = line.split("8-bits:", 1)[1].split(",", 1)[0]
                    fformat_combo.setCurrentIndex( fformat_combo.findText(bits8Log) )

                    bits32Log = line.split("16/32-bits:", 1)[1].split(",", 1)[0]
                    fformat32_combo.setCurrentIndex( fformat32_combo.findText(bits32Log) )

                    filterLog = line.split("Filter:", 1)[1].split(",", 1)[0]
                    filter_combo.setCurrentIndex( filter_combo.findText(filterLog) )

                    exportChansLog = line.split("Export Channels:", 1)[1].split(",", 1)[0]
                    if exportChansLog == "True":
                        chansExportCbox.setCheckState(PySide2.QtCore.Qt.Checked)
                    else:
                        chansExportCbox.setCheckState(PySide2.QtCore.Qt.Unchecked)

                    exportAttrLog = line.split("Export Attributes:", 1)[1].split(",", 1)[0]
                    if exportAttrLog == "True":
                        attExportCbox.setCheckState(PySide2.QtCore.Qt.Checked)
                    else:
                        attExportCbox.setCheckState(PySide2.QtCore.Qt.Unchecked)

                    exportGeoLog = line.split("Export Geo:", 1)[1].split(",", 1)[0]
                    if exportGeoLog == "True":
                        objExportCbox.setCheckState(PySide2.QtCore.Qt.Checked)
                    else:
                        objExportCbox.setCheckState(PySide2.QtCore.Qt.Unchecked)

                    exportOptionsLog = line.split("Export Options:", 1)[1].split(",", 1)[0]
                    multiExport_combo.setCurrentIndex( multiExport_combo.findText(exportOptionsLog[:-1]) ) #get rid of '\n'
    except:
        pass
    # <------------------------ Load mGo Settings in a project basis...	end ------------------------>
    # <------------------------ Main mGo Function start ------------------------>
    # Export Geo, Channels, Attributes and shaders
    def go(exportOption, geo, curShader):

        # <------------------------ Function to Rename Name Spaces	------------------------>
        #Function to better rename channels, shaders, and avoid incompatability with Maya (will crash otherwise)
        def replace_name_spaces(old_name):
            illegalCharactersList = ["!", ":", "@", "#", "$", "%", "&", "*", "+", "{", "}", "[", "]", ",", ".", " ", "(", ")", "-"]
            for illegalChar in illegalCharactersList:
                new_name = old_name.replace(illegalChar, "_")
                old_name = new_name
            return new_name;


        # <------------------------ Mipmap Conversion of the Exported Channels used by a Shader ------------------------>
        def mipmapConversion(exportDir, geoName, chanName, coordinates, ext):
            global subprocessExportStatus
            if subprocessExportStatus != False:
                #This 'try' is here in case the toolpath is wrong!
                try:
                    toolPath = str(toolPath_line.text()).replace( "\\", "/" )
                    options = str(options_line.text())
                    Subfolder = str(subFolder_line.text())
                    extMipmap = str(extMipmap_Combo.currentText())

                    for coordinate in coordinates:
                        file_path = exportDir + geoName + "_" + chanName + "_" + coordinate + "." + ext
                        convertedFile_path = exportDir + geoName + "_" + chanName + "_" + coordinate + "." + extMipmap
                        destFolder = exportDir + Subfolder + "/"
                        destFile_path = destFolder + geoName + "_" + chanName + "_" + coordinate + "." + extMipmap

                        args = [toolPath, file_path]
                        if options != "":
                            optionsList = options.split()
                            for option in optionsList:
                                args.append(option)

                        subprocess.call(args)

                        if not os.path.exists(destFolder):
                            os.makedirs(destFolder)

                        #This try is here in case the subprocess for some reason does not create the file!
                        try:
                            #search and rename any postfix naming convention.
                            #this is a particularly case of the img2tiledexr tool from vray
                            postfixFile_path = exportDir + geoName + "_" + chanName + "_" + coordinate + "_tiled." + extMipmap
                            if os.path.exists(postfixFile_path):
                                postfixDestFile_path = destFolder + geoName + "_" + chanName + "_" + coordinate + "_tiled." + extMipmap
                                shutil.move(postfixFile_path, postfixDestFile_path)
                                if os.path.exists(destFile_path):
                                    os.remove(destFile_path)
                                os.rename(postfixDestFile_path, destFile_path)
                            else:
                                #this need to be in here because it could be a scenario that both postfixFile_path and convertedFile_path exists!
                                #so keeping the postfixFile_path existence as primary to investigate is priority, since if postfixFile_path exists we will have to deal with it
                                #and not with convertedFile_path
                                shutil.move(convertedFile_path, destFile_path)
                            #also keep in mind would be better in peformance if during the subprocess we create the image directly in the subfolder instead of move the file...
                            #but this imply in lock our flags and conversition tools to some sort of specific scenario... while this way, it's more easy to handle from the user perspective.
                        except:
                            printMessage("FAIL - Make sure that your entered Options flags are correct!")

                except:
                    printMessage("ERROR - Any Mipmap conversion process will be aborted!")
                    printMessage("Make sure that the path to your Tool is correct!")
                    subprocessExportStatus = False
            else:
                return


        # <------------------------ Generate Channels HASH ------------------------>
        def generateHASH(channel, metadataIndex, uvIndex, coordinate):
            #Every time start fresh before collect data.
            sha256 = hashlib.sha256()
            _HASHDATA = []
            #The first time you got in here store the strings related to Colorspace settings.
            if metadataIndex == 0:
                _HASHDATA.append( channel.colorspaceConfig().resolveColorspace(mari.ColorspaceConfig.ColorspaceStage.COLORSPACE_STAGE_NATIVE) )
                _HASHDATA.append( channel.colorspaceConfig().resolveColorspace(mari.ColorspaceConfig.ColorspaceStage.COLORSPACE_STAGE_OUTPUT) )
                _HASHDATA.append( channel.colorspaceConfig().resolveColorspace(mari.ColorspaceConfig.ColorspaceStage.COLORSPACE_STAGE_WORKING) )
                _HASHDATA.append( channel.scalarColorspaceConfig().resolveColorspace(mari.ColorspaceConfig.ColorspaceStage.COLORSPACE_STAGE_NATIVE) )
                _HASHDATA.append( channel.scalarColorspaceConfig().resolveColorspace(mari.ColorspaceConfig.ColorspaceStage.COLORSPACE_STAGE_OUTPUT) )
                _HASHDATA.append( channel.scalarColorspaceConfig().resolveColorspace(mari.ColorspaceConfig.ColorspaceStage.COLORSPACE_STAGE_WORKING) )
            else:
                #Second time or more you got in here? Get channels HASH.
                _uvIndex = int(uvIndex)
                coordinate = int(coordinate)
                _HASHDATA.append( channel.hash(coordinate) )
                _HASHDATA.append( channel.imageHash(coordinate) )
                _HASHDATA.append( channel.channelNode().hash(UVIndex=_uvIndex) )

            sha256.update( str(_HASHDATA).encode("utf-8") )

            return	sha256.hexdigest();


        # <------------------------ Export Channels used by a Shader ------------------------>
        def exportChannelPatch(channel, channelDepth):
            Subfolder = str(subFolder_line.text())
            extMipmap = str(extMipmap_Combo.currentText())
            ext = []
            #Check what is the Channel Bit Depth to pick the right extension accordingly to what the user has set in the mGo UI combobox.
            if int(channelDepth) == 8:
                ext = ext8
            else:
                ext = ext32

            #Start the process of Check File Existance in the Output Directory, check if the Channel has the Metadata and if each Patch HASH matches or if it has updates.
            metadataIndex = 0
            uvIndexes = []
            coordinates = []
            chanName = replace_name_spaces(channel.name())
            #It's good to start fresh in case a Patch had been added or removed from the Geo, or in case anything weird had happend to Geo's Patches.
            #This array will get all the HASH before update the Channel Metadata.
            HASH = []
            #1st Step - Check if the Channel has a Metadata that could had been previusly stored in any past mGo exportation process.
            if channel.hasMetadata("Channel_HASH") == True:
                #Print the stored HASH from the Channel Metadata.
                channelMetadata = channel.metadataItemList("Channel_HASH")
                #print "OLD STORED METADATA: " + str(channelMetadata)

                #Generates the first HASH based on the Channel/System Colorspaces.
                generatedHASH = generateHASH(channel, metadataIndex, 0, 0)
                HASH.append(generatedHASH)

                #2nd Step - Compare the generatedHASH with the first item of the Metadata list that is responsible for Channel/System Colorspaces.
                if generatedHASH == channelMetadata[metadataIndex]:
                    #3rd Step - generatedHASH and stored Metadata HASH are equal, loop over the Patches
                    for patch in geo.patchList():
                        metadataIndex +=1
                        #Generates the HASH for each Patch and append it.
                        generatedHASH = generateHASH(channel, metadataIndex, patch.uvIndex(), patch.name())
                        HASH.append(generatedHASH)

                        #Get what is going to be the path and File name to the Patch that is going to be exported.
                        file_path = exportDir + geoName + "_" + chanName + "_" + patch.name() + "." + ext

                        #4th Step - See if the File related to the Current Channel Patch exists in the Output Directory.
                        if os.path.exists(file_path) == True:
                            #5th Step - File related to the Current Channel exists, check if the generatedHASH is equal to the HASH stored in the current Index of the Metadata
                            if generatedHASH == channelMetadata[metadataIndex]:
                                #6th Step - generatedHASH and Metadata HASH stored in the current Index are equal, SKIP the Patch.
                                printMessage("The pixels of the patch: '" +patch.name()+ "' of the channel: '" +chanName+ "' have not been changed.")
                                printMessage("Skipping that patch exportation.")
                                #For this case where the pixels didn't had changed and the exported file exists in the folder,
                                #Check if the converted file does exist in the subfolder, if does not exist convert the already exported file found in the Ouput folder,
                                #and move the converted file to the subfolder.
                                destFolder = exportDir + Subfolder +"/"
                                destFile_path = destFolder + geoName + "_" + chanName + "_" + patch.name() + "." + extMipmap
                                if not os.path.exists(destFile_path) and subprocessExportStatus != False:
                                    printMessage("Mipmap converted file of the patch: '" +patch.name()+ "'  does not exist, converting it.")
                                    #mipmapConversion(exportDir, geoName, chanName, coordinate, ext)
                                    coordinates.append(patch.name())
                            else:
                                #6th Step - generatedHASH and Metadata HASH stored in the current Index are NOT equal, Export the Patch.
                                uvIndexes.append(patch.uvIndex())
                                coordinates.append(patch.name())
                        else:
                            #5th Step - No file related to the Current Channel exists in the Output Directory, Export the Current Patch.
                            uvIndexes.append(patch.uvIndex())
                            coordinates.append(patch.name())

                else:
                    #3rd Step - generatedHASH and the stored HASH in the Metadata Index are NOT equal!
                    #Export each pach and generate the HASH to be appended.
                    for patch in geo.patchList():
                        metadataIndex +=1
                        #Generates the HASH for each Patch and append it.
                        generatedHASH = generateHASH(channel, metadataIndex, patch.uvIndex(), patch.name())
                        HASH.append(generatedHASH)

                        uvIndexes.append(patch.uvIndex())
                        coordinates.append(patch.name())

            else:
                #Create the Metadata and lock it in the Current Channel.
                channel.setMetadata("Channel_HASH", "")
                channel.setMetadataEnabled("Channel_HASH", False)

                #2nd Step - Channel does NOT have a Metadata, so this is the first time we are exporting this channel of the current Geo using mGo.
                #Generate the first HASH that is responsible for the Channel/System Colorspace and append it.
                generatedHASH = generateHASH(channel, metadataIndex, 0, 0)
                HASH.append(generatedHASH)

                #3rd Step - Generate the HASH for each Patch in the Current Channel
                for patch in geo.patchList():
                    metadataIndex +=1
                    #Generates the HASH for each Patch and append it.
                    generatedHASH = generateHASH(channel, metadataIndex, patch.uvIndex(), patch.name())
                    HASH.append(generatedHASH)

                    uvIndexes.append(patch.uvIndex())
                    coordinates.append(patch.name())


            #Last Step - update the Channel Metadata with the ones stored during the process above.
            channel.setMetadataItemList("Channel_HASH", HASH)
            channelMetadata = channel.metadataItemList("Channel_HASH")
            #print "UPDATED METADATA: " + str(channelMetadata)

            #File name of the UDIM paches that are going to be exported to the path.
            file_path = exportDir + geoName + "_" + chanName + "_$UDIM." + ext

            #Export only necessary Patches that are new or have been updated.
            if uvIndexes:
                if ext == "exr":
                    channel.exportImagesFlattened(file_path, 0, uvIndexes, {"compression":"zip"})
                else:
                    channel.exportImagesFlattened(file_path, 0, uvIndexes)

            #Let Mari and mGo keep going while converting the exported channels to Mipmap
            if subprocessExportStatus != False:
                global t1
                threads = [threading.Thread(target=mipmapConversion, args=(exportDir, geoName, chanName, coordinates, ext))]
                for t1 in threads:
                    t1.daemon = True
                    t1.start()

            return


        # <------------------------ Export Masks & MaskStacks from Shaders in a LayeredShader or from Falloff Curve ------------------------>
        def exportMasks(layer, channel, maskStack_parents_name):
            # Only export the Masks if channels are going to be exported.
            if chansExportCbox.isChecked() == True:
                global t1
                ext = []
                if int(channel.depth()) in [16, 32]:
                    ext = ext32
                else:
                    ext = ext8

                if layer.hasMaskStack():
                    maskStack = layer.maskStack()
                    layersCount = 0
                    layersVisible = 0
                    sharedLayer = []
                    # Seek the Layers inside the Mask Stack
                    for maskstackCurrentLayer in maskStack.layerList():
                        layersCount += 1
                        # Only enter if this is the first time you find a visible Layer inside the Mask Stack
                        if maskstackCurrentLayer.isVisible() and layersVisible < 1:
                            layersVisible += 1
                            # Compare the visible Layer Name to the Geo Channels and see if match any it's Channels name.
                            for channel in geo.channelList():
                                #If the current Layer of the Mask Stack is a Shared Channel export it's Channel!
                                if maskstackCurrentLayer.name() == channel.name():
                                    sharedLayer = "True"
                                    printMessage("The layer " + maskstackCurrentLayer.name() + " inside the " + maskStack_parents_name + " shader is a Mask Stack that is also a Shared Channel! We are going export it.")
                                    exportChannelPatch(channel, channel.depth())
                                    return replace_name_spaces(channel.name())+"#" +str( int(channel.depth()) )+ "@"+str(layerInfo(channel.name(), channel));
                                else:
                                    # Continue seek the Geo's Channels if you didn't find any Channel that match the Layer name.
                                    sharedLayer = "False"
                                    continue;
                        # Continue seek the Layers inside the Mask Stack
                        continue;

                    # If there is no Shared Channel from a Layer of the Mask Stack and there is just one Layer inside of it do this:
                    if layersCount == 1:
                        #Only a single Layer inside the Mask Stack, that's easy to export. It does not need any group+ flat layers in order to export them.
                        maskStack.exportImages(exportDir + geoName +'_'+ maskStack_parents_name + '_mask_$UDIM.' + ext)

                        #Convert Exported Mask to Mipmap
                        if subprocessExportStatus != False:
                            coordinates = []
                            for patch in geo.patchList():
                                coordinates.append(patch.name())
                            threads = [threading.Thread(target=mipmapConversion, args=(exportDir, geoName, maskStack_parents_name + '_mask', coordinates, ext))]
                            for t1 in threads:
                                t1.daemon = True
                                t1.start()

                        return maskStack_parents_name+"_mask#"+str( int(channel.depth()) ) + "@None";
                    elif sharedLayer == "False":
                        # elif There are more then 1 Layer inside the Mask Stack and it's not shared as a channel! We have to group them and flatten first in order to export it!
                        # Gives a warning msg to the user asking if he wants to continuing the process of export the masks.
                        # In order to do that, at the current moment Mari will only allow us to do this if we have to merge down all the layers inside of it!
                        titleTXT = "Mask Stacks WARNING"
                        messageTXT = "In order to export your Mask Stack from the layer/shader '" +maskStack_parents_name+ "' as a texture file.\nWe have to flatten all the layers inside of the Mask Stack.\nThe script will perform some Undo actions later as a step to recover what you had before the Exporting process.\nPress 'OK' to export your Mask Stacks, or 'Ignore' to skip this process."
                        mymessage = widgets.QMessageBox()
                        if mymessage.question(None, titleTXT, messageTXT, widgets.QMessageBox.Ok | widgets.QMessageBox.Ignore) == widgets.QMessageBox.Ok:
                            try:
                                # Change this to export Mask when we add a exportMask feature to the UI.
                                maskLayers = maskStack.layerList()
                                countUndo = 0
                                for maskLayer in maskLayers:
                                    countUndo +=1
                                    maskLayer.makeCurrent()
                                grouped = maskStack.groupLayers()
                                grouped.flattenLayerGroup()
                                maskStack.exportImages(exportDir + geoName +'_'+ maskStack_parents_name + '_mask_$UDIM.' + ext)
                                #can't find a neat solution to handle how to export maskStack that has multiple layers, so doing it the hard way, with history undo!
                                countUndo += 3
                                i =0
                                while i < countUndo:
                                    mari.history.undo()
                                    i +=1

                                #Convert Exported Mask to Mipmap
                                if subprocessExportStatus != False:
                                    coordinates = []
                                    for patch in geo.patchList():
                                        coordinates.append(patch.name())
                                    threads = [threading.Thread(target=mipmapConversion, args=(exportDir, geoName, maskStack_parents_name + '_mask', coordinates, ext))]
                                    for t1 in threads:
                                        t1.daemon = True
                                        t1.start()

                                return maskStack_parents_name+"_mask#"+str( int(channel.depth()) ) + "@None";
                            except:
                                #Operation failed or aborted by user!
                                printMessage("ERROR - Fail in export your Mask from: " +maskStack_parents_name)
                                printMessage("Try to export it manually!")
                                return	"none";

                elif layer.hasMask():
                    mask = layer.maskImageSet()
                    mask.exportImages(exportDir + geoName +'_'+ maskStack_parents_name + '_mask_$UDIM.' + ext)

                    #Convert Exported Mask to Mipmap
                    if subprocessExportStatus != False:
                        coordinates = []
                        for patch in geo.patchList():
                            coordinates.append(patch.name())
                        threads = [threading.Thread(target=mipmapConversion, args=(exportDir, geoName, maskStack_parents_name + '_mask', coordinates, ext))]
                        for t1 in threads:
                            t1.daemon = True
                            t1.start()

                    return maskStack_parents_name+"_mask#"+str( int(channel.depth()) ) + "@None";

            return "none";


        # ================== LAYER INFO ===========================================================================================================
        # Export custom layers for recreate a Nested Shader Network.
        layer_data = "None"
        # he only return data if he found the layer as visible, or after look into each layer. Then he will return as hidden if he found something that is turned off but if not, then it means that there is no layer that could be translated to Maya so we return none.
        def layerInfo(input_channel, channel_content):
            _layer_data = "None"
            for layer in channel_content.layerList():
                if True == layer.isVisible():
                    if layer.isGroupLayer():
                        _layer_data = layerInfo(input_channel, layer.layerStack() );
                        return _layer_data;
                    # try to get a parameter pre-defined as Falloff Curve
                    try:
                        blend_mode_type = layer.blendMode()
                        info = "Blend mode," + layer.blendModeName(blend_mode_type) + ",Amount," + str(layer.blendAmount())+","
                        if layer.getPrimaryAdjustmentParameter("adjustmentNode") == "Falloff Curve":

                            maskFilePath = "none"
                            if layer.hasMaskStack() or layer.hasMask():
                                if True == layer.isMaskEnabled():
                                    printMessage("Falloff Curve has maskStack!")
                                    # Mari is baking the mask into the texture correspondent to the flatten of the layers that are below the Falloff Curve layer.
                                    maskFilePath = exportMasks(layer, channel_content, replace_name_spaces(str(channel_content.name()))+"_Falloff" )
                                else:
                                    printMessage("Falloff Curve has maskStack, but is not visible!")

                            # Switch between the different Operation Modes in the adjustment node.
                            if layer.getPrimaryAdjustmentParameter("selector") == "Luma Curve":
                                # clean up some information strings that appear in the end of the parameters attribute.
                                layer_params1 = layer.getPrimaryAdjustmentParameter("lumaCurve").controlPointsAsString()
                                index = layer_params1.index("U")
                                layer_params1 = layer_params1[:index]
                                layer_params1 = "lumaCurve," + str(layer_params1)
                                _layer_data = ("Falloff Curve,Luma Curve,"+info+layer_params1+maskFilePath)
                            else:
                                # clean up some information strings that appear in the end of the parameters attribute.
                                layer_params1 = layer.getPrimaryAdjustmentParameter("redCurve").controlPointsAsString()
                                index = layer_params1.index("U")
                                layer_params1 = layer_params1[:index]
                                layer_params1 = "redCurve," + str(layer_params1)
                                # clean up some information strings that appear in the end of the parameters attribute.
                                layer_params2 = layer.getPrimaryAdjustmentParameter("greenCurve").controlPointsAsString()
                                index = layer_params2.index("U")
                                layer_params2 = layer_params2[:index]
                                layer_params2 = "greenCurve," + str(layer_params2)
                                # clean up some information strings that appear in the end of the parameters attribute.
                                layer_params3 = layer.getPrimaryAdjustmentParameter("blueCurve").controlPointsAsString()
                                index = layer_params3.index("U")
                                layer_params3 = layer_params3[:index]
                                layer_params3 = "blueCurve," + str(layer_params3)
                                # pass all the information to be interpreted in Maya to generate the nodes.
                                _layer_data = ("Falloff Curve,RGB Curves,"+info+layer_params1+layer_params2+layer_params3+maskFilePath)
                            if (attExportCbox.isChecked() == True) or (chansExportCbox.isChecked() == True):
                                printMessage("Node Network:'Falloff Curve'")
                                printMessage("Blend mode:'"+layer.blendModeName(blend_mode_type)+"'||Amount:"+str(layer.blendAmount()))
                        return _layer_data;
                    except:
                        pass

                else:
                    # try to get a parameter pre-defined as Falloff Curve even if the layer is not visible
                    try:
                        if layer.getPrimaryAdjustmentParameter("adjustmentNode") == "Falloff Curve":
                            # in case the user had turn it off.
                            _layer_data = ("Falloff Curve,hidden,"+maskFilePath)
                    except:
                        pass
            # If it doesn't find anything useful return as None
            return _layer_data;


        # ================== SHADERS INFO ===========================================================================================================
        # Export a single shader or the many shaders from a list of shaders inside the LayeredShader
        def exportShader(curShader, info, shaderType, shaderIndex, curShaderStr):

            #ARNOLD ============================================================================================
            if shaderType == "Ai Standard":
                # Initializing all the var as none, so during the loop you just update when it has something.
                DiffuseColor = DiffuseWeight = DiffuseRoughness = Backlighting = SpecularColor = SpecularWeight = SpecularRoughness = Anisotropy = Rotation = specReflectance = ReflectionColor = ReflectionWeight = reflReflectance = RefractionColor = RefractionWeight = IOR = RefractionRoughness = Transmittance = Opacity = SSSColor = SSSWeight = SSSRadius = EmissionColor = Bump = Normal = Displacement="none"
                channel_info = []
                printMessage("Current selected shader type:'" + shaderType + "'")
                printMessage("Geo Name:'" + geoName + "'||Shader Name:'" + curShaderStr + "'")
                printMessage("------ Order of the input channels ------")
                # <---------------------------- START OF THE LOOP ------------------------------------>
                # Check each input channel in the list of the shader.
                for input_channel in curShader.inputList():
                    channel_content = input_channel[1]
                    # If the channel input has a channel_content in the slot assign the information from the current channel input from the loop to the right variables that will be exported.
                    if None != channel_content:
                        channel_info = [replace_name_spaces(str(channel_content.name())), str(int(channel_content.depth()))]
                        printMessage("-------------------------------------------")
                        printMessage("Input:'" + input_channel[0] + "'")
                        printMessage("Channel:'" + str(channel_info[0]) + "'|'" + str(channel_info[1]) + " bits'")

                        if chansExportCbox.isChecked() == True:
                            #Invoke the exportChannelPatch function passing the channel name and channel depth
                            exportChannelPatch(input_channel[1], channel_content.depth())

                        # Look inside the layers list of the current channel from this loop.
                        layer_data = layerInfo(input_channel[0], channel_content)

                        # Diffuse Color
                        if input_channel[0] == "DiffuseColor":
                            difColN=str(channel_info[0])
                            difColD=str(channel_info[1])
                            DiffuseColor = difColN + "#" + difColD + "@"+str(layer_data)

                        # Diffuse Weight
                        if input_channel[0] == "DiffuseWeight":
                            difWeightN=str(channel_info[0])
                            difWeightD=str(channel_info[1])
                            DiffuseWeight = difWeightN + "#" + difWeightD + "@"+str(layer_data)

                        # Diffuse Roughness
                        if input_channel[0] == "DiffuseRoughness":
                            difRoughN=str(channel_info[0])
                            difRoughD=str(channel_info[1])
                            DiffuseRoughness = difRoughN + "#" + difRoughD + "@"+str(layer_data)

                        # Backlighting
                        if input_channel[0] == "Backlighting":
                            BacklightingN=str(channel_info[0])
                            BacklightingD=str(channel_info[1])
                            Backlighting = BacklightingN + "#" + BacklightingD + "@"+str(layer_data)

                        # Specular Color
                        if input_channel[0] == "SpecularColor":
                           specColN=str(channel_info[0])
                           specColD=str(channel_info[1])
                           SpecularColor = specColN + "#" + specColD + "@"+str(layer_data)

                        # Specular Weight
                        if input_channel[0] == "SpecularWeight":
                           specWeightN=str(channel_info[0])
                           specWeightD=str(channel_info[1])
                           SpecularWeight = specWeightN + "#" + specWeightD + "@"+str(layer_data)

                        # Specular Roughness
                        if input_channel[0] == "SpecularRoughness":
                           specRoughN=str(channel_info[0])
                           specRoughD=str(channel_info[1])
                           SpecularRoughness = specRoughN + "#" + specRoughD + "@"+str(layer_data)

                        # Anisotropy
                        if input_channel[0] == "Anisotropy":
                           anisN=str(channel_info[0])
                           anisD=str(channel_info[1])
                           Anisotropy = anisN + "#" + anisD + "@"+str(layer_data)

                        # Rotation
                        if input_channel[0] == "Rotation":
                           rotN=str(channel_info[0])
                           rotD=str(channel_info[1])
                           Rotation = rotN + "#" + rotD + "@"+str(layer_data)

                        # Reflectance at Normal (Specular)
                        if input_channel[0] == "Reflectance":
                            specReflectanceN=str(channel_info[0])
                            specReflectanceD=str(channel_info[1])
                            specReflectance = specReflectanceN + "#" + specReflectanceD + "@"+str(layer_data)

                        # Reflection Color
                        if input_channel[0] == "ReflectionColor":
                            reflColN=str(channel_info[0])
                            reflColD=str(channel_info[1])
                            ReflectionColor = reflColN + "#" + reflColD + "@"+str(layer_data)

                        # Reflection Weight
                        if input_channel[0] == "ReflectionWeight":
                            reflWeightN=str(channel_info[0])
                            reflWeightD=str(channel_info[1])
                            ReflectionWeight = reflWeightN + "#" + reflWeightD + "@"+str(layer_data)

                        # Reflectance at Normal (Reflection)
                        if input_channel[0] == "reflReflectance":
                            reflReflectanceN=str(channel_info[0])
                            reflReflectanceD=str(channel_info[1])
                            reflReflectance = reflReflectanceN + "#" + reflReflectanceD + "@"+str(layer_data)

                        # Refraction Color
                        if input_channel[0] == "RefractionColor":
                           refrColN=str(channel_info[0])
                           refrColD=str(channel_info[1])
                           RefractionColor = refrColN + "#" + refrColD + "@"+str(layer_data)

                        # Refraction Weight
                        if input_channel[0] == "RefractionWeight":
                           refrWeightN=str(channel_info[0])
                           refrWeightD=str(channel_info[1])
                           RefractionWeight = refrWeightN + "#" + refrWeightD + "@"+str(layer_data)

                        # IOR
                        if input_channel[0] == "IOR":
                           iorN=str(channel_info[0])
                           iorD=str(channel_info[1])
                           IOR = iorN + "#" + iorD + "@"+str(layer_data)

                        # Refraction Roughness
                        if input_channel[0] == "RefractionRoughness":
                           refrRoughN=str(channel_info[0])
                           refrRoughD=str(channel_info[1])
                           RefractionRoughness = refrRoughN + "#" + refrRoughD + "@"+str(layer_data)

                        # Transmittance
                        if input_channel[0] == "Transmittance":
                           transmitN=str(channel_info[0])
                           transmitD=str(channel_info[1])
                           Transmittance = transmitN + "#" + transmitD + "@"+str(layer_data)

                        # Opacity
                        if input_channel[0] == "Opacity":
                           opacN=str(channel_info[0])
                           opacD=str(channel_info[1])
                           Opacity = opacN + "#" + opacD + "@"+str(layer_data)

                        # Sub-Surface Scattering Color
                        if input_channel[0] == "SSSColor":
                           sssN=str(channel_info[0])
                           sssD=str(channel_info[1])
                           SSSColor = sssN + "#" + sssD + "@"+str(layer_data)

                        # Sub-Surface Scattering Weight
                        if input_channel[0] == "SSSWeight":
                           sssWeightN=str(channel_info[0])
                           sssWeightD=str(channel_info[1])
                           SSSWeight = sssWeightN + "#" + sssWeightD + "@"+str(layer_data)

                        # Sub-Surface Scattering Radius
                        if input_channel[0] == "SSSRadius":
                           sssRadN=str(channel_info[0])
                           sssRadD=str(channel_info[1])
                           SSSRadius = sssRadN + "#" + sssRadD + "@"+str(layer_data)

                        # Emission Color
                        if input_channel[0] == "EmissionColor":
                           emisN=str(channel_info[0])
                           emisD=str(channel_info[1])
                           EmissionColor = emisN + "#" + emisD + "@"+str(layer_data)

                        # Bump Map
                        if input_channel[0] == "Bump":
                           bumpN=str(channel_info[0])
                           bumpD=str(channel_info[1])
                           Bump = bumpN + "#" + bumpD + "@None"

                        # Normal Map
                        if input_channel[0] == "Normal":
                           normalN=str(channel_info[0])
                           normalD=str(channel_info[1])
                           Normal = normalN + "#" + normalD + "@None"

                        # Displacement Map
                        if input_channel[0] == "Displacement":
                           dispN=str(channel_info[0])
                           dispD=str(channel_info[1])
                           Displacement = dispN + "#" + dispD + "@None"

                        printMessage("-------------------------------------------")
                    else:
                        channel_info = "none"
                        if chansExportCbox.isChecked() == True:
                            printMessage("Input:'" + input_channel[0] + "'||Channel:'" + channel_info + "'")


                # <---------------------------- ENDING OF THE LOOP ------------------------------------>

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
                aRefractionRoughness=str(curShader.getParameter("RefractionRoughness"))
                aIOR=str(curShader.getParameter("IOR"))
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

                aBump=str(curShader.getParameter("BumpWeight"))
                aDisplacementBias=str(curShader.getParameter("DisplacementBias"))
                aDisplacementScale=str(curShader.getParameter("DisplacementScale"))
                aDisplacementRange=str(curShader.getParameter("DisplacementRange"))

                if attExportCbox.isChecked() == True:
                    printMessage("---------- Attributes parameters ----------")
                    for parameter_name in curShader.parameterNameList():
                        try:
                            printMessage("Parameter:'" + parameter_name + "' '" + str( curShader.getParameter( parameter_name).rgb() ) + "'")
                        except:
                            printMessage("Parameter:'" + parameter_name + "' '" + str( curShader.getParameter( parameter_name)) + "'")
                    printMessage("-------------------------------------------")

                configShaderData = (shaderType, curShaderStr, info, DiffuseColor, DiffuseWeight, DiffuseRoughness, Backlighting, SpecularColor, SpecularWeight, SpecularRoughness, Anisotropy, Rotation, specReflectance, ReflectionColor, ReflectionWeight, reflReflectance, RefractionColor, RefractionWeight, IOR, RefractionRoughness, Transmittance, Opacity, SSSColor, SSSWeight, SSSRadius, EmissionColor, Bump, Normal, Displacement, aDiffuseColor, aDiffuseWeight, aDiffuseRoughness, aBacklighting, aDiffuseFresnel, aSpecularColor, aSpecularWeight, aSpecularRoughness, aAnisotropy, aRotation, aFresnel_On, aReflectance, aReflectionColor, aReflectionWeight, aFresnel_On_Ref, areflReflectance, aRefractionColor, aRefractionWeight, aRefractionRoughness, aIOR, aFresnel_useIOR, aTransmittance, aOpacity, aSSSColor, aSSSWeight, aSSSRadius, aEmissionColor, aEmission, aBump, aDisplacementBias, aDisplacementScale, aDisplacementRange)

                if layeredShader == True:
                    shaderData = geoName+"_"+layeredShaderStr+"_data#"+str(shaderIndex)+".mgd"
                else:
                    shaderData = geoName+"_"+curShaderStr+"_data#"+str(shaderIndex)+".mgd"
                shaderData_list.append(shaderData)

                pathfile = sceneDescriptionsDir + shaderData
                with open(pathfile, 'wb') as f:
                    pickle.dump(configShaderData, f)

                printMessage("exported Arnold shader data")

            #VRAY ==============================================================================================
            elif shaderType == "VRay Mtl":
                # Initializing all the var as none, so during the loop you just update when it has something.
                DiffuseColor = DiffuseAmount = Opacity_Map = DiffuseRoughness = Self_Illumination = ReflectionColor = ReflectionAmount = HighlightGlossiness = ReflectionGlossiness = Reflection_IOR = Anisotropy = Rotation = RefractionColor = RefractionAmount = RefractionGlossiness = IOR = Fog_Color = Translucency_Color = Bump = Normal = Displacement="none"
                channel_info = []
                printMessage("Current selected shader type:'" + shaderType + "'")
                printMessage("Geo Name:'" + geoName + "'||Shader Name:'" + curShaderStr + "'")
                printMessage("------ Order of the input channels ------")
                # <---------------------------- START OF THE LOOP ------------------------------------>
                # Check each input channel in the list of the shader.
                for input_channel in curShader.inputList():
                    channel_content = input_channel[1]
                    # If the channel input has a channel_content in the slot assign the information from the current channel input from the loop to the right variables that will be exported.
                    if None != channel_content:
                        channel_info = [replace_name_spaces(str(channel_content.name())), str(int(channel_content.depth()))]
                        printMessage("-------------------------------------------")
                        printMessage("Input:'" + input_channel[0] + "'")
                        printMessage("Channel:'" + str(channel_info[0]) + "'|'" + str(channel_info[1]) + " bits'")

                        if chansExportCbox.isChecked() == True:
                            #Invoke the exportChannelPatch function passing the channel name and channel depth
                            exportChannelPatch(input_channel[1], channel_content.depth())

                        # Look inside the layers list of the current channel from this loop.
                        layer_data = layerInfo(input_channel[0], channel_content)

                        # Diffuse Color
                        if input_channel[0] == "DiffuseColor":
                            difColN=str(channel_info[0])
                            difColD=str(channel_info[1])
                            DiffuseColor = difColN + "#" + difColD + "@"+str(layer_data)

                        # Diffuse Amount
                        if input_channel[0] == "DiffuseAmount":
                            difAmountN=str(channel_info[0])
                            difAmountD=str(channel_info[1])
                            DiffuseAmount = difAmountN + "#" + difAmountD + "@"+str(layer_data)

                        # Opacity
                        if input_channel[0] == "Opacity_Map":
                            opacityN=str(channel_info[0])
                            opacityD=str(channel_info[1])
                            Opacity_Map = opacityN + "#" + opacityD + "@"+str(layer_data)

                        # Diffuse Roughness
                        if input_channel[0] == "DiffuseRoughness":
                            difRoughN=str(channel_info[0])
                            difRoughD=str(channel_info[1])
                            DiffuseRoughness = difRoughN + "#" + difRoughD + "@"+str(layer_data)

                        # Self-Illumination
                        if input_channel[0] == "Self_Illumination":
                           emisN=str(channel_info[0])
                           emisD=str(channel_info[1])
                           Self_Illumination = emisN + "#" + emisD + "@"+str(layer_data)

                        # Reflection Color
                        if input_channel[0] == "ReflectionColor":
                           reflColN=str(channel_info[0])
                           reflColD=str(channel_info[1])
                           ReflectionColor = reflColN + "#" + reflColD + "@"+str(layer_data)

                        # Reflection Amount
                        if input_channel[0] == "ReflectionAmount":
                           reflAmountN=str(channel_info[0])
                           reflAmountD=str(channel_info[1])
                           ReflectionAmount = reflAmountN + "#" + reflAmountD + "@"+str(layer_data)

                        # Highlight Glossiness
                        if input_channel[0] == "HighlightGlossiness":
                           highlightGlossN=str(channel_info[0])
                           highlightGlossD=str(channel_info[1])
                           HighlightGlossiness = highlightGlossN + "#" + highlightGlossD + "@"+str(layer_data)

                        # Reflection Glossiness
                        if input_channel[0] == "ReflectionGlossiness":
                           reflGlossN=str(channel_info[0])
                           reflGlossD=str(channel_info[1])
                           ReflectionGlossiness = reflGlossN + "#" + reflGlossD + "@"+str(layer_data)

                        # Reflection IOR
                        if input_channel[0] == "Reflection_IOR":
                           refl_iorN=str(channel_info[0])
                           refl_iorD=str(channel_info[1])
                           Reflection_IOR = refl_iorN + "#" + refl_iorD + "@"+str(layer_data)

                        # Anisotropy
                        if input_channel[0] == "Anisotropy":
                           anisN=str(channel_info[0])
                           anisD=str(channel_info[1])
                           Anisotropy = anisN + "#" + anisD + "@"+str(layer_data)

                        # Rotation
                        if input_channel[0] == "Rotation":
                           rotN=str(channel_info[0])
                           rotD=str(channel_info[1])
                           Rotation = rotN + "#" + rotD + "@"+str(layer_data)

                        # Refraction Color
                        if input_channel[0] == "RefractionColor":
                           refrColN=str(channel_info[0])
                           refrColD=str(channel_info[1])
                           RefractionColor = refrColN + "#" + refrColD + "@"+str(layer_data)

                        # Refraction Amount
                        if input_channel[0] == "RefractionAmount":
                           refrAmountN=str(channel_info[0])
                           refrAmountD=str(channel_info[1])
                           RefractionAmount = refrAmountN + "#" + refrAmountD + "@"+str(layer_data)

                        # Refraction Glossiness
                        if input_channel[0] == "RefractionGlossiness":
                           refrGlossN=str(channel_info[0])
                           refrGlossD=str(channel_info[1])
                           RefractionGlossiness = refrGlossN + "#" + refrGlossD + "@"+str(layer_data)

                        # IOR
                        if input_channel[0] == "IOR":
                           iorN=str(channel_info[0])
                           iorD=str(channel_info[1])
                           IOR = iorN + "#" + iorD + "@"+str(layer_data)

                        # Fog Color
                        if input_channel[0] == "Fog_Color":
                           fog_colorN=str(channel_info[0])
                           fog_colorD=str(channel_info[1])
                           Fog_Color = fog_colorN + "#" + fog_colorD + "@"+str(layer_data)

                        # Translucency Color
                        if input_channel[0] == "Translucency_Color":
                           translucN=str(channel_info[0])
                           translucD=str(channel_info[1])
                           Translucency_Color = translucN + "#" + translucD + "@"+str(layer_data)

                        # Bump Map
                        if input_channel[0] == "Bump":
                           bumpN=str(channel_info[0])
                           bumpD=str(channel_info[1])
                           Bump = bumpN + "#" + bumpD + "@None"

                        # Normal Map
                        if input_channel[0] == "Normal":
                           normalN=str(channel_info[0])
                           normalD=str(channel_info[1])
                           Normal = normalN + "#" + normalD + "@None"

                        # Displacement Map
                        if input_channel[0] == "Displacement":
                           dispN=str(channel_info[0])
                           dispD=str(channel_info[1])
                           Displacement = dispN + "#" + dispD + "@None"

                        printMessage("-------------------------------------------")
                    else:
                        channel_info = "none"
                        if chansExportCbox.isChecked() == True:
                            printMessage("Input:'" + input_channel[0] + "'||Channel:'" + channel_info + "'")


                # <---------------------------- ENDING OF THE LOOP ------------------------------------>

                #define attributes

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

                aBump=str(curShader.getParameter("BumpWeight"))
                aDisplacementScale=str(curShader.getParameter("DisplacementScale"))

                if attExportCbox.isChecked() == True:
                    printMessage("---------- Attributes parameters ----------")
                    for parameter_name in curShader.parameterNameList():
                        try:
                            printMessage("Parameter:'" + parameter_name + "' '" + str( curShader.getParameter( parameter_name).rgb() ) + "'")
                        except:
                            printMessage("Parameter:'" + parameter_name + "' '" + str( curShader.getParameter( parameter_name)) + "'")
                    printMessage("-------------------------------------------")

                configShaderData = (shaderType, curShaderStr, info, DiffuseColor, DiffuseAmount, Opacity_Map, DiffuseRoughness, Self_Illumination, ReflectionColor, ReflectionAmount, HighlightGlossiness, ReflectionGlossiness, Reflection_IOR, Anisotropy, Rotation, RefractionColor, RefractionAmount, RefractionGlossiness, IOR, Fog_Color, Translucency_Color, Bump, Normal, Displacement, aDiffuseColor, aDiffuseAmount, aOpacity_Map, aDiffuseRoughness, aSelf_Illumination, aBRDF_Model, aReflectionColor, aReflectionAmount, aLock_Highlight_Refle_gloss, aHighlightGlossiness, aReflectionGlossiness, aFresnel_On, aFresnel_useIOR, aReflection_IOR, aggxTailFalloff, aAnisotropy, aRotation, aRefractionColor, aRefractionAmount, aRefractionGlossiness, aIOR, aFog_Color, aFog_multiplier, aFog_bias, aSSS_On, aTranslucency_Color, aFwd_back_coeff, aScatt_coeff, aBump, aDisplacementScale)

                if layeredShader == True:
                    shaderData = geoName+"_"+layeredShaderStr+"_data#"+str(shaderIndex)+".mgd"
                else:
                    shaderData = geoName+"_"+curShaderStr+"_data#"+str(shaderIndex)+".mgd"
                shaderData_list.append(shaderData)

                pathfile = sceneDescriptionsDir + shaderData
                with open(pathfile, 'wb') as f:
                    pickle.dump(configShaderData, f)

                printMessage("exported Vray shader data")

            #REDSHIFT ==========================================================================================
            elif shaderType == "Redshift Architectural":
                # Initializing all the variables as none, so during the loop you just update when it got something.
                diffuse_color = diffuse_weight = diffuse_roughness = refr_trans_color = refr_trans_weight = refl_weight = refl_color = refl_gloss = brdf_0_degree_refl = refl_base_weight = refl_base_color = refl_base_gloss = brdf_base_0_degree_refl = anisotropy = anisotropy_rotation = transparency = refr_color = refr_gloss = refr_falloff_color = refr_ior = cutout_opacity = additional_color = Bump = Normal = Displacement="none"
                channel_info = []
                printMessage("Current selected shader type:'" + shaderType + "'")
                printMessage("Geo Name:'" + geoName + "'||Shader Name:'" + curShaderStr + "'")
                printMessage("------ Order of the input channels ------")
                # <---------------------------- START OF THE LOOP ------------------------------------>
                # Check each input channel in the list of the shader.
                for input_channel in curShader.inputList():
                    channel_content = input_channel[1]
                    # If the channel input has a channel_content in the slot assign the information from the current channel input from the loop to the right variables that will be exported.
                    if None != channel_content:
                        channel_info = [replace_name_spaces(str(channel_content.name())), str(int(channel_content.depth()))]
                        printMessage("-------------------------------------------")
                        printMessage("Input:'" + input_channel[0] + "'")
                        printMessage("Channel:'" + str(channel_info[0]) + "'|'" + str(channel_info[1]) + " bits'")

                        if chansExportCbox.isChecked() == True:
                            #Invoke the exportChannelPatch function passing the channel name and channel depth
                            exportChannelPatch(input_channel[1], channel_content.depth())

                        # Look inside the layers list of the current channel from this loop.
                        layer_data = layerInfo(input_channel[0], channel_content)

                        # diffuse_color (Diffuse Color)
                        if input_channel[0] == "diffuse_color":
                            difColN=str(channel_info[0])
                            difColD=str(channel_info[1])
                            diffuse_color  = difColN + "#" + difColD + "@"+str(layer_data)

                        # diffuse_weight (Diffuse Weight)
                        if input_channel[0] == "diffuse_weight":
                            difWeightN=str(channel_info[0])
                            difWeightD=str(channel_info[1])
                            diffuse_weight  = difWeightN + "#" + difWeightD + "@"+str(layer_data)

                       # diffuse_roughness (Diffuse Roughness)
                        if input_channel[0] == "diffuse_roughness":
                            difRoughN=str(channel_info[0])
                            difRoughD=str(channel_info[1])
                            diffuse_roughness = difRoughN + "#" + difRoughD + "@"+str(layer_data)

                        # refr_trans_color (Translucency Color)
                        if input_channel[0] == "refr_trans_color":
                           refrTransColN=str(channel_info[0])
                           refrTransColD=str(channel_info[1])
                           refr_trans_color = refrTransColN + "#" + refrTransColD + "@"+str(layer_data)

                        # refr_trans_weight (Translucency Weight)
                        if input_channel[0] == "refr_trans_weight":
                           refrTransWeightN=str(channel_info[0])
                           refrTransWeightD=str(channel_info[1])
                           refr_trans_weight = refrTransWeightN + "#" + refrTransWeightD + "@"+str(layer_data)

                        # refl_weight (Reflection Weight (Primary))
                        if input_channel[0] == "refl_weight":
                           reflWeightN=str(channel_info[0])
                           reflWeightD=str(channel_info[1])
                           refl_weight = reflWeightN + "#" + reflWeightD + "@"+str(layer_data)

                        # refl_colour (Reflection Color (Primary))
                        if input_channel[0] == "refl_color":
                           reflColN=str(channel_info[0])
                           reflColD=str(channel_info[1])
                           refl_color = reflColN + "#" + reflColD + "@"+str(layer_data)

                        # refl_gloss (Reflection Glossiness (Primary))
                        if input_channel[0] == "refl_gloss":
                           reflGlossN=str(channel_info[0])
                           reflGlossD=str(channel_info[1])
                           refl_gloss = reflGlossN + "#" + reflGlossD + "@"+str(layer_data)

                        # brdf_0_degree_refl (Reflection 0degree (Primary))
                        if input_channel[0] == "brdf_0_degree_refl":
                           brdf_0_degree_reflN=str(channel_info[0])
                           brdf_0_degree_reflD=str(channel_info[1])
                           brdf_0_degree_refl = brdf_0_degree_reflN + "#" + brdf_0_degree_reflD + "@"+str(layer_data)

                        # refl_base_weight (Reflection Weight (Secondary))
                        if input_channel[0] == "refl_base_weight":
                           reflBaseWeightN=str(channel_info[0])
                           reflBaseWeightD=str(channel_info[1])
                           refl_base_weight = reflBaseWeightN + "#" + reflBaseWeightD + "@"+str(layer_data)

                        # refl_base_color (Reflection Color (Secondary))
                        if input_channel[0] == "refl_base_color":
                           reflBaseColN=str(channel_info[0])
                           reflBaseColD=str(channel_info[1])
                           refl_base_color = reflBaseColN + "#" + reflBaseColD + "@"+str(layer_data)

                        # refl_base_gloss (Reflection Glossiness (Secondary))
                        if input_channel[0] == "refl_base_gloss":
                           reflBaseGlossN=str(channel_info[0])
                           reflBaseGlossD=str(channel_info[1])
                           refl_base_gloss = reflBaseGlossN + "#" + reflBaseGlossD + "@"+str(layer_data)

                        # brdf_base_0_degree_refl (Reflection 0degree (Secondary))
                        if input_channel[0] == "brdf_base_0_degree_refl":
                           brdf_base_0_degree_reflN=str(channel_info[0])
                           brdf_base_0_degree_reflD=str(channel_info[1])
                           brdf_base_0_degree_refl = brdf_base_0_degree_reflN + "#" + brdf_base_0_degree_reflD + "@"+str(layer_data)

                        # anisotropy
                        if input_channel[0] == "anisotropy":
                           anisN=str(channel_info[0])
                           anisD=str(channel_info[1])
                           anisotropy = anisN + "#" + anisD + "@"+str(layer_data)

                        # anisotropy_rotation
                        if input_channel[0] == "anisotropy_rotation":
                           anisRotN=str(channel_info[0])
                           anisRotD=str(channel_info[1])
                           anisotropy_rotation = anisRotN + "#" + anisRotD + "@"+str(layer_data)

                        # transparency (Refraction Weight)
                        if input_channel[0] == "transparency":
                           transparencyN=str(channel_info[0])
                           transparencyD=str(channel_info[1])
                           transparency = transparencyN + "#" + transparencyD + "@"+str(layer_data)

                        # refr_color (Refraction Color)
                        if input_channel[0] == "refr_color":
                           refrColN=str(channel_info[0])
                           refrColD=str(channel_info[1])
                           refr_color = refrColN + "#" + refrColD + "@"+str(layer_data)

                        # refr_gloss (Refraction Glossiness)
                        if input_channel[0] == "refr_gloss":
                           refrGlossN=str(channel_info[0])
                           refrGlossD=str(channel_info[1])
                           refr_gloss = refrGlossN + "#" + refrGlossD + "@"+str(layer_data)

                        # refr_falloff_color (End Color (Fog))
                        if input_channel[0] == "refr_falloff_color":
                            # Redshift does not support textures for the End Color (Fog) yet. Because of that I removed this channel from the shader, but it will not affect here, because of our smart selection using the if statement.
                           refrfalloff_colorN=str(channel_info[0])
                           refrfalloff_colorD=str(channel_info[1])
                           refr_falloff_color = refrfalloff_colorN + "#" + refrfalloff_colorD + "@"+str(layer_data)

                        # refr_ior (Refraction IOR)
                        if input_channel[0] == "refr_ior":
                            # Redshift does not support textures for the End Color (Fog) yet. Because of that I removed this channel from the shader, but it will not affect here, because of our smart selection using the if statement.
                           refr_iorN=str(channel_info[0])
                           refr_iorD=str(channel_info[1])
                           refr_ior = refr_iorN + "#" + refr_iorD + "@"+str(layer_data)

                        # cutout_opacity
                        if input_channel[0] == "cutout_opacity":
                           cutoutON=str(channel_info[0])
                           cutoutOD=str(channel_info[1])
                           cutout_opacity = cutoutON + "#" + cutoutOD + "@"+str(layer_data)

                        # additional_color
                        if input_channel[0] == "additional_color":
                           addColN=str(channel_info[0])
                           addColD=str(channel_info[1])
                           additional_color = addColN + "#" + addColD + "@"+str(layer_data)

                        # bump (bump)
                        if input_channel[0] == "Bump":
                           bumpN=str(channel_info[0])
                           bumpD=str(channel_info[1])
                           Bump = bumpN + "#" + bumpD + "@None"

                        # normal (normal)
                        if input_channel[0] == "Normal":
                           normalN=str(channel_info[0])
                           normalD=str(channel_info[1])
                           Normal = normalN + "#" + normalD + "@None"

                        # disp (disp)
                        if input_channel[0] == "Displacement":
                           dispN=str(channel_info[0])
                           dispD=str(channel_info[1])
                           Displacement = dispN + "#" + dispD + "@None"

                        printMessage("-----------------------------------------")
                    else:
                        channel_info = "none"
                        if chansExportCbox.isChecked() == True:
                            printMessage("Input:'" + input_channel[0] + "'||Channel:'" + channel_info + "'")


                # <---------------------------- ENDING OF THE LOOP ------------------------------------>

                #define attributes

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

                arefr_falloff_dist=str(curShader.getParameter("refr_falloff_dist"))

                aIncandescent_Scale=str(curShader.getParameter("Incandescent_Scale"))

                aBump=str(curShader.getParameter("BumpWeight"))
                aDisplacementScale=str(curShader.getParameter("DisplacementScale"))

                if attExportCbox.isChecked() == True:
                    printMessage("---------- Attributes parameters ----------")
                    for parameter_name in curShader.parameterNameList():
                        try:
                            printMessage("Parameter:'" + parameter_name + "' '" + str( curShader.getParameter( parameter_name).rgb() ) + "'")
                        except:
                            printMessage("Parameter:'" + parameter_name + "' '" + str( curShader.getParameter( parameter_name)) + "'")
                    printMessage("-------------------------------------------")

                configShaderData = (shaderType, curShaderStr, info, diffuse_color, diffuse_weight, diffuse_roughness, refr_trans_color, refr_trans_weight, refl_weight, refl_color, refl_gloss, brdf_0_degree_refl, refl_base_weight, refl_base_color, refl_base_gloss, brdf_base_0_degree_refl, anisotropy, anisotropy_rotation, transparency, refr_color, refr_gloss, refr_ior, refr_falloff_color, cutout_opacity, additional_color, Bump, Normal, Displacement, adiffuse_color, adiffuse_weight, adiffuse_roughness, arefr_translucency, arefr_trans_color, arefr_trans_weight, arefl_weight, arefl_color, arefl_gloss, abrdf_fresnel, abrdf_fresnel_type, abrdf_extinction_coeff, abrdf_0_degree_refl, abrdf_90_degree_refl, abrdf_Curve, arefl_base_weight, arefl_base_color, arefl_base_gloss, abrdf_base_fresnel, abrdf_base_fresnel_type, abrdf_base_extinction_coeff, abrdf_base_0_degree_refl, abrdf_base_90_degree_refl, abrdf_base_Curve, arefl_is_metal, ahl_vs_refl_balance, aanisotropy, aanisotropy_rotation, aanisotropy_orientation, atransparency, arefr_color, arefr_gloss, arefr_ior, arefr_falloff_on, arefr_falloff_dist, arefr_falloff_color_on, arefr_falloff_color, aao_on, aao_combineMode, aao_dark, aao_ambient, acutout_opacity, aadditional_color, aIncandescent_Scale, aBump, aDisplacementScale)

                if layeredShader == True:
                    shaderData = geoName+"_"+layeredShaderStr+"_data#"+str(shaderIndex)+".mgd"
                else:
                    shaderData = geoName+"_"+curShaderStr+"_data#"+str(shaderIndex)+".mgd"
                shaderData_list.append(shaderData)

                pathfile = sceneDescriptionsDir + shaderData
                with open(pathfile, 'wb') as f:
                    pickle.dump(configShaderData, f)

                printMessage("exported Redshift shader data")

            #Non-shader support ==========================================================================================
            else:
                configShaderData = []
                for channel in geo.channelList():
                    #Collect only relevant info
                    if channel.isShaderStack() != True:
                        # Look inside the layers list of the current channel from this loop.
                        chanName = replace_name_spaces(channel.name())
                        layer_data = layerInfo(chanName, channel)
                        chanN = str(chanName)
                        chanD = str(int(channel.depth()))
                        configShaderData.append( chanN +"#"+ chanD +"@"+ str(layer_data) )
                        printMessage(chanN +"#"+ chanD +"@"+ str(layer_data))

                        if chansExportCbox.isChecked() == True:
                            #Invoke the exportChannelPatch function passing the channel name and channel depth
                            exportChannelPatch(channel, chanD)

                shaderData = geoName+"_channels_list_data#"+str(shaderIndex)+".mgd"
                shaderData_list.append(shaderData)
                pathfile = sceneDescriptionsDir + shaderData
                with open(pathfile, 'wb') as f:
                    pickle.dump(configShaderData, f)


            return


        # You have to at least have one of the checkbos checked in order to proceed with export
        if ( attExportCbox.isChecked() != True and chansExportCbox.isChecked() != True and objExportCbox.isChecked() != True and camExportCbox.isChecked() != True and lightsExportCbox.isChecked() != True ):
            printMessage("WARNING - Please check at least one option in order to proceed with the export")
            return

        # var initialization
        sceneDescriptionData = []
        shaderData_list = []
        layeredShader = []
        layeredShaderStr = []

        #Object Name
        geoName = replace_name_spaces( str(geo.name()) )

        #Object Path
        objPath = str(geo.currentVersion().path())
        objName = geo.currentVersion().name()

        #Fill the Blank - Leaving some room for future updates in the list of possible things that could be exported...
        reserved = "reserved"

        #Got Udim?
        patchCount = 0
        udim = "True"
        # count how many patches the geo has.
        if len(geo.patchList()) == 1:
            for patch in geo.patchList():
                coordinate = patch.name()
                # if just one patch is found pass the number of it's coordinate. else, udim stay "True"
                udim = str(coordinate)

        # <------------------------ Export Current Shader or Export the shaders from a LayeredShader list. ------------------------>
        configShaderData = "none"

        # Variables defined for the current selected shader(for single shader),
        # or used in the loop, pointing what is the current shader that is been accessed over the loop interaction
        #curShader = geo.currentShader()
        curShaderStr = str(curShader.name())
        curShaderStr = replace_name_spaces(curShaderStr)

        shaderIndex = 0
        if curShader.isLayeredShader():
            layeredShader = True
            layeredShaderStr = str(geo.currentShader().name())
            if (attExportCbox.isChecked() == True) or (chansExportCbox.isChecked() == True):
                printMessage("Found 'Layered Shader' named as: '" +str(geo.currentShader().name())+"'")
                printMessage("---------- Shaders inside of it ----------")
            #a shader list inside a Layered shader is initially concepted as a channelList
            channels = curShader.channelList()
            for channel in channels:
                if channel.isShaderStack():
                    shaderLayers = channel.layerList()
                    for shaderLayer in shaderLayers:
                        curShader = shaderLayer.shader()
                        # If the shader in the LayeredShader list is turned on or off
                        if True == shaderLayer.isVisible():
                            shaderHidden = "visible"
                        else:
                            shaderHidden = "hidden"
                            printMessage("the current '"+str(curShader)+"' is hidden!")
                        #Supported Shaders inside the Layered Shader
                        try:
                            shaderType = str(curShader.getParameter("shadingNode"))
                        except:
                            printMessage("Shader found inside the Layered Shader is not supported!")
                            return
                        curShaderStr = str(shaderLayer.name())
                        curShaderStr = replace_name_spaces(curShaderStr)
                        if (attExportCbox.isChecked() == True) or (chansExportCbox.isChecked() == True):
                            printMessage("Found:'" +str(curShader.getParameter("shadingNode"))+ "' shader, named as: '" + curShaderStr+"'")
                            maskFilePath = "none"
                            if shaderLayer.hasMaskStack() or shaderLayer.hasMask():
                                if True == shaderLayer.isMaskEnabled():
                                    printMessage(curShaderStr+" has maskStack!")
                                    maskFilePath = exportMasks(shaderLayer, channel, curShaderStr)
                                else:
                                    printMessage(curShaderStr+" has maskStack, but is not visible!")

                            blend_mode_type = shaderLayer.blendMode()
                            info = "Blend mode," + shaderLayer.blendModeName(blend_mode_type) + ",Amount," + str(shaderLayer.blendAmount())+ ","+maskFilePath+","+shaderHidden
                            printMessage("Shader:'" +curShaderStr+ "' Blend mode:'" +shaderLayer.blendModeName(blend_mode_type)+ "' Amount:'" +str(shaderLayer.blendAmount())+ "' Mask:'"+str(maskFilePath)+"'" + " the shader is: "+shaderHidden)

                            # Call the def that is responsible to export any Shader Data found.
                            exportShader(curShader, info, shaderType, shaderIndex, curShaderStr)
                            printMessage("------------------------------------------")
                            shaderIndex +=1


            # After Loop, pass the name of the LayeredShader, the amount of shaders inside of it, and the last shaderType found!
            curShaderStr = layeredShaderStr
            curShaderStr = replace_name_spaces(curShaderStr)
            if shaderIndex >= 1:
                shaderType=str(curShader.getParameter("shadingNode"))+"#"+str(shaderIndex)+"@LayeredShader"
            else:
                if (attExportCbox.isChecked() == True) or (chansExportCbox.isChecked() == True):
                    printMessage("WARNING - No shader was found inside of the Layered Shader list.")

        else:
            info = "none"
            shaderType = "none"
            try:
                shaderType=str(curShader.getParameter("shadingNode"))
            except:
                #Non-shader support!
                curShaderStr = "channels_list"

            if (attExportCbox.isChecked() == True) or (chansExportCbox.isChecked() == True):
                exportShader(curShader, info, shaderType, shaderIndex, curShaderStr)



        # <------------------------ FINISH Export Current Shader or Export the shaders from a LayeredShader list. ------------------------>

        # <------------------------ Output Scene Description data ------------------------>
        #Print Exported Object name
        if objExportCbox.isChecked() == True:
            printMessage("Exported the current geometry selected: " +geoName)

        #Mipmap Conversion?
        extMipmap = "none"
        exportSubfolder = "none"
        global subprocessExportStatus
        if subprocessExportStatus == True:
            printMessage("Mipmap Conversion - success.")
            extMipmap = str(extMipmap_Combo.currentText())
            if str(subFolder_line.text()) != "":
                exportSubfolder = str(subFolder_line.text())+"/"

        #get namespace if the geo has something.
        namespace = ""
        try:
            namespace = str(geo.metadata("namespace"))
        except:
            pass
        # configSceneDescriptionData
        global exportDir, exportObj, ext8, ext32, filtering, exportAttri, exportChannels
        configData = (shaderType, geoName, objPath, exportDir, exportObj, ext8, ext32, udim, filtering, exportAttri, exportChannels, curShaderStr, "False", "none", "False", "none", "none", "none", "none", "none", extMipmap, exportSubfolder, namespace)

        printMessage("mGo Description data exported")

        sceneDescriptionData = geoName+"_"+curShaderStr+"_description.mgo"
        pathfile = sceneDescriptionsDir + sceneDescriptionData
        with open(pathfile, 'wb') as f:
            pickle.dump(configData, f)

        if exportOption == "exportDescriptionOnly":
            printMessage("--- Exported only mGo Project files related ---")
            printMessage("Scene Description & Shader Data saved in the mGo Folder:")
            printMessage(str(sceneDescriptionsDir))
            printMessage("Scene Description saved as:")
            print(sceneDescriptionData)
            for nShadersData in shaderData_list:
                printMessage(nShadersData)

        #----- END OF GO FUNCTION RETURN THE DESCRIPTION PATH FILE -----
        return pathfile;

    # Call the many Export options such as Geo, Channels, Attributes, Shaders or Env/Cam
    def sceneExport(multiGeoExportCbox, exportOption):
        if mari.projects.current() == None:
            printMessage("Please open a project first.")
            return

        #Channels Send?
        global exportChannels
        exportChannels = []
        if chansExportCbox.isChecked() == True:
            exportChannels = "True"
        else:
            exportChannels = "False"

        #Attributes Send?
        global exportAttri
        exportAttri = []
        if attExportCbox.isChecked() == True:
            exportAttri = "True"
        else:
            exportAttri = "False"

        #Export Object?
        global exportObj
        exportObj = []
        if objExportCbox.isChecked() == True:
            exportObj = "True"
        else:
            exportObj = "False"

        #File Extension
        global ext8, ext32
        ext8 = str(fformat_combo.currentText())
        ext32 = str(fformat32_combo.currentText())

        #Filter Type
        global filtering
        filtering = str(filter_combo.currentText())

        #Mipmap Filter?
        global subprocessExportStatus
        subprocessExportStatus = False
        if filtering == "Mipmap":
            subprocessExportStatus = True

        #Export Directory
        global exportDir
        exportDir = str(browse_line.text().replace( "\\", "/" ).rstrip( "/" ))
        exportDir = exportDir + "/"

        #Scene Descriptions Directory
        global sceneDescriptionsDir
        sceneDescriptionsDir = exportDir + "mGo_" + mari.projects.current().name() + "_Description/"
        if not os.path.exists(sceneDescriptionsDir):
            os.makedirs(sceneDescriptionsDir)

        project_pathfile = []
        if multiGeoExportCbox == "Selected OBJ":
            #Export checked items DATA from selected GEO
            printMessage("Export method: Selected OBJ")
            geo = mari.geo.current()
            if geo == None:
                printMessage("ERROR - '" +mari.geo.currentLocator().name()+ "' is currently selected. Please select a Non-Locator Geo in order to export data from a single OBJ.")
            else:
                #Export single SHADER selected
                curShader = geo.currentShader()
                #Call go export function and return to the log where the desciption file has been saved.
                project_pathfile = str(go(exportOption, geo, curShader))

        elif multiGeoExportCbox == "Visible OBJ":
            #Export checked items DATA from visible geo.
            printMessage("Export method: Visible OBJ")
            configData = []
            for geo in mari.geo.list():
                if geo.isVisible():
                    curShader = geo.currentShader()
                    configData.append(str(go(exportOption, geo, curShader)))
            #Write the main description file that contains ALL the paths to the various descriptions of the project.
            sceneDescriptionData = "Project_description.mgo"
            pathfile = sceneDescriptionsDir + sceneDescriptionData
            with open(pathfile, 'wb') as f:
                pickle.dump(configData, f)
            project_pathfile = pathfile

        elif multiGeoExportCbox == "All OBJ":
            #Export checked items DATA from Everything
            printMessage("Export method: All OBJ")
            configData = []
            for geo in mari.geo.list():
                try:
                    curShader = geo.currentShader()
                    configData.append(str(go(exportOption, geo, curShader)))
                except:
                    pass
            #Write the main description file that contains ALL the paths to the various descriptions of the project.
            sceneDescriptionData = "Project_description.mgo"
            pathfile = sceneDescriptionsDir + sceneDescriptionData
            with open(pathfile, 'wb') as f:
                pickle.dump(configData, f)
            project_pathfile = pathfile

        else:
            printMessage("Export method: EnvHDR&Cam")
            geo = mari.geo.current()
            curShader = geo.currentShader()
            shaderType = []
            if curShader.isLayeredShader():
                #Layered shader walk
                channels = curShader.channelList()
                for channel in channels:
                    if channel.isShaderStack():
                        shaderLayers = channel.layerList()
                        for shaderLayer in shaderLayers:
                            curShader = shaderLayer.shader()
                            # If the shader in the LayeredShader list is turned on get it's shaderType parameter
                            if True == shaderLayer.isVisible():
                                shaderType=str(curShader.getParameter("shadingNode"))
            else:
                #single shader
                try:
                    shaderType=str(curShader.getParameter("shadingNode"))
                except:
                    pass

            project_pathfile = []
            if shaderType == "Ai Standard" or shaderType == "VRay Mtl" or shaderType == "Redshift Architectural":
                #Light DATA
                exportLights = "True"
                envLight_data = []
                for light in mari.lights.list():
                    visibility = "hidden"
                    if light.isOn():
                        visibility = "visible"
                    if light.isEnvironmentLight():
                        # Send the file path of the HDR Image, the light intensity, the current rotation and resolution.
                        HDR_File_path = str(light.cubeImageFilename())
                        # In case it is an image in the Mari's root directory then we have to re-path it so Maya can understand the strings and vars
                        try:
                            mari_root_dir = str(mari.__path__).lstrip("['")
                            mari_root_dir = mari_root_dir.rsplit('/Media', 1)[0]
                            HDR_File_path = HDR_File_path.replace("$INSTALL", mari_root_dir,1)
                        except:
                            pass

                        envLight_intensity = str(light.intensity())
                        envLight_rotation = str(light.rotationUp())
                        image = light.cubeImage();
                        if image:
                            HDR_res = str(image.width())
                        else:
                            HDR_res = "1000"
                        envLight_data = "EnvironmentLight, " + HDR_File_path + "," + envLight_intensity + "," + envLight_rotation + "," + HDR_res + "," + visibility
                        printMessage(str(light.name()) + " Light Found!")


                #Camera DATA
                cam_data = "none"
                exportCam = "True"
                canvas = mari.canvases.current()
                if canvas is None:
                    printMessage("WARNING - No canvas selected!")

                camera = canvas.camera()
                if camera is None:
                    printMessage("WARNING - No camera selected!")

                if camera.PERSPECTIVE == camera.type():
                    # get the filed of view to send it to angle of view attribute camera in Maya
                    cam_fov = str(camera.fieldOfView())
                    # get the translation from camera
                    translation = camera.translation()
                    cam_trans = "(" + str(translation.x()) + ", " + str(translation.y()) + ", " + str(translation.z()) + ")"
                    # get the Look At variable from camera to send it to the cameraAim at Maya
                    lookAt = camera.lookAt()
                    cam_lookAt = "(" + str(lookAt.x()) + ", " + str(lookAt.y()) + ", " + str(lookAt.z()) + ")"
                    # get the Look At variable from camera to send it to world up in Maya's camera
                    up = camera.up()
                    cam_up = "(" + str(up.x()) + ", " + str(up.y()) + ", " + str(up.z()) + ")"
                    AspectRatio = str(camera.perspectiveAspectRatio())
                    # Organize all the attributes into a list.
                    cam_data = "MARI_Cam, " + cam_fov + "," + cam_trans + "," + cam_lookAt + "," + cam_up + "," + AspectRatio
                    printMessage("Camera data exported.")
                else:
                    printMessage("ERROR - The current viewport cannot be exported as a camera - please select a Perspective viewport.")
                    cam_data = "none"


                # configShaderData
                configData = (shaderType, "none", "none", exportDir, "false", "none", "none", "none", "none", "none", "none", "none", exportCam, cam_data, exportLights, envLight_data, "none", "none", "none", "none", "none", "none", "")
                #Write the main description file that contains ALL the paths to the various descriptions of the project.
                sceneDescriptionData = "EnvHDR_and_Cam.mgo"
                pathfile = sceneDescriptionsDir + sceneDescriptionData
                with open(pathfile, 'wb') as f:
                    pickle.dump(configData, f)
                project_pathfile = pathfile

                if exportOption == "exportDescriptionOnly":
                    printMessage("--- Exported only mGo Project files related ---")
                    printMessage("Scene Description Data saved in the mGo Folder:")
                    printMessage(str(sceneDescriptionsDir))
                    printMessage("Scene Description saved as:")
                    printMessage(sceneDescriptionData)
            else:
                printMessage("Current shader selected: '" +curShader.name()+ "' is not supported!")
                return

        # <------------------------ Mipmap Conversion Thread Join ------------------------>
        if subprocessExportStatus != False:
            titleTXT = "Mipmap Conversion Tool"
            messageTXT = 'May still exist some Channels to be converted to a Mipmap file image.\nClick "Ok" if you like to wait the process to finish.'
            mymessage = widgets.QMessageBox()
            if mymessage.question(None, titleTXT, messageTXT, widgets.QMessageBox.Ok | widgets.QMessageBox.Cancel) == widgets.QMessageBox.Ok:
                t1.join()

        # <------------------------ Log sceneDescription path ------------------------>
        projName = "Project Name:"+str(mari.projects.current().name())+", "
        mGo_Settings = "MAYA Host:"+str(IP_combo.currentText())+", "
        mGo_Settings += "Output Folder:"+exportDir+", "
        mGo_Settings +="8-bits:"+ext8+", "
        mGo_Settings +="16/32-bits:"+ext32+", "
        mGo_Settings +="Filter:"+filtering+", "
        mGo_Settings +="Export Channels:"+exportChannels+", "
        mGo_Settings +="Export Attributes:"+exportAttri+", "
        mGo_Settings +="Export Geo:"+exportObj+", "
        mGo_Settings +="Export Options:"+multiGeoExportCbox

        Output_Settings = projName+mGo_Settings
        log_pathfile = mGoDir + "mGo_Settings.txt"
        log_pathfile = log_pathfile.replace('\\', '/').rstrip( "/" )
        logLines = []
        try:
            with open(log_pathfile) as rd:
                #Read each line in the txt file, and seek if the project name already exists
                for line in rd:
                    #Keep any lines that are not related to the current Mari project.
                    projNameLog = line.split("Project Name:", 1)[1].split(",", 1)[0]
                    if str(mari.projects.current().name()) != projNameLog:
                        logLines.append(line)

                #after the loop append the current mGo settings related to the opened project.
                logLines.append(Output_Settings+"\n")

            f = open(log_pathfile, 'w')
            for line in logLines:
                f.write(line)
            f.close()
        except:
            #first time creating the file
            f = open(log_pathfile, 'a+')
            f.write(Output_Settings+"\n")
            f.close()


        # <------------------------ Run mGo_Maya ------------------------>
        if exportOption == "exportLive2Maya":
            mayaHost = 'localhost'
            #Interpreting IP Menu
            if str(IP_combo.currentText()) == "Local Host Only":
                mayaHost = 'localhost'
            elif str(IP_combo.currentText()) == "Network Host":
                mayaHost = IPS[0]
            else:
                mayaHost = str(IP_combo.currentText())

            try:
                maya = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                maya.connect((mayaHost, 6010))

                command = 'import mGo_Maya\nreload (mGo_Maya)\nmGo_Maya.autoLoad("%s")' % project_pathfile
                maya.send(command.encode())
                maya.close()
                printMessage("--- Exported to Maya ---")

            except socket.error:
                printMessage("--- ALERT --- You must have to open Maya's port 6010 first!")
                #'\n' command does not work here! Have to manully space out phrases to get a proper line break.
                message = mari.actions.create('open port', 'mari.utils.message("Scene Description & Shader Data saved in the mGo Folder.                                                 If you want to automate the Maya import process make sure port 6010 is open in Maya - See Instructions for Help.")')
                message.trigger()

        #In case using Mipmap as filtering call the function to save the 'Mipmap Tool Settings' after everything got exported.
        if str(filter_combo.currentText()) == "Mipmap":
            saveToolSettings( mari.projects.current().name() )
        #all's well that ends well
        printMessage("------------- finished -------------")
    # <------------------------ Main mGo Function end ------------------------>
    # <------------------------ Function to call 'Materialiser' script ------------------------>
    def loadMaterialiser():
        from . import mGo_Materialiser
        reload(mGo_Materialiser)
        mari.examples.mGo_Materialiser.runMaterialiser()


#------------------------------------------------------------
#send the Projects log to the Maya HOST Machine
def getProjects(mayaHost, mGoPath):
    mariProjs=[]

    for project in mari.projects.names():
        mariProjs.append(project)
    mariProjs=str(mariProjs)

    try:
        maya = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        maya.connect((mayaHost, 6010))
        command = 'f = open("%s" +"/mariProjects.txt", "w");' % mGoPath
        maya.send(command.encode())
        command = 'f.write("%s");' % mariProjs
        maya.send(command.encode())
        command = 'f.close();'
        maya.send(command.encode())
        #try to get the name of the current project open in Mari.
        try:
            curProj = mari.projects.current().name()
            #print in Maya the current opened Mari project
            command = 'print "Current opened project at Mari: " + "%s"' % curProj
            maya.send(command.encode())
        except:
            pass
        maya.close()
    except:
        pass


#------------------------------------------------------------
#import GEO from Maya to Mari
def importGEO(sendMode, projectName, nameSpace, groups, FilePath, setR, sd, isAnim, startAnim, endAnim, myObjList, myFileName, meshData, sendShader, shadersOnly, shader_file):
    def geoLoad(sendMode, options, sd, objects_to_load, nameSpace):
        _sendMode = sendMode
        _myFileName = myFileName
        #Trying to add a new version?
        if (_sendMode == "3"):
            importObj = "ok"
            for myObj in myObjList:
                if myObj == _myFileName.rsplit("_v0", 1)[0]:
                    try:
                        mari.geo.setCurrent(myObj)
                        geo = mari.geo.current()
                        verName = _myFileName
                        if (shadersOnly != "True"):
                            _options = {'MergeType':1, 'CreateSelectionSets':1, 'MergeSelectionGroupWithSameNameType':1}
                            geo.addVersion(FilePath, verName, _options)
                            geo.setCurrentVersion(verName)
                            printMessage("'" +myObj+ "' Object updated.")
                            #update geo metadata namespace
                            try:
                                geo.setMetadataItemList("namespace", nameSpace)
                            except:
                                #add metadata for the namespace of the GEO
                                nameSpace = myObjList[0].split(":", 1)[0]
                                if nameSpace != geo.name():
                                    geo.setMetadata("namespace", nameSpace)
                                else:
                                    geo.setMetadata("namespace", "")
                                geo.setMetadataEnabled("namespace", False)
                    except:
                        importObj = "Fail"
                        if shadersOnly != "True":
                            printMessage("You are trying to update a mesh, but there is no GEO with name: '" +myObj+ "' in the scene.")
                        else:
                            printMessage("You are trying to update a shader of a mesh which doesn't exist in the project. No '" +myObj+ "' found.")

            if importObj == "Fail" and shadersOnly != "True":
                titleTXT = "Import MESH WARNING"
                messageTXT = "The mesh: '" +myObj+ "', you are trying to update does not exist in the project. Do you wish to Add it instead?"
                mymessage = widgets.QMessageBox()
                mymessage.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
                if mymessage.warning(None, titleTXT, messageTXT, widgets.QMessageBox.Ok | widgets.QMessageBox.Close) == widgets.QMessageBox.Ok:
                    #try the sendMode add instead.
                    geoLoad("2", options, sd, objects_to_load, nameSpace)
                return

        else:
            #at the moment it's cumbersome try to avoid import the same geo multiple times. What mari does is rename it to geoName_1, geoName_2...
            #load grouped meshs as grouped GEOS under a single locator.
            if groups != "":
                # seek if locator doesn't exist.
                locatorList = mari.geo.listLocators()
                locatorParent = []

                groupNames = groups.rsplit("|")
                groupName = "locator"
                for _groupName in groupNames:
                    #print _groupName
                    groupName = _groupName
                    locatorExist = False
                    for locator in locatorList:
                        if mari.LocatorEntity.name(locator) == _groupName:
                            locatorExist = True
                            locator.setSelected(True)
                            locatorParent = locator
                            break

                    #If a parent locator exist in Mari but the chield does not, create a chield locator that represents the group chain in Maya.
                    if locatorParent != [] and locatorExist == False:
                        locatorParent.addLocator().setName(_groupName)

                    #There is no locator found in Mari, create a new one
                    if locatorParent == []:
                        mari.geo.addLocator().setName(groupName)
                        locatorParent = mari.geo.listLocators()[-1]
                #load the geo under the parent locator
                geo = mari.geo.load(FilePath, options, objects_to_load, True)
            else:
                #load ungrouped meshs as separeted GEOS
                geo = mari.geo.load(FilePath, options, objects_to_load, False)

            geo = mari.geo.current()
            geo.renameVersion(geo.name(), _myFileName)
            geo.setName(_myFileName.rsplit("_v0", 1)[0])
            printMessage("'" +geo.name()+ "' Object Added.")

            #add metadata for the namespace of the GEO
            #nameSpace = myObjList[0].split(":", 1)[0]
            if nameSpace != geo.name():
                geo.setMetadata("namespace", nameSpace)
            else:
                geo.setMetadata("namespace", "")
            geo.setMetadataEnabled("namespace", False)


        geo = mari.geo.current()
        #setup subdivs in Mari
        sd_method = meshData.split("sd_method:", 1)[1].split(",", 1)[0]
        sd_boundary = meshData.split("sd_boundary:", 1)[1].split(",", 1)[0]
        sd_level = meshData.split("sd_level:", 1)[1].split(",", 1)[0] #int() is given a crash, doing another way with if statement.
        level=0
        if sd_level == "1":
            level=1
        elif sd_level == "2":
            level=2
        elif sd_level == "3":
            level=3

        if sd_level != "0":
            geo.generateSubdivision({"Level":level,"Scheme":sd_method,"Force":True,"Boundary Interpolation":sd_boundary})
            geo.setSubdivisionLevel(level)

        #shader export with the mesh?
        if sendShader == "True" and shader_file != "none":
            from . import mGo_Materialiser
            reload(mGo_Materialiser)
            mari.examples.mGo_Materialiser.importShader(_myFileName.rsplit("_v0", 1)[0], shader_file, _sendMode)

        #manual way to focus camera on Obj (is there a 'focus' command in Mari?)
        """
        canvas = mari.canvases.current()
        camera = canvas.camera()
        bb=geo.boundingSphereCenter()
        bb=bb.asTuple()
        objX= bb[0]
        objY= bb[1]
        objZ= bb[2]
        camera.setLookAt( mari.VectorN(objX,objY,objZ) )
        """
        return


    #Deal with Multiple objects list
    myObjList = myObjList.strip("[").replace("u'", "").replace("'", "").replace(",", "").strip("]").split(" ")
    objects_to_load=[{"/":mari.geo.GEOMETRY_IMPORT_DONT_MERGE_CHILDREN}]
    selectionSetsFromFaces = [{"/":mari.geo.SELECTION_GROUPS_CREATE_FROM_FACE_GROUPS}]
    selectionGroups = [{"/":mari.geo.MERGESELECTIONGROUP_MERGE_SELECTIONGROUP_HAVING_SAME_NAME}]
    for geoParts in myObjList:
        #print geoParts
        #split namespaces.
        objects_to_load.append({"/"+geoParts.rsplit(":")[-1]:None})
        selectionSetsFromFaces.append({"/"+geoParts.rsplit(":")[-1]:None})
        selectionGroups.append({"/"+geoParts.rsplit(":")[-1]:None})

    channel_properties = []
    if setR=="1k":
        channel_properties = [mari.ChannelInfo("diffuse", mari.ImageSet.SIZE_1024, mari.ImageSet.SIZE_1024, mari.Image.DEPTH_BYTE, mari.Color(0.5,0.5,0.5), mari.Image.FILESPACE_NORMAL)]
    elif setR=="2k":
        channel_properties = [mari.ChannelInfo("diffuse", mari.ImageSet.SIZE_2048, mari.ImageSet.SIZE_2048, mari.Image.DEPTH_BYTE, mari.Color(0.5,0.5,0.5), mari.Image.FILESPACE_NORMAL)]
    elif setR=="4k":
        channel_properties = [mari.ChannelInfo("diffuse", mari.ImageSet.SIZE_4096, mari.ImageSet.SIZE_4096, mari.Image.DEPTH_BYTE, mari.Color(0.5,0.5,0.5), mari.Image.FILESPACE_NORMAL)]
    elif setR=="8k":
        channel_properties = [mari.ChannelInfo("diffuse", mari.ImageSet.SIZE_8192, mari.ImageSet.SIZE_8192, mari.Image.DEPTH_BYTE, mari.Color(0.5,0.5,0.5), mari.Image.FILESPACE_NORMAL)]

    objects_to_load=[{}]
    options = {'MergeType':1, 'CreateSelectionSets':1, 'MergeSelectionGroupWithSameNameType':1, 'CreateChannels':channel_properties}
    if isAnim=="True":
        timeRange = [float(startAnim), float(endAnim)]
        options.update({"StartFrame":timeRange[0], "EndFrame":timeRange[1]})

    #create a new Mari Project with Object
    if sendMode=="1":
        #close and create new mari project
        while (mari.projects.current() != None):
            mari.projects.close()

        #Workaround for Create a project with multiple GEO underneath a locator!
        #create the project with simple geo cube that is located at Mari ROOT folder
        mariCubeGEO = mari.resources.path(mari.resources.EXAMPLES)+"/Objects/cube.obj"
        #mari.projects.create(projectName, FilePath, channel_properties)
        if (mari.projects.current() == None):
            mari.projects.create(projectName, mariCubeGEO, channel_properties)
            mari.current.geo().setName("initial_project_creation")
            mari.current.geo().hide()
            mari.selection_groups.removeSelectionGroup(mari.selection_groups.list()[0])
        else:
            #now you can import multiple GEO as separeted pieces.
            geoLoad(sendMode, options, sd, objects_to_load, nameSpace)
            #remove the first geo that was created with the project
            #mari.geo.remove(_myFileName+"_Merged")

    else:
        #Add Object or Obj Version
        #check if a different project is open before send geo, if so close it!
        if (mari.projects.current() != None):
            if (mari.projects.current().name() != projectName):
                while (mari.projects.current() != None):
                    mari.projects.close()

        #try to open the project name, and only then add the geo.
        if (mari.projects.current() == None):
            try:
                mari.projects.open(projectName)
            except:
                printMessage("ERROR - The project does not exist!")
                return

        #call the function responsible for the steps to load the geo inside Mari
        try:
            geoLoad(sendMode, options, sd, objects_to_load, nameSpace)
        except IOError as e:
            printMessage("GEOMETRY LOAD ERROR: '%s'." % str(e))

    #try to clean-up any initial GEO created.
    try:
        mari.geo.remove("initial_project_creation")
    except:
        pass

    return


#------------------------------------------------------------
#import CAM from Maya to Mari
def importCAM(projectName, startTime, endTime, camFileName):
    #check if a different project is open, if so close it first
    if (mari.projects.current() != None):
        if (mari.projects.current().name() != projectName):
            while (mari.projects.current() != None):
                mari.projects.close()

    #try to open the project name
    if (mari.projects.current() == None):
        try:
            mari.projects.open(projectName)
        except:
            printMessage("ERROR - The project does not exist!")
            return

    #add new projector
    options = ["FrameOffset = 0", startTime, endTime]
    #camerasToLoad = "/"+camera_names.rsplit("|", 1)[-1]
    try:
        mari.projectors.load(camFileName, options)
    except:
        pass

    return
