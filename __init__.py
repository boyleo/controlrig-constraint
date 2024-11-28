bl_info = {
    "name": "Control Rig Constraints",
    "blender": (3, 0, 0),
    "category": "Object",
    "description": "Adds Child Of and Copy Location constraints to each bone pair.",
    "author": "Your Name",
    "version": (1, 0),
    "location": "3D View > Tool",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
}

import bpy
import json
from bpy_extras.io_utils import ExportHelper, ImportHelper

class BoneConstraintOperator(bpy.types.Operator):
    bl_idname = "object.bone_constraint_operator"
    bl_label = "Add Bone Constraints"

    def execute(self, context):
        control_rig = bpy.data.objects.get(context.scene.control_rig_name)
        deform_rig = bpy.data.objects.get(context.scene.deform_rig_name)

        if not control_rig or not deform_rig:
            self.report({'ERROR'}, "Invalid rig names")
            return {'CANCELLED'}

        for bone_pair in context.scene.bone_pairs:
            source_bone = control_rig.pose.bones.get(bone_pair.source_bone)
            target_bone = deform_rig.pose.bones.get(bone_pair.target_bone)

            if not source_bone or not target_bone:
                self.report({'ERROR'}, "Invalid bone names")
                return {'CANCELLED'}

            # Delete existing constraints on the target bone
            for constraint in target_bone.constraints:
                target_bone.constraints.remove(constraint)

            # Create "Child Of" constraint
            child_of_constraint = target_bone.constraints.new('CHILD_OF')
            child_of_constraint.target = control_rig
            child_of_constraint.subtarget = source_bone.name

            # Set the inverse matrix for the "Child Of" constraint
            bpy.context.view_layer.objects.active = deform_rig
            bpy.context.object.data.bones.active = target_bone.bone
            bpy.ops.constraint.childof_set_inverse(constraint=child_of_constraint.name, owner='BONE')

            # Create "Copy Location" constraint
            copy_location_constraint = target_bone.constraints.new('COPY_LOCATION')
            copy_location_constraint.target = control_rig
            copy_location_constraint.subtarget = source_bone.name
            copy_location_constraint.use_x = True
            copy_location_constraint.use_y = True
            copy_location_constraint.use_z = True
            copy_location_constraint.use_offset = False
            copy_location_constraint.target_space = 'WORLD'
            copy_location_constraint.owner_space = 'WORLD'

            # Set head/tail value for Copy Location constraint
            copy_location_constraint.head_tail = bone_pair.head_tail

            # Disable "Inherit Rotation" on the target bone
            target_bone.bone.use_inherit_rotation = False

        return {'FINISHED'}

class BonePairProperty(bpy.types.PropertyGroup):
    source_bone: bpy.props.StringProperty(name="Source Bone")
    target_bone: bpy.props.StringProperty(name="Target Bone")
    head_tail: bpy.props.FloatProperty(name="Head/Tail", default=0.0, min=0.0, max=1.0)

class ControlRigConstraintsPanel(bpy.types.Panel):
    bl_label = "Control Rig Constraints"
    bl_idname = "OBJECT_PT_control_rig_constraints"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tool'

    def draw(self, context):
        layout = self.layout
        layout.label(text="This will add Child Of and Copy Location constraints to each bone pair.")
        layout.prop_search(context.scene, "control_rig_name", bpy.data, "objects", text="Control Rig")
        layout.prop_search(context.scene, "deform_rig_name", bpy.data, "objects", text="Deform Rig")

        row = layout.row()
        row.template_list("UI_UL_list", "bone_pairs", context.scene, "bone_pairs", context.scene, "bone_pairs_index", rows=3, type='DEFAULT')
        col = row.column(align=True)
        col.operator("object.add_bone_pair_operator", icon='ADD', text="")
        col.operator("object.remove_bone_pair_operator", icon='REMOVE', text="")

        if context.scene.bone_pairs:
            bone_pair = context.scene.bone_pairs[context.scene.bone_pairs_index]
            layout.prop_search(bone_pair, "source_bone", bpy.data.objects[context.scene.control_rig_name].pose, "bones", text="Source Bone")
            layout.prop_search(bone_pair, "target_bone", bpy.data.objects[context.scene.deform_rig_name].pose, "bones", text="Target Bone")
            layout.prop(bone_pair, "head_tail", text="Head/Tail")

        layout.operator("object.save_bone_pairs_operator", text="Save Bone Pairs")
        layout.operator("object.load_bone_pairs_operator", text="Load Bone Pairs")
        layout.operator("object.bone_constraint_operator")

