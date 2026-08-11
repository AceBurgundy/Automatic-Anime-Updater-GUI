import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kyaa_app/main.dart';

void main() {
  testWidgets('KyaaApp smoke test: renders Title Bar, Tab Bar, and Tasks View', (WidgetTester tester) async {
    tester.view.physicalSize = const Size(1000, 740);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(const KyaaApp());
    await tester.pumpAndSettle();

    // Verify Title Bar
    expect(find.text('Kyaa!!'), findsOneWidget);
    expect(find.byTooltip('Minimize'), findsOneWidget);
    expect(find.byTooltip('Close'), findsOneWidget);

    // Verify Tabs
    expect(find.text('Tasks'), findsOneWidget);
    expect(find.text('Settings'), findsOneWidget);
    expect(find.text('Scheduling'), findsOneWidget);
    expect(find.text('Themes'), findsOneWidget);

    // Verify Tasks View elements
    expect(find.text('Search episode tasks...'), findsOneWidget);
    expect(find.text('Sousou no Frieren - Episode 01'), findsOneWidget);

    // Switch to Themes tab and verify
    await tester.tap(find.text('Themes'));
    await tester.pumpAndSettle();

    expect(find.text('Purple Iris'), findsOneWidget);
    expect(find.text('Ocean Cyan'), findsOneWidget);
  });
}
