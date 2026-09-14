import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import '../../core/constants/app_tokens.dart';
import '../../core/services/cli_bridge_service.dart';
import '../../core/services/subprocess_service.dart';
import '../../core/theme/app_palettes.dart';
import '../common/app_icon_btn.dart';
import '../common/app_icon_square.dart';
import '../common/gradient_progress_bar.dart';

/// Settings view matching single.html with flush top alignment,
/// sleek section titles, preferred quality selector,
/// and unique hover micro-animations.
class SettingsView extends StatefulWidget {
  /// Creates a [SettingsView] widget.
  const SettingsView({
    super.key,
    this.tokens,
  });

  /// Optional active theme color tokens.
  final AppColorTokens? tokens;

  @override
  State<SettingsView> createState() => _SettingsViewState();
}

class _SettingsViewState extends State<SettingsView> {
  final TextEditingController _folderController =
      TextEditingController(text: 'D:/Anime/Animepahe_Library');
  final TextEditingController _ignoreInputController = TextEditingController();

  String _selectedQuality = '1080p';
  String _selectedAudio = 'Subbed';
  double _modelDownloadProgress = 0.0;
  String _modelStatusLabel = 'Idle (Model Needed)';
  bool _isDownloadingModel = false;

  static const List<String> _qualityOptions = <String>[
    '1080p',
    '720p',
    '480p',
    '360p',
  ];

  static const List<String> _audioOptions = <String>[
    'Subbed',
    'Dubbed',
  ];

  @override
  void initState() {
    super.initState();
    _loadInitialState();
    CliBridgeService.instance.configNotifier.addListener(_onConfigChanged);
    CliBridgeService.instance.loadInitialConfig();
    SubprocessService.instance.listIgnored();
  }

