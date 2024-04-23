import bpy
import os 
import json
import mathutils
import pytest
import shutil
import pathlib

@pytest.fixture
def setup_data(request):
    print("\nSetting up resources...")

    def finalizer():
        root_path =  "../../testing/bevy_example"
        assets_root_path = os.path.join(root_path, "assets")
        models_path =  os.path.join(assets_root_path, "models")
        materials_path = os.path.join(assets_root_path, "materials")
        #other_materials_path = os.path.join("../../testing", "other_materials")

        print("\nPerforming teardown...")
        if os.path.exists(models_path):
            shutil.rmtree(models_path)

        if os.path.exists(materials_path):
            shutil.rmtree(materials_path)

        diagnostics_file_path = os.path.join(root_path, "bevy_diagnostics.json")
        if os.path.exists(diagnostics_file_path):
            os.remove(diagnostics_file_path)
        
        hierarchy_file_path = os.path.join(root_path, "bevy_hierarchy.json")
        if os.path.exists(hierarchy_file_path):
            os.remove(hierarchy_file_path)

        screenshot_observed_path = os.path.join(root_path, "screenshot.png")
        if os.path.exists(screenshot_observed_path):
            os.remove(screenshot_observed_path)

    request.addfinalizer(finalizer)

    return None

import bpy
import os 
import json
import pytest
import shutil

@pytest.fixture
def setup_data(request):
    print("\nSetting up resources...")

    def finalizer():
        root_path =  "../../testing/bevy_example"
        assets_root_path = os.path.join(root_path, "assets")
        models_path =  os.path.join(assets_root_path, "models")
        materials_path = os.path.join(assets_root_path, "materials")
        #other_materials_path = os.path.join("../../testing", "other_materials")

        print("\nPerforming teardown...")
        if os.path.exists(models_path):
            shutil.rmtree(models_path)

        if os.path.exists(materials_path):
            shutil.rmtree(materials_path)

        diagnostics_file_path = os.path.join(root_path, "bevy_diagnostics.json")
        if os.path.exists(diagnostics_file_path):
            os.remove(diagnostics_file_path)
        
        hierarchy_file_path = os.path.join(root_path, "bevy_hierarchy.json")
        if os.path.exists(hierarchy_file_path):
            os.remove(hierarchy_file_path)

        screenshot_observed_path = os.path.join(root_path, "screenshot.png")
        if os.path.exists(screenshot_observed_path):
            os.remove(screenshot_observed_path)

    request.addfinalizer(finalizer)

    return None

def test_export_change_tracking_custom_properties(setup_data):
    root_path = "../../testing/bevy_example"
    assets_root_path = os.path.join(root_path, "assets")
    models_path = os.path.join(assets_root_path, "models")
    auto_export_operator = bpy.ops.export_scenes.auto_gltf

    # with change detection
    # first, configure things
    # we use the global settings for that
    export_props = {
        "main_scene_names" : ['World'],
        "library_scene_names": ['Library'],
    }
  
    # store settings for the auto_export part
    stored_auto_settings = bpy.data.texts[".gltf_auto_export_settings"] if ".gltf_auto_export_settings" in bpy.data.texts else bpy.data.texts.new(".gltf_auto_export_settings")
    stored_auto_settings.clear()
    stored_auto_settings.write(json.dumps(export_props))

    gltf_settings = {
        "export_animations": False,
        "export_optimize_animation_size": False
    }
    # and store settings for the gltf part
    stored_gltf_settings = bpy.data.texts[".gltf_auto_export_gltf_settings"] if ".gltf_auto_export_gltf_settings" in bpy.data.texts else bpy.data.texts.new(".gltf_auto_export_gltf_settings")
    stored_gltf_settings.clear()
    stored_gltf_settings.write(json.dumps(gltf_settings))

    auto_export_operator(
        auto_export=True,
        direct_mode=True,
        export_output_folder="./models",
        export_scene_settings=True,
        export_blueprints=True,
        export_legacy_mode=False,
        export_materials_library=False
    )

    world_file_path = os.path.join(models_path, "World.glb")
    assert os.path.exists(world_file_path) == True

    models_library_path = os.path.join(models_path, "library")
    model_library_file_paths = list(map(lambda file_name: os.path.join(models_library_path, file_name), sorted(os.listdir(models_library_path))))
    modification_times_first = list(map(lambda file_path: os.path.getmtime(file_path), model_library_file_paths + [world_file_path]))

    mapped_files_to_timestamps_and_index = {}
    for (index, file_path) in enumerate(model_library_file_paths+ [world_file_path]):
        file_path = pathlib.Path(file_path).stem
        mapped_files_to_timestamps_and_index[file_path] = (modification_times_first[index], index)

    # now add a custom property to the cube in the main scene & export again
    print("----------------")
    print("main scene change (custom property)")
    print("----------------")

    bpy.data.objects["Cube"]["test_property"] = 42
    
    auto_export_operator(
        auto_export=True,
        direct_mode=True,
        export_output_folder="./models",
        export_scene_settings=True,
        export_blueprints=True,
        export_legacy_mode=False,
        export_materials_library=False
    )

    modification_times = list(map(lambda file_path: os.path.getmtime(file_path), model_library_file_paths + [world_file_path]))
    assert modification_times != modification_times_first
    # only the "world" file should have changed
    world_file_index = mapped_files_to_timestamps_and_index["World"][1]
    other_files_modification_times = [value for index, value in enumerate(modification_times) if index not in [world_file_index]]
    other_files_modification_times_first = [value for index, value in enumerate(modification_times_first) if index not in [world_file_index]]

    assert modification_times[world_file_index] != modification_times_first[world_file_index]
    assert other_files_modification_times == other_files_modification_times_first

