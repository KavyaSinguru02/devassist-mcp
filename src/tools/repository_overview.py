from __future__ import annotations

from analyzers.repository_analyzer import analyze_repository


LABELS = {
    "English": {
        "guide": "Repository Guide",
        "audience": "Audience",
        "language": "Language requested",
        "about": "What This Repository Is About",
        "about_text": "This repository contains a software project named **{name}**. DevAssist inspected the files and created a beginner-friendly map so a developer can understand where to start and how the project is organized.",
        "stack": "Technology Stack",
        "frameworks": "Frameworks and Why They Are Used",
        "detected_in": "Detected in",
        "architecture": "Architecture in Simple Words",
        "detected_style": "Detected style",
        "architecture_text": "Think of the repository as a set of organized rooms: entry files receive the request, feature modules do the main work, and utility files support repeated tasks.",
        "diagram": "Architecture Diagram",
        "entry": "Important Entry Points",
        "folders": "Important Folders",
        "files": "Important Files To Read",
        "learning": "Beginner Learning Path",
        "journey": "Repository Journey",
        "quick": "Quick Facts",
        "files_scanned": "Files scanned",
        "folders_scanned": "Folders scanned",
        "not_detected": "Not detected",
        "fallback_step": "Start with the README or the main entry point detected above.",
        "journey_steps": [
            "A developer opens the repository.",
            "They read the README or main entry file to understand the purpose.",
            "They inspect important folders to see where features live.",
            "They open one feature file at a time and follow imports/dependencies.",
            "They use error diagnosis, tests, and git tools when they start changing code.",
        ],
        "teacher_note": "This guide focuses on teaching and orientation, not criticism or code review.",
    },
    "Telugu": {
        "guide": "రిపోజిటరీ గైడ్",
        "audience": "ఎవరికి వివరణ",
        "language": "ఎంచుకున్న భాష",
        "about": "ఈ రిపోజిటరీ గురించి",
        "about_text": "ఈ రిపోజిటరీలో **{name}** అనే సాఫ్ట్‌వేర్ ప్రాజెక్ట్ ఉంది. DevAssist ఫైళ్లను పరిశీలించి, ఎక్కడ మొదలుపెట్టాలి మరియు ప్రాజెక్ట్ ఎలా అమర్చబడిందో సులభంగా అర్థమయ్యే మ్యాప్‌ను తయారు చేసింది.",
        "stack": "టెక్నాలజీ స్టాక్",
        "frameworks": "ఫ్రేమ్‌వర్క్స్ మరియు అవి ఎందుకు వాడారు",
        "detected_in": "ఇక్కడ గుర్తించబడింది",
        "architecture": "ఆర్కిటెక్చర్ సులభమైన మాటల్లో",
        "detected_style": "గుర్తించిన శైలి",
        "architecture_text": "ఈ రిపోజిటరీని ఒక ఇంటి లాగా ఊహించుకోండి: ఎంట్రీ ఫైళ్లు request ను స్వీకరిస్తాయి, feature modules ప్రధాన పని చేస్తాయి, utility files మళ్లీ మళ్లీ ఉపయోగించే సహాయక పనులు చేస్తాయి.",
        "diagram": "ఆర్కిటెక్చర్ డయాగ్రామ్",
        "entry": "ముఖ్యమైన ఎంట్రీ పాయింట్లు",
        "folders": "ముఖ్యమైన ఫోల్డర్లు",
        "files": "మొదట చదవాల్సిన ముఖ్యమైన ఫైళ్లు",
        "learning": "బిగినర్ లెర్నింగ్ పాత్",
        "journey": "రిపోజిటరీ జర్నీ",
        "quick": "త్వరిత విషయాలు",
        "files_scanned": "స్కాన్ చేసిన ఫైళ్లు",
        "folders_scanned": "స్కాన్ చేసిన ఫోల్డర్లు",
        "not_detected": "గుర్తించబడలేదు",
        "fallback_step": "ముందుగా README లేదా పైగా గుర్తించిన main entry point తో ప్రారంభించండి.",
        "journey_steps": [
            "డెవలపర్ రిపోజిటరీని తెరుస్తారు.",
            "ప్రాజెక్ట్ ఉద్దేశాన్ని తెలుసుకోవడానికి README లేదా main entry file చదువుతారు.",
            "ఫీచర్లు ఎక్కడ ఉన్నాయో తెలుసుకోవడానికి ముఖ్యమైన ఫోల్డర్లను చూస్తారు.",
            "ఒక్కో feature file తెరిచి imports/dependencies ను అనుసరిస్తారు.",
            "కోడ్ మార్చడం ప్రారంభించినప్పుడు error diagnosis, tests, git tools వాడుతారు.",
        ],
        "teacher_note": "ఈ గైడ్ బోధన మరియు దారి చూపడానికే; code review లేదా criticism కోసం కాదు.",
    },
    "Hindi": {
        "guide": "Repository Guide",
        "audience": "किसके लिए",
        "language": "चुनी गई भाषा",
        "about": "यह repository किस बारे में है",
        "about_text": "इस repository में **{name}** नाम का software project है। DevAssist ने files को देखकर beginner-friendly map बनाया है ताकि developer समझ सके कि कहाँ से शुरू करना है और project कैसे organized है।",
        "stack": "Technology Stack",
        "frameworks": "Frameworks और उनका उपयोग",
        "detected_in": "Detected in",
        "architecture": "Architecture आसान भाषा में",
        "detected_style": "Detected style",
        "architecture_text": "Repository को organized rooms की तरह सोचें: entry files request लेती हैं, feature modules मुख्य काम करते हैं, और utility files common helper काम करती हैं.",
        "diagram": "Architecture Diagram",
        "entry": "Important Entry Points",
        "folders": "Important Folders",
        "files": "Important Files To Read",
        "learning": "Beginner Learning Path",
        "journey": "Repository Journey",
        "quick": "Quick Facts",
        "files_scanned": "Files scanned",
        "folders_scanned": "Folders scanned",
        "not_detected": "Not detected",
        "fallback_step": "README या detected main entry point से शुरू करें.",
        "journey_steps": [
            "Developer repository खोलता है.",
            "Purpose समझने के लिए README या main entry file पढ़ता है.",
            "Features कहाँ हैं यह देखने के लिए important folders देखता है.",
            "एक-एक feature file खोलकर imports/dependencies follow करता है.",
            "Code बदलते समय error diagnosis, tests और git tools use करता है.",
        ],
        "teacher_note": "यह guide teaching और orientation के लिए है, criticism या code review के लिए नहीं.",
    },
}


