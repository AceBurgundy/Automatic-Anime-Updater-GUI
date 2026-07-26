import 'package:flutter/material.dart';
import '../../core/constants/app_tokens.dart';
import '../../core/theme/app_palettes.dart';

/// Linear progress bar featuring an M3 gradient fill matching single.html.
class GradientProgressBar extends StatelessWidget {
  /// Creates an instance of [GradientProgressBar] with the specified [progress].
  const GradientProgressBar({
    super.key,
    required this.progress,
    this.tokens,
    this.height = AppTokens.progressTrackHeight,
  });

  /// Progress fraction value between 0.0 and 1.0.
  final double progress;

  /// Optional theme color tokens for gradient extraction.
  final AppColorTokens? tokens;

  /// Height of the track bar in pixels.
  final double height;

  @override
  Widget build(BuildContext context) {
    final ThemeData theme = Theme.of(context);
    final ColorScheme colorScheme = theme.colorScheme;
    final Color trackColor = tokens?.surfaceContainerHighest ?? colorScheme.surfaceContainerHighest;
    final Color startColor = tokens?.primary ?? colorScheme.primary;
    final Color endColor = tokens?.tertiary ?? colorScheme.tertiary;

    final double clampedProgress = progress.clamp(0.0, 1.0);

    return Container(
      width: double.infinity,
      height: height,
      decoration: BoxDecoration(
        color: trackColor,
        borderRadius: BorderRadius.circular(AppTokens.cornerFull),
      ),
      clipBehavior: Clip.antiAlias,
      child: LayoutBuilder(
        builder: (BuildContext context, BoxConstraints constraints) {
          final double fillWidth = constraints.maxWidth * clampedProgress;
          return Align(
            alignment: Alignment.centerLeft,
            child: AnimatedContainer(
              duration: const Duration(milliseconds: 300),
              curve: Curves.easeOutCubic,
              width: fillWidth,
              height: height,
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(AppTokens.cornerFull),
                gradient: LinearGradient(
                  colors: <Color>[startColor, endColor],
                  begin: Alignment.centerLeft,
                  end: Alignment.centerRight,
                ),
              ),
            ),
          );
        },
      ),
    );
  }
}
