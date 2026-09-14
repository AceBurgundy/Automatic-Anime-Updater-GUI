import 'package:flutter/material.dart';
import '../../core/constants/app_tokens.dart';
import '../../core/services/cli_bridge_service.dart';
import '../../core/services/subprocess_service.dart';
import '../../core/theme/app_palettes.dart';
import '../common/app_icon_btn.dart';
import '../common/gradient_progress_bar.dart';

/// Formats raw byte counts into human-readable strings (e.g. 1.42 GB).
String _formatBytes(int bytes) {
  if (bytes <= 0) return '0 B';
  const List<String> units = <String>['B', 'KB', 'MB', 'GB', 'TB'];
  int digitGroups = 0;
  double size = bytes.toDouble();
  while (size >= 1024.0 && digitGroups < units.length - 1) {
    size /= 1024.0;
    digitGroups++;
  }
  return '${size.toStringAsFixed(digitGroups == 0 ? 0 : 2)} ${units[digitGroups]}';
}

/// Formats ISO 8601 timestamp strings into readable date-time strings.
String _formatTimestamp(String isoString) {
  if (isoString.isEmpty) return 'N/A';
  final DateTime? parsed = DateTime.tryParse(isoString);
  if (parsed == null) return isoString;
  final String year = parsed.year.toString();
  final String month = parsed.month.toString().padLeft(2, '0');
  final String day = parsed.day.toString().padLeft(2, '0');
  final String hour = parsed.hour.toString().padLeft(2, '0');
  final String minute = parsed.minute.toString().padLeft(2, '0');
  final String second = parsed.second.toString().padLeft(2, '0');
  return '$year-$month-$day $hour:$minute:$second';
}

/// Represents the processing and download state of an episode task.
enum TaskDownloadState {
  /// Task processing is fully completed and ready.
  ready(
    statusLabel: 'Completed',
    icon: Icons.check_rounded,
    backgroundColor: Color(0xFF1E522B),
    foregroundColor: Color(0xFF69F0AE),
  ),

  /// Task processing or download is actively running.
  running(
    statusLabel: 'In Progress',
    icon: Icons.downloading_rounded,
    backgroundColor: Color(0xFF5E35B1),
    foregroundColor: Color(0xFFEDE7F6),
  ),

  /// Task is waiting in batch download queue.
  queued(
    statusLabel: 'Queued',
    icon: Icons.hourglass_top_rounded,
    backgroundColor: Color(0xFF49454F),
    foregroundColor: Color(0xFFE2DDF0),
  ),

  /// Task encountered a download or parsing error.
  failed(
    statusLabel: 'Failed',
    icon: Icons.error_outline_rounded,
    backgroundColor: Color(0xFF5C1D1D),
    foregroundColor: Color(0xFFFFB4AB),
  );

  const TaskDownloadState({
    required this.statusLabel,
    required this.icon,
    required this.backgroundColor,
    required this.foregroundColor,
  });

  /// Descriptive label for task status.
  final String statusLabel;

  /// Icon representing the state.
  final IconData icon;

  /// Default container background color for the state badge.
  final Color backgroundColor;

  /// Foreground accent color for the state badge icon.
  final Color foregroundColor;
}

/// Data model representing a single episode processing task driven by stream map events.
class TaskItemData {
  /// Creates an immutable [TaskItemData] record.
  const TaskItemData({
    required this.id,
    required this.stringEvent,
    required this.stringTimestamp,
    required this.stringAnimeName,
    required this.intEpisodeNumber,
    required this.stringFilename,
    required this.stringDownloadStatus,
    required this.floatProgressPercentage,
    required this.intDownloadedBytes,
    required this.intTotalBytes,
    required this.floatSpeedMbps,
    this.stringShortErrorMessage = '',
    this.stringErrorLogMessage = '',
  });

  /// Constructs a [TaskItemData] instance from a decoded stream event map.
  factory TaskItemData.fromMap(Map<String, Object?> map, {String? id}) {
    return TaskItemData(
      id: id ?? (map['id'] as String? ?? ''),
      stringEvent: map['string_event'] as String? ?? 'download_update',
      stringTimestamp: map['string_timestamp'] as String? ?? '',
      stringAnimeName: map['string_anime_name'] as String? ?? '',
      intEpisodeNumber: (map['int_episode_number'] as num?)?.toInt() ?? 0,
      stringFilename: map['string_filename'] as String? ?? '',
      stringDownloadStatus: map['string_download_status'] as String? ?? 'queue',
      floatProgressPercentage: (map['float_progress_percentage'] as num?)?.toDouble() ?? 0.0,
      intDownloadedBytes: (map['int_downloaded_bytes'] as num?)?.toInt() ?? 0,
      intTotalBytes: (map['int_total_bytes'] as num?)?.toInt() ?? 0,
      floatSpeedMbps: (map['float_speed_mbps'] as num?)?.toDouble() ?? 0.0,
      stringShortErrorMessage: map['string_short_error_message'] as String? ?? '',
      stringErrorLogMessage: map['string_error_log_message'] as String? ?? '',
    );
  }

