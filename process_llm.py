import sys
import os
from openai import OpenAI
from bs4 import BeautifulSoup

client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key=os.getenv("OPENROUTER_API_KEY"),
)

# max_chunks = 3000  # Adjust based on token limits
# max_chunks = 100000  # Adjust based on token limits
max_chunks = 30000  # Adjust based on token limits

def call_llm_api(prompt):
    try:
        # response = openai.ChatCompletion.create(
        #     model="gpt-5.1",
        #     messages=[{"role": "user", "content": prompt}],
        #     temperature=0.2,
        #     max_tokens=3500
        # )
        response = client.chat.completions.create(
            # model="openai/gpt-oss-20b:free",
            # model="google/gemma-3-27b-it:free",
            # model="mistralai/mistral-small-3.2-24b-instruct:free",
            model="nousresearch/hermes-3-llama-3.1-405b:free",
            extra_body={"reasoning": {"enabled": True}},
            messages=[{"role": "user", "content": prompt}],
            # temperature=0.2,
            # max_tokens=3500
        )
        print(response.choices[0].message.content)
        
        return response.choices[0].message.content.strip().strip('`')
    except Exception as e:
        print(f"Error calling LLM API: {e}")
        return None

def chunk_text(text, max_chunk_size=max_chunks):
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

#     return f"""
# انت نموذج لغوي ذكي ومتقدم مختص بفهم النصوص العربية.

# قمت لك بإضافة نص عربي، أرجو منك أن:
# - تحدد العناوين والعناوين الفرعية فيه.
# - تحدد أرقام الصفحات الموجودة في النص.
# - تحدد الحواشي (الهوامش) وترتبها بشكل صحيح.
# - تعيد صياغة النص في ملف HTML منسق بشكل جيد يحتوي على:
#   * العناوين في وسم <h1>
#   * العناوين الفرعية في وسم <h2>
#   * الحواشي في أسفل صفحاتهم مع روابط في النص.
#   * أرقام الصفحات مذكورة بشكل واضح.
#   * اتجاه النص من اليمين لليسار.
# - احرص على وضع فواصل الأسطر حسب نص المصدر.

# النص:
# {chunk}
# """

    return f"""
أنت نموذج لغوي متقدم قادر على فهم النصوص العربية وتنسيقها.

يرجى قراءة النص العربي التالي وتحليله. المطلوب:
- التعرف على العناوين والعناوين الفرعية بكل وضوح.
- التعرف على أرقام الصفحات الظاهرة في النص.
- التعرف على الحواشي وتحديد أماكنها بدقة.
- إخراج النص مُنسقًا على هيئة صفحة HTML كاملة مع:
  * العناوين في وسم <h1>
  * العناوين الفرعية في وسم <h2>
  * الحواشي معرفة ومرفقة في أسفل النص مع روابط نصية لها.
  * فواصل صفحات واضحة مع أرقام الصفحات.
  * النص منسق من اليمين إلى اليسار (dir="rtl").
- المحافظة على فواصل الأسطر كما هي واضحة في النص.

النص للمعالجة:

{chunk}

يرجى إخراج الصفحة HTML فقط. لا تضف أي شرح أو كود برمجي آخر.
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

        # get only inner HTML of the body tag
        soup = BeautifulSoup(response, 'html.parser')
        response = soup.body.decode_contents() if soup.body else response
        all_html_parts.append(response)
        if i == 1:
            break  # Remove this line to process all chunks

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
