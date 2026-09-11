"""
Standard Events
-----------------
تعريف مركزي لأسماء الأحداث القياسية في cai، عشان أي حد في المشروع
(بما فيهم Plugins خارجية) يستخدم نفس الأسماء بالظبط بدل ما يخترع
Strings حرة عرضة للأخطاء الإملائية.

كل حدث موثّق بالـ payload المتوقع فيه (كتوثيق، مش enforced في runtime
لتفادي تعقيد زائد، لكن الـ Handlers لازم تحترم الشكل ده).
"""


class Events:
    # دورة حياة المهام (do / team / template)
    TASK_STARTED = "TaskStarted"        # {task: str}
    TASK_FINISHED = "TaskFinished"      # {task: str, success: bool}
    TASK_STEP_DONE = "TaskStepDone"     # {step_description: str, success: bool}

    # الإضافات
    PLUGIN_LOADED = "PluginLoaded"      # {name: str}
    PLUGIN_UNLOADED = "PluginUnloaded"  # {name: str}

    # المزودين
    PROVIDER_CHANGED = "ProviderChanged"  # {old: str, new: str}
    MODEL_CHANGED = "ModelChanged"        # {old: str, new: str}

    # تنفيذ الأوامر
    COMMAND_EXECUTED = "CommandExecuted"  # {command: str, success: bool, risk: str}
    COMMAND_BLOCKED = "CommandBlocked"    # {command: str, reason: str}

    # الأخطاء
    ERROR_OCCURRED = "ErrorOccurred"      # {command: str, error: str}
    ERROR_FIXED = "ErrorFixed"            # {command: str, fix: str}

    # الجلسات
    SESSION_STARTED = "SessionStarted"    # {session_id: str}
    SESSION_ENDED = "SessionEnded"        # {session_id: str}

    # الملفات
    FILE_EDITED = "FileEdited"            # {path: str, snapshot_id: str}
    FILE_RESTORED = "FileRestored"        # {path: str, snapshot_id: str}

    # الأمان
    SECRET_DETECTED = "SecretDetected"    # {file: str, pattern: str}

    # الوظائف الخلفية
    JOB_STARTED = "JobStarted"            # {job_id: str, command: str}
    JOB_FINISHED = "JobFinished"          # {job_id: str, success: bool}

    # سير العمل
    WORKFLOW_STARTED = "WorkflowStarted"  # {workflow_name: str}
    WORKFLOW_FINISHED = "WorkflowFinished"  # {workflow_name: str, success: bool}
