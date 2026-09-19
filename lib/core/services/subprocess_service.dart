import 'dart:async';
import 'dart:io';
import 'package:flutter/foundation.dart';
import 'cli_bridge_service.dart';

/// Service providing extensible subprocess execution callback templates.
/// Bridges UI events with the active `CliBridgeService` background engine.
class SubprocessService {
  /// Private constructor for [SubprocessService] singleton pattern.
  SubprocessService._();

  /// Singleton shared instance of [SubprocessService].
  static final SubprocessService instance = SubprocessService._();

  /// Generic subprocess runner template.
  /// Replace command, arguments, and environment variables when wiring real backend processes.
  ///
  /// [actionName] identifies the invoked operation.
  /// [arguments] optional map of key-value parameters.
  Future<ProcessResult?> executeTemplateSubprocess({
    required String actionName,
    Map<String, Object?>? arguments,
  }) async {
    debugPrint('[SubprocessService] Action invoked: $actionName | Args: $arguments');
    return null;
  }

  /// Hook: Start Tasks Execution.
  Future<void> startTasks({
    String? preferredResolution,
  }) async {
    await executeTemplateSubprocess(actionName: 'start_tasks');
    unawaited(
      CliBridgeService.instance.startAutomation(
        preferredResolution: preferredResolution,
      ),
    );
  }

  /// Hook: Stop Tasks Execution.
  /// Removes automated task scheduler triggers and terminates active automation process.
  Future<void> stopTasks() async {
    await executeTemplateSubprocess(actionName: 'stop_tasks');
    await CliBridgeService.instance.removeTaskScheduler();
    CliBridgeService.instance.pauseAutomation();
  }

  /// Hook: Pause Tasks Execution (alias for stopTasks).
  Future<void> pauseTasks() async {
    await stopTasks();
  }

  /// Hook: Browse Anime Library Folder.
  Future<String?> browseAnimeFolder() async {
    await executeTemplateSubprocess(actionName: 'browse_anime_folder');
    return null;
  }

  /// Hook: Download / Initialize AI Episode Parser Model.
  Future<void> downloadAiParserModel({
    void Function(double progress)? onProgress,
    void Function(String error)? onError,
    VoidCallback? onComplete,
  }) async {
    await executeTemplateSubprocess(actionName: 'download_ai_parser_model');
    unawaited(
      CliBridgeService.instance.downloadModel(
        onProgress: onProgress ?? (_) {},
        onError: onError ?? (_) {},
        onComplete: onComplete ?? () {},
      ),
    );
  }

  /// Hook: Start / Trigger Automation Schedule.
  ///
  /// [activeDays] contains selected weekday names.
  /// [triggerTimes] contains scheduled 12-hour timestamp strings.
  Future<void> startAutomationSchedule({
    required List<String> activeDays,
    required List<String> triggerTimes,
  }) async {
    final Map<String, Object?> argumentsPayload = <String, Object?>{
      'activeDays': activeDays,
      'triggerTimes': triggerTimes,
    };
    await executeTemplateSubprocess(
      actionName: 'start_automation_schedule',
      arguments: argumentsPayload,
    );
    await CliBridgeService.instance.startScheduler(
      activeDays: activeDays,
      triggerTimes: triggerTimes,
    );
  }

  /// Hook: Stop / Pause Automation Schedule.
  Future<void> stopAutomationSchedule() async {
    await executeTemplateSubprocess(actionName: 'stop_automation_schedule');
    await CliBridgeService.instance.stopScheduler();
  }

  /// Hook: Add Schedule Trigger Time.
  ///
  /// [time] is the 12-hour formatted time string to add.
  Future<void> addTriggerTime(String time) async {
    final Map<String, Object?> argumentsPayload = <String, Object?>{
      'time': time,
    };
    await executeTemplateSubprocess(
      actionName: 'add_trigger_time',
      arguments: argumentsPayload,
    );
  }

  /// Hook: Remove Schedule Trigger Time.
  ///
  /// [time] is the 12-hour formatted time string to remove.
  Future<void> removeTriggerTime(String time) async {
    final Map<String, Object?> argumentsPayload = <String, Object?>{
      'time': time,
    };
    await executeTemplateSubprocess(
      actionName: 'remove_trigger_time',
      arguments: argumentsPayload,
    );
  }

  /// Hook: Open Task Error Log Message.
  ///
  /// [taskId] identifies the task item whose log was requested.
  Future<void> openErrorLog(String taskId) async {
    final Map<String, Object?> argumentsPayload = <String, Object?>{
      'taskId': taskId,
    };
    await executeTemplateSubprocess(
      actionName: 'open_error_log',
      arguments: argumentsPayload,
    );
  }

  /// Hook: Update Preferred Video Quality Setting.
  ///
  /// [quality] represents the chosen resolution ("1080p", "720p", "480p", "360p").
  Future<void> setPreferredQuality(String quality) async {
    final Map<String, Object?> argumentsPayload = <String, Object?>{
      'quality': quality,
    };
    await executeTemplateSubprocess(
      actionName: 'set_preferred_quality',
      arguments: argumentsPayload,
    );
    await CliBridgeService.instance.setPreferredQuality(quality);
  }

  /// Hook: Update Preferred Audio / Release Type Setting.
  ///
  /// [audio] represents the chosen audio language type ("Subbed" or "Dubbed").
  Future<void> setPreferredAudio(String audio) async {
    final Map<String, Object?> argumentsPayload = <String, Object?>{
      'audio': audio,
    };
    await executeTemplateSubprocess(
      actionName: 'set_preferred_audio',
      arguments: argumentsPayload,
    );
    await CliBridgeService.instance.setPreferredAudio(audio);
  }

  /// Hook: Update Target Anime Directory.
  Future<void> setTargetDirectory(String directoryPath) async {
    await CliBridgeService.instance.setTargetDirectory(directoryPath);
  }

  /// Hook: Update Pages to Scrape Count Setting.
  ///
  /// [pages] count integer for pagination scan depth.
  Future<void> setPagesToScrape(int pages) async {
    final Map<String, Object?> argumentsPayload = <String, Object?>{
      'pages': pages,
    };
    await executeTemplateSubprocess(
      actionName: 'set_pages_to_scrape',
      arguments: argumentsPayload,
    );
  }

  /// Hook: List Ignored Items.
  Future<List<String>> listIgnored() async {
    await executeTemplateSubprocess(actionName: 'list_ignored');
    return CliBridgeService.instance.listIgnored();
  }

  /// Hook: Add Ignored Item.
  Future<void> addIgnoredItem(String item) async {
    final Map<String, Object?> argumentsPayload = <String, Object?>{
      'item': item,
    };
    await executeTemplateSubprocess(
      actionName: 'add_ignored_item',
      arguments: argumentsPayload,
    );
    await CliBridgeService.instance.addIgnoredItem(item);
  }

  /// Hook: Remove Ignored Item.
  Future<void> removeIgnoredItem(String item) async {
    final Map<String, Object?> argumentsPayload = <String, Object?>{
      'item': item,
    };
    await executeTemplateSubprocess(
      actionName: 'remove_ignored_item',
      arguments: argumentsPayload,
    );
    await CliBridgeService.instance.removeIgnoredItem(item);
  }

  /// Hook: Reset Ignored Items.
  Future<void> resetIgnoredItems() async {
    await executeTemplateSubprocess(actionName: 'reset_ignored_items');
    await CliBridgeService.instance.resetIgnoredItems();
  }
}
