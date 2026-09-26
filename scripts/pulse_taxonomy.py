"""
Job-title taxonomy for the Build-Out Pulse — one classifier, shared by every Pulse script.

Five classes, checked in this order (first match wins):
  software       software, data, ML/AI, firmware/embedded, product management, design, SRE, security
  manufacturing  production, technicians, assembly, machining, welding, quality, test technicians,
                 supply chain, procurement, facilities, EHS, site security, logistics, maintenance
  commercial     sales, BD, marketing, recruiting, HR, finance, legal, admin, customer success,
                 non-technical program/project management
  hardware       mechanical, electrical, systems, GNC, avionics, thermal, structural, propulsion, RF,
                 power electronics, materials, controls, test/reliability engineering, physicists,
                 chemists, process/nuclear/aerospace/optical engineers — the physical-engineering core
  other          anything else (interns without a discipline, clinical roles, "general application")

Atoms = manufacturing + hardware. Bits = software. The atoms/bits ratio is atoms ÷ bits.
Version 1.1 — 26 Sept 2026. Changing these patterns is a methodology change: bump the version.
"""
import re

TAXONOMY_VERSION = "1.1"

SOFTWARE = re.compile(
    r"software|frontend|front-end|backend|back-end|full[- ]stack|devops|site reliability|\bsre\b|data scientist|data engineer|"
    r"machine learning|\bml\b|\bai\b|\bllm\b|platform engineer|infrastructure engineer|security engineer|cloud engineer|"
    r"product manager|product designer|ux|ui designer|web developer|mobile (?:engineer|developer)|firmware|embedded|"
    r"forward deployed|solutions engineer|perception engineer|autonomy engineer|computer vision|simulation engineer|"
    r"\bqa engineer\b|test automation|developer advocate|data analyst|analytics engineer", re.I)

MANUFACTURING = re.compile(
    r"technician|machinist|welder|weld|manufactur|production|assembl|fabricat|\bcnc\b|electrician|plant manager|plant "
    r"|operator|quality (?:inspector|control|assurance technician)|inspector|supply chain|procurement|purchasing|buyer|planner|"
    r"maintenance|facilit|logistic|warehouse|tooling|machining|fitter|rigger|millwright|composite tech|painter|"
    r"\behs\b|environmental health|safety (?:manager|specialist|officer)|security officer|site (?:lead|manager|supervisor)|"
    r"shop (?:lead|supervisor|manager)|shift (?:lead|supervisor)|material handler|field service|installer|commissioning|"
    r"superintendent|industrial hygien|dangerous goods|hazmat|forklift|crane operator|calibration|metrology", re.I)

COMMERCIAL = re.compile(
    r"\bsales\b|account (?:executive|manager|director)|business development|\bbdr\b|\bsdr\b|marketing|growth|recruit|talent|"
    r"people (?:ops|operations|partner)|\bhr\b|human resources|finance|financial|accountant|accounting|\bcontroller\b|"
    r"\bcfo\b|legal|counsel|paralegal|compliance|executive assistant|administrative|office manager|chief of staff|"
    r"customer success|customer support|community|communications|public relations|policy|government (?:relations|affairs)|"
    r"program manager|project manager|programme manager|operations (?:associate|coordinator|manager|analyst)|"
    r"strategy|analyst|investor relations|partnerships|contracts (?:manager|administrator)|proposal|"
    r"\bit (?:manager|support|specialist|systems|applications|administrator)|systems administrator|help ?desk|customs|trade compliance", re.I)

HARDWARE = re.compile(
    r"mechanical|electrical|electronics|systems engineer|\bgnc\b|guidance|avionics|thermal|structural|propulsion|"
    r"\brf\b|radio frequency|antenna|power electronics|materials|metallurg|controls engineer|control systems|"
    r"test engineer|reliability engineer|validation engineer|integration engineer|hardware|\bpcb\b|"
    r"physicist|chemist|scientist|process engineer|nuclear|reactor|aerospace|aeronautical|optical|photonic|laser|"
    r"design engineer|manufacturing engineer|industrial engineer|civil engineer|fluid|combustion|turbine|battery|cell engineer|"
    r"robotics engineer|mechatronic|engineer", re.I)


def classify(title: str) -> str:
    t = title or ""
    if SOFTWARE.search(t):
        return "software"
    if MANUFACTURING.search(t):
        return "manufacturing"
    if COMMERCIAL.search(t):
        return "commercial"
    if HARDWARE.search(t):
        return "hardware"
    return "other"


SENIOR_MFG = re.compile(
    r"(?:\b(?:vp|vice president|svp|head|director|chief|general manager|gm)\b.*\b(?:manufactur|production|operations|plant|facilit|supply chain|industrial)\b)|"
    r"plant manager|facilities? (?:manager|lead|director)|site (?:lead|director|manager)|factory (?:lead|manager|director)", re.I)


def is_senior_manufacturing(title: str) -> bool:
    return bool(SENIOR_MFG.search(title or ""))
