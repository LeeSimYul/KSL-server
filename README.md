# KSL-server

Welcome! Learn Korean Sign Language (KSL) in VRChat with global friends.

**VRChat 한국수어교실** 디스코드 서버의 공식 안내문과 가이드라인을 관리하는 저장소입니다.
`#안내` 채널에 올라가는 웰컴 공지(디스코드 Embed)와, 같은 내용을 노션 · GitHub Pages 로 공유하는 웹 가이드를 한곳에서 고칩니다.

- 💬 디스코드: [discord.gg/tVyvq5qZgn](https://discord.gg/tVyvq5qZgn)
- 🌐 VRChat 그룹: [vrc.group/KSL.8324](https://vrc.group/KSL.8324)
- 📖 웹 가이드: [docs/welcome-guide.md](./docs/welcome-guide.md)

---

## 📁 프로젝트 구조 (Directory Structure)

```text
KSL-server/
├── send_welcome_embed.py   # #안내 채널 웰컴 Embed 웹후크 전송 · 수정 스크립트
├── docs/
│   └── welcome-guide.md    # 노션 · GitHub Pages 용 3개 국어(한/영/일) 웹 가이드
├── .env.example            # 환경 변수 설정 샘플 (.env 로 복사해서 사용)
├── requirements.txt        # 파이썬 의존성 (requests, python-dotenv)
└── README.md
```

---

## 🚀 Quick Start

### 1. 설치

Python 3.9 이상이 필요합니다.

```bash
pip install -r requirements.txt
```

### 2. `.env` 작성

```bash
cp .env.example .env        # Windows: copy .env.example .env
```

`.env` 를 열어 `DISCORD_WEBHOOK_URL=` 뒤에 `#안내` 채널의 웹후크 주소를 붙여 넣습니다.
(디스코드 `#안내` 채널 → 채널 편집 → 연동 → 웹후크 → 새 웹후크 → **웹후크 URL 복사**)

> ⚠️ 웹후크 주소만 있으면 누구나 그 채널에 글을 쓸 수 있습니다. `.env` 는 `.gitignore` 에 들어 있으니 절대 커밋하지 마세요.

### 3. 미리보기 (선택)

보내지 않고 웹후크에 실릴 JSON 만 출력합니다. 출력을 [discohook.org](https://discohook.org) 의 JSON 편집기에 붙여 넣으면 실제 모습을 미리 볼 수 있어요.

```bash
python send_welcome_embed.py --dry-run
```

### 4. 공지 보내기

```bash
python send_welcome_embed.py
```

전송이 끝나면 **메시지 ID** 를 알려 줍니다. 메시지는 `#안내` 에 고정해 두세요.

### 5. 공지 수정하기

문구를 고친 뒤 같은 메시지를 덮어씁니다. 공지를 지우고 다시 올릴 필요가 없어요.

```bash
python send_welcome_embed.py --edit <MESSAGE_ID>
```

> 메시지 ID 는 4번에서 출력된 값이나, 디스코드 개발자 모드에서 메시지 우클릭 → **ID 복사**로 얻습니다.
> 같은 웹후크로 보낸 메시지만 고칠 수 있습니다.

스크립트는 보내기 전에 디스코드 글자 수 제한(필드 1024자, 전체 6000자 등)을 스스로 검사하고, 넘으면 어디가 넘었는지 알려 주고 멈춥니다.

---

## 🧩 Embed 구성

한 메시지에 Embed 두 개를 이어 보냅니다. (한 Embed 안에서는 큰 이미지가 항상 맨 아래에 붙기 때문에, 배너를 맨 위에 두려고 따로 나눴습니다)

| 순서 | Embed | 내용 |
| :---: | :--- | :--- |
| 1 | 🖼️ 상단 배너 | 공식 타이틀 배너 이미지만 표시 |
| 2 | 📝 본문 | 제목 · 환영 문구 · 오른쪽 위 로고 · 아래 6개 칸 · 푸터(마지막 수정 시각) |

본문 칸 순서 (모두 `inline=False`):

1. `📝 학급 안내 (Class Levels)`: 씨앗반 · 별빛반 · 달빛반
2. `🚀 3분 만에 수업 참여하기 (Quick Start)`: 그룹 가입 → 이벤트 탭 확인 → 그룹 인스턴스 입장
3. `📅 다음 수업 (Next Classes)`: 디스코드 타임스탬프로 읽는 사람의 현지 시각 표시 (`CLASS_SCHEDULE` 이 비어 있으면 생략)
4. `🛡️ 핵심 교실 에티켓 (Core Rules)`: 농문화 존중 · AI 미디어 규칙 · 수어 이름
5. `📜 상세 규칙 (Full Rules)`: `#규칙` 채널 멘션
6. `⬇️ 바로가기 모음 (Quick Links)`: VRChat 그룹 · 노션 가이드 3종

---

## ⚙️ 설정

모든 설정은 `send_welcome_embed.py` 맨 위에 모여 있습니다.
`RULES_CHANNEL_ID` · `VRCHAT_GROUP_URL` 은 `.env` 에 같은 이름으로 넣으면 그 값이 먼저 쓰이고, 없으면 아래 기본값을 씁니다.

| 설정 | 기본값 | 설명 |
| :--- | :--- | :--- |
| `BRAND_COLOR` | `0x4A90E2` | 두 Embed 왼쪽 띠 색 |
| `RULES_CHANNEL_ID` | `1414463866863226983` | `📜 상세 규칙` 칸에 멘션할 `#규칙` 채널 ID. 빈 문자열이면 글자로만 적습니다. |
| `VRCHAT_GROUP_URL` | `https://vrc.group/KSL.8324` | VRChat 그룹 공유 링크 |
| `NOTION_SERVER_GUIDE_URL` | 공식 안내 가이드 노션 | 디스코드 카테고리 · 채널 안내 |
| `NOTION_EVENT_GUIDE_URL` | 이벤트 참여 방법 노션 | PC로 수업에 들어오는 방법 |
| `NOTION_BOT_GUIDE_URL` | 이미숫 봇 안내 노션 | 조교 봇 명령어 안내 |
| `WEB_GUIDE_URL` | 이 저장소의 `docs/welcome-guide.md` | 본문 제목을 누르면 열리는 링크 |
| `BANNER_URL` | `공식 타이틀 배너 together.png` | 상단 배너 Embed 이미지. 비우면 배너 없이 본문만 보냅니다. |
| `THUMBNAIL_URL` · `ICON_URL` | `로고 ver.2 together.png` | 본문 오른쪽 위 로고 · 웹후크 프로필과 푸터 아이콘 |
| `CLASS_SCHEDULE` | 별빛반 매주 일 22:00 | 정기 수업 시간표. 아래 참고. |

링크 설정을 빈 문자열로 두면 그 줄은 바로가기에서 빠집니다.

### 📅 수업 시간표 & 동적 타임스탬프

`CLASS_SCHEDULE` 에 **한국 시간(KST)** 기준으로 `("반", "요일", "HH:MM")` 을 적습니다.

```python
CLASS_SCHEDULE = [
    ("star", "sun", "22:00"),  # 별빛반 매주 일요일 22:00 KST
    ("seed", "토", "21:00"),   # 반: seed · star · moon / 요일: mon~sun 또는 월~일
]
```

시각은 디스코드 타임스탬프(`<t:…:F>`)로 들어가 읽는 사람의 나라 시간과 언어로 자동으로 바뀌어 보입니다.
다만 "보낸 시점 기준 다음 수업"이 찍히므로, 매주 한 번 `--edit` 로 다시 돌려 주면 늘 최신 날짜가 유지됩니다. (Windows 작업 스케줄러나 `cron` 에 걸어 두면 편해요)

---

## 🌐 웹 가이드 게시

[`docs/welcome-guide.md`](./docs/welcome-guide.md) 는 Embed 와 같은 내용을 3개 국어로 조금 더 자세히 풀어 쓴 문서입니다.

- **노션**: GitHub 에서 파일 → **Raw** → 전체 복사 → 노션 페이지 맨 위에 붙여 넣기. 제목 · 표 · 인용 · 이미지가 노션 블록으로 바뀝니다.
- **GitHub Pages**: 저장소 **Settings → Pages → Deploy from a branch → `main` / `/docs`** 로 켜면 `https://leesimyul.github.io/KSL-server/welcome-guide.html` 에서 열립니다.

> Embed 문구와 웹 가이드는 같은 내용을 담고 있으니, 한쪽을 고치면 다른 쪽도 함께 맞춰 주세요.

---

## 🎨 브랜드 자산

로고와 배너는 [LeeSimYul/Kidentity](https://github.com/LeeSimYul/Kidentity) 의 공식 원본을 주소로 불러와 씁니다. (이 저장소에 파일을 복사해 두지 않습니다)
모든 브랜드 자산은 **CC BY-NC-ND 4.0** 및 총괄 대표의 사전 서면 승인 규정을 따릅니다.
