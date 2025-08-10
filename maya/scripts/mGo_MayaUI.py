#-----------------------------------------------------------------
#    SCRIPT            mGo_MayaUI.py
#
#    AUTHOR            Stuart Tozer
#                      stutozer@gmail.com
#
#    CONTRIBUTOR       Antonio Lisboa M. Neto
#                      netocg.fx@gmail.com
#
#    DATE:             July 2015 - September 2015
#
#    DESCRIPTION:      mGo UI/shelf for Maya
#
#    VERSION:          .92
#
#-----------------------------------------------------------------

#to run script, copy/paste and run text below in the script editor or command line (python)...
"""
import mGo_MayaUI; mGo_MayaUI.UI()
"""

import maya.cmds as cmds
import maya.mel
import pickle
import socket
import os
import shutil
import subprocess
import importlib

# Tp 224989. The following Pyside UI classes are only called to create a widget when exporting geo+shader. And the latter functionality is disabled for now.
#import PySide
#from PySide import QtGui, QtCore


#mGo Assets path
path = cmds.internalVar(uad = True).split('/')
mGoPath = '/'.join(path[:-2]) + '/Mari/mGo'
assetsPath = mGoPath + '/Assets'

#create /Mari/mGo/Assets folders if doesn't exist
if not os.path.exists(assetsPath):
    os.makedirs(assetsPath)

#get mGo temp assets in Assets Folder
availProjects=next(os.walk(str(assetsPath)))[1]

mariHosts=[]
filepathHosts=mGoPath + '/mariHosts.txt'

# Tp 224989. The update shader functionality is not working for now and so is disabled, until fixed properly.
SHADER_UI_ENABLED = False

#function to create main mGo_MayaUI user interface
def UI(*args):
    global projMessage
    projMessage=False

    #window
    if cmds.window('mGo', exists = True):
        cmds.deleteUI('mGo')

    mGo_Maya=cmds.window('mGo', s=1, tlb=True)
    global form
    form=cmds.formLayout("form", w=210, h=508)

    #logo
    mGoIcon=cmds.image("mGoIcon", ann="mGo - Mari / Maya Bridge Tool\nAuthor: Stuart Tozer - stutozer@gmail.com \nContributor: Antonio Lisboa M. Neto - netocg.fx@gmail.com", i="mGo_red.png")

    # refresh icon
    refreshIcon = cmds.symbolButton("refreshIcon", image = "mGo_refresh.png", ann= "Refresh Mari Connection", p=form, c=refresh)

    #Projects Menu -------------
    sep1=cmds.separator("sep1",w=210, style='in')
    projectHeading = cmds.frameLayout("projectHeading", l="PROJECT:", p = form, w=200)
    sendOptions=cmds.radioButtonGrp("sendOptions", labelArray3=['New', 'Add', 'Vers'], numberOfRadioButtons=3, cw3=[45, 45, 45], sl=0, an1="Exports to a New Mari Project", an2="Adds to an Existing Mari Project", an3="Exports as a new Version to an Existing Mari Project", p=form, cc1=newProj, cc2=addProj, cc3=verProj)

    #existing projects optionMenu
    try:
        #bsp code only supported by maya2015+
        projectMenu=cmds.optionMenu("projectMenu", w =100, h=18, ann = "Existing Projects", cc=changeProjB, bsp=getProjects, p = form,  en=False)
    except:
        projectMenu=cmds.optionMenu("projectMenu", w =100, h=18, ann = "Existing Projects", cc=changeProjB, p = form, en=False)

    #default item in projects menu
    noProj="- Projects -"

    #add noProj ---
    cmds.menuItem(label = noProj, parent = "projectMenu")


    #Objects Menu -------------
    sep2=cmds.separator("sep2", w=210, style='in', p = form)
    objHeading = cmds.frameLayout("objHeading", l="OBJECT:", p = form, w=200)

    sendShaderCheck=cmds.checkBox("sendShaderCheck", label='', h=12, w=12, p=form, ann="Check to Export any shaders assigned to the Meshes.")
    sendShaderText=cmds.text("sendShaderText", label='Shader', p=form)


    animCheck=cmds.checkBox("animCheck", label='', h=12, w=12, p=form, ann="Check to Export Selected animated Meshes as Alembic file")
    animText=cmds.text("animText", label='Anim', p=form)


    #chanRes optionmenu
    chanRes=cmds.optionMenu("chanRes", l="ChanRes:", w = 97.5, h=16, ann = "Sets the initial Channel Resolution in Mari for Exported Objects", p = form)

    for item in ["1k", "2k", "4k", "8k"]:
        cmds.menuItem(label = item, parent = "chanRes")

    cmds.optionMenu("chanRes", e=True, v="4k")

    #subdiv optionmenu
    smoothAmount=cmds.optionMenu("Subdivs", l="Subdivs: ", w = 97.5, h=16, ann = "Set Object Subdivision Level in Mari", p = form)

    for item in ["auto", "0", "1", "2", "3"]:
        cmds.menuItem(label = item, parent = "Subdivs")

    #send OBJ
    objSendBtn=cmds.button("SendObject", l="Send Object(s)", w=97.5, ann="Send Selected Object(s) to Mari", c=sendObjToMari, en=False, p = form)

    #HDRI Menu -------------
    sep3=cmds.separator("sep3", w=210, style='in', p = form)
    HDRIHeading = cmds.frameLayout("HDRIHeading", l="HDRI:", p = form, w=200)
    hdriOptions=cmds.radioButtonGrp("HdriOptions", labelArray2=['View', 'Object'], numberOfRadioButtons=2, cw2=[53, 53], sl=0, an1="Renders HDRI from Current Viewport Position", an2="Renders HDRI from Selected Object Centre", p=form )

    #HDRI thumbnail icon
    #alpha transparency disable flag (-ua) only works in Maya2016+, avoiding legacy issues...
    try:
        hdriThumb=cmds.iconTextButton("hdriThumb", w=200, h=100, ann="HDRI Preview Image", i ="mGo_HDRIthumbnail.png", mw=1, mh=1, ua=False, bgc=[.32, .52, .65], p = form)
    except TypeError:
        hdriThumb=cmds.iconTextButton("hdriThumb", w=200, h=100, ann="HDRI Preview Image", i ="mGo_HDRIthumbnail.png", mw=1, mh=1, bgc=[.32, .52, .65], p = form)

    #render HDRI button
    mariRenderBtn=cmds.button("RenderHDRI", l="Render HDRI", w=97.5, ann="Render HDRI", c=render_hdri, p = form)

    #send HDRI button
    mariSendBtn=cmds.button("SendHDRI", l = "Send HDRI", w=97.5, ann="Send HDRI to Mari", c=send_hdri_to_mari, en=False, p = form)


    #Extra Utilities Menu -------------
    sep4=cmds.separator("sep4", w=210, style='in', p = form)

    #export Camera button
    exportCamBtn=cmds.button("ExportCamera", l="Export Camera", w=200, ann="Export Current Camera to Mari", p = form, en=False, c=exportCam)

    #cleanup button
    cleanupAssets=cmds.button("Cleanup Assets", w=200, ann="Delete Project Assets from mGo Assets Folder", c=openAssetsCleanup, p = form)

    sep5=cmds.separator("sep5", w=210, style='in', p = form)

    #save a material preset to user specified dir
    saveShaderBtn=cmds.button("Save Shader Preset", w=200, ann="Save a Shader Present (for Use with mGo-Materialiser)", c=saveShader, p = form)

    #load an mGo scene description
    loadDec=cmds.button("Import mGo Description", w=200, ann="Import mGo Mari Description File", c=loadMariSceneDesc, p = form)

    #I put this here (should really be under 'Projects') to stop textfield from being in focus
    projDirIcon=cmds.symbolButton("projDirIcon", image = "SP_DirIcon.png", ann= "Set Export Directory of Asset Files", p=form, c=assets_dir_browse)
    projDir=cmds.textField("projDir", tx=assetsPath, editable=True, p=form, w=180, h=19, ann="Set Asset Directory here...", cc=assets_dir_update)
    projectName=cmds.textField("projectName", tx="New_Project", editable= True, p=form, w=100, h=19, ann="Set a new Mari Project Name here...")

    #Network Elements ----------------
    global IP
    IP = "localhost"

    #local IP Adress UI
    sep6=cmds.separator("sep6", w=210, style='in', p = form)

    #display your IP address
    global yourIP
    yourIP=cmds.text("yourIP", l=IP, p=form, w=83, h=17, ann="Your IP Address", en=False)
    global yourIP_pos
    yourIP_pos = 115

    #Mari host text
    adress2Text=cmds.text("NetworkAdress", label='MARI Host:', ann="Network Address to connect with mGo - Mari", p=form)

    #available host machines
    hosts=cmds.optionMenu("hosts", l="", w = 101, h=14, ann="Network Address list: "+filepathHosts, p = form, cc=openPort)

    #Write inital mariHosts file
    if not os.path.exists(filepathHosts):
        f = open(filepathHosts, 'w')
        mariHosts = ["Local Host Only", "Network Host"]
        for mariHost in mariHosts:
            f.write(mariHost + os.linesep)
        f.close()

    #getting saved addresses
    #every time you start mGo set the menu Host to the last one used in the top of the file list.
    with open(filepathHosts) as rd:
        items = rd.readlines()

    #getting rid of '\n'
    mariHosts = [s.strip() for s in items]
    for item in mariHosts:
        cmds.menuItem(label = item, parent = "hosts")
    cmds.optionMenu("hosts", e = True, v = str(mariHosts[0]) )

    #add new address icon
    addIP=cmds.symbolButton("addIP", image = "mGo_add.png", ann= "Add New Address", p=form, c=newAddress)


    #layout the elements -------------
    cmds.formLayout(form, edit = True, af = [(mGoIcon,  "top", 4), (mGoIcon, "left", 7)] )
    cmds.formLayout(form, edit = True, af = [(yourIP,  "top", 16), (yourIP, "left", yourIP_pos)] )
    cmds.formLayout(form, edit = True, af = [(refreshIcon,  "top", 16), (refreshIcon, "left", 182)] )
    

    cmds.formLayout(form, edit = True, af = [(sep1,  "top", 42), (sep1, "left", 0)] )

    cmds.formLayout(form, edit = True, af = [(projectHeading,  "top", 48), (projectHeading, "left", 5)] )
    cmds.formLayout(form, edit = True, af = [(sendOptions,  "top", 49), (sendOptions, "left", 64)] )
    cmds.formLayout(form, edit = True, af = [(projDir,  "top", 95), (projDir, "left", 4)] )
    cmds.formLayout(form, edit = True, af = [(projDirIcon,  "top", 96), (projDirIcon, "left", 186)] )

    cmds.formLayout(form, edit = True, af = [(projectName,  "top", 73), (projectName, "left", 4)] )
    cmds.formLayout(form, edit = True, af = [(projectMenu,  "top", 74), (projectMenu, "left", 105)] )

    cmds.formLayout(form, edit = True, af = [(sep2,  "top", 120), (sep2, "left", 0)] )

    cmds.formLayout(form, edit = True, af = [(objHeading,  "top", 126), (objHeading, "left", 5)] )
    if SHADER_UI_ENABLED is True:
        cmds.formLayout(form, edit = True, af = [(sendShaderCheck,  "top", 131), (sendShaderCheck, "left", 138)] )
        cmds.formLayout(form, edit = True, af = [(sendShaderText, "top", 130), (sendShaderText, "left", 100)] )
    cmds.formLayout(form, edit = True, af = [(animCheck,  "top", 131), (animCheck, "left", 188)] )
    cmds.formLayout(form, edit = True, af = [(animText,  "top", 130), (animText, "left", 160)] )
    cmds.formLayout(form, edit = True, af = [(chanRes,  "top", 153), (chanRes, "left", 5)] )
    cmds.formLayout(form, edit = True, af = [(smoothAmount,  "top", 171), (smoothAmount, "left", 5)] )
    cmds.formLayout(form, edit = True, af = [(objSendBtn,  "top", 153), (objSendBtn, "left", 108)] )

    cmds.formLayout(form, edit = True, af = [(sep3,  "top", 193), (sep3, "left", 0)] )

    cmds.formLayout(form, edit = True, af = [(HDRIHeading,  "top", 199), (HDRIHeading, "left", 5)] )
    cmds.formLayout(form, edit = True, af = [(hdriOptions,  "top", 200), (hdriOptions, "left", 92)] )
    cmds.formLayout(form, edit = True, af = [(hdriThumb,  "top", 225), (hdriThumb, "left", 5)] )
    cmds.formLayout(form, edit = True, af = [(mariRenderBtn,  "top", 330), (mariRenderBtn, "left", 5)] )
    cmds.formLayout(form, edit = True, af = [(mariSendBtn,  "top", 330), (mariSendBtn, "left", 108)] )

    cmds.formLayout(form, edit = True, af = [(sep4,  "top", 360), (sep4, "left", 0)] )

    cmds.formLayout(form, edit = True, af = [(exportCamBtn,  "top", 367), (exportCamBtn, "left", 5)] )
    cmds.formLayout(form, edit = True, af = [(cleanupAssets,  "top", 395), (cleanupAssets, "left", 5)] )
    cmds.formLayout(form, edit = True, af = [(saveShaderBtn,  "top", 423), (saveShaderBtn, "left", 5)] )
    cmds.formLayout(form, edit = True, af = [(loadDec,  "top", 451), (loadDec, "left", 5)] )

    cmds.formLayout(form, edit = True, af = [(sep6,  "top", 481), (sep5, "left", 0)] )

    cmds.formLayout(form, edit = True, af = [(adress2Text,  "top", 486), (adress2Text, "left", 5)] )
    cmds.formLayout(form, edit = True, af = [(addIP,  "top", 486), (addIP, "left", 83)] )
    cmds.formLayout(form, edit = True, af = [(hosts,  "top", 488), (hosts, "left", 103)] )

    #Open Maya port open for the first item of the Host Menu
    #mariHost menu interpretation
    openPort()

    #show UI window
    cmds.showWindow()

    #load objExport plugin
    if not cmds.pluginInfo('objExport', q=True, l=True):
        cmds.loadPlugin('objExport')

    #load FBX plugin
    if not cmds.pluginInfo('fbxmaya', q=True, l=True):
        cmds.loadPlugin('fbxmaya')

    #load ABC plugin
    if not cmds.pluginInfo('AbcExport', q=True, l=True):
        cmds.loadPlugin("AbcExport")

    #set default directory
    current_project="New_Project"
    projDirUpdate(current_project)

