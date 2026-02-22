import os
import asyncio
import logging
import json

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# LangChain & Google Gemini Imports
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate

# Load .env file (if exists) for GOOGLE_API_KEY etc.
load_dotenv()

logger = logging.getLogger(__name__)

app = FastAPI(title="Bakery Ran Multi-Agent System")

# Enable CORS for the React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if not os.environ.get("GOOGLE_API_KEY"):
    logger.warning("GOOGLE_API_KEY environment variable not set. API calls will fail.")

# ==============================
# Models
# ==============================
class GenerateRequest(BaseModel):
    daily_note: str = Field(..., min_length=1, max_length=2000, description="오늘의 메모")

class GenerateResponse(BaseModel):
    threads_post: str
    instagram_post: str
    danggeun_post: str
    trends_used: list[str]

class CalendarRequest(BaseModel):
    weekly_note: str = Field(..., min_length=1, max_length=2000, description="이번 주 특이사항")

class CalendarDayItem(BaseModel):
    day: str
    threads: str
    instagram: str
    danggeun: str

class CalendarResponse(BaseModel):
    calendar: list[CalendarDayItem]
    trends_used: list[str]

# ==============================
# Persona & Prompts (based on prompts.md — @bakery_ran_ real post analysis)
# ==============================

# 공통 페르소나 (prompts.md Part 0 기반)
BASE_PERSONA = """
너는 제주도 도평동에서 '베이커리란'이라는 빵집을 혼자 운영하는 1인 사장이야.
실제 @bakery_ran_ 계정의 게시물 말투를 분석해서 만든 페르소나야. 이 규칙을 절대 어기지 마.

[화법 규칙]
- 반말 사용 (친구한테 말하듯이, 카톡 하는 느낌). 절대 존댓말(~입니다, ~합니다, ~드립니다) 쓰지 마.
- 어미: ~했어, ~이얌, ~해!, ~쥬?, ~거든, ~인 거야, ~같애, ~더라
- 감정 표현 풍부하게. 이모지 필수로 2~3개 이상: ❣️, 🥲, 🫶🏻, 🫢
- 시그니처 단어: "영롱" (빵이 예쁘고 완성도 높을 때), "겟" (사 가라는 뜻), "순삭" (빨리 팔렸을 때)
- 글 마지막에 항상: 📍 도평길31, 베이커리란

[성격]
- 빵에 진심인 열정적 사장님
- 솔직하고 꾸밈없는 성격 (있는 그대로 표현)
- 강아지 키우는 동물 러버
- 제주도 날씨, 일상을 자연스럽게 녹여냄

[포스팅 전 최종 체크리스트 — 이 규칙을 반드시 지킬 것]
✅ 반말 쓰고 있어? (~입니다 같은 존댓말 없어?)
✅ 이모지 2~3개 이상 들어갔어? (❣️🥲🫶🏻 필수!)
✅ "영롱" 또는 "순삭" 자연스럽게 썼어? (어울리면)
✅ 주소 넣었어? (📍 도평길31, 베이커리란)
✅ 읽어보면 친구한테 카톡하는 느낌이야?
"""

THREADS_PROMPT_TEMPLATE = PromptTemplate.from_template(
    BASE_PERSONA + """
---
위의 페르소나를 완벽하게 유지하면서 스레드(Threads) 포스팅을 작성해줘.
스레드는 짧고 감성적인 일상 공유 플랫폼이야. 너무 홍보글처럼 쓰지 마.

[오늘의 메모 (사장님 코멘트)]
{daily_note}

[오늘의 트렌드 키워드 (참고용 — 자연스럽게 어울리면 슬쩍 넣기, 억지로 넣지 말 것)]
{trends}

[작성 지침]
- 3~5문장으로 짧게
- 빵 만드는 과정의 감성, 오늘의 날씨/기분, 일상 에피소드 중 하나를 중심으로
- 판매용 멘트보다는 "오늘 이런 일이 있었어" 하는 TMI 느낌
- 품절됐다면 "순삭" 사용, 예쁘게 나왔다면 "영롱" 사용
- 마지막에 매장 주소 넣기
"""
)

