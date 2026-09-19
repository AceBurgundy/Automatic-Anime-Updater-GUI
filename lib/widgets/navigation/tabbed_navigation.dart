import 'package:flutter/material.dart';
import '../../core/constants/app_tokens.dart';
import '../../core/theme/app_palettes.dart';

/// Available tabs in the application navigation bar.
enum AppTab {
  /// Tasks view tab.
  tasks('Tasks', Icons.checklist_rounded),

  /// Settings view tab.
  settings('Settings', Icons.settings_rounded),

  /// Scheduling view tab.
  scheduling('Scheduling', Icons.schedule_rounded),

  /// Themes view tab.
  themes('Themes', Icons.palette_rounded);

  const AppTab(this.label, this.icon);

  /// Display text label.
  final String label;

  /// Header icon data.
  final IconData icon;
}

/// Full-width pill tab bar matching .tabbed-navigation in single.html.
/// Features direct active tab selection with smooth hover background fading.
class TabbedNavigation extends StatelessWidget {
  /// Creates a [TabbedNavigation] widget.
  const TabbedNavigation({
    super.key,
    required this.activeTab,
    required this.onTabSelected,
    this.tokens,
  });

  /// Currently selected [AppTab].
  final AppTab activeTab;

  /// Callback invoked when a tab is selected.
  final ValueChanged<AppTab> onTabSelected;

  /// Optional active theme color tokens.
  final AppColorTokens? tokens;

  @override
  Widget build(BuildContext context) {
    final ThemeData theme = Theme.of(context);
    final ColorScheme colorScheme = theme.colorScheme;
    final Color backgroundColor = tokens?.surfaceContainerLow ?? colorScheme.surfaceContainerLow;

    return Container(
      width: double.infinity,
      height: AppTokens.tabBarHeight,
      decoration: BoxDecoration(
        color: backgroundColor,
        borderRadius: BorderRadius.circular(AppTokens.cornerFull),
      ),
      clipBehavior: Clip.antiAlias,
      padding: EdgeInsets.zero,
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: AppTab.values.map((AppTab tab) {
          final bool isActive = tab == activeTab;
          return Expanded(
            child: _TabButton(
              tab: tab,
              isActive: isActive,
              tokens: tokens,
              onTap: () => onTabSelected(tab),
            ),
          );
        }).toList(),
      ),
    );
  }
}

/// Internal widget representing an individual tab item within [TabbedNavigation].
class _TabButton extends StatefulWidget {
  /// Creates a [_TabButton] widget.
  const _TabButton({
    required this.tab,
    required this.isActive,
    required this.onTap,
    this.tokens,
  });

  /// Associated tab identifier and metadata.
  final AppTab tab;

  /// Whether this tab is currently the active tab.
  final bool isActive;

  /// Callback executed when the user taps on this tab.
  final VoidCallback onTap;

  /// Optional theme color tokens.
  final AppColorTokens? tokens;

  @override
  State<_TabButton> createState() => _TabButtonState();
}

class _TabButtonState extends State<_TabButton> {
  /// Whether the pointer is currently hovering over this tab button.
  bool _isHovered = false;

  @override
  Widget build(BuildContext context) {
    final ThemeData theme = Theme.of(context);
    final ColorScheme colorScheme = theme.colorScheme;
    final AppColorTokens? tokens = widget.tokens;

    final Color foregroundColor = widget.isActive
        ? (tokens?.onPrimary ?? colorScheme.onPrimary)
        : (_isHovered
            ? (tokens?.onSurface ?? colorScheme.onSurface)
            : (tokens?.onSurfaceVariant ?? colorScheme.onSurfaceVariant));

    final Color tabBackgroundColor = widget.isActive
        ? (tokens?.primary ?? colorScheme.primary)
        : (_isHovered
            ? (tokens?.surfaceContainerHigh ?? colorScheme.surfaceContainerHigh)
            : Colors.transparent);

    const FontWeight weight = FontWeight.w500;

    return MouseRegion(
      cursor: SystemMouseCursors.click,
      onEnter: (_) => setState(() => _isHovered = true),
      onExit: (_) => setState(() => _isHovered = false),
      child: GestureDetector(
        onTap: widget.onTap,
        behavior: HitTestBehavior.opaque,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 220),
          curve: Curves.easeInOutCubic,
          height: double.infinity,
          decoration: BoxDecoration(
            color: tabBackgroundColor,
            borderRadius: BorderRadius.circular(AppTokens.cornerFull),
          ),
          alignment: Alignment.center,
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.center,
            children: <Widget>[
              Icon(
                widget.tab.icon,
                size: 20.0,
                color: foregroundColor,
              ),
              const SizedBox(width: 10.0),
              Text(
                widget.tab.label,
                style: const TextStyle(
                  fontFamily: AppTokens.fontFamily,
                  fontSize: 14.5,
                  fontWeight: weight,
                  color: null,
                ).copyWith(color: foregroundColor),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