def refresh(*args):
    openPort()

#function for log the projects
def projLog(mGoPath, assetsPath):
    if cmds.optionMenu("projectMenu", q=True, en=True):
        current_project=cmds.optionMenu("projectMenu", q=True, v=True)
    else:
        current_project="New_Project"

    Output_path = current_project + "@" + assetsPath
    projDirLog = mGoPath + "/Project_Log.txt"
    projDirLog = projDirLog.replace('\\', '/').rstrip( "/" )
    logLines = []
    try:
        with open(projDirLog) as rd:
            lineUpdated = False
            #Read each line in the txt file, and seek if the project name already exists
            for line in rd:
                #if so update that line with the Ouput_path
                if line.rsplit("@", 1)[0] == current_project:
                    logLines.append(Output_path+'\n')
                    lineUpdated = True
                #else append the original line of the file
                else:
                    logLines.append(line)

            #The current project is not logged in the file, append it!
            if lineUpdated == False:
                logLines.append(Output_path+'\n')

        f = open(projDirLog, 'w')
        for line in logLines:
            f.write(line)
        f.close()
    except:
        #first time creating the file
        f = open(projDirLog, 'a+')
        f.write(Output_path+'\n')
        f.close()

#function for log the projects
def projDirUpdate(current_project):
    global assetsPath
    Output_path = cmds.textField("projDir", text = True, q = True)
    log_pathfile = mGoPath + "/Project_Log.txt"
    log_pathfile = log_pathfile.replace('\\', '/').rstrip( "/" )
    try:
        with open(projDirLog) as rd:
            lines = rd.readlines()
            #getting rid of '\n'
            lines = [s.strip() for s in lines]
            for line in lines:
                if line.rsplit("@", 1)[0] == current_project:
                    Output_path = line.rsplit("@", 1)[1]
    except:
        #first time creating the file
        f = open(log_pathfile, 'a+')
        f.write(Output_path+'\n')
        f.close()

    cmds.textField("projDir", e= True, tx=Output_path)
    #pass the selected Directory to the var assetsPath

    assetsPath=cmds.textField("projDir", text = True, q = True)

def changeProjB(*args):
    setNewProj=cmds.optionMenu("projectMenu", q=True, v=True)
    cmds.textField("projectName", e= True, tx=setNewProj)
    #call the function to update the project Directory
    projDirUpdate(setNewProj)

#browse to assets directory
def assets_dir_browse(*args):
    newAssetsPath = cmds.fileDialog2(caption="Choose the Assets Export Folder", dir=assetsPath, fileMode=3)
    if newAssetsPath:
        newAssetsPath = newAssetsPath[0].replace("\\", "/")
        cmds.textField("projDir", e=True, tx=newAssetsPath)
        assets_dir_update()

#updates the assets directory when text is entered into textfield, or browsing to assetsfolder
def assets_dir_update(*args):
    global assetsPath
    newAssetsPath = cmds.textField("projDir", text = True, q = True)
    if newAssetsPath:
        newAssetsPath = newAssetsPath.replace("\\", "/")
        cmds.textField("projDir", e=True, tx=newAssetsPath)
        assetsPath=newAssetsPath

        projLog(mGoPath, assetsPath)

#some functions for enabling/disabling project menu and 'new project' textfield
def newProj(*args):
    cmds.textField("projectName", e=True, en=True)
    cmds.optionMenu("projectMenu", e=True, en=False)

    #set default project directory
    current_project="New_Project"

    projDirUpdate(current_project)

def addProj(*args):
    if mariOpen==False:
        openPort(*args)
    global projMessage
    cmds.textField("projectName", e=True, en=False)
    cmds.optionMenu("projectMenu", e=True, en=True)
    projMessage=True

    #update project directory
    current_project=cmds.optionMenu("projectMenu", q=True, v=True)
    projDirUpdate(current_project)

def verProj(*args):
    if mariOpen==False:
        openPort(*args)
    global projMessage
    cmds.textField("projectName", e=True, en=False)
    cmds.optionMenu("projectMenu", e=True, en=True)
    projMessage=True

    #update project directory
    current_project=cmds.optionMenu("projectMenu", q=True, v=True)
    projDirUpdate(current_project)


