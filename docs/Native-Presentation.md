# Native presentation ownership

Native Eto tools use one caption writer, introduced in 0.22.17. The former
0.25-second material status refresh wrote Chinese source text to live controls,
while the 0.6-second workspace scan rewrote it in the selected language.
Changing translation dictionaries could not fix these competing writers.

## Update path

Business/source state → UiCaption → NativeText → InterfacePresentation → native control.

- UiLabel, UiButton and UiCheckBox intercept Text assignments. UiListItem,
  UiButtonMenuItem, UiGroupBox and UiGridColumn own their corresponding captions.
  UiExpander creates a bound label for a string header. UiTextBox binds only its
  placeholder; editable input remains user data.
- UiCaption keeps the source separately from displayed text. The translator never
  reads the current abbreviation to reconstruct the source. Unchanged source
  assignments are skipped; an unchanged result is not written to the handler.
- Icon changes and the Eto WPF caption restoration happen synchronously in the
  same render operation. Framework changes during rendering cannot replace the
  source. Icon glyphs remain 16 DIP.
- PluginPreferences.Save and Rhino AppSettingsChanged refresh the presentation
  context. Weak registrations do not retain closed document tools. Shutdown
  unsubscribes the Rhino event and clears the registry.
- The document timer only detects/rebinds document changes. WorkspaceAppearance
  decorates colours, wrapping and layout at attachment/style changes; it never
  translates or abbreviates Text after it has been displayed.
- Preserve user-content/user-context tags, catalog values, scientific names,
  filenames and editable values. Built-in display-mode choices explicitly opt
  into caption localization; user-named values do not.

## Regression evidence

Use scripts/Test-PresentationIdle.py with the actual B instance. Its UI timer
samples the real label while no Platform command is running. Short/full English,
Chinese, return to English and a live object selection are tested separately.
Sampling within a single blocking Platform command cannot verify idle flicker.

Continue the nine-page language/icon, narrow-layout, preference/draft and
New/Open lifecycle regressions. Static translation fixtures alone do not establish
that the UI has a single writer. New native controls must use the bound types;
keep the constructor/periodic-translation ownership guard passing.
