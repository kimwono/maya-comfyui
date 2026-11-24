import maya.cmds as cmds
import maya.OpenMaya as om
import maya.OpenMayaUI as omui

def get_active_viewport_camera():
    view = omui.M3dView.active3dView()
    cam = om.MDagPath()
    view.getCamera(cam)
    return cam.fullPathName()

def render_view_to_image(file_path, width=1920, height=1080):
    # Set the resolution
    cmds.setAttr("defaultResolution.width", width)
    cmds.setAttr("defaultResolution.height", height)
    
    # Set the image format to PNG
    cmds.setAttr("defaultRenderGlobals.imageFormat", 32)  # 32 is for PNG
    
    # Get the active viewport camera
    active_camera = get_active_viewport_camera()
    
    # Set the current view to the active camera
    cmds.lookThru(active_camera)
    
    # Save the rendered image
    cmds.playblast(
        filename=file_path, 
        forceOverwrite=True, 
        format='image',
        width=width, 
        height=height, 
        startTime=cmds.currentTime(q=True), 
        endTime=cmds.currentTime(q=True), 
        clearCache=True,
        showOrnaments=False, 
        viewer=False,
        percent=100,
        quality=100,
        compression="png"
    )
    
    print(f"Image saved to: {file_path}")

# Example usage
render_view_to_image('/Users/wono/Desktop/Maya/rendered_image.png')