# Tp 224989. The update shader functionality is not working for now and so is disabled, until fixed properly.
##UI Class for the window question - Send version? (Object+Shader)
#class sendVersion_MyButtons(QtGui.QDialog):
#    def __init__(self):
#        super(sendVersion_MyButtons, self).__init__()
#        self.initUI()
#
#    def initUI(self):
#        option1Button = QtGui.QPushButton("Objects + Shaders")
#        option1Button.clicked.connect(self.onOption1)
#        option2Button = QtGui.QPushButton("Only Shaders")
#        option2Button.clicked.connect(self.onOption2)
#        #
#        buttonBox = QtGui.QDialogButtonBox()
#        buttonBox = QtGui.QDialogButtonBox(QtCore.Qt.Horizontal)
#        buttonBox.addButton(option1Button, QtGui.QDialogButtonBox.ActionRole)
#        buttonBox.addButton(option2Button, QtGui.QDialogButtonBox.ActionRole)
#        #
#        mainLayout = QtGui.QVBoxLayout()
#        mainLayout.addWidget(buttonBox)
#        self.setLayout(mainLayout)
#        # define window     xLoc,yLoc,xDim,yDim
#        #self.setGeometry(  250, 250, 0, 50)
#        self.setWindowTitle("Send Version?")
#        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
#
#    def onOption1(self):
#        self.retStatus = "Objects + Shaders"
#        self.close()
#    def onOption2(self):
#        self.retStatus = "Only Shaders"
#        self.close()
        
def getShaderData(shader, shaderType):
    configShaderData = []
    if(shaderType == "aiStandard"):
        print("Ai Standard shader selected")

        attriList = ["color", "Kd", "diffuseRoughness", "Kb", "FresnelAffectDiff",
        "KsColor", "Ks", "specularRoughness", "specularAnisotropy", "specularRotation", "specularFresnel", "Ksn",
        "KrColor", "Kr", "Fresnel", "Krn",
        "KtColor", "Kt", "IOR", "refractionRoughness", "FresnelUseIOR", "transmittance", "opacity",
        "KsssColor", "Ksss", "sssRadius",
        "emissionColor", "emission"]

        configShaderData.append("Ai Standard")
        configShaderData.append(shader.rsplit(":",1)[-1].lstrip("mGo_").rstrip("_mat"))

        for attri in attriList:
            try:
                attribute = str(cmds.getAttr(shader + '.' + attri)).translate(None, '[]')
                print("Parameter:'" + attri + "' '" + attribute)

                configShaderData.append(attribute)
            except:
                # nothing for now fall into exception considering arnold shader from time to time update and it's not backwards compatibility.
                return
        return configShaderData

    elif(shaderType == "VRayMtl"):
        print("VRayMtl shader selected")

        attriList = ["color", "diffuseColorAmount", "opacityMap", "roughnessAmount", "illumColor",
        "brdfType", "reflectionColor", "reflectionColorAmount", "hilightGlossinessLock", "hilightGlossiness", "reflectionGlossiness","useFresnel", "lockFresnelIORToRefractionIOR", "fresnelIOR", "ggxTailFalloff",
        "anisotropy", "anisotropyRotation",
        "refractionColor", "refractionColorAmount", "refractionGlossiness", "refractionIOR", "fogColor", "fogMult", "fogBias",
        "sssOn", "translucencyColor", "scatterDir", "scatterCoeff"]

        configShaderData.append("VRay Mtl")
        configShaderData.append(shader.rsplit(":",1)[-1].lstrip("mGo_").rstrip("_mat"))

        for attri in attriList:
            try:
                attribute = str(cmds.getAttr(shader + '.' + attri)).translate(None, '[]')
                print("Parameter:'" + attri + "' '" + attribute)

                # brdfType attribute in Vray 3.0 has new model called 'GGX' and has a new attribute 'ggxTailFalloff'
                # that's why we have to do this way using 'try' and 'if stamtements' in order to not broke our script and still have backwards compatibility.
                if attri == "brdfType":
                    # append the correct BRDF name accordingly to what value the attribute returned
                    if attribute == "0":
                        configShaderData.append("Phong")
                    elif attribute == "1":
                        configShaderData.append("Blinn")
                    elif attribute == "2":
                        configShaderData.append("Ward")
                    else:
                        configShaderData.append("GGX")
                else:
                    # if it's not the brdfType parameter loop, just store it's value.
                    configShaderData.append(attribute)
            except:
                # this exception will store the value 2.0 for what would be the ggxTailFalloff in case we didn't find this attribute
                configShaderData.append("2.0")
                return
        return configShaderData

    elif(shaderType == "RedshiftArchitectural"):
        print("RedshiftArchitectural shader selected")

        attriList = ["diffuse", "diffuse_weight", "diffuse_roughness",
        "refr_translucency", "refr_trans_color", "refr_trans_weight",
        "reflectivity", "refl_color", "refl_gloss", "brdf_fresnel", "brdf_fresnel_type", "brdf_extinction_coeff", "brdf_0_degree_refl", "brdf_90_degree_refl", "brdf_curve",
        "refl_base", "refl_base_color", "refl_base_gloss", "brdf_base_fresnel", "brdf_base_fresnel_type", "brdf_base_extinction_coeff", "brdf_base_0_degree_refl", "brdf_base_90_degree_refl", "brdf_base_curve",
        "refl_is_metal", "hl_vs_refl_balance",
        "anisotropy", "anisotropy_rotation", "anisotropy_orientation",
        "transparency", "refr_color", "refr_gloss", "refr_ior", "refr_falloff_on", "refr_falloff_dist", "refr_falloff_color_on", "refr_falloff_color",
        "ao_on", "ao_combineMode", "ao_dark", "ao_ambient",
        "cutout_opacity", "additional_color", "incandescent_scale"]

        configShaderData.append("Redshift Architectural")
        configShaderData.append(shader.rsplit(":",1)[-1].lstrip("mGo_").rstrip("_mat"))

        for attri in attriList:
            try:
                attribute = str(cmds.getAttr(shader + '.' + attri)).translate(None, '[]')
                print("Parameter:'" + attri + "' '" + attribute)

                # translate specific combobox int value to specific strings related to that type of attribute
                if attri == "brdf_fresnel_type":
                    if attribute == "0":
                        configShaderData.append("Dielectric")
                    else:
                        configShaderData.append("Conductor")
                elif attri == "brdf_base_fresnel_type":
                    if attribute == "0":
                        configShaderData.append("Dielectric")
                    else:
                        configShaderData.append("Conductor")
                elif attri == "anisotropy_orientation":
                    if attribute == "0":
                        configShaderData.append("none")
                    else:
                        configShaderData.append("From Tangent Channel")
                elif attri == "ao_combineMode":
                    if attribute == "0":
                        configShaderData.append("Add")
                    else:
                        configShaderData.append("Multiply")
                else:
                    # just store the general attribute value
                    configShaderData.append(attribute)
            except:
                # nothing for now fall into exception considering the current shader update development/status.
                return
        return configShaderData

    else:
        print("ERROR - mGo doesn't support export of the current shader you have selected!")
        print(shader)
        cmds.inViewMessage( amg='Please select one of the following shader types: <hl>aiStandard, VRayMtl, RedshiftArchitectural</hl>', pos='midCenter', fade=True, fadeOutTime=500)
        return "none"
        
