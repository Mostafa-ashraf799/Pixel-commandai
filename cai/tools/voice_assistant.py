"""
Voice Assistant (Experimental)
---------------------------------
دعم أولي للتحكم الصوتي: تسجيل صوت من المايك، تحويله لنص عبر أي محرك
Speech-to-Text متاح محليًا، ثم تمرير النص لنفس مسار الأوامر العادي.

ملاحظة: هذه الميزة تعتمد على مكتبات اختيارية (speech_recognition + pyaudio)
غير مضمنة في requirements الأساسية لأنها تحتاج تبعيات نظام إضافية
(portaudio) قد لا تكون متاحة في كل البيئات. الكلاس هنا يتحقق من توفرها
ويرجع رسالة واضحة بدل الانهيار لو غير مثبتة.
"""

from typing import Optional

try:
    import speech_recognition as sr
    _HAS_SR = True
except ImportError:
    _HAS_SR = False


class VoiceAssistant:
    def __init__(self, language: str = "ar-EG"):
        self.language = language
        self.available = _HAS_SR
        if _HAS_SR:
            self.recognizer = sr.Recognizer()

    def is_available(self) -> bool:
        return self.available

    def installation_hint(self) -> str:
        return (
            "الأوامر الصوتية تحتاج تثبيت مكتبات إضافية:\n"
            "  pip install SpeechRecognition pyaudio\n"
            "على Linux قد تحتاج أيضًا: sudo apt install portaudio19-dev"
        )

    def listen_once(self, timeout: int = 5) -> Optional[str]:
        """يسجل من المايك لفترة محددة ويحاول تحويلها لنص."""
        if not self.available:
            return None

        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=timeout)
            return self.recognizer.recognize_google(audio, language=self.language)
        except Exception:
            return None

    def transcribe_file(self, audio_path: str) -> Optional[str]:
        """يحوّل ملف صوتي (wav) موجود مسبقًا لنص، مفيد للاستخدام غير التفاعلي."""
        if not self.available:
            return None
        try:
            with sr.AudioFile(audio_path) as source:
                audio = self.recognizer.record(source)
            return self.recognizer.recognize_google(audio, language=self.language)
        except Exception:
            return None
