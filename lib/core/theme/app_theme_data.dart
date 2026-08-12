import 'package:flutter/material.dart';
import '../constants/app_tokens.dart';
import 'app_palettes.dart';

/// Builder creating M3 ThemeData configured with Google Sans, universal pointer cursors,
/// and smooth desktop hover styling matching single.html.
class AppThemeData {
  AppThemeData._();

  static final Map<AppPaletteOption, ThemeData> _themeCache = <AppPaletteOption, ThemeData>{};

  /// Creates or retrieves a cached configured [ThemeData] instance corresponding to the given [paletteOption].
  static ThemeData create(AppPaletteOption paletteOption) {
    return _themeCache.putIfAbsent(paletteOption, () {
      final AppColorTokens tokens = AppPalettes.getTokens(paletteOption);
      final ColorScheme colorScheme = tokens.toColorScheme();

      return ThemeData(
        useMaterial3: true,
        brightness: Brightness.dark,
        colorScheme: colorScheme,
        scaffoldBackgroundColor: tokens.background,
        fontFamily: AppTokens.fontFamily,
        textTheme: const TextTheme(
          displayLarge: TextStyle(fontFamily: AppTokens.fontFamily, letterSpacing: -0.02),
          displayMedium: TextStyle(fontFamily: AppTokens.fontFamily, letterSpacing: -0.02),
          headlineLarge: TextStyle(fontFamily: AppTokens.fontFamily, fontWeight: FontWeight.w700),
          headlineMedium: TextStyle(fontFamily: AppTokens.fontFamily, fontWeight: FontWeight.w700),
          headlineSmall: TextStyle(fontFamily: AppTokens.fontFamily, fontWeight: FontWeight.w600),
          titleLarge: TextStyle(fontFamily: AppTokens.fontFamily, fontWeight: FontWeight.w600),
          titleMedium: TextStyle(fontFamily: AppTokens.fontFamily, fontWeight: FontWeight.w500),
          titleSmall: TextStyle(fontFamily: AppTokens.fontFamily, fontWeight: FontWeight.w500),
          bodyLarge: TextStyle(fontFamily: AppTokens.fontFamily),
          bodyMedium: TextStyle(fontFamily: AppTokens.fontFamily),
          bodySmall: TextStyle(fontFamily: AppTokens.fontFamily),
          labelLarge: TextStyle(fontFamily: AppTokens.fontFamily, fontWeight: FontWeight.w600),
          labelMedium: TextStyle(fontFamily: AppTokens.fontFamily, fontWeight: FontWeight.w500),
          labelSmall: TextStyle(fontFamily: AppTokens.fontFamily, fontWeight: FontWeight.w500),
        ),
        iconTheme: IconThemeData(
          color: tokens.onSurface,
          size: 20.0,
        ),
        tooltipTheme: TooltipThemeData(
          decoration: BoxDecoration(
            color: tokens.surfaceContainerHighest,
            borderRadius: BorderRadius.circular(AppTokens.cornerFull),
          ),
          textStyle: TextStyle(
            color: tokens.onSurface,
            fontFamily: AppTokens.fontFamily,
            fontSize: 12.0,
            fontWeight: FontWeight.w500,
          ),
          padding: const EdgeInsets.symmetric(horizontal: 12.0, vertical: 6.0),
          waitDuration: const Duration(milliseconds: 200),
        ),
        filledButtonTheme: FilledButtonThemeData(
          style: ButtonStyle(
            mouseCursor: const WidgetStatePropertyAll<MouseCursor>(SystemMouseCursors.click),
            shape: WidgetStatePropertyAll<OutlinedBorder>(
              RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(AppTokens.cornerSquircle),
              ),
            ),
          ),
        ),
        elevatedButtonTheme: ElevatedButtonThemeData(
          style: ButtonStyle(
            mouseCursor: const WidgetStatePropertyAll<MouseCursor>(SystemMouseCursors.click),
            shape: WidgetStatePropertyAll<OutlinedBorder>(
              RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(AppTokens.cornerSquircle),
              ),
            ),
          ),
        ),
        outlinedButtonTheme: OutlinedButtonThemeData(
          style: ButtonStyle(
            mouseCursor: const WidgetStatePropertyAll<MouseCursor>(SystemMouseCursors.click),
            shape: WidgetStatePropertyAll<OutlinedBorder>(
              RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(AppTokens.cornerSquircle),
              ),
            ),
          ),
        ),
        textButtonTheme: const TextButtonThemeData(
          style: ButtonStyle(
            mouseCursor: WidgetStatePropertyAll<MouseCursor>(SystemMouseCursors.click),
          ),
        ),
        iconButtonTheme: const IconButtonThemeData(
          style: ButtonStyle(
            mouseCursor: WidgetStatePropertyAll<MouseCursor>(SystemMouseCursors.click),
          ),
        ),
        radioTheme: RadioThemeData(
          fillColor: WidgetStateProperty.resolveWith<Color>((Set<WidgetState> states) {
            if (states.contains(WidgetState.selected)) {
              return tokens.primary;
            }
            return tokens.onSurfaceVariant;
          }),
          mouseCursor: const WidgetStatePropertyAll<MouseCursor>(SystemMouseCursors.click),
        ),
        checkboxTheme: CheckboxThemeData(
          fillColor: WidgetStateProperty.resolveWith<Color>((Set<WidgetState> states) {
            if (states.contains(WidgetState.selected)) {
              return tokens.primary;
            }
            return Colors.transparent;
          }),
          checkColor: WidgetStatePropertyAll<Color>(tokens.onPrimary),
          mouseCursor: const WidgetStatePropertyAll<MouseCursor>(SystemMouseCursors.click),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(AppTokens.cornerExtraSmall),
          ),
        ),
      );
    });
  }
}
