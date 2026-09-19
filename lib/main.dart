import 'dart:async';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:window_manager/window_manager.dart';

import 'core/constants/app_tokens.dart';
import 'core/services/cli_bridge_service.dart';
import 'core/theme/app_palettes.dart';
import 'core/theme/theme_controller.dart';
import 'widgets/navigation/app_title_bar.dart';
import 'widgets/navigation/tabbed_navigation.dart';
import 'widgets/views/scheduling_view.dart';
import 'widgets/views/settings_view.dart';
import 'widgets/views/tasks_view.dart';
import 'widgets/views/themes_view.dart';

/// Entry point for the Kyaa!! desktop application.
void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  unawaited(CliBridgeService.instance.loadInitialConfig());

  if (Platform.isWindows || Platform.isLinux || Platform.isMacOS) {
    await windowManager.ensureInitialized();

    const WindowOptions windowOptions = WindowOptions(
      size: Size(AppTokens.windowWidth, AppTokens.windowHeight),
      minimumSize: Size(AppTokens.windowWidth, AppTokens.windowHeight),
      maximumSize: Size(AppTokens.windowWidth, AppTokens.windowHeight),
      center: true,
      backgroundColor: Colors.transparent,
      skipTaskbar: false,
      titleBarStyle: TitleBarStyle.hidden,
      title: 'Kyaa!!',
    );

    windowManager.waitUntilReadyToShow(windowOptions, () async {
      await windowManager.show();
      await windowManager.focus();
      await windowManager.setResizable(false);
      await windowManager.setMaximizable(false);
    });
  }

  runApp(const KyaaApp());
}

/// Root application widget providing theme configuration and hosting the main scaffold.
class KyaaApp extends StatefulWidget {
  /// Creates a [KyaaApp] instance.
  const KyaaApp({super.key});

  @override
  State<KyaaApp> createState() => _KyaaAppState();
}

class _KyaaAppState extends State<KyaaApp> {
  /// Controller managing theme state and reactive palette notifications.
  late final ThemeController _themeController;

  @override
  void initState() {
    super.initState();
    _themeController = ThemeController();
  }

  @override
  void dispose() {
    _themeController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _themeController,
      builder: (BuildContext context, Widget? child) {
        return MaterialApp(
          title: 'Kyaa!!',
          debugShowCheckedModeBanner: false,
          theme: _themeController.currentThemeData,
          home: AppWindowScaffold(themeController: _themeController),
        );
      },
    );
  }
}

/// The main application window scaffold managing tabs and layout.
class AppWindowScaffold extends StatefulWidget {
  /// Creates an [AppWindowScaffold] widget.
  const AppWindowScaffold({
    super.key,
    required this.themeController,
    this.initialTab = AppTab.tasks,
  });

  /// The theme controller supplying active tokens and theme data.
  final ThemeController themeController;

  /// The initial tab to display.
  final AppTab initialTab;

  @override
  State<AppWindowScaffold> createState() => _AppWindowScaffoldState();
}

class _AppWindowScaffoldState extends State<AppWindowScaffold> {
  /// Currently active application view tab.
  late AppTab _activeTab;

  @override
  void initState() {
    super.initState();
    _activeTab = widget.initialTab;
  }

  @override
  Widget build(BuildContext context) {
    final AppColorTokens tokens = widget.themeController.tokens;

    return Scaffold(
      backgroundColor: tokens.background,
      body: Padding(
        padding: const EdgeInsets.all(AppTokens.windowPadding),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: <Widget>[
            AppTitleBar(
              tokens: tokens,
            ),
            const SizedBox(height: 12),
            TabbedNavigation(
              activeTab: _activeTab,
              tokens: tokens,
              onTabSelected: (AppTab tab) => setState(() => _activeTab = tab),
            ),
            const SizedBox(height: 14),
            Expanded(
              child: Container(
                decoration: BoxDecoration(
                  color: tokens.surfaceContainerLow,
                  borderRadius: BorderRadius.circular(AppTokens.cornerMedium),
                ),
                padding: const EdgeInsets.all(20.0),
                child: IndexedStack(
                  index: _activeTab.index,
                  children: <Widget>[
                    TasksView(tokens: tokens),
                    SettingsView(tokens: tokens),
                    SchedulingView(tokens: tokens),
                    ThemesView(themeController: widget.themeController),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
