import streamlit as st
import json
import time
import random
from datetime import datetime

# ── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Railways Act 1989 — Companion",
    page_icon="🚂",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Session State ────────────────────────────────────────────────────────────
def init_state():
    defaults = {
        "api_key":          "",
        "bookmarks":        [],          # list of section_no strings
        "notes":            {},          # {section_no: note_text}
        "sections_read":    [],          # list of section_no strings
        "fc_chapter":       "All",
        "fc_index":         0,
        "quiz_session":     None,        # active quiz dict
        "mock_active":      False,
        "mock_qs":          [],
        "mock_answers":     {},
        "mock_start":       None,
        "mock_duration":    1800,        # seconds
        "all_scores":       [],          # list of score dicts
        "chat_history":     [],          # AI assistant conversation
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ── Data Loading ─────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    with open("data/act_sections.json") as f:
        sections = json.load(f)
    with open("data/quiz_bank.json") as f:
        quiz = json.load(f)
    return sections, quiz

sections_data, quiz_bank = load_data()

# Helpers — support both int and alphanumeric section numbers (20A, 20B...)
def sec_id(s):
    return str(s["section_no"]) + "_" + s["title"][:10]

def sec_label(s):
    return f"§ {s['section_no']}"

def is_amended(s):
    return "amendment" in s

AMENDMENT_ACTS = ["Railways (Amendment) Act, 2008 (No. 11 of 2008)"]

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🚂 Railways Act 1989")
    st.caption("General Officer Awareness Companion")
    st.divider()

    nav = st.radio(
        "Navigation",
        [
            "📖  Browse & Read",
            "📋  Amendments",
            "🤖  AI Assistant",
            "🃏  Flashcards",
            "📝  MCQ Quiz",
            "⏱️  Mock Test",
            "📊  Progress",
            "⚙️  Settings",
        ],
        label_visibility="collapsed",
    )

    st.divider()

    if st.session_state.api_key:
        st.success("🟢 AI Features Active")
    else:
        st.warning("🟡 AI Offline\nSet key in ⚙️ Settings")

    st.caption(f"Sections read: {len(set(st.session_state.sections_read))}/{len(sections_data)}")
    st.caption(f"Bookmarks: {len(st.session_state.bookmarks)}")
    if st.session_state.all_scores:
        avg = sum(s["score"]/s["total"]*100 for s in st.session_state.all_scores) / len(st.session_state.all_scores)
        st.caption(f"Avg score: {avg:.0f}%")

# ═════════════════════════════════════════════════════════════════════════════
# PAGE: BROWSE & READ
# ═════════════════════════════════════════════════════════════════════════════
if nav == "📖  Browse & Read":
    st.title("📖 Browse & Read")
    st.caption("The Railways Act, 1989 — Section Browser")

    # Search bar
    search = st.text_input(
        "🔍 Search",
        placeholder="e.g. ticketless, level crossing, compensation, goods ...",
    )

    if search:
        display = [
            s for s in sections_data
            if search.lower() in s["title"].lower()
            or search.lower() in s["content"].lower()
            or search.lower() in " ".join(s.get("tags", []))
        ]
        if not display:
            st.info("No sections matched your search.")
            st.stop()
        st.caption(f"{len(display)} result(s) found")
    else:
        display = sections_data

    col1, col2 = st.columns([1, 2], gap="large")

    with col1:
        chapters = sorted(set(s["chapter"] for s in display))
        ch_sel = st.selectbox("Filter by Chapter", ["All"] + chapters)

        filtered = display if ch_sel == "All" else [s for s in display if s["chapter"] == ch_sel]

        if not filtered:
            st.info("No sections in this chapter.")
            st.stop()

        labels = [f"§ {s['section_no']}  {s['title']}" for s in filtered]
        chosen_label = st.radio("Sections", labels, label_visibility="collapsed")
        chosen = filtered[labels.index(chosen_label)]

    with col2:
        sid = sec_id(chosen)

        # Mark as read
        if sid not in st.session_state.sections_read:
            st.session_state.sections_read.append(sid)

        # Header row
        hcol1, hcol2, hcol3 = st.columns([4, 1, 1])
        with hcol1:
            st.subheader(f"Section {chosen['section_no']} — {chosen['title']}")
            st.caption(chosen["chapter"])
        with hcol2:
            bm_label = "🔖 Saved" if sid in st.session_state.bookmarks else "☆ Save"
            if st.button(bm_label, key="bm_btn"):
                if sid in st.session_state.bookmarks:
                    st.session_state.bookmarks.remove(sid)
                else:
                    st.session_state.bookmarks.append(sid)
                st.rerun()
        with hcol3:
            if chosen.get("amendment"):
                st.markdown("🔄 **Amended**")

        # Amendment banner
        if chosen.get("amendment"):
            amend = chosen["amendment"]
            st.info(
                f"⚖️ **Amended by {amend['act']}** ({amend['no']}) — "
                f"w.e.f. {amend.get('wef', 'N/A')}  \n"
                f"_{amend.get('changes', '')}_"
            )

        st.divider()
        st.write(chosen["content"])

        if chosen.get("penalty"):
            st.error(f"⚠️  **Penalty:** {chosen['penalty']}")

        if chosen.get("tags"):
            st.caption("Tags: " + " · ".join(f"`{t}`" for t in chosen["tags"]))

        # AI Explain button
        if st.session_state.api_key:
            if st.button("🤖 Explain this section in plain language"):
                with st.spinner("Generating explanation..."):
                    try:
                        import anthropic
                        client = anthropic.Anthropic(api_key=st.session_state.api_key)
                        prompt = (
                            f"Explain Section {chosen['section_no']} of the Railways Act 1989 "
                            f"titled '{chosen['title']}' in simple, practical language for a "
                            f"Railway officer. Keep it under 150 words. Text: {chosen['content']}"
                        )
                        msg = client.messages.create(
                            model="claude-sonnet-4-20250514",
                            max_tokens=300,
                            messages=[{"role": "user", "content": prompt}],
                        )
                        st.info("🤖 " + msg.content[0].text)
                    except Exception as e:
                        st.error(f"API error: {e}")

        # Notes
        st.divider()
        with st.expander("📝 My Notes for this section"):
            note_val = st.session_state.notes.get(sid, "")
            new_note = st.text_area("Notes", value=note_val, placeholder="Write study notes here...", key=f"note_{sid}")
            if st.button("💾 Save Note"):
                st.session_state.notes[sid] = new_note
                st.success("Note saved!")

# ═════════════════════════════════════════════════════════════════════════════
# PAGE: AMENDMENTS
# ═════════════════════════════════════════════════════════════════════════════
elif nav == "📋  Amendments":
    st.title("📋 Amendment Acts")
    st.caption("Amendments to the Railways Act 1989, integrated inline.")

    # ── Amendment index card ─────────────────────────────────────────────────
    with st.container(border=True):
        st.markdown("### ⚖️ Railways (Amendment) Act, 2008")
        col1, col2, col3 = st.columns(3)
        col1.metric("Act No.", "No. 11 of 2008")
        col2.metric("Assented", "28 March 2008")
        col3.metric("W.e.f.", "31 January 2008")
        st.markdown(
            "**Purpose:** Further amends the Railways Act, 1989. "
            "Primarily deals with **land acquisition for Special Railway Projects**, "
            "introducing an entirely new Chapter IVA (§§20A–20P) with a self-contained "
            "land acquisition regime, bypassing the Land Acquisition Act, 1894. "
            "Also amends §2 with three new definitions."
        )
        st.markdown("**Key changes:**")
        st.markdown(
            "- §2 amended: New definitions of *competent authority* (§2(7A)), "
            "*person interested* (§2(29A)), and *special railway project* (§2(37A))\n"
            "- **New Chapter IVA** inserted: 16 new sections (§20A to §20P) — "
            "complete land acquisition procedure for special railway projects\n"
            "- Land Acquisition Act 1894 explicitly excluded (§20N)\n"
            "- 60% solatium on market value (§20F(9))\n"
            "- 80% profit-sharing with original landowners on resale (§20M)\n"
            "- 5-year reversion clause for unutilised land (§20L)\n"
            "- National Rehabilitation & Resettlement Policy 2007 made applicable (§20O)"
        )

    st.divider()

    # ── All amended/inserted sections ────────────────────────────────────────
    st.subheader("All Amended & Inserted Sections")

    amended_sections = [s for s in sections_data if s.get("amendment")]

    if not amended_sections:
        st.info("No amendments found in data.")
    else:
        # Group by amendment act
        from collections import defaultdict
        by_act = defaultdict(list)
        for s in amended_sections:
            act_name = s["amendment"].get("act", "Unknown")
            by_act[act_name].append(s)

        for act_name, act_sections in by_act.items():
            st.markdown(f"**{act_name}** — {len(act_sections)} sections")
            for s in act_sections:
                with st.expander(
                    f"§{s['section_no']} — {s['title']}  |  "
                    f"`{s['chapter'].split('—')[0].strip()}`"
                ):
                    amend = s["amendment"]
                    st.info(
                        f"⚖️ **{amend['act']}** ({amend['no']}) — "
                        f"w.e.f. {amend.get('wef', 'N/A')}  \n"
                        f"_{amend.get('changes', '')}_"
                    )
                    st.write(s["content"])
                    if s.get("penalty"):
                        st.error(f"⚠️  **Penalty:** {s['penalty']}")

    st.divider()

    # ── MCQ questions on amendments ──────────────────────────────────────────
    st.subheader("📝 Amendment — Key Facts for Exam")
    facts = [
        ("What is the short title of the 2008 amendment?",
         "The Railways (Amendment) Act, 2008 (No. 11 of 2008)."),
        ("From which date did the 2008 Amendment Act come into force?",
         "It is deemed to have come into force on **31st January 2008**, "
         "though it received Presidential assent on 28th March 2008."),
        ("What is a 'special railway project' as defined by the 2008 Amendment?",
         "A project notified by the Central Government for providing **national infrastructure for a public purpose** "
         "in a specified time-frame, covering one or more States or Union territories [§2(37A)]."),
        ("Which Chapter and sections were inserted by the 2008 Amendment?",
         "**Chapter IVA** — Sections **20A to 20P** (Land Acquisition for a Special Railway Project)."),
        ("What is the time limit to file objections under §20D?",
         "**30 days** from the date of publication of the notification under §20A."),
        ("Under §20F, what solatium is awarded over market value?",
         "**60 per cent** of the market value, in consideration of the compulsory nature of the acquisition."),
        ("What interest rate applies on excess arbitration award under §20H?",
         "**9 per cent per annum** from the date of taking possession till actual deposit."),
        ("What happens if land acquired under the Act is unutilised for 5 years? (§20L)",
         "The land **reverts to the Central Government** by reversion."),
        ("What percentage of profit is shared with original landowners on resale? (§20M)",
         "**80 per cent** of the difference between acquisition cost and higher sale consideration."),
        ("Does the Land Acquisition Act, 1894 apply to acquisitions under Chapter IVA?",
         "**No.** Section 20N explicitly excludes it."),
        ("What policy applies to persons displaced by land acquisition under Chapter IVA?",
         "The **National Rehabilitation and Resettlement Policy, 2007** (§20O)."),
        ("Under §20E, what is the time limit for the Central Government to issue declaration after §20A notification?",
         "**One year.** If no declaration is published within one year, the §20A notification ceases to have effect."),
    ]

    for q, a in facts:
        with st.expander(f"❓  {q}"):
            st.success(f"✅  {a}")


elif nav == "🤖  AI Assistant":
    st.title("🤖 AI Assistant")

    if not st.session_state.api_key:
        st.warning("Please set your Anthropic API key in **⚙️ Settings** to use the AI Assistant.")
        st.stop()

    st.caption("Ask anything about the Railways Act 1989. Answers are grounded in the Act text.")

    if st.button("🗑️ Clear Conversation"):
        st.session_state.chat_history = []
        st.rerun()

    # Build Act context from loaded sections
    # TODO: Once PDF is parsed, replace this with full Act text
    act_context = "\n\n".join(
        f"Section {s['section_no']} ({s['title']}, {s['chapter']}): {s['content']}"
        + (f" Penalty: {s['penalty']}" if s.get("penalty") else "")
        for s in sections_data
    )

    system_prompt = f"""You are an expert on the Railways Act 1989 (India), assisting Railway officers.
Answer questions based on the Act text provided. Always cite specific section numbers.
Be concise, practical, and precise. If a question is outside the Act's scope, say so clearly.

RAILWAYS ACT 1989 — KEY SECTIONS:
{act_context}

Note: This is a skeleton dataset with selected sections. For comprehensive coverage, refer to the full Act text.
"""

    # Display chat history
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # Chat input
    if user_input := st.chat_input("Ask about the Railways Act 1989..."):
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.write(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    import anthropic
                    client = anthropic.Anthropic(api_key=st.session_state.api_key)
                    response = client.messages.create(
                        model="claude-sonnet-4-20250514",
                        max_tokens=800,
                        system=system_prompt,
                        messages=st.session_state.chat_history,
                    )
                    answer = response.content[0].text
                    st.write(answer)
                    st.session_state.chat_history.append({"role": "assistant", "content": answer})
                except Exception as e:
                    st.error(f"API error: {e}")

# ═════════════════════════════════════════════════════════════════════════════
# PAGE: FLASHCARDS
# ═════════════════════════════════════════════════════════════════════════════
elif nav == "🃏  Flashcards":
    st.title("🃏 Flashcards")
    st.caption("Look at the section number → guess the topic → reveal to check.")

    chapters = sorted(set(s["chapter"] for s in sections_data))
    ch_filter = st.selectbox("Chapter", ["All"] + chapters, key="fc_ch")

    deck = sections_data if ch_filter == "All" else [s for s in sections_data if s["chapter"] == ch_filter]

    if not deck:
        st.info("No sections found.")
        st.stop()

    # Reset index if chapter changed or out of bounds
    if st.session_state.get("_last_fc_ch") != ch_filter:
        st.session_state.fc_index = 0
        st.session_state["_last_fc_ch"] = ch_filter

    idx = st.session_state.fc_index % len(deck)
    card = deck[idx]

    st.divider()
    st.progress((idx + 1) / len(deck), text=f"Card {idx + 1} of {len(deck)}")

    # The card face — show section number, hide content
    st.markdown(
        f"""
        <div style="
            background: #1e3a5f;
            border-radius: 12px;
            padding: 2rem;
            text-align: center;
            margin: 1rem 0;
        ">
            <p style="color:#aac4e0; font-size:0.9rem; margin:0">Railways Act 1989</p>
            <h1 style="color:white; font-size:3rem; margin:0.5rem 0">§ {card['section_no']}</h1>
            <p style="color:#aac4e0; font-size:0.85rem">{card['chapter']}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("🔍 Reveal Answer", expanded=False):
        st.subheader(card["title"])
        st.write(card["content"])
        if card.get("penalty"):
            st.error(f"⚠️  **Penalty:** {card['penalty']}")

    # Navigation
    st.divider()
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button("⬅️ Previous"):
            st.session_state.fc_index = max(0, idx - 1)
            st.rerun()
    with c2:
        if st.button("Next ➡️"):
            st.session_state.fc_index = min(len(deck) - 1, idx + 1)
            st.rerun()
    with c3:
        if st.button("🔀 Random"):
            st.session_state.fc_index = random.randint(0, len(deck) - 1)
            st.rerun()
    with c4:
        if st.button("⏮️ Restart"):
            st.session_state.fc_index = 0
            st.rerun()

# ═════════════════════════════════════════════════════════════════════════════
# PAGE: MCQ QUIZ
# ═════════════════════════════════════════════════════════════════════════════
elif nav == "📝  MCQ Quiz":
    st.title("📝 MCQ Quiz Bank")

    if st.session_state.quiz_session is None:
        # Quiz setup screen
        chapters = sorted(set(q["chapter"] for q in quiz_bank))
        ch = st.selectbox("Filter by Chapter", ["All"] + chapters)
        pool = quiz_bank if ch == "All" else [q for q in quiz_bank if q["chapter"] == ch]
        st.caption(f"{len(pool)} questions available in this selection")

        n = st.slider(
            "Number of questions",
            min_value=5,
            max_value=min(len(pool), 25),
            value=min(10, len(pool)),
        )

        if st.button("🚀 Start Quiz", type="primary"):
            selected = random.sample(pool, n)
            st.session_state.quiz_session = {
                "questions": selected,
                "answers":   {},
                "submitted": False,
                "chapter":   ch,
            }
            st.rerun()

    else:
        qs = st.session_state.quiz_session["questions"]
        answered = st.session_state.quiz_session["answers"]
        submitted = st.session_state.quiz_session["submitted"]

        if not submitted:
            # Answer phase
            st.caption(f"Answered: {len(answered)}/{len(qs)}")
            st.progress(len(answered) / len(qs) if qs else 0)
            st.divider()

            for i, q in enumerate(qs):
                st.markdown(f"**Q{i+1}. {q['question']}**")
                prev = answered.get(i)
                ans = st.radio(
                    f"q{i}",
                    q["options"],
                    index=q["options"].index(prev) if prev else None,
                    key=f"quiz_q_{i}",
                    label_visibility="collapsed",
                )
                if ans:
                    answered[i] = ans
                st.divider()

            c1, c2 = st.columns(2)
            with c1:
                if st.button(
                    "✅ Submit Quiz",
                    type="primary",
                    disabled=len(answered) < len(qs),
                    help="Answer all questions to submit",
                ):
                    st.session_state.quiz_session["submitted"] = True
                    st.rerun()
            with c2:
                if st.button("🔄 Reset"):
                    st.session_state.quiz_session = None
                    st.rerun()

        else:
            # Results screen
            score = sum(1 for i, q in enumerate(qs) if answered.get(i) == q["answer"])
            total = len(qs)
            pct = (score / total) * 100

            # Log the score
            already_logged = any(
                s.get("_quiz_id") == id(st.session_state.quiz_session)
                for s in st.session_state.all_scores
            )
            if not already_logged:
                st.session_state.all_scores.append({
                    "_quiz_id": id(st.session_state.quiz_session),
                    "date":    datetime.now().strftime("%d %b %Y %H:%M"),
                    "type":    "MCQ Quiz",
                    "chapter": st.session_state.quiz_session["chapter"],
                    "score":   score,
                    "total":   total,
                })

            # Score display
            m1, m2, m3 = st.columns(3)
            m1.metric("Score", f"{score}/{total}")
            m2.metric("Percentage", f"{pct:.0f}%")
            m3.metric("Questions", total)

            if pct >= 80:
                st.success("🎉 Excellent performance!")
            elif pct >= 60:
                st.warning("👍 Good — keep revising!")
            else:
                st.error("📚 Needs more study. Review the answers below.")

            st.divider()
            st.subheader("Review Answers")

            for i, q in enumerate(qs):
                user_ans = answered.get(i, "—")
                correct = q["answer"]
                icon = "✅" if user_ans == correct else "❌"

                with st.expander(f"{icon}  Q{i+1}: {q['question']}"):
                    for opt in q["options"]:
                        if opt == correct and opt == user_ans:
                            st.markdown(f"**✅ {opt}** ← Your answer (Correct)")
                        elif opt == correct:
                            st.markdown(f"**✅ {opt}** ← Correct answer")
                        elif opt == user_ans:
                            st.markdown(f"❌ ~~{opt}~~ ← Your answer")
                        else:
                            st.write(opt)
                    if q.get("explanation"):
                        st.info(f"💡 {q['explanation']}")

            if st.button("🔄 New Quiz", type="primary"):
                st.session_state.quiz_session = None
                st.rerun()

# ═════════════════════════════════════════════════════════════════════════════
# PAGE: MOCK TEST
# ═════════════════════════════════════════════════════════════════════════════
elif nav == "⏱️  Mock Test":
    st.title("⏱️ Mock Test")

    if not st.session_state.mock_active:
        st.caption("Timed, full-length test simulating exam conditions. All chapters, randomized order.")
        st.divider()

        c1, c2 = st.columns(2)
        with c1:
            n_qs = st.selectbox("Number of Questions", [10, 15, 20, 25], index=1)
        with c2:
            duration_min = st.selectbox("Time Limit (minutes)", [10, 15, 20, 30, 45, 60], index=2)

        st.info(f"📋 {n_qs} questions · ⏱️ {duration_min} minutes · All chapters")

        if st.button("🚀 Start Mock Test", type="primary"):
            pool = quiz_bank.copy()
            random.shuffle(pool)
            st.session_state.mock_active   = True
            st.session_state.mock_qs       = pool[: min(n_qs, len(pool))]
            st.session_state.mock_answers  = {}
            st.session_state.mock_start    = time.time()
            st.session_state.mock_duration = duration_min * 60
            st.rerun()

    else:
        elapsed   = time.time() - st.session_state.mock_start
        remaining = st.session_state.mock_duration - elapsed
        qs        = st.session_state.mock_qs

        # ── Timer display ──────────────────────────────────────────────────
        if remaining > 0:
            mins = int(remaining // 60)
            secs = int(remaining % 60)
            timer_color = "red" if remaining < 120 else "orange" if remaining < 300 else "green"
            st.markdown(
                f"""<h2 style='color:{timer_color}'>⏱️ {mins:02d}:{secs:02d} remaining</h2>""",
                unsafe_allow_html=True,
            )
        else:
            st.error("⏰ Time's up!")

        answered = len(st.session_state.mock_answers)
        p1, p2, p3 = st.columns(3)
        p1.metric("Answered", f"{answered}/{len(qs)}")
        p2.metric("Remaining", f"{len(qs) - answered}")
        elapsed_min = elapsed / 60
        p3.metric("Time Used", f"{elapsed_min:.1f} min")

        st.caption("⚠️ Timer is approximate — refresh the page to update the countdown.")
        st.divider()

        # Questions
        for i, q in enumerate(qs):
            prev = st.session_state.mock_answers.get(i)
            st.markdown(f"**Q{i+1}.  {q['question']}**")
            ans = st.radio(
                f"mq{i}",
                q["options"],
                index=q["options"].index(prev) if prev else None,
                key=f"mock_q_{i}",
                label_visibility="collapsed",
            )
            if ans:
                st.session_state.mock_answers[i] = ans
            st.divider()

        c1, c2 = st.columns(2)
        with c1:
            if st.button("✅ Submit Test", type="primary"):
                score = sum(1 for i, q in enumerate(qs) if st.session_state.mock_answers.get(i) == q["answer"])
                time_taken = (time.time() - st.session_state.mock_start) / 60
                st.session_state.all_scores.append({
                    "date":       datetime.now().strftime("%d %b %Y %H:%M"),
                    "type":       "Mock Test",
                    "chapter":    "All",
                    "score":      score,
                    "total":      len(qs),
                    "time_taken": f"{time_taken:.1f} min",
                })
                st.session_state.mock_active = False
                st.success(f"✅ Test submitted! Score: {score}/{len(qs)} ({score/len(qs)*100:.0f}%)")
                time.sleep(1.5)
                st.rerun()
        with c2:
            if st.button("❌ Abandon Test"):
                st.session_state.mock_active = False
                st.rerun()

# ═════════════════════════════════════════════════════════════════════════════
# PAGE: PROGRESS DASHBOARD
# ═════════════════════════════════════════════════════════════════════════════
elif nav == "📊  Progress":
    st.title("📊 Progress Dashboard")

    # ── Top metrics ──────────────────────────────────────────────────────────
    read_count = len(set(st.session_state.sections_read))
    total_secs = len(sections_data)
    scores     = st.session_state.all_scores
    bm_count   = len(st.session_state.bookmarks)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Sections Read", f"{read_count}/{total_secs}", f"{read_count/total_secs*100:.0f}%")
    m2.metric("Bookmarks", bm_count)
    m3.metric("Tests Taken", len(scores))
    if scores:
        avg = sum(s["score"]/s["total"]*100 for s in scores) / len(scores)
        m4.metric("Avg Score", f"{avg:.0f}%")
    else:
        m4.metric("Avg Score", "—")

    st.divider()

    # ── Reading progress by chapter ──────────────────────────────────────────
    st.subheader("Reading Progress by Chapter")
    chapters = sorted(set(s["chapter"] for s in sections_data))
    for ch in chapters:
        ch_secs = [s for s in sections_data if s["chapter"] == ch]
        ch_read = sum(1 for s in ch_secs if sec_id(s) in st.session_state.sections_read)
        pct = ch_read / len(ch_secs) if ch_secs else 0
        st.write(f"**{ch}**")
        st.progress(pct, text=f"{ch_read} / {len(ch_secs)} sections read")

    st.divider()

    # ── Score history ────────────────────────────────────────────────────────
    st.subheader("Score History")
    if scores:
        for s in reversed(scores[-15:]):
            c1, c2, c3, c4 = st.columns([3, 2, 2, 1])
            c1.write(f"**{s['type']}**  —  {s.get('chapter', 'All')}")
            c2.write(s["date"])
            c3.write(s.get("time_taken", "—"))
            pct = s["score"] / s["total"] * 100
            badge = "🟢" if pct >= 80 else "🟡" if pct >= 60 else "🔴"
            c4.write(f"{badge} {s['score']}/{s['total']}")
    else:
        st.info("Complete a quiz or mock test to see scores here.")

    # ── Bookmarked sections ──────────────────────────────────────────────────
    if st.session_state.bookmarks:
        st.divider()
        st.subheader("Bookmarked Sections")
        for sid in st.session_state.bookmarks:
            sec = next((s for s in sections_data if sec_id(s) == sid), None)
            if sec:
                st.write(f"§ {sec['section_no']} — **{sec['title']}**  `{sec['chapter']}`")

    # ── Notes ────────────────────────────────────────────────────────────────
    if st.session_state.notes:
        st.divider()
        st.subheader("My Study Notes")
        for sid, note in st.session_state.notes.items():
            if note.strip():
                sec = next((s for s in sections_data if sec_id(s) == sid), None)
                label = f"§ {sec['section_no']} — {sec['title']}" if sec else sid
                with st.expander(label):
                    st.write(note)

# ═════════════════════════════════════════════════════════════════════════════
# PAGE: SETTINGS
# ═════════════════════════════════════════════════════════════════════════════
elif nav == "⚙️  Settings":
    st.title("⚙️ Settings")

    st.subheader("AI Configuration (Anthropic API)")
    st.caption("Required for the AI Assistant and 'Explain this section' features.")

    api_key_input = st.text_input(
        "Anthropic API Key",
        value=st.session_state.api_key,
        type="password",
        placeholder="sk-ant-...",
    )
    if st.button("💾 Save API Key", type="primary"):
        st.session_state.api_key = api_key_input
        st.success("API key saved for this session!")

    st.warning("⚠️ The API key is stored only in your browser session and is not persisted after you close the tab.")

    st.divider()
    st.subheader("Data & Progress")
    st.caption("Reset your reading history, bookmarks, notes, and scores.")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("🗑️ Clear All Progress", type="secondary"):
            st.session_state.sections_read = []
            st.session_state.bookmarks     = []
            st.session_state.notes         = {}
            st.session_state.all_scores    = []
            st.session_state.quiz_session  = None
            st.session_state.mock_active   = False
            st.success("All progress cleared.")
    with c2:
        if st.button("🗑️ Clear Chat History"):
            st.session_state.chat_history = []
            st.success("Chat history cleared.")

    st.divider()
    st.subheader("About")
    st.info(
        """
        **Railways Act 1989 — Companion App**  
        Built for Railway officer awareness and training.  
        
        **Version:** 0.2 — PDF Parsed  
        **Data:** 159 sections extracted directly from the Gazette of India original publication (No. 24 of 1989).  
        **AI:** Powered by Anthropic Claude (claude-sonnet-4-20250514)  
        **MCQ Bank:** 25 questions across all chapters  
        
        **Known limitations:**  
        - 41 sections not extracted (OCR layout issue with two-column scanned PDF)  
        - Section content may have minor marginal-note OCR artifacts  
        
        **TODO before production:**  
        - Manually fill missing 41 sections  
        - Expand MCQ bank to 200+ questions  
        - Add persistence layer (SQLite or Streamlit Cloud secrets)  
        - Add auto-refresh for live mock test timer (streamlit-autorefresh)  
        """
    )
