import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:path/path.dart' as p;
import '../../widgets/views/tasks_view.dart';

/// Configuration state loaded from the backend CLI.
class CliConfigState {
  /// Creates a [CliConfigState] instance with optional configuration values.
  const CliConfigState({
    this.targetDirectory = '',
    this.preferredQuality = '1080p',
    this.preferredAudio = 'Subbed',
    this.isModelInstalled = false,
    this.modelSizeMb = 0.0,
    this.folderAsTitle = true,
  });

  /// Target directory path where downloaded anime is stored.
  final String targetDirectory;

  /// Preferred video resolution (e.g. '1080p', '720p').
  final String preferredQuality;

  /// Preferred audio language/release preference (e.g. 'Subbed', 'Dubbed').
  final String preferredAudio;

  /// Whether the AI episode parser model is currently installed.
  final bool isModelInstalled;

  /// File size of the installed AI parser model in megabytes.
  final double modelSizeMb;

  /// Whether folder names are prioritized as anime titles.
  final bool folderAsTitle;

  /// Returns a copy of this [CliConfigState] with specified fields replaced.
  CliConfigState copyWith({
    String? targetDirectory,
    String? preferredQuality,
    String? preferredAudio,
    bool? isModelInstalled,
    double? modelSizeMb,
    bool? folderAsTitle,
  }) {
    return CliConfigState(
      targetDirectory: targetDirectory ?? this.targetDirectory,
      preferredQuality: preferredQuality ?? this.preferredQuality,
      preferredAudio: preferredAudio ?? this.preferredAudio,
      isModelInstalled: isModelInstalled ?? this.isModelInstalled,
      modelSizeMb: modelSizeMb ?? this.modelSizeMb,
      folderAsTitle: folderAsTitle ?? this.folderAsTitle,
    );
  }
}

/// Service orchestrating real-time communication, configuration management,
/// and background subprocess execution with the Python `anime-refresher-cli`.
class CliBridgeService {
  /// Private constructor for [CliBridgeService] singleton pattern.
  CliBridgeService._();

  /// Shared singleton instance of [CliBridgeService].
  static final CliBridgeService instance = CliBridgeService._();

  /// Active system process running the Python automation engine.
  Process? _activeAutomationProcess;

  /// Active system process running the AI model downloader.
  Process? _activeModelProcess;

  /// Internal flag indicating whether the automation engine is running.
  bool _isAutomationRunning = false;

  /// Internal stream controller emitting task item updates.
  final StreamController<TaskItemData> _taskEventController = StreamController<TaskItemData>.broadcast();

  /// Internal reactive notifier for the list of task items.
  final ValueNotifier<List<TaskItemData>> _tasksNotifier = ValueNotifier<List<TaskItemData>>(<TaskItemData>[]);

  /// Internal reactive notifier indicating whether automation is executing.
  final ValueNotifier<bool> _isExecutingNotifier = ValueNotifier<bool>(false);

  /// Internal reactive notifier for backend configuration state.
  final ValueNotifier<CliConfigState> _configNotifier = ValueNotifier<CliConfigState>(const CliConfigState());

  /// Internal reactive notifier for the list of ignored items.
  final ValueNotifier<List<String>> _ignoredItemsNotifier = ValueNotifier<List<String>>(<String>[]);

  /// Periodic timer triggering scheduled automation runs.
  Timer? _schedulerTimer;

  /// Internal reactive notifier for scheduler active state.
  final ValueNotifier<bool> _isSchedulerActiveNotifier = ValueNotifier<bool>(false);

  /// Stream of live episode task updates emitted from the CLI engine.
  Stream<TaskItemData> get taskEvents => _taskEventController.stream;

  /// Reactive list of all accumulated and active tasks.
  ValueListenable<List<TaskItemData>> get tasksNotifier => _tasksNotifier;

  /// Reactive boolean indicating if the automation engine is actively running.
  ValueListenable<bool> get isExecutingNotifier => _isExecutingNotifier;

  /// Reactive configuration state.
  ValueListenable<CliConfigState> get configNotifier => _configNotifier;

  /// Reactive list of currently ignored folders and files.
  ValueListenable<List<String>> get ignoredItemsNotifier => _ignoredItemsNotifier;

  /// Reactive boolean indicating whether the background scheduler is currently active.
  ValueListenable<bool> get isSchedulerActiveNotifier => _isSchedulerActiveNotifier;

  /// Whether the automation engine is currently executing.
  bool get isAutomationRunning => _isAutomationRunning;

