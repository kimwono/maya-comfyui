import maya.cmds as cmds

def setup_camera(camera_name, width, height):
    # Create a new camera or use an existing one
    if not cmds.objExists(camera_name):
        camera_name = cmds.camera(name=camera_name)[0]
    else:
        camera_name = camera_name

    # Set the camera's position and focus
    cmds.setAttr(camera_name + '.translateX', 0)
    cmds.setAttr(camera_name + '.translateY', 0)
    cmds.setAttr(camera_name + '.translateZ', 10)  # Move the camera back along Z axis

    # Adjust the camera's focal length
    cmds.setAttr(camera_name + '.focalLength', 35)  # Adjust focal length as needed

    # Adjust the near and far clip planes
    cmds.setAttr(camera_name + '.nearClipPlane', 0.1)
    cmds.setAttr(camera_name + '.farClipPlane', 1000)

    # Adjust the orthographic width if using an orthographic camera
    if cmds.getAttr(camera_name + '.orthographic'):
        cmds.setAttr(camera_name + '.orthographicWidth', width / 10)

    return camera_name

def render_view_to_image(file_path, width=1920, height=1080):
    # Set the resolution
    cmds.setAttr("defaultResolution.width", width)
    cmds.setAttr("defaultResolution.height", height)

    # Set the image format (0 = PNG, 1 = JPEG, etc.)
    cmds.setAttr("defaultRenderGlobals.imageFormat", 0)

    # Setup camera
    camera_name = setup_camera('renderCam', width, height)

    # Set the current view to the render camera
    cmds.lookThru(camera_name)

    # Save the rendered image
    cmds.playblast(format='image', filename=file_path, forceOverwrite=True, width=width, height=height, startTime=1, endTime=1, showOrnaments=False, viewer=False)

# Example usage
render_view_to_image('/Users/wono/Desktop/Maya/rendered_image.png')
