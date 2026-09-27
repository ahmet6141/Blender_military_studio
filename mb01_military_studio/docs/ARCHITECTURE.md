# MB01 implementation map

`core.py`: standard-library geometry, parameter validation and typed ports. Reuses the unchanged AS07 primitive implementation. Source design space X/across Y/depth is converted to public +X/inward +Y/left +Z/up once. Runtime bpy is not imported by core.

`materials.py`: immutable semantic recipes and packaged/optional complete PBR families. Blender material IDs use recipe hashes. Existing user shaders are not globally rewritten.

`blender_backend.py`: staging collections, owned roots, mesh/UV/tint construction, preview door poses, preservation of locked objects and user descendants. Partial-commit failure leaves data for diagnosis rather than deleting reparented user data.

`ui.py`: legacy Blender add-on operators, panels and typed settings. No postponed annotation stringification on PropertyGroups. Modal stepping happens only on Blender's main thread. Initial pure calculation is not preempted by Esc.

`exporter.py`: evaluated triangulated mesh copies, local pivots, one render asset per FBX, convex door UCX hulls, static complex architecture, separate placements/materials. Hash checks and failure marker. Blender source meshes are not destructively triangulated/applied.

`coordinates.py`: measured import basis and affine conversion; rejects zero/mirrored/sheared transforms. Scale centimetres applies to translation only because FBX mesh units are independently calibrated.

`unreal/MB01_Import.py`: editor-only import, material recipes, unit/pivot probes and actors. Dry-run default. User-owned assets are not overwritten. Whole-project re-placement is opt-in, not incremental merge. Exported connection ports remain JSON metadata; socket/graph construction not implemented.

`tests/test_core.py`: portable regression suite; geometry, parameter errors, coordinate transforms, maps, syntax, source identity and render-envelope checks. Does not mock bpy to claim native execution.

`tools/BLENDER_SMOKE.py`: native user-run background Blender test (not executed in development).

`tools/preview.py`: explicit-triangle GLB writer and legacy VTK visual fallback. `ray_preview.py` plus `render_inspection.py`: final independent inspection views. Font outlines in these previews come from VTK vector text; fonts are not packaged. They may differ from native Blender labels.

Asset routes are independent. AF01/SW01/PK01 code/objects are never deleted or silently upgraded. Configuration/coordinate matching is required for scene assembly.
