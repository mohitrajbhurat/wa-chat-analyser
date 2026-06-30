import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

_TEMPLATE = "plotly_white"
_COLOR_SEQ = px.colors.qualitative.Set2


def active_days_chart(data: pd.DataFrame) -> go.Figure:
    fig = px.bar(
        data, x="year_month", y="active_days", color="year",
        title="Active Days per Month",
        labels={"year_month": "Month", "active_days": "Days with Messages", "year": "Year"},
        color_discrete_sequence=_COLOR_SEQ,
        template=_TEMPLATE,
    )
    fig.update_layout(xaxis_tickangle=-45)
    return fig


def messages_by_hour_chart(data: pd.DataFrame) -> go.Figure:
    fig = px.bar(
        data, x="hour", y="message_count",
        title="Messages by Hour of Day",
        labels={"hour": "Hour (24h)", "message_count": "Messages"},
        template=_TEMPLATE,
        color="message_count",
        color_continuous_scale="Blues",
    )
    # Blues starts near-white for low values; use a green ramp that stays visible
    fig.update_traces(marker_color=None)
    fig.update_layout(xaxis=dict(dtick=1), coloraxis_showscale=False)
    fig.update_traces(marker=dict(color=data["message_count"],
                                  colorscale=[[0, "#A8D8C8"], [1, "#075E54"]]))
    return fig


def monthly_volume_chart(data: pd.DataFrame) -> go.Figure:
    data = data.copy()
    data["year"] = data["year"].astype(str)
    fig = px.line(
        data, x="month", y="message_count", color="year",
        markers=True,
        title="Monthly Message Volume by Year",
        labels={"month": "Month", "message_count": "Messages", "year": "Year"},
        template=_TEMPLATE,
        color_discrete_sequence=_COLOR_SEQ,
    )
    fig.update_layout(xaxis=dict(dtick=1))
    return fig


def monthly_by_author_chart(data: pd.DataFrame) -> go.Figure:
    fig = px.line(
        data, x="year_month", y="message_count", color="author",
        markers=True,
        title="Monthly Messages per Person",
        labels={"year_month": "Month", "message_count": "Messages", "author": "Person"},
        template=_TEMPLATE,
        color_discrete_sequence=_COLOR_SEQ,
    )
    fig.update_layout(xaxis_tickangle=-45)
    return fig


def reply_matrix_chart(data: pd.DataFrame) -> go.Figure:
    fig = px.imshow(
        data,
        text_auto=".2f",
        color_continuous_scale="Blues",
        title="Who Replies to Whom",
        labels=dict(x="Replies from", y="Original message from", color="Reply %"),
        template=_TEMPLATE,
    )
    # Black out the diagonal — replying to yourself is meaningless
    for i in range(len(data.index)):
        fig.add_shape(
            type="rect",
            x0=i - 0.5, x1=i + 0.5,
            y0=i - 0.5, y1=i + 0.5,
            fillcolor="black",
            line=dict(width=0),
            layer="above",
        )
    return fig


def avg_response_time_chart(data: pd.DataFrame) -> go.Figure:
    fig = px.imshow(
        data.astype(float),
        text_auto=".1f",
        color_continuous_scale="RdBu_r",
        title="Average First-Reply Time (minutes)",
        labels=dict(x="Replied by", y="Message from", color="Minutes"),
        template=_TEMPLATE,
    )
    return fig


def top_words_chart(data: pd.DataFrame, author: str) -> go.Figure:
    fig = px.bar(
        data.sort_values("count"), x="count", y="word",
        orientation="h",
        title=f"Top Words — {author}",
        labels={"count": "Count", "word": "Word"},
        template=_TEMPLATE,
        color="count",
        color_continuous_scale="Teal",
    )
    fig.update_layout(coloraxis_showscale=False, yaxis_title="")
    return fig


def emoji_chart(data: pd.DataFrame, author: str) -> go.Figure:
    if data.empty:
        fig = go.Figure()
        fig.add_annotation(text="No emojis found", showarrow=False, font_size=16)
        fig.update_layout(title=f"Top Emojis — {author}", template=_TEMPLATE)
        return fig
    fig = px.bar(
        data.sort_values("count"), x="count", y="emoji",
        orientation="h",
        title=f"Top Emojis — {author}",
        labels={"count": "Count", "emoji": "Emoji"},
        template=_TEMPLATE,
        color="count",
        color_continuous_scale="Oranges",
    )
    fig.update_layout(coloraxis_showscale=False, yaxis_title="", yaxis_tickfont_size=18)
    return fig


def conversation_starters_chart(data: pd.Series) -> go.Figure:
    df = data.reset_index()
    df.columns = ["author", "count"]
    fig = px.pie(
        df, names="author", values="count",
        title="Who Starts Conversations (after 4h gap)",
        template=_TEMPLATE,
        color_discrete_sequence=_COLOR_SEQ,
    )
    fig.update_traces(textinfo="label+percent")
    return fig