#function for sending geo to Mari
def sendObjToMari(*args):
    def sendShaderToMari(projectName):
        # get shading groups from shapes
        shadingGroups = cmds.listConnections( cmds.ls(selection = True,typ='mesh', o = True, dag=True), t='shadingEngine')
        shader = cmds.ls(cmds.listConnections(shadingGroups), materials=1)[0]
        #Send the shader Data
        cmds.select(shader)
        shaderType = str(cmds.nodeType(shader))
        
        #Materialiser Path
        presetsmGoPath = mGoPath + "/Presets"
        shaderTypeFolder = []
        if(shaderType == "aiStandard"):
            shaderTypeFolder = "Arnold"
        elif(shaderType == "VRayMtl"):
            shaderTypeFolder = "Vray"
        elif(shaderType == "RedshiftArchitectural"):
            shaderTypeFolder = "Redshift"
        else:
            print("no supported shader assigned to the mesh, skip sending the shader to Mari.")
            print("Assigned shader: '" +shader+ "', node type: '" +shaderType+ "'")
            return "none"
        
        #print shader info
        print("Assigned shader: '" +shader+ "', node type: '" +shaderType+ "'")
        
        path = presetsmGoPath +"/"+shaderTypeFolder+"/"+ projectName
        if not os.path.exists(path):
            os.makedirs(path)
        print("------------- Shader File Path -------------")
        print(path)
        
        #Write the preset file with the shader info.
        configShaderData = getShaderData(shader, shaderType)
        fileName = shader.rsplit(":",1)[-1].lstrip("mGo_").rstrip("_mat")
        if configShaderData != None:
            f = open(path+"/"+fileName+".pre", 'w')
            pickle.dump(configShaderData, f)
            f.close()
        
        return path+"/"+fileName+".pre"
        
        
    #get the folder where the Assets going to be exported
    #assetsPath=cmds.textField("projDir", text = True, q = True)
    #assetsPath = assetsPath.replace("\\", "/")

    #check whether mesh to send will be animated .abc
    isAnim=cmds.checkBox("animCheck", q=True, v=True)
    
    #check whether shader will be sent
    sendShader=cmds.checkBox("sendShaderCheck", q=True, v=True)

    #get playback range for .abc files
    startAnim = cmds.playbackOptions(query=True, minTime=True)
    endAnim = cmds.playbackOptions(query=True, maxTime=True)

    #how many subdivs?
    sd=cmds.optionMenu("Subdivs", q=True, v=True)

    #what's channelRes?
    setR=cmds.optionMenu("chanRes", q=True, v=True)

    #query whether object is to be sent to new Mari project, added to current, or added as new version to current
    sendMode=cmds.radioButtonGrp("sendOptions", q=True, sl=True)

    #take projectName from either textfield or projectMenu (depending on sendMode)
    if sendMode==1:
        print("New project.")
        #query the typed Mari project name
        projectName=cmds.textField("projectName", text = True, q = True)
        if not os.path.exists(assetsPath + "/" + projectName):
            print("making new path")
            print("making dir: " + str(assetsPath + "/" + projectName))
            os.makedirs(assetsPath + "/" + projectName)
    else:
        projectName=cmds.optionMenu("projectMenu", q=True, v = True)
        if not os.path.exists(assetsPath + "/" + projectName):
            os.makedirs(assetsPath + "/" + projectName)

    #check selection and start the process to send stuff to Mari...
    myObj = []
    selectedMeshes = cmds.ls(selection = True,typ='mesh', o = True, dag=True)
    if selectedMeshes!=[]:
        #socket code
        global mariHost
        try:
            mari = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            mari.connect((mariHost, 6100))
        except socket.error:
            print("ERROR - Please Make Sure Port 6100 is Open in Mari")
            cmds.inViewMessage( amg='<hl>ERROR</hl> - Please Make Sure Port 6100 is Open in Mari', pos='botCenter', fade=True, fadeOutTime=500)
            return

            
        #Initial the creation project in Mari.
        if sendMode==1:
            mari.send('Mari.Scripts.mGo.importGEO("%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s")\x04' % (sendMode, projectName, "initialCreation", "initialCreation", setR, sd, isAnim, startAnim, endAnim, "initialCreation", "initialCreation", "initialCreation", "initialCreation", False, False, "none"))
            mari.close()
            sendMode=2
            mari = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            mari.connect((mariHost, 6100))
        
        # Tp 224989. The update shader functionality is not working for now and so is disabled, until fixed properly.
        ##update just the Shaders?
        #form = sendVersion_MyButtons()
        shadersOnly = False
        #if sendMode==3 and sendShader==True:
        #    form.exec_()
        #    if form.retStatus=="Objects + Shaders":
        #        print "Send Object+Shaders."
        #    elif form.retStatus=="Only Shaders":
        #        shadersOnly = True
        #        print "Send only Shaders."
        #    else:
        #        print "Send Object+Shaders canceled."
        #        return
        
        selectedMeshes = cmds.listRelatives(selectedMeshes, parent=True)
        for mesh in selectedMeshes:
            #get namespace name
            nameSpace = 'root'
            nameSpace = cmds.listRelatives(mesh)[0].rsplit(":", 1)[0]
            #get the group name
            groups = ''
            groupNames = cmds.listRelatives(mesh, fullPath=True)[0].split("|")[0:-2]
            if len(groupNames) > 1:
                for groupName in groupNames:
                    #split any namespaces
                    groups += groupName.rsplit(":")[-1]+"|"
                #strip unecessary '|' in the begining and the end of the string.
                groups = groups[1:-1].strip()
            #get mesh name and shape name and split any namespaces
            currentMesh = cmds.listRelatives(mesh, fullPath=True)[0].rsplit("|")[-2].rsplit(":", 1)[-1]
            meshShape = cmds.listRelatives(mesh, fullPath=True)[0].rsplit("|")[-1].rsplit(":", 1)[-1]
            
            #non namespace meshs
            if nameSpace == meshShape:
                nameSpace = ''
            else:
                nameSpace = nameSpace+":"
            
            myObj = currentMesh
            sd_level = "sd_level:0"
            sd_method="sd_method:Catmull Clark"
            sd_boundary="sd_boundary:Always Sharp"
            #Start the automated process to get the sd information for each mesh.
            if sd == "auto":
                #Check if the Smooth Mesh Preview is check, if not sd is 0
                if cmds.getAttr(nameSpace+meshShape + '.displaySmoothMesh') == 2:
                    #Get the value from SmoothPreviewForRender?
                    if cmds.getAttr(nameSpace+meshShape +'.useSmoothPreviewForRender') == 1:
                        sd_level = "sd_level:" + str(cmds.getAttr(nameSpace+meshShape + '.smoothLevel'))
                    else:
                        sd_level = "sd_level:" + str(cmds.getAttr(nameSpace+meshShape + '.renderSmoothLevel'))

                #(Subdivision Method atribute - Maya 2015+)
                try:
                    if cmds.getAttr(nameSpace+meshShape +'.smoothDrawType') != 0:
                        #OpenSubdivision
                        sd_method = "sd_method:Catmull Clark"
                        # 0 - Smooth(No Interpolation), 1 - Smooth(Sharp Edges and Corners), 2 - Smooth(Sharp Edges), 3 - Smooth(All sharp)
                        if cmds.getAttr(nameSpace+meshShape +'.osdFvarBoundary') == 0:
                            sd_boundary = "sd_boundary:None"
                        if cmds.getAttr(nameSpace+meshShape +'.osdFvarBoundary') == 1:
                            if cmds.getAttr(nameSpace+meshShape +'.osdFvarPropagateCorners') == 0:
                                sd_boundary = "sd_boundary:Edge And Corner"
                            else:
                                sd_boundary = "sd_boundary:Always Sharp"
                        if cmds.getAttr(nameSpace+meshShape +'.osdFvarBoundary') == 2:
                            sd_boundary = "sd_boundary:Edge Only"
                        else:
                            sd_boundary = "sd_boundary:Always Sharp"

                    else:
                        #(default Maya's Subdivision Method)
                        if cmds.getAttr(nameSpace+meshShape +'.smoothUVs') == 1:
                            sd_method = "sd_method:Catmull Clark"
                            # 0 - Smooth all, 1 - Smooth Internal, 2 - Do not Smooth
                            if cmds.getAttr(nameSpace+meshShape +'.keepMapBorders') == 0:
                                sd_boundary = "sd_boundary:Edge Only"
                            elif cmds.getAttr(nameSpace+meshShape +'.keepMapBorders') == 1:
                                sd_boundary = "sd_boundary:Edge Only"
                            else:
                                sd_boundary = "sd_boundary:Always Sharp"
                        else:
                            sd_boundary = "sd_boundary:None"
                except:
                    #(default Maya's Subdivision Method)
                    if cmds.getAttr(nameSpace+meshShape +'.smoothUVs') == 1:
                        sd_method = "sd_method:1"
                        #2 Do not Smooth, #1 Smooth Internal, #0 Smooth all
                        sd_boundary = "sd_boundary:" +str(cmds.getAttr(nameSpace+meshShape +'.keepMapBorders'))
                    else:
                        sd_boundary = "sd_boundary:2"
            else:
                sd_level = "sd_level:" +str(sd)

            #check whether the shader assigned to the mesh will be send as well
            shader_file = "none"
            cmds.select(mesh)
            if sendShader == True:
                shader_file = sendShaderToMari(projectName)
            
            meshData = meshShape +","+ sd_level +","+ sd_method +","+ sd_boundary
            
            myFileName = ""
            if nameSpace != "":
                nameSpace = nameSpace.strip(":")
                myFileName = myFileName + nameSpace.replace(":", "_") + "_"
            if groups != "":
                myFileName = myFileName + groups.replace("|", "_") + "_"
            myFileName = myFileName + currentMesh + "_v0"
            version=1
            #abc file path/name
            abcSel = '-root ' + nameSpace+currentMesh
            #filePath = assetsPath + "/" + projectName + "/" + myFileName + str(version) + ".abc"
            filePath = assetsPath + "/" + projectName + "/" + myFileName + str(version) + ".fbx"
            
            #save obj as new version?
            if sendMode==3:
                #While the pathFile exists increment one number until it's unique, and then save as.
                while os.path.exists(filePath)==True:
                    version+=1
                    #filePath = assetsPath + "/" + projectName + "/" + myFileName + str(version) + ".abc"
                    filePath = assetsPath + "/" + projectName + "/" + myFileName + str(version) + ".fbx"
            
            #get final obj version Name without namespaces and group names
            myFileName = currentMesh +"_v0"+ str(version)
            
            #export Shaders Only?
            if shadersOnly != True:
                #export the abc/fbx file
                maya.mel.eval('FBXExportFileVersion "FBX201200"')
                maya.mel.eval('FBXExportInAscii -v true')
                maya.mel.eval('FBXExportCameras -v false')
                maya.mel.eval('FBXExportLights -v false')
                maya.mel.eval('FBXExportSmoothingGroups -v true')
                maya.mel.eval('FBXExportQuickSelectSetAsCache -v "setName"')
                maya.mel.eval('FBXExportAnimationOnly -v false')
                """
                if isAnim==True:
                    maya.mel.eval('AbcExport -j "-uvWrite -writeFaceSets -worldSpace -fr %s %s %s -sn -file %s";' % (startAnim, endAnim, abcSel, filePath))
                else:
                    maya.mel.eval('AbcExport -j "-uvWrite -writeFaceSets -worldSpace %s -sn -file %s";' % (abcSel, filePath))
                """
                maya.mel.eval(('FBXExport -f \"{}\" -s').format(filePath))
                    
            #Function inside mGo - Mari that is responsible to manage the import process of an asset from Maya to Mari.
            mari.send('Mari.Scripts.mGo.importGEO("%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s")\x04' % (sendMode, projectName, nameSpace, groups, filePath, setR, sd, isAnim, startAnim, endAnim, nameSpace+currentMesh, myFileName, meshData, sendShader, shadersOnly, shader_file))
            #after create the project for the first time switch the send Object mode to the add GEO method.
            
        mari.close()

    else:
        print("Please Select Object(s) for Export and Try Again")
        cmds.inViewMessage( amg='Please Select Object(s) for Export and Try Again', pos='botCenter', fade=True, fadeOutTime=500)
        return

    if len(selectedMeshes) >1:
        cmds.inViewMessage( amg="<hl>Multi Objects</hl> sent to Mari", pos='botCenter', fade=True, fadeOutTime=500 )
    else:
        cmds.inViewMessage( amg="<hl>'%s'</hl> sent to Mari" % myObj, pos='botCenter', fade=True, fadeOutTime=500 )

    #update project menu
    allProjs = cmds.optionMenu("projectMenu", q = True, itemListLong = True)
    if allProjs is not None:
        for item in allProjs:
            cmds.deleteUI(item)

    availProjects=next(os.walk(str(assetsPath)))[1]
    if availProjects is not None:
        for item in availProjects:
            cmds.menuItem(label = item, parent = "projectMenu")

    cmds.optionMenu("projectMenu", e = True, v = projectName)
    #call the func to log proj paths
    projLog(mGoPath, assetsPath)

    cmds.select(selectedMeshes)
    return