  /// Resolves the directory path of the backend Python CLI engine.
  String resolveCliDirectory() {
    // 1. Environment variable override
    final String? environmentOverride = Platform.environment['KYAA_BACKEND_DIR'] ??
        Platform.environment['KYAA_CLI_DIR'] ??
        Platform.environment['ANIME_REFRESHER_CLI_DIR'];
    if (environmentOverride != null && Directory(environmentOverride).existsSync()) {
      return environmentOverride;
    }

    // 2. Check child backend directory (monorepo structure)
    final String childBackend = p.normalize(p.join(Directory.current.path, 'backend'));
    if (Directory(childBackend).existsSync()) {
      return childBackend;
    }

    // 3. Check child anime-refresher-cli directory (legacy)
    final String childCliDirectory = p.normalize(p.join(Directory.current.path, 'anime-refresher-cli'));
    if (Directory(childCliDirectory).existsSync()) {
      return childCliDirectory;
    }

    // 4. Check sibling backend directory
    final String siblingBackend = p.normalize(p.join(Directory.current.path, '..', 'backend'));
    if (Directory(siblingBackend).existsSync()) {
      return siblingBackend;
    }

    // 5. Check sibling anime-refresher-cli directory
    final String siblingCliDirectory = p.normalize(p.join(Directory.current.path, '..', 'anime-refresher-cli'));
    if (Directory(siblingCliDirectory).existsSync()) {
      return siblingCliDirectory;
    }

    // 6. Check consolidated Flutter project path
    final Directory consolidatedDirectory = Directory(r'D:\Documents\Programming\Frameworks\Flutter\projects\kyaa_anime_refresher\backend');
    if (consolidatedDirectory.existsSync()) {
      return consolidatedDirectory.path;
    }

    // 7. Check standalone Automation CLI path
    final Directory standaloneDirectory = Directory(r'D:\Documents\Programming\Languages\Python\Automation\anime-refresher-cli');
    if (standaloneDirectory.existsSync()) {
      return standaloneDirectory.path;
    }

    // 8. Fallback to default path
    return r'D:\Documents\Programming\Frameworks\Flutter\projects\kyaa_anime_refresher\backend';
  }

  /// Resolves the Python binary (prioritizing the local virtual environment).
  String resolvePythonBinary() {
    final String cliDirectory = resolveCliDirectory();

    // Prioritize CLI virtual environment Python (env, .venv, venv)
    final File environmentPythonFile = File(p.join(cliDirectory, 'env', 'Scripts', 'python.exe'));
    if (environmentPythonFile.existsSync()) {
      return environmentPythonFile.path;
    }

    final File dotVenvPythonFile = File(p.join(cliDirectory, '.venv', 'Scripts', 'python.exe'));
    if (dotVenvPythonFile.existsSync()) {
      return dotVenvPythonFile.path;
    }

    final File alternateVenvPythonFile = File(p.join(cliDirectory, 'venv', 'Scripts', 'python.exe'));
    if (alternateVenvPythonFile.existsSync()) {
      return alternateVenvPythonFile.path;
    }

    // Local kyaa_app env fallback
    final File localEnvironmentPythonFile = File(p.join(Directory.current.path, 'env', 'Scripts', 'python.exe'));
    if (localEnvironmentPythonFile.existsSync()) {
      return localEnvironmentPythonFile.path;
    }

    return 'python';
  }

  /// Loads initial configuration from the CLI `.env` file and model directory.
  Future<void> loadInitialConfig() async {
    try {
      final String cliDirectory = resolveCliDirectory();
      final File environmentFile = File(p.join(cliDirectory, '.env'));
      String targetDirectory = r'D:\Videos\Anime Unwatched';
      String quality = '1080p';
      String audio = 'Subbed';

      if (environmentFile.existsSync()) {
        final List<String> lines = await environmentFile.readAsLines();
        for (final String line in lines) {
          final String trimmed = line.trim();
          if (trimmed.startsWith('TARGET_DIR=')) {
            targetDirectory = trimmed.substring('TARGET_DIR='.length).trim();
          } else if (trimmed.startsWith('PREFERRED_RESOLUTION=')) {
            final String rawResolution = trimmed.substring('PREFERRED_RESOLUTION='.length).trim().replaceAll('p', '');
            quality = '${rawResolution}p';
          } else if (trimmed.startsWith('AUDIO_PREFERENCE=')) {
            final String rawAudio = trimmed.substring('AUDIO_PREFERENCE='.length).trim().toLowerCase();
            audio = rawAudio.contains('dub') ? 'Dubbed' : 'Subbed';
          }
        }
      }

      // Check model file presence
      final Directory modelsDirectory = Directory(p.join(cliDirectory, 'models'));
      bool modelPresent = false;
      double modelSizeMb = 0.0;
      if (modelsDirectory.existsSync()) {
        final List<FileSystemEntity> entities = modelsDirectory.listSync();
        for (final FileSystemEntity entity in entities) {
          if (entity is File && entity.path.endsWith('.gguf')) {
            modelPresent = true;
            modelSizeMb = entity.lengthSync() / (1024 * 1024);
            break;
          }
        }
      }

      _configNotifier.value = CliConfigState(
        targetDirectory: targetDirectory,
        preferredQuality: quality,
        preferredAudio: audio,
        isModelInstalled: modelPresent,
        modelSizeMb: modelSizeMb,
      );

      unawaited(listIgnored());
    } catch (exception) {
      debugPrint('[CliBridgeService] Notice loading initial config: $exception');
    }
  }

