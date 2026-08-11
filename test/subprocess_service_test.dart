import 'package:flutter_test/flutter_test.dart';
import 'package:kyaa_app/core/services/subprocess_service.dart';

void main() {
  group('SubprocessService Tests', () {
    test('Template hooks execute successfully without exception', () async {
      final SubprocessService service = SubprocessService.instance;

      expect(() => service.startTasks(), returnsNormally);
      expect(() => service.pauseTasks(), returnsNormally);
      expect(() => service.browseAnimeFolder(), returnsNormally);
      expect(() => service.downloadAiParserModel(), returnsNormally);
      expect(
        () => service.startAutomationSchedule(
          activeDays: const <String>['Monday', 'Tuesday'],
          triggerTimes: const <String>['04:00', '12:30'],
        ),
        returnsNormally,
      );
      expect(() => service.addTriggerTime('18:00'), returnsNormally);
      expect(() => service.removeTriggerTime('04:00'), returnsNormally);
      expect(() => service.openErrorLog('task_1'), returnsNormally);
      expect(() => service.setPreferredQuality('720p'), returnsNormally);
      expect(() => service.setPreferredAudio('Dubbed'), returnsNormally);
      expect(() => service.setPagesToScrape(5), returnsNormally);
    });
  });
}