#function for rendering Scene HDRIs
def render_hdri(*args):
    global render_geo
    global image_path

    currentRenderer = cmds.getAttr('defaultRenderGlobals.currentRenderer')

    image_path = cmds.renderSettings(firstImageName=True,  fpt=True)
    image_path = image_path[0].rsplit('.', 1)[0] + '.exr'

    print("current renderer: " + str(currentRenderer))
    print("image path: " + str(image_path))

    if currentRenderer != "vray" and currentRenderer != "redshift" and currentRenderer != "arnold":
        cmds.inViewMessage(amg="This feature currently supports Vray, Arnold or Redshift renderers only", pos="botCenter", fade=True)

    else:
        #query whether HDRI renders from current view, or selected object
        render_view=cmds.radioButtonGrp("HdriOptions", q=True, sl=True)

        #if rendering from object, make sure object is selected - if not, return
        if render_view == 2:
            #get object selection
            render_geo = cmds.ls(sl=True, typ="transform")
            if render_geo == []:
                cmds.inViewMessage(amg="Please Select an Object from which to render HDRI View", pos="botCenter", fade=True)
                return
        else:
            #used later on for saving out filename
            render_geo = "Scene"

        render_camera = cmds.modelPanel("modelPanel4", query=True, camera=True)
        print("render_camera: " + str(render_camera))

        #store current camera xforms
        orig_t = cmds.xform(render_camera, query=True, worldSpace=True, t=True)
        orig_r = cmds.xform(render_camera, query=True, worldSpace=True, ro=True)
        orig_tx = orig_t[0]
        orig_ty = orig_t[1]
        orig_tz = orig_t[2]
        orig_rx = orig_r[0]
        orig_ry = orig_r[1]
        orig_rz = orig_r[2]

        if render_view == 2:
            #get bounding box centre position of selected object
            bbx = cmds.xform(render_geo, q=True, bb=True, ws=True) # world space
            new_xPos = (bbx[0] + bbx[3]) / 2.0
            new_yPos = (bbx[1] + bbx[4]) / 2.0
            new_zPos = (bbx[2] + bbx[5]) / 2.0

            #hide object
            cmds.hide(render_geo)

            #set camera's translation coords
            cmds.setAttr("%s.translateX" % render_camera, new_xPos )
            cmds.setAttr("%s.translateY" % render_camera, new_yPos )
            cmds.setAttr("%s.translateZ" % render_camera, new_zPos )

        #zero out rotation
        cmds.setAttr("%s.rotateX" % render_camera, 0)
        cmds.setAttr("%s.rotateY" % render_camera, 0)
        cmds.setAttr("%s.rotateZ" % render_camera, 0)

        print("finished pre-render setup")

        #display 'rendering' message in thumbnail icon
        cmds.iconTextButton('hdriThumb', e=True, image="mGo_rendering.png")

        #run render function specific to current renderer ------------------------------
        if currentRenderer == "redshift":
            #add post render mel
            postRenderMel = """python("image_path=cmds.renderSettings(firstImageName=True, fpt=True); image_path=image_path[0].rsplit('.', 1)[0] + '.exr'; cmds.iconTextButton('hdriThumb', e=True, image=image_path); cmds.button('SendHDRI', e=True, en=True)")"""
            cmds.setAttr ('redshiftOptions.postRenderMel', postRenderMel, type='string')
            render_redshift_image(render_camera, render_geo)

        elif currentRenderer == "arnold":
            render_arnold_image(render_camera, render_geo)

        elif currentRenderer == "vray":
            render_vray_image(render_camera, render_geo)

        print("render finished")

        #render finished, now put everything back the way you found it ------------------
        if render_geo != "Scene":
            cmds.showHidden(render_geo)
            #reposition to original camera position
            cmds.setAttr("%s.translateX" % render_camera, orig_tx)
            cmds.setAttr("%s.translateY" % render_camera, orig_ty)
            cmds.setAttr("%s.translateZ" % render_camera, orig_tz)

        cmds.setAttr("%s.rotateX" % render_camera, orig_rx)
        cmds.setAttr("%s.rotateY" % render_camera, orig_ry)
        cmds.setAttr("%s.rotateZ" % render_camera, orig_rz)

        #enable 'send hdri' button (in redshift this command runs as postrender mel)
        if currentRenderer != "redshift":
            cmds.button("SendHDRI", e=True, en=True)

def render_arnold_image(render_camera, render_geo):
    sky_transform = None

    #store original settings
    prev_width = cmds.getAttr('defaultResolution.width')
    prev_height = cmds.getAttr('defaultResolution.height')
    prev_deviceAspectRatio = cmds.getAttr('defaultResolution.deviceAspectRatio')
    driver = cmds.ls('defaultArnoldDriver')
    prev_format = cmds.getAttr(driver[0] + '.aiTranslator')
    prev_cam_type = cmds.getAttr(render_camera + '.aiTranslator')

    #apply new settings
    cmds.setAttr('defaultResolution.width', 2000)
    cmds.setAttr('defaultResolution.height', 1000)
    cmds.setAttr('defaultResolution.deviceAspectRatio', 2000/1000)
    cmds.setAttr(driver[0] + '.aiTranslator', 'exr', type='string')
    cmds.setAttr("%s.aiTranslator" %render_camera,"spherical", type="string")

    dome_light = cmds.ls(type="aiSkyDomeLight")
    sky = cmds.ls(type="aiSky")

    if dome_light != []:
        dome_transform = cmds.listRelatives(dome_light, parent=True, fullPath=True)
        if sky == []:
            #if domelight exists but no sky (bg), create one and set texture, rotation and intensity values (making the HDRI visible in render)
            dome_texture=cmds.listConnections(dome_light[0] + '.color')

            if dome_texture is not None:
                #create new aiSky and plug in dome texture
                aiSky = cmds.shadingNode("aiSky", asUtility=True)
                sky_transform = cmds.listRelatives(aiSky, allParents=True )
                cmds.connectAttr("%s.message" % aiSky, "defaultArnoldRenderOptions.background", f=True)
                cmds.connectAttr("%s.outColor" % dome_texture[0], "%s.color" % aiSky, f=True)

                #get domeLight attrs (intensity, rotation, format)
                dome_intensity = cmds.getAttr (dome_light[0] + '.intensity')
                dome_format = cmds.getAttr (dome_light[0] + '.format')
                dome_rotation = cmds.getAttr (dome_transform[0] + '.rotateY')

                #set aiSky attrs
                cmds.setAttr('aiSky1.format', dome_format)
                cmds.setAttr('aiSky1.intensity', dome_intensity)
                cmds.setAttr(sky_transform[0] + '.rotateY', dome_rotation)

    print("rendering arnold image...")

    #render, then restore changes
    cmds.arnoldRender(cam=render_camera)

    if sky_transform is not None:
        cmds.delete(sky_transform)

    cmds.setAttr('defaultResolution.width', prev_width)
    cmds.setAttr('defaultResolution.height', prev_height)
    cmds.setAttr('defaultResolution.deviceAspectRatio', prev_deviceAspectRatio)
    cmds.setAttr(driver[0] + '.aiTranslator', prev_format, type='string')
    cmds.setAttr(render_camera + '.aiTranslator', prev_cam_type, type='string')
    
    #update thumbnail
    cmds.iconTextButton('hdriThumb', e=True, image=image_path)

def render_redshift_image(render_camera, render_geo):
    background_enabled = None

    #store original settings
    prev_width = cmds.getAttr('defaultResolution.width')
    prev_height = cmds.getAttr('defaultResolution.height')
    prev_deviceAspectRatio = cmds.getAttr('defaultResolution.deviceAspectRatio')
    prev_format = cmds.getAttr('redshiftOptions.imageFormat')
    prev_PostMel = cmds.getAttr('redshiftOptions.postRenderMel')

    #apply new settings
    cmds.setAttr('defaultResolution.width', 2000)
    cmds.setAttr('defaultResolution.height', 1000)
    cmds.setAttr('defaultResolution.deviceAspectRatio', 2000/1000)
    cmds.setAttr("redshiftOptions.imageFormat", 1)
    cmds.setAttr("%s.rsCameraType" % render_camera, 3)

    dome_light = cmds.ls(type="RedshiftDomeLight")
    sky = cmds.ls(type="RedshiftEnvironment")

    if dome_light != []:
        background_enabled = cmds.getAttr(dome_light[0] + '.background_enable')
        if sky == []:
            if background_enabled == False:
                cmds.setAttr('redshiftDomeLightShape1.background_enable', 1)

    print("rendering redshift image...")

    #render, then restore changes
    cmds.rsRender(render=True, camera=render_camera)

    cmds.setAttr('defaultResolution.width', prev_width)
    cmds.setAttr('defaultResolution.height', prev_height)
    cmds.setAttr('defaultResolution.deviceAspectRatio', prev_deviceAspectRatio)
    cmds.setAttr('redshiftOptions.imageFormat', prev_format)
    cmds.setAttr('redshiftOptions.postRenderMel', prev_PostMel, type='string')

    if background_enabled is not None:
        cmds.setAttr('redshiftDomeLightShape1.background_enable', background_enabled)

