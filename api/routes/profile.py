"""POST /api/profile — one chat turn of the "tell us about yourself" conversation.

The server keeps NOTHING between requests (US-203): the browser sends the profile
it has so far with every message, and gets the updated profile back.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field

from core.languages import ascii_digits
from core.privacy import redact
from core.profile import MAX_FOLLOW_UP_ROUNDS, Country, Profile, missing_fields
from core.profile_agent import FollowUp, Language, detect_language, extract_profile, follow_up_question

router = APIRouter(prefix="/api", tags=["profile"])

# Fields answered by picking an option (they get quick-reply buttons)
CHOICE_FIELDS = {"gender", "caste_category", "occupation", "has_children", "has_disability"}

PRIVACY_NOTE = {
    "hinglish": "Aapka number hata diya gaya hai. Haq ko Aadhaar, PAN ya bank details ki zaroorat nahi hai.",
    "english": "We removed that number. Haq never needs ID numbers (Aadhaar, PAN, National Insurance) or bank details.",
    "hindi": "आपका नंबर हटा दिया गया है। Haq को आधार, PAN या बैंक विवरण की ज़रूरत नहीं है।",
    "marathi": "तुमचा नंबर काढून टाकला आहे. Haq ला आधार, PAN किंवा बँक तपशीलांची गरज नाही.",
    "bengali": "আপনার নম্বরটি সরিয়ে দেওয়া হয়েছে। Haq-এর আধার, PAN বা ব্যাংকের তথ্যের দরকার নেই।",
}


# When a message tells us nothing ("sdfsdf", "hello", "-20"), say so instead of moving on
NOT_UNDERSTOOD = {
    "hinglish": "Lagta hai message galti se type ho gaya 😊 Apne baare mein bataiye — jaise umar, kya karte hain, "
                "ghar ki income, aur kis cheez mein madad chahiye.",
    "english": "Looks like that message was typed by mistake 😊 Tell me about yourself — for example your age, "
               "what you do, your income, and what you need help with.",
    "hindi": "लगता है संदेश ग़लती से टाइप हो गया 😊 अपने बारे में बताइए — जैसे उम्र, आप क्या करते हैं, "
             "घर की आमदनी, और किस चीज़ में मदद चाहिए।",
    "marathi": "संदेश चुकून टाइप झाला असे दिसते 😊 तुमच्याबद्दल सांगा — जसे वय, तुम्ही काय करता, "
               "घरचे उत्पन्न, आणि कशासाठी मदत हवी आहे.",
    "bengali": "মনে হচ্ছে বার্তাটি ভুল করে টাইপ হয়েছে 😊 নিজের সম্পর্কে বলুন — যেমন বয়স, কী কাজ করেন, "
               "পরিবারের আয়, আর কোন বিষয়ে সাহায্য চান।",
}
SORRY = {
    "hinglish": "Maaf kijiye, ye samajh nahi aaya 😊",
    "english": "Sorry, I didn't understand that 😊",
    "hindi": "माफ़ कीजिए, यह समझ नहीं आया 😊",
    "marathi": "माफ करा, हे समजले नाही 😊",
    "bengali": "দুঃখিত, বুঝতে পারলাম না 😊",
}
# "I don't know" is a real answer: move on, like the Skip button (which sends "skip")
SKIP_WORDS = {"skip", "pata nahi", "nahi pata", "pta nahi", "malum nahi", "maloom nahi", "don't know", "dont know",
              "not sure", "पता नहीं", "नहीं पता", "मालूम नहीं", "माहीत नाही", "জানি না"}


def is_skip(message: str) -> bool:
    return message.strip().lower().strip(".!?। ") in SKIP_WORDS


class ProfileTurn(BaseModel):
    country: Country
    message: str = Field(min_length=1, max_length=2000)
    profile: Profile = Field(default_factory=Profile)
    asked: list[str] = Field(default_factory=list, description="All fields we've asked about so far")
    answering: list[str] = Field(default_factory=list, description="Fields the previous follow-up asked about")
    rounds: int = Field(0, ge=0, description="How many follow-up questions were asked so far")
    language: Language | None = Field(None, description="Conversation language from the previous reply")


class ProfileReply(BaseModel):
    profile: Profile
    follow_up: FollowUp | None = Field(description="Next question, or null when we have enough to search")
    asking: list[str] = Field(description="Fields the follow-up asks about — send back as `answering` and add to `asked`")
    ready: bool = Field(description="True when it's time to show results")
    language: Language = Field(description="Send back as `language` next turn")
    privacy_note: str | None = None
    retry: bool = Field(False, description="True when we didn't understand and asked again — not a new round")


@router.post("/profile", response_model=ProfileReply)
def profile_turn(turn: ProfileTurn) -> ProfileReply:
    # "२० साल" / "১.৫ লাখ" -> ASCII digits first, so ID-number removal and number checks see real digits
    message, removed = redact(ascii_digits(turn.message))
    language = detect_language(message, turn.country, turn.language)
    profile = extract_profile(message, turn.profile, turn.country, turn.answering)

    if profile == turn.profile and not is_skip(message):
        # Nothing understood: ask again (the same question, if we had asked one) instead of moving on
        if turn.answering:
            again = follow_up_question(turn.answering, language)
            follow_up = FollowUp(question=f"{SORRY[language]} {again.question}", options=again.options)
        else:
            follow_up = FollowUp(question=NOT_UNDERSTOOD[language])
        return ProfileReply(profile=profile, follow_up=follow_up, asking=turn.answering, ready=False,
                            language=language, privacy_note=PRIVACY_NOTE[language] if removed else None, retry=True)

    missing = missing_fields(profile, turn.country, turn.asked)
    follow_up, asking = None, []
    if missing and turn.rounds < MAX_FOLLOW_UP_ROUNDS:
        # A choice question (with quick-reply buttons) is asked on its own, so the buttons
        # clearly answer it. Other facts can be paired: at most two per question.
        if missing[0] in CHOICE_FIELDS:
            asking = missing[:1]
        else:
            asking = [name for name in missing[:2] if name not in CHOICE_FIELDS] or missing[:1]
        follow_up = follow_up_question(asking, language)

    return ProfileReply(
        profile=profile,
        follow_up=follow_up,
        asking=asking,
        ready=follow_up is None,
        language=language,
        privacy_note=PRIVACY_NOTE[language] if removed else None,
    )
