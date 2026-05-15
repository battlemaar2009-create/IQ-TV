import os
import re
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
from supabase import create_client, Client

# البيانات مدمجة 100%
API_ID = 36988553
API_HASH = '2299d5e458048bbaf5e4186289c02ae7'
SUPABASE_URL = "https://bfgjorejtfzttchfvmrc.supabase.co"
SUPABASE_KEY = "EyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJmZ2pvcmVqdGZ6dHRjaGZ2bXJjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzg4MzM2NzUsImV4cCI6MjA5NDQwOTY3NX0.vPWy_h_02O9gsIwkuzSn2_NUWwSpBm5oQyUJDm0zAIE"

SESSION_STR = os.environ.get("TG_SESSION")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

async def main():
    async with TelegramClient(StringSession(SESSION_STR), API_ID, API_HASH) as client:
        
        # أولاً: معالجة طلبات المستخدمين المعلقة (تلبية النواقص فوراً)
        reqs = supabase.table("user_requests").select("*").eq("status", "pending").execute()
        for req in reqs.data:
            movie_name = req['movie_title']
            supabase.table("user_requests").update({"status": "processing"}).eq("id", req['id']).execute()
            print(f"🎯 معالجة طلب مستخدم: {movie_name}")
            # (هنا يتم البحث المكثف عن هذا الفيلم بالتحديد)

        # ثانياً: المسح التلقائي (جلب الأفلام الجديدة من القنوات)
        print("📡 بدأ المسح الدوري للقنوات...")
        async for dialog in client.iter_dialogs():
            if dialog.is_channel:
                async for message in client.iter_messages(dialog.id, limit=150): # تم زيادة الحد للمسح التلقائي
                    if message.video or message.document:
                        raw_text = message.text or (message.file.name if message.file else "")
                        if raw_text:
                            clean_id = str(dialog.id).replace("-100", "")
                            link = f"https://t.me/c/{clean_id}/{message.id}"
                            
                            # تخزين البيانات
                            data = {
                                "title": raw_text[:100], # تجنب العناوين الطويلة جداً
                                "link": link,
                                "quality": "HD",
                                "channel_name": dialog.name
                            }
                            try:
                                supabase.table("movies_library").upsert(data, on_conflict="link").execute()
                                # إذا كان هذا الفيلم مطلوباً، حدّث حالته لمكتمل
                                supabase.table("user_requests").update({"status": "completed"}).eq("movie_title", raw_text).execute()
                            except: continue
        print("✅ اكتملت دورة العمل.")

if __name__ == "__main__":
    asyncio.run(main())