def test_export_change_tracking_custom_properties_collection_instances_combine_mode_embed(setup_data):
    root_path = "../../testing/bevy_example"
    assets_root_path = os.path.join(root_path, "assets")
    models_path = os.path.join(assets_root_path, "models")
    auto_export_operator = bpy.ops.export_scenes.auto_gltf

    # with change detection
    # first, configure things
    # we use the global settings for that
    export_props = {
        "main_scene_names" : ['World'],
        "library_scene_names": ['Library'],

        "collection_instances_combine_mode":"Embed"
    }
  
    # store settings for the auto_export part
    stored_auto_settings = bpy.data.texts[".gltf_auto_export_settings"] if ".gltf_auto_export_settings" in bpy.data.texts else bpy.data.texts.new(".gltf_auto_export_settings")
    stored_auto_settings.clear()
    stored_auto_settings.write(json.dumps(export_props))

    gltf_settings = {
        "export_animations": False,
        "export_optimize_animation_size": False
    }
    # and store settings for the gltf part
    stored_gltf_settings = bpy.data.texts[".gltf_auto_export_gltf_settings"] if ".gltf_auto_export_gltf_settings" in bpy.data.texts else bpy.data.texts.new(".gltf_auto_export_gltf_settings")
    stored_gltf_settings.clear()
    stored_gltf_settings.write(json.dumps(gltf_settings))

    auto_export_operator(
        auto_export=True,
        direct_mode=True,
        export_output_folder="./models",
        export_scene_settings=True,
        export_blueprints=True,
        export_legacy_mode=False,
        export_materials_library=False
    )

    world_file_path = os.path.join(models_path, "World.glb")
    assert os.path.exists(world_file_path) == True

    models_library_path = os.path.join(models_path, "library")

    blueprint1_file_path = os.path.join(models_library_path, "Blueprint1.glb")
    assert os.path.exists(blueprint1_file_path) == False


    mapped_files_to_timestamps_and_index = {}
    model_library_file_paths = []
    all_files_paths = []
    if os.path.exists(models_library_path):
        model_library_file_paths = list(map(lambda file_name: os.path.join(models_library_path, file_name), sorted(os.listdir(models_library_path))))
        all_files_paths = model_library_file_paths + [world_file_path]
    else:
        all_files_paths = [world_file_path]

    modification_times_first = list(map(lambda file_path: os.path.getmtime(file_path), all_files_paths))

    for (index, file_path) in enumerate(all_files_paths):
        file_path = pathlib.Path(file_path).stem
        mapped_files_to_timestamps_and_index[file_path] = (modification_times_first[index], index)

    # now add a custom property to the cube in the library scene & export again
    # this should trigger changes in the main scene as well since the mode is embed & this blueprints has an instance in the main scene
    print("----------------")
    print("library change (custom property)")
    print("----------------")

    bpy.data.objects["Blueprint1_mesh"]["test_property"] = 42
    
    auto_export_operator(
        auto_export=True,
        direct_mode=True,
        export_output_folder="./models",
        export_scene_settings=True,
        export_blueprints=True,
        export_legacy_mode=False,
        export_materials_library=False
    )
    
    modification_times = list(map(lambda file_path: os.path.getmtime(file_path), model_library_file_paths + [world_file_path]))
    assert modification_times != modification_times_first

    # there should not be a "Blueprint1" file
    assert os.path.exists(blueprint1_file_path) == False

    # only the "world" file should have changed
    world_file_index = mapped_files_to_timestamps_and_index["World"][1]
    other_files_modification_times = [value for index, value in enumerate(modification_times) if index not in [world_file_index]]
    other_files_modification_times_first = [value for index, value in enumerate(modification_times_first) if index not in [world_file_index]]

    assert modification_times[world_file_index] != modification_times_first[world_file_index]
    assert other_files_modification_times == other_files_modification_times_first

    # reset the comparing 
    modification_times_first = modification_times


    # now we set the _combine mode of the instance to "split", so auto_export should:
    # * not take the changes into account in the main scene
    # * export the blueprint (so file for Blueprint1 will be changed)
    bpy.data.objects["Blueprint1"]["_combine"] = "Split"

    # but first do an export so that the changes to _combine are not taken into account
    auto_export_operator(
        auto_export=True,
        direct_mode=True,
        export_output_folder="./models",
        export_scene_settings=True,
        export_blueprints=True,
        export_legacy_mode=False,
        export_materials_library=False
    )
    modification_times_first = modification_times = list(map(lambda file_path: os.path.getmtime(file_path), model_library_file_paths + [world_file_path]))

    print("----------------")
    print("library change (custom property, forced 'Split' combine mode )")
    print("----------------")

    bpy.data.objects["Blueprint1_mesh"]["test_property"] = 151

    auto_export_operator(
        auto_export=True,
        direct_mode=True,
        export_output_folder="./models",
        export_scene_settings=True,
        export_blueprints=True,
        export_legacy_mode=False,
        export_materials_library=False
    )
    
    modification_times = list(map(lambda file_path: os.path.getmtime(file_path), model_library_file_paths + [world_file_path]))
    assert modification_times != modification_times_first

    # the "world" file should have changed
    world_file_index = mapped_files_to_timestamps_and_index["World"][1]

    # the "Blueprint1" file should now exist
    assert os.path.exists(blueprint1_file_path) == True

    # and the "Blueprint1" file too
    #blueprint1_file_index = mapped_files_to_timestamps_and_index["Blueprint1"][1]

    other_files_modification_times = [value for index, value in enumerate(modification_times) if index not in [world_file_index]]
    other_files_modification_times_first = [value for index, value in enumerate(modification_times_first) if index not in [world_file_index]]

    assert modification_times[world_file_index] != modification_times_first[world_file_index]
    #assert modification_times[blueprint1_file_index] != modification_times_first[blueprint1_file_index]

    assert other_files_modification_times == other_files_modification_times_first