def _labels(language: str) -> dict:
    return LABELS.get(language, LABELS["English"])


def _bullet(items, language: str = "English"):
    t = _labels(language)
    return "\n".join(f"- `{item}`" for item in items) if items else f"- {t['not_detected']}"


def _diagram(architecture: str) -> str:
    if "Streamlit" in architecture or "tool" in architecture.lower():
        return """```mermaid
graph TD
    User[Developer/User] --> UI[Streamlit UI]
    UI --> Router[Tool Selection]
    Router --> Repo[Repository Overview]
    Router --> Chat[Repository Chat]
    Router --> Build[Code Builder]
    Router --> Explain[Code Explainer]
    Router --> Debug[Error Diagnoser]
    Router --> Tests[Test Generator]
    Router --> Git[Git Analyzer]
    Repo --> Result[Beginner Friendly Output]
    Chat --> Result
    Build --> Result
    Explain --> Result
    Debug --> Result
    Tests --> Result
    Git --> Result
```"""
    if "MVC" in architecture or "Layered" in architecture:
        return """```mermaid
graph TD
    User[User] --> Controller[Controller / Route]
    Controller --> Service[Service / Business Logic]
    Service --> Repository[Repository / Data Access]
    Repository --> Database[(Database)]
    Database --> Repository
    Repository --> Service
    Service --> Controller
    Controller --> User
```"""
    return """```mermaid
graph TD
    User[User] --> Entry[Entry Point]
    Entry --> Core[Core Modules]
    Core --> Helpers[Utilities / Helpers]
    Core --> Output[Result]
```"""


def _translate_reason(reason: str, language: str) -> str:
    if language != "Telugu":
        return reason
    mapping = {
        "Start here to understand the project goal.": "ప్రాజెక్ట్ లక్ష్యాన్ని అర్థం చేసుకోవడానికి ఇక్కడి నుంచి ప్రారంభించండి.",
        "Main user interface entry point, if present.": "ఇది ఉంటే, user interface ప్రారంభమయ్యే ప్రధాన ఫైల్.",
        "Core feature implementations usually live here.": "సాధారణంగా ప్రధాన ఫీచర్ల implementation ఇక్కడ ఉంటుంది.",
        "Shared helper logic usually lives here.": "మళ్లీ మళ్లీ ఉపయోగించే helper logic సాధారణంగా ఇక్కడ ఉంటుంది.",
    }
    return mapping.get(reason, reason)


def generate_repository_overview(repo_path: str, audience: str = "Beginner", language: str = "English", include_diagram: bool = True) -> str:
    a = analyze_repository(repo_path)
    t = _labels(language)
    lines = []
    lines.append(f"# {t['guide']}: {a.name}")
    lines.append("")
    lines.append(f"**{t['audience']}:** {audience}")
    lines.append(f"**{t['language']}:** {language}")
    lines.append("")
    lines.append(f"## {t['about']}")
    lines.append(t["about_text"].format(name=a.name))
    lines.append("")
    lines.append(f"## {t['stack']}")
    if a.stack:
        for item in a.stack:
            lines.append(f"- **{item}**")
    else:
        lines.append(f"- {t['not_detected']}")
    lines.append("")
    lines.append(f"## {t['frameworks']}")
    if a.frameworks:
        for fw in a.frameworks:
            lines.append(f"- **{fw['name']}** — {fw['why']} {t['detected_in']} `{fw['detected_in']}`.")
    else:
        lines.append(f"- {t['not_detected']}")
    lines.append("")
    lines.append(f"## {t['architecture']}")
    lines.append(f"**{t['detected_style']}:** {a.architecture}")
    lines.append(t["architecture_text"])
    lines.append("")
    if include_diagram:
        lines.append(f"## {t['diagram']}")
        lines.append(_diagram(a.architecture))
        lines.append("")
    lines.append(f"## {t['entry']}")
    lines.append(_bullet(a.entry_points, language))
    lines.append("")
    lines.append(f"## {t['folders']}")
    lines.append(_bullet(a.important_folders, language))
    lines.append("")
    lines.append(f"## {t['files']}")
    lines.append(_bullet(a.important_files[:20], language))
    lines.append("")
    lines.append(f"## {t['learning']}")
    if a.learning_path:
        for step in a.learning_path:
            lines.append(f"{step['step']}. `{step['path']}` — {_translate_reason(step['reason'], language)}")
    else:
        lines.append(f"1. {t['fallback_step']}")
    lines.append("")
    lines.append(f"## {t['journey']}")
    for index, step in enumerate(t["journey_steps"], start=1):
        lines.append(f"{index}. {step}")
    lines.append("")
    lines.append(f"## {t['quick']}")
    lines.append(f"- {t['files_scanned']}: **{a.file_count}**")
    lines.append(f"- {t['folders_scanned']}: **{a.folder_count}**")
    lines.append(f"- {t['teacher_note']}")
    return "\n".join(lines)