def ghosting_chart(data: pd.Series) -> go.Figure:
    df = data.reset_index()
    df.columns = ["author", "unanswered"]
    fig = px.bar(
        df, x="author", y="unanswered",
        title="Unanswered Messages (no reply within 24 h)",
        labels={"unanswered": "Unanswered Messages", "author": "Person"},
        template=_TEMPLATE,
        color="unanswered",
        color_continuous_scale="Reds",
    )
    fig.update_layout(coloraxis_showscale=False)
    return fig


def weekend_weekday_chart(data: pd.DataFrame) -> go.Figure:
    fig = px.bar(
        data, x="author", y="count", color="day_type",
        barmode="group",
        title="Weekend vs Weekday Activity",
        labels={"count": "Messages", "author": "Person", "day_type": "Day Type"},
        template=_TEMPLATE,
        color_discrete_sequence=_COLOR_SEQ,
    )
    return fig


def night_owl_chart(data: pd.DataFrame) -> go.Figure:
    melted = data.melt(id_vars="author", value_vars=["night_pct", "morning_pct"],
                       var_name="period", value_name="pct")
    melted["period"] = melted["period"].map({"night_pct": "Night (10pm–5am)",
                                             "morning_pct": "Morning (6am–10am)"})
    fig = px.bar(
        melted, x="author", y="pct", color="period",
        barmode="group",
        title="Night Owl vs Early Bird",
        labels={"pct": "% of Messages", "author": "Person", "period": "Period"},
        template=_TEMPLATE,
        color_discrete_sequence=_COLOR_SEQ,
    )
    return fig


def link_sharing_chart(data: pd.Series) -> go.Figure:
    df = data.reset_index()
    df.columns = ["author", "links"]
    fig = px.bar(
        df, x="author", y="links",
        title="Links Shared",
        labels={"links": "URLs Shared", "author": "Person"},
        template=_TEMPLATE,
        color="links",
        color_continuous_scale="Purples",
    )
    fig.update_layout(coloraxis_showscale=False)
    return fig


def most_active_day_chart(data: pd.DataFrame) -> go.Figure:
    data = data.copy()
    # Format date as "07 Apr 2025" for readability
    data["date_label"] = pd.to_datetime(data["date_only"]).dt.strftime("%d %b %Y")
    # Sort ascending so highest bar ends up at top in a horizontal chart
    data = data.sort_values("count", ascending=True)
    fig = px.bar(
        data, x="count", y="date_label",
        orientation="h",
        title="Top 10 Most Active Days",
        labels={"count": "Messages", "date_label": "Date"},
        template=_TEMPLATE,
        text="count",
        color="count",
        color_continuous_scale="Greens",
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        coloraxis_showscale=False,
        yaxis_title="",
        xaxis_title="Messages",
        xaxis=dict(range=[0, data["count"].max() * 1.15]),
    )
    return fig


def message_race_chart(df: pd.DataFrame, granularity: str = "M", frame_ms: int = 600) -> go.Figure:
    """
    Racing bar chart with smooth native CSS transitions.

    Author labels are a go.Scatter(mode='text') trace whose y values are the
    same rank values as the bars — so they animate together with redraw=False.
    The x-axis is extended into negative territory to give room for the labels.
    """
    df = df.copy()
    df["period"] = df["datetime"].dt.to_period(granularity).astype(str)
    periods = sorted(df["period"].unique())
    authors = sorted(df["author"].unique())
    n = len(authors)

    pivot = (
        df.groupby(["period", "author"])
        .size()
        .unstack(fill_value=0)
        .reindex(index=periods, columns=authors, fill_value=0)
        .cumsum()
    )
    max_val = int(pivot.max().max())

    palette = px.colors.qualitative.Set2 + px.colors.qualitative.Pastel
    color_map = {a: palette[i % len(palette)] for i, a in enumerate(authors)}

    # Space reserved left of x=0 for name labels (in data units)
    label_pad = max_val * 0.22

    def ranks_for(period: str) -> dict:
        vals = pivot.loc[period]
        return {a: float(i) for i, a in enumerate(vals.sort_values(ascending=True).index)}

    def make_traces(period: str) -> list:
        r = ranks_for(period)

        # Trace 0: author names as scatter text anchored at x=0, textposition="middle left"
        # → text extends LEFT into the label_pad region.
        # Because this is DATA (not layout), redraw=False animates the y positions smoothly.
        traces = [go.Scatter(
            x=[0] * n,
            y=[r[a] for a in authors],
            mode="text",
            text=[f"<b>{a}</b>" for a in authors],
            textposition="middle left",
            textfont=dict(size=12, color=[color_map[a] for a in authors]),
            showlegend=False,
            hoverinfo="skip",
            cliponaxis=False,
            name="_labels",
        )]

        # Traces 1…n: one Bar per author so Plotly tracks each across frames
        for a in authors:
            v = float(pivot.loc[period, a])
            traces.append(go.Bar(
                name=a,
                x=[v],
                y=[r[a]],
                orientation="h",
                width=0.8,
                marker_color=color_map[a],
                text=[f"{int(v):,}"],
                textposition="outside",
                cliponaxis=False,
                hovertemplate=f"<b>{a}</b><br>Messages: %{{x:,.0f}}<extra></extra>",
            ))
        return traces

    all_frames = [go.Frame(data=make_traces(p), name=p) for p in periods]

    slider_steps = [
        dict(
            args=[[p], {
                "frame": {"duration": 0, "redraw": True},
                "mode": "immediate",
                "transition": {"duration": 0},
            }],
            label=p,
            method="animate",
        )
        for p in periods
    ]

    transition_ms = max(100, int(frame_ms * 0.9))
    fig = go.Figure(data=make_traces(periods[0]), frames=all_frames)

    fig.update_layout(
        title="Cumulative Message Count",
        xaxis=dict(
            range=[-label_pad, max_val * 1.15],
            title="Total Messages",
            fixedrange=True,
            # Only tick marks in the positive/zero range
            tickvals=[int(max_val * i / 4) for i in range(5)],
            ticktext=[f"{int(max_val * i / 4):,}" for i in range(5)],
            zeroline=True,
            zerolinewidth=1.5,
            zerolinecolor="#bbbbbb",
        ),
        yaxis=dict(
            showticklabels=False,
            showgrid=False,
            zeroline=False,
            range=[-0.6, n - 0.4],
            fixedrange=True,
        ),
        barmode="overlay",
        legend=dict(x=1.02, y=0.5, xanchor="left", yanchor="middle"),
        template=_TEMPLATE,
        height=max(420, n * 70 + 180),
        margin=dict(l=10, r=160, t=80, b=60),
        updatemenus=[dict(
            type="buttons",
            showactive=False,
            y=1.12, x=0, xanchor="left",
            buttons=[
                dict(
                    label="▶  Play",
                    method="animate",
                    args=[None, {
                        "frame": {"duration": frame_ms, "redraw": False},
                        "fromcurrent": True,
                        "transition": {"duration": transition_ms, "easing": "cubic-in-out"},
                    }],
                ),
                dict(
                    label="⏸  Pause",
                    method="animate",
                    args=[[None], {"frame": {"duration": 0}, "mode": "immediate"}],
                ),
            ],
        )],
        sliders=[dict(
            active=0,
            currentvalue=dict(prefix="Period: ", visible=True, xanchor="center"),
            pad=dict(t=50),
            steps=slider_steps,
        )],
    )

    return fig