def test_export_change_tracking_light_properties(setup_data):
    root_path = "../../testing/bevy_example"
    assets_root_path = os.path.join(root_path, "assets")
    models_path = os.path.join(assets_root_path, "models")
    auto_export_operator = bpy.ops.export_scenes.auto_gltf

    # with change detection
    # first, configure things
    # we use the global settings for that
    export_props = {
        "main_scene_names" : ['World'],
        "library_scene_names": ['Library'],
    }
  
    # store settings for the auto_export part
    stored_auto_settings = bpy.data.texts[".gltf_auto_export_settings"] if ".gltf_auto_export_settings" in bpy.data.texts else bpy.data.texts.new(".gltf_auto_export_settings")
    stored_auto_settings.clear()
    stored_auto_settings.write(json.dumps(export_props))

    gltf_settings = {
        "export_animations": False,
        "export_optimize_animation_size": False
    }
    # and store settings for the gltf part
    stored_gltf_settings = bpy.data.texts[".gltf_auto_export_gltf_settings"] if ".gltf_auto_export_gltf_settings" in bpy.data.texts else bpy.data.texts.new(".gltf_auto_export_gltf_settings")
    stored_gltf_settings.clear()
    stored_gltf_settings.write(json.dumps(gltf_settings))

    auto_export_operator(
        auto_export=True,
        direct_mode=True,
        export_output_folder="./models",
        export_scene_settings=True,
        export_blueprints=True,
        export_legacy_mode=False,
        export_materials_library=False
    )

    world_file_path = os.path.join(models_path, "World.glb")
    assert os.path.exists(world_file_path) == True

    models_library_path = os.path.join(models_path, "library")
    model_library_file_paths = list(map(lambda file_name: os.path.join(models_library_path, file_name), sorted(os.listdir(models_library_path))))
    modification_times_first = list(map(lambda file_path: os.path.getmtime(file_path), model_library_file_paths + [world_file_path]))

    mapped_files_to_timestamps_and_index = {}
    for (index, file_path) in enumerate(model_library_file_paths+ [world_file_path]):
        file_path = pathlib.Path(file_path).stem
        mapped_files_to_timestamps_and_index[file_path] = (modification_times_first[index], index)

    print("----------------")
    print("main scene change (light, energy)")
    print("----------------")

    bpy.data.lights["Light"].energy = 100
    
    auto_export_operator(
        auto_export=True,
        direct_mode=True,
        export_output_folder="./models",
        export_scene_settings=True,
        export_blueprints=True,
        export_legacy_mode=False,
        export_materials_library=False
    )

    modification_times = list(map(lambda file_path: os.path.getmtime(file_path), model_library_file_paths + [world_file_path]))
    assert modification_times != modification_times_first
    # only the "world" file should have changed
    world_file_index = mapped_files_to_timestamps_and_index["World"][1]
    other_files_modification_times = [value for index, value in enumerate(modification_times) if index not in [world_file_index]]
    other_files_modification_times_first = [value for index, value in enumerate(modification_times_first) if index not in [world_file_index]]

    assert modification_times[world_file_index] != modification_times_first[world_file_index]
    assert other_files_modification_times == other_files_modification_times_first

    # reset the comparing 
    modification_times_first = modification_times

    print("----------------")
    print("main scene change (light, shadow_cascade_count)")
    print("----------------")

    bpy.data.lights["Light"].shadow_cascade_count = 2
    
    auto_export_operator(
        auto_export=True,
        direct_mode=True,
        export_output_folder="./models",
        export_scene_settings=True,
        export_blueprints=True,
        export_legacy_mode=False,
        export_materials_library=False
    )

    modification_times = list(map(lambda file_path: os.path.getmtime(file_path), model_library_file_paths + [world_file_path]))
    assert modification_times != modification_times_first
    # only the "world" file should have changed
    world_file_index = mapped_files_to_timestamps_and_index["World"][1]
    other_files_modification_times = [value for index, value in enumerate(modification_times) if index not in [world_file_index]]
    other_files_modification_times_first = [value for index, value in enumerate(modification_times_first) if index not in [world_file_index]]

    assert modification_times[world_file_index] != modification_times_first[world_file_index]
    assert other_files_modification_times == other_files_modification_times_first

    # reset the comparing 
    modification_times_first = modification_times

    print("----------------")
    print("main scene change (light, use_shadow)")
    print("----------------")

    bpy.data.lights["Light"].use_shadow = False
    
    auto_export_operator(
        auto_export=True,
        direct_mode=True,
        export_output_folder="./models",
        export_scene_settings=True,
        export_blueprints=True,
        export_legacy_mode=False,
        export_materials_library=False
    )

    modification_times = list(map(lambda file_path: os.path.getmtime(file_path), model_library_file_paths + [world_file_path]))
    assert modification_times != modification_times_first
    # only the "world" file should have changed
    world_file_index = mapped_files_to_timestamps_and_index["World"][1]
    other_files_modification_times = [value for index, value in enumerate(modification_times) if index not in [world_file_index]]
    other_files_modification_times_first = [value for index, value in enumerate(modification_times_first) if index not in [world_file_index]]

    assert modification_times[world_file_index] != modification_times_first[world_file_index]
    assert other_files_modification_times == other_files_modification_times_first