  /// Converts this [TaskItemData] instance into a stream event map payload.
  Map<String, Object?> toMap() {
    return <String, Object?>{
      'id': id,
      'string_event': stringEvent,
      'string_timestamp': stringTimestamp,
      'string_anime_name': stringAnimeName,
      'int_episode_number': intEpisodeNumber,
      'string_filename': stringFilename,
      'string_download_status': stringDownloadStatus,
      'float_progress_percentage': floatProgressPercentage,
      'int_downloaded_bytes': intDownloadedBytes,
      'int_total_bytes': intTotalBytes,
      'float_speed_mbps': floatSpeedMbps,
      'string_short_error_message': stringShortErrorMessage,
      'string_error_log_message': stringErrorLogMessage,
    };
  }

  /// Unique task identifier.
  final String id;

  /// Event category string (e.g. "download_update").
  final String stringEvent;

  /// Event generation timestamp string in ISO 8601 format.
  final String stringTimestamp;

  /// Anime series title string.
  final String stringAnimeName;

  /// Current episode number integer.
  final int intEpisodeNumber;

  /// Target video filename string.
  final String stringFilename;

  /// Current download status string ("queue", "in-progress", "completed", "failed").
  final String stringDownloadStatus;

  /// Progress percentage float value (0.0 to 100.0).
  final double floatProgressPercentage;

  /// Transferred download bytes integer count.
  final int intDownloadedBytes;

  /// Total target file bytes integer count.
  final int intTotalBytes;

  /// Real-time download transfer speed in megabytes per second.
  final double floatSpeedMbps;

  /// Brief short error message summary string when failed.
  final String stringShortErrorMessage;

  /// Full traceback or diagnostic error log message string when failed.
  final String stringErrorLogMessage;

  /// Formatted title combining anime title and episode number.
  String get title {
    if (stringAnimeName.isEmpty) return stringFilename;
    final String episodeString = intEpisodeNumber.toString().padLeft(2, '0');
    return '$stringAnimeName - Episode $episodeString';
  }

  /// Normalized progress value clamped between 0.0 and 1.0.
  double get progress => (floatProgressPercentage / 100.0).clamp(0.0, 1.0);

  /// Whether the task is in a failed error state.
  bool get isFailed =>
      stringDownloadStatus.toLowerCase() == 'failed' || stringShortErrorMessage.isNotEmpty;

  /// Mapped [TaskDownloadState] reflecting current status.
  TaskDownloadState get state {
    if (isFailed) return TaskDownloadState.failed;
    switch (stringDownloadStatus.toLowerCase()) {
      case 'completed':
      case 'ready':
        return TaskDownloadState.ready;
      case 'in-progress':
      case 'running':
        return TaskDownloadState.running;
      case 'queue':
      case 'queued':
      default:
        return TaskDownloadState.queued;
    }
  }
}

/// Tasks view matching single.html with expandable stream metadata dashboards,
/// download state icon badges, and strictly NO borders.
class TasksView extends StatefulWidget {
  /// Creates a [TasksView] widget.
  const TasksView({
    super.key,
    this.tokens,
  });

  /// Optional active theme color tokens.
  final AppColorTokens? tokens;

  @override
  State<TasksView> createState() => _TasksViewState();
}

class _TasksViewState extends State<TasksView> {
  final TextEditingController _searchController = TextEditingController();
  String _searchQuery = '';
  final Set<String> _expandedTaskIds = <String>{};

  late List<TaskItemData> _tasks;

