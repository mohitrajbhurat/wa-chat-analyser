import streamlit as st
import pandas as pd

import metrics as m
import charts as c
from parser import parse_chat


@st.cache_data(show_spinner=False)
def cached_parse(file_bytes: bytes) -> pd.DataFrame:
    return parse_chat(file_bytes)


@st.cache_data(show_spinner=False)
def cached_reply_matrix(df: pd.DataFrame, window_hours: int = 2):
    return m.reply_matrix(df, window_hours)


@st.cache_data(show_spinner=False)
def cached_avg_response_time(df: pd.DataFrame, window_hours: int = 2):
    return m.avg_response_time(df, window_hours)


@st.cache_data(show_spinner=False)
def cached_top_words(df: pd.DataFrame):
    return m.top_words(df)


@st.cache_data(show_spinner=False)
def cached_emoji_analysis(df: pd.DataFrame):
    return m.emoji_analysis(df)


@st.cache_data(show_spinner=False)
def cached_race_mp4(df: pd.DataFrame, granularity: str, fps: int) -> bytes:
    return c.generate_race_mp4(df, granularity=granularity, fps=fps)


@st.cache_data(show_spinner=False)
def cached_word_cloud(df: pd.DataFrame, author: str | None = None) -> bytes:
    return c.word_cloud_img(df, author)


@st.cache_data(show_spinner=False)
def cached_summary_pdf(df: pd.DataFrame, stats_frozen: tuple) -> bytes:
    stats = dict(stats_frozen)
    return c.generate_summary_pdf(df, stats)


@st.cache_data(show_spinner=False)
def cached_overview_img(df: pd.DataFrame, stats_frozen: tuple) -> bytes:
    stats = dict(stats_frozen)
    return c.generate_overview_image(df, stats)


_TOOLTIP_CSS = """<style>
.wa-info{position:relative;display:inline-block;cursor:help}
.wa-info .wa-tip{
  visibility:hidden;opacity:0;
  background:rgba(20,20,20,0.93);color:#f2f2f2;
  font-size:0.79rem;line-height:1.5;
  padding:9px 13px;border-radius:7px;
  position:absolute;z-index:9999;
  right:0;top:150%;width:300px;
  white-space:normal;box-shadow:0 3px 12px rgba(0,0,0,.4);
  transition:opacity .15s ease;pointer-events:none}
.wa-info:hover .wa-tip{visibility:visible;opacity:1}
</style>"""


def _show_chart(fig, info: str = ""):
    """Render title + ℹ️ tooltip as HTML, then the Plotly chart without its own title."""
    title = (fig.layout.title.text or "").strip()
    safe = (info.replace("&", "&amp;")
               .replace("<", "&lt;")
               .replace(">", "&gt;")
               .replace('"', "&quot;"))
    tip = (f'&ensp;<span class="wa-info">ℹ️<span class="wa-tip">{safe}</span></span>'
           if info else "")
    if title or tip:
        st.markdown(
            f'<p style="font-size:1em;font-weight:600;margin:8px 0 2px 4px;">'
            f'{title}{tip}</p>',
            unsafe_allow_html=True,
        )
    # Remove the Plotly title (shown via HTML above instead).
    # text="" alone still reserves vertical space; zeroing the pad removes it.
    # Animated charts keep enough top margin for the Play/Pause buttons (y=1.12).
    has_controls = bool(fig.layout.updatemenus or fig.layout.sliders)
    t_margin = 55 if has_controls else 30
    fig.update_layout(
        title=dict(text="", pad=dict(t=0, b=0)),
        margin=dict(t=t_margin),
    )
    st.plotly_chart(fig, width='stretch')


st.set_page_config(
    page_title="WhatsApp Chat Analyser",
    page_icon="💬",
    layout="wide",
)
st.markdown(_TOOLTIP_CSS, unsafe_allow_html=True)

# ── Header ──────────────────────────────────────────────────────────────────