def test_export_change_tracking_camera_properties(setup_data):
    root_path = "../../testing/bevy_example"
    assets_root_path = os.path.join(root_path, "assets")
    models_path = os.path.join(assets_root_path, "models")
    auto_export_operator = bpy.ops.export_scenes.auto_gltf

    # with change detection
    # first, configure things
    # we use the global settings for that
    export_props = {
        "main_scene_names" : ['World'],
        "library_scene_names": ['Library'],
    }
  
    # store settings for the auto_export part
    stored_auto_settings = bpy.data.texts[".gltf_auto_export_settings"] if ".gltf_auto_export_settings" in bpy.data.texts else bpy.data.texts.new(".gltf_auto_export_settings")
    stored_auto_settings.clear()
    stored_auto_settings.write(json.dumps(export_props))

    gltf_settings = {
        "export_animations": False,
        "export_optimize_animation_size": False
    }
    # and store settings for the gltf part
    stored_gltf_settings = bpy.data.texts[".gltf_auto_export_gltf_settings"] if ".gltf_auto_export_gltf_settings" in bpy.data.texts else bpy.data.texts.new(".gltf_auto_export_gltf_settings")
    stored_gltf_settings.clear()
    stored_gltf_settings.write(json.dumps(gltf_settings))

    auto_export_operator(
        auto_export=True,
        direct_mode=True,
        export_output_folder="./models",
        export_scene_settings=True,
        export_blueprints=True,
        export_legacy_mode=False,
        export_materials_library=False
    )

    world_file_path = os.path.join(models_path, "World.glb")
    assert os.path.exists(world_file_path) == True

    models_library_path = os.path.join(models_path, "library")
    model_library_file_paths = list(map(lambda file_name: os.path.join(models_library_path, file_name), sorted(os.listdir(models_library_path))))
    modification_times_first = list(map(lambda file_path: os.path.getmtime(file_path), model_library_file_paths + [world_file_path]))

    mapped_files_to_timestamps_and_index = {}
    for (index, file_path) in enumerate(model_library_file_paths+ [world_file_path]):
        file_path = pathlib.Path(file_path).stem
        mapped_files_to_timestamps_and_index[file_path] = (modification_times_first[index], index)

    print("----------------")
    print("main scene change (camera)")
    print("----------------")

    bpy.data.cameras["Camera"].angle = 0.5
    
    auto_export_operator(
        auto_export=True,
        direct_mode=True,
        export_output_folder="./models",
        export_scene_settings=True,
        export_blueprints=True,
        export_legacy_mode=False,
        export_materials_library=False
    )

    modification_times = list(map(lambda file_path: os.path.getmtime(file_path), model_library_file_paths + [world_file_path]))
    assert modification_times != modification_times_first
    # only the "world" file should have changed
    world_file_index = mapped_files_to_timestamps_and_index["World"][1]
    other_files_modification_times = [value for index, value in enumerate(modification_times) if index not in [world_file_index]]
    other_files_modification_times_first = [value for index, value in enumerate(modification_times_first) if index not in [world_file_index]]

    assert modification_times[world_file_index] != modification_times_first[world_file_index]
    assert other_files_modification_times == other_files_modification_times_first


