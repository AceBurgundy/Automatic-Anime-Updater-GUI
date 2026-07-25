import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:path/path.dart' as p;
import '../../widgets/views/tasks_view.dart';

/// Configuration state loaded from the backend CLI.
class CliConfigState {
  const CliConfigState({
    this.targetDirectory = '',
    this.preferredQuality = '1080p',
    this.preferredAudio = 'Subbed',
    this.isModelInstalled = false,
    this.modelSizeMb = 0.0,
    this.folderAsTitle = true,
  });

  final String targetDirectory;
  final String preferredQuality;
  final String preferredAudio;
  final bool isModelInstalled;
  final double modelSizeMb;
  final bool folderAsTitle;

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
  CliBridgeService._();

  /// Shared singleton instance of [CliBridgeService].
  static final CliBridgeService instance = CliBridgeService._();

  Process? _activeAutomationProcess;
  Process? _activeModelProcess;
  bool _isAutomationRunning = false;

  final StreamController<TaskItemData> _taskEventController =
      StreamController<TaskItemData>.broadcast();

  final ValueNotifier<List<TaskItemData>> _tasksNotifier =
      ValueNotifier<List<TaskItemData>>(<TaskItemData>[]);

  final ValueNotifier<bool> _isExecutingNotifier = ValueNotifier<bool>(false);

  final ValueNotifier<CliConfigState> _configNotifier =
      ValueNotifier<CliConfigState>(const CliConfigState());

  /// Stream of live episode task updates emitted from the CLI engine.
  Stream<TaskItemData> get taskEvents => _taskEventController.stream;

  /// Reactive list of all accumulated and active tasks.
  ValueListenable<List<TaskItemData>> get tasksNotifier => _tasksNotifier;

  /// Reactive boolean indicating if the automation engine is actively running.
  ValueListenable<bool> get isExecutingNotifier => _isExecutingNotifier;

  /// Reactive configuration state.
  ValueListenable<CliConfigState> get configNotifier => _configNotifier;

  /// Whether the automation engine is currently executing.
  bool get isAutomationRunning => _isAutomationRunning;

  /// Resolves the directory path of the backend Python CLI engine.
  String resolveCliDirectory() {
    // 1. Environment variable override
    final String? envOverride = Platform.environment['KYAA_BACKEND_DIR'] ??
        Platform.environment['KYAA_CLI_DIR'] ??
        Platform.environment['ANIME_REFRESHER_CLI_DIR'];
    if (envOverride != null && Directory(envOverride).existsSync()) {
      return envOverride;
    }

    // 2. Check child backend directory (monorepo structure)
    final String childBackend = p.normalize(p.join(Directory.current.path, 'backend'));
    if (Directory(childBackend).existsSync()) {
      return childBackend;
    }

    // 3. Check child anime-refresher-cli directory (legacy)
    final String childCli = p.normalize(p.join(Directory.current.path, 'anime-refresher-cli'));
    if (Directory(childCli).existsSync()) {
      return childCli;
    }

    // 4. Check sibling backend directory
    final String siblingBackend = p.normalize(p.join(Directory.current.path, '..', 'backend'));
    if (Directory(siblingBackend).existsSync()) {
      return siblingBackend;
    }

    // 5. Check sibling anime-refresher-cli directory
    final String siblingCli = p.normalize(p.join(Directory.current.path, '..', 'anime-refresher-cli'));
    if (Directory(siblingCli).existsSync()) {
      return siblingCli;
    }

    // 6. Check consolidated Flutter project path
    final Directory consolidatedDir = Directory(r'D:\Documents\Programming\Frameworks\Flutter\projects\kyaa_anime_refresher\backend');
    if (consolidatedDir.existsSync()) {
      return consolidatedDir.path;
    }

    // 7. Check standalone Automation CLI path
    final Directory standaloneDir = Directory(r'D:\Documents\Programming\Languages\Python\Automation\anime-refresher-cli');
    if (standaloneDir.existsSync()) {
      return standaloneDir.path;
    }

    // 8. Fallback to default path
    return r'D:\Documents\Programming\Frameworks\Flutter\projects\kyaa_anime_refresher\backend';
  }