class AddBonePairOperator(bpy.types.Operator):
    bl_idname = "object.add_bone_pair_operator"
    bl_label = "Add Bone Pair"

    def execute(self, context):
        bone_pair = context.scene.bone_pairs.add()
        bone_pair.source_bone = ""
        bone_pair.target_bone = ""
        bone_pair.head_tail = 0.0
        context.scene.bone_pairs_index = len(context.scene.bone_pairs) - 1
        return {'FINISHED'}

class RemoveBonePairOperator(bpy.types.Operator):
    bl_idname = "object.remove_bone_pair_operator"
    bl_label = "Remove Bone Pair"

    def execute(self, context):
        if context.scene.bone_pairs:
            context.scene.bone_pairs.remove(context.scene.bone_pairs_index)
            context.scene.bone_pairs_index = max(0, context.scene.bone_pairs_index - 1)
        return {'FINISHED'}

class SaveBonePairsOperator(bpy.types.Operator, ExportHelper):
    bl_idname = "object.save_bone_pairs_operator"
    bl_label = "Save Bone Pairs"

    filename_ext = ".json"
    filter_glob: bpy.props.StringProperty(default="*.json", options={'HIDDEN'})

    def execute(self, context):
        bone_pairs = []
        for bone_pair in context.scene.bone_pairs:
            bone_pairs.append({
                "source_bone": bone_pair.source_bone,
                "target_bone": bone_pair.target_bone,
                "head_tail": bone_pair.head_tail
            })

        with open(self.filepath, 'w') as file:
            json.dump({"bone_pairs": bone_pairs}, file, indent=4)

        return {'FINISHED'}

class LoadBonePairsOperator(bpy.types.Operator, ImportHelper):
    bl_idname = "object.load_bone_pairs_operator"
    bl_label = "Load Bone Pairs"

    filter_glob: bpy.props.StringProperty(default="*.json", options={'HIDDEN'})

    def execute(self, context):
        with open(self.filepath, 'r') as file:
            data = json.load(file)
            bone_pairs = data.get("bone_pairs", [])

        context.scene.bone_pairs.clear()
        for bone_pair in bone_pairs:
            new_bone_pair = context.scene.bone_pairs.add()
            new_bone_pair.source_bone = bone_pair["source_bone"]
            new_bone_pair.target_bone = bone_pair["target_bone"]
            new_bone_pair.head_tail = bone_pair.get("head_tail", 0.0)

        return {'FINISHED'}

def register():
    bpy.utils.register_class(BoneConstraintOperator)
    bpy.utils.register_class(BonePairProperty)
    bpy.utils.register_class(ControlRigConstraintsPanel)
    bpy.utils.register_class(AddBonePairOperator)
    bpy.utils.register_class(RemoveBonePairOperator)
    bpy.utils.register_class(SaveBonePairsOperator)
    bpy.utils.register_class(LoadBonePairsOperator)
    bpy.types.Scene.control_rig_name = bpy.props.StringProperty(name="Control Rig")
    bpy.types.Scene.deform_rig_name = bpy.props.StringProperty(name="Deform Rig")
    bpy.types.Scene.bone_pairs = bpy.props.CollectionProperty(type=BonePairProperty)
    bpy.types.Scene.bone_pairs_index = bpy.props.IntProperty(name="Bone Pairs Index", default=0)

def unregister():
    bpy.utils.unregister_class(BoneConstraintOperator)
    bpy.utils.unregister_class(BonePairProperty)
    bpy.utils.unregister_class(ControlRigConstraintsPanel)
    bpy.utils.unregister_class(AddBonePairOperator)
    bpy.utils.unregister_class(RemoveBonePairOperator)
    bpy.utils.unregister_class(SaveBonePairsOperator)
    bpy.utils.unregister_class(LoadBonePairsOperator)
    del bpy.types.Scene.control_rig_name
    del bpy.types.Scene.deform_rig_name
    del bpy.types.Scene.bone_pairs
    del bpy.types.Scene.bone_pairs_index

if __name__ == "__main__":
    register()