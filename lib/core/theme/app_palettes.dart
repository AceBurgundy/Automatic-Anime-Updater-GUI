import 'package:flutter/material.dart';

/// Enum representing the 4 Material 3 Theme Palettes defined in single.html.
enum AppPaletteOption {
  /// Default purple / iris theme option.
  purpleIris('Purple Iris', 'purple'),

  /// Ocean cyan theme option.
  oceanCyan('Ocean Cyan', 'ocean'),

  /// Emerald mint theme option.
  emeraldMint('Emerald Mint', 'emerald'),

  /// Mango yellow theme option.
  sunsetAmber('Mango Yellow', 'sunset');

  const AppPaletteOption(this.displayName, this.key);

  /// Human-readable display label.
  final String displayName;

  /// Unique internal string key.
  final String key;
}

/// Color tokens model encompassing all M3 surface container levels and accents.
class AppColorTokens {
  /// Creates an immutable [AppColorTokens] instance with full M3 color specifications.
  const AppColorTokens({
    required this.primary,
    required this.onPrimary,
    required this.primaryContainer,
    required this.onPrimaryContainer,
    required this.secondary,
    required this.onSecondary,
    required this.secondaryContainer,
    required this.onSecondaryContainer,
    required this.tertiary,
    required this.onTertiary,
    required this.tertiaryContainer,
    required this.onTertiaryContainer,
    required this.background,
    required this.onBackground,
    required this.surface,
    required this.onSurface,
    required this.surfaceVariant,
    required this.onSurfaceVariant,
    required this.surfaceContainerLowest,
    required this.surfaceContainerLow,
    required this.surfaceContainer,
    required this.surfaceContainerHigh,
    required this.surfaceContainerHighest,
  });

  /// Primary accent color.
  final Color primary;

  /// Color for content on top of primary.
  final Color onPrimary;

  /// Primary container background color.
  final Color primaryContainer;

  /// Color for content on top of primary container.
  final Color onPrimaryContainer;

  /// Secondary accent color.
  final Color secondary;

  /// Color for content on top of secondary.
  final Color onSecondary;

  /// Secondary container background color.
  final Color secondaryContainer;

  /// Color for content on top of secondary container.
  final Color onSecondaryContainer;

  /// Tertiary accent color.
  final Color tertiary;

  /// Color for content on top of tertiary.
  final Color onTertiary;

  /// Tertiary container background color.
  final Color tertiaryContainer;

  /// Color for content on top of tertiary container.
  final Color onTertiaryContainer;

  /// Base scaffold background color.
  final Color background;

  /// Color for content on top of background.
  final Color onBackground;

  /// Base surface color.
  final Color surface;

  /// Color for content on top of surface.
  final Color onSurface;

  /// Surface variant outline/divider color.
  final Color surfaceVariant;

  /// Color for muted text and secondary iconography.
  final Color onSurfaceVariant;

  /// Lowest surface container tone.
  final Color surfaceContainerLowest;

  /// Low surface container tone for content areas.
  final Color surfaceContainerLow;

  /// Standard surface container tone for cards.
  final Color surfaceContainer;

  /// High surface container tone for interactive inputs.
  final Color surfaceContainerHigh;

  /// Highest surface container tone for active highlights.
  final Color surfaceContainerHighest;

  /// Convert tokens into Material 3 [ColorScheme].
  ColorScheme toColorScheme() {
    return ColorScheme.dark(
      primary: primary,
      onPrimary: onPrimary,
      primaryContainer: primaryContainer,
      onPrimaryContainer: onPrimaryContainer,
      secondary: secondary,
      onSecondary: onSecondary,
      secondaryContainer: secondaryContainer,
      onSecondaryContainer: onSecondaryContainer,
      tertiary: tertiary,
      onTertiary: onTertiary,
      tertiaryContainer: tertiaryContainer,
      onTertiaryContainer: onTertiaryContainer,
      surface: surface,
      onSurface: onSurface,
      surfaceContainerLowest: surfaceContainerLowest,
      surfaceContainerLow: surfaceContainerLow,
      surfaceContainer: surfaceContainer,
      surfaceContainerHigh: surfaceContainerHigh,
      surfaceContainerHighest: surfaceContainerHighest,
      onSurfaceVariant: onSurfaceVariant,
      outline: surfaceVariant,
    );
  }
}

/// Palette repository mapping each [AppPaletteOption] to its [AppColorTokens].
class AppPalettes {
  AppPalettes._();

  /// Default Purple Iris palette tokens with neutral lighter black surfaces and purple accents.
  static const AppColorTokens purpleIris = AppColorTokens(
    primary: Color(0xFFC084FC),
    onPrimary: Color(0xFF2E1065),
    primaryContainer: Color(0xFF7E22CE),
    onPrimaryContainer: Color(0xFFF3E8FF),
    secondary: Color(0xFFD8B4FE),
    onSecondary: Color(0xFF3B0764),
    secondaryContainer: Color(0xFF581C87),
    onSecondaryContainer: Color(0xFFFAF5FF),
    tertiary: Color(0xFFF472B6),
    onTertiary: Color(0xFF500724),
    tertiaryContainer: Color(0xFF831843),
    onTertiaryContainer: Color(0xFFFCE7F3),
    background: Color(0xFF141416),
    onBackground: Color(0xFFEDEDF0),
    surface: Color(0xFF141416),
    onSurface: Color(0xFFEDEDF0),
    surfaceVariant: Color(0xFF42424C),
    onSurfaceVariant: Color(0xFFA0A0AB),
    surfaceContainerLowest: Color(0xFF0E0E10),
    surfaceContainerLow: Color(0xFF1A1A1E),
    surfaceContainer: Color(0xFF222226),
    surfaceContainerHigh: Color(0xFF2A2A30),
    surfaceContainerHighest: Color(0xFF34343C),
  );