  /// Resolves the Python binary (prioritizing the local virtual environment).
  String resolvePythonBinary() {
    final String cliDir = resolveCliDirectory();

    // Prioritize CLI virtual environment Python (env, .venv, venv)
    final File envPython = File(p.join(cliDir, 'env', 'Scripts', 'python.exe'));
    if (envPython.existsSync()) {
      return envPython.path;
    }

    final File dotVenvPython = File(p.join(cliDir, '.venv', 'Scripts', 'python.exe'));
    if (dotVenvPython.existsSync()) {
      return dotVenvPython.path;
    }

    final File altVenvPython = File(p.join(cliDir, 'venv', 'Scripts', 'python.exe'));
    if (altVenvPython.existsSync()) {
      return altVenvPython.path;
    }

    // Local kyaa_app env fallback
    final File localEnvPython = File(p.join(Directory.current.path, 'env', 'Scripts', 'python.exe'));
    if (localEnvPython.existsSync()) {
      return localEnvPython.path;
    }

    return 'python';
  }

  /// Loads initial configuration from the CLI `.env` file and model directory.
  Future<void> loadInitialConfig() async {
    try {
      final String cliDir = resolveCliDirectory();
      final File envFile = File(p.join(cliDir, '.env'));
      String targetDir = r'D:\Videos\Anime Unwatched';
      String quality = '1080p';
      String audio = 'Subbed';

      if (envFile.existsSync()) {
        final List<String> lines = await envFile.readAsLines();
        for (final String line in lines) {
          final String trimmed = line.trim();
          if (trimmed.startsWith('TARGET_DIR=')) {
            targetDir = trimmed.substring('TARGET_DIR='.length).trim();
          } else if (trimmed.startsWith('PREFERRED_RESOLUTION=')) {
            final String rawRes = trimmed.substring('PREFERRED_RESOLUTION='.length).trim().replaceAll('p', '');
            quality = '${rawRes}p';
          } else if (trimmed.startsWith('AUDIO_PREFERENCE=')) {
            final String rawAudio = trimmed.substring('AUDIO_PREFERENCE='.length).trim().toLowerCase();
            audio = rawAudio.contains('dub') ? 'Dubbed' : 'Subbed';
          }
        }
      }

      // Check model file presence
      final Directory modelsDir = Directory(p.join(cliDir, 'models'));
      bool modelPresent = false;
      double modelSizeMb = 0.0;
      if (modelsDir.existsSync()) {
        final List<FileSystemEntity> entities = modelsDir.listSync();
        for (final FileSystemEntity entity in entities) {
          if (entity is File && entity.path.endsWith('.gguf')) {
            modelPresent = true;
            modelSizeMb = entity.lengthSync() / (1024 * 1024);
            break;
          }
        }
      }

      _configNotifier.value = CliConfigState(
        targetDirectory: targetDir,
        preferredQuality: quality,
        preferredAudio: audio,
        isModelInstalled: modelPresent,
        modelSizeMb: modelSizeMb,
      );
    } catch (e) {
      debugPrint('[CliBridgeService] Notice loading initial config: $e');
    }
  }