def generate_race_mp4(df: pd.DataFrame, granularity: str = "M", fps: int = 2) -> bytes:
    """Render bar-race frames with matplotlib and encode to MP4 via imageio-ffmpeg."""
    import io as _io
    import os
    import tempfile
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import imageio
        import numpy as np
    except ImportError as exc:
        raise RuntimeError(
            "MP4 export requires matplotlib and imageio-ffmpeg.\n"
            "Run: pip install matplotlib 'imageio[ffmpeg]'"
        ) from exc

    df = df.copy()
    df["period"] = df["datetime"].dt.to_period(granularity).astype(str)
    periods = sorted(df["period"].unique())
    authors = sorted(df["author"].unique())
    n = len(authors)

    pivot = (
        df.groupby(["period", "author"])
        .size()
        .unstack(fill_value=0)
        .reindex(index=periods, columns=authors, fill_value=0)
        .cumsum()
    )
    max_val = int(pivot.max().max())

    # Use guaranteed-hex colours — Plotly's qualitative palettes can return
    # 'rgb(…)' strings which matplotlib does not accept.
    color_map = {a: _PDF_COLORS[i % len(_PDF_COLORS)] for i, a in enumerate(authors)}

    # Fixed canvas size so all frames are identical dimensions
    w_px = 1400
    h_px = max(500, n * 90 + 200)
    h_px += h_px % 2      # ensure even for h264
    fig_mpl, ax = plt.subplots(figsize=(w_px / 100, h_px / 100), dpi=100)
    fig_mpl.patch.set_facecolor("white")
    fig_mpl.subplots_adjust(left=0.18, right=0.92, top=0.88, bottom=0.10)

    frame_arrays = []
    for period in periods:
        ax.clear()
        counts = pivot.loc[period].sort_values(ascending=True)

        ax.barh(range(len(counts)), counts.values,
                color=[color_map[a] for a in counts.index], height=0.7, edgecolor="white")
        ax.set_yticks(range(len(counts)))
        ax.set_yticklabels(counts.index, fontsize=11, fontweight="bold")
        ax.set_xlim(0, max_val * 1.15)
        ax.set_ylim(-0.6, n - 0.4)
        ax.set_xlabel("Total Messages", fontsize=11)
        ax.set_title(f"Cumulative Message Count — {period}", fontsize=14, fontweight="bold")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.tick_params(left=False)

        for i, (_, v) in enumerate(counts.items()):
            if v > 0:
                ax.text(v + max_val * 0.01, i, f"{int(v):,}", va="center", fontsize=10, color="#333")

        buf = _io.BytesIO()
        fig_mpl.savefig(buf, format="png", dpi=100, facecolor="white")
        buf.seek(0)
        img = imageio.imread(buf)
        frame_arrays.append(img[:, :, :3])   # drop alpha channel if present

    plt.close(fig_mpl)

    # All frames should be the same size from fixed figsize, but guard anyway
    h0, w0 = frame_arrays[0].shape[:2]
    frame_arrays = [f[:h0, :w0] for f in frame_arrays]

    tmp = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
    tmp_path = tmp.name
    tmp.close()
    try:
        imageio.mimwrite(tmp_path, frame_arrays, fps=fps, quality=8)
        with open(tmp_path, "rb") as f:
            return f.read()
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def word_count_bar(word_counts: pd.Series, avg_lengths: pd.Series) -> go.Figure:
    df = pd.DataFrame({
        "author": word_counts.index,
        "total_words": word_counts.values,
    })
    fig = px.bar(
        df, x="author", y="total_words",
        title="Total Words Sent",
        labels={"total_words": "Words", "author": "Person"},
        template=_TEMPLATE,
        color="total_words",
        color_continuous_scale="Teal",
    )
    fig.update_layout(coloraxis_showscale=False)
    return fig


