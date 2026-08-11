import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kyaa_app/widgets/views/tasks_view.dart';

void main() {
  group('TaskItemData Model & Stream Map Schema Tests', () {
    test('TaskItemData converts from and to stream map correctly', () {
      final Map<String, Object?> rawMap = <String, Object?>{
        'id': 'test_stream_task',
        'string_event': 'download_update',
        'string_timestamp': '2026-09-07T23:20:00Z',
        'string_anime_name': 'Sousou no Frieren',
        'int_episode_number': 1,
        'string_filename': '[SubsPlease] Sousou no Frieren - 01 (1080p) [BD].mkv',
        'string_download_status': 'in-progress',
        'float_progress_percentage': 75.5,
        'int_downloaded_bytes': 1057000000,
        'int_total_bytes': 1400000000,
        'float_speed_mbps': 18.2,
        'string_short_error_message': '',
        'string_error_log_message': '',
      };

      final TaskItemData task = TaskItemData.fromMap(rawMap);

      expect(task.id, 'test_stream_task');
      expect(task.stringEvent, 'download_update');
      expect(task.stringTimestamp, '2026-09-07T23:20:00Z');
      expect(task.stringAnimeName, 'Sousou no Frieren');
      expect(task.intEpisodeNumber, 1);
      expect(task.title, 'Sousou no Frieren - Episode 01');
      expect(task.progress, 0.755);
      expect(task.state, TaskDownloadState.running);
      expect(task.isFailed, isFalse);

      final Map<String, Object?> outputMap = task.toMap();
      expect(outputMap['id'], 'test_stream_task');
      expect(outputMap['string_anime_name'], 'Sousou no Frieren');
      expect(outputMap['float_progress_percentage'], 75.5);
      expect(outputMap['float_speed_mbps'], 18.2);
    });

    test('TaskItemData correctly maps failed status and error message', () {
      final TaskItemData failedTask = TaskItemData.fromMap(const <String, Object?>{
        'id': 'failed_1',
        'string_anime_name': 'Cyberpunk: Edgerunners',
        'int_episode_number': 6,
        'string_download_status': 'failed',
        'string_short_error_message': 'Connection timed out',
        'string_error_log_message': 'Traceback:\nsocket timeout',
      });

      expect(failedTask.isFailed, isTrue);
      expect(failedTask.state, TaskDownloadState.failed);
      expect(failedTask.stringShortErrorMessage, 'Connection timed out');
    });
  });

  group('TasksView Widget Tests', () {
    testWidgets('TasksView renders tasks, expands item, and displays stream metadata', (WidgetTester tester) async {
      tester.view.physicalSize = const Size(1000, 800);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);

      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: Padding(
              padding: EdgeInsets.all(16.0),
              child: TasksView(),
            ),
          ),
        ),
      );
      await tester.pumpAndSettle();

      // Verify collapsed tasks are visible
      expect(find.text('Sousou no Frieren - Episode 01'), findsOneWidget);
      expect(find.text('Bocchi the Rock! - Episode 08'), findsOneWidget);
      expect(find.text('Chainsaw Man - Episode 04'), findsOneWidget);
      expect(find.text('Cyberpunk: Edgerunners - Episode 06'), findsOneWidget);

      // Verify dropdown expand icons exist
      final Finder expandButtons = find.byIcon(Icons.keyboard_arrow_down_rounded);
      expect(expandButtons, findsNWidgets(4));

      // Expand the first task
      await tester.tap(expandButtons.first);
      await tester.pumpAndSettle();

      // Verify stream details are shown inside extended area
      expect(find.text('Completed'), findsWidgets);
      expect(find.text('Event: download_update'), findsWidgets);

      // Expand the failed task (last one)
      await tester.tap(expandButtons.last);
      await tester.pumpAndSettle();

      // Verify error banner and terminal icon button appear
      expect(find.text('Connection reset by peer while downloading stream chunk #42'), findsOneWidget);
      expect(find.byIcon(Icons.terminal_rounded), findsOneWidget);

      // Tap the terminal log button
      await tester.tap(find.byIcon(Icons.terminal_rounded));
      await tester.pumpAndSettle();
    });

    testWidgets('TasksView search filtering works accurately', (WidgetTester tester) async {
      tester.view.physicalSize = const Size(1000, 800);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);

      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: Padding(
              padding: EdgeInsets.all(16.0),
              child: TasksView(),
            ),
          ),
        ),
      );
      await tester.pumpAndSettle();

      // Enter search query
      await tester.enterText(find.byType(TextField), 'Bocchi');
      await tester.pumpAndSettle();

      // Only Bocchi the Rock should be displayed
      expect(find.text('Bocchi the Rock! - Episode 08'), findsOneWidget);
      expect(find.text('Sousou no Frieren - Episode 01'), findsNothing);
    });
  });
}