  /// Starts the automation pipeline subprocess in real-time stream mode.
  Future<void> startAutomation({
    String? preferredResolution,
  }) async {
    if (_isAutomationRunning) {
      debugPrint('[CliBridgeService] Automation is already active.');
      return;
    }

    final String cliDirectory = resolveCliDirectory();
    final String pythonBinary = resolvePythonBinary();
    final String mainPythonScript = p.join(cliDirectory, 'main.py');

    final List<String> arguments = <String>[
      mainPythonScript,
      '--start-automation-stream',
    ];

    if (preferredResolution != null && preferredResolution.isNotEmpty) {
      arguments.addAll(<String>[
        '--preferred-resolution',
        preferredResolution.replaceAll('p', ''),
      ]);
    }

    debugPrint('[CliBridgeService] Launching automation: $pythonBinary ${arguments.join(" ")}');

    _isAutomationRunning = true;
    _isExecutingNotifier.value = true;

    try {
      final Process process = await Process.start(
        pythonBinary,
        arguments,
        workingDirectory: cliDirectory,
        runInShell: true,
      );

      _activeAutomationProcess = process;

      // Listen for NDJSON event stream on stdout
      process.stdout
          .transform(utf8.decoder)
          .transform(const LineSplitter())
          .listen(
            _handleStreamLine,
            onError: (Object error) {
              debugPrint('[CliBridgeService] Stdout stream error: $error');
            },
          );

      process.stderr
          .transform(utf8.decoder)
          .transform(const LineSplitter())
          .listen(
            (String errorLine) {
              if (errorLine.trim().isNotEmpty) {
                debugPrint('[CliBridgeService StdErr] $errorLine');
              }
            },
          );

      final int exitCode = await process.exitCode;
      debugPrint('[CliBridgeService] Automation process concluded with code $exitCode');
    } catch (exception) {
      debugPrint('[CliBridgeService] Failed to start automation process: $exception');
    } finally {
      _activeAutomationProcess = null;
      _isAutomationRunning = false;
      _isExecutingNotifier.value = false;
    }
  }

  /// Parses a single NDJSON line emitted by `emit_stream_event`.
  void _handleStreamLine(String rawLine) {
    final String line = rawLine.trim();
    if (line.isEmpty) return;

    try {
      final dynamic decoded = jsonDecode(line);
      if (decoded is Map<String, dynamic>) {
        final Map<String, Object?> map = Map<String, Object?>.from(decoded);
        final String animeName = map['string_anime_name'] as String? ?? 'Episode';
        final int episodeNumber = (map['int_episode_number'] as num?)?.toInt() ?? 0;
        final String generatedId = '${animeName.toLowerCase().replaceAll(RegExp(r'[^a-z0-9]'), '_')}_ep$episodeNumber';

        final TaskItemData item = TaskItemData.fromMap(map, id: generatedId);

        // Notify stream subscribers
        _taskEventController.add(item);

        // Update accumulated tasks list
        final List<TaskItemData> currentList = List<TaskItemData>.from(_tasksNotifier.value);
        final int existingIndex = currentList.indexWhere((TaskItemData taskItem) => taskItem.id == item.id);

        if (existingIndex >= 0) {
          currentList[existingIndex] = item;
        } else {
          currentList.insert(0, item);
        }

        _tasksNotifier.value = currentList;
      }
    } catch (exception) {
      // Not JSON or plain log line
      debugPrint('[CliBridgeService Raw Log] $line');
    }
  }

