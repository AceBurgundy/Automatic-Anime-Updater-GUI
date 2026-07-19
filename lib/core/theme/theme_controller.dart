import 'package:flutter/material.dart';
import 'app_palettes.dart';
import 'app_theme_data.dart';

/// Controller managing active theme palette and broadcasting changes.
class ThemeController extends ChangeNotifier {
  /// Creates a [ThemeController] initialized with [initialPalette].
  ThemeController({AppPaletteOption initialPalette = AppPaletteOption.sunsetAmber})
      : _activePalette = initialPalette;

  AppPaletteOption _activePalette;

  /// Currently selected [AppPaletteOption].
  AppPaletteOption get activePalette => _activePalette;

  /// Active [AppColorTokens] matching the selected palette.
  AppColorTokens get tokens => AppPalettes.getTokens(_activePalette);

  /// Current [ThemeData] constructed from the active palette.
  ThemeData get currentThemeData => AppThemeData.create(_activePalette);

  /// Updates the active palette to [newPalette] and notifies listeners if changed.
  void setPalette(AppPaletteOption newPalette) {
    if (_activePalette == newPalette) return;
    _activePalette = newPalette;
    notifyListeners();
  }
}
