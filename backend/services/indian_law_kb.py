"""
indian_law_kb.py — India-specific legal knowledge base.

Purpose:
    Inject real Indian law citations into AI risk analysis so every
    risk flag says "violates Section 106, Transfer of Property Act"
    instead of "this looks risky".

Structure:
    INDIAN_LAW_KB       — full knowledge base, keyed by document type
    get_law_context()   — returns formatted prompt snippet for a doc type
    check_clause_laws() — given clause text, returns matching law violations
"""

from __future__ import annotations

# ─── Master Knowledge Base ───────────────────────────────────────────────────

INDIAN_LAW_KB: dict[str, dict] = {

    # ── RENTAL / LEASE ───────────────────────────────────────────────────────
    "rental": {
        "display_name": "Rental / Lease Agreement",
        "primary_laws": [
            "Transfer of Property Act, 1882 (TPA)",
            "Rent Control Acts (state-specific)",
            "Indian Contract Act, 1872",
            "Registration Act, 1908",
        ],
        "rules": [
            {
                "topic": "Notice Period for Termination",
                "law": "Section 106, Transfer of Property Act 1882",
                "rule": "Minimum 15 days written notice required for month-to-month tenancy; 6 months for annual tenancy",
                "violation_keywords": ["notice", "terminate", "vacate", "quit"],
                "risky_if": "notice period is less than 15 days",
                "safe_if": "notice period is 15 days or more (monthly) or 6 months (annual)",
            },
            {
                "topic": "Security Deposit Limits",
                "law": "State Rent Control Acts",
                "rule": "Maharashtra: max 3 months rent. Delhi: no statutory cap but 2-3 months is standard. Karnataka: max 10 months rent.",
                "violation_keywords": ["security deposit", "advance", "caution deposit"],
                "risky_if": "deposit exceeds 3 months rent in Maharashtra, or 10 months in Karnataka",
                "safe_if": "deposit is within state-specific limits",
            },
            {
                "topic": "Rent Increase",
                "law": "Respective State Rent Control Acts; Section 8, Maharashtra Rent Control Act 1999",
                "rule": "Landlord cannot unilaterally increase rent mid-tenancy without mutual written agreement",
                "violation_keywords": ["rent increase", "revise rent", "enhanced rent", "hike"],
                "risky_if": "landlord given unilateral right to increase rent at any time",
                "safe_if": "rent increase tied to fixed schedule or mutual written consent",
            },
            {
                "topic": "Registration Requirement",
                "law": "Section 17, Registration Act 1908; Section 107, TPA 1882",
                "rule": "Leases exceeding 12 months MUST be registered. Unregistered leases over 12 months are not admissible as evidence.",
                "violation_keywords": ["lease", "agreement", "term", "period"],
                "risky_if": "agreement is for more than 12 months but not registered",
                "safe_if": "agreement is registered or term is under 12 months (leave and license preferred)",
            },
            {
                "topic": "Maintenance Liability",
                "law": "Section 108, Transfer of Property Act 1882",
                "rule": "Landlord must keep the property in tenantable condition. Structural repairs are landlord's responsibility.",
                "violation_keywords": ["maintenance", "repair", "damage", "upkeep"],
                "risky_if": "tenant made responsible for all maintenance including structural",
                "safe_if": "maintenance split — day-to-day tenant, structural landlord",
            },
            {
                "topic": "Lock-in Period",
                "law": "Indian Contract Act 1872 (Section 73, 74 — damages for breach)",
                "rule": "Lock-in periods are enforceable but penalty for early exit must be reasonable, not punitive.",
                "violation_keywords": ["lock-in", "lockin", "lock in", "early exit", "early termination"],
                "risky_if": "lock-in penalty equals full remaining rent or is clearly punitive",
                "safe_if": "early exit penalty is 1-2 months rent or proportional",
            },
            {
                "topic": "Subletting",
                "law": "Section 108(j), Transfer of Property Act 1882",
                "rule": "Tenant cannot sublet without landlord's written consent unless agreement expressly allows it.",
                "violation_keywords": ["sublet", "sublease", "assign", "transfer"],
                "risky_if": "absolute prohibition without any exception",
                "safe_if": "subletting allowed with written consent",
            },
        ],
        "tenant_rights": [
            "Right to peaceful enjoyment (Section 108, TPA)",
            "Right to receive rent receipt",
            "Right to 15 days minimum notice before eviction (Section 106, TPA)",
            "Landlord cannot enter without notice except emergencies",
            "Deposit must be returned within 15-30 days of vacating (varies by state)",
        ],
        "state_variations": {
            "Maharashtra": "Maharashtra Rent Control Act 1999 — deposit max 3 months, rent increase max 4% per year for controlled premises",
            "Delhi": "Delhi Rent Control Act 1958 — applies to premises with rent below ₹3,500/month",
            "Karnataka": "Karnataka Rent Act 2001 — deposit max 10 months",
            "Tamil Nadu": "Tamil Nadu Regulation of Rights and Responsibilities of Landlords and Tenants Act 2017",
            "West Bengal": "West Bengal Premises Tenancy Act 1997",
        },
    },

    # ── EMPLOYMENT ───────────────────────────────────────────────────────────
    "employment": {
        "display_name": "Employment Contract",
        "primary_laws": [
            "Industrial Disputes Act, 1947",
            "Shops and Establishments Act (state-specific)",
            "Payment of Gratuity Act, 1972",
            "Employees' Provident Funds Act, 1952",
            "Maternity Benefit Act, 1961",
            "Sexual Harassment of Women at Workplace Act, 2013 (POSH)",
            "Payment of Bonus Act, 1965",
            "Minimum Wages Act, 1948",
        ],
        "rules": [
            {
                "topic": "Notice Period",
                "law": "Section 25-N, Industrial Disputes Act 1947; Shops & Establishments Acts",
                "rule": "Minimum 1 month notice for employees with more than 1 year service; 3 months for managerial cadre is common. No notice period can be zero.",
                "violation_keywords": ["notice period", "notice", "terminate", "resignation"],
                "risky_if": "notice period is zero or less than 30 days for non-probation employees",
                "safe_if": "notice period is 30-90 days with buyout option at basic salary",
            },
            {
                "topic": "Probation Period",
                "law": "Shops and Establishments Act (varies by state)",
                "rule": "Probation typically 3-6 months. During probation, employer can terminate without notice. Probation beyond 6 months is unusual and may be challenged.",
                "violation_keywords": ["probation", "probationary", "trial period"],
                "risky_if": "probation exceeds 6 months or is indefinitely extendable",
                "safe_if": "probation is 3-6 months with clear confirmation process",
            },
            {
                "topic": "Non-Compete Clause",
                "law": "Section 27, Indian Contract Act 1872",
                "rule": "Post-employment non-compete clauses are VOID in India under Section 27 ICA. They are unenforceable against employees after termination.",
                "violation_keywords": ["non-compete", "non compete", "competition", "competitor"],
                "risky_if": "post-employment non-compete restricts employment for any period",
                "safe_if": "only non-solicitation (clients/employees) is present, not blanket non-compete",
                "note": "Non-compete DURING employment is valid. Post-employment is void.",
            },
            {
                "topic": "Provident Fund (PF)",
                "law": "Employees' Provident Funds and Miscellaneous Provisions Act 1952",
                "rule": "Mandatory for establishments with 20+ employees. Employee contributes 12% of basic salary; employer matches 12% (of which 8.33% goes to EPS).",
                "violation_keywords": ["pf", "provident fund", "epf", "eps"],
                "risky_if": "PF not mentioned for companies with 20+ employees",
                "safe_if": "PF contribution clearly stated at statutory rates",
            },
            {
                "topic": "Gratuity",
                "law": "Payment of Gratuity Act 1972",
                "rule": "Payable after 5 years of continuous service. Formula: (15 × last drawn basic salary × years of service) / 26.",
                "violation_keywords": ["gratuity"],
                "risky_if": "gratuity explicitly waived or formula differs unfavorably",
                "safe_if": "gratuity per statutory formula or better",
            },
            {
                "topic": "Intellectual Property Assignment",
                "law": "Copyright Act 1957; Patents Act 1970",
                "rule": "Employer can own work created during employment. Blanket assignment of ALL future IP including personal projects is overreach.",
                "violation_keywords": ["intellectual property", "ip", "invention", "copyright", "patent", "ownership"],
                "risky_if": "all IP including personal projects outside work hours assigned to employer",
                "safe_if": "only work-related IP during employment assigned to employer",
            },
            {
                "topic": "Confidentiality / NDA",
                "law": "Indian Contract Act 1872 (enforceable if reasonable in scope and time)",
                "rule": "Reasonable NDAs are enforceable. Perpetual confidentiality on all information is unreasonable and courts may not enforce it.",
                "violation_keywords": ["confidential", "nda", "non-disclosure", "secret"],
                "risky_if": "perpetual confidentiality on all information including publicly available",
                "safe_if": "confidentiality limited to genuinely proprietary information with reasonable time limit",
            },
            {
                "topic": "Termination Without Cause",
                "law": "Industrial Disputes Act 1947; Standing Orders",
                "rule": "For workmen (non-managerial), termination requires notice + retrenchment compensation (15 days per year of service). Managerial staff have contractual notice only.",
                "violation_keywords": ["terminate", "termination", "dismiss", "discharge", "at will"],
                "risky_if": "employer can terminate 'at will' or 'for convenience' without compensation",
                "safe_if": "termination requires notice period or payment in lieu",
            },
            {
                "topic": "ESOP / Stock Options",
                "law": "SEBI (Share Based Employee Benefits) Regulations 2021; Companies Act 2013",
                "rule": "ESOPs must follow SEBI regulations for listed companies. Vesting schedule and cliff period must be clearly defined.",
                "violation_keywords": ["esop", "stock option", "equity", "shares", "vesting"],
                "risky_if": "vesting conditions unclear, or company retains unilateral right to cancel all unvested options",
                "safe_if": "vesting schedule clear, cliff period defined, acceleration on change of control",
            },
        ],
        "employee_rights": [
            "Right to PF (Employees' Provident Funds Act)",
            "Right to gratuity after 5 years (Payment of Gratuity Act)",
            "Right to maternity leave — 26 weeks for first 2 children (Maternity Benefit Act)",
            "Right to safe workplace and POSH compliance",
            "Post-employment non-compete is unenforceable (Section 27, ICA)",
            "Minimum wages as per state notification",
        ],
    },

    # ── LOAN ─────────────────────────────────────────────────────────────────
    "loan": {
        "display_name": "Loan Agreement",
        "primary_laws": [
            "Reserve Bank of India Act, 1934",
            "Indian Contract Act, 1872",
            "SARFAESI Act, 2002",
            "Recovery of Debts and Bankruptcy Act, 1993",
            "Consumer Protection Act, 2019",
            "Usurious Loans Act, 1918",
        ],
        "rules": [
            {
                "topic": "Interest Rate",
                "law": "RBI Fair Practices Code; Usurious Loans Act 1918",
                "rule": "RBI has not set a universal cap but NBFC rates above 36% p.a. for microfinance and 18-24% for personal loans raise usury concerns. Courts can reduce unreasonable rates.",
                "violation_keywords": ["interest", "rate", "per annum", "p.a.", "monthly"],
                "risky_if": "interest rate exceeds 24% p.a. for personal loans or 36% for microfinance",
                "safe_if": "interest rate is within RBI benchmarked rates",
            },
            {
                "topic": "Prepayment / Foreclosure Charges",
                "law": "RBI Circular on Prepayment of Loans (2012); Consumer Protection Act 2019",
                "rule": "RBI has banned prepayment penalties for floating rate loans for individual borrowers. Fixed rate loans may have charges but must be disclosed upfront.",
                "violation_keywords": ["prepayment", "foreclosure", "pre-payment", "early repayment"],
                "risky_if": "prepayment penalty on floating rate loan, or penalty not disclosed upfront",
                "safe_if": "no penalty on floating rate; fixed rate penalty clearly disclosed",
            },
            {
                "topic": "Penal Interest / Late Payment Charges",
                "law": "RBI Circular on Penal Charges in Loan Accounts (August 2023)",
                "rule": "From January 2024, banks cannot compound penal charges. Penal charges are separate from interest and must not be capitalized.",
                "violation_keywords": ["penalty", "penal", "late payment", "overdue", "default charge"],
                "risky_if": "penal charges are compounded or added to principal",
                "safe_if": "penal charges are flat, non-compounding, and separately disclosed",
            },
            {
                "topic": "Collateral / Security",
                "law": "SARFAESI Act 2002",
                "rule": "Lender can enforce security without court order under SARFAESI. Borrower must receive 60-day notice before enforcement.",
                "violation_keywords": ["collateral", "security", "mortgage", "hypothecation", "pledge"],
                "risky_if": "lender can seize collateral without 60-day notice",
                "safe_if": "60-day notice period maintained as per SARFAESI",
            },
            {
                "topic": "Personal Guarantee",
                "law": "Indian Contract Act 1872 (Sections 126-147 on Guarantee)",
                "rule": "Personal guarantee makes guarantor equally liable as principal debtor. Continuing guarantee covers all future transactions.",
                "violation_keywords": ["guarantee", "guarantor", "personal guarantee", "surety"],
                "risky_if": "open-ended continuing guarantee with no cap on liability",
                "safe_if": "guarantee limited to specific loan amount and tenure",
            },
            {
                "topic": "Cross-Default Clause",
                "law": "Indian Contract Act 1872",
                "rule": "A default on any other loan triggers default under this agreement too. Extremely risky for borrowers.",
                "violation_keywords": ["cross default", "cross-default", "other obligations", "other loans"],
                "risky_if": "default on any other loan automatically triggers default here",
                "safe_if": "default limited to obligations under this specific agreement",
            },
        ],
        "borrower_rights": [
            "Right to full disclosure of interest rate, fees, and charges (RBI KFS guidelines)",
            "No prepayment penalty on floating rate individual loans",
            "60-day notice before collateral enforcement (SARFAESI)",
            "Right to grievance redressal — RBI Ombudsman for banks/NBFCs",
            "Right to credit score disclosure before rejection",
        ],
    },

    # ── PROPERTY SALE ────────────────────────────────────────────────────────
    "property_sale": {
        "display_name": "Property Sale Agreement / Sale Deed",
        "primary_laws": [
            "Transfer of Property Act, 1882",
            "Registration Act, 1908",
            "Stamp Act (state-specific)",
            "Real Estate (Regulation and Development) Act, 2016 (RERA)",
            "Income Tax Act, 1961 (TDS on property)",
            "Consumer Protection Act, 2019",
        ],
        "rules": [
            {
                "topic": "Registration Requirement",
                "law": "Section 17, Registration Act 1908; Section 54, TPA 1882",
                "rule": "Sale of immovable property valued above ₹100 MUST be registered. Unregistered sale deeds are not valid and transfer no title.",
                "violation_keywords": ["registration", "register", "sale deed", "transfer"],
                "risky_if": "agreement does not mention registration or attempts unregistered transfer",
                "safe_if": "registration at sub-registrar's office clearly mentioned",
            },
            {
                "topic": "Stamp Duty",
                "law": "Indian Stamp Act 1899; State Stamp Acts",
                "rule": "Stamp duty varies 4-8% by state. Underpaid stamp duty makes document inadmissible in court.",
                "violation_keywords": ["stamp duty", "stamp", "registration charges"],
                "risky_if": "stamp duty not paid or document only has agreement to sell stamp",
                "safe_if": "full stamp duty as per state circle rate paid",
            },
            {
                "topic": "TDS on Property",
                "law": "Section 194-IA, Income Tax Act 1961",
                "rule": "Buyer must deduct 1% TDS for property purchases above ₹50 lakhs and deposit with government. Non-compliance attracts penalty.",
                "violation_keywords": ["tds", "tax deducted", "income tax", "form 26qb"],
                "risky_if": "TDS obligation not mentioned for properties above ₹50 lakhs",
                "safe_if": "TDS obligation clearly stated with Form 26QB requirement",
            },
            {
                "topic": "Title Verification",
                "law": "Transfer of Property Act 1882; Specific Relief Act 1963",
                "rule": "Seller must have clear, marketable title. Buyer should verify 30-year title chain. Seller warranties should survive sale.",
                "violation_keywords": ["title", "encumbrance", "clear title", "ownership"],
                "risky_if": "seller's warranty limited or excluded; title not warranted",
                "safe_if": "seller warrants clear title and indemnifies buyer against title defects",
            },
            {
                "topic": "RERA Compliance",
                "law": "RERA Act 2016",
                "rule": "New residential projects must be RERA registered. Builders must disclose project details, timelines, and carpet area. Delay attracts SBI MCLR interest penalty.",
                "violation_keywords": ["builder", "developer", "project", "flat", "apartment", "possession"],
                "risky_if": "builder project not RERA registered; no delay compensation clause",
                "safe_if": "RERA registration number mentioned; delay compensation at SBI MCLR rate",
            },
        ],
        "buyer_rights": [
            "Right to clear title and undisputed ownership",
            "RERA complaint for delayed possession",
            "Refund with interest if builder defaults",
            "12% interest on delayed refunds under RERA",
            "Consumer forum complaint under Consumer Protection Act 2019",
        ],
    },

    # ── SERVICE CONTRACT ─────────────────────────────────────────────────────
    "service": {
        "display_name": "Service / Freelance Contract",
        "primary_laws": [
            "Indian Contract Act, 1872",
            "Specific Relief Act, 1963",
            "Arbitration and Conciliation Act, 1996",
            "GST Act, 2017",
            "Copyright Act, 1957",
        ],
        "rules": [
            {
                "topic": "Payment Terms",
                "law": "Indian Contract Act 1872 (Section 55 — time as essence)",
                "rule": "If time is of essence for payment, delay gives right to rescind. GST must be charged and a proper invoice raised.",
                "violation_keywords": ["payment", "invoice", "gst", "fees"],
                "risky_if": "no payment schedule; vague 'upon completion'; no late payment interest",
                "safe_if": "clear payment milestones; 1.5-2% monthly interest on delayed payment",
            },
            {
                "topic": "Liability Cap",
                "law": "Indian Contract Act 1872 (Section 73 — measure of damages)",
                "rule": "Unlimited liability for service providers is extremely risky. Liability should be capped at contract value.",
                "violation_keywords": ["liability", "damages", "loss", "indemnify"],
                "risky_if": "unlimited liability; broad indemnification covering consequential losses",
                "safe_if": "liability capped at 1x contract value; consequential damages excluded",
            },
            {
                "topic": "Dispute Resolution",
                "law": "Arbitration and Conciliation Act 1996",
                "rule": "Arbitration is faster than courts. Single arbitrator is common for small contracts. MSME disputes under MSMED Act have special fast-track mechanism.",
                "violation_keywords": ["dispute", "arbitration", "jurisdiction", "court"],
                "risky_if": "no dispute resolution clause; only expensive courts mentioned",
                "safe_if": "arbitration clause with seat, number of arbitrators, and governing law",
            },
            {
                "topic": "Intellectual Property",
                "law": "Copyright Act 1957 (Section 17 — first ownership)",
                "rule": "Under Section 17, if a freelancer creates work for consideration, copyright vests in the client only if the contract says so. Without explicit assignment, freelancer retains copyright.",
                "violation_keywords": ["ip", "copyright", "ownership", "work product", "deliverable"],
                "risky_if": "no IP clause — freelancer may retain rights causing future dispute",
                "safe_if": "clear IP assignment to client upon full payment; moral rights waived",
            },
        ],
        "service_provider_rights": [
            "Right to payment per agreed milestones",
            "Copyright remains with creator unless assigned (Section 17, Copyright Act)",
            "Right to stop work if payment not received",
            "GST input credit on business expenses",
        ],
    },

    # ── COURT / LEGAL DOCUMENTS ──────────────────────────────────────────────
    "court": {
        "display_name": "Court Document / Legal Notice",
        "primary_laws": [
            "Code of Civil Procedure, 1908 (CPC)",
            "Code of Criminal Procedure, 1973 (CrPC)",
            "Indian Penal Code, 1860 (IPC) / Bharatiya Nyaya Sanhita 2023",
            "Evidence Act, 1872",
            "Limitation Act, 1963",
        ],
        "rules": [
            {
                "topic": "Limitation Period",
                "law": "Limitation Act 1963",
                "rule": "Civil suits: 3 years from cause of action. Property disputes: 12 years. Criminal complaints: varies. Missing deadline bars the remedy.",
                "violation_keywords": ["limitation", "time limit", "period", "days", "expire"],
                "risky_if": "action required within tight deadline mentioned in document",
                "safe_if": "well within limitation period",
            },
            {
                "topic": "Legal Notice Response",
                "law": "Section 80, CPC (government notices); Indian Contract Act",
                "rule": "Legal notices typically require 30-60 day response. Ignoring a notice can be used against you in court.",
                "violation_keywords": ["legal notice", "notice", "reply", "respond"],
                "risky_if": "notice demands response within less than 15 days",
                "safe_if": "30+ days given to respond",
            },
            {
                "topic": "Bail Conditions",
                "law": "Sections 436-439, CrPC / BNSS 2023",
                "rule": "Bail conditions must be reasonable and not more onerous than necessary. Conditions restricting travel or reporting have legal standing.",
                "violation_keywords": ["bail", "surety", "bond", "travel", "passport"],
                "risky_if": "conditions appear disproportionate to offence alleged",
                "safe_if": "standard bail conditions consistent with offence severity",
            },
        ],
    },

    # ── INSURANCE ────────────────────────────────────────────────────────────
    "insurance": {
        "display_name": "Insurance Policy / Claim",
        "primary_laws": [
            "Insurance Act, 1938",
            "Insurance Regulatory and Development Authority Act, 1999 (IRDAI)",
            "Consumer Protection Act, 2019",
        ],
        "rules": [
            {
                "topic": "Exclusion Clauses",
                "law": "IRDAI Regulations; Consumer Protection Act 2019",
                "rule": "Insurers must clearly disclose all exclusions at time of sale. Hidden exclusions that defeat the purpose of the policy are unfair trade practice.",
                "violation_keywords": ["exclusion", "not covered", "excluded", "except"],
                "risky_if": "broad exclusions covering common scenarios without clear disclosure",
                "safe_if": "exclusions clearly listed and reasonable",
            },
            {
                "topic": "Claim Rejection Grounds",
                "law": "Section 45, Insurance Act 1938 (insurer cannot repudiate after 3 years)",
                "rule": "After 3 years, insurer can only contest claim if fraudulent misrepresentation proven. Rejection for minor non-disclosures after 3 years is illegal.",
                "violation_keywords": ["reject", "repudiate", "void", "misrepresentation", "disclosure"],
                "risky_if": "insurer reserves right to reject any claim based on any non-disclosure",
                "safe_if": "rejection grounds limited and consistent with IRDAI regulations",
            },
        ],
    },

    # ── CONSUMER ─────────────────────────────────────────────────────────────
    "consumer": {
        "display_name": "Consumer Agreement / E-commerce T&C",
        "primary_laws": [
            "Consumer Protection Act, 2019",
            "Consumer Protection (E-Commerce) Rules, 2020",
            "Information Technology Act, 2000",
        ],
        "rules": [
            {
                "topic": "Unfair Contract Terms",
                "law": "Section 2(46), Consumer Protection Act 2019",
                "rule": "Unfair contract terms that cause significant imbalance to consumer's detriment are void. This includes clauses preventing consumer from exercising legal rights.",
                "violation_keywords": ["no refund", "no warranty", "no liability", "waive", "waiver"],
                "risky_if": "blanket no-refund, no-warranty, or waiver of all legal rights",
                "safe_if": "reasonable terms with consumer's statutory rights preserved",
            },
            {
                "topic": "Return / Refund Policy",
                "law": "Consumer Protection (E-Commerce) Rules 2020",
                "rule": "E-commerce entities must provide return policy. Defective goods entitle consumer to replacement, repair, or refund (Section 18, CPA 2019).",
                "violation_keywords": ["return", "refund", "replacement", "cancellation"],
                "risky_if": "no return policy; return window less than 7 days for e-commerce",
                "safe_if": "7+ day return window; defective goods fully covered",
            },
        ],
    },

    # ── FRANCHISE / BUSINESS ─────────────────────────────────────────────────
    "business": {
        "display_name": "Business / Franchise Agreement",
        "primary_laws": [
            "Indian Contract Act, 1872",
            "Competition Act, 2002",
            "Arbitration and Conciliation Act, 1996",
            "Intellectual Property Laws",
        ],
        "rules": [
            {
                "topic": "Territorial Exclusivity",
                "law": "Competition Act 2002 (Section 3 — anti-competitive agreements)",
                "rule": "Absolute territorial restrictions in franchises can be anti-competitive. Must be reasonable and justified.",
                "violation_keywords": ["territory", "exclusive", "region", "area"],
                "risky_if": "franchisor can unilaterally grant competing franchises in same territory",
                "safe_if": "exclusive territory clearly defined and protected",
            },
            {
                "topic": "Termination Without Cause",
                "law": "Indian Contract Act 1872; Specific Relief Act 1963",
                "rule": "Franchise agreements with heavy upfront investment require reasonable termination notice. Courts may grant injunction against arbitrary termination.",
                "violation_keywords": ["terminate", "termination", "exit", "close"],
                "risky_if": "franchisor can terminate without cause with minimal notice",
                "safe_if": "termination requires cause or 6-12 months notice",
            },
        ],
    },

    # ── DIVORCE / FAMILY ─────────────────────────────────────────────────────
    "family": {
        "display_name": "Divorce / Family Law Document",
        "primary_laws": [
            "Hindu Marriage Act, 1955",
            "Special Marriage Act, 1954",
            "Protection of Women from Domestic Violence Act, 2005",
            "Hindu Succession Act, 1956",
            "Maintenance and Welfare of Parents and Senior Citizens Act, 2007",
        ],
        "rules": [
            {
                "topic": "Maintenance / Alimony",
                "law": "Section 125, CrPC; Section 24-25, Hindu Marriage Act 1955",
                "rule": "Courts determine alimony based on spouse's income, lifestyle, and contribution. Agreed amounts in settlement must be fair to both parties.",
                "violation_keywords": ["maintenance", "alimony", "support", "monthly payment"],
                "risky_if": "maintenance waiver without proper compensation; unusually low amount",
                "safe_if": "maintenance consistent with party's standard of living",
            },
            {
                "topic": "Child Custody",
                "law": "Guardians and Wards Act 1890; Hindu Minority and Guardianship Act 1956",
                "rule": "Best interest of the child is paramount. Courts may override parental agreements that harm the child.",
                "violation_keywords": ["custody", "child", "minor", "guardian", "visitation", "access"],
                "risky_if": "complete denial of access to one parent; child's welfare not primary consideration",
                "safe_if": "joint custody or defined visitation schedule with child's welfare central",
            },
            {
                "topic": "Property Division",
                "law": "Hindu Succession Act 1956; Section 27, Hindu Marriage Act",
                "rule": "Hindu women have equal rights in ancestral property since 2005 amendment. Matrimonial home rights exist for wife during marriage.",
                "violation_keywords": ["property", "asset", "division", "share", "transfer"],
                "risky_if": "unequal division without reason; wife's contribution to matrimonial home ignored",
                "safe_if": "fair division with both parties' financial contribution considered",
            },
        ],
    },
}