def render_vray_image(render_camera, render_geo):
    background_invisible = None
    renderlayer = cmds.editRenderLayerGlobals(query=True, currentRenderLayer=True)

    #store original settings
    prev_width = cmds.getAttr('vraySettings.width')
    prev_height = cmds.getAttr('vraySettings.height')
    prev_aspectRatio = cmds.getAttr('vraySettings.aspectRatio')
    prev_imageFormatStr = cmds.getAttr('vraySettings.imageFormatStr')
    prev_cam_type = cmds.getAttr('vraySettings.cam_type')
    prev_cam_overrideFov = cmds.getAttr('vraySettings.cam_overrideFov')
    prev_cam_fov = cmds.getAttr('vraySettings.cam_fov')
    prev_noAlpha = cmds.getAttr('vraySettings.noAlpha')

    #apply new settings
    cmds.setAttr('vraySettings.width', 2000)
    cmds.setAttr('vraySettings.height', 1000)
    cmds.setAttr('vraySettings.aspectRatio', 2000/1000)
    cmds.setAttr('vraySettings.imageFormatStr', 'exr', type='string')
    cmds.setAttr('vraySettings.cam_type', 1)
    cmds.setAttr('vraySettings.cam_overrideFov', 1)
    cmds.setAttr('vraySettings.cam_fov', 360)
    cmds.setAttr('vraySettings.noAlpha', 1)

    dome_light = cmds.ls(type="VRayLightDomeShape")
    sky = cmds.ls(type="VRaySky")

    if dome_light != []:
        background_invisible=cmds.getAttr(dome_light[0] + '.invisible')
        if sky == []:
            if background_invisible == True:
                maya.mel.eval('setAttr "VRayLightDomeShape1.invisible" 0;')

    print("rendering vray image...")

    #render, then restore changes
    args = ('-camera', render_camera, '-layer', renderlayer, '-w', 2000, '-h', 1000)
    cmds.vrend(*args)


    #restore settings
    if background_invisible is not None:
        cmds.setAttr(dome_light[0] + '.invisible', background_invisible)

    cmds.setAttr('vraySettings.width', prev_width)
    cmds.setAttr('vraySettings.height', prev_height)
    cmds.setAttr('vraySettings.aspectRatio', prev_aspectRatio)
    cmds.setAttr('vraySettings.imageFormatStr', prev_imageFormatStr, type='string')
    cmds.setAttr('vraySettings.cam_type', prev_cam_type)
    cmds.setAttr('vraySettings.cam_overrideFov', prev_cam_overrideFov)
    cmds.setAttr('vraySettings.cam_fov', prev_cam_fov)
    cmds.setAttr('vraySettings.noAlpha', prev_noAlpha)

    #update thumbnail
    cmds.iconTextButton('hdriThumb', e=True, image=image_path)

#function to send scene HDRIs to Mari
def send_hdri_to_mari(*args):
    sendMode=cmds.radioButtonGrp("sendOptions", q=True, sl=True)
    project_name=cmds.optionMenu("projectMenu", q=True, v = True)
    filename = image_path.rsplit("/", 1)[1].rsplit(".", 1)[0]

    if not os.path.exists(assetsPath + "/" + project_name):
        os.makedirs(assetsPath + "/" + project_name)
        
    if render_geo == "Scene":
        final_path = assetsPath + "/" + project_name + "/" + filename + "_" + render_geo + ".exr"
    else:
        final_path = assetsPath + "/" + project_name + "/" + filename + "_" + render_geo[0] + ".exr"

    print("final image path: " + final_path)

    #copy HDRI to Mari Folder
    shutil.copy(image_path, final_path)

    #socket code
    global mariHost

    try:
        mari = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        mari.connect((mariHost, 6100))

        if sendMode == 1:
            cmds.inViewMessage( amg="HDRI's cannot export to 'New' project. Please select 'Add' or 'Version' instead", pos='botCenter', fade=True, fadeOutTime=500)
            return
            
        else:
            #load the HDRI in Mari and set attributes
            mari.send('project_name = "%s"\x04' % project_name)
            mari.send('if Mari.projects.current().name() != project_name:\n    Mari.projects.close()\x04')
            mari.send('if (Mari.projects.current() == None):\n try:\n    Mari.projects.open(project_name)\n except:\n    print("ERROR - The project does not exist!")\x04')
            mari.send('oldHDR=None\x04')
            mari.send("myEnvLight=next(x for x in Mari.lights.list() if x.isEnvironmentLight())\x04")
            mari.send("oldHDR = [i for i in Mari.images.list() if i.filePath() == myEnvLight.cubeImageFilename()]\x04")
            mari.send("if oldHDR:\n    oldHDR[0].close()\x04")
            mari.send("myEnvLight.setCubeImage( '%s', myEnvLight.TYPE_GUESS)\x04" % final_path)
            mari.send("myEnvLight.setCanvasDisplay( True)\x04")
            mari.send("myEnvLight.setIntensity(1)\x04")
            mari.send("myEnvLight.setRotationUp(270)\x04")

            mari.close()

            cmds.inViewMessage(amg='<hl>HDRI</hl> sent to Mari', pos='botCenter', fade=True, fadeOutTime=500)

    except socket.error:
        print("ERROR - Please Make Sure Port 6100 is Open in Mari")
        cmds.inViewMessage(amg='<hl>ERROR</hl> - Please Make Sure Port 6100 is Open in Mari', pos='botCenter', fade=True, fadeOutTime=500)

    #call the func to log proj paths
    projLog(mGoPath, assetsPath)

#function for exporting the current perspviewport camera to Mari
def exportCam(*args):
    #query sendmode
    sendMode=cmds.radioButtonGrp("sendOptions", q=True, sl=True)

    if sendMode==2 or sendMode==3:
        exportCamValid = False
        #selection list.
        camerasSelected = cmds.ls(sl=True, dag=True, s=True)
        #validate each selected thing in the selection list.
        for cam in camerasSelected:
            if cmds.objectType(cam, isType="camera")==1:
                if cam != "perspShape" and cam != "topShape" and cam != "frontShape" and cam != "sideShape":
                    exportCamValid = True
                    print("'" + cam + "' selected.")
                else:
                    print("FBX does not support export: '" + cam + "' skiping this selection...")

        #Return fail if the selection does not have at least one good camera that can be exported.
        if exportCamValid == False:
            cmds.inViewMessage( amg= "Export Cameras Fail. Please select only cameras. *FBX does not support export default Maya's camera." , pos='botCenter', fade=True, fadeOutTime=500 )
            return

        #select the cam
        #Time range of the Animation from the Maya Scene
        StartFrame = str(cmds.playbackOptions(query = True, minTime = True))
        EndFrame= str(cmds.playbackOptions(query = True, maxTime = True))

        #Mari format
        #options = ["FrameOffset = 0", "StartFrame = 1", "EndFrame=24"]
        #camerasToLoad = ["/CameraTopPersp/CameraTopPersp"]
        startTime = "StartFrame = " + StartFrame
        endTime = "EndFrame = " + EndFrame

        #query the selected Mari project name
        projectName=cmds.optionMenu("projectMenu", q=True, v = True)

        if not os.path.exists(assetsPath + "/" + projectName):
            os.makedirs(assetsPath + "/" + projectName)

        camFileName=assetsPath + "/" + projectName + "/" + projectName+"_cameras.fbx"

        print("Camera file name: " + camFileName)

        #save the cam to project folder
        maya.mel.eval('FBXExportFileVersion "FBX201200"')
        maya.mel.eval('FBXExportInAscii -v true')
        maya.mel.eval("FBXExportCameras -v true")
        cmds.file(camFileName, force=True, options='v=0', type='FBX export', pr=True, es=True)

        #ABC bugged in Mari.
        #command = "-frameRange" +" "+ StartFrame +" "+ EndFrame +" "+ "-worldSpace -dataFormat ogawa -root |" + camera_names + " -file " + camFileName
        #cmds.AbcExport(j= command)

        #socket code
        global mariHost
        try:
            mari = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            mari.connect((mariHost, 6100))
            mari.send('Mari.Scripts.mGo.importCAM("%s", "%s", "%s", "%s")\x04' % (projectName, startTime, endTime, camFileName) )
            mari.close()
            #show message
            cmds.inViewMessage( amg="Cameras sent to Mari", pos='botCenter', fade=True, fadeOutTime=500 )
        except:
            print("failure")

        #call the func to log proj paths
        projLog(mGoPath, assetsPath)
    else:
        cmds.inViewMessage( amg="Camera's Can't be exported to New Scenes. Choose <hl>'Add'</hl> or <hl>'Vers'</hl> instead", pos='botCenter', fade=True, fadeOutTime=500 )


#function to open Mari Assets Directory
def openExplorer(*args):
    print(assetsPath)
    assetsPathExp = assetsPath.replace('/', "\\")

    try:
        subprocess.check_call(['explorer', assetsPathExp])

    except:
        pass

