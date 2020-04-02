NeedleTracking
==============
Slicer Module for Needle Tracking


Prerequisite
============

This module has been tested only on Slicer 4.10.x 

Installation
============

3D Slicer Extensions
--------------------

After installing 3D Slicer, add the following extensions (plug-ins) from the Extension Manager:

- SlicerOpenIGTLink
- SlicerIGT

After adding those extensions, you will be asked to restart 3D Slicer.

Needle Tracking Module
-----------------------

[Needle Tracking Module](https://github.com/ProstateBRP/NeedleTracking) is currently not listed in the Extension Manager, and will need to be installed manually with the following steps:

- Download the source code by either:
  - downloading a zipped archive from [this link](https://github.com/ProstateBRP/NeedleTracking/archive/master.zip)
  - Cloning the repository using the Git command:

~~~~
$ git clone https://github.com/ProstateBRP/NeedleTracking
~~~~

- Extract the source tree if you have downloaded the zipped archive. Save the source tree in your local disk.
- Launch 3D Slicer and open "Application Settings" form the "Edit" menu.
- Choose "Modules" from the list on the left of the Application Setting window.
- In the "Additional module paths," click the "Add" button. If "Add" button is hiddne, click the ">>" button on the right edge of the module list.
- Choose the "NeedleTracking" under the source tree. Note that there is a child "NeedleTracking" folder under the parent "NeedleTracking" folder. Choose the child one.
- The module path that shows up on the list would look like: "/Users/junichi/modules/NeedleTracking/NeedleTracking" (Confirm that there is "NeedleTracking" under "NeedleTracking".
- Restart 3D Slicer.
- If the module is installed properly, it should be listed under "IGT" on the Modules menu.

Usage
=====

Network Setting
---------------
The connector setup by the module works as a TCP server. The sender must be configured as a client. If the data is transferred over network, make sure that port 18944 TCP is open.

While the module provide the simple interface to setup an OpenIGTLink connector, the user may setup one from the SlicerOpenIGTLink module instead. In this case, the connector can be setup either server or client depending on the configuration of the sender. The rest of the module features do not depend on a specific configuration of the OpenIGTLink connector. 

Setting Up 3D Slicer
--------------------
- Open 3D Slicer
- Choose "IGT" -> "NeedleTracking" under the modules menu.
- Click the "Connector" pull-down menu and choose "Create new IGTLConnector"
- Make sure to specify "18944" (default) for the Port.
- Click the "Active" check box.


Starting the sender software
-----------------------------
Setup the tracking sequence and start the scan. If the tracking sequence is connected to the 3D Slicer properly, the catheter model should appear on the screen. You may not seen the model during prescan or while the catheter is outside the imaging volume.


Configuring the catheter (needle)
---------------------------------
Once Slicer starts receiving TDATA messages from the sender, a TrackingData node will appears in the "TrackingData" pull-down menu. Select the one with the message name and click the "Active" check button below the selector. The user can change the tip length, diameter, and opacity in the "Catheter configuration" menu.





