# ── Word clouds ──────────────────────────────────────────────────────────────

_WC_STOP = {
    "the","a","an","and","or","but","in","on","at","to","for","of","with",
    "is","it","this","that","was","are","be","been","have","has","had","do",
    "did","will","would","could","should","i","you","he","she","we","they",
    "my","your","his","her","our","their","me","him","us","them","so","if",
    "as","up","out","no","not","what","all","just","by","from","about","can",
    "when","there","which","also","into","its","than","then","like","ok",
    "okay","yeah","yes","lol","omitted","media","deleted","message","null",
    "yea","haha","hahaha","na","nah","ll","ve","re","got","get","let","know",
    "think","make","one","two","oh","ah","um","don","didn","won","isn","aren",
}


def word_cloud_img(df: pd.DataFrame, author: str | None = None) -> bytes:
    """Return a PNG word cloud (bytes) for one author or the whole chat."""
    import re as _re, io as _io
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    try:
        from wordcloud import WordCloud
    except ImportError:
        raise RuntimeError("wordcloud not installed — run: pip install wordcloud")

    subset = df if author is None else df[df["author"] == author]
    raw = " ".join(subset["message"].fillna(""))
    words = _re.findall(r"\b[a-zA-Z]{2,}\b", raw.lower())
    text = " ".join(w for w in words if w not in _WC_STOP) or "no text"

    wc = WordCloud(
        width=900, height=380,
        background_color=None,
        mode="RGBA",
        max_words=120,
        colormap="Dark2",        # always-dark colours — visible on both light and dark bg
        collocations=False,
        prefer_horizontal=0.7,
    ).generate(text)

    fig, ax = plt.subplots(figsize=(9, 3.8))
    fig.patch.set_alpha(0)       # transparent figure background
    ax.patch.set_alpha(0)        # transparent axes background
    ax.imshow(wc, interpolation="bilinear")
    ax.axis("off")
    buf = _io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", pad_inches=0.05, dpi=120,
                transparent=True)
    plt.close(fig)
    buf.seek(0)
    return buf.read()


# ── PDF report ───────────────────────────────────────────────────────────────

_WA_GREEN = "#25D366"
_WA_DARK  = "#075E54"
_PDF_COLORS = ["#25D366", "#128C7E", "#075E54", "#34B7F1", "#A8D8A8",
               "#F6D860", "#F19CBB", "#B2DFDB", "#FFB74D", "#CE93D8"]