st.markdown(
    """
    <div style="display:flex;align-items:center;gap:14px;margin-bottom:6px;padding:4px 0">
      <div style="background:#25D366;border-radius:50%;width:58px;height:58px;flex-shrink:0;
                  display:flex;align-items:center;justify-content:center;
                  box-shadow:0 2px 10px rgba(37,211,102,0.4)">
        <span style="color:white;font-size:1.5rem;font-weight:800;letter-spacing:-1px;
                     line-height:1">WA</span>
      </div>
      <div>
        <div style="font-size:1.9rem;font-weight:700;line-height:1.1">
          WhatsApp Chat Analyser
        </div>
        <div style="color:#888;font-size:0.9rem;margin-top:2px">
          Upload any WhatsApp exported chat to see stats and graphs
        </div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.info(
    "**Privacy notice:** Your chat file is processed entirely within your "
    "browser session. No messages are stored, logged, or sent anywhere. "
    "Everything is discarded when you close this page.",
    icon="🔒",
)

# ── File Upload ──────────────────────────────────────────────────────────────

uploaded = st.file_uploader(
    "Upload your WhatsApp export (.txt)",
    type=["txt"],
    help="In WhatsApp: open a chat → ⋮ → More → Export Chat → Without Media",
)

if not uploaded:
    st.markdown("### How to export a WhatsApp chat")
    col_and, col_ios = st.columns(2)
    with col_and:
        st.markdown(
            """
            **Android**
            1. Open WhatsApp and go to the chat or group
            2. Tap **⋮** (top-right) → **More** → **Export chat**
            3. Choose **Without Media**
            4. Share or save the `.txt` file, then upload it above

            > For groups: open the group → tap the group name at the top → scroll down → **Export chat**
            """
        )
    with col_ios:
        st.markdown(
            """
            **iPhone (iOS)**
            1. Open WhatsApp and go to the chat or group
            2. Tap the **contact / group name** at the top
            3. Scroll down and tap **Export Chat**
            4. Choose **Without Media**
            5. AirDrop, email, or save to Files, then upload above

            > Group export: tap the group name → scroll to the bottom → **Export Chat**
            """
        )
    st.stop()

# ── Parse ────────────────────────────────────────────────────────────────────

with st.spinner("Parsing chat…"):
    df = cached_parse(uploaded.read())

if df.empty:
    st.error(
        "Could not parse this file. Make sure it is a WhatsApp exported .txt file "
        "and that it contains text messages (not just media)."
    )
    st.stop()

# ── Date filter ───────────────────────────────────────────────────────────────

st.sidebar.header("Filters")
min_date = df["datetime"].min().date()
max_date = df["datetime"].max().date()

date_range = st.sidebar.date_input(
    "Date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)

if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
    start, end = date_range
    df = df[(df["datetime"].dt.date >= start) & (df["datetime"].dt.date <= end)]

if df.empty:
    st.warning("No messages in the selected date range.")
    st.stop()

# Author filter
all_authors = sorted(df["author"].unique())
selected_authors = st.sidebar.multiselect(
    "Show only these people",
    options=all_authors,
    default=all_authors,
)
if selected_authors:
    df = df[df["author"].isin(selected_authors)]

if df.empty:
    st.warning("No messages for the selected people.")
    st.stop()

# Store filtered df so @st.fragment functions can read it without taking df as a parameter.
# Passing a large DataFrame as a fragment argument is unreliable across fragment reruns.
st.session_state["_df"] = df

# ── Summary cards ─────────────────────────────────────────────────────────────

stats = m.summary_stats(df)
st.session_state["_stats"] = stats

col1, col2, col3, col4, col5, col6 = st.columns([1.1, 0.8, 1.3, 1.3, 1.5, 1])
col1.metric("Total Messages", f"{stats['total_messages']:,}",
            help="Total number of text messages parsed (media and system messages excluded)")
col2.metric("People", stats["total_authors"],
            help="Number of unique senders in the chat")
col3.metric("From", stats["date_from"],
            help="Date of the first message in the selected filter")
col4.metric("To", stats["date_to"],
            help="Date of the last message in the selected filter")
col5.metric("Active Days", f"{stats['active_days']:,} / {stats['total_days']:,}",
            help="Days with at least one message out of the total days the chat has existed")
col6.metric("Activity Rate", stats["activity_rate"],
            help="Percentage of days in the chat's lifetime that had at least one message")

st.divider()

# ── Tab fragments — each runs independently so one tab's widgets don't
#    trigger reruns in the others. ──────────────────────────────────────────

@st.fragment
def _tab_overview():
    df = st.session_state.get("_df")
    if df is None or df.empty:
        return
    msg_counts = m.message_counts(df)
    wrd_counts = m.word_counts(df)
    avg_lens   = m.avg_message_length(df)

    person_col = st.column_config.TextColumn("Person", width="medium")
    num_col    = st.column_config.NumberColumn(width="small")

    ov1, ov2, ov3 = st.columns(3)
    with ov1:
        st.dataframe(
            msg_counts.rename("Messages").reset_index().rename(columns={"index": "Person"}),
            width='stretch', hide_index=True,
            column_config={"Person": person_col, "Messages": num_col},
        )
    with ov2:
        st.dataframe(
            wrd_counts.rename("Total Words").reset_index().rename(columns={"index": "Person"}),
            width='stretch', hide_index=True,
            column_config={"Person": person_col, "Total Words": num_col},
        )
    with ov3:
        st.dataframe(
            avg_lens.rename("Avg Words/Msg").reset_index().rename(columns={"index": "Person"}),
            width='stretch', hide_index=True,
            column_config={"Person": person_col, "Avg Words/Msg": num_col},
        )

    st.plotly_chart(c.word_count_bar(wrd_counts, avg_lens), width='stretch')
    st.plotly_chart(c.monthly_by_author_chart(m.monthly_by_author(df)), width='stretch')
    st.plotly_chart(c.most_active_day_chart(m.most_active_day(df)), width='stretch')

    streak = m.longest_streak(df)
    st.info(
        f"🔥 **Longest streak:** {streak['streak_days']} consecutive days "
        f"({streak['start']} to {streak['end']})"
    )

    # st.divider()
    # st.markdown("**Export**")
    # stats_frozen = tuple(st.session_state.get("_stats", {}).items())
    # exp1, exp2 = st.columns(2)
    # with exp1:
    #     if st.button("📄 Generate PDF Report", key="gen_pdf_btn"):
    #         with st.spinner("Building PDF…"):
    #             st.session_state["_pdf_bytes"] = cached_summary_pdf(df, stats_frozen)
    #     if st.session_state.get("_pdf_bytes"):
    #         st.download_button(
    #             "⬇️ Download PDF",
    #             data=st.session_state["_pdf_bytes"],
    #             file_name="wa_chat_report.pdf",
    #             mime="application/pdf",
    #             key="dl_pdf_btn",
    #         )
    # with exp2:
    #     if st.button("🖼️ Save Overview as Image", key="gen_img_btn"):
    #         with st.spinner("Rendering image…"):
    #             st.session_state["_img_bytes"] = cached_overview_img(df, stats_frozen)
    #     if st.session_state.get("_img_bytes"):
    #         st.download_button(
    #             "⬇️ Download Image",
    #             data=st.session_state["_img_bytes"],
    #             file_name="wa_overview.png",
    #             mime="image/png",
    #             key="dl_img_btn",
    #         )


@st.fragment
def _tab_timing():
    df = st.session_state.get("_df")
    if df is None or df.empty:
        return
    _show_chart(c.messages_by_hour_chart(m.messages_by_hour(df)),
                "Shows which hour of the day (0 = midnight, 12 = noon) had the most messages overall. "
                "Useful for seeing when the chat is most active.")

    _show_chart(c.active_days_chart(m.active_days_per_month(df)),
                "For each month, how many distinct calendar days had at least one message. "
                "A month with 30 active days means someone texted every single day that month.")

    st.plotly_chart(c.monthly_volume_chart(m.monthly_volume(df)), width='stretch')

    _show_chart(c.weekend_weekday_chart(m.weekend_vs_weekday(df)),
                "Compares how many messages each person sends on weekdays (Mon-Fri) vs weekends (Sat-Sun). "
                "Helps reveal whether the chat is more of a weekday habit or a weekend one.")

    _show_chart(c.night_owl_chart(m.night_owl_score(df)),
                "Night (10 pm–5 am) and Morning (6 am–10 am) bars show each person's share of messages "
                "sent in those windows as a percentage of their total messages. "
                "A high Night % means they tend to text late; a high Morning % means they start early.")


@st.fragment
def _tab_response():
    df = st.session_state.get("_df")
    if df is None or df.empty:
        return
    reply_hours = st.slider(
        "Reply window (hours)",
        min_value=1, max_value=48, value=2, step=1,
        key="reply_window_slider",
        help="A response only counts as a reply if it arrives within this many hours. "
             "Increase it to capture slower conversations; decrease it for fast back-and-forth chats.",
    )

    rep_mat = cached_reply_matrix(df, reply_hours)
    avg_rt  = cached_avg_response_time(df, reply_hours)

    _show_chart(c.reply_matrix_chart(rep_mat),
                f"Each cell answers: when the row person sends a message, what fraction of the time "
                f"does the column person send the next reply within {reply_hours} hour(s)? "
                f"Values range from 0 (never replies first) to 1 (always the first to reply). "
                f"Rows sum to 1 or less because sometimes nobody replies within the window.")

    _show_chart(c.avg_response_time_chart(avg_rt),
                f"Average time in minutes before the column person replies to the row person, "
                f"measured only for replies that arrived within {reply_hours} hour(s). "
                f"Blank cells mean no reply was recorded in that direction within the window.")


@st.fragment
def _tab_words():
    df = st.session_state.get("_df")
    if df is None or df.empty:
        return
    tw = cached_top_words(df)
    ea = cached_emoji_analysis(df)
    authors = list(tw.keys())

    # Single dropdown drives everything on this tab
    options = ["Everyone"] + authors
    selected = st.selectbox("Show data for", options, key="words_author_select")
    person = None if selected == "Everyone" else selected

    st.divider()

    # ── Word cloud ───────────────────────────────────────────────────────────
    try:
        st.image(cached_word_cloud(df, person), use_container_width=True)
    except RuntimeError as e:
        st.info(f"ℹ️ {e}")

    st.divider()

    # ── Top words + emoji charts ──────────────────────────────────────────────
    if person is None:
        # "Everyone" — show all people side-by-side (max 4 cols, wrap after that)
        chunk = 4
        for i in range(0, len(authors), chunk):
            group = authors[i:i + chunk]
            cols = st.columns(len(group))
            for col, a in zip(cols, group):
                with col:
                    st.plotly_chart(c.top_words_chart(tw[a], a), width='stretch')
            cols2 = st.columns(len(group))
            for col, a in zip(cols2, group):
                with col:
                    st.plotly_chart(c.emoji_chart(ea[a], a), width='stretch')
    else:
        st.plotly_chart(c.top_words_chart(tw[person], person), width='stretch')
        st.plotly_chart(c.emoji_chart(ea[person], person), width='stretch')


@st.fragment
def _tab_behaviour():
    df = st.session_state.get("_df")
    if df is None or df.empty:
        return
    _show_chart(c.conversation_starters_chart(m.conversation_starters(df)),
                "A conversation start is counted every time someone sends the first message "
                "after the chat has been silent for 4+ hours. This reveals who tends to initiate "
                "contact rather than waiting for the other person to reach out.")

    ghost = m.ghosting_index(df)
    if not ghost.empty:
        _show_chart(c.ghosting_chart(ghost),
                    "Counts the number of times a person's last message in a conversation turn "
                    "went unanswered for 24+ hours. Messages ending with farewell phrases "
                    "(e.g. bye, good night, gtg) are excluded since no reply is expected.")
    else:
        st.info("No unanswered messages found.")

    links = m.link_sharing(df)
    if not links.empty:
        _show_chart(c.link_sharing_chart(links),
                    "Total number of URLs (http/https/www links) shared by each person.")
    else:
        st.info("No links found in this chat.")


@st.fragment
def _tab_race():
    df = st.session_state.get("_df")
    if df is None or df.empty:
        return

    st.markdown(
        "Watch message counts accumulate over time. "
        "Press **▶ Play** to start, or drag the slider to any point."
    )

    rc1, rc2 = st.columns(2)
    with rc1:
        granularity = st.selectbox(
            "Time granularity",
            options=["Monthly", "Weekly", "Daily"],
            index=0,
            key="race_granularity",
            help="How finely to slice time. Daily can be very slow for long chats.",
        )
    with rc2:
        speed = st.slider(
            "Animation speed (ms per frame)",
            min_value=100, max_value=2000, value=600, step=100,
            key="race_speed_slider",
            help="Lower = faster animation. 600 ms is a good default.",
        )

    gran_map  = {"Monthly": "M", "Weekly": "W", "Daily": "D"}
    gran_code = gran_map[granularity]

    if gran_code == "D" and len(df) > 3000:
        st.warning(
            "Daily granularity on a large chat can generate hundreds of frames and may be slow. "
            "Consider switching to Weekly or Monthly."
        )

    race_fig = c.message_race_chart(df, granularity=gran_code, frame_ms=speed)

    _show_chart(race_fig,
                "Bars are sorted by current cumulative count each frame, so rankings shift as the "
                "animation plays. The slider lets you jump to any specific time period manually.")

    html_bytes = race_fig.to_html(include_plotlyjs="cdn").encode()
    st.download_button(
        label="⬇️ Download animation as HTML",
        data=html_bytes,
        file_name="message_race.html",
        mime="text/html",
        key="dl_html_btn",
        help="Opens in any browser. The animation is fully interactive — no internet needed after download.",
    )

    st.divider()
    st.markdown("**Export as MP4 video**")
    mp4_col1, mp4_col2 = st.columns([1, 2])
    with mp4_col1:
        mp4_fps = st.selectbox(
            "Video speed",
            options=[1, 2, 3, 5],
            index=1,
            key="mp4_fps",
            format_func=lambda x: f"{x} fps",
            help="Frames per second. 2 fps = 0.5 s per time period.",
        )
    with mp4_col2:
        if st.button("🎬 Generate MP4", key="gen_mp4_btn"):
            with st.spinner("Rendering frames — this takes ~10–30 s…"):
                try:
                    st.session_state["_mp4_bytes"] = cached_race_mp4(df, gran_code, mp4_fps)
                except RuntimeError as e:
                    st.error(str(e))

    if st.session_state.get("_mp4_bytes"):
        st.download_button(
            "⬇️ Download MP4",
            data=st.session_state["_mp4_bytes"],
            file_name="message_race.mp4",
            mime="video/mp4",
            key="dl_mp4_btn",
        )


# ── Render tabs ───────────────────────────────────────────────────────────────

tab_overview, tab_timing, tab_response, tab_words, tab_behaviour, tab_race = st.tabs([
    "📊 Overview",
    "⏰ Timing",
    "↩️ Responses",
    "🔤 Words & Emojis",
    "🧠 Behaviour",
    "🎬 Message Race",
])

with tab_overview:  _tab_overview()
with tab_timing:    _tab_timing()
with tab_response:  _tab_response()
with tab_words:     _tab_words()
with tab_behaviour: _tab_behaviour()
with tab_race:      _tab_race()


# ── Footer ────────────────────────────────────────────────────────────────────

st.divider()
st.caption(
    "Built with Streamlit & Plotly · All processing is in-memory · No data is stored"
)
