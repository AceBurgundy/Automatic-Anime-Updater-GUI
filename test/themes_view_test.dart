import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kyaa_app/core/theme/app_palettes.dart';
import 'package:kyaa_app/core/theme/theme_controller.dart';
import 'package:kyaa_app/widgets/views/themes_view.dart';

void main() {
  group('ThemesView Tests', () {
    testWidgets('Renders all theme preview cards with zero layout overflow', (
      WidgetTester tester,
    ) async {
      tester.view.physicalSize = const Size(1000, 740);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);

      final ThemeController themeController = ThemeController();
      addTearDown(themeController.dispose);

      await tester.pumpWidget(
        MaterialApp(
          theme: themeController.currentThemeData,
          home: Scaffold(
            body: SizedBox(
              width: 952.0,
              height: 580.0,
              child: ThemesView(themeController: themeController),
            ),
          ),
        ),
      );
      await tester.pumpAndSettle();

      // Verify all theme titles are rendered
      for (final AppPaletteOption option in AppPaletteOption.values) {
        expect(find.text(option.displayName), findsOneWidget);
      }

      // Tap an unselected theme (e.g., Ocean Cyan)
      await tester.tap(find.text('Ocean Cyan'));

      // Progress through the snap-fade animation
      await tester.pump(const Duration(milliseconds: 70));
      await tester.pump(const Duration(milliseconds: 140));
      await tester.pumpAndSettle();

      // Verify active theme updated
      expect(themeController.activePalette, AppPaletteOption.oceanCyan);
    });
  });
}
