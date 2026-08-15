import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:path/path.dart' as p;

/// Service managing execution of the background Python AI episode parser subprocess.
class AiSubprocessService {
  Process? _activeProcess;
  bool _isExecuting = false;

  /// Whether the AI parser subprocess is actively executing.
  bool get isExecuting => _isExecuting;

  /// Executes the AI episode parser script asynchronously with progress reporting.
  ///
  /// [onProgress] receives a normalized float progress value between 0.0 and 1.0.
  /// [onError] receives error message strings encountered during execution.
  /// [onComplete] is invoked upon successful model download and relocation.
  /// [scriptPath] optional custom relative or absolute path to parser.py.
  /// [destinationModelDir] optional target directory where completed model weights are moved.
  Future<void> executeParser({
    required void Function(double progress) onProgress,
    required void Function(String error) onError,
    required VoidCallback onComplete,
    String? scriptPath,
    String? destinationModelDir,
  }) async {
    if (_isExecuting) {
      onError('Parser is already running.');
      return;
    }

    _isExecuting = true;

    try {
      final Directory temporaryDirectory = Directory.systemTemp;
      final String targetScript = scriptPath ?? p.join('assets', 'scripts', 'parser.py');
      final String targetModelDir = destinationModelDir ?? p.join('assets', 'models');

      // Verify script exists or locate it relative to current working directory
      final File scriptFile = File(targetScript);
      final String resolvedScriptPath = scriptFile.existsSync()
          ? scriptFile.path
          : p.join(Directory.current.path, targetScript);

      // Detect Python binary: prioritize local venv (virtual environment) if available
      String pythonBinary = 'python';
      final File virtualEnvironmentPython = File(p.join(Directory.current.path, 'env', 'Scripts', 'python.exe'));
      if (virtualEnvironmentPython.existsSync()) {
        pythonBinary = virtualEnvironmentPython.path;
      }

      final Process process = await Process.start(
        pythonBinary,
        <String>[resolvedScriptPath, '--temp-dir', temporaryDirectory.path],
        runInShell: true,
      );

      _activeProcess = process;
      String? savedModelTempPath;

      process.stdout
          .transform(utf8.decoder)
          .transform(const LineSplitter())
          .listen((String line) {
            final String trimmedLine = line.trim();
            if (trimmedLine.startsWith('PROGRESS:')) {
              final List<String> progressParts = trimmedLine.split(':');
              if (progressParts.length > 1) {
                final double parsedProgressValue = double.tryParse(progressParts[1]) ?? 0.0;
                onProgress((parsedProgressValue / 100.0).clamp(0.0, 1.0));
              }
            } else if (trimmedLine.startsWith('MODEL_SAVED:')) {
              savedModelTempPath = trimmedLine.substring('MODEL_SAVED:'.length).trim();
            }
          });

      process.stderr
          .transform(utf8.decoder)
          .transform(const LineSplitter())
          .listen((String errorLine) {
            if (errorLine.trim().isNotEmpty) {
              onError(errorLine.trim());
            }
          });

      final int exitCode = await process.exitCode;
      _activeProcess = null;
      _isExecuting = false;

      if (exitCode == 0) {
        // Move completed payload to assets/models/
        try {
          final Directory modelsDirectory = Directory(targetModelDir);
          if (!modelsDirectory.existsSync()) {
            modelsDirectory.createSync(recursive: true);
          }

          if (savedModelTempPath != null && File(savedModelTempPath!).existsSync()) {
            final File temporaryModelFile = File(savedModelTempPath!);
            final String targetPath = p.join(modelsDirectory.path, p.basename(temporaryModelFile.path));
            temporaryModelFile.copySync(targetPath);
            temporaryModelFile.deleteSync();
          } else {
            // Fallback check in temporary directory
            final File expectedFile = File(p.join(temporaryDirectory.path, 'kyaa_ai_model.bin'));
            if (expectedFile.existsSync()) {
              final String targetPath = p.join(modelsDirectory.path, 'kyaa_ai_model.bin');
              expectedFile.copySync(targetPath);
              expectedFile.deleteSync();
            }
          }
        } catch (exception) {
          debugPrint('Notice moving model file: $exception');
        }

        onProgress(1.0);
        onComplete();
      } else {
        onError('Parser process exited with code $exitCode.');
      }
    } catch (exception) {
      _activeProcess = null;
      _isExecuting = false;
      onError(exception.toString());
    }
  }

  /// Cancels any currently running AI parser subprocess.
  void cancel() {
    if (_activeProcess != null) {
      try {
        _activeProcess!.kill(ProcessSignal.sigkill);
      } catch (_) {}
      _activeProcess = null;
      _isExecuting = false;
    }
  }
}

