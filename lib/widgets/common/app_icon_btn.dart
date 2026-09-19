import 'dart:math' as math;
import 'package:flutter/material.dart';
import '../../core/constants/app_tokens.dart';
import '../../core/theme/app_palettes.dart';

/// Style variants for [AppIconBtn].
enum AppIconBtnVariant {
  /// Standard neutral surface container variant.
  standard,

  /// High contrast primary accent container variant.
  primary,

  /// Dangerous action / window close variant with red hover styling.
  close,

  /// High-visibility yellow test indicator variant.
  yellow,
}

/// Unique desktop micro-animation types for [AppIconBtn].
enum AppIconAnimationType {
  /// No hover animation.
  none,

  /// Subtle upward translation on hover.
  scale,

  /// 90 degree clockwise rotation on hover.
  rotate90,

  /// Translate rightward on hover.
  shiftRight,

  /// Translate downward on hover.
  shiftDown,

  /// Bounce upward with subtle tilt on hover.
  bounceUp,

  /// Subtle vertical pulse translation on hover.
  pulse,

  /// Smooth clock hand rotation on hover.
  rotateClock,

  /// Wiggle rotation on hover.
  wiggle,
}

/// Squircle icon button matching single.html with fluid micro-animations.
class AppIconBtn extends StatefulWidget {
  /// Creates an [AppIconBtn] instance.
  const AppIconBtn({
    super.key,
    required this.icon,
    required this.onPressed,
    this.tooltip,
    this.variant = AppIconBtnVariant.standard,
    this.animationType = AppIconAnimationType.scale,
    this.isLarge = false,
    this.isCircle = false,
    this.tokens,
    this.size,
    this.iconSize,
    this.customBg,
    this.customFg,
  });

  /// The icon data displayed in the button center.
  final IconData icon;

  /// Callback executed when the button is tapped.
  final VoidCallback onPressed;

  /// Optional tooltip text displayed on desktop hover.
  final String? tooltip;

  /// Color style variant for the button container.
  final AppIconBtnVariant variant;

  /// Animation style applied to the icon on hover.
  final AppIconAnimationType animationType;

  /// Whether the button renders in large dimensions (56px).
  final bool isLarge;

  /// Whether the button renders with a full circular shape.
  final bool isCircle;

  /// Optional theme color tokens for color calculations.
  final AppColorTokens? tokens;

  /// Explicit custom width and height in pixels.
  final double? size;

  /// Explicit custom icon size in pixels.
  final double? iconSize;

  /// Optional override for background color.
  final Color? customBg;

  /// Optional override for foreground icon color.
  final Color? customFg;

  @override
  State<AppIconBtn> createState() => _AppIconBtnState();
}

class _AppIconBtnState extends State<AppIconBtn> with SingleTickerProviderStateMixin {
  /// Animation controller driving the hover micro-animation.
  late final AnimationController _controller;

