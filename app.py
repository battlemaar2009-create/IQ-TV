from flask import Flask, request, redirect
import os

app = Flask(__name__)

# هذا الرابط هو الذي سيتصل به تطبيقك
@app.route('/stream/<path:filename>')
def stream(filename):
    # استبدل هذا الرابط بعنوان IP الخاص بهاتفك (إذا كنت ستستضيف TorrServer على هاتفك)
    # أو برابط سيرفر آخر إذا كان لديك مصدر مختلف
    base_url = "http://YOUR_PUBLIC_IP:8090" 
    query = request.query_string.decode()
    return redirect(f"{base_url}/stream/{filename}?{query}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
  