def generate_summary_pdf(df: pd.DataFrame, stats: dict) -> bytes:
    """Render a 4-page A4 PDF with professional layout and branding."""
    import io as _io
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.gridspec as gridspec
    from matplotlib.patches import Circle, FancyBboxPatch
    from matplotlib.backends.backend_pdf import PdfPages
    import numpy as np

    buf = _io.BytesIO()
    authors = sorted(df["author"].unique())
    n_auth = len(authors)
    color_for = {a: _PDF_COLORS[i % len(_PDF_COLORS)] for i, a in enumerate(authors)}

    def _clean(ax):
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color("#CCCCCC")
        ax.spines["bottom"].set_color("#CCCCCC")
        ax.yaxis.grid(True, color="#F2F2F2", linewidth=0.8, zorder=0)
        ax.set_axisbelow(True)
        ax.set_facecolor("#FAFAFA")
        ax.tick_params(axis="both", length=0, labelsize=9, pad=4)

    # fig.patches approach: patches added directly to the figure with
    # transform=fig.transFigure are immune to axis("off") / set_frame_on side-effects.
    from matplotlib.patches import Rectangle as _Rect, Ellipse as _Ell

    def _bg(fig, x, y, w, h, color, zorder=1):
        """Add a solid colored rectangle to the figure (not an axes)."""
        fig.patches.append(_Rect((x, y), w, h, facecolor=color, edgecolor="none",
                                 transform=fig.transFigure, zorder=zorder,
                                 clip_on=False))

    def _banner(fig, title):
        _bg(fig, 0, 0.964, 1, 0.036, _WA_DARK)
        fig.text(0.015, 0.982, f"  {title}", ha="left", va="center",
                 fontsize=10, fontweight="bold", color="white", zorder=2)
        fig.text(0.985, 0.982, "WhatsApp Chat Analyser  ", ha="right", va="center",
                 fontsize=8, color=_WA_GREEN, zorder=2)

    def _card(fig, x, y, w, h, value, label):
        ax = fig.add_axes([x, y, w, h])
        ax.axis("off")
        ax.add_patch(FancyBboxPatch(
            (0.04, 0.06), 0.92, 0.88,
            boxstyle="round,pad=0.04",
            facecolor="#F0FAF5", edgecolor=_WA_GREEN,
            linewidth=1.8, transform=ax.transAxes, clip_on=False,
        ))
        ax.text(0.5, 0.63, value, ha="center", va="center",
                fontsize=19, fontweight="bold", color=_WA_DARK,
                transform=ax.transAxes)
        ax.text(0.5, 0.24, label, ha="center", va="center",
                fontsize=9, color="#666", transform=ax.transAxes)

    FW_PDF, FH_PDF = 8.27, 11.69

    def _wa_logo_pdf(fig, cx_fig, cy_fig, r_in=0.75):
        """Draw a true circle WA logo in figure coordinates.
        Uses Ellipse with compensated axis dimensions so it appears circular."""
        ew = 2 * r_in / FW_PDF   # fraction of figure width
        eh = 2 * r_in / FH_PDF   # fraction of figure height
        # Physical: ew*FW_PDF == eh*FH_PDF == 2*r_in inches → truly circular
        fig.patches.append(_Ell((cx_fig, cy_fig), width=ew, height=eh,
                                facecolor=_WA_GREEN, edgecolor="white", linewidth=3,
                                transform=fig.transFigure, zorder=3, clip_on=False))
        fig.text(cx_fig, cy_fig, "WA", ha="center", va="center",
                 fontsize=22, fontweight="bold", color="white", zorder=4)

    with PdfPages(buf) as pdf:

        # ── Page 1: Cover ────────────────────────────────────────────────────
        fig = plt.figure(figsize=(FW_PDF, FH_PDF))
        fig.patch.set_facecolor("white")

        # Dark green top half and footer via figure patches (not axes)
        _bg(fig, 0, 0.47, 1, 0.53, _WA_DARK)
        _bg(fig, 0.04, 0.465, 0.92, 0.004, _WA_GREEN)   # thin divider
        _bg(fig, 0, 0, 1, 0.05, _WA_GREEN)               # footer

        # WA circle: Ellipse in figure coords → always circular
        _wa_logo_pdf(fig, cx_fig=0.5, cy_fig=0.878)

        # Text in coloured band — use fig.text with figure coordinates
        fig.text(0.5, 0.746, "WhatsApp Chat Analysis",
                 ha="center", fontsize=22, fontweight="bold", color="white", zorder=2)
        fig.text(0.5, 0.646, f"{stats['date_from']}  →  {stats['date_to']}",
                 ha="center", fontsize=13, color="#A8E6C1", zorder=2)
        fig.text(0.5, 0.565,
                 f"{stats['total_messages']:,} messages · {stats['total_authors']} people",
                 ha="center", fontsize=11, color="#CCE5D8", zorder=2)
        fig.text(0.5, 0.022, "Generated by WhatsApp Chat Analyser",
                 ha="center", fontsize=9, color="white", zorder=2)

        # Stat cards (2 × 2) in the white lower half
        card_data = [
            (f"{stats['total_messages']:,}", "Total Messages"),
            (str(stats["total_authors"]),    "People"),
            (f"{stats['active_days']:,} / {stats['total_days']:,}", "Active Days"),
            (stats["activity_rate"],          "Activity Rate"),
        ]
        for idx, (value, label) in enumerate(card_data):
            _card(fig,
                  x=0.06 + (idx % 2) * 0.50,
                  y=0.26 - (idx // 2) * 0.19,
                  w=0.40, h=0.15, value=value, label=label)

        pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)

        # ── Page 2: Message Activity ─────────────────────────────────────────
        msg_counts = df["author"].value_counts()
        hour_counts = df["hour"].value_counts().reindex(range(24), fill_value=0)

        fig = plt.figure(figsize=(8.27, 11.69))
        fig.patch.set_facecolor("white")
        _banner(fig, "Message Activity")
        gs = gridspec.GridSpec(2, 1, left=0.18, right=0.90,
                               top=0.91, bottom=0.07, hspace=0.50)

        ax = fig.add_subplot(gs[0])
        ax.barh(msg_counts.index[::-1], msg_counts.values[::-1],
                color=[color_for.get(a, _WA_GREEN) for a in msg_counts.index[::-1]],
                height=0.55)
        _clean(ax)
        ax.xaxis.grid(True, color="#F2F2F2", linewidth=0.8)
        ax.yaxis.grid(False)
        ax.set_title("Total Messages per Person", fontsize=13, fontweight="bold",
                     color=_WA_DARK, pad=10, loc="left")
        ax.set_xlabel("Messages", fontsize=9)
        for i, v in enumerate(msg_counts.values[::-1]):
            ax.text(v + msg_counts.max() * 0.012, i, f"{v:,}",
                    va="center", fontsize=8, color="#444")

        peak_h = hour_counts.idxmax()
        bar_colors = [_WA_GREEN if h != peak_h else "#FF6B35" for h in range(24)]
        ax = fig.add_subplot(gs[1])
        ax.bar(range(24), [hour_counts.get(h, 0) for h in range(24)],
               color=bar_colors, width=0.72)
        _clean(ax)
        ax.xaxis.grid(False)
        ax.set_title("Messages by Hour of Day", fontsize=13, fontweight="bold",
                     color=_WA_DARK, pad=10, loc="left")
        ax.set_xlabel("Hour (24 h)", fontsize=9)
        ax.set_ylabel("Messages", fontsize=9)
        ax.set_xticks(range(0, 24, 3))
        ax.set_xticklabels([f"{h:02d}h" for h in range(0, 24, 3)], fontsize=8)
        ax.annotate(f"Peak: {peak_h:02d}h",
                    xy=(peak_h, hour_counts[peak_h]),
                    xytext=(min(peak_h + 3, 20), hour_counts[peak_h] * 0.80),
                    fontsize=8, color="#FF6B35", fontweight="bold",
                    arrowprops=dict(arrowstyle="->", color="#FF6B35", lw=0.9))

        fig.text(0.5, 0.022, "2 / 4", ha="center", fontsize=8, color="#AAAAAA")
        pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)

        # ── Page 3: Timing ───────────────────────────────────────────────────
        monthly = (df.groupby(["author", "year_month"]).size()
                   .unstack(fill_value=0).sort_index(axis=1))
        wk = df.copy()
        wk["type"] = wk["weekday"].isin(["Saturday", "Sunday"]).map(
            {True: "Weekend", False: "Weekday"})
        wk_counts = wk.groupby(["author", "type"]).size().unstack(fill_value=0)

        fig = plt.figure(figsize=(8.27, 11.69))
        fig.patch.set_facecolor("white")
        _banner(fig, "Timing Patterns")
        gs = gridspec.GridSpec(2, 1, left=0.12, right=0.92,
                               top=0.91, bottom=0.08, hspace=0.52)

        ax = fig.add_subplot(gs[0])
        for a in monthly.index:
            vals = monthly.loc[a].values
            xs = range(len(monthly.columns))
            ax.plot(xs, vals, marker="o", markersize=4, label=a,
                    color=color_for.get(a, _WA_GREEN), lw=2, solid_capstyle="round")
            ax.fill_between(xs, vals, alpha=0.07, color=color_for.get(a, _WA_GREEN))
        _clean(ax)
        step = max(1, len(monthly.columns) // 8)
        ax.set_xticks(range(0, len(monthly.columns), step))
        ax.set_xticklabels(
            [monthly.columns[i] for i in range(0, len(monthly.columns), step)],
            rotation=35, ha="right", fontsize=8)
        ax.set_title("Monthly Messages per Person", fontsize=13, fontweight="bold",
                     color=_WA_DARK, pad=10, loc="left")
        ax.set_ylabel("Messages", fontsize=9)
        ax.legend(fontsize=9, framealpha=0.85, edgecolor="#DDD", loc="upper left")

        ax = fig.add_subplot(gs[1])
        xi = list(range(len(wk_counts)))
        w = 0.35
        wday = wk_counts.get("Weekday", pd.Series(0, index=wk_counts.index))
        wend = wk_counts.get("Weekend", pd.Series(0, index=wk_counts.index))
        ax.bar([x - w / 2 for x in xi], wday, width=w, label="Weekday",
               color=_WA_GREEN, alpha=0.9)
        ax.bar([x + w / 2 for x in xi], wend, width=w, label="Weekend",
               color="#34B7F1", alpha=0.9)
        _clean(ax)
        ax.set_xticks(xi)
        ax.set_xticklabels(wk_counts.index, rotation=20, ha="right", fontsize=9)
        ax.set_title("Weekend vs Weekday Activity", fontsize=13, fontweight="bold",
                     color=_WA_DARK, pad=10, loc="left")
        ax.set_ylabel("Messages", fontsize=9)
        ax.legend(fontsize=9, framealpha=0.85, edgecolor="#DDD")

        fig.text(0.5, 0.022, "3 / 4", ha="center", fontsize=8, color="#AAAAAA")
        pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)

        # ── Page 4: Response heatmap ─────────────────────────────────────────
        df_s = df.sort_values("datetime").reset_index(drop=True)
        df_s["turn"] = (df_s["author"] != df_s["author"].shift()).cumsum()
        turns = (df_s.groupby("turn", sort=False)
                 .agg(author=("author", "first"),
                      first_time=("datetime", "min"),
                      last_time=("datetime", "max"))
                 .reset_index(drop=True))
        turns["next_author"] = turns["author"].shift(-1)
        turns["next_time"]   = turns["first_time"].shift(-1)
        turns["gap"]         = turns["next_time"] - turns["last_time"]
        valid = turns[turns["gap"].notna() & (turns["gap"] <= pd.Timedelta(hours=2))]
        counts_rep = valid.groupby(["author", "next_author"]).size()
        rep_mat = pd.DataFrame(0.0, index=authors, columns=authors)
        for (s, r), n in counts_rep.items():
            if s in rep_mat.index and r in rep_mat.columns:
                rep_mat.loc[s, r] = n
        rep_norm = rep_mat.div(rep_mat.sum(axis=1), axis=0).fillna(0)
        mat = rep_norm.values.astype(float)
        for i in range(n_auth):
            mat[i, i] = np.nan

        fig = plt.figure(figsize=(8.27, 11.69))
        fig.patch.set_facecolor("white")
        _banner(fig, "Response Analysis")

        # Dynamically size the heatmap so it looks good for 2–8 authors
        cell = min(1.5, 7.5 / max(n_auth, 2))
        hm_h = min(0.55, n_auth * cell / 11.69)
        hm_w = min(0.68, n_auth * cell / 8.27)
        hm_x = (1.0 - hm_w) / 2
        hm_y = 0.90 - hm_h - 0.06   # just below the banner

        ax = fig.add_axes([hm_x, hm_y, hm_w, hm_h])
        im = ax.imshow(mat, cmap="Blues", aspect="auto", vmin=0, vmax=1,
                       interpolation="nearest")
        ax.set_xticks(range(n_auth))
        ax.set_xticklabels(authors, rotation=35, ha="right", fontsize=9)
        ax.set_yticks(range(n_auth))
        ax.set_yticklabels(authors, fontsize=9)
        ax.set_title("Who Replies to Whom\n(reply fraction within 2 hours)",
                     fontsize=13, fontweight="bold", color=_WA_DARK, pad=12, loc="left")
        ax.set_xlabel("Replied by", fontsize=10, labelpad=8)
        ax.set_ylabel("Message from", fontsize=10, labelpad=8)
        ax.tick_params(length=0)
        for i in range(n_auth):
            for j in range(n_auth):
                if i == j:
                    ax.add_patch(
                        plt.Rectangle((j - 0.5, i - 0.5), 1, 1, color="black", zorder=2))
                elif not np.isnan(mat[i, j]):
                    tc = "white" if mat[i, j] > 0.55 else "#333"
                    ax.text(j, i, f"{mat[i, j]:.2f}", ha="center", va="center",
                            fontsize=9, color=tc, fontweight="bold", zorder=3)
        cbar = plt.colorbar(im, ax=ax, fraction=0.04, pad=0.03, shrink=0.85)
        cbar.ax.tick_params(labelsize=8, length=0)
        cbar.set_label("Reply fraction", fontsize=9)

        fig.text(0.12, hm_y - 0.05,
                 "How to read: each cell = fraction of times the column person\n"
                 "replied first to the row person within 2 hours.\n"
                 "Black cells on the diagonal = same person (not applicable).",
                 fontsize=8, color="#666", va="top", linespacing=1.7)

        fig.text(0.5, 0.022, "4 / 4", ha="center", fontsize=8, color="#AAAAAA")
        pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)

    buf.seek(0)
    return buf.read()


