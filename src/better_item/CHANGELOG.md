# Better Item — changelog

## 1.6.2

### Changed
- Add category icons to Orientation and Location labels, with an indented branch for their required Object, Frame or custom-orientation Name.
- Use the same reference hierarchy in Transform, Align and Distribute and the Frame editor; keep child-label icons absent and selector icons native.
- Preserve reference data, transform calculations and the stable installer filename.

## 1.6.1

### Fixed
- Classify arrangement input failures with existing specific support codes; retain the common BI-V001 fallback.
- Document self-following Normal/Gimbal Rotation, Object/Gimbal basis differences and signed distribution ordering with examples.

### Changed
- Remove an unused import and move historical validation narratives out of this changelog into repository documentation.
- Keep the stable `addons/better_item.zip` installer filename. Transform mathematics and panel layout are unchanged.

## 1.6.0

### Added
- Geometry Bounds distribution with signed Spacing and zero-gap packing.
- Match Reference and per-component Set Rotation for the selection.
- Collapsed Solver Settings and separate pending-input, warning and failure diagnostics.

## 1.5.7

### Fixed
- Improve numeric readback, zero-dimension guards, parent diagnostics and transactional affine-stage validation.
- Reject edits whose moving reference prevents the requested absolute relative readout (BI-T009).

Earlier delivery notes and test narratives: [documentation history](https://github.com/Borbofruto/Blender-Plugins/blob/main/docs/better_item/delivery-history-through-1.6.0.md).
