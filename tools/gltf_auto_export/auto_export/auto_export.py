import copy
import json
import os
from types import SimpleNamespace
import bpy
import traceback


from .preferences import AutoExportGltfAddonPreferences

from .get_collections_to_export import get_collections_to_export
from .get_levels_to_export import get_levels_to_export
from .get_standard_exporter_settings import get_standard_exporter_settings

from .export_main_scenes import export_main_scene
from .export_blueprints import export_blueprints

from ..helpers.helpers_scenes import (get_scenes, )
from ..helpers.helpers_blueprints import blueprints_scan

from ..modules.export_materials import cleanup_materials, export_materials
from ..modules.bevy_scene_components import remove_scene_components, upsert_scene_components


"""this is the main 'central' function for all auto export """
def auto_export(changes_per_scene, changed_export_parameters, addon_prefs):
    # have the export parameters (not auto export, just gltf export) have changed: if yes (for example switch from glb to gltf, compression or not, animations or not etc), we need to re-export everything
    print ("changed_export_parameters", changed_export_parameters)
    try:
        # path to the current blend file
        file_path = bpy.data.filepath
        # Get the folder
        folder_path = os.path.dirname(file_path)
        # get the preferences for our addon
        #should we use change detection or not 
        export_change_detection = getattr(addon_prefs, "export_change_detection")

        do_export_blueprints = getattr(addon_prefs,"export_blueprints")
        export_output_folder = getattr(addon_prefs,"export_output_folder")
        export_models_path = os.path.join(folder_path, export_output_folder)

        export_materials_library = getattr(addon_prefs,"export_materials_library")
        export_scene_settings = getattr(addon_prefs,"export_scene_settings")

        # standard gltf export settings are stored differently
        standard_gltf_exporter_settings = get_standard_exporter_settings()
        gltf_extension = standard_gltf_exporter_settings.get("export_format", 'GLB')
        gltf_extension = '.glb' if gltf_extension == 'GLB' else '.gltf'

        # here we do a bit of workaround by creating an override # TODO: do this at the "UI" level
        export_blueprints_path = os.path.join(folder_path, export_output_folder, getattr(addon_prefs,"export_blueprints_path")) if getattr(addon_prefs,"export_blueprints_path") != '' else folder_path
        #print('addon_prefs', AutoExportGltfAddonPreferences.__annotations__)#)addon_prefs.__annotations__)

        print("collection_instances_combine_mode", addon_prefs.collection_instances_combine_mode)
        """if hasattr(addon_prefs, "__annotations__") :
            tmp = {}
            for k in AutoExportGltfAddonPreferences.__annotations__:
                item = AutoExportGltfAddonPreferences.__annotations__[k]
                #print("tutu",k, item.keywords.get('default', None) )
                default = item.keywords.get('default', None)
                tmp[k] = default
            
            for (k, v) in addon_prefs.properties.items():
                tmp[k] = v

            addon_prefs = SimpleNamespace(**tmp) #copy.deepcopy(addon_prefs)
            addon_prefs.__annotations__ = tmp"""
        addon_prefs.export_blueprints_path = export_blueprints_path
        addon_prefs.export_gltf_extension = gltf_extension
        addon_prefs.export_models_path = export_models_path

        [main_scene_names, level_scenes, library_scene_names, library_scenes] = get_scenes(addon_prefs)

        print("main scenes", main_scene_names, "library_scenes", library_scene_names)
        print("export_output_folder", export_output_folder)

        blueprints_data = blueprints_scan(level_scenes, library_scenes, addon_prefs)
        blueprints_per_scene = blueprints_data.blueprints_per_scenes
        internal_blueprints = [blueprint.name for blueprint in blueprints_data.internal_blueprints]
        external_blueprints = [blueprint.name for blueprint in blueprints_data.external_blueprints]

        if export_scene_settings:
            # inject/ update scene components
            upsert_scene_components(level_scenes)
        #inject/ update light shadow information
        for light in bpy.data.lights:
            enabled = 'true' if light.use_shadow else 'false'
            light['BlenderLightShadows'] = f"(enabled: {enabled}, buffer_bias: {light.shadow_buffer_bias})"

        # export
        if do_export_blueprints:
            print("EXPORTING")
            # get blueprints/collections infos
            (blueprints_to_export) = get_collections_to_export(changes_per_scene, changed_export_parameters, blueprints_data, addon_prefs)
             
            # get level/main scenes infos
            (main_scenes_to_export) = get_levels_to_export(changes_per_scene, changed_export_parameters, blueprints_data, addon_prefs)

            # since materials export adds components we need to call this before blueprints are exported
            # export materials & inject materials components into relevant objects
            if export_materials_library:
                export_materials(blueprints_data.blueprint_names, library_scenes, folder_path, addon_prefs)

            # update the list of tracked exports
            exports_total = len(blueprints_to_export) + len(main_scenes_to_export) + (1 if export_materials_library else 0)
            bpy.context.window_manager.auto_export_tracker.exports_total = exports_total
            bpy.context.window_manager.auto_export_tracker.exports_count = exports_total

            print("-------------------------------")
            #print("collections:               all:", collections)
            #print("collections: not found on disk:", collections_not_on_disk)
            print("BLUEPRINTS:    local/internal:", internal_blueprints)
            print("BLUEPRINTS:          external:", external_blueprints)
            print("BLUEPRINTS:         per_scene:", blueprints_per_scene)
            print("-------------------------------")
            print("BLUEPRINTS:          to export:", [blueprint.name for blueprint in blueprints_to_export])
            print("-------------------------------")
            print("MAIN SCENES:         to export:", main_scenes_to_export)
            print("-------------------------------")
            # backup current active scene
            old_current_scene = bpy.context.scene
            # backup current selections
            old_selections = bpy.context.selected_objects

            # first export any main/level/world scenes
            if len(main_scenes_to_export) > 0:
                print("export MAIN scenes")
                for scene_name in main_scenes_to_export:
                    print("     exporting scene:", scene_name)
                    export_main_scene(bpy.data.scenes[scene_name], folder_path, addon_prefs, blueprints_data)

            # now deal with blueprints/collections
            do_export_library_scene = not export_change_detection or changed_export_parameters or len(blueprints_to_export) > 0
            if do_export_library_scene:
                print("export LIBRARY")
                # we only want to go through the library scenes where our blueprints to export are present
                """for (scene_name, blueprints_to_export)  in blueprints_per_scene.items():
                    print("     exporting blueprints from scene:", scene_name)
                    print("     blueprints to export", blueprints_to_export)"""
                export_blueprints(blueprints_to_export, folder_path, addon_prefs, blueprints_data)

            # reset current scene from backup
            bpy.context.window.scene = old_current_scene

            # reset selections
            for obj in old_selections:
                obj.select_set(True)
            if export_materials_library:
                cleanup_materials(blueprints_data.blueprint_names, library_scenes)

        else:
            for scene_name in main_scene_names:
                export_main_scene(bpy.data.scenes[scene_name], folder_path, addon_prefs, [])



    except Exception as error:
        print(traceback.format_exc())

        def error_message(self, context):
            self.layout.label(text="Failure during auto_export: Error: "+ str(error))

        bpy.context.window_manager.popup_menu(error_message, title="Error", icon='ERROR')

    finally:
        # FIXME: error handling ? also redundant
        [main_scene_names, main_scenes, library_scene_names, library_scenes] = get_scenes(addon_prefs)

        if export_scene_settings:
            # inject/ update scene components
            remove_scene_components(main_scenes)