# ── Overview shareable image ─────────────────────────────────────────────────

def generate_overview_image(df: pd.DataFrame, stats: dict) -> bytes:
    """Return a portrait PNG card in social-media-share style."""
    import io as _io
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.gridspec as gridspec
    from matplotlib.patches import Rectangle as _Rect, Ellipse as _Ell

    FW, FH = 8.0, 14.0

    authors = sorted(df["author"].unique())
    color_for = {a: _PDF_COLORS[i % len(_PDF_COLORS)] for i, a in enumerate(authors)}
    msg_counts = df["author"].value_counts()
    hc = df["hour"].value_counts().reindex(range(24), fill_value=0)
    monthly = (df.groupby(["author", "year_month"]).size()
               .unstack(fill_value=0).sort_index(axis=1))

    fig = plt.figure(figsize=(FW, FH))
    fig.patch.set_facecolor("white")

    # ── Coloured bands via figure patches (bypasses axis frame issues) ────────
    HDR_Y, HDR_H = 0.87, 0.13   # header (dark green)
    STS_Y, STS_H = 0.78, 0.09   # stats strip (WA green)
    FTR_Y, FTR_H = 0.00, 0.03   # footer (dark green)
    fig.patches.extend([
        _Rect((0, HDR_Y), 1, HDR_H, facecolor=_WA_DARK, edgecolor="none",
              transform=fig.transFigure, zorder=1, clip_on=False),
        _Rect((0, STS_Y), 1, STS_H, facecolor=_WA_GREEN, edgecolor="none",
              transform=fig.transFigure, zorder=1, clip_on=False),
        _Rect((0, FTR_Y), 1, FTR_H, facecolor=_WA_DARK, edgecolor="none",
              transform=fig.transFigure, zorder=1, clip_on=False),
    ])

    # ── WA circle: Ellipse in figure coords — always renders as a circle ──────
    # Compensate for non-square figure: ew*FW == eh*FH == 2*r_in (inches)
    r_in = 0.52
    cx_fig = 0.09
    cy_fig = HDR_Y + HDR_H * 0.50
    ew = 2 * r_in / FW; eh = 2 * r_in / FH
    fig.patches.append(_Ell((cx_fig, cy_fig), width=ew, height=eh,
                            facecolor=_WA_GREEN, edgecolor="white", linewidth=2,
                            transform=fig.transFigure, zorder=3, clip_on=False))
    fig.text(cx_fig, cy_fig, "WA", ha="center", va="center",
             fontsize=13, fontweight="bold", color="white", zorder=4)

    # ── Header text ───────────────────────────────────────────────────────────
    fig.text(0.20, HDR_Y + HDR_H * 0.70, "WhatsApp Chat Analyser",
             ha="left", fontsize=13, fontweight="bold", color="white", zorder=2)
    fig.text(0.20, HDR_Y + HDR_H * 0.28, f"{stats['date_from']}  →  {stats['date_to']}",
             ha="left", fontsize=9, color="#A8E6C1", zorder=2)

    # ── Stats strip text ──────────────────────────────────────────────────────
    for i, (val, lbl) in enumerate([
        (f"{stats['total_messages']:,}", "Messages"),
        (str(stats["total_authors"]),    "People"),
        (f"{stats['active_days']:,}",    "Active Days"),
        (stats["activity_rate"],          "Activity"),
    ]):
        x = 0.125 + i * 0.25
        fig.text(x, STS_Y + STS_H * 0.65, val, ha="center",
                 fontsize=14, fontweight="bold", color="white", zorder=2)
        fig.text(x, STS_Y + STS_H * 0.20, lbl, ha="center",
                 fontsize=7.5, color="#D0F5E4", zorder=2)

    # ── Footer text ───────────────────────────────────────────────────────────
    fig.text(0.5, FTR_Y + FTR_H * 0.45, "Made with WhatsApp Chat Analyser",
             ha="center", va="center", fontsize=8, color="#A8E6C1", zorder=2)

    # ── Chart area ────────────────────────────────────────────────────────────
    def _clean(ax):
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color("#CCCCCC")
        ax.spines["bottom"].set_color("#CCCCCC")
        ax.set_facecolor("#FAFAFA")
        ax.tick_params(length=0, labelsize=8, pad=3)
        ax.set_axisbelow(True)
        ax.yaxis.grid(True, color="#F0F0F0", linewidth=0.7)

    gs = gridspec.GridSpec(3, 1, left=0.16, right=0.93,
                           top=STS_Y - 0.02, bottom=FTR_H + 0.02, hspace=0.58)

    # Chart 1: messages per person
    ax1 = fig.add_subplot(gs[0])
    ax1.barh(msg_counts.index[::-1], msg_counts.values[::-1],
             color=[color_for.get(a, _WA_GREEN) for a in msg_counts.index[::-1]],
             height=0.55)
    _clean(ax1)
    ax1.xaxis.grid(True, color="#F0F0F0", linewidth=0.7)
    ax1.yaxis.grid(False)
    ax1.set_title("Messages per Person", fontsize=11, fontweight="bold",
                  color=_WA_DARK, pad=7, loc="left")
    for i, v in enumerate(msg_counts.values[::-1]):
        ax1.text(v + msg_counts.max() * 0.012, i, f"{v:,}",
                 va="center", fontsize=7.5, color="#444")

    # Chart 2: messages by hour (peak highlighted in orange)
    peak = hc.idxmax()
    hour_colors = [_WA_GREEN if h != peak else "#FF6B35" for h in range(24)]
    ax2 = fig.add_subplot(gs[1])
    ax2.bar(range(24), [hc.get(h, 0) for h in range(24)],
            color=hour_colors, width=0.72)
    _clean(ax2)
    ax2.xaxis.grid(False)
    ax2.set_title("Messages by Hour", fontsize=11, fontweight="bold",
                  color=_WA_DARK, pad=7, loc="left")
    ax2.set_xticks([0, 6, 12, 18, 23])
    ax2.set_xticklabels(["Midnight", "6 am", "Noon", "6 pm", "11 pm"], fontsize=7.5)
    ax2.text(peak, hc[peak] * 1.04, f"Peak\n{peak:02d}h",
             ha="center", va="bottom", fontsize=7, color="#FF6B35", fontweight="bold")

    # Chart 3: monthly trend with area fill
    ax3 = fig.add_subplot(gs[2])
    for a in monthly.index:
        vals = monthly.loc[a].values
        xs = range(len(monthly.columns))
        ax3.plot(xs, vals, marker=".", markersize=4, label=a,
                 color=color_for.get(a, _WA_GREEN), lw=2)
        ax3.fill_between(xs, vals, alpha=0.09, color=color_for.get(a, _WA_GREEN))
    _clean(ax3)
    step = max(1, len(monthly.columns) // 5)
    ax3.set_xticks(range(0, len(monthly.columns), step))
    ax3.set_xticklabels(
        [monthly.columns[i] for i in range(0, len(monthly.columns), step)],
        rotation=30, ha="right", fontsize=7)
    ax3.set_title("Monthly Activity", fontsize=11, fontweight="bold",
                  color=_WA_DARK, pad=7, loc="left")
    ax3.legend(fontsize=7.5, loc="upper left", framealpha=0.75, edgecolor="#DDD")

    buf = _io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                facecolor="white", edgecolor="none")
    plt.close(fig)
    buf.seek(0)
    return buf.read()
