// UI text in both conversation languages. The backend decides the language;
// the UI follows it so buttons and messages match the chat.
import type { Language } from './types'

const text = {
  english: {
    tagline: "Find the government benefits you're entitled to — and how to claim them.",
    chooseCountry: 'Where do you live?',
    chooseState: 'Which state?',
    otherState: 'Other state',
    greeting: (country: string): string =>
      country === 'IN'
        ? 'Tell me about yourself in your own words — Hindi, Hinglish or English. For example: your age, what you do, your family income, and what help you need.'
        : 'Tell me about yourself in your own words — your age, work, family, income, and what you need help with.',
    placeholder: 'Type here…',
    send: 'Send',
    skip: 'Skip',
    showResults: 'Show my results',
    thinking: 'Haq is thinking…',
    privacy: "Your details stay in this browser. Haq never stores them and never needs ID numbers.",
    whatWeKnow: 'What Haq knows about you',
    remove: 'Remove',
    loadingSteps: [
      'Reading your profile…',
      'Checking eligibility rules for hundreds of schemes…',
      'Nemotron Ultra is reading the official rules for your best matches…',
      'Writing simple explanations for you…',
    ],
    yourEntitlements: 'You may be entitled to',
    perYear: 'per year',
    upTo: 'up to',
    schemesFound: (n: number) => `${n} schemes found for you`,
    checking: (judged: number, total: number) => `Nemotron Ultra is checking your best matches… ${judged} of ${total}`,
    noneFound: "We couldn't find a scheme that clearly fits yet. Try adding more details about yourself.",
    verdict: { eligible: 'Eligible', likely_eligible: 'Likely eligible', need_more_info: 'Check a few things' },
    stateScheme: 'State scheme',
    whyThisMatches: 'Why',
    toConfirm: 'To confirm',
    documents: 'Documents you need',
    howToApply: 'How to apply',
    applyNow: 'Apply online',
    officialSource: 'Official source',
    verify: 'Added by hand — please verify on the official website.',
    otherSchemes: (n: number) => `${n} more schemes that might apply`,
    startOver: 'Start over',
    error: 'Something went wrong. Please try again.',
    retry: 'Try again',
    disclaimer:
      'Haq gives guidance only, not an official decision. Always confirm on the official website before applying.',
    attribution: 'Data: myScheme.gov.in (Government of India) and GOV.UK (Open Government Licence v3.0).',
    poweredBy: 'Powered by NVIDIA Nemotron on Nebius Token Factory',
  },
  hinglish: {
    tagline: 'Jaaniye aap kin sarkari yojanaon ke haqdaar hain — aur unhe kaise paayein.',
    chooseCountry: 'Aap kahan rehte hain?',
    chooseState: 'Kaunsa rajya?',
    otherState: 'Koi aur rajya',
    greeting: (_country: string): string =>
      'Apne baare mein apne shabdon mein bataiye — umar, kya karte hain, ghar ki income, aur kis cheez ki madad chahiye.',
    placeholder: 'Yahan likhiye…',
    send: 'Bhejein',
    skip: 'Chhodein',
    showResults: 'Mere results dikhao',
    thinking: 'Haq soch raha hai…',
    privacy: 'Aapki jaankari sirf is browser mein rehti hai. Haq use save nahi karta, aur Aadhaar jaise number kabhi nahi maangta.',
    whatWeKnow: 'Haq aapke baare mein kya jaanta hai',
    remove: 'Hatayein',
    loadingSteps: [
      'Aapki profile padh rahe hain…',
      'Sainkdon yojanaon ke niyam check kar rahe hain…',
      'Nemotron Ultra aapke best matches ke official niyam padh raha hai…',
      'Aapke liye aasaan bhasha mein samjha rahe hain…',
    ],
    yourEntitlements: 'Aapko mil sakta hai',
    perYear: 'har saal',
    upTo: 'zyada se zyada',
    schemesFound: (n: number) => `Aapke liye ${n} yojanayein mili`,
    checking: (judged: number, total: number) => `Nemotron Ultra aapke best matches check kar raha hai… ${judged}/${total}`,
    noneFound: 'Abhi koi yojana saaf taur par fit nahi hui. Apne baare mein thodi aur jaankari dekar dobara try karein.',
    verdict: { eligible: 'Eligible', likely_eligible: 'Shayad eligible', need_more_info: 'Kuch cheezein check karein' },
    stateScheme: 'Rajya yojana',
    whyThisMatches: 'Kyun',
    toConfirm: 'Confirm karein',
    documents: 'Zaroori documents',
    howToApply: 'Apply kaise karein',
    applyNow: 'Online apply karein',
    officialSource: 'Official source',
    verify: 'Haath se joda gaya — official website par confirm karein.',
    otherSchemes: (n: number) => `${n} aur yojanayein jo shayad laagu hon`,
    startOver: 'Phir se shuru karein',
    error: 'Kuch gadbad ho gayi. Dobara koshish karein.',
    retry: 'Dobara try karein',
    disclaimer:
      'Haq sirf margdarshan deta hai, sarkari faisla nahi. Apply karne se pehle official website par zaroor confirm karein.',
    attribution: 'Data: myScheme.gov.in (Bharat Sarkar) aur GOV.UK (Open Government Licence v3.0).',
    poweredBy: 'NVIDIA Nemotron on Nebius Token Factory dwara sanchalit',
  },
}

export type Strings = (typeof text)['english']

export function t(language: Language): Strings {
  return text[language]
}

export function formatMoney(amount: number, currency: 'INR' | 'GBP'): string {
  return new Intl.NumberFormat(currency === 'INR' ? 'en-IN' : 'en-GB', {
    style: 'currency',
    currency,
    maximumFractionDigits: 0,
  }).format(amount)
}
