import streamlit as st
import google.generativeai as genai
import json
import re

# 1. Konfigurasi API Key Gemini via Streamlit Secrets
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("API Key tidak ditemukan di Streamlit Secrets!")
    st.stop()

# 2. Setup Model & Prompt (Optimasi Hemat Kuota & Token)
system_instruction = (
    "Anda adalah 'QuizMaster AI', seorang guru yang ahli membuat kuis interaktif yang ringkas. "
    "Tugas Anda adalah membuat TEPAT 3 soal kuis sesuai dengan topik yang diminta pengguna. "
    "Untuk menghemat token, berikan penjelasan yang padat, jelas, dan langsung ke inti materi. "
    "Anda WAJIB memberikan output dalam bentuk JSON dengan format objek tunggal seperti ini (jangan dibungkus dalam array/list []):\n"
    "{\n"
    "  \"quiz_title\": \"Judul Kuis\",\n"
    "  \"questions\": [\n"
    "    {\n"
    "      \"question\": \"Teks pertanyaan (Gunakan LaTeX jika ada rumus matematika, misal $f(x) = 3x^2$)\",\n"
    "      \"options\": [\"A. Pilihan A\", \"B. Pilihan B\", \"C. Pilihan C\", \"D. Pilihan D\"],\n"
    "      \"correct_answer\": \"A\",\n"
    "      \"explanation\": \"Penjelasan singkat & padat mengapa jawaban tersebut benar.\"\n"
    "    }\n"
    "  ]\n"
    "}"
)

model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    system_instruction=system_instruction,
    generation_config={"response_mime_type": "application/json", "temperature": 0.4}
)

# Fungsi pembantu untuk membersihkan text mentah dari Gemini sebelum di-load sebagai JSON
def clean_and_parse_json(raw_text):
    # Hilangkan blok pembungkus markdown ```json atau ``` jika ada
    cleaned = re.sub(r"^```[a-zA-Z]*\s*", "", raw_text.strip())
    cleaned = re.sub(r"\s*```$", "", cleaned.strip())
    
    # Load ke python dictionary
    parsed = json.loads(cleaned)
    
    # JIKA Gemini mengembalikan list berisi satu dict, ambil dict pertamanya saja
    if isinstance(parsed, list):
        if len(parsed) > 0:
            parsed = parsed[0]
        else:
            raise ValueError("Data JSON kosong.")
            
    return parsed

# 3. Inisialisasi State Manajemen di Streamlit
if "quiz_data" not in st.session_state:
    st.session_state.quiz_data = None
if "user_answers" not in st.session_state:
    st.session_state.user_answers = {}
if "submitted" not in st.session_state:
    st.session_state.submitted = False

# --- TAMPILAN UI ---
st.set_page_config(page_title="QuizMaster AI", layout="centered")
st.title("🧠 QuizMaster AI: Belajar Jadi Seru!")
st.write("Masukkan topik belajar, AI akan merancang kuis hemat kuota secara instan.")

# Form Pembuatan Kuis
topic_input = st.text_input("Mau belajar apa hari ini?", placeholder="Contoh: Kalkulus Integral, Logika Matematika, Python Loop")

if st.button("Generate Kuis Baru"):
    if topic_input:
        with st.spinner("AI sedang merancang 3 soal terbaik (Menghemat kuota)... 📝"):
            try:
                # Meminta kuis ke API Gemini
                response = model.generate_content(f"Buatkan kuis tentang: {topic_input}")
                
                # Menggunakan parser aman baru kita
                st.session_state.quiz_data = clean_and_parse_json(response.text)
                st.session_state.user_answers = {}  # Reset jawaban
                st.session_state.submitted = False  # Reset status submit
                st.success("Kuis berhasil dibuat! Silakan kerjakan di bawah.")
            except Exception as e:
                st.error("Gagal memuat kuis karena kesalahan format respons AI atau masalah koneksi. Coba klik 'Generate Kuis Baru' sekali lagi.")

st.write("---")

# --- PANEL JALANNYA KUIS ---
if st.session_state.quiz_data and isinstance(st.session_state.quiz_data, dict) and "questions" in st.session_state.quiz_data:
    st.header(f"📝 {st.session_state.quiz_data.get('quiz_title', 'Kuis AI')}")
    
    questions_list = st.session_state.quiz_data.get('questions', [])
    
    # 1. TAMPILKAN HASIL SKOR (Jika sudah di-submit)
    if st.session_state.submitted:
        correct_count = 0
        total_questions = len(questions_list)
        
        for idx, q in enumerate(questions_list):
            if st.session_state.user_answers.get(idx) == q.get('correct_answer'):
                correct_count += 1
                
        score_percentage = (correct_count / total_questions) * 100 if total_questions > 0 else 0
        
        st.subheader("📊 Hasil Evaluasi Kuis")
        col1, col2 = st.columns(2)
        with col1:
            st.metric(label="Skor Akhir Kamu", value=f"{score_percentage:.0f}%")
        with col2:
            st.metric(label="Total Benar", value=f"{correct_count} / {total_questions} Soal")
            
        # Feedback Selebrasi
        if score_percentage == 100:
            st.balloons()
            st.success("🌟 Luar biasa! Kamu berhasil menjawab semua dengan sempurna!")
        elif score_percentage >= 60:
            st.info("👍 Kerja bagus! Pemahamanmu sudah cukup baik, yuk tingkatkan lagi!")
        else:
            st.warning("📚 Jangan berkecil hati! Pelajari poin penjelasan di bawah untuk belajar kembali.")
        st.write("---")

    # 2. TAMPILKAN DAFTAR SOAL
    for idx, q in enumerate(questions_list):
        st.write(f"**Soal {idx+1}:** {q.get('question', '')}")
        options = q.get('options', [])
        
        # JIKA BELUM SUBMIT: Tampilkan pilihan ganda interaktif
        if not st.session_state.submitted:
            user_choice = st.radio(
                f"Pilih opsi untuk Soal {idx+1}:", 
                options=options, 
                key=f"q_{idx}",
                index=None
            )
            if user_choice:
                # Mengambil karakter pertama saja (A, B, C, atau D)
                st.session_state.user_answers[idx] = user_choice[0]
        
        # JIKA SUDAH SUBMIT: Tampilkan koreksi dan kunci jawaban
        else:
            user_ans = st.session_state.user_answers.get(idx, "Tidak Dijawab")
            correct_ans = q.get('correct_answer', 'A')
            
            st.write(f"Jawaban kamu: **{user_ans}**")
            
            if user_ans == correct_ans:
                st.success(f"🎯 **Benar!** Kunci jawaban: {correct_ans}")
            else:
                st.error(f"❌ **Salah.** Kunci jawaban yang benar: {correct_ans}")
                
            st.info(f"💡 **Penjelasan Singkat:** {q.get('explanation', '')}")
        st.write("")

    # 3. TOMBOL AKSI (SUBMIT / ULANGI)
    if not st.session_state.submitted:
        all_answered = len(st.session_state.user_answers) == len(questions_list)
        
        if st.button("Submit Semua Jawaban", disabled=not all_answered, help="Isi semua soal dahulu untuk membuka tombol"):
            st.session_state.submitted = True
            st.rerun()
    else:
        if st.button("Coba Kuis Lagi (Gunakan Soal yang Sama)"):
            st.session_state.submitted = False
            st.session_state.user_answers = {}
            st.rerun()