  /// Starts the automation pipeline subprocess in real-time stream mode.
  Future<void> startAutomation({
    bool synchronizePosters = true,
    String? preferredResolution,
    int? maxDownloads,
    bool dryRun = false,
  }) async {
    if (_isAutomationRunning) {
      debugPrint('[CliBridgeService] Automation is already active.');
      return;
    }

    final String cliDir = resolveCliDirectory();
    final String pythonBin = resolvePythonBinary();
    final String mainPy = p.join(cliDir, 'main.py');

    final List<String> args = <String>[
      mainPy,
      '--start-automation-stream',
    ];

    if (synchronizePosters) {
      args.add('--synchronize-posters');
    }

    if (preferredResolution != null && preferredResolution.isNotEmpty) {
      args.addAll(<String>[
        '--preferred-resolution',
        preferredResolution.replaceAll('p', ''),
      ]);
    }

    if (maxDownloads != null && maxDownloads > 0) {
      args.addAll(<String>['--maximum-downloads', maxDownloads.toString()]);
    }

    if (dryRun) {
      args.add('--dry-run');
    }

    debugPrint('[CliBridgeService] Launching automation: $pythonBin ${args.join(" ")}');

    _isAutomationRunning = true;
    _isExecutingNotifier.value = true;

    try {
      final Process process = await Process.start(
        pythonBin,
        args,
        workingDirectory: cliDir,
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
            (String errLine) {
              if (errLine.trim().isNotEmpty) {
                debugPrint('[CliBridgeService StdErr] $errLine');
              }
            },
          );

      final int exitCode = await process.exitCode;
      debugPrint('[CliBridgeService] Automation process concluded with code $exitCode');
    } catch (e) {
      debugPrint('[CliBridgeService] Failed to start automation process: $e');
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
        final int epNum = (map['int_episode_number'] as num?)?.toInt() ?? 0;
        final String generatedId = '${animeName.toLowerCase().replaceAll(RegExp(r'[^a-z0-9]'), '_')}_ep$epNum';

        final TaskItemData item = TaskItemData.fromMap(map, id: generatedId);

        // Notify stream subscribers
        _taskEventController.add(item);

        // Update accumulated tasks list
        final List<TaskItemData> currentList = List<TaskItemData>.from(_tasksNotifier.value);
        final int existingIndex = currentList.indexWhere((TaskItemData t) => t.id == item.id);

        if (existingIndex >= 0) {
          currentList[existingIndex] = item;
        } else {
          currentList.insert(0, item);
        }

        _tasksNotifier.value = currentList;
      }
    } catch (e) {
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
      } catch (e) {
        debugPrint('[CliBridgeService] Error killing automation process: $e');
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
    final String cliDir = resolveCliDirectory();
    final String pythonBin = resolvePythonBinary();
    final String mainPy = p.join(cliDir, 'main.py');

    debugPrint('[CliBridgeService] Invoking model download: $pythonBin $mainPy --download-model');

    try {
      final Process process = await Process.start(
        pythonBin,
        <String>[mainPy, '--download-model'],
        workingDirectory: cliDir,
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
            final RegExp pctRegex = RegExp(r'(\d+(?:\.\d+)?)\s*%');
            final Match? match = pctRegex.firstMatch(trimmed);
            if (match != null) {
              final double? pct = double.tryParse(match.group(1) ?? '');
              if (pct != null) {
                onProgress((pct / 100.0).clamp(0.0, 1.0));
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
          .listen((String errLine) {
            if (errLine.trim().isNotEmpty) onError(errLine.trim());
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
    } catch (e) {
      _activeModelProcess = null;
      onError(e.toString());
    }
  }

  /// Cancels any active model download subprocess.
  void cancelModelDownload() {
    if (_activeModelProcess != null) {
      try {
        _activeModelProcess!.kill(ProcessSignal.sigkill);
      } catch (_) {}
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

  /// Toggles folder-indexed template (`<Folder Name> <01>.<ext>`) in SQLite.
  Future<void> setFolderAsTitle(bool enabled) async {
    await _executeCliConfigCommand(<String>[
      enabled ? '--set-folder-as-title' : '--unset-folder-as-title'
    ]);
    _configNotifier.value = _configNotifier.value.copyWith(folderAsTitle: enabled);
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
  Future<ProcessResult?> _executeCliConfigCommand(List<String> args) async {
    try {
      final String cliDir = resolveCliDirectory();
      final String pythonBin = resolvePythonBinary();
      final String mainPy = p.join(cliDir, 'main.py');

      final List<String> fullArgs = <String>[mainPy, ...args];
      debugPrint('[CliBridgeService Config] Executing: $pythonBin ${fullArgs.join(" ")}');

      final ProcessResult result = await Process.run(
        pythonBin,
        fullArgs,
        workingDirectory: cliDir,
        runInShell: true,
      );

      debugPrint('[CliBridgeService Config Result] Exit: ${result.exitCode} | Out: ${result.stdout}');
      return result;
    } catch (e) {
      debugPrint('[CliBridgeService Config Error] $e');
      return null;
    }
  }
}
