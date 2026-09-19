import 'package:flutter/material.dart';
import '../../core/constants/app_tokens.dart';
import '../../core/services/cli_bridge_service.dart';
import '../../core/services/subprocess_service.dart';
import '../../core/theme/app_palettes.dart';
import '../common/app_icon_btn.dart';
import '../common/app_icon_square.dart';

/// Information record for a schedule day.
class DayInfo {
  /// Creates an immutable [DayInfo] instance.
  const DayInfo({
    required this.letter,
    required this.name,
  });

  /// Single letter representation (e.g. 'M', 'T', 'W').
  final String letter;

  /// Full weekday name (e.g. 'Monday').
  final String name;
}

/// Scheduling view matching single.html with 12-hour time format,
/// checkbox Everyday toggle, isolated day button click events,
/// and unique hover micro-animations.
class SchedulingView extends StatefulWidget {
  /// Creates a [SchedulingView] widget.
  const SchedulingView({
    super.key,
    this.tokens,
  });

  /// Optional active theme color tokens.
  final AppColorTokens? tokens;

  @override
  State<SchedulingView> createState() => _SchedulingViewState();
}

class _SchedulingViewState extends State<SchedulingView> {
  /// Ordered list of days in the week with their short and full titles.
  final List<DayInfo> _days = const <DayInfo>[
    DayInfo(letter: 'M', name: 'Monday'),
    DayInfo(letter: 'T', name: 'Tuesday'),
    DayInfo(letter: 'W', name: 'Wednesday'),
    DayInfo(letter: 'T', name: 'Thursday'),
    DayInfo(letter: 'F', name: 'Friday'),
    DayInfo(letter: 'S', name: 'Saturday'),
    DayInfo(letter: 'S', name: 'Sunday'),
  ];

  /// Active selection state flags corresponding to [_days].
  late List<bool> _daySelections;

  /// Whether all days are selected collectively.
  bool _isEverydayOn = true;

  /// Configured 12-hour formatted automation trigger times.
  final List<String> _triggerTimes = <String>['04:00 AM', '12:30 PM', '08:00 PM'];

  @override
  void initState() {
    super.initState();
    _daySelections = List<bool>.generate(_days.length, (_) => true);
  }

  void _handleToggleEveryday() {
    setState(() {
      _isEverydayOn = !_isEverydayOn;
      for (int index = 0; index < _daySelections.length; index++) {
        _daySelections[index] = _isEverydayOn;
      }
    });
  }

  void _handleToggleDay(int index) {
    setState(() {
      _daySelections[index] = !_daySelections[index];
      _isEverydayOn = _daySelections.every((bool selected) => selected);
    });
  }

  void _handleRemoveTime(String time) {
    setState(() {
      _triggerTimes.remove(time);
    });
    SubprocessService.instance.removeTriggerTime(time);
  }

