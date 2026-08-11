import 'dart:io';
import 'dart:typed_data';
import 'dart:ui' as ui;
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kyaa_app/core/constants/app_tokens.dart';
import 'package:kyaa_app/core/theme/theme_controller.dart';
import 'package:kyaa_app/main.dart';
import 'package:kyaa_app/widgets/navigation/tabbed_navigation.dart';

Future<void> _loadFonts() async {
  try {
    final FontLoader googleSansLoader = FontLoader('GoogleSans');
    final File regularFile = File('assets/fonts/GoogleSans-Regular.ttf');
    if (regularFile.existsSync()) {
      googleSansLoader.addFont(Future.value(ByteData.view(regularFile.readAsBytesSync().buffer)));
    }
    final File mediumFile = File('assets/fonts/GoogleSans-Medium.ttf');
    if (mediumFile.existsSync()) {
      googleSansLoader.addFont(Future.value(ByteData.view(mediumFile.readAsBytesSync().buffer)));
    }
    final File boldFile = File('assets/fonts/GoogleSans-Bold.ttf');
    if (boldFile.existsSync()) {
      googleSansLoader.addFont(Future.value(ByteData.view(boldFile.readAsBytesSync().buffer)));
    }
    await googleSansLoader.load();

    final FontLoader monospaceLoader = FontLoader('monospace');
    if (regularFile.existsSync()) {
      monospaceLoader.addFont(Future.value(ByteData.view(regularFile.readAsBytesSync().buffer)));
      await monospaceLoader.load();
    }
  } catch (_) {}

  try {
    final FontLoader materialIconsLoader = FontLoader('MaterialIcons');
    final File iconFile = File(
      'D:/Documents/Programming/Frameworks/Flutter/fvm/default/bin/cache/dart-sdk/bin/resources/devtools/assets/fonts/MaterialIcons-Regular.otf',
    );
    if (iconFile.existsSync()) {
      materialIconsLoader.addFont(Future.value(ByteData.view(iconFile.readAsBytesSync().buffer)));
      await materialIconsLoader.load();
    }
  } catch (_) {}
}

void main() {
  testWidgets('Generate 4 tab UI screenshot images with rounded corners', (WidgetTester tester) async {
    await _loadFonts();

    tester.view.physicalSize = const Size(1000, 740);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    final ThemeController themeController = ThemeController();

    final List<AppTab> tabs = <AppTab>[
      AppTab.tasks,
      AppTab.settings,
      AppTab.scheduling,
      AppTab.themes,
    ];

    for (final AppTab tab in tabs) {
      final GlobalKey repaintKey = GlobalKey();

      await tester.pumpWidget(
        MaterialApp(
          key: ValueKey<String>('app_${tab.name}'),
          debugShowCheckedModeBanner: false,
          theme: themeController.currentThemeData,
          home: Scaffold(
            backgroundColor: Colors.transparent,
            body: Center(
              child: RepaintBoundary(
                key: repaintKey,
                child: SizedBox(
                  width: 1000,
                  height: 740,
                  child: ClipRRect(
                    borderRadius: BorderRadius.circular(AppTokens.cornerExtraLarge),
                    child: AppWindowScaffold(
                      key: ValueKey<AppTab>(tab),
                      themeController: themeController,
                      initialTab: tab,
                    ),
                  ),
                ),
              ),
            ),
          ),
        ),
      );

      await tester.pump(const Duration(milliseconds: 300));

      final RenderRepaintBoundary boundary =
          repaintKey.currentContext!.findRenderObject() as RenderRepaintBoundary;

      await tester.runAsync(() async {
        final ui.Image image = await boundary.toImage(pixelRatio: 1.0);
        final ByteData? byteData = await image.toByteData(format: ui.ImageByteFormat.png);
        expect(byteData, isNotNull);

        final Uint8List pngBytes = byteData!.buffer.asUint8List();
        final String fileName = '${tab.name}.png';

        // Save in kyaa_app/images/
        final File localFile = File('images/$fileName');
        localFile.parent.createSync(recursive: true);
        localFile.writeAsBytesSync(pngBytes);

        // Also save in root images/ if accessible
        try {
          final File rootFile = File('../images/$fileName');
          rootFile.parent.createSync(recursive: true);
          rootFile.writeAsBytesSync(pngBytes);
        } catch (_) {}

        // Also save with descriptive names (e.g. tasks_tab.png)
        final File descriptiveFile = File('images/${tab.name}_tab.png');
        descriptiveFile.writeAsBytesSync(pngBytes);
        try {
          final File rootDescriptiveFile = File('../images/${tab.name}_tab.png');
          rootDescriptiveFile.writeAsBytesSync(pngBytes);
        } catch (_) {}
      });
    }
  });
}
