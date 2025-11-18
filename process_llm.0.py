import sys
import os
import openai

# Make sure you set OPENAI_API_KEY in your environment before running:
# export OPENAI_API_KEY="your_api_key"

openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise RuntimeError("OpenAI API key is not set in environment variable OPENAI_API_KEY")

def call_llm_api(prompt):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-5.1",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=3500
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"Error calling LLM API: {e}")
        return None

def chunk_text(text, max_chunk_size=3000):
    paragraphs = text.split('\n\n')
    chunks = []
    current_chunk = ''
    for para in paragraphs:
        if len(current_chunk) + len(para) > max_chunk_size:
            chunks.append(current_chunk.strip())
            current_chunk = para + '\n\n'
        else:
            current_chunk += para + '\n\n'
    if current_chunk:
        chunks.append(current_chunk.strip())
    return chunks

def build_prompt(chunk):
    return f"""
انت نموذج لغوي ذكي ومتقدم مختص بفهم النصوص العربية.

قمت لك بإضافة نص عربي، أرجو منك أن:
- تحدد العناوين والعناوين الفرعية فيه.
- تحدد أرقام الصفحات الموجودة في النص.
- تحدد الحواشي (الهوامش) وترتبها بشكل صحيح.
- تعيد صياغة النص في ملف HTML منسق بشكل جيد يحتوي على:
  * العناوين في وسم <h1>
  * العناوين الفرعية في وسم <h2>
  * الحواشي في أسفل صفحاتهم مع روابط في النص.
  * أرقام الصفحات مذكورة بشكل واضح.
  * اتجاه النص من اليمين لليسار.
- احرص على وضع فواصل الأسطر حسب نص المصدر.

النص:
{chunk}
"""

def process_file_with_llm(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        full_text = f.read()

    chunks = chunk_text(full_text)

    all_html_parts = []
    for i, chunk in enumerate(chunks):
        print(f"Processing chunk {i+1} of {len(chunks)}...")
        prompt = build_prompt(chunk)
        response = call_llm_api(prompt)
        if response is None:
            print("LLM call failed on this chunk, skipping...")
            continue
        all_html_parts.append(response)

    complete_html = "<html dir=\"rtl\" lang=\"ar\"><head><meta charset=\"UTF-8\"><title>مصنف عربي منسق</title></head><body>"
    complete_html += "\n<hr style=\"border-top:1px dotted #888;margin:20px 0;\">\n".join(all_html_parts)
    complete_html += "</body></html>"

    with open(output_file, 'w', encoding='utf-8') as outf:
        outf.write(complete_html)

    print(f"Structured HTML saved to {output_file}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python llm_arabic_formatter.py input.txt output.html")
        sys.exit(1)
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    process_file_with_llm(input_path, output_path)
