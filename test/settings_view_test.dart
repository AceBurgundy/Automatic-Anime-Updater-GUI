import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kyaa_app/widgets/views/settings_view.dart';

void main() {
  group('SettingsView Tests', () {
    testWidgets('Renders all settings sections correctly including Preferred Quality and Audio Preference', (WidgetTester tester) async {
      tester.view.physicalSize = const Size(1000, 800);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);

      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: Padding(
              padding: EdgeInsets.all(16.0),
              child: SettingsView(),
            ),
          ),
        ),
      );
      await tester.pumpAndSettle();

      // Verify Section 1: Anime Folder
      expect(find.text('Anime Folder'), findsOneWidget);
      expect(find.text('D:/Anime/Animepahe_Library'), findsOneWidget);

      // Verify Section 2: AI Episode Parser
      expect(find.text('AI Episode Parser'), findsOneWidget);
      expect(find.text('Idle (Model Needed)'), findsOneWidget);

      // Verify Section 3: Preferred Quality (1080p to 360p)
      expect(find.text('Preferred Quality'), findsOneWidget);
      expect(find.text('1080p'), findsOneWidget);
      expect(find.text('720p'), findsOneWidget);
      expect(find.text('480p'), findsOneWidget);
      expect(find.text('360p'), findsOneWidget);

      // Verify Section 4: Audio Preference (Subbed, Dubbed)
      expect(find.text('Audio Preference'), findsOneWidget);
      expect(find.text('Subbed'), findsOneWidget);
      expect(find.text('Dubbed'), findsOneWidget);

      // Verify Pages to Scrape is NOT present
      expect(find.text('Pages to Scrape'), findsNothing);

      // Tap 720p to select
      await tester.tap(find.text('720p'));
      await tester.pumpAndSettle();

      // Tap 720p again (remains selected, cannot be null)
      await tester.tap(find.text('720p'));
      await tester.pumpAndSettle();

      // Tap Dubbed to select
      await tester.tap(find.text('Dubbed'));
      await tester.pumpAndSettle();

      // Tap Dubbed again (remains selected, cannot be null)
      await tester.tap(find.text('Dubbed'));
      await tester.pumpAndSettle();
    });
  });
}

