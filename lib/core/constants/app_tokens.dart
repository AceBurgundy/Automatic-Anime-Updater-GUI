import 'package:flutter/material.dart';

/// Design tokens and structural constants matching the single.html specification.
class AppTokens {
  AppTokens._();

  /// Default application window width in pixels.
  static const double windowWidth = 1000.0;

  /// Default application window height in pixels.
  static const double windowHeight = 740.0;

  /// Standard outer window margin and padding in pixels (1rem).
  static const double windowPadding = 16.0;

  /// Extra small corner radius in pixels (0.375rem).
  static const double cornerExtraSmall = 6.0;

  /// Standard squircle corner radius in pixels (0.875rem).
  static const double cornerSquircle = 14.0;

  /// Small corner radius in pixels (0.875rem).
  static const double cornerSmall = 14.0;

  /// Medium corner radius in pixels (1.25rem).
  static const double cornerMedium = 20.0;

  /// Large corner radius in pixels (1.5rem).
  static const double cornerLarge = 24.0;

  /// Extra large corner radius in pixels (2rem).
  static const double cornerExtraLarge = 32.0;

  /// Full stadium/pill corner radius in pixels.
  static const double cornerFull = 9999.0;

  /// Title bar vertical height in pixels.
  static const double titleBarHeight = 44.0;

  /// Top pill navigation tab bar height in pixels (4.375rem).
  static const double tabBarHeight = 70.0;

  /// Standard squircle icon button dimension in pixels (2.75rem).
  static const double iconButtonSize = 44.0;

  /// Large squircle icon button dimension in pixels (3.5rem).
  static const double iconButtonLargeSize = 56.0;

  /// Section header squircle icon square container dimension in pixels (2.25rem).
  static const double iconSquareSize = 36.0;

  /// Full pill search input container height in pixels (3.25rem).
  static const double searchInputHeight = 52.0;

  /// Squircle day letter button dimension in pixels (3.25rem).
  static const double dayButtonSize = 52.0;

  /// Full pill trigger time item height in pixels (3.25rem).
  static const double timePillHeight = 52.0;

  /// Linear progress track bar height in pixels (0.45rem).
  static const double progressTrackHeight = 7.2;

  /// Default application typography font family name.
  static const String fontFamily = 'GoogleSans';

  /// Monospace code font family name.
  static const String codeFontFamily = 'monospace';

  /// Pure AMOLED dark black background color.
  static const Color amoledBlack = Color(0xFF000000);
}