  static const List<TaskItemData> _demoTasks = <TaskItemData>[
    TaskItemData(
      id: 'task_1',
      stringEvent: 'download_update',
      stringTimestamp: '2026-09-07T22:45:10Z',
      stringAnimeName: 'Sousou no Frieren',
      intEpisodeNumber: 1,
      stringFilename: '[SubsPlease] Sousou no Frieren - 01 (1080p) [BD].mkv',
      stringDownloadStatus: 'completed',
      floatProgressPercentage: 100.0,
      intDownloadedBytes: 1420000000,
      intTotalBytes: 1420000000,
      floatSpeedMbps: 0.0,
      stringShortErrorMessage: '',
      stringErrorLogMessage: '',
    ),
    TaskItemData(
      id: 'task_2',
      stringEvent: 'download_update',
      stringTimestamp: '2026-09-07T23:19:54Z',
      stringAnimeName: 'Bocchi the Rock!',
      intEpisodeNumber: 8,
      stringFilename: '[Erai-raws] Bocchi the Rock! - 08 [1080p][Multiple Subtitle].mkv',
      stringDownloadStatus: 'in-progress',
      floatProgressPercentage: 64.0,
      intDownloadedBytes: 921600000,
      intTotalBytes: 1440000000,
      floatSpeedMbps: 14.8,
      stringShortErrorMessage: '',
      stringErrorLogMessage: '',
    ),
    TaskItemData(
      id: 'task_3',
      stringEvent: 'download_update',
      stringTimestamp: '2026-09-07T23:15:00Z',
      stringAnimeName: 'Chainsaw Man',
      intEpisodeNumber: 4,
      stringFilename: '[SubsPlease] Chainsaw Man - 04 (1080p) [WEBRip].mkv',
      stringDownloadStatus: 'queue',
      floatProgressPercentage: 0.0,
      intDownloadedBytes: 0,
      intTotalBytes: 1350000000,
      floatSpeedMbps: 0.0,
      stringShortErrorMessage: '',
      stringErrorLogMessage: '',
    ),
    TaskItemData(
      id: 'task_4',
      stringEvent: 'download_update',
      stringTimestamp: '2026-09-07T23:18:22Z',
      stringAnimeName: 'Cyberpunk: Edgerunners',
      intEpisodeNumber: 6,
      stringFilename: '[SubsPlease] Cyberpunk Edgerunners - 06 (1080p).mkv',
      stringDownloadStatus: 'failed',
      floatProgressPercentage: 38.5,
      intDownloadedBytes: 539000000,
      intTotalBytes: 1400000000,
      floatSpeedMbps: 0.0,
      stringShortErrorMessage: 'Connection reset by peer while downloading stream chunk #42',
      stringErrorLogMessage: 'Traceback (most recent call last):\n  File "stream_downloader.py", line 184, in download_chunk\n    socket.error: [Errno 104] Connection reset by peer\n  Pipeline failed at 38.5% completion.',
    ),
  ];

  @override
  void initState() {
    super.initState();
    _syncTasks();
  }

