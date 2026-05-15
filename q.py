import os
import re
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
from supabase import create_client, Client

# --- البيانات الثابتة (مدمجة بالكامل) ---
API_ID = 36988553
API_HASH = '2299d5e458048bbaf5e4186289c02ae7'
SUPABASE_URL = "https://bfgjorejtfzttchfvmrc.supabase.co"
SUPABASE_KEY = "EyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJmZ2pvcmVqdGZ6dHRjaGZ2bXJjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzg4MzM2NzUsImV4cCI6MjA5NDQwOTY3NX0.vPWy_h_02O9gsIwkuzSn2_NUWwSpBm5oQyUJDm0zAIE"

# جلب الجلسة من Secrets في GitHub لضمان الأمان وتجاوز التحقق الثنائي
SESSION_STR = os.environ.get("TG_SESSION")

# تهيئة عميل Supabase للاتصال بقاعدة البيانات
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def clean_movie_title(text):
    if not text: return "Unknown Title"
    # تنظيف الأسماء من رموز Markdown والرموز الخاصة
    name = re.sub(r'[\*_`\[\]\(\)\-\.]', ' ', text)
    return ' '.join(name.split()).strip()

def detect_quality(text):
    # نظام رصد الجودات الذكي
    text = text.lower()
    for q in ['2160p', '4k', '1080p', '720p', '480p', '360p']:
        if q in text:
            return q
    return "HD"

async def main():
    if not SESSION_STR:
        print("❌ خطأ حرج: لم يتم العثور على متغير TG_SESSION في GitHub Secrets.")
        return

    async with TelegramClient(StringSession(SESSION_STR), API_ID, API_HASH) as client:
        print("🚀 المحرك يعمل الآن.. جاري مسح القنوات وتحديث المكتبة.")
        
        # 1. البحث التلقائي في القنوات
        async for dialog in client.iter_dialogs():
            if dialog.is_channel:
                print(f"📂 فحص القناة: {dialog.name}")
                async for message in client.iter_messages(dialog.id, limit=80):
                    if message.video or (message.document and "video" in (message.document.mime_type or "")):
                        raw_txt = message.text or (message.file.name if message.file else "")
                        title = clean_movie_title(raw_txt)
                        quality = detect_quality(raw_txt)
                        
                        # إنشاء رابط الرسالة للقنوات العامة والخاصة
                        clean_id = str(dialog.id).replace("-100", "")
                        msg_link = f"https://t.me/c/{clean_id}/{message.id}"
                        
                        # إرسال البيانات لـ Supabase (التحديث التلقائي يمنع التكرار)
                        data = {
                            "title": title,
                            "link": msg_link,
                            "quality": quality,
                            "channel_name": dialog.name
                        }
                        try:
                            supabase.table("movies_library").upsert(data, on_conflict="link").execute()
                        except Exception as e:
                            print(f"⚠️ فشل تحديث فيلم: {title} | {e}")

        # 2. معالجة طلبات الجودات من جدول user_requests
        try:
            pending_reqs = supabase.table("user_requests").select("*").eq("status", "pending").execute()
            for req in pending_reqs.data:
                search_query = f"{req['movie_title']} {req['requested_quality']}"
                print(f"🔍 تنفيذ طلب مستخدم: {search_query}")
                
                # إرسال الطلب للبوت (استبدل المعرف بالبوت الذي تفضله)
                await client.send_message("@SearchBot", search_query)
                
                # تحديث حالة الطلب لضمان عدم التكرار
                supabase.table("user_requests").update({"status": "processing"}).eq("id", req['id']).execute()
        except Exception as e:
            print(f"⚠️ خطأ في معالجة الطلبات: {e}")

        print("✅ اكتملت دورة العمل بنجاح.")

if __name__ == "__main__":
    asyncio.run(main())
