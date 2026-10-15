cmake_minimum_required(VERSION 3.16.3...3.19.7 FATAL_ERROR)

project(SlicerStrokeSegmentator)

set(EXTENSION_HOMEPAGE "https://github.com/parvezamu/SlicerStrokeSegmentator")
set(EXTENSION_CATEGORY "Segmentation")
set(EXTENSION_CONTRIBUTORS "Parvez Ahmad (Auckland Bioengineering Institute, University of Auckland)")
set(EXTENSION_DESCRIPTION "Automated chronic ischemic stroke lesion segmentation from T1-weighted MRI.")
set(EXTENSION_ICONURL "https://raw.githubusercontent.com/parvezamu/SlicerStrokeSegmentator/main/SlicerStrokeSegmentator/Resources/Icons/SlicerStrokeSegmentator.png")
set(EXTENSION_SCREENSHOTURLS "https://raw.githubusercontent.com/parvezamu/SlicerStrokeSegmentator/main/SlicerStrokeSegmentator/Resources/Screenshots/StrokeSegmentator.png")
set(EXTENSION_DEPENDS "NA")

find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

add_subdirectory(SlicerStrokeSegmentator)

include(${Slicer_EXTENSION_GENERATE_CONFIG})
include(${Slicer_EXTENSION_CPACK})
