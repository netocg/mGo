mGo! - Mari 3.2 to Maya 2015 Bridge tool
https://youtu.be/cE-eKhWPLz4

Works in conjunction with Custom Mari Shaders by Antonio Neto. 

--------------------------------

Installation and Usage:

--------------------------------


1. Place mGo.py in C:\Users\xxxx\Documents\Mari

2. Place mGo_Maya.py in your Maya scripts folder

3. Before Mari can talk to Maya, you'll need to open a specific port in Maya. To do this, input this code in the Maya mel command line or script editor... 


commandPort -n ":6010" -sourceType "python";


4. In Mari, open the python console by clicking on the 'Python' menu in the top menu bar, then selecting 'Show Console'. 

5. Click the button associated with the 'Script Path' text field (small, square, lower right button), select 'mGo.py'and click 'Open'. 

6. Finally, click on the 'Evaluate' button in the bottom left of the python console. The mGo pallete should now show in the Mari UI. Dock to preference.


---------------------------------

How to Use

---------------------------------


mGo! is an exporter tool designed to shorten the asset creation and look development gap existing between Mari and your 3d software package (presently only Maya is supported). Working in conjunction with OpenGL production based shaders (Arnold, Vray, Redshift, etc) mGo! takes shader data (inputs and attributes) which the user has set in Mari, and re-creates the same shader in Maya by constructing a new shading network and setting the same data. Shaders can be updated in Mari and re-transferred over to Maya at any time. 

There are a few options for defining what kinds of information will be sent across to Maya- listed below.


Channels: 
--------- 

When enabled, any channels assigned to shader inputs within the currently selected Mari shader will be exported (flattened) to a folder specified by the user in the 'Output Directory' text field in the mGo! UI. 

Note: mGo_Maya script will look for textures based on a particular naming convention set when saving out channels via mGo!. If you've defined your textures folder in mGo!, but haven't saved out your textures based on this convention, then Maya won't be able to find the textures and hook them up to the network properly. It's advised to tick the mGo! checkbox 'Channels' when first transferring your data over to Maya- that way the textures will be saved with the appropriate filenames.

Similarly, it's probably a good idea to untick the channels checkbox if no changes have been made to previously saved textures via mGo! (for instance, you are just tweaking shader attributes). 


Attributes:
-----------

When enabled, all attributes set within the currently selected Mari shader will be exported. Attributes are shader parameters which aren't being defined by textures. For eg, the shader component Diffuse Color, can have a texture assigned to it via an 'input', or be defined by an RGB colour or numerical value instead as an 'attribute'. The basic rule is that if there's a texture (channel) assigned to an input, that will override the attribute for that component. 


Object:
-------

When enabled, the currently selected Mari object will be imported into the Maya scene (provided the file is still in the same location it was saved), and the relevant shader will be connected to it.


More options:
-------------

Texture files are named based on the channel assigned to a shader input, and include a <udim> tag for multi UV patch rendering inside Maya. The file format is set by the two file format option boxes inside the UI. 8-Bit file formats will be saved as the chosen 8-bit format, likewise for 16/32 bit files. 

Filter:

This setting relates to texture filtering options inside Maya's filenode. By default in Maya, filter type is set to 'Quadratic'. If you want quadratic filtering, select the 'Default' setting in mGo!.

The 'Off' setting sets filter type to 'Off' in Maya. 

The 'Animation' or 'Anim' setting may be more appropriate for animations. It is Quadratic filtering with a reduced filter of .1, down from the default of 1. 


mGo!
----

The mGo! button begins the export function, which includes saving out any channels, attributes and other data selected for export. A small data file is generated followed by a python command sent to Maya via the command port, telling it to run the mGo_Maya.py file. mGo_Maya.py reads the data from the data file and constructs the shading network. The type of shader created depends on the type of shader you are using in Mari (aiStandard shader in Mari will create an aiStandard material in Maya). Textures will automatically be hooked up to the shading network, consistent with how they were assigned in Mari (a channel feeding into the diffuse input in the Mari shader will be assigned to the diffuse slot in the Maya shader, and so on). Displacement and bump nodes will be automatically generated where necessary. 



You can update the network as long as you like, adding and deleting channels/textures and tweaking attributes. 


Happy Texturing/Shading,


Exporter Author:

Stu Tozer
stutozer@gmail.com

Shaders Author:

Antonio Neto
netocg.fx@gmail.com





















