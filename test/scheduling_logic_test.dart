import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kyaa_app/widgets/views/scheduling_view.dart';

void main() {
  group('SchedulingView Tests', () {
    testWidgets('Toggling Everyday checkbox selects all day buttons and displays 12h times', (WidgetTester tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: SchedulingView(),
          ),
        ),
      );

      expect(find.text('Active Days'), findsOneWidget);
      expect(find.text('Trigger Times'), findsOneWidget);
      expect(find.text('Everyday'), findsOneWidget);

      expect(find.text('04:00 AM'), findsOneWidget);
      expect(find.text('12:30 PM'), findsOneWidget);
      expect(find.text('08:00 PM'), findsOneWidget);

      // Initially all 7 days are active and Everyday is checked
      expect(find.byIcon(Icons.check_rounded), findsOneWidget);

      // Clicking an active day (e.g. 'M') unchecks that day and unchecks Everyday consecutively
      await tester.tap(find.text('M'));
      await tester.pumpAndSettle();

      // Everyday checkbox check icon should no longer be rendered
      expect(find.byIcon(Icons.check_rounded), findsNothing);

      // Clicking 'M' again reactivates Monday, so all 7 days are active -> Everyday becomes checked again
      await tester.tap(find.text('M'));
      await tester.pumpAndSettle();

      expect(find.byIcon(Icons.check_rounded), findsOneWidget);

      // Clicking Everyday unchecks all days
      await tester.tap(find.text('Everyday'));
      await tester.pumpAndSettle();
      expect(find.byIcon(Icons.check_rounded), findsNothing);

      // Clicking Everyday again re-checks all days
      await tester.tap(find.text('Everyday'));
      await tester.pumpAndSettle();
      expect(find.byIcon(Icons.check_rounded), findsOneWidget);
    });
  });
}
