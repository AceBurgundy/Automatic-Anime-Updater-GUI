import 'package:flutter/material.dart';

/// Legacy theme palette enumeration.
enum AppThemeOption {
  /// Solar Flare amber theme option.
  solarFlare,

  /// Ultraviolet purple theme option.
  ultraviolet,

  /// Rose Coral pink theme option.
  roseCoral,

  /// Sage Emerald green theme option.
  sageEmerald,
}

/// Comprehensive theme definition containing all base colors for legacy palettes.
class AppThemeDefinition {
  /// Theme enum identifier.
  final AppThemeOption option;

  /// Human-readable theme name.
  final String name;

  /// Primary accent color.
  final Color primaryAccent;

  /// Background scaffold color.
  final Color background;

  /// Card surface color.
  final Color cardSurface;

  /// Main typography color.
  final Color textMain;

  /// Secondary pop accent color.
  final Color accentPop;

  /// Creates an immutable [AppThemeDefinition] instance.
  const AppThemeDefinition({
    required this.option,
    required this.name,
    required this.primaryAccent,
    required this.background,
    required this.cardSurface,
    required this.textMain,
    required this.accentPop,
  });

  /// Builds a [ThemeData] instance from this theme definition.
  ThemeData buildThemeData() {
    final ColorScheme colorScheme = ColorScheme.dark(
      primary: primaryAccent,
      onPrimary: const Color(0xFF14161D),
      primaryContainer: primaryAccent.withAlpha(45),
      onPrimaryContainer: primaryAccent,
      secondary: accentPop,
      onSecondary: const Color(0xFF14161D),
      secondaryContainer: accentPop.withAlpha(45),
      onSecondaryContainer: accentPop,
      tertiary: accentPop,
      surface: cardSurface,
      surfaceContainerLowest: const Color(0xFF07080B),
      surfaceContainerLow: const Color(0xFF101217),
      surfaceContainer: cardSurface,
      surfaceContainerHigh: const Color(0xFF1D2028),
      surfaceContainerHighest: const Color(0xFF262A34),
      onSurface: textMain,
      onSurfaceVariant: textMain.withAlpha(160),
      outline: Colors.transparent,
      outlineVariant: Colors.transparent,
      error: const Color(0xFFFF6B6B),
      onError: const Color(0xFF1A0002),
      errorContainer: const Color(0xFF4D0009),
      onErrorContainer: const Color(0xFFFFDAD6),
    );

    return ThemeData(
      useMaterial3: true,
      fontFamily: 'GoogleSans',
      brightness: Brightness.dark,
      scaffoldBackgroundColor: background,
      canvasColor: background,
      colorScheme: colorScheme,
      cardColor: cardSurface,
      cardTheme: CardThemeData(
        color: const Color(0xFF14171E),
        elevation: 0,
        margin: EdgeInsets.zero,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(18),
          side: BorderSide.none,
        ),
      ),
      chipTheme: ChipThemeData(
        backgroundColor: const Color(0xFF14171E),
        selectedColor: primaryAccent.withAlpha(45),
        disabledColor: const Color(0xFF14171E).withAlpha(100),
        labelStyle: TextStyle(
          fontFamily: 'GoogleSans',
          color: textMain.withAlpha(200),
          fontSize: 13,
          fontWeight: FontWeight.w500,
        ),
        secondaryLabelStyle: TextStyle(
          fontFamily: 'GoogleSans',
          color: primaryAccent,
          fontSize: 13,
          fontWeight: FontWeight.w600,
        ),
        side: BorderSide.none,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          backgroundColor: primaryAccent,
          foregroundColor: const Color(0xFF14161D),
          elevation: 0,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
          padding: const EdgeInsets.symmetric(horizontal: 22, vertical: 16),
          minimumSize: const Size(0, 50),
          enabledMouseCursor: SystemMouseCursors.click,
          disabledMouseCursor: SystemMouseCursors.basic,
          textStyle: const TextStyle(
            fontFamily: 'GoogleSans',
            fontWeight: FontWeight.w600,
            fontSize: 14,
          ),
        ),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          enabledMouseCursor: SystemMouseCursors.click,
          disabledMouseCursor: SystemMouseCursors.basic,
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          enabledMouseCursor: SystemMouseCursors.click,
          disabledMouseCursor: SystemMouseCursors.basic,
        ),
      ),
      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(
          enabledMouseCursor: SystemMouseCursors.click,
          disabledMouseCursor: SystemMouseCursors.basic,
        ),
      ),
      iconButtonTheme: IconButtonThemeData(
        style: IconButton.styleFrom(
          foregroundColor: primaryAccent,
          enabledMouseCursor: SystemMouseCursors.click,
          disabledMouseCursor: SystemMouseCursors.basic,
        ),
      ),
      checkboxTheme: CheckboxThemeData(
        mouseCursor: WidgetStateProperty.resolveWith<MouseCursor>((Set<WidgetState> states) {
          if (states.contains(WidgetState.disabled)) {
            return SystemMouseCursors.basic;
          }
          return SystemMouseCursors.click;
        }),
      ),
      switchTheme: SwitchThemeData(
        mouseCursor: WidgetStateProperty.resolveWith<MouseCursor>((Set<WidgetState> states) {
          if (states.contains(WidgetState.disabled)) {
            return SystemMouseCursors.basic;
          }
          return SystemMouseCursors.click;
        }),
      ),
      radioTheme: RadioThemeData(
        mouseCursor: WidgetStateProperty.resolveWith<MouseCursor>((Set<WidgetState> states) {
          if (states.contains(WidgetState.disabled)) {
            return SystemMouseCursors.basic;
          }
          return SystemMouseCursors.click;
        }),
      ),
      progressIndicatorTheme: ProgressIndicatorThemeData(
        color: primaryAccent,
        linearTrackColor: const Color(0xFF20242E),
        borderRadius: BorderRadius.circular(4),
      ),
      timePickerTheme: TimePickerThemeData(
        backgroundColor: const Color(0xFF14171E),
        hourMinuteColor: const Color(0xFF07080B),
        hourMinuteTextColor: textMain,
        dialHandColor: primaryAccent,
        dialBackgroundColor: const Color(0xFF07080B),
        dialTextColor: textMain,
        entryModeIconColor: primaryAccent,
        dayPeriodColor: primaryAccent.withAlpha(45),
        dayPeriodTextColor: textMain,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(24),
          side: BorderSide.none,
        ),
      ),
      textTheme: TextTheme(
        headlineMedium: TextStyle(fontFamily: 'GoogleSans', color: textMain, fontWeight: FontWeight.bold, fontSize: 20),
        titleLarge: TextStyle(fontFamily: 'GoogleSans', color: textMain, fontWeight: FontWeight.w600, fontSize: 17),
        titleMedium: TextStyle(fontFamily: 'GoogleSans', color: textMain, fontWeight: FontWeight.w600, fontSize: 14),
        bodyLarge: TextStyle(fontFamily: 'GoogleSans', color: textMain, fontSize: 14),
        bodyMedium: TextStyle(fontFamily: 'GoogleSans', color: textMain.withAlpha(190), fontSize: 13),
        bodySmall: TextStyle(fontFamily: 'GoogleSans', color: textMain.withAlpha(150), fontSize: 12),
      ),
    );
  }
}