  /// Gracefully stops or terminates the active automation subprocess.
  void pauseAutomation() {
    if (_activeAutomationProcess != null) {
      try {
        debugPrint('[CliBridgeService] Terminating active automation process...');
        _activeAutomationProcess!.kill(ProcessSignal.sigkill);
      } catch (exception) {
        debugPrint('[CliBridgeService] Error killing automation process: $exception');
      }
      _activeAutomationProcess = null;
      _isAutomationRunning = false;
      _isExecutingNotifier.value = false;
    }
  }

  /// Downloads the AI parser model weights via `main.py --download-model`.
  Future<void> downloadModel({
    required void Function(double progress) onProgress,
    required void Function(String error) onError,
    required VoidCallback onComplete,
  }) async {
    final String cliDirectory = resolveCliDirectory();
    final String pythonBinary = resolvePythonBinary();
    final String mainPythonScript = p.join(cliDirectory, 'main.py');

    debugPrint('[CliBridgeService] Invoking model download: $pythonBinary $mainPythonScript --download-model');

    try {
      final Process process = await Process.start(
        pythonBinary,
        <String>[mainPythonScript, '--download-model'],
        workingDirectory: cliDirectory,
        runInShell: true,
      );

      _activeModelProcess = process;

      process.stdout
          .transform(utf8.decoder)
          .transform(const LineSplitter())
          .listen((String line) {
            final String trimmed = line.trim();
            debugPrint('[Model Download] $trimmed');

            // Match progress patterns like "[Download: 45.2%]" or "45%"
            final RegExp percentageRegex = RegExp(r'(\d+(?:\.\d+)?)\s*%');
            final Match? match = percentageRegex.firstMatch(trimmed);
            if (match != null) {
              final double? percentage = double.tryParse(match.group(1) ?? '');
              if (percentage != null) {
                onProgress((percentage / 100.0).clamp(0.0, 1.0));
              }
            } else if (trimmed.startsWith('PROGRESS:')) {
              final List<String> parts = trimmed.split(':');
              if (parts.length > 1) {
                final double? parsed = double.tryParse(parts[1]);
                if (parsed != null) onProgress((parsed / 100.0).clamp(0.0, 1.0));
              }
            }
          });

      process.stderr
          .transform(utf8.decoder)
          .transform(const LineSplitter())
          .listen((String errorLine) {
            if (errorLine.trim().isNotEmpty) onError(errorLine.trim());
          });

      final int exitCode = await process.exitCode;
      _activeModelProcess = null;

      if (exitCode == 0) {
        onProgress(1.0);
        await loadInitialConfig();
        onComplete();
      } else {
        onError('Model download failed with exit code $exitCode');
      }
    } catch (exception) {
      _activeModelProcess = null;
      onError(exception.toString());
    }
  }

  /// Cancels any active model download subprocess.
  void cancelModelDownload() {
    if (_activeModelProcess != null) {
      try {
        _activeModelProcess!.kill(ProcessSignal.sigkill);
      } catch (exception) {
        debugPrint('Notice killing model download process: $exception');
      }
      _activeModelProcess = null;
    }
  }

  /// Updates target anime directory in the CLI configuration (`.env`).
  Future<void> setTargetDirectory(String directoryPath) async {
    await _executeCliConfigCommand(<String>['--set-target-directory', directoryPath]);
    _configNotifier.value = _configNotifier.value.copyWith(targetDirectory: directoryPath);
  }

  /// Updates preferred video resolution preference in the CLI configuration (`.env`).
  Future<void> setPreferredQuality(String quality) async {
    final String cleanRes = quality.replaceAll('p', '').trim();
    await _executeCliConfigCommand(<String>['--set-preferred-resolution', cleanRes]);
    _configNotifier.value = _configNotifier.value.copyWith(preferredQuality: quality);
  }

  /// Updates audio track preference in the CLI configuration (`.env`).
  Future<void> setPreferredAudio(String audio) async {
    final String pref = audio.toLowerCase().contains('dub') ? 'dub' : 'sub';
    await _executeCliConfigCommand(<String>['--set-audio-preference', pref]);
    _configNotifier.value = _configNotifier.value.copyWith(preferredAudio: audio);
  }

  /// Folder-indexed template is default and hardcoded.
  Future<void> setFolderAsTitle(bool enabled) async {
    _configNotifier.value = _configNotifier.value.copyWith(folderAsTitle: true);
  }