  void _syncTasks() {
    // If no tasks generated yet, show demo preview
    _tasks = List<TaskItemData>.from(_demoTasks);
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  void _toggleExpanded(String id) {
    setState(() {
      if (_expandedTaskIds.contains(id)) {
        _expandedTaskIds.remove(id);
      } else {
        _expandedTaskIds.add(id);
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final ThemeData theme = Theme.of(context);
    final ColorScheme colorScheme = theme.colorScheme;
    final AppColorTokens? tokens = widget.tokens;

    final Color searchBackground = tokens?.surfaceContainer ?? colorScheme.surfaceContainer;
    final Color onSurface = tokens?.onSurface ?? colorScheme.onSurface;
    final Color onSurfaceVariant = tokens?.onSurfaceVariant ?? colorScheme.onSurfaceVariant;

    return ValueListenableBuilder<List<TaskItemData>>(
      valueListenable: CliBridgeService.instance.tasksNotifier,
      builder: (BuildContext context, List<TaskItemData> liveTasks, _) {
        final List<TaskItemData> activeTasks = liveTasks.isNotEmpty ? liveTasks : _demoTasks;
        final List<TaskItemData> filteredTasks = activeTasks.where((TaskItemData task) {
          if (_searchQuery.isEmpty) return true;
          final String query = _searchQuery.toLowerCase();
          return task.title.toLowerCase().contains(query) ||
              task.stringFilename.toLowerCase().contains(query) ||
              task.stringAnimeName.toLowerCase().contains(query);
        }).toList();

        return Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: <Widget>[
            // Header Row: Search Input + Action Buttons
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: <Widget>[
                // Search Input Field
                Container(
                  width: 420.0,
                  height: AppTokens.searchInputHeight,
                  decoration: BoxDecoration(
                    color: searchBackground,
                    borderRadius: BorderRadius.circular(AppTokens.cornerFull),
                  ),
                  padding: const EdgeInsets.symmetric(horizontal: 20.0),
                  child: Row(
                    children: <Widget>[
                      Icon(
                        Icons.search_rounded,
                        size: 20.0,
                        color: onSurfaceVariant,
                      ),
                      const SizedBox(width: 12.0),
                      Expanded(
                        child: TextField(
                          controller: _searchController,
                          onChanged: (String value) => setState(() => _searchQuery = value),
                          style: TextStyle(
                            fontFamily: AppTokens.fontFamily,
                            fontSize: 14.5,
                            color: onSurface,
                          ),
                          decoration: InputDecoration(
                            isDense: true,
                            hintText: 'Search episode tasks...',
                            hintStyle: TextStyle(
                              fontFamily: AppTokens.fontFamily,
                              fontSize: 14.5,
                              color: onSurfaceVariant,
                            ),
                            border: InputBorder.none,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),

                // Actions Row with Unique Micro-Animations
                ValueListenableBuilder<bool>(
                  valueListenable: CliBridgeService.instance.isExecutingNotifier,
                  builder: (BuildContext context, bool isExecuting, _) {
                    return Row(
                      mainAxisSize: MainAxisSize.min,
                      children: <Widget>[
                        AppIconBtn(
                          icon: Icons.play_arrow_rounded,
                          tooltip: 'Start Tasks',
                          variant: isExecuting ? AppIconBtnVariant.standard : AppIconBtnVariant.primary,
                          animationType: AppIconAnimationType.shiftRight,
                          tokens: tokens,
                          onPressed: () => SubprocessService.instance.startTasks(),
                        ),
                        const SizedBox(width: 12.0),
                        AppIconBtn(
                          icon: Icons.stop_rounded,
                          tooltip: 'Stop Tasks',
                          variant: isExecuting ? AppIconBtnVariant.primary : AppIconBtnVariant.standard,
                          animationType: AppIconAnimationType.pulse,
                          tokens: tokens,
                          onPressed: () => SubprocessService.instance.stopTasks(),
                        ),
                      ],
                    );
                  },
                ),
              ],
            ),

            const SizedBox(height: 18.0),

            // Scrollable Task List with Rounded Overflow Clipping
            Expanded(
              child: ClipRRect(
                borderRadius: BorderRadius.circular(AppTokens.cornerMedium),
                child: ListView.separated(
                  itemCount: filteredTasks.length,
                  separatorBuilder: (BuildContext context, int index) => const SizedBox(height: 14.0),
                  itemBuilder: (BuildContext context, int index) {
                    final TaskItemData task = filteredTasks[index];
                    final bool isExpanded = _expandedTaskIds.contains(task.id);
                    return _TaskItemCard(
                      task: task,
                      isExpanded: isExpanded,
                      tokens: tokens,
                      onToggleExpand: () => _toggleExpanded(task.id),
                    );
                  },
                ),
              ),
            ),
          ],
        );
      },
    );
  }
}

class _TaskItemCard extends StatefulWidget {
  const _TaskItemCard({
    required this.task,
    required this.isExpanded,
    required this.onToggleExpand,
    this.tokens,
  });

  final TaskItemData task;
  final bool isExpanded;
  final VoidCallback onToggleExpand;
  final AppColorTokens? tokens;

  @override
  State<_TaskItemCard> createState() => _TaskItemCardState();
}

class _TaskItemCardState extends State<_TaskItemCard> {
  bool _isHovered = false;
  bool _isArrowHovered = false;

  @override
  Widget build(BuildContext context) {
    final ThemeData theme = Theme.of(context);
    final ColorScheme colorScheme = theme.colorScheme;
    final AppColorTokens? tokens = widget.tokens;

    final Color cardBackgroundColor = _isHovered
        ? (tokens?.surfaceContainerHigh ?? colorScheme.surfaceContainerHigh)
        : (tokens?.surfaceContainer ?? colorScheme.surfaceContainer);
    final Color detailBackgroundColor = tokens?.surfaceContainerLowest ?? colorScheme.surfaceContainerLowest;
    final Color onSurface = tokens?.onSurface ?? colorScheme.onSurface;
    final Color onSurfaceVariant = tokens?.onSurfaceVariant ?? colorScheme.onSurfaceVariant;

    final TaskDownloadState state = widget.task.state;
    final Color stateBackgroundColor = state.backgroundColor;
    final Color stateForegroundColor = state.foregroundColor;

    return MouseRegion(
      onEnter: (_) => setState(() => _isHovered = true),
      onExit: (_) => setState(() => _isHovered = false),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        decoration: BoxDecoration(
          color: cardBackgroundColor,
          borderRadius: BorderRadius.circular(AppTokens.cornerMedium),
        ),
        padding: const EdgeInsets.symmetric(horizontal: 20.0, vertical: 16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: <Widget>[
            // Top Main Row: Icon + Title/Progress + Expand Arrow
            Row(
              children: <Widget>[
                // Dynamic State-Driven Squircle Icon Badge
                AnimatedContainer(
                  duration: const Duration(milliseconds: 200),
                  width: AppTokens.iconButtonSize,
                  height: AppTokens.iconButtonSize,
                  decoration: BoxDecoration(
                    color: stateBackgroundColor,
                    borderRadius: BorderRadius.circular(AppTokens.cornerSquircle),
                  ),
                  alignment: Alignment.center,
                  child: Icon(
                    state.icon,
                    size: 22.0,
                    color: stateForegroundColor,
                  ),
                ),
                const SizedBox(width: 16.0),

                // Info Column: Title + Gradient Progress Bar (Clean without chaotic subtitle)
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: <Widget>[
                      Text(
                        widget.task.title,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: TextStyle(
                          fontFamily: AppTokens.fontFamily,
                          fontSize: 14.5,
                          fontWeight: FontWeight.w500,
                          color: onSurface,
                        ),
                      ),
                      const SizedBox(height: 8.0),
                      GradientProgressBar(
                        progress: widget.task.progress,
                        tokens: tokens,
                      ),
                    ],
                  ),
                ),

                const SizedBox(width: 12.0),

                // Expandable Dropdown Arrow Icon Button
                MouseRegion(
                  cursor: SystemMouseCursors.click,
                  onEnter: (_) => setState(() => _isArrowHovered = true),
                  onExit: (_) => setState(() => _isArrowHovered = false),
                  child: GestureDetector(
                    onTap: widget.onToggleExpand,
                    child: AnimatedContainer(
                      duration: const Duration(milliseconds: 180),
                      width: 36.0,
                      height: 36.0,
                      decoration: BoxDecoration(
                        color: _isArrowHovered
                            ? (tokens?.surfaceContainerHighest ?? colorScheme.surfaceContainerHighest)
                            : Colors.transparent,
                        borderRadius: BorderRadius.circular(AppTokens.cornerSquircle),
                      ),
                      alignment: Alignment.center,
                      child: AnimatedRotation(
                        turns: widget.isExpanded ? 0.5 : 0.0,
                        duration: const Duration(milliseconds: 240),
                        curve: Curves.easeInOutCubic,
                        child: Icon(
                          Icons.keyboard_arrow_down_rounded,
                          size: 24.0,
                          color: _isArrowHovered
                              ? (tokens?.primary ?? colorScheme.primary)
                              : onSurfaceVariant,
                        ),
                      ),
                    ),
                  ),
                ),
              ],
            ),

            // Expandable Structured Stream Event Metadata (Directly rendered without borders)
            AnimatedCrossFade(
              firstChild: const SizedBox.shrink(),
              secondChild: Padding(
                padding: const EdgeInsets.only(top: 16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: <Widget>[
                    // Stream Metrics Row: Status + Speed + Transferred Bytes
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: <Widget>[
                        // Status Badge Chip
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 10.0, vertical: 4.0),
                          decoration: BoxDecoration(
                            color: stateBackgroundColor,
                            borderRadius: BorderRadius.circular(AppTokens.cornerFull),
                          ),
                          child: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: <Widget>[
                              Icon(
                                state.icon,
                                size: 13.0,
                                color: stateForegroundColor,
                              ),
                              const SizedBox(width: 6.0),
                              Text(
                                state.statusLabel,
                                style: TextStyle(
                                  fontFamily: AppTokens.fontFamily,
                                  fontSize: 11.5,
                                  fontWeight: FontWeight.w500,
                                  color: stateForegroundColor,
                                ),
                              ),
                            ],
                          ),
                        ),

                        // Download Speed
                        Row(
                          mainAxisSize: MainAxisSize.min,
                          children: <Widget>[
                            Icon(
                              Icons.speed_rounded,
                              size: 15.0,
                              color: onSurfaceVariant,
                            ),
                            const SizedBox(width: 6.0),
                            Text(
                              widget.task.floatSpeedMbps > 0
                                  ? '${widget.task.floatSpeedMbps.toStringAsFixed(1)} MB/s'
                                  : '-- MB/s',
                              style: TextStyle(
                                fontFamily: AppTokens.fontFamily,
                                fontSize: 12.0,
                                color: onSurfaceVariant,
                              ),
                            ),
                          ],
                        ),

                        // Byte Transfer Ratio
                        Row(
                          mainAxisSize: MainAxisSize.min,
                          children: <Widget>[
                            Icon(
                              Icons.data_usage_rounded,
                              size: 15.0,
                              color: onSurfaceVariant,
                            ),
                            const SizedBox(width: 6.0),
                            Text(
                              '${_formatBytes(widget.task.intDownloadedBytes)} / ${_formatBytes(widget.task.intTotalBytes)} (${widget.task.floatProgressPercentage.toStringAsFixed(1)}%)',
                              style: TextStyle(
                                fontFamily: AppTokens.fontFamily,
                                fontSize: 12.0,
                                color: onSurfaceVariant,
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),

                    const SizedBox(height: 12.0),

                    // Secondary File Progress Bar
                    GradientProgressBar(
                      progress: widget.task.progress,
                      tokens: tokens,
                    ),

                    const SizedBox(height: 12.0),

                    // Stream Event Category and Timestamp Meta Row
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: <Widget>[
                        Row(
                          mainAxisSize: MainAxisSize.min,
                          children: <Widget>[
                            Icon(
                              Icons.stream_rounded,
                              size: 14.0,
                              color: onSurfaceVariant.withValues(alpha: 0.7),
                            ),
                            const SizedBox(width: 6.0),
                            Text(
                              'Event: ${widget.task.stringEvent}',
                              style: TextStyle(
                                fontFamily: AppTokens.codeFontFamily,
                                fontSize: 11.0,
                                color: onSurfaceVariant.withValues(alpha: 0.8),
                              ),
                            ),
                          ],
                        ),
                        Row(
                          mainAxisSize: MainAxisSize.min,
                          children: <Widget>[
                            Icon(
                              Icons.access_time_rounded,
                              size: 14.0,
                              color: onSurfaceVariant.withValues(alpha: 0.7),
                            ),
                            const SizedBox(width: 6.0),
                            Text(
                              'Updated: ${_formatTimestamp(widget.task.stringTimestamp)}',
                              style: TextStyle(
                                fontFamily: AppTokens.fontFamily,
                                fontSize: 11.0,
                                color: onSurfaceVariant.withValues(alpha: 0.8),
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),

                    // Error Diagnostic Section and Bottommost Terminal Icon Button (Normal Button Colors)
                    if (widget.task.isFailed) ...<Widget>[
                      const SizedBox(height: 12.0),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 14.0, vertical: 12.0),
                        decoration: BoxDecoration(
                          color: detailBackgroundColor,
                          borderRadius: BorderRadius.circular(AppTokens.cornerSmall),
                        ),
                        child: Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: <Widget>[
                            Padding(
                              padding: const EdgeInsets.only(top: 1.0),
                              child: Icon(
                                Icons.info_outline_rounded,
                                size: 16.0,
                                color: onSurfaceVariant,
                              ),
                            ),
                            const SizedBox(width: 10.0),
                            Expanded(
                              child: Text(
                                widget.task.stringShortErrorMessage.isNotEmpty
                                    ? widget.task.stringShortErrorMessage
                                    : 'Task failed during stream processing.',
                                style: TextStyle(
                                  fontFamily: AppTokens.fontFamily,
                                  fontSize: 12.5,
                                  height: 1.35,
                                  color: onSurface,
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 12.0),
                      Align(
                        alignment: Alignment.centerRight,
                        child: AppIconBtn(
                          icon: Icons.terminal_rounded,
                          tooltip: 'Open Log Message',
                          variant: AppIconBtnVariant.primary,
                          animationType: AppIconAnimationType.shiftRight,
                          tokens: tokens,
                          onPressed: () => SubprocessService.instance.openErrorLog(widget.task.id),
                        ),
                      ),
                    ],
                  ],
                ),
              ),
              crossFadeState: widget.isExpanded
                  ? CrossFadeState.showSecond
                  : CrossFadeState.showFirst,
              duration: const Duration(milliseconds: 240),
              sizeCurve: Curves.easeOutCubic,
            ),
          ],
        ),
      ),
    );
  }
}