  void _loadInitialState() {
    final CliConfigState config = CliBridgeService.instance.configNotifier.value;
    if (config.targetDirectory.isNotEmpty) {
      _folderController.text = config.targetDirectory.replaceAll(r'\', '/');
    }
    _selectedQuality = config.preferredQuality;
    _selectedAudio = config.preferredAudio;
    if (config.isModelInstalled) {
      _modelDownloadProgress = 1.0;
      _modelStatusLabel = 'Installed (${config.modelSizeMb.toStringAsFixed(1)} MB)';
    } else if (!_isDownloadingModel) {
      _modelDownloadProgress = 0.0;
      _modelStatusLabel = 'Idle (Model Needed)';
    }
  }

  void _onConfigChanged() {
    if (mounted) {
      setState(() {
        _loadInitialState();
      });
    }
  }

  @override
  void dispose() {
    CliBridgeService.instance.configNotifier.removeListener(_onConfigChanged);
    _folderController.dispose();
    _ignoreInputController.dispose();
    super.dispose();
  }

  Future<void> _handleBrowseDirectory() async {
    await SubprocessService.instance.browseAnimeFolder();

    try {
      final String? selectedDirectory = await FilePicker.platform.getDirectoryPath();
      if (selectedDirectory != null && mounted) {
        final String normalized = selectedDirectory.replaceAll(r'\', '/');
        setState(() {
          _folderController.text = normalized;
        });
        await SubprocessService.instance.setTargetDirectory(normalized);
      }
    } catch (exception) {
      debugPrint('Error picking directory: $exception');
    }
  }

  void _handleQualitySelected(String quality) {
    if (_selectedQuality == quality) return;
    setState(() {
      _selectedQuality = quality;
    });
    SubprocessService.instance.setPreferredQuality(quality);
  }

  void _handleAudioSelected(String audio) {
    if (_selectedAudio == audio) return;
    setState(() {
      _selectedAudio = audio;
    });
    SubprocessService.instance.setPreferredAudio(audio);
  }

  void _handleDownloadModel() {
    if (_isDownloadingModel) return;
    setState(() {
      _isDownloadingModel = true;
      _modelStatusLabel = 'Starting download...';
      _modelDownloadProgress = 0.05;
    });

    SubprocessService.instance.downloadAiParserModel(
      onProgress: (double p) {
        if (mounted) {
          setState(() {
            _modelDownloadProgress = p;
            _modelStatusLabel = 'Downloading (${(p * 100).toInt()}%)';
          });
        }
      },
      onError: (String err) {
        if (mounted) {
          setState(() {
            _isDownloadingModel = false;
            _modelStatusLabel = 'Error: $err';
          });
        }
      },
      onComplete: () {
        if (mounted) {
          setState(() {
            _isDownloadingModel = false;
            _modelDownloadProgress = 1.0;
            _modelStatusLabel = 'Installed & Ready';
          });
        }
      },
    );
  }

  Future<void> _handleAddIgnored() async {
    final String text = _ignoreInputController.text.trim();
    if (text.isEmpty) return;
    _ignoreInputController.clear();
    await SubprocessService.instance.addIgnoredItem(text);
  }

  Future<void> _handleRemoveIgnored(String item) async {
    await SubprocessService.instance.removeIgnoredItem(item);
  }

  Future<void> _handleResetIgnored() async {
    await SubprocessService.instance.resetIgnoredItems();
  }

  @override
  Widget build(BuildContext context) {
    final ThemeData theme = Theme.of(context);
    final ColorScheme colorScheme = theme.colorScheme;
    final AppColorTokens? tokens = widget.tokens;

    final Color cardBackgroundColor = tokens?.surfaceContainer ?? colorScheme.surfaceContainer;
    final Color inputBackgroundColor = tokens?.surfaceContainerHigh ?? colorScheme.surfaceContainerHigh;
    final Color onSurface = tokens?.onSurface ?? colorScheme.onSurface;
    final Color onSurfaceVariant = tokens?.onSurfaceVariant ?? colorScheme.onSurfaceVariant;

    return SingleChildScrollView(
      padding: EdgeInsets.zero,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: <Widget>[
          // Section 1: Anime Folder
          Container(
            decoration: BoxDecoration(
              color: cardBackgroundColor,
              borderRadius: BorderRadius.circular(AppTokens.cornerMedium),
            ),
            padding: const EdgeInsets.symmetric(horizontal: 20.0, vertical: 18.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                // Title Group
                Row(
                  children: <Widget>[
                    AppIconSquare(
                      icon: Icons.folder_open_rounded,
                      tokens: tokens,
                    ),
                    const SizedBox(width: 12.0),
                    Text(
                      'Anime Folder',
                      style: TextStyle(
                        fontFamily: AppTokens.fontFamily,
                        fontSize: 15.0,
                        fontWeight: FontWeight.w500,
                        color: onSurface,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 8.0),
                Text(
                  'It must be a folder containing a list of anime folders with names taken from Animepahe.',
                  style: TextStyle(
                    fontFamily: AppTokens.fontFamily,
                    fontSize: 13.5,
                    height: 1.45,
                    color: onSurfaceVariant,
                  ),
                ),
                const SizedBox(height: 14.0),
                // Input Row: Path TextField + Browse Button
                Row(
                  children: <Widget>[
                    Expanded(
                      child: Container(
                        height: 48.0,
                        decoration: BoxDecoration(
                          color: inputBackgroundColor,
                          borderRadius: BorderRadius.circular(AppTokens.cornerSmall),
                        ),
                        padding: const EdgeInsets.symmetric(horizontal: 16.0),
                        alignment: Alignment.centerLeft,
                        child: TextField(
                          controller: _folderController,
                          style: TextStyle(
                            fontFamily: AppTokens.codeFontFamily,
                            fontSize: 13.5,
                            color: onSurface,
                          ),
                          decoration: const InputDecoration(
                            isDense: true,
                            border: InputBorder.none,
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(width: 12.0),
                    AppIconBtn(
                      icon: Icons.folder_open_rounded,
                      tooltip: 'Browse Directory',
                      animationType: AppIconAnimationType.bounceUp,
                      tokens: tokens,
                      onPressed: _handleBrowseDirectory,
                    ),
                  ],
                ),
              ],
            ),
          ),

          const SizedBox(height: 16.0),

          // Section 2: AI Episode Parser
          Container(
            decoration: BoxDecoration(
              color: cardBackgroundColor,
              borderRadius: BorderRadius.circular(AppTokens.cornerMedium),
            ),
            padding: const EdgeInsets.symmetric(horizontal: 20.0, vertical: 18.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                // Title Group
                Row(
                  children: <Widget>[
                    AppIconSquare(
                      icon: Icons.smart_toy_rounded,
                      tokens: tokens,
                    ),
                    const SizedBox(width: 12.0),
                    Text(
                      'AI Episode Parser',
                      style: TextStyle(
                        fontFamily: AppTokens.fontFamily,
                        fontSize: 15.0,
                        fontWeight: FontWeight.w500,
                        color: onSurface,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 8.0),
                Text(
                  'An AI model is needed to ensure that the app works smoothly',
                  style: TextStyle(
                    fontFamily: AppTokens.fontFamily,
                    fontSize: 13.5,
                    height: 1.45,
                    color: onSurfaceVariant,
                  ),
                ),
                const SizedBox(height: 14.0),
                // Progress Row: Progress Track Column + Download Button
                Row(
                  crossAxisAlignment: CrossAxisAlignment.center,
                  children: <Widget>[
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: <Widget>[
                          GradientProgressBar(
                            progress: _modelDownloadProgress,
                            tokens: tokens,
                          ),
                          const SizedBox(height: 8.0),
                          Text(
                            _modelStatusLabel,
                            style: TextStyle(
                              fontFamily: AppTokens.fontFamily,
                              fontSize: 12.5,
                              fontWeight: FontWeight.w500,
                              color: onSurfaceVariant,
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(width: 20.0),
                    AppIconBtn(
                      icon: Icons.download_rounded,
                      tooltip: 'Download Model',
                      variant: AppIconBtnVariant.primary,
                      animationType: AppIconAnimationType.shiftDown,
                      tokens: tokens,
                      onPressed: _handleDownloadModel,
                    ),
                  ],
                ),
              ],
            ),
          ),

          const SizedBox(height: 16.0),

          // Section 3 & 4: Preferred Quality & Audio Preference (2 Columns)
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              // Column 1: Preferred Quality
              Expanded(
                child: Container(
                  decoration: BoxDecoration(
                    color: cardBackgroundColor,
                    borderRadius: BorderRadius.circular(AppTokens.cornerMedium),
                  ),
                  padding: const EdgeInsets.symmetric(horizontal: 20.0, vertical: 18.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: <Widget>[
                      // Title Group
                      Row(
                        children: <Widget>[
                          AppIconSquare(
                            icon: Icons.high_quality_rounded,
                            tokens: tokens,
                          ),
                          const SizedBox(width: 12.0),
                          Text(
                            'Preferred Quality',
                            style: TextStyle(
                              fontFamily: AppTokens.fontFamily,
                              fontSize: 15.0,
                              fontWeight: FontWeight.w500,
                              color: onSurface,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 8.0),
                      Text(
                        'Select preferred download video resolution quality.',
                        style: TextStyle(
                          fontFamily: AppTokens.fontFamily,
                          fontSize: 13.5,
                          height: 1.45,
                          color: onSurfaceVariant,
                        ),
                      ),
                      const SizedBox(height: 14.0),
                      // Quality Selection Row
                      Container(
                        height: 48.0,
                        decoration: BoxDecoration(
                          color: inputBackgroundColor,
                          borderRadius: BorderRadius.circular(AppTokens.cornerSmall),
                        ),
                        clipBehavior: Clip.antiAlias,
                        child: Row(
                          children: _qualityOptions.map((String quality) {
                            final bool isSelected = _selectedQuality == quality;
                            return Expanded(
                              child: _QualityPillButton(
                                label: quality,
                                isSelected: isSelected,
                                tokens: tokens,
                                onTap: () => _handleQualitySelected(quality),
                              ),
                            );
                          }).toList(),
                        ),
                      ),
                    ],
                  ),
                ),
              ),

              const SizedBox(width: 16.0),

              // Column 2: Audio Preference (Subbed / Dubbed)
              Expanded(
                child: Container(
                  decoration: BoxDecoration(
                    color: cardBackgroundColor,
                    borderRadius: BorderRadius.circular(AppTokens.cornerMedium),
                  ),
                  padding: const EdgeInsets.symmetric(horizontal: 20.0, vertical: 18.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: <Widget>[
                      // Title Group
                      Row(
                        children: <Widget>[
                          AppIconSquare(
                            icon: Icons.subtitles_rounded,
                            tokens: tokens,
                          ),
                          const SizedBox(width: 12.0),
                          Text(
                            'Audio Preference',
                            style: TextStyle(
                              fontFamily: AppTokens.fontFamily,
                              fontSize: 15.0,
                              fontWeight: FontWeight.w500,
                              color: onSurface,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 8.0),
                      Text(
                        'Choose between subbed or dubbed anime releases.',
                        style: TextStyle(
                          fontFamily: AppTokens.fontFamily,
                          fontSize: 13.5,
                          height: 1.45,
                          color: onSurfaceVariant,
                        ),
                      ),
                      const SizedBox(height: 14.0),
                      // Audio Selection Row
                      Container(
                        height: 48.0,
                        decoration: BoxDecoration(
                          color: inputBackgroundColor,
                          borderRadius: BorderRadius.circular(AppTokens.cornerSmall),
                        ),
                        clipBehavior: Clip.antiAlias,
                        child: Row(
                          children: _audioOptions.map((String audio) {
                            final bool isSelected = _selectedAudio == audio;
                            return Expanded(
                              child: _QualityPillButton(
                                label: audio,
                                isSelected: isSelected,
                                tokens: tokens,
                                onTap: () => _handleAudioSelected(audio),
                              ),
                            );
                          }).toList(),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),

          const SizedBox(height: 16.0),

          // Section 5: Ignored Folders & Files
          Container(
            decoration: BoxDecoration(
              color: cardBackgroundColor,
              borderRadius: BorderRadius.circular(AppTokens.cornerMedium),
            ),
            padding: const EdgeInsets.symmetric(horizontal: 20.0, vertical: 18.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                // Header Row: Title & Clear All Action
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: <Widget>[
                    Row(
                      children: <Widget>[
                        AppIconSquare(
                          icon: Icons.folder_off_rounded,
                          tokens: tokens,
                        ),
                        const SizedBox(width: 12.0),
                        Text(
                          'Ignored Folders & Files',
                          style: TextStyle(
                            fontFamily: AppTokens.fontFamily,
                            fontSize: 15.0,
                            fontWeight: FontWeight.w500,
                            color: onSurface,
                          ),
                        ),
                      ],
                    ),
                    ValueListenableBuilder<List<String>>(
                      valueListenable: CliBridgeService.instance.ignoredItemsNotifier,
                      builder: (BuildContext context, List<String> ignoredList, _) {
                        if (ignoredList.isEmpty) return const SizedBox.shrink();
                        return AppIconBtn(
                          icon: Icons.delete_sweep_rounded,
                          tooltip: 'Reset Ignored List',
                          animationType: AppIconAnimationType.pulse,
                          tokens: tokens,
                          onPressed: _handleResetIgnored,
                        );
                      },
                    ),
                  ],
                ),
                const SizedBox(height: 8.0),
                Text(
                  'Excluded anime folders or files will be skipped during automated library scans and downloads.',
                  style: TextStyle(
                    fontFamily: AppTokens.fontFamily,
                    fontSize: 13.5,
                    height: 1.45,
                    color: onSurfaceVariant,
                  ),
                ),
                const SizedBox(height: 14.0),
                // Input Row: Add Item TextField + Add Button
                Row(
                  children: <Widget>[
                    Expanded(
                      child: Container(
                        height: 48.0,
                        decoration: BoxDecoration(
                          color: inputBackgroundColor,
                          borderRadius: BorderRadius.circular(AppTokens.cornerSmall),
                        ),
                        padding: const EdgeInsets.symmetric(horizontal: 16.0),
                        alignment: Alignment.centerLeft,
                        child: TextField(
                          controller: _ignoreInputController,
                          onSubmitted: (_) => _handleAddIgnored(),
                          style: TextStyle(
                            fontFamily: AppTokens.codeFontFamily,
                            fontSize: 13.5,
                            color: onSurface,
                          ),
                          decoration: InputDecoration(
                            isDense: true,
                            hintText: 'Enter folder or file name to ignore...',
                            hintStyle: TextStyle(
                              fontFamily: AppTokens.fontFamily,
                              fontSize: 13.5,
                              color: onSurfaceVariant,
                            ),
                            border: InputBorder.none,
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(width: 12.0),
                    AppIconBtn(
                      icon: Icons.add_rounded,
                      tooltip: 'Add to Ignore List',
                      animationType: AppIconAnimationType.rotate90,
                      variant: AppIconBtnVariant.primary,
                      tokens: tokens,
                      onPressed: _handleAddIgnored,
                    ),
                  ],
                ),
                const SizedBox(height: 14.0),
                // Dynamic Ignored Items List
                ValueListenableBuilder<List<String>>(
                  valueListenable: CliBridgeService.instance.ignoredItemsNotifier,
                  builder: (BuildContext context, List<String> ignoredList, _) {
                    if (ignoredList.isEmpty) {
                      return Container(
                        width: double.infinity,
                        padding: const EdgeInsets.symmetric(vertical: 14.0, horizontal: 16.0),
                        decoration: BoxDecoration(
                          color: inputBackgroundColor.withValues(alpha: 0.5),
                          borderRadius: BorderRadius.circular(AppTokens.cornerSmall),
                        ),
                        child: Text(
                          'No items currently ignored. All library folders and files will be processed.',
                          style: TextStyle(
                            fontFamily: AppTokens.fontFamily,
                            fontSize: 13.0,
                            fontStyle: FontStyle.italic,
                            color: onSurfaceVariant,
                          ),
                        ),
                      );
                    }

                    return Wrap(
                      spacing: 8.0,
                      runSpacing: 8.0,
                      children: ignoredList.map((String item) {
                        return Container(
                          decoration: BoxDecoration(
                            color: inputBackgroundColor,
                            borderRadius: BorderRadius.circular(AppTokens.cornerSmall),
                          ),
                          padding: const EdgeInsets.only(left: 12.0, right: 8.0, top: 6.0, bottom: 6.0),
                          child: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: <Widget>[
                              Text(
                                item,
                                style: TextStyle(
                                  fontFamily: AppTokens.codeFontFamily,
                                  fontSize: 13.0,
                                  color: onSurface,
                                ),
                              ),
                              const SizedBox(width: 6.0),
                              GestureDetector(
                                onTap: () => _handleRemoveIgnored(item),
                                child: MouseRegion(
                                  cursor: SystemMouseCursors.click,
                                  child: Icon(
                                    Icons.close_rounded,
                                    size: 16.0,
                                    color: onSurfaceVariant,
                                  ),
                                ),
                              ),
                            ],
                          ),
                        );
                      }).toList(),
                    );
                  },
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _QualityPillButton extends StatefulWidget {
  const _QualityPillButton({
    required this.label,
    required this.isSelected,
    required this.onTap,
    this.tokens,
  });

  final String label;
  final bool isSelected;
  final VoidCallback onTap;
  final AppColorTokens? tokens;

  @override
  State<_QualityPillButton> createState() => _QualityPillButtonState();
}

class _QualityPillButtonState extends State<_QualityPillButton> {
  bool _isHovered = false;

  @override
  Widget build(BuildContext context) {
    final ThemeData theme = Theme.of(context);
    final ColorScheme colorScheme = theme.colorScheme;
    final AppColorTokens? tokens = widget.tokens;

    final Color activeBackground = tokens?.primary ?? colorScheme.primary;
    final Color activeTextColor = tokens?.onPrimary ?? colorScheme.onPrimary;
    final Color inactiveHoverBackground = (tokens?.surfaceContainerHighest ?? colorScheme.surfaceContainerHighest).withValues(alpha: 0.5);
    final Color inactiveTextColor = _isHovered
        ? (tokens?.onSurface ?? colorScheme.onSurface)
        : (tokens?.onSurfaceVariant ?? colorScheme.onSurfaceVariant);

    final Color pillBackground = widget.isSelected
        ? activeBackground
        : (_isHovered ? inactiveHoverBackground : Colors.transparent);
    final Color textColor = widget.isSelected ? activeTextColor : inactiveTextColor;

    return MouseRegion(
      cursor: SystemMouseCursors.click,
      onEnter: (_) => setState(() => _isHovered = true),
      onExit: (_) => setState(() => _isHovered = false),
      child: GestureDetector(
        onTap: widget.onTap,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 180),
          curve: Curves.easeInOutCubic,
          height: double.infinity,
          decoration: BoxDecoration(
            color: pillBackground,
            borderRadius: BorderRadius.circular(AppTokens.cornerSmall),
          ),
          alignment: Alignment.center,
          child: Text(
            widget.label,
            style: TextStyle(
              fontFamily: AppTokens.fontFamily,
              fontSize: 13.0,
              fontWeight: widget.isSelected ? FontWeight.w600 : FontWeight.w500,
              color: textColor,
            ),
          ),
        ),
      ),
    );
  }
}