#function to create Assets Cleanup UI
def openAssetsCleanup(*args):
    #get mGo projects in Assets Folder
    availProjects=next(os.walk(str(assetsPath)))[1]

    #get asset files
    contents = os.listdir(assetsPath)

    #create UI
    if cmds.window("mGo_Cleanup", exists = True):
        cmds.deleteUI("mGo_Cleanup")

    assetsWindow=cmds.window("mGo_Cleanup", s=1, rtf=True, tlb=True)
    assetsForm = cmds.formLayout("form", h=268, w=210)

    #create heading
    assetText = cmds.frameLayout("assetHeading", l="ASSETS:", p = assetsForm, w=200)

    #create thumbnails layout
    assetList=cmds.iconTextScrollList("assetList", w=200, h=200, allowMultiSelection=True, p=assetsForm)

    #create buttons
    delSelAssets=cmds.button("dSel", l="Delete Selected", w=97.5, p=assetsForm, c=delSelAssA, ann="Delete Selected mGo Asset Folders")
    delAllAssets=cmds.button("dAll", l="Delete All", w=97.5, p=assetsForm, c=delAllAssA, ann="Delete All mGo Assets")

    #browse button
    assetIcon=cmds.iconTextButton("browseIcon", p=assetsForm, image="SP_DirIcon.png", ann="Explore Main mGo Assets Folder (" + assetsPath + ")", c=openExplorer)

    if availProjects is not None:
        for i in availProjects:
            cmds.iconTextScrollList("assetList", e=True, append = i)

    cmds.formLayout(assetsForm, edit = True, af = [(assetText,  "top", 5), (assetText, "left", 5)] )
    cmds.formLayout(assetsForm, edit = True, af = [(assetIcon,  "top", 7), (assetIcon, "left", 184)] )
    cmds.formLayout(assetsForm, edit = True, af = [(assetList,  "top", 32), (assetList, "left", 5)] )
    cmds.formLayout(assetsForm, edit = True, af = [(delSelAssets,  "top", 237), (delSelAssets, "left", 5)] )
    cmds.formLayout(assetsForm, edit = True, af = [(delAllAssets,  "top", 237), (delAllAssets, "left", 108)] )

    #show the assetUI window
    cmds.showWindow(assetsWindow)

#function to begin deletion of selected assets
def delSelAssA(*args):

    myitems=cmds.iconTextScrollList("assetList", q=True, si = True)

    #get amount of selected assets
    try:
        numAss=len(myitems)

        cmds.frameLayout("assetHeading", e=True, l="DELETING " + str(numAss) + " FOLDER(S) - Y / N ?")
        cmds.button("dSel", e=True, l="No", c=resetAssetMenu, ann="Cancel Operation")
        cmds.button("dAll", e=True, l="Yes", c=delSelAssB, ann="Delete Selected mGo Asset Folders")

    except:
        print("Please Select Atleast 1 File for Deletion")
        cmds.inViewMessage( amg='Please Select Atleast 1 File for Deletion', pos='botCenter', fade=True, fadeOutTime=500)

#function to finalise deletion of selected assets
def delSelAssB(*args):
    #set working dir
    os.chdir(assetsPath)

    #query selected assets
    assetFolders=cmds.iconTextScrollList("assetList", q=True, si = True)

    #remove folders
    for i in assetFolders:
        try:
            shutil.rmtree(i)
        except:
            cmds.inViewMessage( amg="Couldn't delete <hl>'%s'</hl> folder, possibly <hl>in use by another program</hl>" %i , pos='botCenter', fade=True, fadeOutTime=500)

    #get latest contents
    availProjects=next(os.walk(str(assetsPath)))[1]

    #clear text scroll list
    cmds.iconTextScrollList("assetList", e=True, ra = True)

    #populate contents
    if availProjects is not None:
        for i in availProjects:
            cmds.iconTextScrollList("assetList", e=True, append = i)

    #reset Assets UI
    resetAssetMenu()

#function to begin deletion of all assets
def delAllAssA(*args):

    cmds.frameLayout("assetHeading", e=True, l="DELETE ALL FOLDERS - Y / N ?")
    cmds.button("dSel", e=True, l="No", c=resetAssetMenu, ann="Cancel Operation")
    cmds.button("dAll", e=True, l="Yes", c=delAllAssB, ann="Delete All Assets")

#function to finalise deletion of all assets
def delAllAssB(*args):
    #set working dir
    os.chdir(assetsPath)

    #get all folders in Assets dir and delete
    try:
        if availProjects is not None:
            for i in availProjects:
                try:
                    shutil.rmtree(i)
                except:
                    cmds.inViewMessage( amg="Couldn't delete <hl>'%s'</hl> folder, possibly <hl>in use by another program</hl>" %i , pos='botCenter', fade=True, fadeOutTime=500)

        #clear text scroll list
        cmds.iconTextScrollList("assetList", e=True, ra = True)
        cmds.inViewMessage( amg='mGo Assets Folder Cleared', pos='botCenter', fade=True, fadeOutTime=500)

    except:
        print("Unable to delete all assets. Please check Assets folder")
        cmds.inViewMessage( amg='Unable to delete all assets. Please check Assets folder', pos='midCenter', fade=True, fadeOutTime=500)

#function to reset Assets UI
def resetAssetMenu(*args):
    cmds.frameLayout("assetHeading", e=True, l="ASSETS:")
    cmds.button("dSel", e=True, l="Delete Selected", c=delSelAssA, ann= "Delete Selected mGo Asset Folders")
    cmds.button("dAll", e=True, l="Delete All", c=delAllAssA, ann= "Delete All mGo Assets")
    cmds.iconTextScrollList("assetList", e=True, da = True)


#function to save out shader attributes as a .pre file for mGo-Materialiser
def saveShader(*args):
    #Materialiser Path
    presetsmGoPath = mGoPath + "/Presets"
    #Check if the selected Nodes are one of the supported shaders
    try:
        shaders = cmds.selectedNodes()
        for shader in shaders:
            shaderType = str(cmds.nodeType(shader))
            print("Node type: '" +shaderType+ "'")
            if (shaderType != "aiStandard") and (shaderType != "VRayMtl") and (shaderType != "RedshiftArchitectural"):
                cmds.inViewMessage( amg='Please select one of the following shader types: <hl>aiStandard, VRayMtl, RedshiftArchitectural</hl>', pos='midCenter', fade=True, fadeOutTime=500)
                return
    except:
        cmds.inViewMessage( amg='Please select one of the following shader types: <hl>aiStandard, VRayMtl, RedshiftArchitectural</hl>', pos='midCenter', fade=True, fadeOutTime=500)
        return

    #Multiple shaders save by name in the current selected directory.
    if len(shaders) > 0:
        filePath = cmds.fileDialog2(dir=presetsmGoPath, fileFilter="*.pre", caption="Please select a Folder to where the Shaders Preset will be saved.", fileMode=3)
        if filePath != None:
            path = filePath[0]
            print("------------- File Path -------------")
            print(path)
            for shader in shaders:
                print("------- Current Selected shader: '" +shader+ "' -------")
                #Write the preset file with the shader info.
                configShaderData = getShaderData(shader, shaderType)
                fileName = shader.rsplit(":",1)[-1].lstrip("mGo_").rstrip("_mat")
                if configShaderData != None:
                    f = open(path+"/"+fileName+".pre", 'w')
                    pickle.dump(configShaderData, f)
                    f.close()
        else:
            print("Save shader operation canceled.")

    #Single shader save by name in the current selected directory.
    else:
        shader = shaders
        print("------- Current Selected shader: '" +shader+ "' -------")
        #Write the preset file with the shader info.
        configShaderData = getShaderData(shader, shaderType)
        if configShaderData != None:
            filePath = cmds.fileDialog2(dir=presetsmGoPath, fileFilter="*.pre", caption="Save Shader Preset for mGo - Materialiser in Mari", fileMode=0)
            if filePath != None:
                path = filePath[0]
                print("------------- File Path -------------")
                print(path)
                
                f = open(path, 'w')
                pickle.dump(configShaderData, f)
                f.close()
            else:
                print("Save shader operation canceled.")


#function for importing previously saved .mgo Description files
def loadMariSceneDesc(*args):

    try:
        filePath = cmds.fileDialog2(fileFilter="*.mgo", caption="Locate an mGo Description File", fileMode=1 )
        #Check if we are about to load multipleDescriptions
        if filePath[0].rsplit("/", 1)[-1] == "Project_description.mgo":
            f = open(filePath[0], 'r')
            config = pickle.load(f)
            f.close()

            # Get all Scene Description Paths
            print("------------- mGo Load Scene Description -------------")
            filePaths = config[0]
            # Load each Description found
            for filePath in config:
                sceneDescriptionFilePath = filePath
                print("Description Path: '" + sceneDescriptionFilePath.rsplit("/",1)[0] + "/'")
                import mGo_Maya
                importlib.reload(mGo_Maya)
                mGo_Maya.loadSceneDesc(sceneDescriptionFilePath)

        else:
            #Single Description Load
            print("------------- mGo Load Scene Description -------------")
            sceneDescriptionFilePath = filePath[0]
            print("Description Path: '" + sceneDescriptionFilePath.rsplit("/",1)[0] + "/'")
            import mGo_Maya
            importlib.reload(mGo_Maya)
            mGo_Maya.loadSceneDesc(sceneDescriptionFilePath)


        print("mGo Description Loaded!")
        cmds.inViewMessage( amg='Imported mGo Description', pos='botCenter', fade=True, fadeOutTime=500)

    except:
        print("ERROR - Unable to load file!")
        cmds.inViewMessage( amg='ERROR - Unable to load file!', pos='botCenter', fade=True, fadeOutTime=500)