  Future<void> _handleAddTime() async {
    await SubprocessService.instance.addTriggerTime('New Trigger Time');

    if (!mounted) return;

    final ThemeData theme = Theme.of(context);
    final AppColorTokens? tokens = widget.tokens;

    // Material 3 Dark TimePicker
    final TimeOfDay? timeOfDay = await showTimePicker(
      context: context,
      initialTime: const TimeOfDay(hour: 8, minute: 0),
      builder: (BuildContext context, Widget? child) {
        return Theme(
          data: theme.copyWith(
            colorScheme: (tokens?.toColorScheme() ?? theme.colorScheme).copyWith(
              surface: tokens?.surfaceContainerHigh ?? theme.colorScheme.surfaceContainerHigh,
              onSurface: tokens?.onSurface ?? theme.colorScheme.onSurface,
            ),
            timePickerTheme: TimePickerThemeData(
              backgroundColor: tokens?.surfaceContainer ?? const Color(0xFF211F26),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(AppTokens.cornerMedium),
              ),
              hourMinuteShape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(AppTokens.cornerSmall),
              ),
              dayPeriodShape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(AppTokens.cornerSmall),
              ),
            ),
          ),
          child: child ?? const SizedBox.shrink(),
        );
      },
    );

    if (timeOfDay != null && mounted) {
      // Format 12-hour string (hh:mm AM/PM)
      final int hour = timeOfDay.hourOfPeriod == 0 ? 12 : timeOfDay.hourOfPeriod;
      final String formattedHour = hour.toString().padLeft(2, '0');
      final String formattedMinute = timeOfDay.minute.toString().padLeft(2, '0');
      final String period = timeOfDay.period == DayPeriod.am ? 'AM' : 'PM';
      final String newTime = '$formattedHour:$formattedMinute $period';

      if (!_triggerTimes.contains(newTime)) {
        setState(() {
          // Appended so it shows beside the plus icon
          _triggerTimes.add(newTime);
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final ThemeData theme = Theme.of(context);
    final ColorScheme colorScheme = theme.colorScheme;
    final AppColorTokens? tokens = widget.tokens;

    final Color cardBackgroundColor = tokens?.surfaceContainer ?? colorScheme.surfaceContainer;
    final Color onSurface = tokens?.onSurface ?? colorScheme.onSurface;
    final Color primaryColor = tokens?.primary ?? colorScheme.primary;

    return Column(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: <Widget>[
        // Main Body: Active Days + Trigger Times
        Expanded(
          child: SingleChildScrollView(
            padding: EdgeInsets.zero,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: <Widget>[
                // Card 1: Active Days
                Container(
                  decoration: BoxDecoration(
                    color: cardBackgroundColor,
                    borderRadius: BorderRadius.circular(AppTokens.cornerMedium),
                  ),
                  padding: const EdgeInsets.symmetric(horizontal: 24.0, vertical: 20.0),
                  child: Column(
                    children: <Widget>[
                      // Header Row: Active Days + Everyday Checkbox
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: <Widget>[
                          Row(
                            children: <Widget>[
                              AppIconSquare(
                                icon: Icons.calendar_today_rounded,
                                tokens: tokens,
                              ),
                              const SizedBox(width: 12.0),
                              Text(
                                'Active Days',
                                style: TextStyle(
                                  fontFamily: AppTokens.fontFamily,
                                  fontSize: 15.0,
                                  fontWeight: FontWeight.w500,
                                  color: onSurface,
                                ),
                              ),
                            ],
                          ),
                          // Everyday Checkbox Row
                          MouseRegion(
                            cursor: SystemMouseCursors.click,
                            child: GestureDetector(
                              onTap: _handleToggleEveryday,
                              child: Row(
                                mainAxisSize: MainAxisSize.min,
                                children: <Widget>[
                                  AnimatedContainer(
                                    duration: const Duration(milliseconds: 180),
                                    width: 20.0,
                                    height: 20.0,
                                    decoration: BoxDecoration(
                                      color: _isEverydayOn
                                          ? primaryColor
                                          : (tokens?.surfaceContainerHighest ?? colorScheme.surfaceContainerHighest),
                                      borderRadius: BorderRadius.circular(AppTokens.cornerExtraSmall),
                                    ),
                                    alignment: Alignment.center,
                                    child: _isEverydayOn
                                        ? Icon(
                                            Icons.check_rounded,
                                            size: 15.0,
                                            color: tokens?.onPrimary ?? colorScheme.onPrimary,
                                          )
                                        : null,
                                  ),
                                  const SizedBox(width: 8.0),
                                  Text(
                                    'Everyday',
                                    style: TextStyle(
                                      fontFamily: AppTokens.fontFamily,
                                      fontSize: 13.5,
                                      fontWeight: FontWeight.w500,
                                      color: onSurface,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ),
                        ],
                      ),

                      const SizedBox(height: 18.0),

                      // Squircle Letter Day Buttons (Isolated Events)
                      Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: List<Widget>.generate(_days.length, (int index) {
                          final DayInfo day = _days[index];
                          final bool isActive = _daySelections[index];
                          return Padding(
                            padding: EdgeInsets.only(
                              right: index == _days.length - 1 ? 0 : 16.0,
                            ),
                            child: _DayButton(
                              day: day,
                              isActive: isActive,
                              tokens: tokens,
                              onTap: () => _handleToggleDay(index),
                            ),
                          );
                        }),
                      ),
                    ],
                  ),
                ),

                const SizedBox(height: 20.0),

                // Card 2: Trigger Times
                Container(
                  decoration: BoxDecoration(
                    color: cardBackgroundColor,
                    borderRadius: BorderRadius.circular(AppTokens.cornerMedium),
                  ),
                  padding: const EdgeInsets.symmetric(horizontal: 24.0, vertical: 20.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: <Widget>[
                      // Header Row
                      Row(
                        children: <Widget>[
                          AppIconSquare(
                            icon: Icons.schedule_rounded,
                            tokens: tokens,
                          ),
                          const SizedBox(width: 12.0),
                          Text(
                            'Trigger Times',
                            style: TextStyle(
                              fontFamily: AppTokens.fontFamily,
                              fontSize: 15.0,
                              fontWeight: FontWeight.w500,
                              color: onSurface,
                            ),
                          ),
                        ],
                      ),

                      const SizedBox(height: 18.0),

                      // Trigger Time Pills + Add Button (New items show beside +)
                      Wrap(
                        spacing: 14.0,
                        runSpacing: 12.0,
                        crossAxisAlignment: WrapCrossAlignment.center,
                        children: <Widget>[
                          ..._triggerTimes.map((String time) {
                            return _TimePill(
                              time: time,
                              tokens: tokens,
                              onRemove: () => _handleRemoveTime(time),
                            );
                          }),
                          AppIconBtn(
                            icon: Icons.add_rounded,
                            tooltip: 'Add Time',
                            animationType: AppIconAnimationType.rotate90,
                            size: AppTokens.dayButtonSize,
                            tokens: tokens,
                            onPressed: _handleAddTime,
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),

        // Footer: Play / Pause Scheduler Action Buttons with Unique Micro-Animations
        Padding(
          padding: const EdgeInsets.only(top: 10.0),
          child: ValueListenableBuilder<bool>(
            valueListenable: CliBridgeService.instance.isSchedulerActiveNotifier,
            builder: (BuildContext context, bool isSchedulerActive, _) {
              return Row(
                mainAxisAlignment: MainAxisAlignment.end,
                children: <Widget>[
                  AppIconBtn(
                    icon: Icons.play_arrow_rounded,
                    tooltip: 'Start Scheduler',
                    isLarge: true,
                    variant: isSchedulerActive ? AppIconBtnVariant.standard : AppIconBtnVariant.primary,
                    animationType: AppIconAnimationType.shiftRight,
                    tokens: tokens,
                    onPressed: () {
                      final List<String> selectedDayNames = <String>[];
                      for (int index = 0; index < _daySelections.length; index++) {
                        if (_daySelections[index]) {
                          selectedDayNames.add(_days[index].name);
                        }
                      }
                      SubprocessService.instance.startAutomationSchedule(
                        activeDays: selectedDayNames,
                        triggerTimes: _triggerTimes,
                      );
                    },
                  ),
                  const SizedBox(width: 12.0),
                  AppIconBtn(
                    icon: Icons.pause_rounded,
                    tooltip: 'Stop Scheduler',
                    isLarge: true,
                    variant: isSchedulerActive ? AppIconBtnVariant.primary : AppIconBtnVariant.standard,
                    animationType: AppIconAnimationType.pulse,
                    tokens: tokens,
                    onPressed: () {
                      SubprocessService.instance.stopAutomationSchedule();
                    },
                  ),
                ],
              );
            },
          ),
        ),
      ],
    );
  }
}

/// Internal squircle button widget representing a single day of the week.
class _DayButton extends StatefulWidget {
  /// Creates a [_DayButton] widget.
  const _DayButton({
    required this.day,
    required this.isActive,
    required this.onTap,
    this.tokens,
  });

  /// Associated day data record.
  final DayInfo day;

  /// Whether this day is currently active.
  final bool isActive;

  /// Callback executed when the day button is tapped.
  final VoidCallback onTap;

  /// Optional active theme color tokens.
  final AppColorTokens? tokens;

  @override
  State<_DayButton> createState() => _DayButtonState();
}

class _DayButtonState extends State<_DayButton> {
  /// Whether the button is currently hovered.
  bool _isHovered = false;

  @override
  Widget build(BuildContext context) {
    final ThemeData theme = Theme.of(context);
    final ColorScheme colorScheme = theme.colorScheme;
    final AppColorTokens? tokens = widget.tokens;

    final Color backgroundColor = widget.isActive
        ? (tokens?.primary ?? colorScheme.primary)
        : (_isHovered
            ? (tokens?.surfaceContainerHighest ?? colorScheme.surfaceContainerHighest)
            : (tokens?.surfaceContainerHigh ?? colorScheme.surfaceContainerHigh));
    final Color foregroundColor = widget.isActive
        ? (tokens?.onPrimary ?? colorScheme.onPrimary)
        : (_isHovered
            ? (tokens?.onSurface ?? colorScheme.onSurface)
            : (tokens?.onSurfaceVariant ?? colorScheme.onSurfaceVariant));

    return Tooltip(
      message: widget.day.name,
      child: MouseRegion(
        cursor: SystemMouseCursors.click,
        onEnter: (_) => setState(() => _isHovered = true),
        onExit: (_) => setState(() => _isHovered = false),
        child: GestureDetector(
          behavior: HitTestBehavior.opaque,
          onTap: widget.onTap,
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 150),
            curve: Curves.easeOut,
            width: AppTokens.dayButtonSize,
            height: AppTokens.dayButtonSize,
            decoration: BoxDecoration(
              color: backgroundColor,
              borderRadius: BorderRadius.circular(AppTokens.cornerSquircle),
            ),
            alignment: Alignment.center,
            child: Text(
              widget.day.letter,
              style: TextStyle(
                fontFamily: AppTokens.fontFamily,
                fontSize: 16.0,
                fontWeight: FontWeight.w700,
                color: foregroundColor,
              ),
            ),
          ),
        ),
      ),
    );
  }
}

/// Internal pill chip representing a scheduled execution trigger time.
class _TimePill extends StatefulWidget {
  /// Creates a [_TimePill] widget.
  const _TimePill({
    required this.time,
    required this.onRemove,
    this.tokens,
  });

  /// 12-hour formatted time string.
  final String time;

  /// Callback executed when removing this trigger time.
  final VoidCallback onRemove;

  /// Optional active theme color tokens.
  final AppColorTokens? tokens;

  @override
  State<_TimePill> createState() => _TimePillState();
}

class _TimePillState extends State<_TimePill> {
  /// Whether the remove button icon is currently hovered.
  bool _isCloseHovered = false;

  @override
  Widget build(BuildContext context) {
    final ThemeData theme = Theme.of(context);
    final ColorScheme colorScheme = theme.colorScheme;
    final AppColorTokens? tokens = widget.tokens;

    final Color pillBackgroundColor = tokens?.surfaceContainerHigh ?? colorScheme.surfaceContainerHigh;
    final Color primaryColor = tokens?.primary ?? colorScheme.primary;
    final Color onSurface = tokens?.onSurface ?? colorScheme.onSurface;
    final Color onSurfaceVariant = tokens?.onSurfaceVariant ?? colorScheme.onSurfaceVariant;

    return Container(
      height: AppTokens.timePillHeight,
      decoration: BoxDecoration(
        color: pillBackgroundColor,
        borderRadius: BorderRadius.circular(AppTokens.cornerFull),
      ),
      padding: const EdgeInsets.symmetric(horizontal: 18.0),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: <Widget>[
          Icon(
            Icons.schedule_rounded,
            size: 19.0,
            color: primaryColor,
          ),
          const SizedBox(width: 8.0),
          Text(
            widget.time,
            style: TextStyle(
              fontFamily: AppTokens.codeFontFamily,
              fontSize: 14.5,
              fontWeight: FontWeight.w600,
              color: onSurface,
            ),
          ),
          const SizedBox(width: 6.0),
          Tooltip(
            message: 'Remove time',
            child: MouseRegion(
              cursor: SystemMouseCursors.click,
              onEnter: (_) => setState(() => _isCloseHovered = true),
              onExit: (_) => setState(() => _isCloseHovered = false),
              child: GestureDetector(
                onTap: widget.onRemove,
                child: AnimatedContainer(
                  duration: const Duration(milliseconds: 150),
                  width: 26.0,
                  height: 26.0,
                  decoration: BoxDecoration(
                    color: _isCloseHovered
                        ? const Color(0x1FFF6B6B)
                        : Colors.transparent,
                    borderRadius: BorderRadius.circular(AppTokens.cornerExtraSmall),
                  ),
                  alignment: Alignment.center,
                  child: AnimatedRotation(
                    turns: _isCloseHovered ? 0.25 : 0.0,
                    duration: const Duration(milliseconds: 150),
                    child: Icon(
                      Icons.close_rounded,
                      size: 17.0,
                      color: _isCloseHovered
                          ? const Color(0xFFFFB4AB)
                          : onSurfaceVariant,
                    ),
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