INSTA_PROMPT_TEMPLATE = PromptTemplate.from_template(
    BASE_PERSONA + """
---
위의 페르소나를 완벽하게 유지하면서 인스타그램(Instagram) 캡션을 작성해줘.
인스타는 빵 사진과 함께 올라가는 글이야. 비주얼 묘사에 집중해.

[오늘의 메모 (사장님 코멘트)]
{daily_note}

[오늘의 트렌드 키워드 (참고용)]
{trends}

[작성 지침]
- 맛과 비주얼 묘사에 집중 (색감, 식감, 향기 등 감각적으로 표현)
- "영롱" 키워드 자연스럽게 사용
- 줄바꿈 넉넉히 활용해서 가독성 높이기
- 오늘의 라인업(빵 목록)이 있으면 이모지와 함께 한 줄씩 소개
- 트렌드가 어울리면 해시태그나 본문에 유쾌하게 살짝 반영
- 마지막에 반드시:
  🏡 도평길31, 베이커리란
  #제주빵집 #제주베이커리 #도평빵집 #빵지순례 #제주카페 #소금빵
"""
)

DANGGEUN_PROMPT_TEMPLATE = PromptTemplate.from_template(
    BASE_PERSONA + """
---
위의 페르소나를 완벽하게 유지하면서 당근마켓(Danggeun) 동네생활 / 비즈프로필 포스팅을 작성해줘.
당근은 도평동 동네 주민들이 보는 플랫폼이야. 가까운 이웃한테 말 거는 느낌으로.

[오늘의 메모 (사장님 코멘트)]
{daily_note}

[오늘의 트렌드 키워드 (참고용)]
{trends}

[작성 지침]
- "도평동 천사님들~" 또는 "제주 사람들~" 같이 동네 주민한테 친근하게 말 거는 스타일로 시작
- 오늘 갓 구운 빵, 당일 방문을 유도하는 멘트 포함
- 관광객보다 동네 단골 위주로 공략하는 느낌
- 영업시간 or 오늘만 특별한 것이 있으면 언급
- 마지막에 매장 주소 넣기
"""
)

CALENDAR_PROMPT_TEMPLATE = PromptTemplate.from_template(
    BASE_PERSONA + """
---
위의 페르소나를 완벽하게 유지하면서 이번 주(월~일) SNS 콘텐츠 캘린더를 만들어줘.

[이번 주 특이사항]
{weekly_note}

[이번 주 트렌드 키워드 (참고용)]
{trends}

각 요일(월요일~일요일)마다 3개 채널의 포스팅 핵심 메시지를 한 줄씩 만들어줘.
- 스레드: 짧고 감성적인 일상 한 줄
- 인스타: 비주얼 중심 한 줄 (어떤 빵을 강조할지)
- 당근: 동네 주민 대상 한 줄

트렌드가 자연스럽게 어울리는 요일엔 살짝 녹여줘.

반드시 아래 JSON 형식으로만 출력해. 다른 텍스트 없이 순수 JSON만 출력해:
[
  {{"day": "월요일", "threads": "스레드 한줄 메시지", "instagram": "인스타 한줄 메시지", "danggeun": "당근 한줄 메시지"}},
  {{"day": "화요일", "threads": "...", "instagram": "...", "danggeun": "..."}},
  {{"day": "수요일", "threads": "...", "instagram": "...", "danggeun": "..."}},
  {{"day": "목요일", "threads": "...", "instagram": "...", "danggeun": "..."}},
  {{"day": "금요일", "threads": "...", "instagram": "...", "danggeun": "..."}},
  {{"day": "토요일", "threads": "...", "instagram": "...", "danggeun": "..."}},
  {{"day": "일요일", "threads": "...", "instagram": "...", "danggeun": "..."}}
]
"""
)


# ==============================
# Trend Analysis (Enhanced with Jeju/Dessert Filtering)
# ==============================

# 제주도 & 디저트/베이커리 관련 키워드 사전
JEJU_DESSERT_KEYWORDS = [
    # 제주 관련
    "제주", "제주도", "제주시", "서귀포", "한라산", "우도", "성산", "협재", "월정리",
    "도평", "애월", "중문", "탐라", "올레길", "제주여행", "제주관광",
    # 디저트/빵 관련
    "빵", "베이커리", "디저트", "카페", "케이크", "크루아상", "소금빵",
    "마들렌", "쿠키", "타르트", "파이", "마카롱", "스콘", "바게트",
    "초콜릿", "말차", "딸기", "흑임자", "앙버터", "식빵", "브런치",
    "맛집", "카페투어", "빵지순례", "빵스타그램", "디저트맛집",
    # 음식/트렌드 관련
    "맛집", "푸드", "요리", "레시피", "음식", "먹방", "쿡방",
    "흑백요리사", "쿠킹", "달달", "달콤", "수제",
]