  /// Fetches and updates the list of ignored items via `main.py --list-ignored`.
  Future<List<String>> listIgnored() async {
    final ProcessResult? result = await _executeCliConfigCommand(<String>['--list-ignored']);
    final List<String> items = <String>[];
    if (result != null && result.exitCode == 0) {
      final String stdout = result.stdout as String? ?? '';
      final List<String> lines = stdout.split(RegExp(r'\r?\n'));
      for (final String rawLine in lines) {
        final String trimmed = rawLine.trim();
        if (trimmed.startsWith('- ')) {
          final String item = trimmed.substring(2).trim();
          if (item.isNotEmpty && !items.contains(item)) {
            items.add(item);
          }
        }
      }
    }
    _ignoredItemsNotifier.value = items;
    return items;
  }

  /// Adds a folder or file to the ignore list via `main.py --ignore <item>`.
  Future<void> addIgnoredItem(String item) async {
    final String clean = item.trim();
    if (clean.isEmpty) return;
    await _executeCliConfigCommand(<String>['--ignore', clean]);
    await listIgnored();
  }

  /// Removes an item from the ignore list via `main.py --unignore <item>`.
  Future<void> removeIgnoredItem(String item) async {
    final String clean = item.trim();
    if (clean.isEmpty) return;
    await _executeCliConfigCommand(<String>['--unignore', clean]);
    await listIgnored();
  }

  /// Clears all items from the ignore list via `main.py --reset-ignored`.
  Future<void> resetIgnoredItems() async {
    await _executeCliConfigCommand(<String>['--reset-ignored']);
    _ignoredItemsNotifier.value = <String>[];
  }

  /// Starts the background schedule, registers Windows task scheduler, and starts internal periodic timer.
  Future<void> startScheduler({
    required List<String> activeDays,
    required List<String> triggerTimes,
  }) async {
    await setupTaskScheduler();
    _isSchedulerActiveNotifier.value = true;
    _schedulerTimer?.cancel();

    _schedulerTimer = Timer.periodic(const Duration(seconds: 30), (_) {
      _checkScheduleTriggers(activeDays: activeDays, triggerTimes: triggerTimes);
    });
  }

  /// Stops the background scheduler, unregisters Windows task scheduler, and cancels timer.
  Future<void> stopScheduler() async {
    _schedulerTimer?.cancel();
    _schedulerTimer = null;
    _isSchedulerActiveNotifier.value = false;
    await removeTaskScheduler();
  }

  void _checkScheduleTriggers({
    required List<String> activeDays,
    required List<String> triggerTimes,
  }) {
    if (!_isSchedulerActiveNotifier.value || _isAutomationRunning) return;

    final DateTime now = DateTime.now();
    const List<String> weekdayNames = <String>[
      'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'
    ];
    final String currentDay = weekdayNames[now.weekday - 1];

    if (!activeDays.contains(currentDay)) return;

    final int hour = now.hour % 12 == 0 ? 12 : now.hour % 12;
    final String hourString = hour.toString().padLeft(2, '0');
    final String minuteString = now.minute.toString().padLeft(2, '0');
    final String period = now.hour >= 12 ? 'PM' : 'AM';
    final String currentTimeFormatted = '$hourString:$minuteString $period';

    for (final String targetTime in triggerTimes) {
      if (currentTimeFormatted.toUpperCase() == targetTime.trim().toUpperCase()) {
        debugPrint('[CliBridgeService Scheduler] Trigger matched: $currentTimeFormatted on $currentDay. Starting automation...');
        startAutomation();
        break;
      }
    }
  }

  /// Registers automated triggers in Windows Task Scheduler.
  Future<void> setupTaskScheduler() async {
    await _executeCliConfigCommand(<String>['--setup-task-scheduler']);
  }

  /// Removes automated triggers from Windows Task Scheduler.
  Future<void> removeTaskScheduler() async {
    await _executeCliConfigCommand(<String>['--remove-task-scheduler']);
  }

  /// Helper to execute a quick CLI configuration command.
  Future<ProcessResult?> _executeCliConfigCommand(List<String> arguments) async {
    try {
      final String cliDirectory = resolveCliDirectory();
      final String pythonBinary = resolvePythonBinary();
      final String mainPythonScript = p.join(cliDirectory, 'main.py');

      final List<String> fullArguments = <String>[mainPythonScript, ...arguments];
      debugPrint('[CliBridgeService Config] Executing: $pythonBinary ${fullArguments.join(" ")}');

      final ProcessResult result = await Process.run(
        pythonBinary,
        fullArguments,
        workingDirectory: cliDirectory,
        runInShell: true,
      );

      debugPrint('[CliBridgeService Config Result] Exit: ${result.exitCode} | Out: ${result.stdout}');
      return result;
    } catch (exception) {
      debugPrint('[CliBridgeService Config Error] $exception');
      return null;
    }
  }
}