def test_export_change_tracking_material_properties(setup_data):
    root_path = "../../testing/bevy_example"
    assets_root_path = os.path.join(root_path, "assets")
    models_path = os.path.join(assets_root_path, "models")
    auto_export_operator = bpy.ops.export_scenes.auto_gltf

    # with change detection
    # first, configure things
    # we use the global settings for that
    export_props = {
        "main_scene_names" : ['World'],
        "library_scene_names": ['Library'],
    }
  
    # store settings for the auto_export part
    stored_auto_settings = bpy.data.texts[".gltf_auto_export_settings"] if ".gltf_auto_export_settings" in bpy.data.texts else bpy.data.texts.new(".gltf_auto_export_settings")
    stored_auto_settings.clear()
    stored_auto_settings.write(json.dumps(export_props))

    gltf_settings = {
        "export_animations": False,
        "export_optimize_animation_size": False
    }
    # and store settings for the gltf part
    stored_gltf_settings = bpy.data.texts[".gltf_auto_export_gltf_settings"] if ".gltf_auto_export_gltf_settings" in bpy.data.texts else bpy.data.texts.new(".gltf_auto_export_gltf_settings")
    stored_gltf_settings.clear()
    stored_gltf_settings.write(json.dumps(gltf_settings))

    auto_export_operator(
        auto_export=True,
        direct_mode=True,
        export_output_folder="./models",
        export_scene_settings=True,
        export_blueprints=True,
        export_legacy_mode=False,
        export_materials_library=False
    )

    world_file_path = os.path.join(models_path, "World.glb")
    assert os.path.exists(world_file_path) == True

    models_library_path = os.path.join(models_path, "library")
    model_library_file_paths = list(map(lambda file_name: os.path.join(models_library_path, file_name), sorted(os.listdir(models_library_path))))
    modification_times_first = list(map(lambda file_path: os.path.getmtime(file_path), model_library_file_paths + [world_file_path]))

    mapped_files_to_timestamps_and_index = {}
    for (index, file_path) in enumerate(model_library_file_paths+ [world_file_path]):
        file_path = pathlib.Path(file_path).stem
        mapped_files_to_timestamps_and_index[file_path] = (modification_times_first[index], index)

    print("----------------")
    print("main scene change (material, clip)")
    print("----------------")

    bpy.data.materials["Material.001"].blend_method = 'CLIP'

    auto_export_operator(
        auto_export=True,
        direct_mode=True,
        export_output_folder="./models",
        export_scene_settings=True,
        export_blueprints=True,
        export_legacy_mode=False,
        export_materials_library=False
    )

    modification_times = list(map(lambda file_path: os.path.getmtime(file_path), model_library_file_paths + [world_file_path]))
    assert modification_times != modification_times_first
    # the material is assigned to Blueprint 1 so in normal (split mode) only the "Blueprint1" file should have changed
    blueprint1_file_index = mapped_files_to_timestamps_and_index["Blueprint1"][1]
    # the same material is assigned to Blueprint 7 so in normal (split mode) only the "Blueprint1" file should have changed
    blueprint7_file_index = mapped_files_to_timestamps_and_index["Blueprint7_hierarchy"][1]

    other_files_modification_times = [value for index, value in enumerate(modification_times) if index not in [blueprint1_file_index, blueprint7_file_index]]
    other_files_modification_times_first = [value for index, value in enumerate(modification_times_first) if index not in [blueprint1_file_index, blueprint7_file_index]]

    assert modification_times[blueprint1_file_index] != modification_times_first[blueprint1_file_index]
    assert modification_times[blueprint7_file_index] != modification_times_first[blueprint7_file_index]

    assert other_files_modification_times == other_files_modification_times_first

    # reset the comparing 
    modification_times_first = modification_times

    print("----------------")
    print("main scene change (material, alpha_threshold)")
    print("----------------")
    bpy.data.materials["Material.001"].alpha_threshold = 0.2

    auto_export_operator(
        auto_export=True,
        direct_mode=True,
        export_output_folder="./models",
        export_scene_settings=True,
        export_blueprints=True,
        export_legacy_mode=False,
        export_materials_library=False
    )

    modification_times = list(map(lambda file_path: os.path.getmtime(file_path), model_library_file_paths + [world_file_path]))
    assert modification_times != modification_times_first
    # the material is assigned to Blueprint 1 so in normal (split mode) only the "Blueprint1" file should have changed
    blueprint1_file_index = mapped_files_to_timestamps_and_index["Blueprint1"][1]
    # the same material is assigned to Blueprint 7 so in normal (split mode) only the "Blueprint1" file should have changed
    blueprint7_file_index = mapped_files_to_timestamps_and_index["Blueprint7_hierarchy"][1]

    other_files_modification_times = [value for index, value in enumerate(modification_times) if index not in [blueprint1_file_index, blueprint7_file_index]]
    other_files_modification_times_first = [value for index, value in enumerate(modification_times_first) if index not in [blueprint1_file_index, blueprint7_file_index]]

    assert modification_times[blueprint1_file_index] != modification_times_first[blueprint1_file_index]
    assert modification_times[blueprint7_file_index] != modification_times_first[blueprint7_file_index]
    assert other_files_modification_times == other_files_modification_times_first


     # reset the comparing 
    modification_times_first = modification_times

    print("----------------")
    print("main scene change (material, diffuse_color)")
    print("----------------")
    bpy.data.materials["Material.001"].diffuse_color[0] = 0.2

    auto_export_operator(
        auto_export=True,
        direct_mode=True,
        export_output_folder="./models",
        export_scene_settings=True,
        export_blueprints=True,
        export_legacy_mode=False,
        export_materials_library=False
    )

    modification_times = list(map(lambda file_path: os.path.getmtime(file_path), model_library_file_paths + [world_file_path]))
    assert modification_times != modification_times_first
    # the material is assigned to Blueprint 1 so in normal (split mode) only the "Blueprint1" file should have changed
    blueprint1_file_index = mapped_files_to_timestamps_and_index["Blueprint1"][1]
    # the same material is assigned to Blueprint 7 so in normal (split mode) only the "Blueprint1" file should have changed
    blueprint7_file_index = mapped_files_to_timestamps_and_index["Blueprint7_hierarchy"][1]

    other_files_modification_times = [value for index, value in enumerate(modification_times) if index not in [blueprint1_file_index, blueprint7_file_index]]
    other_files_modification_times_first = [value for index, value in enumerate(modification_times_first) if index not in [blueprint1_file_index, blueprint7_file_index]]

    assert modification_times[blueprint1_file_index] != modification_times_first[blueprint1_file_index]
    assert modification_times[blueprint7_file_index] != modification_times_first[blueprint7_file_index]
    assert other_files_modification_times == other_files_modification_times_first