  /// Curved animation for hover transitions.
  late final Animation<double> _animation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 320),
    );
    _animation = CurvedAnimation(
      parent: _controller,
      curve: Curves.easeOutCubic,
      reverseCurve: Curves.easeInCubic,
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  /// Updates animation controller direction on mouse hover events.
  void _handleHover(bool isHovered) {
    if (isHovered) {
      _controller.forward();
    } else {
      _controller.reverse();
    }
  }

  /// Checks whether the button icon represents a clock or time animation.
  bool _isClockIcon() {
    return widget.animationType == AppIconAnimationType.rotateClock ||
        widget.icon == Icons.schedule_rounded ||
        widget.icon == Icons.access_time_rounded ||
        widget.icon == Icons.access_time;
  }

  @override
  Widget build(BuildContext context) {
    final ThemeData theme = Theme.of(context);
    final ColorScheme colorScheme = theme.colorScheme;
    final AppColorTokens? tokens = widget.tokens;

    final double buttonSize = widget.size ??
        (widget.isLarge ? AppTokens.iconButtonLargeSize : AppTokens.iconButtonSize);
    final double borderRadiusValue = widget.isCircle
        ? AppTokens.cornerFull
        : (widget.isLarge ? 18.0 : AppTokens.cornerSquircle);
    final double iconDimension = widget.iconSize ?? (widget.isLarge ? 26.0 : 20.0);

    Color idleBackgroundColor;
    Color hoverBackgroundColor;
    Color idleForegroundColor;
    Color hoverForegroundColor;

    if (widget.customBg != null && widget.customFg != null) {
      idleBackgroundColor = widget.customBg!;
      hoverBackgroundColor = widget.customBg!.withValues(alpha: 0.85);
      idleForegroundColor = widget.customFg!;
      hoverForegroundColor = widget.customFg!;
    } else {
      switch (widget.variant) {
        case AppIconBtnVariant.primary:
          idleBackgroundColor = tokens?.primary ?? colorScheme.primary;
          hoverBackgroundColor = tokens?.primary ?? colorScheme.primary;
          idleForegroundColor = tokens?.onPrimary ?? colorScheme.onPrimary;
          hoverForegroundColor = tokens?.onPrimary ?? colorScheme.onPrimary;
          break;
        case AppIconBtnVariant.close:
          idleBackgroundColor = tokens?.surfaceContainerHigh ?? colorScheme.surfaceContainerHigh;
          hoverBackgroundColor = const Color(0xFFB3261E);
          idleForegroundColor = tokens?.onSurface ?? colorScheme.onSurface;
          hoverForegroundColor = const Color(0xFFFFFFFF);
          break;
        case AppIconBtnVariant.yellow:
          idleBackgroundColor = const Color(0xFFFFC107);
          hoverBackgroundColor = const Color(0xFFFFD54F);
          idleForegroundColor = const Color(0xFF212121);
          hoverForegroundColor = const Color(0xFF3E2723);
          break;
        case AppIconBtnVariant.standard:
          idleBackgroundColor = tokens?.surfaceContainerHigh ?? colorScheme.surfaceContainerHigh;
          hoverBackgroundColor = tokens?.surfaceContainerHighest ?? colorScheme.surfaceContainerHighest;
          idleForegroundColor = tokens?.onSurface ?? colorScheme.onSurface;
          hoverForegroundColor = tokens?.onSurface ?? colorScheme.onSurface;
          break;
      }
    }

    Widget buttonWidget = MouseRegion(
      cursor: SystemMouseCursors.click,
      onEnter: (_) => _handleHover(true),
      onExit: (_) => _handleHover(false),
      child: GestureDetector(
        onTap: widget.onPressed,
        child: AnimatedBuilder(
          animation: _animation,
          builder: (BuildContext context, Widget? child) {
            final double progress = _animation.value;
            final Color backgroundColor = Color.lerp(
                  idleBackgroundColor,
                  hoverBackgroundColor,
                  progress,
                ) ??
                idleBackgroundColor;
            final Color foregroundColor = Color.lerp(
                  idleForegroundColor,
                  hoverForegroundColor,
                  progress,
                ) ??
                idleForegroundColor;

            Widget iconWidget;
            if (_isClockIcon()) {
              iconWidget = _AnimatedClockWidget(
                progress: progress,
                color: foregroundColor,
                size: iconDimension,
              );
            } else {
              iconWidget = Icon(
                widget.icon,
                size: iconDimension,
                color: foregroundColor,
              );

              switch (widget.animationType) {
                case AppIconAnimationType.scale:
                  iconWidget = Transform.translate(
                    offset: Offset(0.0, -2.5 * progress),
                    child: iconWidget,
                  );
                  break;
                case AppIconAnimationType.rotate90:
                  iconWidget = Transform.rotate(
                    angle: (math.pi / 2) * progress,
                    child: iconWidget,
                  );
                  break;
                case AppIconAnimationType.shiftRight:
                  iconWidget = Transform.translate(
                    offset: Offset(3.0 * progress, 0.0),
                    child: iconWidget,
                  );
                  break;
                case AppIconAnimationType.shiftDown:
                  iconWidget = Transform.translate(
                    offset: Offset(0.0, 2.5 * progress),
                    child: iconWidget,
                  );
                  break;
                case AppIconAnimationType.bounceUp:
                  iconWidget = Transform.translate(
                    offset: Offset(0.0, -3.5 * progress),
                    child: Transform.rotate(
                      angle: -0.12 * progress,
                      child: iconWidget,
                    ),
                  );
                  break;
                case AppIconAnimationType.pulse:
                  iconWidget = Transform.translate(
                    offset: Offset(0.0, -2.0 * progress),
                    child: iconWidget,
                  );
                  break;
                case AppIconAnimationType.rotateClock:
                  iconWidget = Transform.rotate(
                    angle: (math.pi / 4) * progress,
                    child: iconWidget,
                  );
                  break;
                case AppIconAnimationType.wiggle:
                  iconWidget = Transform.rotate(
                    angle: 0.15 * progress,
                    child: iconWidget,
                  );
                  break;
                case AppIconAnimationType.none:
                  break;
              }
            }

            return Container(
              width: buttonSize,
              height: buttonSize,
              decoration: BoxDecoration(
                color: backgroundColor,
                borderRadius: BorderRadius.circular(borderRadiusValue),
              ),
              alignment: Alignment.center,
              child: iconWidget,
            );
          },
        ),
      ),
    );

    if (widget.tooltip != null && widget.tooltip!.isNotEmpty) {
      buttonWidget = Tooltip(
        message: widget.tooltip!,
        child: buttonWidget,
      );
    }

    return buttonWidget;
  }
}