# ─── Public API ───────────────────────────────────────────────────────────────

def get_law_context(document_type: str) -> str:
    """
    Return a formatted prompt snippet for the given document type.
    Injected into the AI system prompt so every analysis cites real laws.
    
    Args:
        document_type: One of the keys in INDIAN_LAW_KB, or a free-form 
                       string that we map to the closest category.
    
    Returns:
        Multi-line string ready to be inserted into a prompt.
    """
    kb = _find_kb_entry(document_type)
    if not kb:
        return _generic_law_context()

    lines = [
        f"INDIAN LAW CONTEXT FOR {kb['display_name'].upper()}:",
        "",
        "Applicable Laws:",
    ]
    for law in kb.get("primary_laws", []):
        lines.append(f"  • {law}")

    lines.append("")
    lines.append("Key Legal Rules — CITE THESE when flagging risks:")
    lines.append("")

    for rule in kb.get("rules", []):
        lines.append(f"  ► {rule['topic']}")
        lines.append(f"    Law: {rule['law']}")
        lines.append(f"    Rule: {rule['rule']}")
        lines.append(f"    Risky if: {rule['risky_if']}")
        lines.append(f"    Safe if: {rule['safe_if']}")
        if "note" in rule:
            lines.append(f"    Note: {rule['note']}")
        lines.append("")

    rights_key = next(
        (k for k in kb if k.endswith("_rights") or k == "borrower_rights"), None
    )
    if rights_key and kb.get(rights_key):
        lines.append("User's Legal Rights:")
        for right in kb[rights_key]:
            lines.append(f"  ✓ {right}")
        lines.append("")

    lines.append(
        "INSTRUCTION: For EVERY risk you flag, cite the specific law and section number. "
        "Use format: 'This violates Section X, [Law Name]' or 'Under [Law], [rule]'. "
        "Never give generic risk warnings — always tie to an actual Indian law."
    )

    return "\n".join(lines)


