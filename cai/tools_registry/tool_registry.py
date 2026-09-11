"""
Tool Registry (Real Tool Calling)
------------------------------------
الفرق الجوهري بين ده وبين اللي كان موجود قبل كده: قبل كده الـ AI كان
"بيتكلم" عن أوامر (يولّد نص Terminal)، والـ ExecutionEngine هو اللي
كان بيفهمها ويشغّلها كـ subprocess.

دلوقتي: أي Tool مسجّل هنا بيتحول لـ JSON Schema بصيغة Function Calling
القياسية (نفس صيغة OpenAI/Gemini/Groq)، ويتبعت مع كل رسالة للـ AI.
الـ AI يقدر "ينادي" الأداة مباشرة (tool_call) بدل ما يكتب أمر Terminal،
والـ ToolExecutor هو اللي بيستقبل النداء وينفذ الكود البايثون الحقيقي
المرتبط بيه (FileManager.open() مثلاً)، مش بيمرره كنص لـ shell.

مثال على الفرق:
    قبل: الـ AI يرد بنص "run cat file.txt" -> ExecutionEngine ينفذه كـ subprocess.
    دلوقتي: الـ AI يرد بـ tool_call={"name": "read_file", "arguments": {"path": "file.txt"}}
            -> ToolRegistry ينادي مباشرة على الدالة البايثون المسجّلة.

ده أدق وأأمن (مفيش command injection عبر نص حر) وأسرع (مفيش تحويل
لـ shell command ورجوع).
"""

import inspect
import json
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional


@dataclass
class ToolParameter:
    name: str
    type: str  # "string" | "number" | "boolean" | "array" | "object"
    description: str
    required: bool = True
    enum: Optional[List[str]] = None


@dataclass
class ToolDefinition:
    name: str
    description: str
    parameters: List[ToolParameter]
    handler: Callable[..., Any]
    requires_confirmation: bool = False  # للأدوات الحساسة (حذف ملف، تنفيذ أمر خطير...)

    def to_schema(self) -> Dict[str, Any]:
        """يحول تعريف الأداة لصيغة JSON Schema متوافقة مع OpenAI/Gemini function calling."""
        properties = {}
        required = []
        for p in self.parameters:
            prop: Dict[str, Any] = {"type": p.type, "description": p.description}
            if p.enum:
                prop["enum"] = p.enum
            properties[p.name] = prop
            if p.required:
                required.append(p.name)

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            },
        }


@dataclass
class ToolCallResult:
    tool_name: str
    success: bool
    result: Any = None
    error: Optional[str] = None

    def to_message_content(self) -> str:
        if self.success:
            return json.dumps({"result": self.result}, ensure_ascii=False, default=str)
        return json.dumps({"error": self.error}, ensure_ascii=False)


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}

    def register(
        self,
        name: str,
        description: str,
        parameters: List[ToolParameter],
        handler: Callable[..., Any],
        requires_confirmation: bool = False,
    ) -> None:
        self._tools[name] = ToolDefinition(
            name=name, description=description, parameters=parameters,
            handler=handler, requires_confirmation=requires_confirmation,
        )

    def unregister(self, name: str) -> bool:
        if name in self._tools:
            del self._tools[name]
            return True
        return False

    def get(self, name: str) -> Optional[ToolDefinition]:
        return self._tools.get(name)

    def list_tools(self) -> List[str]:
        return list(self._tools.keys())

    def get_schemas(self, only: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """يرجع قائمة الـ JSON Schemas الجاهزة للإرسال في بارامتر tools للـ Provider."""
        tools = self._tools.values()
        if only:
            tools = [t for t in tools if t.name in only]
        return [t.to_schema() for t in tools]

    def call(self, name: str, arguments: Dict[str, Any], confirm_callback: Optional[Callable] = None) -> ToolCallResult:
        tool = self._tools.get(name)
        if not tool:
            return ToolCallResult(tool_name=name, success=False, error=f"أداة غير مسجّلة: {name}")

        if tool.requires_confirmation and confirm_callback:
            approved = confirm_callback(tool, arguments)
            if not approved:
                return ToolCallResult(tool_name=name, success=False, error="تم رفض تنفيذ الأداة من المستخدم.")

        try:
            # فلترة الوسائط لتطابق فقط ما تقبله الدالة فعليًا (حماية من hallucinated params)
            sig = inspect.signature(tool.handler)
            valid_keys = set(sig.parameters.keys())
            filtered_args = {k: v for k, v in arguments.items() if k in valid_keys}

            result = tool.handler(**filtered_args)
            return ToolCallResult(tool_name=name, success=True, result=result)
        except Exception as e:
            return ToolCallResult(tool_name=name, success=False, error=str(e))
