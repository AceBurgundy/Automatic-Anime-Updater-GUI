import 'package:flutter/material.dart';

/// Application-wide constants, default dimensions, and script paths.
class AppConstants {
  AppConstants._();

  /// Main application title.
  static const String appTitle = 'Kyaa!!';

  /// Default window dimensions.
  static const Size defaultWindowSize = Size(720, 900);

  /// Path to the AI parser script.
  static const String parserScriptPath = 'assets/scripts/parser.py';

  /// Directory path where downloaded models are stored.
  static const String modelsDirPath = 'assets/models';

  /// Subprocess status description message.
  static const String parserStatusMessage =
      'An AI model is needed to ensure that the app works smoothly.';

  /// Button label when parser download is idle.
  static const String parserButtonIdle = 'Download AI Model';

  /// Button label when parser download is running.
  static const String parserButtonRunning = 'Downloading...';

  /// Button label when parser download is ready.
  static const String parserButtonCompleted = 'Model Ready';

  /// Title for the subtitled preference option.
  static const String subtitledTitle = 'Subtitled';

  /// Subtitle description for the subtitled preference option.
  static const String subtitledSubtitle = 'Original voiceover with translated text';

  /// Title for the dubbed preference option.
  static const String dubbedTitle = 'Dubbed';

  /// Subtitle description for the dubbed preference option.
  static const String dubbedSubtitle = 'Localized voice acting';

  /// Default folder placeholder display text.
  static const String defaultFolderPlaceholder = 'Select Directory';
}
