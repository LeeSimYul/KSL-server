"""
send_welcome_embed.py
VRChat 한국수어교실 - #안내 채널 웰컴 Embed 전송기 (Discord Webhook)

씨앗반 · 별빛반 · 달빛반 학급 안내, 3단계 참여 방법, 핵심 규칙을 한/영/일 3개 국어로
짧게 요약한 Embed 를 #안내 채널 웹후크로 보냅니다. 한 번 보낸 메시지는 --edit 로 같은
자리에서 고칠 수 있어서, 공지를 지우고 다시 올릴 필요가 없습니다.

    python send_welcome_embed.py --dry-run          # 보내지 않고 JSON 만 출력 (discohook.org 미리보기용)
    python send_welcome_embed.py                    # 새 메시지로 전송 → 메시지 ID 출력
    python send_welcome_embed.py --edit 메시지ID     # 이미 보낸 메시지를 최신 내용으로 수정

웹후크 주소는 비밀번호와 같습니다. 코드에 적지 말고 환경 변수 DISCORD_WEBHOOK_URL
(또는 이 파일 옆의 .env)로 넘겨 주세요.

문구를 고치면 웹 가이드(docs/welcome-guide.md)도 함께 맞춰 주세요.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import parse_qsl, quote, urlsplit, urlunsplit

import requests

try:
    from dotenv import load_dotenv
except ImportError:  # python-dotenv 가 없으면 환경 변수만 읽습니다
    load_dotenv = None

BASE_DIR = Path(__file__).resolve().parent


# ── 서버 설정 (필요한 곳만 고쳐 쓰세요) ──────────────────────────
BRAND_COLOR = 0x4A90E2  # KSL 브랜드 블루

# 채널 ID: 디스코드 개발자 모드 → 채널 우클릭 → 'ID 복사'. 숫자만 적습니다.
GUIDE_CHANNEL_ID = ""  # 📑┃안내 - 비워 두면 웹후크가 걸린 채널(= #안내)을 자동으로 씁니다
RULES_CHANNEL_ID = ""  # 📋┃규칙 - 비워 두면 채널 이름을 글자로만 적습니다

# 링크: 비워 둔 항목은 Embed 에서 빠집니다.
VRCHAT_GROUP_URL = ""  # VRChat 그룹 페이지의 공유 링크 (예: https://vrc.group/KSL.0000)
NOTION_GUIDE_URL = "https://likeable-bucket-c21.notion.site/VRChat-189a401b541880c48656f69895bf48a9"
WEB_GUIDE_URL = "https://github.com/LeeSimYul/KSL-server/blob/main/docs/welcome-guide.md"
DISCORD_INVITE_URL = "https://discord.gg/tVyvq5qZgn"

# 이미지: 공식 브랜드 저장소(Kidentity)의 원본을 그대로 씁니다. 빈 문자열이면 생략합니다.
# 디스코드 첨부 파일 주소는 시간이 지나면 만료되니, 바꿀 때도 GitHub 처럼 고정된 주소를 쓰세요.
_KIDENTITY_PNG = "https://raw.githubusercontent.com/LeeSimYul/Kidentity/main/assets/png/"
LOGO_URL = _KIDENTITY_PNG + quote("logo-icon/한국수어교실 로고 ver.2 2026.png")
BANNER_URL = _KIDENTITY_PNG + quote("discord-server-banner/VRChat 한국수어교실 디스코드 서버 배너 2.png")

WEBHOOK_USERNAME = "VRChat 한국수어교실"
WEBHOOK_AVATAR_URL = LOGO_URL

# 정기 수업 시간표 (한국 시간 KST 기준): ("반", "요일", "HH:MM")
#   반: seed(씨앗반) · star(별빛반) · moon(달빛반)   요일: mon~sun 또는 월~일
# 채우면 '📅 다음 수업' 칸이 생기고, 디스코드 타임스탬프(<t:…>)라 읽는 사람마다 자기 나라
# 시간으로 보입니다. '보낸 시점 기준 다음 수업'이 찍히므로 매주 --edit 로 다시 돌려 주세요.
# 비워 두면 칸을 생략합니다.
CLASS_SCHEDULE: list[tuple[str, str, str]] = [
    # ("seed", "sat", "21:00"),
]


# ── 문구 ─────────────────────────────────────────────────────
@dataclass(frozen=True)
class Level:
    emoji: str
    name: str      # 반 이름
    grade_ko: str  # 단계 (한국어)
    grade_en: str
    grade_ja: str
    topic_ko: str  # 배우는 내용
    topic_en: str
    topic_ja: str


LEVELS: dict[str, Level] = {
    "seed": Level("🌱", "씨앗반", "입문", "Introductory", "入門",
                  "지문자 · 기본 인사",
                  "Fingerspelling & greetings", "指文字とあいさつ"),
    "star": Level("⭐", "별빛반", "초급", "Vocabulary", "初級",
                  "필수 단어 · 손 모양",
                  "Everyday words & handshapes", "必須単語と手の形"),
    "moon": Level("🌙", "달빛반", "중급", "Sentences", "中級",
                  "문장 구성 · 비수지 신호(표정)",
                  "Sentences & non-manual markers", "文章と非手指動作(表情)"),
}

TITLE = "🏫 VRChat 한국수어교실 공식 안내"
FOOTER = "VRChat 한국수어교실 · Korean Sign Language Class · 韓国手話教室"

DESCRIPTION = "\n".join([
    '> **"당신의 손짓으로 세상과의 연결을 도와드려요."**',
    "> *Let your hands connect you to the world. · あなたの手で、世界とつながろう。*",
    "",
    "🇰🇷 VRChat에서 농인과 청인이 함께 한국수어(**KSL**)를 배우고 소통하는 커뮤니티예요.",
    "🇺🇸 A VRChat community where Deaf and hearing friends learn Korean Sign Language (**KSL**) together.",
    "🇯🇵 VRChatで、ろう者と聴者が一緒に韓国手話(**KSL**)を学び、交流するコミュニティです。",
    "",
    "👋 처음이라면 🌱 씨앗반부터! · New here? Start with 🌱 씨앗반! · 初めての方は🌱씨앗반へ！",
])

# 요일: 입력 표기 → 파이썬 weekday 번호, 번호 → (한, 영, 일) 표기
WEEKDAY_ALIASES = {
    **{name: i for i, name in enumerate(["mon", "tue", "wed", "thu", "fri", "sat", "sun"])},
    **{name: i for i, name in enumerate(["월", "화", "수", "목", "금", "토", "일"])},
}
WEEKDAY_LABELS = [("월", "Mon", "月"), ("화", "Tue", "火"), ("수", "Wed", "水"), ("목", "Thu", "木"),
                  ("금", "Fri", "金"), ("토", "Sat", "土"), ("일", "Sun", "日")]

KST = timezone(timedelta(hours=9), "KST")  # 한국은 서머타임이 없어 고정 오프셋이면 충분합니다


# ── 디스코드 제한 ──────────────────────────────────────────────
# https://discord.com/developers/docs/resources/message#embed-object-embed-limits
MAX_TITLE = 256
MAX_DESCRIPTION = 4096
MAX_FIELDS = 25
MAX_FIELD_NAME = 256
MAX_FIELD_VALUE = 1024
MAX_FOOTER = 2048
MAX_TOTAL_CHARS = 6000  # 한 메시지에 담긴 모든 Embed 글자 수의 합
MAX_EMBEDS = 10

REQUEST_TIMEOUT = 15.0  # 초
MAX_ATTEMPTS = 3        # 429(요청 과다)를 받으면 디스코드가 알려 준 시간만큼 쉬고 다시 보냅니다

WEBHOOK_URL_RE = re.compile(
    r"^https://(?:(?:ptb|canary)\.)?discord(?:app)?\.com/api(?:/v\d+)?/webhooks/\d+/[\w-]+$"
)


# ── Embed 만들기 ──────────────────────────────────────────────
def channel_ref(channel_id: str | None, fallback: str) -> str:
    """채널 ID 가 있으면 클릭 가능한 멘션, 없으면 굵은 글씨 이름."""
    return f"<#{channel_id}>" if channel_id else f"**{fallback}**"


def build_class_field() -> dict:
    lines: list[str] = []
    for lv in LEVELS.values():
        lines += [
            f"{lv.emoji} **{lv.name}** {lv.grade_ko} · {lv.grade_en} · {lv.grade_ja}",
            f"> {lv.topic_ko}",
            f"> {lv.topic_en} · {lv.topic_ja}",
        ]
    return {"name": "🌱 학급 안내 · Class Levels · クラス案内", "value": "\n".join(lines)}


def build_join_field(guide: str) -> dict:
    lines = [
        "**1️⃣ 그룹 가입** · Join the Group · グループ参加",
        "> VRChat 그룹 검색 `한국수어교실` → 가입 요청",
        "> Search `한국수어교실` in VRChat Groups · グループ検索 → 参加リクエスト",
        "**2️⃣ 일정 확인** · Check the Schedule · 日程確認",
        f"> {guide} · 이벤트 탭의 시간은 **내 현지 시간**으로 표시",
        "> Times show in your local time · 現地時間で自動表示",
        "**3️⃣ 수업 입장** · Join the Class · 授業に参加",
        "> 수업 15분 전, 그룹 인스턴스(Group Instance) 입장",
        "> Join the Group Instance 15 min early · 15分前にグループインスタンスへ",
    ]
    return {"name": "🚀 참여 방법 · How to Join · 参加方法", "value": "\n".join(lines)}


def build_rules_field(rules: str) -> dict:
    lines = [
        "🤟 **농문화 존중** · Respect Deaf Culture · ろう文化の尊重",
        "> 농인·학습자 서로 존중, 수어 비하·희화화 금지",
        "> No mocking signs or Deaf people · 手話・ろう者をからかわない",
        "🤖 **AI 태그 필수** · Tag AI Content · AI生成物はタグ必須",
        "> AI 생성물 업로드 시 `🤖` 태그, 무단 도용 금지",
        "> Tag AI-made media with `🤖`, no art theft · 無断転載禁止",
        "🏷️ **수어 이름은 선물** · Name Signs Are Gifts · サインネームは贈り物",
        "> 스스로 짓지 않고, 농인 멘토와의 교류로 받아요",
        "> Given by Deaf mentors, not self-made · ろうの先輩から贈られるもの",
        f"📋 전체 규칙 · Full rules · ルール全文 → {rules}",
    ]
    return {"name": "🛡️ 교실 규칙 · Rules & Etiquette · ルール", "value": "\n".join(lines)}


def next_class_start(weekday: int, hhmm: str, now: datetime) -> datetime:
    """now 이후 처음 돌아오는 해당 요일·시각(KST)."""
    hour, minute = (int(part) for part in hhmm.split(":"))
    local_now = now.astimezone(KST)
    start = (local_now + timedelta(days=(weekday - local_now.weekday()) % 7)).replace(
        hour=hour, minute=minute, second=0, microsecond=0
    )
    if start <= local_now:
        start += timedelta(days=7)
    return start


def build_schedule_field(now: datetime) -> dict | None:
    if not CLASS_SCHEDULE:
        return None
    slots = []
    for level_key, day, hhmm in CLASS_SCHEDULE:
        weekday = WEEKDAY_ALIASES[day.lower()]
        slots.append((next_class_start(weekday, hhmm, now), LEVELS[level_key], weekday, hhmm))
    slots.sort(key=lambda slot: slot[0])

    lines: list[str] = []
    for start, lv, weekday, hhmm in slots:
        ts = int(start.timestamp())
        ko, en, ja = WEEKDAY_LABELS[weekday]
        lines += [
            f"{lv.emoji} **{lv.name}** · 매주 {ko} {en} {ja} {hhmm} KST",
            f"> <t:{ts}:F> · <t:{ts}:R>",
        ]
    lines.append("*🕒 내 현지 시간으로 표시 · Shown in your local time · 現地時間で表示*")
    return {"name": "📅 다음 수업 · Next Classes · 次の授業", "value": "\n".join(lines)}


def build_links_field(guide: str) -> dict:
    lines: list[str] = []
    if VRCHAT_GROUP_URL:
        lines.append(f"🌐 [VRChat 그룹 · Group · グループ]({VRCHAT_GROUP_URL})")
    if NOTION_GUIDE_URL:
        lines.append(f"📘 [이벤트 참여 가이드 · Event Guide (Notion)]({NOTION_GUIDE_URL})")
    if WEB_GUIDE_URL:
        lines.append(f"📖 [웹 가이드 · Web Guide · ウェブガイド]({WEB_GUIDE_URL})")
    if DISCORD_INVITE_URL:
        lines.append(f"💌 친구 초대 · Invite · 招待: {DISCORD_INVITE_URL}")
    lines.append(f"📌 서버 안내 · Server Guide · サーバー案内: {guide}")
    return {"name": "🔗 바로가기 · Quick Links · リンク", "value": "\n".join(lines)}


def build_embeds(*, now: datetime, guide_channel_id: str | None) -> list[dict]:
    guide = channel_ref(guide_channel_id, "#안내")
    rules = channel_ref(RULES_CHANNEL_ID or None, "#규칙")

    fields = [build_class_field(), build_join_field(guide), build_rules_field(rules)]
    schedule = build_schedule_field(now)
    if schedule:
        fields.append(schedule)
    fields.append(build_links_field(guide))

    guide_embed: dict = {
        "title": TITLE,
        "description": DESCRIPTION,
        "color": BRAND_COLOR,
        "fields": [{**field, "inline": False} for field in fields],
        "footer": {"text": FOOTER},
        "timestamp": now.isoformat(),  # 푸터 옆에 '마지막 수정 시각'으로 보입니다
    }
    if WEB_GUIDE_URL:
        guide_embed["url"] = WEB_GUIDE_URL
    if LOGO_URL:
        guide_embed["thumbnail"] = {"url": LOGO_URL}
        guide_embed["footer"]["icon_url"] = LOGO_URL

    # 배너는 이미지만 담은 Embed 를 앞에 하나 더 붙여, 안내문 위쪽 머리 그림처럼 보이게 합니다.
    embeds = [guide_embed]
    if BANNER_URL:
        embeds.insert(0, {"color": BRAND_COLOR, "image": {"url": BANNER_URL}})
    return embeds


def build_payload(*, now: datetime, guide_channel_id: str | None, editing: bool) -> dict:
    payload: dict = {
        "embeds": build_embeds(now=now, guide_channel_id=guide_channel_id),
        "allowed_mentions": {"parse": []},  # 혹시 문구에 멘션이 들어가도 알림은 보내지 않습니다
    }
    if not editing:  # 이름·프로필 사진은 새로 보낼 때만 정할 수 있습니다
        payload["username"] = WEBHOOK_USERNAME
        if WEBHOOK_AVATAR_URL:
            payload["avatar_url"] = WEBHOOK_AVATAR_URL
    return payload


# ── 검사 ─────────────────────────────────────────────────────
def check_settings() -> list[str]:
    problems: list[str] = []
    for label, value in (("GUIDE_CHANNEL_ID", GUIDE_CHANNEL_ID), ("RULES_CHANNEL_ID", RULES_CHANNEL_ID)):
        if value and not value.isdigit():
            problems.append(f"{label} 는 숫자만 적어 주세요: {value!r}")
    for i, slot in enumerate(CLASS_SCHEDULE, 1):
        if len(slot) != 3:
            problems.append(f"CLASS_SCHEDULE {i}번째 줄은 (반, 요일, 'HH:MM') 세 칸이어야 해요: {slot!r}")
            continue
        level_key, day, hhmm = slot
        if level_key not in LEVELS:
            problems.append(f"CLASS_SCHEDULE {i}번째 줄의 반 {level_key!r} → {', '.join(LEVELS)} 중 하나")
        if day.lower() not in WEEKDAY_ALIASES:
            problems.append(f"CLASS_SCHEDULE {i}번째 줄의 요일 {day!r} → mon~sun 또는 월~일")
        if not re.fullmatch(r"([01]\d|2[0-3]):[0-5]\d", hhmm):
            problems.append(f"CLASS_SCHEDULE {i}번째 줄의 시각 {hhmm!r} → 'HH:MM' (예: '21:00')")
    return problems


def embed_char_count(embed: dict) -> int:
    fields = embed.get("fields", [])
    return (
        len(embed.get("title", ""))
        + len(embed.get("description", ""))
        + sum(len(f["name"]) + len(f["value"]) for f in fields)
        + len(embed.get("footer", {}).get("text", ""))
        + len(embed.get("author", {}).get("name", ""))
    )


def check_limits(embeds: list[dict]) -> list[str]:
    """디스코드가 거절할 길이를 보내기 전에 미리 찾아냅니다."""
    problems: list[str] = []
    if len(embeds) > MAX_EMBEDS:
        problems.append(f"Embed 개수 {len(embeds)} > {MAX_EMBEDS}")
    for n, embed in enumerate(embeds, 1):
        checks = [
            ("title", len(embed.get("title", "")), MAX_TITLE),
            ("description", len(embed.get("description", "")), MAX_DESCRIPTION),
            ("fields 개수", len(embed.get("fields", [])), MAX_FIELDS),
            ("footer", len(embed.get("footer", {}).get("text", "")), MAX_FOOTER),
        ]
        for field in embed.get("fields", []):
            checks.append((f"'{field['name']}' 이름", len(field["name"]), MAX_FIELD_NAME))
            checks.append((f"'{field['name']}' 내용", len(field["value"]), MAX_FIELD_VALUE))
        problems += [f"Embed {n} {label}: {size}자 > {limit}자" for label, size, limit in checks if size > limit]
    total = sum(embed_char_count(embed) for embed in embeds)
    if total > MAX_TOTAL_CHARS:
        problems.append(f"전체 글자 수 {total}자 > {MAX_TOTAL_CHARS}자")
    return problems


# ── 웹후크 전송 ───────────────────────────────────────────────
class WebhookError(RuntimeError):
    pass


def split_webhook_url(url: str) -> tuple[str, dict[str, str]]:
    """웹후크 주소를 '기본 주소'와 쿼리(thread_id 등)로 나눕니다."""
    parts = urlsplit(url.strip())
    base = urlunsplit((parts.scheme, parts.netloc, parts.path.rstrip("/"), "", ""))
    if not WEBHOOK_URL_RE.match(base):
        raise WebhookError(
            "DISCORD_WEBHOOK_URL 이 디스코드 웹후크 주소가 아니에요. "
            "(https://discord.com/api/webhooks/숫자/토큰 형식)"
        )
    return base, dict(parse_qsl(parts.query))


def discord_request(method: str, url: str, *, params: dict | None = None, payload: dict | None = None) -> dict:
    """디스코드 API 호출. 오류 메시지에는 토큰이 든 주소를 절대 싣지 않습니다."""
    for _ in range(MAX_ATTEMPTS):
        try:
            resp = requests.request(method, url, params=params, json=payload, timeout=REQUEST_TIMEOUT)
        except requests.RequestException as e:
            raise WebhookError(f"디스코드에 연결하지 못했어요: {type(e).__name__}") from None

        if resp.status_code == 429:
            try:
                wait = float(resp.json().get("retry_after", 1.0))
            except ValueError:  # Cloudflare 가 막으면 JSON 대신 HTML 이 옵니다
                wait = float(resp.headers.get("Retry-After", 5))
            print(f"⏳ 요청이 많아 {wait:.1f}초 쉬었다 다시 보낼게요.", file=sys.stderr)
            time.sleep(wait)
            continue

        if resp.status_code in (401, 404):
            raise WebhookError(f"웹후크(또는 메시지)를 찾을 수 없어요 ({resp.status_code}). "
                               "주소가 바뀌었거나, 삭제됐거나, 다른 웹후크가 보낸 메시지인지 확인해 주세요.")
        if not resp.ok:
            raise WebhookError(f"디스코드가 거절했어요 ({resp.status_code}): {resp.text[:1000]}")
        return resp.json() if resp.content else {}

    raise WebhookError(f"{MAX_ATTEMPTS}번 시도했지만 요청 과다(429)가 풀리지 않았어요. 잠시 뒤 다시 실행해 주세요.")


def fetch_webhook_channel_id(base_url: str) -> str | None:
    """웹후크가 걸린 채널 ID. (토큰이 든 주소라면 봇 없이도 조회됩니다)"""
    try:
        return discord_request("GET", base_url).get("channel_id")
    except WebhookError as e:
        print(f"⚠️ 안내 채널을 자동으로 찾지 못해 글자로 적을게요: {e}", file=sys.stderr)
        return None


# ── 실행 ─────────────────────────────────────────────────────
def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="VRChat 한국수어교실 #안내 채널 웰컴 Embed 를 디스코드 웹후크로 보냅니다.",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true",
                      help="보내지 않고 웹후크에 실릴 JSON 만 출력합니다. (discohook.org 에 붙여 넣어 미리보기)")
    mode.add_argument("--edit", metavar="MESSAGE_ID",
                      help="같은 웹후크로 보냈던 메시지를 새 내용으로 덮어씁니다.")
    args = parser.parse_args(argv)
    if args.edit is not None and not args.edit.isdigit():
        parser.error("--edit 에는 숫자로 된 메시지 ID 를 넣어 주세요. (메시지 우클릭 → 'ID 복사')")
    return args


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):  # Windows 에서 파이프로 받을 때도 한글·이모지가 깨지지 않게
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")

    args = parse_args(argv)
    if problems := check_settings():
        print("❌ 설정을 확인해 주세요.\n  - " + "\n  - ".join(problems), file=sys.stderr)
        return 1

    now = datetime.now(timezone.utc).replace(microsecond=0)

    if args.dry_run:
        payload = build_payload(now=now, guide_channel_id=GUIDE_CHANNEL_ID or None, editing=False)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        problems = check_limits(payload["embeds"])
        total = sum(embed_char_count(embed) for embed in payload["embeds"])
        print(f"\n📏 전체 {total}/{MAX_TOTAL_CHARS}자 · Embed {len(payload['embeds'])}개", file=sys.stderr)
        if not GUIDE_CHANNEL_ID:
            print("ℹ️ 미리보기에서는 #안내 멘션이 글자로 보여요. 실제 전송 때는 웹후크 채널로 자동 연결돼요.",
                  file=sys.stderr)
        for problem in problems:
            print(f"❌ {problem}", file=sys.stderr)
        return 1 if problems else 0

    if load_dotenv is not None:
        load_dotenv(BASE_DIR / ".env")
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL", "").strip()
    if not webhook_url:
        print("❌ DISCORD_WEBHOOK_URL 이 비어 있어요. 환경 변수나 .env 에 웹후크 주소를 넣어 주세요.",
              file=sys.stderr)
        return 1

    try:
        base_url, params = split_webhook_url(webhook_url)
        guide_channel_id = GUIDE_CHANNEL_ID or fetch_webhook_channel_id(base_url)
        payload = build_payload(now=now, guide_channel_id=guide_channel_id, editing=bool(args.edit))
        if problems := check_limits(payload["embeds"]):
            print("❌ 디스코드 글자 수 제한을 넘었어요.\n  - " + "\n  - ".join(problems), file=sys.stderr)
            return 1

        if args.edit:
            message = discord_request("PATCH", f"{base_url}/messages/{args.edit}", params=params, payload=payload)
            print(f"✅ 메시지 {message.get('id', args.edit)} 를 새 내용으로 고쳤어요.")
        else:
            message = discord_request("POST", base_url, params={**params, "wait": "true"}, payload=payload)
            message_id = message.get("id", "?")
            print(f"✅ 보냈어요! 메시지 ID: {message_id}")
            print(f"   다음부터는 python send_welcome_embed.py --edit {message_id} 로 같은 자리를 고칠 수 있어요.")
    except WebhookError as e:
        print(f"❌ {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
