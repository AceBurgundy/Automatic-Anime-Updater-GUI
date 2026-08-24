import 'package:flutter/material.dart';
import 'package:window_manager/window_manager.dart';

import '../../core/constants/app_tokens.dart';
import '../../core/theme/app_palettes.dart';
import '../common/app_icon_btn.dart';

/// Frameless title bar with draggable window support, brand, and minimize/close controls.
class AppTitleBar extends StatelessWidget {
  /// Creates an [AppTitleBar] instance.
  const AppTitleBar({
    super.key,
    this.tokens,
  });

  /// Optional active theme color tokens.
  final AppColorTokens? tokens;

  @override
  Widget build(BuildContext context) {
    final ThemeData theme = Theme.of(context);
    final ColorScheme colorScheme = theme.colorScheme;
    final Color primaryColor = tokens?.primary ?? colorScheme.primary;
    final Color onSurfaceColor = tokens?.onSurface ?? colorScheme.onSurface;

    return DragToMoveArea(
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 8.0, vertical: 4.0),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          crossAxisAlignment: CrossAxisAlignment.center,
          children: <Widget>[
            // Brand Group (Draggable)
            Row(
              mainAxisSize: MainAxisSize.min,
              children: <Widget>[
                Icon(
                  Icons.bolt_rounded,
                  size: 28.0,
                  color: primaryColor,
                ),
                const SizedBox(width: 12.0),
                Text(
                  'Kyaa!!',
                  style: TextStyle(
                    fontFamily: AppTokens.fontFamily,
                    fontSize: 21.6,
                    fontWeight: FontWeight.w700,
                    letterSpacing: -0.32,
                    color: onSurfaceColor,
                  ),
                ),
              ],
            ),

            // Action Controls: Minimize + Close
            Row(
              mainAxisSize: MainAxisSize.min,
              children: <Widget>[
                AppIconBtn(
                  icon: Icons.remove_rounded,
                  tooltip: 'Minimize',
                  animationType: AppIconAnimationType.shiftDown,
                  tokens: tokens,
                  onPressed: () async {
                    try {
                      await windowManager.minimize();
                    } catch (exception) {
                      debugPrint('Error minimizing window: $exception');
                    }
                  },
                ),
                const SizedBox(width: 12.0),
                AppIconBtn(
                  icon: Icons.close_rounded,
                  tooltip: 'Close',
                  variant: AppIconBtnVariant.close,
                  animationType: AppIconAnimationType.rotate90,
                  tokens: tokens,
                  onPressed: () async {
                    try {
                      await windowManager.close();
                    } catch (exception) {
                      debugPrint('Error closing window: $exception');
                    }
                  },
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
