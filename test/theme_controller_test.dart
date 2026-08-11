import 'package:flutter_test/flutter_test.dart';
import 'package:kyaa_app/core/theme/app_palettes.dart';
import 'package:kyaa_app/core/theme/theme_controller.dart';

void main() {
  group('ThemeController Tests', () {
    test('Initial theme defaults to Mango Yellow', () {
      final ThemeController controller = ThemeController();
      expect(controller.activePalette, AppPaletteOption.sunsetAmber);
      expect(controller.tokens.primary, AppPalettes.sunsetAmber.primary);
    });

    test('All 4 palettes are defined correctly with valid tokens', () {
      for (final AppPaletteOption option in AppPaletteOption.values) {
        final AppColorTokens tokens = AppPalettes.getTokens(option);
        expect(tokens.primary, isNotNull);
        expect(tokens.background, isNotNull);
        expect(tokens.surfaceContainer, isNotNull);
        expect(tokens.toColorScheme().brightness, isNotNull);
      }
    });

    test('Switching theme notifies listeners', () {
      final ThemeController controller = ThemeController();
      bool notified = false;

      controller.addListener(() {
        notified = true;
      });

      controller.setPalette(AppPaletteOption.oceanCyan);
      expect(notified, isTrue);
      expect(controller.activePalette, AppPaletteOption.oceanCyan);
      expect(controller.tokens.primary, AppPalettes.oceanCyan.primary);

      // Switching to same palette should not notify
      notified = false;
      controller.setPalette(AppPaletteOption.oceanCyan);
      expect(notified, isFalse);
    });
  });
}
