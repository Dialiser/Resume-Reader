import streamlit as st
import pdfplumber
import re
import json
from datetime import datetime

st.set_page_config(page_title="Resume Skill Extractor", layout="wide", page_icon="📄")

# Sidebar
with st.sidebar:
    st.header("📘 About")
    st.markdown("""
    This tool helps you:
    - 📤 Upload a PDF Resume  
    - 🧠 Extract important information  
    - 💾 Save and search stored resumes  
    - 🔍 Filter by skills

    Made for the Windsurf AI Assignment.
    """)
    st.markdown("----")
    st.info("👉 Upload your resume to get started!")

st.title("📄 Resume Skill Extractor")
st.caption("Extract Name, Email, Phone, Skills, and Work Experience from PDF resumes.")

# Extract raw text from PDF
def extract_text_from_pdf(uploaded_file):
    text = ""
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

# Extract structured fields
def extract_fields(text):
    email = re.findall(r"[\w\.-]+@[\w\.-]+", text)
    phone = re.findall(r"\+?\d[\d\s()-]{8,}\d", text)
    name = text.split("\n")[0] if text else "N/A"
    skills = re.findall(r"(Python|Java|C\+\+|SQL|Machine Learning|Data Analysis|React|Node\.js|AWS|Typescript|MongoDB)", text, re.IGNORECASE)
    work_experience = extract_work_experience(text)
    
    return {
        "Name": name.strip(),
        "Email": email[0] if email else "Not found",
        "Phone": phone[0] if phone else "Not found",
        "Skills": list(set([s.strip().title() for s in skills])) if skills else "Not found",
        "Work Experience": work_experience,
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

# Improved Work Experience Extractor with Company & Date Highlighting
def extract_work_experience(text):
    match = re.search(r"(Experience|Work History|Professional Background)(.*?)(Education|Skills|Projects|$)", text, re.IGNORECASE | re.DOTALL)
    if not match:
        return []

    experience_text = match.group(2).strip()

    # Heuristic split using likely company/job start indicators
    experience_blocks = re.split(r"(?:\n|\.)\s*(?=(Tata|Teachnook|Google|Amazon|Intern|Engineer|Analyst|Developer))", experience_text, flags=re.IGNORECASE)

    # Recombine to complete blocks
    formatted_experiences = []
    buffer = ""
    for part in experience_blocks:
        if part.strip() == "":
            continue
        if buffer:
            formatted_experiences.append(buffer.strip())
        buffer = part

    formatted_experiences.append(buffer.strip())

    # Highlight Company & Date
    final_output = []
    for block in formatted_experiences:
        if not block.strip():
            continue

        highlighted = "• " + block

        company_match = re.search(r"(?P<company>[A-Z][\w &,-]{2,})", block)
        date_match = re.search(r"(?P<date>(\b\d{4}\b)[^.\n]{0,40}(\b\d{4}\b|Present|Now|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec))", block, re.IGNORECASE)

        if company_match:
            highlighted = highlighted.replace(company_match.group("company"), f"**🧑‍💼 {company_match.group('company')}**", 1)
        if date_match:
            highlighted = highlighted.replace(date_match.group("date"), f"🗓️ `{date_match.group('date')}`", 1)

        final_output.append(highlighted.strip())

    return final_output

# Save results to file
def save_to_file(data):
    try:
        with open("resume_data.json", "a", encoding="utf-8") as f:
            f.write(json.dumps(data) + "\n")
    except Exception as e:
        st.error(f"❌ Error saving data: {e}")

# Load stored data
def load_saved_resumes():
    try:
        with open("resume_data.json", "r", encoding="utf-8") as f:
            return [json.loads(line) for line in f]
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        st.warning("⚠️ Corrupted JSON data.")
        return []

# === GUI ===
uploaded_file = st.file_uploader("📤 Upload a Resume (PDF only)", type=["pdf"], help="Only PDF resumes are supported.")

if uploaded_file:
    text = extract_text_from_pdf(uploaded_file)
    extracted_data = extract_fields(text)

    st.success("✅ Resume processed successfully!")
    with st.expander("🔍 View Extracted Resume Information", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**👤 Name:** `{extracted_data['Name']}`")
            st.markdown(f"**📧 Email:** `{extracted_data['Email']}`")
            st.markdown(f"**📞 Phone:** `{extracted_data['Phone']}`")
            st.markdown(f"**🕓 Timestamp:** `{extracted_data['Timestamp']}`")
        with col2:
            st.markdown("**🛠️ Skills:**")
            if isinstance(extracted_data["Skills"], list):
                st.code(", ".join(extracted_data["Skills"]))
            else:
                st.warning("No skills found.")

            st.markdown("**💼 Work Experience:**")
            if isinstance(extracted_data["Work Experience"], list) and extracted_data["Work Experience"]:
                for job in extracted_data["Work Experience"]:
                    st.markdown(job)
                    st.markdown(" ")  # space between jobs
            else:
                st.warning("No work experience found.")

    save_to_file(extracted_data)

st.markdown("----")
st.subheader("📚 Stored Resumes")

all_resumes = load_saved_resumes()

if all_resumes:
    st.caption(f"🧾 Total Resumes Stored: `{len(all_resumes)}`")

    filter_toggle = st.checkbox("🎯 Enable Skill Filtering")

    if filter_toggle:
        available_skills = sorted({skill for r in all_resumes for skill in r.get("Skills", []) if isinstance(r.get("Skills"), list)})
        skill_filter = st.multiselect("Select skills to filter resumes:", options=available_skills)
    else:
        skill_filter = []

    for res in all_resumes:
        if not skill_filter or any(skill in res.get("Skills", []) for skill in skill_filter):
            with st.expander(f"📝 {res['Name']} — {res['Email']} ({res['Timestamp']})", expanded=False):
                st.markdown(f"- **📞 Phone:** `{res['Phone']}`")
                st.markdown(f"- **🛠️ Skills:** `{', '.join(res['Skills']) if isinstance(res['Skills'], list) else res['Skills']}`")
                st.markdown("- **💼 Work Experience:**")
                if isinstance(res['Work Experience'], list):
                    for job in res['Work Experience']:
                        st.markdown(job)
                        st.markdown(" ")
                else:
                    st.write(res['Work Experience'])
else:
    st.info("No resumes stored yet. Upload a resume to get started.")
