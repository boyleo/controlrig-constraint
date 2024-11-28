# Description
UE5 Mannequin bone has different orientation than Blender, so it's difficult to animate.
This addon helps constraint a UE5 mannequin rig to Blender's Rigify control rig
by adding 'Child of' and 'Copy Location' constraint to corresponding bones.

With this, the resulting animation will be compatible with standard UE5 mannequin without the need to retarget.

# Usage
1. Install and enable addon. It will be in Tool tab.
2. Specify the Rigify control rig and UE5 mannequin rig
3. Load bone pairs from json file.
4. Add Bone Constraint.
