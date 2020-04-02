cmake_minimum_required(VERSION 2.8.9)

project(NeedleTracking)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "http://www.example.com/Slicer/Extensions/NeedleTracking")
set(EXTENSION_CATEGORY "IGT")
set(EXTENSION_CONTRIBUTORS "Junichi Tokuda, Wei Wang, Ehud Schmidt (BWH)")
set(EXTENSION_DESCRIPTION "Utility module for MR Tracking Research.")
set(EXTENSION_ICONURL "http://www.example.com/Slicer/Extensions/NeedleTracking.png")
set(EXTENSION_SCREENSHOTURLS "http://www.example.com/Slicer/Extensions/NeedleTracking/Screenshots/1.png")

#-----------------------------------------------------------------------------
# Extension dependencies
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

#-----------------------------------------------------------------------------
# Extension modules
add_subdirectory(NeedleTracking)
## NEXT_MODULE

#-----------------------------------------------------------------------------
include(${Slicer_EXTENSION_CPACK})
