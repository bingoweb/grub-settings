# Palette's Journal

## 2024-05-22 - Password Dialog Focus
**Learning:** Custom GTK windows do not auto-focus input fields unless explicitly set, leading to user friction (click-to-type).
**Action:** Always set `self.set_focus(widget)` in `__init__` for custom dialogs containing inputs.

## 2024-05-22 - Modal Dialog Keyboard Shortcuts
**Learning:** Custom `Gtk.Window` used as dialog does not handle `Escape` key to close by default.
**Action:** Add `Gtk.EventControllerKey` to handle `Escape` key for custom dialogs to match platform expectations.

## 2026-01-16 - Password Visibility
**Learning:** `Gtk.PasswordEntry` defaults to hidden peek icon, reducing usability and accessibility.
**Action:** Always enable `show-peek-icon` for password fields to allow user verification.

## 2026-01-16 - Async Button Feedback
**Learning:** Blocking subprocess calls freeze the UI without feedback. `Gtk.Button` can temporarily host a `Gtk.Spinner` via `set_child()` to provide inline loading feedback.
**Action:** For all async button actions, disable button, replace child with spinner, and restore state upon completion.

## 2026-01-20 - Dialog Keyboard Navigation
**Learning:** `Adw.MessageDialog` does not automatically map Enter to default or Escape to close unless explicitly configured, breaking expected keyboard workflows.
**Action:** Always set `set_default_response()` and `set_close_response()` when creating message dialogs.

## 2024-10-24 - Accessibility Property Compatibility
**Learning:** `update_property([Gtk.AccessibleProperty.LABEL], ...)` is the correct way to set accessible labels in GTK4 but may fail on older PyGObject versions or specific environments.
**Action:** Wrap `update_property` calls in `try-except AttributeError` blocks to ensure backward compatibility and prevent crashes.

## 2026-01-20 - Subprocess UI Responsiveness
**Learning:** Polling subprocess output with `GLib.timeout_add` + `readline()` causes UI freezes/jank if the pipe blocks or buffers.
**Action:** Use a background thread to iterate over `process.stdout` and push updates via `GLib.idle_add` for smooth, responsive terminal dialogs.
## 2026-01-22 - Dependent Settings Validation
**Learning:** Users can misconfigure dependent settings (e.g., Visibility=Hidden + Timeout=0) leading to lockout states.
**Action:** Add real-time validation for dependent settings and display an `Adw.ActionRow` with `.warning` class to guide correction.
## 2026-01-24 - Actionable Empty States
**Learning:** Static empty states are missed opportunities; users expect large placeholders to be actionable (e.g. click to add).
**Action:** Wrap empty state content in a flat `Gtk.Button` that triggers the primary "Add" action to improve discoverability.
## 2026-01-24 - Interactive Empty States
**Learning:** Static empty state boxes miss a chance for direct interaction. Making the entire empty state area a clickable `Gtk.Button` (with `.flat` style) significantly improves discoverability and reduces friction.
**Action:** Replace static `Gtk.Box` empty states with `Gtk.Button` widgets that trigger the primary creation/addition action.
## 2026-01-22 - Interactive Empty States
**Learning:** Static empty states (labels/icons) have poor discoverability. Wrapping them in a flat `Gtk.Button` with `vexpand`/`hexpand` creates a large, clickable "drop zone" that reduces friction.
**Action:** Use `Gtk.Button` with `.flat` class and full expansion for interactive empty states instead of static `Gtk.Box`.