  /// Ocean Cyan palette tokens with neutral lighter black surfaces and cyan accents.
  static const AppColorTokens oceanCyan = AppColorTokens(
    primary: Color(0xFF22D3EE),
    onPrimary: Color(0xFF083344),
    primaryContainer: Color(0xFF0891B2),
    onPrimaryContainer: Color(0xFFECFEFF),
    secondary: Color(0xFF67E8F9),
    onSecondary: Color(0xFF164E63),
    secondaryContainer: Color(0xFF0E7490),
    onSecondaryContainer: Color(0xFFCFFAFE),
    tertiary: Color(0xFF38BDF8),
    onTertiary: Color(0xFF0C4A6E),
    tertiaryContainer: Color(0xFF0284C7),
    onTertiaryContainer: Color(0xFFE0F2FE),
    background: Color(0xFF141416),
    onBackground: Color(0xFFEDEDF0),
    surface: Color(0xFF141416),
    onSurface: Color(0xFFEDEDF0),
    surfaceVariant: Color(0xFF42424C),
    onSurfaceVariant: Color(0xFFA0A0AB),
    surfaceContainerLowest: Color(0xFF0E0E10),
    surfaceContainerLow: Color(0xFF1A1A1E),
    surfaceContainer: Color(0xFF222226),
    surfaceContainerHigh: Color(0xFF2A2A30),
    surfaceContainerHighest: Color(0xFF34343C),
  );

  /// Emerald Mint palette tokens with neutral lighter black surfaces and mint accents.
  static const AppColorTokens emeraldMint = AppColorTokens(
    primary: Color(0xFF34D399),
    onPrimary: Color(0xFF022C22),
    primaryContainer: Color(0xFF059669),
    onPrimaryContainer: Color(0xFFECFDF5),
    secondary: Color(0xFF6EE7B7),
    onSecondary: Color(0xFF064E3B),
    secondaryContainer: Color(0xFF047857),
    onSecondaryContainer: Color(0xFFD1FAE5),
    tertiary: Color(0xFF2DD4BF),
    onTertiary: Color(0xFF134E4A),
    tertiaryContainer: Color(0xFF0F766E),
    onTertiaryContainer: Color(0xFFCCFBF1),
    background: Color(0xFF141416),
    onBackground: Color(0xFFEDEDF0),
    surface: Color(0xFF141416),
    onSurface: Color(0xFFEDEDF0),
    surfaceVariant: Color(0xFF42424C),
    onSurfaceVariant: Color(0xFFA0A0AB),
    surfaceContainerLowest: Color(0xFF0E0E10),
    surfaceContainerLow: Color(0xFF1A1A1E),
    surfaceContainer: Color(0xFF222226),
    surfaceContainerHigh: Color(0xFF2A2A30),
    surfaceContainerHighest: Color(0xFF34343C),
  );

  /// Mango Yellow palette tokens with neutral lighter black surfaces and bright soft mango yellow accents.
  static const AppColorTokens sunsetAmber = AppColorTokens(
    primary: Color(0xFFFDE047),
    onPrimary: Color(0xFF3A2E00),
    primaryContainer: Color(0xFFFDE047),
    onPrimaryContainer: Color(0xFF3A2E00),
    secondary: Color(0xFFFEE685),
    onSecondary: Color(0xFF382C00),
    secondaryContainer: Color(0xFFFDE047),
    onSecondaryContainer: Color(0xFF3A2E00),
    tertiary: Color(0xFFFDF08A),
    onTertiary: Color(0xFF382B00),
    tertiaryContainer: Color(0xFFFEE685),
    onTertiaryContainer: Color(0xFF3A2E00),
    background: Color(0xFF141416),
    onBackground: Color(0xFFEDEDF0),
    surface: Color(0xFF141416),
    onSurface: Color(0xFFEDEDF0),
    surfaceVariant: Color(0xFF42424C),
    onSurfaceVariant: Color(0xFFA0A0AB),
    surfaceContainerLowest: Color(0xFF0E0E10),
    surfaceContainerLow: Color(0xFF1A1A1E),
    surfaceContainer: Color(0xFF222226),
    surfaceContainerHigh: Color(0xFF2A2A30),
    surfaceContainerHighest: Color(0xFF34343C),
  );

  /// Returns [AppColorTokens] corresponding to the given [option].
  static AppColorTokens getTokens(AppPaletteOption option) {
    switch (option) {
      case AppPaletteOption.purpleIris:
        return purpleIris;
      case AppPaletteOption.oceanCyan:
        return oceanCyan;
      case AppPaletteOption.emeraldMint:
        return emeraldMint;
      case AppPaletteOption.sunsetAmber:
        return sunsetAmber;
    }
  }
}