/// Renders a fluid clock icon where hovering smoothly rotates the minute / long hand to its end position.
class _AnimatedClockWidget extends StatelessWidget {
  /// Creates an [_AnimatedClockWidget] with animated progress and color styling.
  const _AnimatedClockWidget({
    required this.progress,
    required this.color,
    required this.size,
  });

  /// Current animation progression ratio from 0.0 to 1.0.
  final double progress;

  /// Foreground color for clock hands and outline.
  final Color color;

  /// Target square boundary size in pixels.
  final double size;

  @override
  Widget build(BuildContext context) {
    return CustomPaint(
      size: Size(size, size),
      painter: _ClockCustomPainter(
        progress: progress,
        color: color,
      ),
    );
  }
}

/// Custom painter drawing animated clock face and rotating hands.
class _ClockCustomPainter extends CustomPainter {
  /// Creates a [_ClockCustomPainter] instance.
  _ClockCustomPainter({
    required this.progress,
    required this.color,
  });

  /// Current animation progression ratio from 0.0 to 1.0.
  final double progress;

  /// Stroke and fill color for clock elements.
  final Color color;

  @override
  void paint(Canvas canvas, Size size) {
    final Offset center = Offset(size.width / 2.0, size.height / 2.0);
    final double radius = (size.width / 2.0) - 1.5;

    final Paint circlePaint = Paint()
      ..color = color
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2.0;

    final Paint centerDotPaint = Paint()
      ..color = color
      ..style = PaintingStyle.fill;

    final Paint handPaint = Paint()
      ..color = color
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2.0
      ..strokeCap = StrokeCap.round;

    // Draw clock circular outline
    canvas.drawCircle(center, radius, circlePaint);

    // Draw center dot
    canvas.drawCircle(center, 1.6, centerDotPaint);

    // Short Hour Hand: pointing to ~9:30 (-2.2 rad), subtly advances as minute hand rotates
    const double hourStartAngle = -2.2;
    final double hourCurrentAngle = hourStartAngle + (0.35 * progress);
    final double hourLength = radius * 0.48;
    final Offset hourEnd = Offset(
      center.dx + (hourLength * math.cos(hourCurrentAngle)),
      center.dy + (hourLength * math.sin(hourCurrentAngle)),
    );
    canvas.drawLine(center, hourEnd, handPaint);

    // Long Minute Hand: Starts at 12 o'clock (-math.pi / 2),
    // smoothly sweeps clockwise to 4 o'clock (-math.pi / 2 + math.pi * 1.25) on hover
    const double minuteStartAngle = -math.pi / 2.0;
    const double minuteSweepAngle = math.pi * 1.25;
    final double minuteCurrentAngle = minuteStartAngle + (minuteSweepAngle * progress);
    final double minuteLength = radius * 0.72;
    final Offset minuteEnd = Offset(
      center.dx + (minuteLength * math.cos(minuteCurrentAngle)),
      center.dy + (minuteLength * math.sin(minuteCurrentAngle)),
    );
    canvas.drawLine(center, minuteEnd, handPaint);
  }

  @override
  bool shouldRepaint(covariant _ClockCustomPainter oldDelegate) {
    return oldDelegate.progress != progress || oldDelegate.color != color;
  }
}
