import 'package:flutter/material.dart';

import '../../core/constants/app_tokens.dart';
import '../../core/theme/app_palettes.dart';
import '../../core/theme/theme_controller.dart';

/// Themes view displaying the selected theme alone at the top,
/// and unselected themes in a 3-column row below.
/// Features zero-lag, instant theme switching with no outer borders.
class ThemesView extends StatefulWidget {
  /// Creates a [ThemesView] widget.
  const ThemesView({
    super.key,
    required this.themeController,
  });

  /// The theme controller managing the active application palette.
  final ThemeController themeController;

  @override
  State<ThemesView> createState() => _ThemesViewState();
}

class _ThemesViewState extends State<ThemesView> {
  void _handleThemeSelected(AppPaletteOption selectedOption) {
    widget.themeController.setPalette(selectedOption);
  }

  @override
  Widget build(BuildContext context) {
    final AppPaletteOption activePalette = widget.themeController.activePalette;
    final List<AppPaletteOption> otherPalettes = AppPaletteOption.values
        .where((AppPaletteOption option) => option != activePalette)
        .toList();

    return LayoutBuilder(
      builder: (BuildContext context, BoxConstraints constraints) {
        final double cardWidth = (constraints.maxWidth - 32.0) / 3.0;

        return SingleChildScrollView(
          padding: EdgeInsets.zero,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              // Selected Theme (Alone at the top, matching cardWidth)
              SizedBox(
                width: cardWidth,
                child: _ThemeCard(
                  key: ValueKey<String>('theme_selected_${activePalette.key}'),
                  option: activePalette,
                  isSelected: true,
                  onTap: () {},
                ),
              ),
              const SizedBox(height: 24.0),

              // Unselected Themes (3-column row below)
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: otherPalettes.map((AppPaletteOption option) {
                  final int optionIndex = otherPalettes.indexOf(option);
                  final bool isLast = optionIndex == otherPalettes.length - 1;

                  return Expanded(
                    child: Padding(
                      padding: EdgeInsets.only(right: isLast ? 0.0 : 16.0),
                      child: _ThemeCard(
                        key: ValueKey<String>('theme_option_${option.key}'),
                        option: option,
                        isSelected: false,
                        onTap: () => _handleThemeSelected(option),
                      ),
                    ),
                  );
                }).toList(),
              ),
            ],
          ),
        );
      },
    );
  }
}

/// Interactive theme preview card with skeleton animation and right-side active indicator dot.
class _ThemeCard extends StatefulWidget {
  const _ThemeCard({
    super.key,
    required this.option,
    required this.isSelected,
    required this.onTap,
  });

  final AppPaletteOption option;
  final bool isSelected;
  final VoidCallback onTap;

  @override
  State<_ThemeCard> createState() => _ThemeCardState();
}

class _ThemeCardState extends State<_ThemeCard> with SingleTickerProviderStateMixin {
  bool _isHovered = false;
  late final AnimationController _animationController;