def get_enhanced_trends() -> tuple[list[str], list[str]]:
    """
    Fetches Google Trends and filters them for Jeju/dessert relevance.
    Returns: (filtered_trends, all_trends)
    """
    all_trends: list[str] = []
    try:
        from pytrends.request import TrendReq
        pytrends = TrendReq(hl='ko-KR', tz=540)
        trending_df = pytrends.trending_searches(pn='south_korea')
        all_trends = trending_df[0].head(15).tolist()
    except Exception as e:
        logger.warning(f"Failed to fetch Google Trends: {e}")
        all_trends = ["흑백요리사", "제주도 여행", "봄 날씨", "카페 투어", "디저트 맛집"]

    # Filter: prioritize Jeju/dessert-related trends
    filtered = []
    general = []
    for trend in all_trends:
        trend_lower = trend.lower()
        if any(kw in trend_lower for kw in JEJU_DESSERT_KEYWORDS):
            filtered.append(trend)
        else:
            general.append(trend)

    # Return filtered first, then fill with general up to 5 total
    result = filtered[:3]
    remaining_slots = max(0, 3 - len(result))
    result.extend(general[:remaining_slots])

    return result, all_trends


# ==============================
# LLM Helpers
# ==============================
async def generate_post(llm: ChatGoogleGenerativeAI, prompt_template: PromptTemplate, inputs: dict) -> str:
    chain = prompt_template | llm
    response = await chain.ainvoke(inputs)
    return response.content


def _ensure_api_key():
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Google API Key missing. Please set GOOGLE_API_KEY environment variable.")
    return api_key


# ==============================
# API Endpoints
# ==============================

@app.post("/api/generate", response_model=GenerateResponse)
async def generate_sns_posts(request: GenerateRequest):
    _ensure_api_key()

    try:
        llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.7)

        # 1. Enhanced Trend Analysis
        filtered_trends, _ = get_enhanced_trends()
        trends_str = ", ".join(filtered_trends)

        inputs = {
            "daily_note": request.daily_note,
            "trends": trends_str
        }

        # 2. Generate all 3 channels concurrently
        results = await asyncio.gather(
            generate_post(llm, THREADS_PROMPT_TEMPLATE, inputs),
            generate_post(llm, INSTA_PROMPT_TEMPLATE, inputs),
            generate_post(llm, DANGGEUN_PROMPT_TEMPLATE, inputs),
        )

        return GenerateResponse(
            threads_post=results[0],
            instagram_post=results[1],
            danggeun_post=results[2],
            trends_used=filtered_trends,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/calendar", response_model=CalendarResponse)
async def generate_weekly_calendar(request: CalendarRequest):
    _ensure_api_key()

    try:
        llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.7)

        filtered_trends, _ = get_enhanced_trends()
        trends_str = ", ".join(filtered_trends)

        inputs = {
            "weekly_note": request.weekly_note,
            "trends": trends_str,
        }

        chain = CALENDAR_PROMPT_TEMPLATE | llm
        response = await chain.ainvoke(inputs)
        raw_text = response.content.strip()

        # Parse JSON from the LLM response (strip markdown code fences if present)
        json_str = raw_text
        if json_str.startswith("```"):
            json_str = json_str.split("\n", 1)[1] if "\n" in json_str else json_str[3:]
        if json_str.endswith("```"):
            json_str = json_str[:-3]
        json_str = json_str.strip()

        calendar_data = json.loads(json_str)

        calendar_items = []
        for item in calendar_data:
            calendar_items.append(CalendarDayItem(
                day=item.get("day", ""),
                threads=item.get("threads", ""),
                instagram=item.get("instagram", ""),
                danggeun=item.get("danggeun", ""),
            ))

        return CalendarResponse(calendar=calendar_items, trends_used=filtered_trends)

    except json.JSONDecodeError as e:
        logger.error(f"Calendar JSON parse error: {e}, raw: {raw_text[:200]}")
        raise HTTPException(status_code=500, detail="캘린더 데이터 파싱 오류. 다시 시도해주세요.")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Calendar generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
def health_check():
    return {"status": "ok"}
