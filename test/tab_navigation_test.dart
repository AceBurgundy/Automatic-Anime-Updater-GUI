import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kyaa_app/widgets/navigation/tabbed_navigation.dart';

void main() {
  group('TabbedNavigation Tests', () {
    testWidgets('Renders all 4 tabs and handles tab selection', (WidgetTester tester) async {
      AppTab selectedTab = AppTab.tasks;

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: StatefulBuilder(
              builder: (BuildContext context, StateSetter setState) {
                return TabbedNavigation(
                  activeTab: selectedTab,
                  onTabSelected: (AppTab tab) {
                    setState(() {
                      selectedTab = tab;
                    });
                  },
                );
              },
            ),
          ),
        ),
      );

      expect(find.text('Tasks'), findsOneWidget);
      expect(find.text('Settings'), findsOneWidget);
      expect(find.text('Scheduling'), findsOneWidget);
      expect(find.text('Themes'), findsOneWidget);

      await tester.tap(find.text('Settings'));
      await tester.pumpAndSettle();
      expect(selectedTab, AppTab.settings);

      await tester.tap(find.text('Themes'));
      await tester.pumpAndSettle();
      expect(selectedTab, AppTab.themes);
    });
  });
}