def get_state_variations(document_type: str) -> str | None:
    """Return state-specific variations if they exist for the document type."""
    kb = _find_kb_entry(document_type)
    if not kb or "state_variations" not in kb:
        return None

    lines = ["STATE-SPECIFIC RULES (mention if you can identify the state from the document):"]
    for state, rule in kb["state_variations"].items():
        lines.append(f"  {state}: {rule}")
    return "\n".join(lines)


def get_violation_check(clause_text: str, document_type: str) -> list[dict]:
    """
    Quick keyword scan to find potential law violations in a clause.
    Returns list of matching rules for the AI to elaborate on.
    
    This is NOT a replacement for AI analysis — it's a pre-scan to
    help the AI know which laws to check.
    """
    kb = _find_kb_entry(document_type)
    if not kb:
        return []

    clause_lower = clause_text.lower()
    violations = []

    for rule in kb.get("rules", []):
        keywords = rule.get("violation_keywords", [])
        if any(kw in clause_lower for kw in keywords):
            violations.append({
                "topic": rule["topic"],
                "law": rule["law"],
                "risky_if": rule["risky_if"],
                "safe_if": rule["safe_if"],
            })

    return violations


# ─── Internal helpers ─────────────────────────────────────────────────────────

_TYPE_MAP = {
    # Rental variants
    "rental agreement": "rental",
    "lease agreement": "rental",
    "rent agreement": "rental",
    "leave and license": "rental",
    "tenancy agreement": "rental",
    "lease deed": "rental",
    # Employment variants
    "employment contract": "employment",
    "offer letter": "employment",
    "appointment letter": "employment",
    "service agreement": "employment",
    "work contract": "employment",
    # Loan variants
    "loan agreement": "loan",
    "credit agreement": "loan",
    "mortgage deed": "loan",
    "hypothecation": "loan",
    "promissory note": "loan",
    # Property variants
    "sale deed": "property_sale",
    "sale agreement": "property_sale",
    "agreement to sell": "property_sale",
    "purchase agreement": "property_sale",
    "conveyance deed": "property_sale",
    # Service variants
    "service contract": "service",
    "freelance agreement": "service",
    "consulting agreement": "service",
    "vendor agreement": "service",
    # Court variants
    "fir": "court",
    "charge sheet": "court",
    "legal notice": "court",
    "court summons": "court",
    "bail application": "court",
    "civil suit": "court",
    # Family variants
    "divorce petition": "family",
    "maintenance order": "family",
    "alimony agreement": "family",
    "custody agreement": "family",
    # Insurance variants
    "insurance policy": "insurance",
    "claim rejection": "insurance",
    # Consumer variants
    "terms of service": "consumer",
    "terms and conditions": "consumer",
    "consumer agreement": "consumer",
}


