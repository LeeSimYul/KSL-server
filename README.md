# KSL-server
Welcome! Learn Korean Sign Language (KSL) in VRChat with global friends.

VRChat 한국수어교실 디스코드 서버의 `#안내` 채널을 꾸리는 도구와 웹 안내 문서입니다.

| 파일 | 하는 일 |
| :--- | :--- |
| [`send_welcome_embed.py`](./send_welcome_embed.py) | 씨앗반 · 별빛반 · 달빛반 학급 안내, 3단계 참여 방법, 핵심 규칙을 한/영/일로 요약한 **웰컴 Embed** 를 웹후크로 보내고, 보낸 메시지를 같은 자리에서 고칩니다. |
| [`docs/welcome-guide.md`](./docs/welcome-guide.md) | 같은 내용을 조금 더 자세히 풀어 쓴 **웹 가이드**. 노션이나 GitHub Pages 에 그대로 붙여 넣어 외부에 공유합니다. |

## 🚀 웰컴 Embed 보내기

1. **설치** (Python 3.9+)
   ```bash
   pip install -r requirements.txt
   ```
2. **웹후크 만들기**: 디스코드 `#안내` 채널 → 채널 편집 → 연동 → 웹후크 → 새 웹후크 → **웹후크 URL 복사**
3. **웹후크 주소 넣기**: `.env.example` 을 `.env` 로 복사하고 `DISCORD_WEBHOOK_URL=` 뒤에 붙여 넣습니다.
   > ⚠️ 웹후크 주소는 누구나 그 채널에 글을 쓸 수 있게 하는 비밀번호입니다. `.env` 는 `.gitignore` 에 들어 있으니 커밋하지 마세요.
4. **미리보기** — 보내지 않고 JSON 만 출력합니다. 출력된 JSON 을 [discohook.org](https://discohook.org) 의 JSON 편집기에 붙여 넣으면 실제 모습을 볼 수 있어요.
   ```bash
   python send_welcome_embed.py --dry-run
   ```
5. **전송** — 끝나면 메시지 ID 를 알려 줍니다. 메시지를 `#안내` 에 고정해 두세요.
   ```bash
   python send_welcome_embed.py
   ```
6. **수정** — 문구를 고친 뒤 같은 메시지를 덮어씁니다. (공지를 지우고 다시 올릴 필요가 없어요)
   ```bash
   python send_welcome_embed.py --edit 메시지ID
   ```

보내기 전에 디스코드 글자 수 제한(필드 1024자, 전체 6000자 등)을 스스로 검사하고, 넘으면 어디가 넘었는지 알려 주고 멈춥니다.

## ⚙️ 설정 (`send_welcome_embed.py` 맨 위)

| 설정 | 기본값 | 설명 |
| :--- | :--- | :--- |
| `BRAND_COLOR` | `0x4A90E2` | Embed 왼쪽 띠 색 |
| `GUIDE_CHANNEL_ID` | (비움) | `#안내` 채널 ID. 비워 두면 웹후크가 걸린 채널을 자동으로 멘션합니다. |
| `RULES_CHANNEL_ID` | (비움) | `#규칙` 채널 ID. 비워 두면 `#규칙` 을 글자로만 적습니다. |
| `VRCHAT_GROUP_URL` | (비움) | VRChat 그룹 공유 링크. **채우면 바로가기에 그룹 링크가 추가됩니다.** |
| `NOTION_GUIDE_URL` | 이벤트 참여 방법 노션 | 비우면 링크를 뺍니다. |
| `WEB_GUIDE_URL` | 이 저장소의 `docs/welcome-guide.md` | 제목 링크 겸 바로가기. `main` 에 합쳐져야 열립니다. |
| `DISCORD_INVITE_URL` | `discord.gg/tVyvq5qZgn` | 친구 초대 링크 |
| `LOGO_URL` · `BANNER_URL` | [Kidentity](https://github.com/LeeSimYul/Kidentity) 공식 로고 · 배너 | 빈 문자열이면 생략합니다. |
| `CLASS_SCHEDULE` | (비움) | 정기 수업 시간표. 아래 참고. |

> 채널 ID 는 디스코드 **설정 → 고급 → 개발자 모드**를 켠 뒤, 채널을 우클릭 → **ID 복사**로 얻습니다.

### 📅 수업 시간표 & 동적 타임스탬프

`CLASS_SCHEDULE` 에 **한국 시간(KST)** 기준으로 적으면 Embed 에 `📅 다음 수업` 칸이 생깁니다.

```python
CLASS_SCHEDULE = [
    ("seed", "sat", "21:00"),  # 씨앗반 매주 토요일 21:00 KST
    ("moon", "수", "22:00"),   # 요일은 mon~sun 또는 월~일
]
```

시간은 디스코드 타임스탬프(`<t:…:F>` · `<t:…:R>`)로 들어가서, 읽는 사람의 나라 시간과 언어로 자동으로 바뀌어 보입니다. 다만 "보낸 시점 기준 다음 수업"이 찍히므로, 매주 한 번 `--edit` 로 다시 돌려 주면 늘 최신 날짜가 유지됩니다. (Windows 작업 스케줄러나 `cron` 에 걸어 두면 편해요)

## 🌐 웹 가이드 게시

- **노션**: GitHub 에서 [`docs/welcome-guide.md`](./docs/welcome-guide.md) → **Raw** → 전체 복사 → 노션 페이지 맨 위에 붙여 넣기. 제목 · 표 · 인용 · 이미지가 노션 블록으로 바뀝니다.
- **GitHub Pages**: 저장소 **Settings → Pages → Deploy from a branch → `main` / `/docs`** 로 켜면 `https://leesimyul.github.io/KSL-server/welcome-guide.html` 에서 열립니다.

Embed 문구와 웹 가이드는 같은 내용을 담고 있으니, 한쪽을 고치면 다른 쪽도 함께 맞춰 주세요.

## 🎨 브랜드 자산

로고와 배너는 [LeeSimYul/Kidentity](https://github.com/LeeSimYul/Kidentity) 의 공식 원본을 주소로 불러와 씁니다. (파일을 복사해 두지 않습니다)
모든 브랜드 자산은 **CC BY-NC-ND 4.0** 및 총괄 대표의 사전 서면 승인 규정을 따릅니다.
