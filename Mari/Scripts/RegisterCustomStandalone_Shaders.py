# ------------------------------------------------------------------------------
# Mari Custom Shaders BRDF models written in GLSL & Mari Custom BRDF Function Library Extension Registration
# Copyright (c) 2014 Antonio Lisboa M. Neto. All Rights Reserved.
# ------------------------------------------------------------------------------
# Author: Antonio Neto
# Web: www.netocg.blogspot.com
# Email: netocg.fx@gmail.com
# ------------------------------------------------------------------------------

import mari	

def registerBRDF_FunctionLib_ext_Header():
	"Register a new module extension of functions for Custom BRDF Shaders"
	# Register the code as glsl header and source files
	try:
		mari.gl_render.registerCustomHeaderFile("BRDF_FunctionLib_ext_Header", mari.resources.path(mari.resources.USER_SCRIPTS) + "/Mari/Shaders/include_library/BRDF_FunctionLib_ext.glslh")
		mari.gl_render.registerCustomCodeFile("BRDF_FunctionLib_ext_Source", mari.resources.path(mari.resources.USER_SCRIPTS) + "/Mari/Shaders/include_library/BRDF_FunctionLib_ext.glslc")
		print 'Registered Library - BRDF Lib extension'
	except Exception as exc:
		print 'Error Register Library - BRDF Lib extension : ' + str(exc)		
	
def registeraiStandard():
	"Register a Custom Standalone Shader"
	# Register the code as a new custom shader module
	try:
		mari.gl_render.registerCustomStandaloneShaderFromXMLFile("aiStandard",mari.resources.path(mari.resources.USER_SCRIPTS) + "/Mari/Shaders/AiStandard.xml")
		print 'Registered Custom Standalone Arnold Shader - aiStandard'
	except Exception as exc:
		print 'Error Register Custom Standalone Arnold Shader - aiStandard : ' + str(exc)

def registerVRayMtl():
	"Register a Custom Standalone Shader"
	# Register the code as a new custom shader module
	try:
		mari.gl_render.registerCustomStandaloneShaderFromXMLFile("VRayMtl",mari.resources.path(mari.resources.USER_SCRIPTS) + "/Mari/Shaders/VRayMtl.xml")
		print 'Registered Custom Standalone V-Ray Shader - VRayMtl'
	except Exception as exc:
		print 'Error Register Custom Standalone V-Ray Shader - VRayMtl : ' + str(exc)

def registerredshiftArchitectural():
	"Register a Custom Standalone Shader"
	# Register the code as a new custom shader module
	try:
		mari.gl_render.registerCustomStandaloneShaderFromXMLFile("redshiftArchitectural",mari.resources.path(mari.resources.USER_SCRIPTS) + "/Mari/Shaders/RedshiftArchitectural.xml")
		print 'Registered Custom Standalone Redshift Shader - redshiftArchitectural'
	except Exception as exc:
		print 'Error Register Custom Standalone Redshift Shader - redshiftArchitectural : ' + str(exc)		
# ------------------------------------------------------------------------------
# Main function library

# Call register function from module
registerBRDF_FunctionLib_ext_Header()

# Call register Custom Standalone Shaders
registeraiStandard()
registerVRayMtl()
registerredshiftArchitectural()