def _find_kb_entry(document_type: str) -> dict | None:
    """Find KB entry for a document type string (case-insensitive fuzzy match)."""
    if not document_type:
        return None

    doc_lower = document_type.lower().strip()

    # Direct key match
    if doc_lower in INDIAN_LAW_KB:
        return INDIAN_LAW_KB[doc_lower]

    # Exact map match
    if doc_lower in _TYPE_MAP:
        return INDIAN_LAW_KB.get(_TYPE_MAP[doc_lower])

    # Partial map match
    for key, kb_key in _TYPE_MAP.items():
        if key in doc_lower or doc_lower in key:
            return INDIAN_LAW_KB.get(kb_key)

    # Partial direct key match
    for kb_key in INDIAN_LAW_KB:
        if kb_key in doc_lower:
            return INDIAN_LAW_KB[kb_key]

    return None


def _generic_law_context() -> str:
    return """INDIAN LAW CONTEXT:

Key Laws to reference in your analysis:
  • Indian Contract Act 1872 — governs all contracts; Section 23 (unlawful consideration), Section 27 (void agreements in restraint of trade)
  • Consumer Protection Act 2019 — protects consumers from unfair contract terms
  • Arbitration and Conciliation Act 1996 — dispute resolution
  • Limitation Act 1963 — time limits for legal action

INSTRUCTION: For every risk you flag, cite the specific Indian law and section number.
Never give generic risk warnings — always tie to an actual Indian law."""


def get_statute_by_keyword(query: str) -> list[dict]:
    query_lower = query.lower()
    results = []
    for doc_type, data in INDIAN_LAW_KB.items():
        for rule in data.get("rules", []):
            topic = rule.get("topic", "")
            law = rule.get("law", "")
            if any(k in query_lower for k in rule.get("violation_keywords", [])) or query_lower in topic.lower() or query_lower in law.lower():
                results.append({
                    "title": topic,
                    "act": law,
                    "summary": rule.get("rule", ""),
                    "doc_type": doc_type
                })
    return results


def get_relevant_acts(doc_type: str) -> list[str]:
    kb = INDIAN_LAW_KB.get(doc_type.lower(), {})
    return kb.get("primary_laws", ["Indian Contract Act, 1872"])
