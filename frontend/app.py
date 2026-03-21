"""
frontend/app.py - Streamlit UI for the Resume Analyzer.
"""
import time
import requests
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

API_BASE = "http://localhost:8000/api"

st.set_page_config(
    page_title="AI Resume Analyzer",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .main-header { font-size: 2.4rem; font-weight: 700; color: #1a1a2e; margin-bottom: 0.2rem; }
    .sub-header  { font-size: 1rem; color: #555; margin-bottom: 2rem; }
    .shortlisted { background:#d4efdf; border-left:4px solid #27ae60; padding:0.5rem 1rem; border-radius:6px; margin:4px 0; }
    .not-listed  { background:#fde8e8; border-left:4px solid #e74c3c; padding:0.5rem 1rem; border-radius:6px; margin:4px 0; }
    .tag { display:inline-block; background:#e8f4fd; color:#2980b9; border-radius:20px; padding:2px 10px; margin:2px; font-size:0.8rem; }
    .tag-red   { display:inline-block; background:#fde8e8; color:#c0392b; border-radius:20px; padding:2px 10px; margin:2px; font-size:0.8rem; }
    .tag-green { display:inline-block; background:#d4efdf; color:#1e8449; border-radius:20px; padding:2px 10px; margin:2px; font-size:0.8rem; }
    .api-warning { background:#fff3cd; border-left:4px solid #ffc107; padding:1rem; border-radius:6px; margin:8px 0; }
</style>
""", unsafe_allow_html=True)


# ─── Session State ────────────────────────────────────────────────────────────
def init_state():
    defaults = {
        "file_ids": [],
        "uploaded_files_info": [],
        "job_profile_id": None,
        "job_profile_data": None,
        "ranking_results": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()


# ─── API Helpers ──────────────────────────────────────────────────────────────
def api_upload(files):
    try:
        file_tuples = []
        for f in files:
            ext = f.name.split(".")[-1].lower()
            mime = "application/pdf" if ext == "pdf" else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            file_tuples.append(("files", (f.name, f.getvalue(), mime)))
        r = requests.post(f"{API_BASE}/upload_resume", files=file_tuples, timeout=60)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to backend. Is the FastAPI server running on port 8000?")
    except Exception as e:
        st.error(f"Upload failed: {e}")
    return None


def api_analyze_job(job_role, job_desc):
    try:
        r = requests.post(f"{API_BASE}/analyze_job",
                          json={"job_role": job_role, "job_description": job_desc},
                          timeout=60)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"Job analysis failed: {e}")
    return None


def api_rank_candidates(file_ids, job_profile_id):
    try:
        r = requests.post(f"{API_BASE}/rank_candidates",
                          json={"file_ids": file_ids, "job_profile_id": job_profile_id},
                          timeout=300)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"Ranking failed: {e}")
    return None


def api_get_candidate(candidate_id):
    try:
        r = requests.get(f"{API_BASE}/candidate/{candidate_id}", timeout=30)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"Could not fetch candidate: {e}")
    return None


def api_export(job_profile_id, fmt="csv"):
    try:
        r = requests.get(f"{API_BASE}/export_shortlist",
                         params={"job_profile_id": job_profile_id, "format": fmt},
                         timeout=30)
        r.raise_for_status()
        return r.content
    except Exception as e:
        st.error(f"Export failed: {e}")
    return None


# ─── UI Helpers ───────────────────────────────────────────────────────────────
def render_tags(items, color=""):
    css = f"tag-{color}" if color else "tag"
    return " ".join(f'<span class="{css}">{i}</span>' for i in (items or []))


def score_label(score):
    """Plain text score label — safe for expander titles."""
    if score >= 7:
        return f"★ {score:.1f}/10"
    elif score >= 5:
        return f"◆ {score:.1f}/10"
    else:
        return f"✗ {score:.1f}/10"


def make_gauge(score, title="Overall Score"):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        title={"text": title, "font": {"size": 14}},
        number={"suffix": "/10", "font": {"size": 22, "color": "#1a1a2e"}},
        gauge={
            "axis": {"range": [0, 10], "tickwidth": 1},
            "bar": {"color": "#667eea"},
            "steps": [
                {"range": [0, 4],  "color": "#fde8e8"},
                {"range": [4, 7],  "color": "#fef9e7"},
                {"range": [7, 10], "color": "#d4efdf"},
            ],
            "threshold": {"line": {"color": "#764ba2", "width": 3}, "value": 7},
        },
    ))
    fig.update_layout(height=200, margin=dict(l=20, r=20, t=40, b=10),
                      paper_bgcolor="rgba(0,0,0,0)")
    return fig


def api_key_warning():
    st.markdown("""
    <div class="api-warning">
    ⚠️ <strong>AI analysis returned no results.</strong><br>
    Your API key may be missing or invalid. Add it to your <code>.env</code> file:<br>
    <code>OPENROUTER_API_KEY=sk-or-v1-your-key-here</code><br>
    Get a free key at <strong>openrouter.ai</strong> then restart the backend.
    </div>
    """, unsafe_allow_html=True)


# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📋 Resume Analyzer")
    st.markdown("---")
    st.markdown(f"**Step 1:** Upload Resumes {'✅' if st.session_state.file_ids else '⬜'}")
    st.markdown(f"**Step 2:** Set Job Profile {'✅' if st.session_state.job_profile_id else '⬜'}")
    st.markdown(f"**Step 3:** Analyze & Rank {'✅' if st.session_state.ranking_results else '⬜'}")
    st.markdown("---")

    if st.session_state.job_profile_data:
        jp = st.session_state.job_profile_data
        st.markdown(f"**Role:** {jp.get('job_role', '')}")
        st.markdown(f"**Experience:** {jp.get('experience_level', 'N/A')}")
        skills = jp.get("required_skills", [])
        if skills:
            st.markdown("**Required Skills:**")
            for s in skills[:8]:
                st.markdown(f"  • {s}")

    st.markdown("---")
    if st.button("🔄 Reset Session", use_container_width=True):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()


# ─── Header ───────────────────────────────────────────────────────────────────
st.markdown('<h1 class="main-header">🤖 AI Resume Analyzer</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Upload resumes · Set job requirements · Get AI-powered rankings & insights</p>',
            unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["📤 Upload", "💼 Job Profile", "🏆 Rankings", "📄 Reports"])


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 – UPLOAD
# ═══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.subheader("Step 1 — Upload Candidate Resumes")
    st.markdown("Upload up to **20 resumes** in PDF or DOCX format.")

    uploaded = st.file_uploader(
        "Drop resumes here",
        type=["pdf", "docx"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )

    col1, col2 = st.columns([2, 1])
    with col1:
        upload_btn = st.button("📤 Upload Resumes", type="primary",
                               disabled=not uploaded, use_container_width=True)
    with col2:
        st.metric("Files Selected", len(uploaded) if uploaded else 0)

    if upload_btn and uploaded:
        with st.spinner(f"Uploading {len(uploaded)} file(s)..."):
            result = api_upload(uploaded)
        if result:
            st.session_state.file_ids = [f["file_id"] for f in result["uploaded"]]
            st.session_state.uploaded_files_info = result["uploaded"]
            st.success(f"✅ Successfully uploaded **{result['total']} resume(s)**")

    if st.session_state.uploaded_files_info:
        st.markdown("### Uploaded Resumes")
        df = pd.DataFrame(st.session_state.uploaded_files_info)
        df.columns = ["File ID", "File Name", "Type"]
        df["File ID"] = df["File ID"].str[:8] + "..."
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.info("➡️ Proceed to the **Job Profile** tab.")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 – JOB PROFILE
# ═══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.subheader("Step 2 — Configure Job Requirements")

    if not st.session_state.file_ids:
        st.warning("⚠️ Please upload resumes first (Step 1).")
    else:
        col_left, col_right = st.columns([1, 1])
        with col_left:
            job_role = st.text_input("Job Role *", placeholder="e.g. Senior Python Developer",
                                     value="Senior Python Developer")
        with col_right:
            st.markdown("**Quick Templates**")
            template = st.selectbox("Load a template", [
                "— Select —", "Senior Python Developer", "Data Scientist",
                "Frontend React Engineer", "DevOps / SRE Engineer", "Product Manager",
            ], label_visibility="collapsed")

        TEMPLATES = {
            "Senior Python Developer": "We are looking for a Senior Python Developer with 5+ years of experience.\n\nRequired:\n- Python, FastAPI / Django\n- PostgreSQL, Redis\n- Docker, Kubernetes\n- REST API design\n- CI/CD pipelines\n\nPreferred:\n- AWS or GCP\n- Microservices\n- GraphQL",
            "Data Scientist": "We need a Data Scientist with strong ML skills.\n\nRequired:\n- Python (pandas, scikit-learn, numpy)\n- Machine Learning\n- SQL\n- Data visualization\n\nPreferred:\n- Deep Learning (TensorFlow, PyTorch)\n- MLflow\n- Cloud platforms",
            "Frontend React Engineer": "Frontend Engineer with React expertise.\n\nRequired:\n- React.js, TypeScript\n- HTML5, CSS3, Tailwind\n- REST APIs\n- Git\n\nPreferred:\n- Next.js\n- Testing (Jest, Cypress)",
            "DevOps / SRE Engineer": "DevOps/SRE with cloud experience.\n\nRequired:\n- Kubernetes, Docker\n- AWS or GCP\n- Terraform\n- CI/CD\n- Linux\n\nPreferred:\n- Prometheus, Grafana\n- Python or Go scripting",
            "Product Manager": "Product Manager for B2B SaaS.\n\nRequired:\n- 3+ years PM experience\n- Product roadmap ownership\n- Stakeholder communication\n- Agile/Scrum\n\nPreferred:\n- Technical background\n- Analytics tools",
        }

        default_desc = TEMPLATES.get(template, "") if template != "— Select —" else TEMPLATES.get(job_role, "")

        job_description = st.text_area(
            "Job Description *", value=default_desc, height=280,
            placeholder="Paste the full job description here..."
        )

        analyze_btn = st.button(
            "🔍 Analyze Job Requirements", type="primary", use_container_width=True,
            disabled=not (job_role.strip() and len(job_description.strip()) > 20)
        )

        if analyze_btn:
            with st.spinner("🤖 AI is extracting job requirements..."):
                result = api_analyze_job(job_role, job_description)
            if result:
                st.session_state.job_profile_id = result["job_profile_id"]
                st.session_state.job_profile_data = result
                st.success("✅ Job profile analyzed and stored!")

        if st.session_state.job_profile_data:
            jp = st.session_state.job_profile_data
            st.markdown("---")
            st.markdown("### 📊 Extracted Job Requirements")

            c1, c2, c3 = st.columns(3)
            c1.metric("Required Skills", len(jp.get("required_skills", [])))
            c2.metric("Preferred Skills", len(jp.get("preferred_skills", [])))
            c3.metric("ATS Keywords", len(jp.get("keywords", [])))

            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown("**✅ Required Skills**")
                st.markdown(render_tags(jp.get("required_skills", []), "green"), unsafe_allow_html=True)
                st.markdown("**⭐ Preferred Skills**")
                st.markdown(render_tags(jp.get("preferred_skills", []), ""), unsafe_allow_html=True)
            with col_b:
                st.markdown("**🔑 ATS Keywords**")
                st.markdown(render_tags(jp.get("keywords", []), ""), unsafe_allow_html=True)
                st.markdown(f"**📅 Experience Level:** `{jp.get('experience_level', 'N/A')}`")

            st.info("➡️ Ready! Go to the **Rankings** tab and click **Analyze & Rank**.")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 – RANKINGS
# ═══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.subheader("Step 3 — Analyze & Rank Candidates")

    if not st.session_state.file_ids:
        st.warning("⚠️ Upload resumes first.")
    elif not st.session_state.job_profile_id:
        st.warning("⚠️ Set up a job profile first.")
    else:
        col_btn, col_info = st.columns([2, 3])
        with col_btn:
            analyze_btn = st.button("🚀 Analyze & Rank All Candidates",
                                    type="primary", use_container_width=True)
        with col_info:
            jp_name = (st.session_state.job_profile_data or {}).get("job_role", "")
            st.info(f"**{len(st.session_state.file_ids)} resumes** ready · Job: **{jp_name}**")

        if analyze_btn:
            progress_bar = st.progress(0, text="Initializing...")
            stages = [
                (15, "📄 Extracting text from resumes..."),
                (35, "🧠 Parsing candidate profiles with AI..."),
                (55, "📊 Scoring candidates against job requirements..."),
                (70, "🔍 Running ATS keyword gap analysis..."),
                (85, "✍️ Detecting resume weaknesses..."),
                (95, "📝 Generating recruiter reports..."),
            ]
            for pct, msg in stages:
                time.sleep(0.3)
                progress_bar.progress(pct, text=msg)

            result = api_rank_candidates(st.session_state.file_ids, st.session_state.job_profile_id)
            progress_bar.progress(100, text="✅ Complete!")
            time.sleep(0.5)
            progress_bar.empty()

            if result:
                st.session_state.ranking_results = result
                st.success(f"✅ Ranked **{result['total_candidates']}** candidates · "
                           f"**{result['shortlisted_count']} shortlisted**")
                st.rerun()

        # ── Results ──────────────────────────────────────────────────────────
        if st.session_state.ranking_results:
            results = st.session_state.ranking_results
            candidates = results.get("candidates", [])

            # Summary metrics
            st.markdown("---")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total Candidates", results["total_candidates"])
            m2.metric("Shortlisted", results["shortlisted_count"])
            top = candidates[0] if candidates else None
            m3.metric("Top Score", f"{top['score']:.1f}/10" if top else "—")
            avg = sum(c["score"] for c in candidates) / len(candidates) if candidates else 0
            m4.metric("Average Score", f"{avg:.1f}/10")

            # Check if AI data is missing
            has_ai_data = any(c.get("strengths") or c.get("weaknesses") or c.get("reasoning") for c in candidates)
            if not has_ai_data:
                api_key_warning()

            # Score chart
            if len(candidates) > 1:
                st.markdown("#### Score Distribution")
                df_chart = pd.DataFrame([{
                    "Name": c.get("name") or c["file_name"],
                    "Score": c["score"],
                    "Status": "✅ Shortlisted" if c["shortlisted"] else "❌ Not Shortlisted",
                } for c in candidates])
                fig = px.bar(df_chart, x="Name", y="Score", color="Status",
                             color_discrete_map={"✅ Shortlisted": "#27ae60", "❌ Not Shortlisted": "#e74c3c"},
                             text="Score")
                fig.update_traces(texttemplate="%{text:.1f}", textposition="outside")
                fig.update_layout(height=320, paper_bgcolor="rgba(0,0,0,0)",
                                  plot_bgcolor="rgba(0,0,0,0)", margin=dict(t=40, b=20))
                fig.add_hline(y=7, line_dash="dash", line_color="#764ba2",
                              annotation_text="Shortlist threshold (7)")
                st.plotly_chart(fig, use_container_width=True, key="bar_chart_scores")

            # Filters
            st.markdown("#### Candidate Rankings")
            fc1, fc2 = st.columns(2)
            show_shortlisted = fc1.checkbox("Show shortlisted only", value=False)
            min_score = fc2.slider("Minimum score filter", 1.0, 10.0, 1.0, 0.5)

            filtered = [c for c in candidates
                        if c["score"] >= min_score and (not show_shortlisted or c["shortlisted"])]

            for cand in filtered:
                cid = cand["candidate_id"]
                name = cand.get("name") or cand["file_name"]
                shortlisted = cand["shortlisted"]
                score = cand["score"]

                # Plain text expander title — no HTML allowed here
                icon = "✅" if shortlisted else "❌"
                expander_title = f"{icon} #{cand['rank']} {name} — {score_label(score)}"

                with st.expander(expander_title, expanded=(cand["rank"] == 1)):
                    left_col, right_col = st.columns([1, 2])

                    with left_col:
                        # Unique key per candidate gauge
                        st.plotly_chart(make_gauge(score), use_container_width=True,
                                        key=f"gauge_{cid}")
                        st.metric("Match %", f"{cand['match_percentage']:.0f}%")
                        if shortlisted:
                            st.markdown('<div class="shortlisted">✅ SHORTLISTED</div>',
                                        unsafe_allow_html=True)
                        else:
                            st.markdown('<div class="not-listed">❌ Not Shortlisted</div>',
                                        unsafe_allow_html=True)

                    with right_col:
                        st.markdown(f"**📧 Email:** {cand.get('email') or 'N/A'}")
                        st.markdown(f"**⏱ Experience:** {cand.get('experience_years') or 'N/A'} years")

                        reasoning = cand.get("reasoning") or ""
                        if reasoning and reasoning != "Analysis unavailable.":
                            st.markdown(f"**🤖 AI Reasoning:** *{reasoning}*")

                        if cand.get("skills"):
                            st.markdown("**🛠 Skills:**")
                            st.markdown(render_tags(cand["skills"][:15]), unsafe_allow_html=True)

                        st.markdown("---")

                        # ── Strengths ────────────────────────────────────
                        st.markdown("**💪 Strengths**")
                        strengths = [s for s in (cand.get("strengths") or []) if s and str(s).strip()]
                        if strengths:
                            for s in strengths:
                                st.markdown(f"✓ {s}")
                        else:
                            st.caption("No strength data — check API key in .env")

                        # ── Weaknesses ───────────────────────────────────
                        st.markdown("**⚠️ Weaknesses**")
                        weaknesses = [w for w in (cand.get("weaknesses") or []) if w and str(w).strip()]
                        if weaknesses:
                            for w in weaknesses:
                                st.markdown(f"• {w}")
                        else:
                            st.caption("No weakness data — check API key in .env")

                        # ── ATS Gaps ─────────────────────────────────────
                        st.markdown("**🔍 ATS Missing Keywords**")
                        missing = cand.get("ats_missing_keywords") or []
                        if missing:
                            st.markdown(render_tags(missing, "red"), unsafe_allow_html=True)
                        else:
                            st.success("No major ATS gaps!")

            # Exports
            st.markdown("---")
            st.markdown("### 📥 Export Results")
            ex1, ex2 = st.columns(2)
            with ex1:
                csv_data = api_export(st.session_state.job_profile_id, "csv")
                if csv_data:
                    st.download_button(
                        "📊 Download CSV", data=csv_data,
                        file_name=f"candidates_{st.session_state.job_profile_id[:8]}.csv",
                        mime="text/csv", use_container_width=True,
                    )
            with ex2:
                json_data = api_export(st.session_state.job_profile_id, "json")
                if json_data:
                    st.download_button(
                        "📋 Download JSON", data=json_data,
                        file_name=f"candidates_{st.session_state.job_profile_id[:8]}.json",
                        mime="application/json", use_container_width=True,
                    )


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4 – INDIVIDUAL REPORTS
# ═══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.subheader("Individual Candidate Reports")

    if not st.session_state.ranking_results:
        st.info("Run analysis first (Step 3) to generate individual reports.")
    else:
        candidates = st.session_state.ranking_results.get("candidates", [])
        options = {
            f"#{c['rank']} {c.get('name') or c['file_name']} — {score_label(c['score'])}": c["candidate_id"]
            for c in candidates
        }
        selected_label = st.selectbox("Select a candidate", list(options.keys()))
        selected_id = options[selected_label]

        if st.button("📄 Load Full Report", type="primary", use_container_width=True):
            with st.spinner("Loading candidate details..."):
                detail = api_get_candidate(selected_id)

            if detail:
                st.markdown("---")

                # Header
                h1, h2, h3 = st.columns(3)
                h1.markdown(f"### {detail.get('name') or 'Unknown'}")
                h2.markdown(f"📧 {detail.get('email') or 'N/A'}")
                h3.markdown(f"📞 {detail.get('phone') or 'N/A'}")

                # Score + info
                left, right = st.columns([1, 2])
                with left:
                    if detail.get("score"):
                        st.plotly_chart(
                            make_gauge(detail["score"], "Overall Score"),
                            use_container_width=True,
                            key=f"report_gauge_{selected_id}"
                        )
                    st.metric("Match %", f"{detail.get('match_percentage', 0):.1f}%")
                    st.metric("Experience", f"{detail.get('experience_years', 0)} years")
                    st.metric("Rank", f"#{detail.get('rank', 'N/A')}")
                    if detail.get("shortlisted"):
                        st.markdown('<div class="shortlisted">✅ SHORTLISTED</div>', unsafe_allow_html=True)
                    elif detail.get("shortlisted") is False:
                        st.markdown('<div class="not-listed">❌ Not Shortlisted</div>', unsafe_allow_html=True)

                with right:
                    if detail.get("skills"):
                        st.markdown("**🛠 Skills**")
                        st.markdown(render_tags(detail["skills"]), unsafe_allow_html=True)
                    if detail.get("companies"):
                        st.markdown("**🏢 Work History**")
                        for comp in detail["companies"]:
                            st.markdown(f"• {comp}")
                    if detail.get("education"):
                        st.markdown("**🎓 Education**")
                        for e in detail["education"]:
                            st.markdown(f"• {e}")
                    if detail.get("certifications"):
                        st.markdown("**🏅 Certifications**")
                        for cert in detail["certifications"]:
                            st.markdown(f"• {cert}")

                # AI Reasoning
                reasoning = detail.get("reasoning") or ""
                if reasoning and reasoning != "Analysis unavailable.":
                    st.markdown("---")
                    st.markdown("### 🤖 AI Assessment")
                    st.info(reasoning)

                # Strengths
                st.markdown("---")
                st.markdown("### 💪 Strengths")
                strengths = [s for s in (detail.get("strengths") or []) if s and str(s).strip()]
                if strengths:
                    for s in strengths:
                        st.markdown(f"✓ {s}")
                else:
                    api_key_warning()

                # Weaknesses
                st.markdown("---")
                st.markdown("### ⚠️ Weaknesses & Areas for Improvement")
                weaknesses = [w for w in (detail.get("weaknesses") or []) if w and str(w).strip()]
                if weaknesses:
                    for w in weaknesses:
                        st.markdown(f"• {w}")
                else:
                    api_key_warning()

                # ATS
                st.markdown("---")
                st.markdown("### 🔍 ATS Keyword Analysis")
                ats1, ats2 = st.columns(2)
                with ats1:
                    st.markdown("**❌ Missing Keywords**")
                    missing = detail.get("ats_missing_keywords") or []
                    if missing:
                        st.markdown(render_tags(missing, "red"), unsafe_allow_html=True)
                    else:
                        st.success("No major ATS gaps!")
                with ats2:
                    st.markdown("**💡 Suggestions**")
                    for sug in (detail.get("ats_suggestions") or []):
                        if sug:
                            st.markdown(f"💡 {sug}")

                # Full Report
                if detail.get("report"):
                    st.markdown("---")
                    st.markdown("### 📋 Full Recruiter Report")
                    st.markdown(detail["report"])

                # PDF Download
                st.markdown("---")
                st.markdown("### 📥 Download Full Report")
                col_pdf1, col_pdf2 = st.columns(2)
                with col_pdf1:
                    try:
                        pdf_response = requests.get(
                            f"{API_BASE}/candidate/{selected_id}/report_pdf",
                            timeout=30
                        )
                        if pdf_response.status_code == 200:
                            safe_name = (detail.get("name") or "candidate").replace(" ", "_")
                            st.download_button(
                                label="📄 Download PDF Report",
                                data=pdf_response.content,
                                file_name=f"report_{safe_name}.pdf",
                                mime="application/pdf",
                                use_container_width=True,
                                type="primary",
                            )
                        else:
                            st.error("PDF generation failed.")
                    except Exception as e:
                        st.error(f"PDF download error: {e}")

                with col_pdf2:
                    if detail.get("report"):
                        st.download_button(
                            label="📝 Download Markdown Report",
                            data=detail["report"],
                            file_name=f"report_{(detail.get('name') or 'candidate').replace(' ', '_')}.md",
                            mime="text/markdown",
                            use_container_width=True,
                        )

                # Cover Letter
                if detail.get("cover_letter"):
                    st.markdown("---")
                    with st.expander("✍️ AI-Generated Cover Letter"):
                        st.markdown(detail["cover_letter"])
                        st.download_button(
                            "Download Cover Letter",
                            data=detail["cover_letter"],
                            file_name=f"cover_letter_{(detail.get('name') or 'candidate').replace(' ', '_')}.txt",
                            mime="text/plain",
                        )

# Footer
st.markdown("---")
st.markdown(
    "<center><small>AI Resume Analyzer · Powered by FastAPI + Streamlit ·</small></center>",
    unsafe_allow_html=True,
)