#function to change the color of the light in the mGo logo accordingly to the connection status.
def portLight(mariHost):
        global IP
        print(mariHost)
        #Check the state of each port, and set the light colour accordingly
        if mariOpen==True:
            print("Maya and Mari port are open.")
            mGoIcon=cmds.image("mGoIcon", e=True, i="mGo_green.png")
            cmds.button("SendObject", e=True, en=True)
            cmds.button("ExportCamera", e=True, en=True)
        else:
            print("Maya is open. Mari port is closed")
            mGoIcon=cmds.image("mGoIcon", e=True, i="mGo_yellow.png")
            cmds.button("SendObject", e=True, en=False)
            cmds.button("ExportCamera", e=True, en=False)

#function to test connection to currently selected network address
def testConnection(mariHost):
    global mariOpen

    #try out the connection
    try:
        mari = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        mari.connect((mariHost, 6100))
        mari.send('print("establishing connection with mGo Maya...")\x04')
        mari.close()

        mariOpen=True
        cmds.inViewMessage( amg="Connection to Mari <hl>established</hl>", pos='botCenter', fade=True, fadeOutTime=500 )
    except:
        mariOpen=False

        cmds.inViewMessage( amg="<hl>ERROR</hl> - Unable to reach Mari at network address <hl>'%s'</hl>" % mariHost, pos='botCenter', fade=True, fadeOutTime=500 )

    #Switch the icons for the mGo Logo
    portLight(mariHost)


#Function responsible to change on fly the ip display on the top of the UI
def changeUI(ipDisplay):
    global yourIP_pos
    global form
    global yourIP
    yourIP_pos = 115+( 15-len(ipDisplay) )-len(ipDisplay)
    cmds.text("yourIP", e= True, l=ipDisplay)
    cmds.formLayout(form, edit = True, af = [(yourIP,  "top", 23), (yourIP, "left", yourIP_pos)] )

#function to update the projects menu UI with existing Mari projects in the Mari HOST Machine
def getProjects(*args):
    if mariOpen==False:
        cmds.inViewMessage( amg="<hl>ERROR</hl> - Unable to reach Mari at network address <hl>'%s'</hl>" % mariHost, pos='botCenter', fade=True, fadeOutTime=500 )
        
    global mariOpen
    #If the connection can't be made, clear the projects menu!
    if mariOpen != True:
        print("Mari port is not open!")
        allProjs = cmds.optionMenu("projectMenu", q = True, itemListLong = True)

        #delete current projects in list
        if allProjs is not None:
            for item in allProjs:
                cmds.deleteUI(item)

        #default item in projects menu
        noProj="- Projects -"

        #add noProj ---
        cmds.menuItem(label = noProj, parent = "projectMenu")
        return

    ipConnection = 'localhost'
    #Interprete the menu, use currentMariHost, and pass the ipConnection that is the ip of the mayaHost Machine
    currentMariHost=cmds.optionMenu("hosts", q = True, v = True)
    if currentMariHost != "Local Host Only":
        global IP
        ipConnection = IP

    #socket code
    global mariHost
    try:
        mari = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        mari.connect((mariHost, 6100))
        mari.send('Mari.Scripts.mGo.getProjects("%s", "%s")\x04' % (ipConnection, mGoPath) )
        mari.close()
        mariOpen=True
    except:
        #Mari port is not open!
        mariOpen=False
        print("Failed to establish a connection with Mari to update Mari Projects List... Please launch Mari and enable Port 6100")

    try:
        #get the Mari projects list and populate Projects Menu
        mariProjs = open(mGoPath +"/"+ 'mariProjects.txt', 'r')
        getProjs= mariProjs.read()
        mariProjs.close()

        allProjs = cmds.optionMenu("projectMenu", q = True, itemListLong = True)

        #delete current projects in list
        if allProjs is not None:
            for item in allProjs:
                cmds.deleteUI(item)

        getProjs.split("[", 1)[1]

        #do magic to turn string into list
        import ast
        getProjs = ast.literal_eval(getProjs)

        #alphabetise list
        getProjs.sort()

        #put projects in list
        for p in getProjs:
            cmds.menuItem(label = p, parent = "projectMenu", ann=p)

    except:
        print("mariProjects.txt File not found... Check the mGo connection between Mari and Maya by closing and opening again mGo Maya UI. Notice if the mGo logo has green light on it?")


    #display message if can't update projects list and set portlight
    if projMessage==True:

        if mariOpen==False:
            cmds.inViewMessage( amg='Unable to set current Mari Projects List... Please open Mari and make sure <hl>Port 6100</hl> is enabled', pos='botCenter', fade=True, fadeOutTime=2000)

        #set the icons
        portLight(mariHost)
        changeProjB()


#function to write a user Mel file that keeps the port 6010 open at localhost
def writeUserMel(*args):
    #create userSetup Mel to keep port open over maya sessions
    scriptsPath = cmds.internalVar(userScriptDir=True)
    name_of_file = "userSetup.mel"
    completeName = os.path.join(scriptsPath, name_of_file)

    appendText='commandPort -n "localhost:6010" -sourceType "python";'
    try:
        with open(completeName, "a+") as myfile:
            appendTextExists = False
            lines = myfile.readlines()
            #getting rid of '\n'
            lines = [s.strip() for s in lines]
            #Seek in the lines of the file userSetup.mel for the command that you want to append.
            for line in lines:
                if line == appendText:
                    appendTextExists = True

            #Append the command to the userSetup.mel
            if appendTextExists != True:
                myfile.write(appendText+'\n')
    except:
        pass

#function to open/close port 6010 for an specific network address
def openPort(*args):
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
                if  ifconfig_strings == "inet":
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

    #mariHost menu interpretation
    global mariHost
    mariHost=cmds.optionMenu("hosts", q = True, v = True)
    if mariHost == "Local Host Only":
        #close IP port if that is opened
        for IP in IPS:
            try:
                if cmds.commandPort(str(IP)+":6010", q=True):
                    cmds.commandPort(name=str(IP)+":6010", cl=True)
            except:
                print("ERROR - Couldn't Close the port for: "+IP+" address.")

        #Open the port to 'localhost'
        mariHost = "localhost"
        if cmds.commandPort(mariHost+":6010", q=True) != True:
            cmds.commandPort(name=mariHost+":6010", sourceType="python")
            writeUserMel()
        changeUI(mariHost)

    elif mariHost == "Network Host":
        #Open the port to my IP
        mariHost = IPS[0]
        for IP in IPS:
            try:
                if not cmds.commandPort(str(IP)+":6010", q=True):
                    cmds.commandPort(name=str(IP)+":6010", sourceType="python")
            except:
                print("ERROR - Couldn't OPen the port for: "+IP+" address.")
        changeUI(IPS[0])

    else:
        mariHost = cmds.optionMenu("hosts", q = True, v = True)
        #Open the port to my IP but keep mariHost with the selected IP from hosts menu in order to maintain any connection with the machine where Mari is hosted
        for IP in IPS:
            try:
                if not cmds.commandPort(str(IP)+":6010", q=True):
                    cmds.commandPort(name=str(IP)+":6010", sourceType="python")
            except:
                print("ERROR - Couldn't OPen the port for: "+IP+" address.")
        changeUI(IPS[0])

    global IP
    IP = str(IPS[0])
    #write the current Host used in the top of the file list. So every time you start mGo, it will set the menu to this Host.
    filepathHosts=mGoPath + '/mariHosts.txt'
    with open(filepathHosts) as rd:
        items = rd.readlines()
        #getting rid of '\n'
        items = [s.strip() for s in items]

    hostLog = items

    currentMariHost=cmds.optionMenu("hosts", q = True, v = True)

    hostList = []
    hostList.append(currentMariHost)

    for item in hostLog:
        if item != currentMariHost:
            hostList.append(item)

    f = open(filepathHosts, 'w')
    for item in hostList:
        f.write(item + os.linesep)
    f.close()

    testConnection(mariHost)
    #Update the projects menu as you switch Hosts.
    getProjects()

#function to add a specific network address
def newAddress(*args):
    #create promptDialog
    result = cmds.promptDialog(
            title='MARI Machine IP',
            message='Enter New Address:',
            button=['Cancel', 'OK'],
            defaultButton='OK',
            cancelButton='Cancel',
            dismissString='Cancel')

    if result == 'OK':
        text = cmds.promptDialog(query=True, text=True)

        filepathHosts=mGoPath + '/mariHosts.txt'

        print("Mari Host file: '" + filepathHosts + "'")

        #Try to read the file and see if the address already exists in the file
        addressExist = False
        try:
            with open(filepathHosts) as rd:
                items = rd.readlines()

            #getting rid of '\n'
            items = [s.strip() for s in items]

            for i in items:
                if i == text:
                    addressExist = True
        except:
            pass

        #If address does not exists then do what it is needed
        if addressExist == False:
            f = open(filepathHosts, 'a+')
            f.write(str(text) + '\n')
            f.close()

            #updating the hosts optionmenu
            allHosts = cmds.optionMenu("hosts", q = True, itemListLong = True)

            #delete current projects in list
            if allHosts!=[]:
                for item in allHosts:
                    cmds.deleteUI(item)

            #reading the Mari host addresses from mariHosts.txt
            with open(filepathHosts) as rd:
                items = rd.readlines()

            #getting rid of '\n'
            items = [s.strip() for s in items]

            #put addresses in list
            for i in items:
                cmds.menuItem(label = i, parent = "hosts", ann=i)

        #set saved address
        cmds.optionMenu("hosts", e = True, v = text)

        #try out the connection
        openPort()
