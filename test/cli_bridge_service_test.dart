import 'dart:convert';
import 'package:flutter_test/flutter_test.dart';
import 'package:kyaa_app/core/services/cli_bridge_service.dart';
import 'package:kyaa_app/widgets/views/tasks_view.dart';

void main() {
  group('CliBridgeService Tests', () {
    test('Singleton instance initializes correctly', () {
      final CliBridgeService instance1 = CliBridgeService.instance;
      final CliBridgeService instance2 = CliBridgeService.instance;
      expect(identical(instance1, instance2), isTrue);
      expect(instance1.isAutomationRunning, isFalse);
      expect(instance1.tasksNotifier.value, isEmpty);
      expect(instance1.isExecutingNotifier.value, isFalse);
    });

    test('resolveCliDirectory returns valid non-empty path', () {
      final String cliDir = CliBridgeService.instance.resolveCliDirectory();
      expect(cliDir, isNotEmpty);
      expect(cliDir.contains('backend') || cliDir.contains('anime-refresher-cli'), isTrue);
    });

    test('resolvePythonBinary returns valid string', () {
      final String pythonBin = CliBridgeService.instance.resolvePythonBinary();
      expect(pythonBin, isNotEmpty);
    });

    test('CliConfigState copyWith works as expected', () {
      const CliConfigState initial = CliConfigState(
        targetDirectory: 'C:/Anime',
        preferredQuality: '1080p',
        preferredAudio: 'Subbed',
        isModelInstalled: false,
        modelSizeMb: 0.0,
      );

      final CliConfigState updated = initial.copyWith(
        preferredQuality: '720p',
        preferredAudio: 'Dubbed',
        isModelInstalled: true,
        modelSizeMb: 1250.5,
      );

      expect(updated.targetDirectory, 'C:/Anime');
      expect(updated.preferredQuality, '720p');
      expect(updated.preferredAudio, 'Dubbed');
      expect(updated.isModelInstalled, isTrue);
      expect(updated.modelSizeMb, 1250.5);
    });

    test('TaskItemData properly deserializes and exposes formatted values', () {
      final Map<String, Object?> streamPayload = <String, Object?>{
        'string_event': 'download_update',
        'string_timestamp': '2026-09-11T12:00:00Z',
        'string_anime_name': 'Solo Leveling',
        'int_episode_number': 12,
        'string_filename': 'Solo Leveling 12.mp4',
        'string_download_status': 'in-progress',
        'float_progress_percentage': 85.5,
        'int_downloaded_bytes': 855000000,
        'int_total_bytes': 1000000000,
        'float_speed_mbps': 18.4,
        'string_short_error_message': '',
        'string_error_log_message': '',
      };

      final TaskItemData item = TaskItemData.fromMap(streamPayload, id: 'solo_leveling_ep12');

      expect(item.id, 'solo_leveling_ep12');
      expect(item.stringAnimeName, 'Solo Leveling');
      expect(item.intEpisodeNumber, 12);
      expect(item.title, 'Solo Leveling - Episode 12');
      expect(item.progress, closeTo(0.855, 0.001));
      expect(item.isFailed, isFalse);
      expect(item.state, TaskDownloadState.running);
      expect(item.floatSpeedMbps, 18.4);
    });

    test('TaskItemData handles failed status and error logs', () {
      final Map<String, Object?> streamPayload = <String, Object?>{
        'string_event': 'download_update',
        'string_timestamp': '2026-09-11T12:05:00Z',
        'string_anime_name': 'Clockwork Planet',
        'int_episode_number': 3,
        'string_filename': 'Clockwork Planet 03.mp4',
        'string_download_status': 'failed',
        'float_progress_percentage': 40.0,
        'int_downloaded_bytes': 400000000,
        'int_total_bytes': 1000000000,
        'float_speed_mbps': 0.0,
        'string_short_error_message': 'Network socket timed out',
        'string_error_log_message': 'Traceback (most recent call last):\nTimeoutError',
      };

      final TaskItemData item = TaskItemData.fromMap(streamPayload, id: 'clockwork_planet_ep3');

      expect(item.isFailed, isTrue);
      expect(item.state, TaskDownloadState.failed);
      expect(item.stringShortErrorMessage, 'Network socket timed out');
      expect(item.stringErrorLogMessage.contains('TimeoutError'), isTrue);
    });

    test('loadInitialConfig loads without uncaught exceptions', () async {
      await CliBridgeService.instance.loadInitialConfig();
      expect(CliBridgeService.instance.configNotifier.value.preferredQuality, isNotEmpty);
      expect(CliBridgeService.instance.configNotifier.value.preferredAudio, isNotEmpty);
    });
  });
}
