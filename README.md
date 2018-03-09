## Download
http://www.luxrender.net/en_GB/blender_2_5


## Installation
http://www.luxrender.net/wiki/LuxBlend_2.5_installation_instructions


## One-Click Update
http://www.luxrender.net/wiki/LuxBlend25_LuxCore#Updating_LuxBlend


## Usage
http://www.luxrender.net/wiki/LuxBlend25_Manual

#### Classic API
This is the old PBRTv3 API that is no longer under active development. The following pages are specific to this API.

* [Render Settings](http://www.luxrender.net/wiki/LuxBlend25_Render_Panel)
* [Old Material Editor](http://www.luxrender.net/wiki/LuxBlend25_Materials)
* [Node Material Editor](http://www.luxrender.net/wiki/LuxBlend_Node_Editor)

#### LuxCore API
This is the new PBRTv3 API that is under active development. The following pages describe which features of the new API LuxBlend supports and how it differs from the old API.

* [LuxCore API Mode - Overview](http://www.luxrender.net/wiki/LuxBlend25_LuxCore)
* [LuxCore API Node Material Editor](http://www.luxrender.net/wiki/LuxBlend25_LuxCore_NodeEditor)


## Tutorials

* http://www.luxrender.net/wiki/LuxBlend25_Tutorials


# For Developers

## Project Structure
The code is located in **src/luxrender**. 

* **core** Most of the main work (rendering loop, material previews) starts here. 
* **export** All geometry export happens here, also all materials defined in the old material editor (panel-based) are exported here. Note: nodetree export functions are defined in **properties**. The **luxcore** subfolder contains the LuxCore API export routines.
* **extensions_framework** Abstraction code for LuxBlend's data structures
* **operators** All operators are located here.
* **outputs** API specific stuff.
* **properties** Definitions of LuxBlend datastructures (e.g. materials, lamp settings, export settings, basically every panel you see in the UI). This also includes the node editor as well as the Classic/LuxCore export routines for material and volume nodetrees.
* **ui** Drawing of UI elements happens here. Most of the time this is just a call to the corresponding property group (defined in **properties/**), but sometimes we need more control than those can offer, so there's also "Blender-Style" UI code.


## Authors
http://www.luxrender.net/en_GB/authors_contributors