import streamlit as st
import google.generativeai as genai
import json

if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("API Key tidak ditemukan di Streamlit Secrets!")
    st.stop()

system_instruction = (
    "Anda adalah 'QuizMaster AI', seorang guru yang ahli membuat kuis interaktif yang ringkas. "
    "Tugas Anda adalah membuat TEPAT 3 soal kuis sesuai dengan topik yang diminta pengguna. "
    "Untuk menghemat token, berikan penjelasan yang padat, jelas, dan langsung ke inti materi. "
    "Anda WAJIB memberikan output dalam bentuk JSON (HANYA JSON, tanpa markdown http://googleusercontent.com/immersive_entry_chip/0). "
)
    

model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    system_instruction=system_instruction,
    generation_config={"response_mime_type": "application/json", "temperature": 0.5}
)

if "quiz_data" not in st.session_state:
    st.session_state.quiz_data = None
if "user_answers" not in st.session_state:
    st.session_state.user_answers = {}
if "submitted" not in st.session_state:
    st.session_state.submitted = False

st.set_page_config(page_title="QuizMaster AI", layout="centered")
st.title("🧠 QuizMaster AI: Belajar Jadi Seru!")
st.write("Masukkan topik yang ingin kamu pelajari, dan biarkan AI menyusun kuis interaktif untukmu.")

topic_input = st.text_input("Mau belajar apa hari ini?", placeholder="Contoh: Kalkulus turunan, Aljabar Linear, Sejarah Indonesia")

if st.button("Generate Kuis Baru"):
    if topic_input:
        with st.spinner("AI sedang merancang soal terbaik untukmu... 📝"):
            try:
                response = model.generate_content(f"Buatkan kuis tentang: {topic_input}")
                
                st.session_state.quiz_data = json.loads(response.text)
                st.session_state.user_answers = {} 
                st.session_state.submitted = False 
                st.success("Kuis berhasil dibuat! Selamat mengerjakan.")
            except Exception as e:
                st.error("Gagal memuat kuis karena batasan kuota API atau kesalahan format. Silakan coba lagi.")

st.write("---")

if st.session_state.quiz_data:
    st.header(f"📝 {st.session_state.quiz_data['quiz_title']}")
    
    for idx, q in enumerate(st.session_state.quiz_data['questions']):
        st.write(f"**Soal {idx+1}:** {q['question']}")
        
        if not st.session_state.submitted:
            user_choice = st.radio(
                f"Pilih jawaban untuk Soal {idx+1}:", 
                options=q['options'], 
                key=f"q_{idx}",
                index=None 
            )
            if user_choice:
                st.session_state.user_answers[idx] = user_choice[0]
        else:
            user_ans = st.session_state.user_answers.get(idx, "Belum Dijawab")
            correct_ans = q['correct_answer']
            
            st.write(f"Jawaban kamu: **{user_ans}**")
            
            if user_ans == correct_ans:
                st.success(f"🎯 **Benar!** Jawaban kunci adalah {correct_ans}.")
            else:
                st.error(f"❌ **Salah.** Jawaban yang benar adalah {correct_ans}.")
                
            st.info(f"💡 **Penjelasan:** {q['explanation']}")
        st.write("")

    if not st.session_state.submitted and st.session_state.quiz_data:
        if st.button("Submit Semua Jawaban"):
            st.session_state.submitted = True
            st.rerun()
            
    if st.session_state.submitted:
        if st.button("Coba Kuis Lagi"):
            st.session_state.submitted = False
            st.session_state.user_answers = {}
            st.rerun()