"""
- setup gltf parameters & auto_export parameters
- calls exporter on the testing scene
- saves timestamps of generated files
- changes things in the main scene and/or library
- checks if timestamps have changed
- if all worked => test is a-ok
- removes generated files

"""
def test_export_various_chained_changes(setup_data):
    root_path = "../../testing/bevy_example"
    assets_root_path = os.path.join(root_path, "assets")
    models_path = os.path.join(assets_root_path, "models")
    auto_export_operator = bpy.ops.export_scenes.auto_gltf

    # with change detection
    # first, configure things
    # we use the global settings for that
    export_props = {
        "main_scene_names" : ['World'],
        "library_scene_names": ['Library'],
    }
  
    # store settings for the auto_export part
    stored_auto_settings = bpy.data.texts[".gltf_auto_export_settings"] if ".gltf_auto_export_settings" in bpy.data.texts else bpy.data.texts.new(".gltf_auto_export_settings")
    stored_auto_settings.clear()
    stored_auto_settings.write(json.dumps(export_props))

    gltf_settings = {
        "export_animations": False,
        "export_optimize_animation_size": False
    }
    # and store settings for the gltf part
    stored_gltf_settings = bpy.data.texts[".gltf_auto_export_gltf_settings"] if ".gltf_auto_export_gltf_settings" in bpy.data.texts else bpy.data.texts.new(".gltf_auto_export_gltf_settings")
    stored_gltf_settings.clear()
    stored_gltf_settings.write(json.dumps(gltf_settings))

    auto_export_operator(
        auto_export=True,
        direct_mode=True,
        export_output_folder="./models",
        export_scene_settings=True,
        export_blueprints=True,
        export_legacy_mode=False,
        export_materials_library=False
    )

    world_file_path = os.path.join(models_path, "World.glb")
    assert os.path.exists(world_file_path) == True

    models_library_path = os.path.join(models_path, "library")
    model_library_file_paths = list(map(lambda file_name: os.path.join(models_library_path, file_name), sorted(os.listdir(models_library_path))))
    modification_times_first = list(map(lambda file_path: os.path.getmtime(file_path), model_library_file_paths + [world_file_path]))

    mapped_files_to_timestamps_and_index = {}
    for (index, file_path) in enumerate(model_library_file_paths+ [world_file_path]):
        file_path = pathlib.Path(file_path).stem
        mapped_files_to_timestamps_and_index[file_path] = (modification_times_first[index], index)
    print("files", mapped_files_to_timestamps_and_index)
    #print("mod times", modification_times_first)

    # export again with no changes
    print("----------------")
    print("no changes")
    print("----------------")
    bpy.context.window_manager.auto_export_tracker.enable_change_detection() # FIXME: should not be needed, but ..

    auto_export_operator(
        auto_export=True,
        direct_mode=True,
        export_output_folder="./models",
        export_scene_settings=True,
        export_blueprints=True,
        export_legacy_mode=False,
        export_materials_library=False
    )

    modification_times_no_change = list(map(lambda file_path: os.path.getmtime(file_path), model_library_file_paths + [world_file_path]))
    assert modification_times_no_change == modification_times_first

    # now move the main cube & export again
    print("----------------")
    print("main scene change")
    print("----------------")

    bpy.context.window_manager.auto_export_tracker.enable_change_detection() # FIXME: should not be needed, but ..
    bpy.data.objects["Cube"].location = [1, 0, 0]
    
    auto_export_operator(
        auto_export=True,
        direct_mode=True,
        export_output_folder="./models",
        export_scene_settings=True,
        export_blueprints=True,
        export_legacy_mode=False,
        export_materials_library=False
    )

    modification_times = list(map(lambda file_path: os.path.getmtime(file_path), model_library_file_paths + [world_file_path]))
    assert modification_times != modification_times_first
    # only the "world" file should have changed
    world_file_index = mapped_files_to_timestamps_and_index["World"][1]
    other_files_modification_times = [value for index, value in enumerate(modification_times) if index not in [world_file_index]]
    other_files_modification_times_first = [value for index, value in enumerate(modification_times_first) if index not in [world_file_index]]

    assert modification_times[world_file_index] != modification_times_first[world_file_index]
    assert other_files_modification_times == other_files_modification_times_first
    # reset the comparing 
    modification_times_first = modification_times


    # now same, but move the cube in the library
    print("----------------")
    print("library change (blueprint) ")
    print("----------------")
    bpy.context.window_manager.auto_export_tracker.enable_change_detection() # FIXME: should not be needed, but ..

    bpy.data.objects["Blueprint1_mesh"].location = [1, 2, 1]

    auto_export_operator(
        auto_export=True,
        direct_mode=True,
        export_output_folder="./models",
        export_scene_settings=True,
        export_blueprints=True,
        export_legacy_mode=False,
        export_materials_library=False
    )

    modification_times = list(map(lambda file_path: os.path.getmtime(file_path), model_library_file_paths + [world_file_path]))
    assert modification_times != modification_times_first
    # the "world" file should have changed (TODO: double check: this is since changing an instances collection changes the instance too ?)
    world_file_index = mapped_files_to_timestamps_and_index["World"][1]
    # and the blueprint1 file too, since that is the collection we changed
    blueprint1_file_index = mapped_files_to_timestamps_and_index["Blueprint1"][1]
    other_files_modification_times = [value for index, value in enumerate(modification_times) if index not in [world_file_index, blueprint1_file_index]]
    other_files_modification_times_first = [value for index, value in enumerate(modification_times_first) if index not in [world_file_index, blueprint1_file_index]]

    assert modification_times[world_file_index] == modification_times_first[world_file_index]
    assert modification_times[blueprint1_file_index] != modification_times_first[blueprint1_file_index]
    assert other_files_modification_times == other_files_modification_times_first
    # reset the comparing 
    modification_times_first = modification_times


    # now change something in a nested blueprint
    print("----------------")
    print("library change (nested blueprint) ")
    print("----------------")

    bpy.data.objects["Blueprint3_mesh"].location= [0, 0.1 ,2]

    auto_export_operator(
        auto_export=True,
        direct_mode=True,
        export_output_folder="./models",
        export_scene_settings=True,
        export_blueprints=True,
        export_legacy_mode=False,
        export_materials_library=False
    )

    modification_times = list(map(lambda file_path: os.path.getmtime(file_path), model_library_file_paths + [world_file_path]))
    assert modification_times != modification_times_first
    # the "world" file should not have changed
    world_file_index = mapped_files_to_timestamps_and_index["World"][1]
    #  the blueprint3 file should have changed, since that is the collection we changed
    blueprint3_file_index = mapped_files_to_timestamps_and_index["Blueprint3"][1]
    # the blueprint4 file NOT, since, while it contains an instance of the collection we changed, the default export mode is "split"
    blueprint4_file_index = mapped_files_to_timestamps_and_index["Blueprint4_nested"][1]

    other_files_modification_times = [value for index, value in enumerate(modification_times) if index not in [world_file_index, blueprint3_file_index, blueprint4_file_index]]
    other_files_modification_times_first = [value for index, value in enumerate(modification_times_first) if index not in [world_file_index, blueprint3_file_index, blueprint4_file_index]]

    assert modification_times[world_file_index] == modification_times_first[world_file_index]
    assert modification_times[blueprint3_file_index] != modification_times_first[blueprint3_file_index]
    assert modification_times[blueprint4_file_index] == modification_times_first[blueprint4_file_index]
    assert other_files_modification_times == other_files_modification_times_first

    # reset the comparing 
    modification_times_first = modification_times

    # now same, but using an operator
    print("----------------")
    print("change using operator")
    print("----------------")

    with bpy.context.temp_override(active_object=bpy.data.objects["Cube"], selected_objects=[bpy.data.objects["Cube"]], scene=bpy.data.scenes["World"]):
        print("translate using operator")
        bpy.ops.transform.translate(value=mathutils.Vector((2.0, 1.0, -5.0)))
        bpy.ops.transform.rotate(value=0.378874, constraint_axis=(False, False, True), mirror=False, proportional_edit_falloff='SMOOTH', proportional_size=1)
        bpy.ops.object.transform_apply()
        bpy.ops.transform.translate(value=(3.5, 0, 0), constraint_axis=(True, False, False))

    auto_export_operator(
        auto_export=True,
        direct_mode=True,
        export_output_folder="./models",
        export_scene_settings=True,
        export_blueprints=True,
        export_legacy_mode=False,
        export_materials_library=False
    )

    modification_times = list(map(lambda file_path: os.path.getmtime(file_path), model_library_file_paths + [world_file_path]))
    assert modification_times != modification_times_first
    modification_times_first = modification_times

    


   