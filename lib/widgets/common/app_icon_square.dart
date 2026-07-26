import 'package:flutter/material.dart';
import '../../core/constants/app_tokens.dart';
import '../../core/theme/app_palettes.dart';

/// Squircle header icon square container matching .app-icon-square in single.html.
class AppIconSquare extends StatelessWidget {
  /// Creates an [AppIconSquare] displaying [icon].
  const AppIconSquare({
    super.key,
    required this.icon,
    this.tokens,
    this.size = AppTokens.iconSquareSize,
  });

  /// The icon data to render within the squircle container.
  final IconData icon;

  /// Optional theme color tokens for color derivation.
  final AppColorTokens? tokens;

  /// Dimensions (width and height) of the square container in pixels.
  final double size;

  @override
  Widget build(BuildContext context) {
    final ThemeData theme = Theme.of(context);
    final ColorScheme colorScheme = theme.colorScheme;
    final Color backgroundColor = tokens?.surfaceContainerHighest ?? colorScheme.surfaceContainerHighest;
    final Color foregroundColor = tokens?.primary ?? colorScheme.primary;

    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        color: backgroundColor,
        borderRadius: BorderRadius.circular(AppTokens.cornerSquircle),
      ),
      alignment: Alignment.center,
      child: Icon(
        icon,
        size: size * 0.55,
        color: foregroundColor,
      ),
    );
  }
}