/// Registry of legacy theme definitions.
class AppThemes {
  AppThemes._();

  /// Solar Flare theme definition.
  static const AppThemeDefinition solarFlare = AppThemeDefinition(
    option: AppThemeOption.solarFlare,
    name: 'Solar Flare',
    primaryAccent: Color(0xFFFFB300),
    background: Color(0xFF000000),
    cardSurface: Color(0xFF181612),
    textMain: Color(0xFFE8E5E0),
    accentPop: Color(0xFFF97316),
  );

  /// Ultraviolet theme definition.
  static const AppThemeDefinition ultraviolet = AppThemeDefinition(
    option: AppThemeOption.ultraviolet,
    name: 'Ultraviolet',
    primaryAccent: Color(0xFFB388FF),
    background: Color(0xFF000000),
    cardSurface: Color(0xFF16131C),
    textMain: Color(0xFFE6E2E8),
    accentPop: Color(0xFFEC4899),
  );

  /// Rose Coral theme definition.
  static const AppThemeDefinition roseCoral = AppThemeDefinition(
    option: AppThemeOption.roseCoral,
    name: 'Rose Coral',
    primaryAccent: Color(0xFFFB7185),
    background: Color(0xFF000000),
    cardSurface: Color(0xFF171315),
    textMain: Color(0xFFE8E2E4),
    accentPop: Color(0xFFF59E0B),
  );

  /// Sage Emerald theme definition.
  static const AppThemeDefinition sageEmerald = AppThemeDefinition(
    option: AppThemeOption.sageEmerald,
    name: 'Sage Emerald',
    primaryAccent: Color(0xFF34D399),
    background: Color(0xFF000000),
    cardSurface: Color(0xFF111614),
    textMain: Color(0xFFE2E8E5),
    accentPop: Color(0xFFAEEA00),
  );

  /// All available theme definitions in order.
  static const List<AppThemeDefinition> allThemes = <AppThemeDefinition>[
    solarFlare,
    ultraviolet,
    roseCoral,
    sageEmerald,
  ];

  /// Resolves the [AppThemeDefinition] for a given [option].
  static AppThemeDefinition getDefinition(AppThemeOption option) {
    return allThemes.firstWhere(
      (AppThemeDefinition theme) => theme.option == option,
      orElse: () => solarFlare,
    );
  }
}