  @override
  void initState() {
    super.initState();
    _animationController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1200),
    );
  }

  @override
  void dispose() {
    _animationController.dispose();
    super.dispose();
  }

  void _handleHoverChanged(bool isHovered) {
    setState(() => _isHovered = isHovered);
    if (isHovered) {
      _animationController.repeat(reverse: true);
    } else {
      _animationController.stop();
      _animationController.reset();
    }
  }

  @override
  Widget build(BuildContext context) {
    final AppColorTokens tokens = AppPalettes.getTokens(widget.option);

    return MouseRegion(
      cursor: SystemMouseCursors.click,
      onEnter: (_) => _handleHoverChanged(true),
      onExit: (_) => _handleHoverChanged(false),
      child: GestureDetector(
        onTap: widget.onTap,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: <Widget>[
            // Theme Name with Active Dot on the RIGHT
            Row(
              mainAxisSize: MainAxisSize.min,
              children: <Widget>[
                Text(
                  widget.option.displayName,
                  style: TextStyle(
                    fontFamily: AppTokens.fontFamily,
                    fontSize: 14.0,
                    fontWeight: widget.isSelected ? FontWeight.w600 : FontWeight.w500,
                    color: widget.isSelected
                        ? tokens.primary
                        : (_isHovered ? tokens.primary : tokens.onSurface),
                  ),
                ),
                if (widget.isSelected) ...<Widget>[
                  const SizedBox(width: 8),
                  Container(
                    width: 8,
                    height: 8,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: tokens.primary,
                    ),
                  ),
                ],
              ],
            ),
            const SizedBox(height: 12),
            // Skeleton Container adhering to 1000/740 aspect ratio with strictly NO border
            AspectRatio(
              aspectRatio: AppTokens.windowWidth / AppTokens.windowHeight,
              child: Container(
                decoration: BoxDecoration(
                  color: tokens.background,
                  borderRadius: BorderRadius.circular(AppTokens.cornerMedium),
                ),
                padding: const EdgeInsets.all(12.0),
                clipBehavior: Clip.antiAlias,
                child: AnimatedBuilder(
                  animation: _animationController,
                  builder: (BuildContext context, Widget? child) {
                    final double animationValue = _animationController.value;
                    return Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: <Widget>[
                        // Mini Tab Bar
                        Container(
                          height: 20,
                          decoration: BoxDecoration(
                            color: tokens.surfaceContainerLow,
                            borderRadius: BorderRadius.circular(AppTokens.cornerFull),
                          ),
                          padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 2),
                          child: Row(
                            children: <Widget>[
                              Expanded(
                                child: Container(
                                  height: double.infinity,
                                  decoration: BoxDecoration(
                                    color: tokens.secondaryContainer,
                                    borderRadius: BorderRadius.circular(AppTokens.cornerFull),
                                  ),
                                ),
                              ),
                              const SizedBox(width: 4),
                              Expanded(
                                child: Container(
                                  height: double.infinity,
                                  decoration: BoxDecoration(
                                    color: tokens.surfaceContainerHighest.withValues(alpha: 0.4),
                                    borderRadius: BorderRadius.circular(AppTokens.cornerFull),
                                  ),
                                ),
                              ),
                              const SizedBox(width: 4),
                              Expanded(
                                child: Container(
                                  height: double.infinity,
                                  decoration: BoxDecoration(
                                    color: tokens.surfaceContainerHighest.withValues(alpha: 0.4),
                                    borderRadius: BorderRadius.circular(AppTokens.cornerFull),
                                  ),
                                ),
                              ),
                              const SizedBox(width: 4),
                              Expanded(
                                child: Container(
                                  height: double.infinity,
                                  decoration: BoxDecoration(
                                    color: tokens.surfaceContainerHighest.withValues(alpha: 0.4),
                                    borderRadius: BorderRadius.circular(AppTokens.cornerFull),
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ),
                        const SizedBox(height: 10),
                        // Mini Body with 3 Animated Task Rows
                        Expanded(
                          child: Container(
                            decoration: BoxDecoration(
                              color: tokens.surfaceContainerLow,
                              borderRadius: BorderRadius.circular(AppTokens.cornerSmall),
                            ),
                            padding: const EdgeInsets.all(10.0),
                            child: Column(
                              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                              children: <Widget>[
                                _buildAnimatedTaskRow(
                                  tokens,
                                  titleWidthFactor: 0.45,
                                  trackWidthFactor: 0.85,
                                  shiftX: _isHovered ? (animationValue * 3.5) : 0.0,
                                ),
                                _buildAnimatedTaskRow(
                                  tokens,
                                  titleWidthFactor: 0.65,
                                  trackWidthFactor: 0.60,
                                  shiftX: _isHovered ? ((1.0 - animationValue) * 3.0) : 0.0,
                                ),
                                _buildAnimatedTaskRow(
                                  tokens,
                                  titleWidthFactor: 0.40,
                                  trackWidthFactor: 0.35,
                                  shiftX: _isHovered ? (animationValue * 2.8) : 0.0,
                                ),
                              ],
                            ),
                          ),
                        ),
                      ],
                    );
                  },
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildAnimatedTaskRow(
    AppColorTokens tokens, {
    required double titleWidthFactor,
    required double trackWidthFactor,
    required double shiftX,
  }) {
    return Transform.translate(
      offset: Offset(shiftX, 0),
      child: Container(
        height: 22,
        decoration: BoxDecoration(
          color: tokens.surfaceContainer,
          borderRadius: BorderRadius.circular(AppTokens.cornerExtraSmall),
        ),
        padding: const EdgeInsets.symmetric(horizontal: 7.0),
        child: Row(
          children: <Widget>[
            Container(
              width: 12,
              height: 12,
              decoration: BoxDecoration(
                color: tokens.primary,
                borderRadius: BorderRadius.circular(3),
              ),
            ),
            const SizedBox(width: 7),
            Expanded(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  FractionallySizedBox(
                    widthFactor: titleWidthFactor,
                    child: Container(
                      height: 3.2,
                      decoration: BoxDecoration(
                        color: tokens.onSurface,
                        borderRadius: BorderRadius.circular(AppTokens.cornerFull),
                      ),
                    ),
                  ),
                  const SizedBox(height: 3.0),
                  FractionallySizedBox(
                    widthFactor: trackWidthFactor,
                    child: Container(
                      height: 2.5,
                      decoration: BoxDecoration(
                        color: tokens.primaryContainer,
                        borderRadius: BorderRadius.circular(AppTokens.cornerFull),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
