"""
Business License Hub Knowledge Base for SmartLegal-AI Phase 4C.

Complete guidance platform for 9 Indian business registration types:
- GST Registration (Goods & Services Tax)
- FSSAI Registration (Food Safety & Standards Authority of India)
- MSME/Udyam Registration (Micro, Small, Medium Enterprises)
- Shop & Establishment Registration (State-Level Business License)
- IEC (Import Export Code) Registration
- Trade License (Municipal Corporation)
- Professional Tax Registration
- PAN/TAN Registration (Permanent Account Number / Tax Account Number)
- Startup India Registration

All data is static, verified, and deterministic.
Sources: Official government portals, GSTN, FSSAI, Udyam portal, ministry websites.
"""

BUSINESS_KB = {
    "gst": {
        "display_name": "GST Registration",
        "icon": "📊",
        "authority": "Central Board of Indirect Taxes & Customs (CBIC) / State Tax Authority",
        "governing_law": "Goods and Services Tax Act, 2017; GST Rules, 2017",
        "official_portal": "https://www.gst.gov.in (National GST Portal) — online registration & compliance",
        "overview": "Complete guide to registering for GST (Goods and Services Tax). GST is a unified indirect tax on the supply of goods and services. Registration is mandatory if annual turnover exceeds ₹20 lakh (₹10 lakh for NE states). Essential for any business dealing in goods/services across India.",

        "services": [
            {
                "service": "Determine GST Registration Eligibility",
                "description": "Check if your business meets GST registration threshold based on annual turnover.",
                "where": "Self-assessment or CA consultation",
                "documents_required": [
                    "Business type (sole proprietor, partnership, company, etc.)",
                    "Estimated annual turnover",
                    "Business location (state)",
                ],
                "fee": "Free (assessment)",
                "timeline": "1–2 hours",
                "official_link": "https://www.gst.gov.in/",
            },
            {
                "service": "Apply for GST Registration Online",
                "description": "Submit GST application through the GST portal with business and personal details.",
                "where": "GST portal (https://www.gst.gov.in) — online registration",
                "documents_required": [
                    "PAN (Permanent Account Number) of proprietor/partners/directors",
                    "Aadhaar of all stakeholders",
                    "Business registration documents (if registered entity: certificate of incorporation, MOA/AOA)",
                    "Proof of business premises (lease deed, ownership proof, utility bill)",
                    "Proof of personal identity (Aadhaar, PAN, DL, Passport)",
                    "Proof of residence (utility bill, rental agreement, property tax receipt)",
                    "Bank account details (business or personal)",
                ],
                "fee": "Free (registration)",
                "timeline": "1–3 working days for provisional GST; 7–14 days for final registration",
                "official_link": "https://www.gst.gov.in/new-registration",
            },
            {
                "service": "Get Provisional GST & Final GST Certificate",
                "description": "Receive provisional GST (PRN) immediately; final GST certificate after verification.",
                "where": "GST portal (automatic issuance after application approval)",
                "documents_required": [
                    "Approved application reference",
                    "Identity proof",
                ],
                "fee": "No fee",
                "timeline": "Immediate (provisional); 7–14 days (final certificate)",
                "official_link": "https://www.gst.gov.in/",
            },
            {
                "service": "File GST Returns (GSTR-1, GSTR-3B, etc.)",
                "description": "File monthly/quarterly GST return summarizing sales and purchases.",
                "where": "GST portal (online return filing)",
                "documents_required": [
                    "GST registration number",
                    "Sales invoices (GSTR-1: outward supplies)",
                    "Purchase invoices (GSTR-2: inward supplies)",
                    "Bank statements and payment records",
                ],
                "fee": "No filing fee; late filing penalty: ₹100–₹500 per day (capped)",
                "timeline": "Monthly GSTR-3B (by 20th of following month); GSTR-1 (monthly)",
                "official_link": "https://www.gst.gov.in/",
            },
            {
                "service": "Claim Input Tax Credit (ITC)",
                "description": "Claim credit for GST paid on business purchases (reduce GST liability).",
                "where": "GST return filing (GSTR-3B, GSTR-1)",
                "documents_required": [
                    "Invoices from GST-registered suppliers",
                    "Proof of payment (bank statements)",
                    "GST certificate of suppliers (to verify they're registered)",
                ],
                "fee": "No fee; improper ITC claim can attract ₹500–₹10,000 penalty",
                "timeline": "Claimed in monthly GSTR-3B; processed by tax officer",
                "official_link": "https://www.gst.gov.in/",
            },
            {
                "service": "Amend GST Registration Details",
                "description": "Update business address, partner details, or turnover classification.",
                "where": "GST portal (online amendment form)",
                "documents_required": [
                    "GST registration number",
                    "Reason for amendment",
                    "Updated documents (if address change: utility bill; if partner change: deed)",
                    "Identity proof",
                ],
                "fee": "No fee",
                "timeline": "1–5 working days",
                "official_link": "https://www.gst.gov.in/",
            },
            {
                "service": "Deregister or Surrender GST Registration",
                "description": "Surrender GST if business is closed or doesn't qualify for GST.",
                "where": "GST portal (deregistration form)",
                "documents_required": [
                    "GST registration number",
                    "Final return & tax clearance",
                    "Proof of business closure or non-qualification",
                ],
                "fee": "No fee; pending tax liability must be cleared before deregistration",
                "timeline": "30 days for deregistration after application",
                "official_link": "https://www.gst.gov.in/",
            },
        ],

        "faqs": [
            {
                "q": "What is GST and why is it important?",
                "a": "GST (Goods and Services Tax) is a unified indirect tax on the supply of goods and services. It replaced older taxes like VAT, excise, service tax. GST registration is mandatory for businesses exceeding ₹20 lakh turnover (₹10 lakh for NE states, Sikkim, Uttarakhand). It simplifies interstate transactions and provides input tax credit benefit."
            },
            {
                "q": "Is GST registration mandatory for all businesses?",
                "a": "No. Registration is mandatory only if annual turnover exceeds ₹20 lakh (₹10 lakh for specific states). Small businesses below threshold can apply voluntarily. Even if not mandatory, GST registration helps in B2B sales and ITC claims."
            },
            {
                "q": "How long does GST registration take?",
                "a": "Typically 1–3 days for provisional GST (PRN issued immediately). Final GST certificate takes 7–14 days after verification by tax officer. Online portal is real-time; delays rare unless documents are incomplete."
            },
            {
                "q": "Can a sole proprietor and company operate under same GST?",
                "a": "No. Each legal entity needs separate GST registration. If you're sole proprietor and later form a company, both need separate GST numbers. You cannot merge GST registrations."
            },
            {
                "q": "What happens if I don't file GST return on time?",
                "a": "Late filing attracts penalties: ₹100 per day (capped at ₹5,000 or ITC amount, whichever is higher). If invoice details don't match between supplier's GSTR-1 and buyer's GSTR-2, system flags discrepancies for reconciliation."
            },
        ],

        "common_issues": [
            "Application rejected due to Aadhaar/PAN mismatch — verify details with UIDAI/IT dept; resubmit with corrected documents",
            "Provisional GST issued but final GST delayed — follow up with field officer; provide missing documents; request status update via portal grievance",
            "ITC wrongly denied due to supplier's inactive GST — verify supplier's GST status; claim after supplier reactivates or obtain alternate invoice",
            "GSTR-1 and GSTR-2 mismatch causing return rejection — match invoice details; request supplier to correct GSTR-1; file amended return",
            "Unable to link Aadhaar with GST — ensure Aadhaar is updated with current details; verify with UIDAI; re-authenticate on GST portal",
        ],

        "legal_protections": [
            "Goods and Services Tax Act, 2017 — defines registration, compliance, penalties; appeals available to appellate authority",
            "GST Rules, 2017 — detailed procedures for registration, filing, ITC, audits; compliance mandatory",
            "Right to Information Act, 2005 — applicant can RTI for GST registration status, assessment details, or audit reports",
            "Alternate Dispute Resolution — GST disputes can be resolved via advance rulings or appellate authority without court litigation",
        ],

        "disclaimer": "This guidance is for informational purposes only and does not constitute legal or tax advice. GST rules, turnover thresholds, and compliance procedures vary by state and business type. We strongly recommend consulting a chartered accountant or GST consultant before registration and for ongoing compliance, especially regarding ITC claims, return filing, and audit requirements.",
    },

    "fssai": {
        "display_name": "FSSAI Registration",
        "icon": "🍔",
        "authority": "Food Safety and Standards Authority of India (FSSAI)",
        "governing_law": "Food Safety and Standards Act, 2006; Food Safety and Standards Rules, 2011",
        "official_portal": "https://fssairegistration.fssai.gov.in/ (FSSAI online portal)",
        "overview": "Complete guide to FSSAI registration for food businesses. Mandatory for all food manufacturing, processing, distribution, and retail businesses in India. FSSAI ensures food safety, hygiene, and quality standards.",

        "services": [
            {
                "service": "Determine FSSAI License Category",
                "description": "Identify if your food business needs Basic, State, or Central license based on type and turnover.",
                "where": "Self-assessment or FSSAI guidance",
                "documents_required": [
                    "Type of food business (manufacture, processing, distribution, retail)",
                    "Annual turnover",
                    "Food products handled",
                ],
                "fee": "Free (assessment)",
                "timeline": "1–2 hours",
                "official_link": "https://fssairegistration.fssai.gov.in/",
            },
            {
                "service": "Register for FSSAI Basic License",
                "description": "Online registration for small food businesses (retail, small manufacturing) with turnover <₹50 lakh.",
                "where": "FSSAI online portal (https://fssairegistration.fssai.gov.in/)",
                "documents_required": [
                    "Business ownership proof (sole proprietor: PAN/Aadhaar; company: certificate of incorporation)",
                    "Proof of business premises (lease deed, ownership, utility bill)",
                    "Photo of premises/business location",
                    "Identity & address proof of owner (Aadhaar, DL, Passport)",
                    "Food safety plan/hygiene certificate (if available)",
                    "Proof of water/food storage facilities",
                ],
                "fee": "Basic License: ₹500–₹1,000 (one-time); valid for 5 years",
                "timeline": "7–14 days for approval after application",
                "official_link": "https://fssairegistration.fssai.gov.in/",
            },
            {
                "service": "Apply for FSSAI State License",
                "description": "Registration for medium food businesses (manufacturing, processing) with turnover ₹50 lakh–₹20 crore.",
                "where": "State FSSAI office or online portal",
                "documents_required": [
                    "Business registration (partnership deed, MOA/AOA for companies)",
                    "Factory license or shop & establishment registration",
                    "Building plan approval (if manufacturing)",
                    "Proof of business premises (lease/ownership documents)",
                    "Environmental compliance certificate (if applicable)",
                    "Food handler's training certificate",
                    "Identity & address proof of all partners/directors",
                    "Audited financial statements (if turnover >₹5 lakh)",
                ],
                "fee": "State License: ₹2,000–₹5,000 (one-time); valid for 5 years",
                "timeline": "30–45 days for approval (includes inspection)",
                "official_link": "https://fssairegistration.fssai.gov.in/",
            },
            {
                "service": "Apply for FSSAI Central License",
                "description": "Registration for large food businesses (manufacturing, exporting) with turnover >₹20 crore or multi-state operations.",
                "where": "Central FSSAI office, New Delhi or state office",
                "documents_required": [
                    "Business registration documents (certificate of incorporation, partnership deed)",
                    "Factory license & building approvals",
                    "Environmental clearance (if required)",
                    "Proof of business premises & facilities",
                    "Quality assurance & food safety management system (ISO, HACCP)",
                    "Audited financial statements",
                    "List of food products & manufacturing process",
                    "Identity & address proof of key personnel",
                ],
                "fee": "Central License: ₹5,000–₹10,000 (one-time); valid for 5 years",
                "timeline": "60–90 days (includes inspection by FSSAI)",
                "official_link": "https://fssairegistration.fssai.gov.in/",
            },
            {
                "service": "Renew FSSAI License",
                "description": "Renew license 6 months before expiry to avoid business closure.",
                "where": "FSSAI online portal or state FSSAI office",
                "documents_required": [
                    "Existing license number",
                    "Compliance report (food safety audit if required)",
                    "Updated business & premises details (if changed)",
                    "Renewal fee payment",
                ],
                "fee": "Same as original license (₹500–₹10,000)",
                "timeline": "10–30 days for renewal after application",
                "official_link": "https://fssairegistration.fssai.gov.in/",
            },
            {
                "service": "Amend FSSAI License Details",
                "description": "Update business address, partners, product list, or manufacturing process.",
                "where": "FSSAI online portal or state office",
                "documents_required": [
                    "License number",
                    "Reason for amendment",
                    "Updated documents (proof of new address, deed, etc.)",
                ],
                "fee": "₹100–₹500 (amendment fee, state-dependent)",
                "timeline": "5–15 days",
                "official_link": "https://fssairegistration.fssai.gov.in/",
            },
        ],

        "faqs": [
            {
                "q": "Is FSSAI license mandatory for all food businesses?",
                "a": "Yes. Any business involved in manufacturing, processing, distribution, storage, or retail of food in India requires FSSAI registration or license. Only exempted: very small informal food sellers in some states (check with state FSSAI). Organized retail/e-commerce always require FSSAI."
            },
            {
                "q": "What's the difference between FSSAI registration and license?",
                "a": "Basic License is 'registration' for small businesses; State/Central Licenses are formal licenses for larger businesses. Basic License is simpler, faster, lower-fee; State/Central licenses have stricter standards & inspections but no turnover limit for multi-state operations."
            },
            {
                "q": "How long does FSSAI license take?",
                "a": "Basic License: 7–14 days. State License: 30–45 days (includes inspection). Central License: 60–90 days (includes FSSAI inspection). Online portal processes applications in real-time; inspection delays are main factor."
            },
            {
                "q": "What if FSSAI inspection fails?",
                "a": "If non-compliant areas found, FSSAI issues list of defects. You have 7–14 days to rectify & resubmit. Common issues: poor hygiene, incorrect food labels, improper storage, unauthorized additives. Rectify & reapply; rejection rare if corrected."
            },
            {
                "q": "Can I operate food business without FSSAI?",
                "a": "No. Operating without FSSAI is illegal; penalties: ₹1,000–₹5,000 fine or 6 months imprisonment (first offense). Repeat offense: up to ₹10,000 fine or 2 years imprisonment. Health department can shut down business."
            },
        ],

        "common_issues": [
            "Application rejected due to unhygienic premises — improve sanitation, water quality, storage; photographic evidence; reapply after upgrades",
            "Food safety audit failed — hire FSSAI-approved food safety consultant; implement HACCP/GMP; resubmit with compliance proof",
            "Unable to obtain building plan approval — apply to municipal corporation separately; provide proposed food business layout; separate approval needed",
            "Food handler training certificate not recognized — enroll in FSSAI-approved training course; obtain official certificate from approved trainer",
            "Inspection pending for 3+ months — follow up with state FSSAI office; escalate if unreasonable delay; provide additional compliance documents",
        ],

        "legal_protections": [
            "Food Safety and Standards Act, 2006 — defines FSSAI registration requirements, penalties for non-compliance; appeals available",
            "Food Safety and Standards Rules, 2011 — detailed standards for food manufacturing, labeling, packaging, storage; compliance mandatory",
            "Right to Information Act, 2005 — applicant can RTI for inspection reports, license status, or compliance details",
            "Consumer Protection Act, 2019 — applies to food quality disputes; consumers can claim damages for unsafe food",
        ],

        "disclaimer": "This guidance is for informational purposes only and does not constitute legal advice. FSSAI requirements, license categories, fees, and inspection standards vary by state and food product type. We strongly recommend consulting an FSSAI-certified food safety consultant before application, especially for manufacturing/processing businesses, to ensure full compliance with food safety standards and regulations.",
    },

    "msme": {
        "display_name": "MSME / Udyam Registration",
        "icon": "🏭",
        "authority": "Ministry of MSME, Government of India",
        "governing_law": "Micro, Small & Medium Enterprises Development Act, 2006; Udyam Registration Scheme, 2020",
        "official_portal": "https://udyamregistration.gov.in/ (Udyam online registration)",
        "overview": "Complete guide to MSME/Udyam registration. Essential for all small & medium businesses to access government subsidies, loans, tax benefits, and procurement preferences. Replaces old MSME classification system with simpler Udyam registration.",

        "services": [
            {
                "service": "Determine MSME Category & Udyam Eligibility",
                "description": "Check if your business qualifies as Micro, Small, or Medium Enterprise based on investment & turnover.",
                "where": "Self-assessment or business consultant",
                "documents_required": [
                    "Annual turnover or investment in plant & machinery",
                    "Type of business (manufacturing, services, trading)",
                ],
                "fee": "Free",
                "timeline": "1 hour",
                "official_link": "https://udyamregistration.gov.in/",
            },
            {
                "service": "Register for Udyam (Online Registration)",
                "description": "Free online registration via Udyam portal using Aadhaar and PAN.",
                "where": "Udyam registration portal (https://udyamregistration.gov.in/)",
                "documents_required": [
                    "Aadhar number of proprietor/partners",
                    "PAN (Permanent Account Number)",
                    "Proof of business premises (lease/ownership)",
                    "Bank account details",
                    "Type of business & business description",
                    "Annual turnover or investment details",
                ],
                "fee": "Free",
                "timeline": "Instant registration; certificate issued immediately",
                "official_link": "https://udyamregistration.gov.in/",
            },
            {
                "service": "Obtain Udyam Registration Certificate",
                "description": "Get official Udyam certificate and registration number (UR ID).",
                "where": "Automatic on portal after registration completion",
                "documents_required": [
                    "Approved registration",
                    "Identity proof",
                ],
                "fee": "No fee",
                "timeline": "Instant upon registration completion",
                "official_link": "https://udyamregistration.gov.in/",
            },
            {
                "service": "Access Government Schemes & Subsidies",
                "description": "Leverage Udyam registration to claim government benefits (credit, subsidies, procurement preference).",
                "where": "Government ministry websites & SIDBI (Small Industries Development Bank of India)",
                "documents_required": [
                    "Udyam registration certificate",
                    "Business financial statements",
                    "Bank account proof",
                ],
                "fee": "Scheme-dependent (mostly free or subsidized)",
                "timeline": "Varies by scheme (1–30 days)",
                "official_link": "https://www.sidbi.in/",
            },
            {
                "service": "Update Udyam Registration Details",
                "description": "Modify business name, activity type, investment, or turnover.",
                "where": "Udyam portal (online update)",
                "documents_required": [
                    "Udyam registration number (UR ID)",
                    "Updated business details",
                    "Supporting documents (if investment/turnover changed)",
                ],
                "fee": "Free",
                "timeline": "Instant to 1 day",
                "official_link": "https://udyamregistration.gov.in/",
            },
            {
                "service": "Claim Government Procurement Preference",
                "description": "Get preference for government tenders & procurement as MSME.",
                "where": "Government e-procurement portals (GeM, tender portal)",
                "documents_required": [
                    "Udyam certificate",
                    "Business registration (if applicable)",
                    "GST registration (for contracts >₹50,000)",
                ],
                "fee": "No fee; savings from exemption/concessions in government procurement",
                "timeline": "Automatic after Udyam registration",
                "official_link": "https://gem.gov.in/",
            },
        ],

        "faqs": [
            {
                "q": "What is Udyam and why is it important?",
                "a": "Udyam is the new unified system for MSME registration (replaces old MSME certificate). It simplifies classification into Micro, Small, Medium based on investment or turnover. Udyam is free, instant, and gives access to government schemes: credit, subsidies, tax benefits, procurement preference."
            },
            {
                "q": "Is Udyam registration mandatory?",
                "a": "Not legally mandatory, but practically essential. To claim government benefits (CGTMSE credit guarantee, Credit Guarantee Fund subsidy, procurement preference, etc.), Udyam is required. Highly recommended for all small businesses."
            },
            {
                "q": "How long does Udyam registration take?",
                "a": "Instant. Once you fill online form with Aadhaar and PAN, registration is immediate and certificate is downloadable. No waiting period; no approval required."
            },
            {
                "q": "What's the difference between Micro, Small, and Medium?",
                "a": "Micro: investment <₹25 lakh or turnover <₹5 crore. Small: investment ₹25 lakh–₹5 crore or turnover ₹5–₹50 crore. Medium: investment ₹5–₹10 crore or turnover ₹50–₹250 crore. Classification determines loan limits, subsidy amounts, tax benefits."
            },
            {
                "q": "Can I update Udyam if business turnover increases?",
                "a": "Yes. You can update Udyam details anytime on the portal. If business grows to Medium size, update investment/turnover; new benefits automatically apply."
            },
        ],

        "common_issues": [
            "Aadhaar authentication fails on Udyam portal — verify Aadhaar is linked to PAN; try again; contact UIDAI if persistent",
            "PAN not recognized in Udyam system — ensure PAN is recent & correct; apply for new PAN if never used; retry on portal",
            "Unable to access SIDBI loans despite Udyam registration — contact bank directly; ensure Udyam is linked to bank account; provide all required documents",
            "GeM procurement tender rejected due to Udyam category mismatch — verify your category matches tender requirement; update if necessary; reapply",
            "Udyam certificate not updating after registration — refresh browser; download directly from portal if not auto-emailed",
        ],

        "legal_protections": [
            "Micro, Small & Medium Enterprises Development Act, 2006 — establishes MSME definitions, government support, credit guarantee schemes",
            "Udyam Registration Scheme, 2020 — simplifies MSME registration; registration is free and instant",
            "PMMY (Pradhan Mantri Mudra Yojana) — guarantees loans up to ₹10 lakh for MSMEs without collateral; Udyam registration helps",
            "TReDS Platform — enables MSMEs to get discounted financing on receivables; Udyam registration required",
        ],

        "disclaimer": "This guidance is for informational purposes only and does not constitute business or financial advice. Government schemes, loan limits, and subsidy amounts change periodically. We strongly recommend consulting a business development consultant or visiting ministry websites for current scheme details before applying. Eligibility criteria vary by scheme; verify before claiming benefits.",
    },

    "shop_establishment": {
        "display_name": "Shop & Establishment Registration",
        "icon": "🏪",
        "authority": "State Labour Department / Municipal Corporation",
        "governing_law": "State Shop and Establishment Act (varies by state: Maharashtra, Karnataka, etc.); National legislation guidance from Ministry of Labour",
        "official_portal": "State-specific online portals (Maharashtra: https://shops.mahaonline.gov.in/)",
        "overview": "Complete guide to Shop & Establishment registration. Mandatory for all retail shops, restaurants, offices, and workplaces in India. Regulates working hours, wages, safety, and working conditions.",

        "services": [
            {
                "service": "Understand Shop & Establishment Requirements",
                "description": "Learn if your business needs Shop & Establishment license and what it covers.",
                "where": "Self-education or state labour office",
                "documents_required": [
                    "Type of business (shop, restaurant, office, factory)",
                    "Number of employees",
                    "Business address",
                ],
                "fee": "Free",
                "timeline": "1–2 hours",
                "official_link": "https://shops.mahaonline.gov.in/",
            },
            {
                "service": "Apply for Shop & Establishment Registration Online",
                "description": "Submit application through state portal with business and employee details.",
                "where": "State labour department online portal (state-specific)",
                "documents_required": [
                    "Ownership proof (PAN, Aadhaar, partnership deed, incorporation certificate)",
                    "Proof of business premises (lease deed, ownership, property tax receipt, utility bill)",
                    "Address proof of proprietor (Aadhaar, DL, Passport)",
                    "Identity proof (Aadhaar, PAN, DL)",
                    "List of employees & their identity proof",
                    "Business activity description",
                    "Workplace layout/floor plan (for offices & factories)",
                    "Photo of business premises",
                ],
                "fee": "Registration fee: ₹500–₹2,000 (state-dependent); annual renewal: ₹500–₹1,000",
                "timeline": "10–20 days after application",
                "official_link": "https://shops.mahaonline.gov.in/",
            },
            {
                "service": "Obtain Shop & Establishment License",
                "description": "Get official license certificate and registration number after approval.",
                "where": "State labour office (after approval on portal)",
                "documents_required": [
                    "Approved application reference",
                    "Identity proof",
                    "Registration fee payment receipt",
                ],
                "fee": "Included in registration fee",
                "timeline": "Issued immediately after approval",
                "official_link": "https://shops.mahaonline.gov.in/",
            },
            {
                "service": "Renew Shop & Establishment Registration",
                "description": "Renew annual license before expiry (usually every year or 5 years).",
                "where": "State labour online portal",
                "documents_required": [
                    "License number",
                    "Updated employee list (if changed)",
                    "Renewal fee payment",
                    "Updated business premises proof (if relocated)",
                ],
                "fee": "Annual renewal: ₹500–₹1,000",
                "timeline": "5–10 days for renewal after application",
                "official_link": "https://shops.mahaonline.gov.in/",
            },
            {
                "service": "Comply with Shop & Establishment Rules",
                "description": "Understand working hours, wage, leave, and safety requirements under the act.",
                "where": "State labour department website or manual",
                "documents_required": [
                    "Copy of Shop & Establishment Act (state-specific)",
                    "Workplace inspection checklist",
                ],
                "fee": "Free (guidance)",
                "timeline": "2–4 hours for understanding",
                "official_link": "https://shops.mahaonline.gov.in/",
            },
            {
                "service": "Amend Registration (Employee/Address Changes)",
                "description": "Update license if business address, employees, or activity type changes.",
                "where": "State labour online portal",
                "documents_required": [
                    "License number",
                    "Reason for amendment (address/employee change)",
                    "Updated documents (new address proof, new employee details)",
                ],
                "fee": "₹100–₹500 (amendment fee, state-dependent)",
                "timeline": "5–15 days",
                "official_link": "https://shops.mahaonline.gov.in/",
            },
        ],

        "faqs": [
            {
                "q": "Who needs Shop & Establishment registration?",
                "a": "All businesses with employees (retail, restaurant, office, factory, workshop). Even solo business with 1 helper needs registration. Home-based freelancers with no employees may be exempt (check state rules)."
            },
            {
                "q": "What happens if I don't register?",
                "a": "Non-registration is illegal; penalties: ₹1,000–₹5,000 fine or 3 months imprisonment (first offense); closure of business. Labour department conducts surprise inspections; non-compliance results in hefty penalties."
            },
            {
                "q": "Is registration the same for all states?",
                "a": "No. Each state has its own Shop & Establishment Act (Maharashtra, Karnataka, Gujarat, etc.). Requirements, fees, renewal period, and working hour limits vary by state. Check your state labour department portal."
            },
            {
                "q": "What's the renewal cycle — annual or 5-year?",
                "a": "Varies by state. Most states require annual renewal (every 31 Dec or business anniversary). Some allow 5-year renewal. Check your state labour department for exact renewal date."
            },
            {
                "q": "Do I need separate registration for each shop location?",
                "a": "Yes. Each business location (shop, office, factory) needs separate registration under its own license number. If you have multiple outlets, register each separately."
            },
        ],

        "common_issues": [
            "Application rejected due to proof of premises issue — provide alternative proof (utility bill, property tax, insurance); resubmit",
            "Employee list disputes with inspector — maintain current employee register; provide salary records; resolve discrepancies with inspector",
            "Late renewal penalty applied — renew before expiry; if delayed, pay penalty; submit late renewal application immediately",
            "Cannot access state portal (technical issues) — visit labour office in person with documents; manual application available",
            "Inspection failure due to safety non-compliance — rectify safety issues (first aid box, emergency exits, etc.); call for re-inspection after compliance",
        ],

        "legal_protections": [
            "State Shop & Establishment Act — governs working hours, leave, wages, safety; defines employer/employee obligations",
            "Ministry of Labour guidelines — national framework for state-specific acts; appeals available",
            "Right to Information Act, 2005 — applicant can RTI for inspection reports or license status",
            "Labour Codes (2020, 2023) — newer unified labour codes gradually replacing state acts; provide worker protections",
        ],

        "disclaimer": "This guidance is for informational purposes only and does not constitute legal advice. Shop & Establishment requirements, fees, and compliance standards vary significantly by state and type of business. We strongly recommend consulting your state labour department or a labour law advocate to ensure full compliance, especially regarding working hours, wage regulations, and employee safety requirements.",
    },

    "iec": {
        "display_name": "IEC (Import Export Code) Registration",
        "icon": "📦",
        "authority": "DGFT (Directorate General of Foreign Trade), Ministry of Commerce & Industry",
        "governing_law": "Foreign Trade Policy, 2015; DGFT Handbook of Procedures; Customs Act, 1962",
        "official_portal": "https://ecommerce.dgft.gov.in/ (IEC registration portal)",
        "overview": "Complete guide to IEC (Import Export Code) registration. Mandatory for any business importing or exporting goods from India. IEC is a 10-digit identification number issued by DGFT; essential for customs clearance, shipping, and FDI applications.",

        "services": [
            {
                "service": "Understand IEC Eligibility & Categories",
                "description": "Check if your business needs IEC and what type (manufacturer, trader, individual, etc.).",
                "where": "Self-assessment or DGFT guidance",
                "documents_required": [
                    "Business type (manufacturing, trading, services, etc.)",
                    "Import/export product category",
                ],
                "fee": "Free",
                "timeline": "1 hour",
                "official_link": "https://ecommerce.dgft.gov.in/",
            },
            {
                "service": "Apply for IEC Online (e-filing via DGFT)",
                "description": "File IEC application online through DGFT portal with business and financial details.",
                "where": "IEC portal (https://ecommerce.dgft.gov.in/)",
                "documents_required": [
                    "Business registration (if company: MOA/AOA; if partnership: deed; if sole: PAN)",
                    "PAN certificate (individual/proprietor or entity)",
                    "Bank details & account proof",
                    "Proof of business premises (lease/ownership, utility bill)",
                    "Address proof of proprietor/director (Aadhaar, DL, Passport)",
                    "Passport copy (if applicant is NRI)",
                    "Factory/office photos (if manufacturing)",
                    "List of import/export goods & HS codes",
                ],
                "fee": "No fee (IEC registration is free)",
                "timeline": "1–3 working days (almost instant if documents are digital and verified)",
                "official_link": "https://ecommerce.dgft.gov.in/",
            },
            {
                "service": "Obtain IEC Number & Certificate",
                "description": "Get 10-digit IEC number (import export code) immediately after approval.",
                "where": "Automatic issuance via DGFT portal",
                "documents_required": [
                    "Approved application",
                    "Identity proof for download",
                ],
                "fee": "No fee",
                "timeline": "Instant upon approval",
                "official_link": "https://ecommerce.dgft.gov.in/",
            },
            {
                "service": "Update IEC Registration (Name, Address, Product Category)",
                "description": "Modify IEC details if business name, location, or product changes.",
                "where": "IEC portal (online update form)",
                "documents_required": [
                    "IEC number",
                    "Updated business documents (deed, MOA, etc.)",
                    "Proof of updated address (if relocated)",
                ],
                "fee": "No fee",
                "timeline": "5–10 days for approval",
                "official_link": "https://ecommerce.dgft.gov.in/",
            },
            {
                "service": "Use IEC for Customs Clearance & Shipping",
                "description": "Present IEC to customs, shipping lines, and cargo agents for import/export transactions.",
                "where": "Port authority, customs, shipping company",
                "documents_required": [
                    "IEC certificate (physical or digital copy)",
                    "Commercial invoice, packing list, bill of lading (for each shipment)",
                ],
                "fee": "No fee; customs & shipping charges separate",
                "timeline": "Same-day submission at port/customs",
                "official_link": "https://ecommerce.dgft.gov.in/",
            },
        ],

        "faqs": [
            {
                "q": "What is IEC and who needs it?",
                "a": "IEC (Import Export Code) is a 10-digit identification number issued by DGFT for businesses importing or exporting goods. Mandatory for: manufacturers, traders, individuals engaging in import/export. Not needed for pure service export (IT, consulting) unless goods are also involved."
            },
            {
                "q": "Is IEC registration free?",
                "a": "Yes, completely free. DGFT issues IEC without any fee. Beware of agents charging fees; they're not authorized. Apply directly on DGFT portal."
            },
            {
                "q": "How long does IEC take to get?",
                "a": "1–3 working days from submission if documents are complete & digital. Almost instant in many cases. Processing is now fully automated on DGFT portal."
            },
            {
                "q": "Can individual apply for IEC or only companies?",
                "a": "Both individuals and companies can apply. Individuals need PAN, address proof, bank account. No minimum turnover or business size required."
            },
            {
                "q": "What if my product requires import license (like drugs, chemicals)?",
                "a": "IEC alone is not enough for restricted goods. Some products need additional licenses: DCGI approval (pharma), FSSAI (food), DGMS (mines), etc. Obtain product-specific license first, then IEC helps with customs clearance."
            },
        ],

        "common_issues": [
            "IEC application rejected due to PAN issues — verify PAN is 10 digits & in GSTIN/tax database; obtain new PAN if outdated; resubmit",
            "Portal technical issues during filing — try again later; use Chrome/Firefox browser; enable JavaScript; clear cache if persistent",
            "Bank details not matching NEFT records — ensure bank account has been settled for 1–2 months; verify account with bank; update if needed; resubmit",
            "Cannot download IEC certificate — IEC number issued but certificate needs manual download; log in portal, go to 'My IEC', download PDF",
            "Customs clearance delayed due to expired IEC — even though IEC has no expiry, verify if details match current business status; update if address changed; re-verify with customs",
        ],

        "legal_protections": [
            "Foreign Trade Policy, 2015 — establishes IEC requirements, eligible exporters, incentive schemes",
            "DGFT Handbook of Procedures — detailed IEC procedures, restricted items, documentation requirements",
            "Customs Act, 1962 — governs customs clearance using IEC; penalties for misuse or wrong HS codes",
            "Right to Information Act, 2005 — applicant can RTI for IEC processing status or queries",
        ],

        "disclaimer": "This guidance is for informational purposes only and does not constitute legal or trade advice. Some products are restricted for export/import and require separate licenses (pharma, chemicals, wildlife). We strongly recommend consulting a customs broker or trade consultant to ensure compliance with product-specific regulations before importing/exporting. HS code classification is critical for customs purposes; incorrect codes can delay shipments or result in penalties.",
    },

    "trade_license": {
        "display_name": "Trade License",
        "icon": "🏢",
        "authority": "Municipal Corporation / Municipal Council / Gram Panchayat (local authority)",
        "governing_law": "Municipal Corporation Act (varies by state); Municipal Solid Waste Management Rules; Local Bylaws",
        "official_portal": "Municipal corporation websites (state & city-specific); online systems vary",
        "overview": "Complete guide to Trade License registration. Mandatory for all businesses operating from a physical location (shop, factory, office, restaurant). Issued by local municipal authority; confirms business legitimacy and compliance with local regulations.",

        "services": [
            {
                "service": "Determine Trade License Category",
                "description": "Identify license type based on business activity (retail, manufacturing, restaurant, etc.).",
                "where": "Self-assessment or municipal office consultation",
                "documents_required": [
                    "Type of business",
                    "Business location (shop, factory, office)",
                    "Scale (small, medium, large)",
                ],
                "fee": "Free (assessment)",
                "timeline": "1 hour",
                "official_link": "Check your municipal corporation website",
            },
            {
                "service": "Apply for Trade License Online / Offline",
                "description": "Submit trade license application to municipal corporation with business details.",
                "where": "Municipal corporation online portal or office (city-dependent)",
                "documents_required": [
                    "Property ownership/lease deed (proof of business premises)",
                    "Property tax receipt or NOC from property owner",
                    "Identity & address proof of applicant (Aadhaar, DL, Passport)",
                    "PAN or business registration certificate",
                    "Building plan approval (if new construction)",
                    "Proof of water & electricity connection (utility bills)",
                    "Photos of business premises (exterior & interior)",
                    "List of employees (for large businesses)",
                    "Proposed business activity description",
                ],
                "fee": "₹500–₹5,000 (depends on business type & city; varies widely)",
                "timeline": "15–30 days after application (inspection required)",
                "official_link": "Check your city's municipal corporation website",
            },
            {
                "service": "Trade License Inspection & Verification",
                "description": "Municipal inspector verifies business premises compliance (hygiene, safety, space, etc.).",
                "where": "On-site at business premises",
                "documents_required": [
                    "All above documents at premises",
                    "Business setup as per application",
                ],
                "fee": "Included in license fee",
                "timeline": "1–2 weeks after application (inspector visit)",
                "official_link": "Check your city's municipal corporation website",
            },
            {
                "service": "Obtain Trade License Certificate",
                "description": "Get official trade license certificate after inspection approval.",
                "where": "Municipal corporation office (or online portal)",
                "documents_required": [
                    "Approved application reference",
                    "Identity proof",
                    "License fee payment receipt",
                ],
                "fee": "License fee (₹500–₹5,000) + processing fee",
                "timeline": "Issued same day or within 1–3 days after approval",
                "official_link": "Check your city's municipal corporation website",
            },
            {
                "service": "Renew Trade License Annually",
                "description": "Renew license each year before expiry to maintain legal operation.",
                "where": "Municipal corporation online portal or office",
                "documents_required": [
                    "Trade license number",
                    "Renewal fee",
                    "Updated business premises proof (if changed)",
                ],
                "fee": "Annual renewal fee (₹500–₹2,000, city-dependent)",
                "timeline": "5–15 days for renewal processing",
                "official_link": "Check your city's municipal corporation website",
            },
            {
                "service": "Amend Trade License (Business Activity / Location Change)",
                "description": "Update license if business activity or location changes.",
                "where": "Municipal corporation portal or office",
                "documents_required": [
                    "License number",
                    "Reason for amendment",
                    "Updated documents (new lease, address proof, etc.)",
                ],
                "fee": "₹100–₹500 (amendment fee, city-dependent)",
                "timeline": "5–10 days",
                "official_link": "Check your city's municipal corporation website",
            },
        ],

        "faqs": [
            {
                "q": "Is Trade License mandatory for all businesses?",
                "a": "Yes, for all businesses operating from a physical location (shop, factory, restaurant, office, salon, clinic). Home-based freelancers with no employees may be exempt (check local rules). Online businesses with no physical store may not need it."
            },
            {
                "q": "What happens if I operate without Trade License?",
                "a": "Illegal; penalties: ₹1,000–₹10,000 fine or 3–6 months imprisonment. Municipal authorities can seal/demolish unauthorized premises. Business operations cease until licensed."
            },
            {
                "q": "How long does Trade License take?",
                "a": "15–30 days from application. Timeline depends on: (1) document completeness, (2) inspector availability, (3) any objections from neighbors. Faster if all documents submitted at once."
            },
            {
                "q": "Can I operate before Trade License is issued?",
                "a": "No. Business can only legally operate after license is issued. However, you can apply immediately upon business setup; don't wait to start."
            },
            {
                "q": "What's the difference between Trade License and Shop & Establishment?",
                "a": "Trade License = municipal authorization to operate a business from that location. Shop & Establishment = labour law compliance (working hours, wages, safety). Both are needed for retail/restaurants. Trade License is for municipal/civic compliance; Shop Act is for worker protection."
            },
        ],

        "common_issues": [
            "Inspection failed due to hygiene/space issues — rectify defects within 7 days; call for re-inspection; most issues are correctable",
            "Neighbor objection to business (noise, traffic, etc.) — address concern (soundproofing, parking); obtain written no-objection from neighbor; resubmit",
            "Property owner refuses to sign — if you're the owner, provide ownership deed; if rented, persuade landlord or provide notarized authorization",
            "License fee unclear or unexpectedly high — verify on municipal portal; apply for fee waiver if eligible (micro business); appeal if over-charged",
            "License not renewed, operation sealed — pay renewal fee immediately with penalty; appeal for re-opening; avoid future delays",
        ],

        "legal_protections": [
            "Municipal Corporation Act (state-specific) — establishes trade license authority, fee structure, appeal process",
            "Municipal Solid Waste Management Rules, 2016 — governs waste management compliance for licensed businesses",
            "Right to Information Act, 2005 — applicant can RTI for inspection reports, fee details, or processing timeline",
            "Consumer Protection Act, 2019 — applies if municipal authority refuses license arbitrarily; remedy via consumer commission",
        ],

        "disclaimer": "This guidance is for informational purposes only and does not constitute legal advice. Trade license requirements, fees, renewal periods, and procedures vary significantly by city and municipal corporation. We strongly recommend verifying current requirements with your local municipal office or checking the municipal corporation website before applying, as rules change periodically and differ between urban, suburban, and rural areas.",
    },

    "professional_tax": {
        "display_name": "Professional Tax Registration",
        "icon": "💼",
        "authority": "State Commercial Tax Department / Revenue Department",
        "governing_law": "State Professional Tax Act (varies by state); Maharashtra Professional Tax Act, 1975 (as example)",
        "official_portal": "State-specific portals (Maharashtra: https://pt.mahavat.gov.in/)",
        "overview": "Complete guide to Professional Tax registration. Mandatory in states like Maharashtra, Karnataka, Gujarat, Telangana for individuals and businesses earning professional/business income. Annual tax on professionals (doctors, lawyers, CAs, business owners, consultants).",

        "services": [
            {
                "service": "Check Professional Tax Applicability",
                "description": "Determine if you need Professional Tax based on state and income category.",
                "where": "Self-assessment or state tax department",
                "documents_required": [
                    "State of operation",
                    "Type of profession/business",
                    "Annual income/turnover",
                ],
                "fee": "Free",
                "timeline": "1 hour",
                "official_link": "Check your state tax department website",
            },
            {
                "service": "Apply for Professional Tax Registration Online",
                "description": "File professional tax registration online through state portal.",
                "where": "State professional tax portal (state-specific)",
                "documents_required": [
                    "PAN (Permanent Account Number)",
                    "Aadhar number",
                    "Proof of professional qualification (degree, certificate, if applicable)",
                    "Proof of address (Aadhar, DL, Passport, property tax receipt)",
                    "Bank account details",
                    "Business address proof (lease/ownership)",
                    "Income declaration or ITR copy",
                ],
                "fee": "Annual tax: ₹0–₹2,500 (depends on state & income slab)",
                "timeline": "3–7 days for registration",
                "official_link": "State-specific portal",
            },
            {
                "service": "Get Professional Tax Registration Certificate",
                "description": "Obtain registration certificate after approval.",
                "where": "State tax portal (automatic) or office",
                "documents_required": [
                    "Approved application reference",
                    "Identity proof",
                ],
                "fee": "No additional fee",
                "timeline": "Issued 1–2 days after approval",
                "official_link": "State-specific portal",
            },
            {
                "service": "Pay Annual Professional Tax",
                "description": "Pay annual professional tax before deadline (usually Dec 31 in Maharashtra).",
                "where": "State tax portal or authorized bank",
                "documents_required": [
                    "Professional tax registration number",
                    "Annual tax payment amount",
                ],
                "fee": "Annual tax: ₹0–₹2,500 (state & income-dependent)",
                "timeline": "Annual payment; deadline varies by state",
                "official_link": "State-specific portal",
            },
            {
                "service": "Update Professional Tax Details (Income, Address)",
                "description": "Update registration if income or address changes.",
                "where": "State tax portal",
                "documents_required": [
                    "Registration number",
                    "Updated income details (ITR copy, if required)",
                    "Updated address proof (if relocated)",
                ],
                "fee": "No fee",
                "timeline": "5–10 days",
                "official_link": "State-specific portal",
            },
        ],

        "faqs": [
            {
                "q": "Is Professional Tax mandatory?",
                "a": "Yes in states that have Professional Tax Act (Maharashtra, Karnataka, Gujarat, Telangana, Punjab, etc.). Individuals and businesses with income/turnover above state's threshold must register. No exemption for most professions."
            },
            {
                "q": "What's the professional tax amount?",
                "a": "Varies by state & income. Maharashtra: ₹0–₹2,500 annually (income slab-based). Karnataka: ₹30–₹5,000. Check your state's slab. Tax increases with higher income."
            },
            {
                "q": "Who pays professional tax?",
                "a": "Individuals: doctors, lawyers, CAs, architects, engineers, consultants earning >threshold. Businesses: proprietors, partners, directors of companies in professional fields. Does NOT apply to pure trading/retail businesses in some states; check state rules."
            },
            {
                "q": "What if I don't pay professional tax?",
                "a": "Penalties: ₹100–₹1,000 fine, prosecution, attachment of property. State tax department can initiate recovery action. Best to register and pay on time."
            },
            {
                "q": "Is professional tax deductible in income tax?",
                "a": "Yes. Professional tax is allowed deduction under Section 36 of Income Tax Act. Reduces taxable income. Deduct in ITR filing."
            },
        ],

        "common_issues": [
            "Professional tax portal down or slow — contact state tax dept; manual registration available at office with same documents",
            "PAN not matching records — verify PAN is correct & updated; update with IT dept if outdated; re-register on portal",
            "Late payment penalty imposed — pay immediately with penalty; most states allow late payment for small fines",
            "Unable to determine if professional tax applies — consult CA for your profession & state; safer to register if turnover is close to threshold",
            "Registration rejected due to eligibility — appeal with income proof (ITR); some states have exemptions for small earners",
        ],

        "legal_protections": [
            "State Professional Tax Acts (e.g., Maharashtra Professional Tax Act, 1975) — defines applicability, rate, exemptions, appeal process",
            "Income Tax Act, 1961 — professional tax is deductible under Section 36, reducing taxable income",
            "Right to Information Act, 2005 — applicant can RTI for registration status or tax demand",
            "Consumer Protection Act, 2019 — applies if state tax authority acts arbitrarily; limited remedy available",
        ],

        "disclaimer": "This guidance is for informational purposes only and does not constitute tax or legal advice. Professional tax requirements, rates, thresholds, and deadlines vary significantly by state. Some states do not have professional tax; others have different rules for different professions. We strongly recommend consulting a Chartered Accountant or tax professional familiar with your state's laws before registration and for ongoing compliance.",
    },

    "pan_tan": {
        "display_name": "PAN / TAN Registration",
        "icon": "🆔",
        "authority": "Income Tax Department, Ministry of Finance (NSDL / UTIITSL)",
        "governing_law": "Income Tax Act, 1961; Tax Collection at Source (TCS) Rules",
        "official_portal": "https://www.onlineservices.nsdl.com/ (PAN portal) | https://www.tin-nsdl.com/ (TAN portal)",
        "overview": "Complete guide to PAN (Permanent Account Number) and TAN (Tax Account Number) registration. PAN is mandatory for individuals, HUFs, and businesses with taxable income. TAN is mandatory for businesses deducting tax at source (TDS/TCS). Essential for tax compliance and financial transactions.",

        "services": [
            {
                "service": "Apply for PAN (Individual / HUF / Business)",
                "description": "Obtain Permanent Account Number (PAN) for income tax purposes.",
                "where": "NSDL portal (https://www.onlineservices.nsdl.com/) or Aadhaar link",
                "documents_required": [
                    "Aadhaar number (for link-based PAN, fastest)",
                    "Date of birth",
                    "Address proof (Aadhaar, utility bill, property tax, rental agreement)",
                    "Proof of identity (Aadhaar, DL, Passport)",
                    "For business: business registration documents (partnership deed, MOA/AOA, etc.)",
                ],
                "fee": "Free",
                "timeline": "Instant (Aadhaar link-based) or 10–15 days (document-based)",
                "official_link": "https://www.onlineservices.nsdl.com/",
            },
            {
                "service": "Link PAN with Aadhaar",
                "description": "Link existing PAN to Aadhaar for tax record integration and benefits.",
                "where": "IT e-filing portal or NSDL website",
                "documents_required": [
                    "PAN number",
                    "Aadhaar number",
                    "Name & date of birth match between PAN & Aadhaar",
                ],
                "fee": "Free",
                "timeline": "Instant online linking",
                "official_link": "https://www.incometaxindiaefiling.gov.in/",
            },
            {
                "service": "Apply for TAN (Business / Employer)",
                "description": "Obtain Tax Account Number if business deducts TDS (tax on salary, rent, interest, commission) or collects TCS.",
                "where": "UTIITSL portal (https://www.tin-nsdl.com/) or NSDL",
                "documents_required": [
                    "PAN of applicant (individual proprietor/company director)",
                    "Aadhaar number",
                    "Business registration documents (partnership deed, MOA/AOA, shop act, MSME, etc.)",
                    "Proof of business premises (lease/ownership, utility bill)",
                    "Bank account details",
                    "Identity & address proof of principal officer",
                    "List of employees (if deducting salary TDS)",
                ],
                "fee": "Free",
                "timeline": "5–10 working days",
                "official_link": "https://www.tin-nsdl.com/",
            },
            {
                "service": "Get PAN / TAN Certificate",
                "description": "Download PAN/TAN certificate (digital; physical copy optional).",
                "where": "NSDL/TIN portal (automatic download)",
                "documents_required": [
                    "Approved application",
                    "Identity proof for download",
                ],
                "fee": "Free digital; ₹50–₹100 for physical copy (if requested)",
                "timeline": "Instant (digital) or 3–5 days (physical)",
                "official_link": "https://www.onlineservices.nsdl.com/",
            },
            {
                "service": "File Income Tax Return (ITR) using PAN",
                "description": "File annual income tax return using PAN on e-filing portal.",
                "where": "IT e-filing portal (https://www.incometaxindiaefiling.gov.in/)",
                "documents_required": [
                    "PAN",
                    "Financial statements (income, expenses, investments)",
                    "Bank statements",
                    "Investment proofs (insurance, PPF, FDs, mutual funds)",
                ],
                "fee": "Free filing; tax liability depends on income slab",
                "timeline": "Annual (by July 31 of following financial year)",
                "official_link": "https://www.incometaxindiaefiling.gov.in/",
            },
            {
                "service": "File TDS / TCS Returns using TAN",
                "description": "File quarterly TDS (salary, rent, interest) or TCS (goods sale) returns on e-filing portal.",
                "where": "IT e-filing portal or TDS portal",
                "documents_required": [
                    "TAN",
                    "List of payees & TDS deducted (quarterly for TDS; monthly for TCS)",
                    "Bank statements showing TDS deposit",
                ],
                "fee": "Free; late filing penalty: ₹100–₹500 per day (capped)",
                "timeline": "Quarterly (TDS) or monthly (TCS) by specified date",
                "official_link": "https://www.incometaxindiaefiling.gov.in/",
            },
            {
                "service": "Correct PAN / TAN Details (Name, Address, etc.)",
                "description": "Update PAN/TAN if name, address, or other details have changed.",
                "where": "NSDL/TIN portal or IT e-filing portal",
                "documents_required": [
                    "PAN/TAN number",
                    "Updated documents (address proof, name change deed, if applicable)",
                    "Reason for correction",
                ],
                "fee": "Free",
                "timeline": "5–10 working days",
                "official_link": "https://www.incometaxindiaefiling.gov.in/",
            },
        ],

        "faqs": [
            {
                "q": "Is PAN mandatory for everyone?",
                "a": "Mandatory for: individuals earning >₹2.5 lakh annually, HUFs with >₹5,000 income, businesses, professionals. Optional for: NRIs, students below threshold, salaried employees with tax-only income <₹5 lakh (though recommended). Banking & investment transactions often require PAN anyway."
            },
            {
                "q": "What's the difference between PAN and TAN?",
                "a": "PAN = personal income tax identification. TAN = business identification for deducting/collecting tax from others. Individual employees need PAN; employers/businesses need both PAN & TAN."
            },
            {
                "q": "How fast can I get PAN via Aadhaar link?",
                "a": "Instant on NSDL portal if Aadhaar & details match. PAN issued same day; certificate downloadable immediately. No waiting period for Aadhaar-linked PAN."
            },
            {
                "q": "What if my PAN name doesn't match Aadhaar?",
                "a": "Update name on UIDAI (Aadhaar) first; wait 1–2 weeks for UIDAI update; then link PAN to updated Aadhaar. Or correct PAN name via NSDL portal with name change proof (marriage cert, deed poll, etc.)."
            },
            {
                "q": "Can business have PAN of proprietor or separate company PAN?",
                "a": "Sole proprietor: uses individual's PAN as business PAN. Partnership/Company: separate PAN for business entity. You cannot merge business PAN into personal PAN."
            },
        ],

        "common_issues": [
            "PAN application rejected due to Aadhaar mismatch — verify Aadhaar has current name & address; update UIDAI; reapply on NSDL",
            "TAN not approved due to business registration mismatch — ensure TAN applicant PAN matches business registration authority name; correct PAN first; reapply",
            "PAN/TAN certificate not downloading — try different browser; ensure JavaScript enabled; contact NSDL support if persistent",
            "Late ITR filing penalty — file immediately; penalties apply but IT dept usually grants relief if you file within 1 year",
            "Unable to link PAN with Aadhaar online — visit CSC (Common Service Center) or NSDL office for manual linking assistance",
        ],

        "legal_protections": [
            "Income Tax Act, 1961 — mandates PAN/TAN; defines registration, penalties for non-compliance, appeal process",
            "Right to Information Act, 2005 — applicant can RTI for registration status or tax demand details",
            "Data Protection: Aadhaar Act, 2016 — protects Aadhaar-linked PAN data; IT dept must follow privacy protocols",
            "Alternate Dispute Resolution — PAN/TAN disputes can appeal to IT appellate authority; no court filing needed",
        ],

        "disclaimer": "This guidance is for informational purposes only and does not constitute tax or financial advice. PAN/TAN requirements, income thresholds, and filing deadlines vary by financial year and individual circumstances. We strongly recommend consulting a Chartered Accountant or tax professional for personalized guidance on PAN/TAN registration, ITR filing, TDS obligations, and tax compliance, especially if your income situation is complex.",
    },

    "startup_india": {
        "display_name": "Startup India Registration",
        "icon": "🚀",
        "authority": "DPIIT (Department for Promotion of Industry and Internal Trade), Ministry of Commerce & Industry",
        "governing_law": "Startup India Initiative Regulations; Company Act / Partnership Act",
        "official_portal": "https://www.startupindia.gov.in/ (Startup India portal & Startup India Seed Fund Scheme)",
        "overview": "Complete guide to Startup India registration. Qualifies new businesses for tax benefits, FDI liberalization, and government support. Recognize startups must meet specific criteria (age, entity type, innovation focus). Tax exemption for 5–10 years, reduced compliance burden.",

        "services": [
            {
                "service": "Check Startup India Eligibility Criteria",
                "description": "Determine if your business qualifies as Startup India entity.",
                "where": "Self-assessment or DPIIT guidance",
                "documents_required": [
                    "Business age (must be <10 years)",
                    "Entity type (company, partnership, LLP preferred; sole proprietor not eligible)",
                    "Business model (innovative product/service required)",
                    "Annual turnover (<₹100 crore preferred)",
                ],
                "fee": "Free",
                "timeline": "1–2 hours",
                "official_link": "https://www.startupindia.gov.in/",
            },
            {
                "service": "Apply for Startup India Recognition",
                "description": "Register business for official Startup India status and benefits.",
                "where": "Startup India portal (https://www.startupindia.gov.in/)",
                "documents_required": [
                    "Company registration certificate (or incorporation doc for LLP/partnership)",
                    "Certificate of commencement of business (if company)",
                    "PAN & TAN of the startup",
                    "Address proof of registered office",
                    "Brief business description & innovation focus",
                    "Identity proof of founder/director (Aadhaar, DL, Passport)",
                    "Proof of equity (shareholding details if company)",
                    "ITR filed (if >1 year old, to show compliance)",
                ],
                "fee": "Free registration",
                "timeline": "5–10 working days for recognition",
                "official_link": "https://www.startupindia.gov.in/",
            },
            {
                "service": "Obtain Startup India Certificate",
                "description": "Get official recognition certificate for tax & regulatory benefits.",
                "where": "Startup India portal (automatic after approval)",
                "documents_required": [
                    "Approved registration",
                    "Identity proof",
                ],
                "fee": "No fee",
                "timeline": "Issued 1–2 days after recognition",
                "official_link": "https://www.startupindia.gov.in/",
            },
            {
                "service": "Claim Income Tax Exemption (100% under Section 80-IAC)",
                "description": "Get 100% income tax exemption for 5–10 years if recognized startup with innovation focus.",
                "where": "IT e-filing portal; self-declare in ITR",
                "documents_required": [
                    "Startup India recognition certificate",
                    "Audited financial statements",
                    "IT department approval (processing ITR with exemption claim)",
                ],
                "fee": "No fee; tax saving automatically applied if eligible",
                "timeline": "Claimed annually in ITR (approval 1–2 months after filing)",
                "official_link": "https://www.incometaxindiaefiling.gov.in/",
            },
            {
                "service": "Access Government Startup Schemes & Funding",
                "description": "Apply for government grants, loan guarantees, and mentorship programs.",
                "where": "Startup India portal & ministry websites (SIDBI, PMMY, SISF)",
                "documents_required": [
                    "Startup India certificate",
                    "Business plan & financial projections",
                    "Founder bios & experience",
                    "Innovation description (patent/prototype if available)",
                ],
                "fee": "Scheme-dependent (mostly free or low-cost)",
                "timeline": "Varies by scheme (1–30 days)",
                "official_link": "https://www.startupindia.gov.in/",
            },
            {
                "service": "Self-Certification for Labour & Environment Compliance",
                "description": "Claim self-certification for labour & environment rules for first 5 years (reduced compliance burden).",
                "where": "Startup India portal (self-declare in application)",
                "documents_required": [
                    "Startup India recognition",
                    "Compliance commitment letter",
                ],
                "fee": "No fee",
                "timeline": "Automatic; effective from recognition date",
                "official_link": "https://www.startupindia.gov.in/",
            },
        ],

        "faqs": [
            {
                "q": "What qualifies as a Startup India entity?",
                "a": "Company/LLP/Partnership (sole proprietor NOT eligible) incorporated <10 years ago with innovation focus. Must not have distributed dividends >50% of profit or made profit >₹100 crore. Innovation can be new product, tech, business model serving social/economic objective."
            },
            {
                "q": "How much tax exemption do startups get?",
                "a": "100% profit exemption for 5 consecutive years (within 10 years of incorporation) if recognized & eligible. First 3 years (100%), then must reapply for next 2 years. Must meet criteria: engaged in innovation, turnover <₹25 crore in last 3 years."
            },
            {
                "q": "Is Startup India registration free?",
                "a": "Yes, completely free. Apply on portal; recognition is at no cost. Government also offers free mentorship, networking, and information."
            },
            {
                "q": "How long does Startup India recognition take?",
                "a": "5–10 working days. Processing is automated on portal. Most applications approved within 10 days if documents are complete & criteria met."
            },
            {
                "q": "Can I claim income tax exemption if I don't have Startup India recognition?",
                "a": "No. Section 80-IAC exemption is only available for startups with official Startup India recognition certificate. Self-declared startups are ineligible."
            },
        ],

        "common_issues": [
            "Application rejected due to 'not innovative' claim — redefine business as innovative (tech, new model, social impact); obtain patent/IP if possible; reapply with clearer innovation narrative",
            "Cannot prove you're <10 years old — provide company registration certificate with incorporation date; LLP/partnership registration; clear calendar proof",
            "ITR exemption not approved despite recognition — ensure ITR filed with exemption claim & Startup certificate attached; IT dept processes in 1–2 months; follow up if delayed",
            "Funding application rejected — ensure business is actually operating & generating revenue (not just on paper); show customer traction; improve business plan; reapply",
            "Recognition status unclear or certificate not downloaded — log in portal, check 'My Profile', download latest certificate if issued; contact DPIIT support if not issued",
        ],

        "legal_protections": [
            "Startup India Scheme — established by Department for Promotion of Industry and Internal Trade (DPIIT); creates legal framework for startup benefits",
            "Income Tax Act, 1961 Section 80-IAC — defines tax exemption criteria, 5–10 year window, amendment procedures",
            "Company Act / Partnership Act — governs startup legal structure; all corporate laws still apply",
            "Right to Information Act, 2005 — applicant can RTI for recognition status or processing delays",
        ],

        "disclaimer": "This guidance is for informational purposes only and does not constitute legal, tax, or business advice. Startup India benefits, recognition criteria, tax exemption rules, and available schemes change periodically. We strongly recommend consulting a Chartered Accountant or business consultant familiar with Startup India regulations before registration and for ongoing compliance, especially regarding income tax exemption claims and government funding applications.",
    },
}


# ── Helper Functions ────────────────────────────────────────────────────────

def get_all_business_types() -> list[dict]:
    """Return summary list of all 9 business registration types for hub grid."""
    return [
        {
            "key": "gst",
            "display_name": BUSINESS_KB["gst"]["display_name"],
            "icon": BUSINESS_KB["gst"]["icon"],
            "authority": BUSINESS_KB["gst"]["authority"],
            "official_portal": BUSINESS_KB["gst"]["official_portal"],
        },
        {
            "key": "fssai",
            "display_name": BUSINESS_KB["fssai"]["display_name"],
            "icon": BUSINESS_KB["fssai"]["icon"],
            "authority": BUSINESS_KB["fssai"]["authority"],
            "official_portal": BUSINESS_KB["fssai"]["official_portal"],
        },
        {
            "key": "msme",
            "display_name": BUSINESS_KB["msme"]["display_name"],
            "icon": BUSINESS_KB["msme"]["icon"],
            "authority": BUSINESS_KB["msme"]["authority"],
            "official_portal": BUSINESS_KB["msme"]["official_portal"],
        },
        {
            "key": "shop_establishment",
            "display_name": BUSINESS_KB["shop_establishment"]["display_name"],
            "icon": BUSINESS_KB["shop_establishment"]["icon"],
            "authority": BUSINESS_KB["shop_establishment"]["authority"],
            "official_portal": BUSINESS_KB["shop_establishment"]["official_portal"],
        },
        {
            "key": "iec",
            "display_name": BUSINESS_KB["iec"]["display_name"],
            "icon": BUSINESS_KB["iec"]["icon"],
            "authority": BUSINESS_KB["iec"]["authority"],
            "official_portal": BUSINESS_KB["iec"]["official_portal"],
        },
        {
            "key": "trade_license",
            "display_name": BUSINESS_KB["trade_license"]["display_name"],
            "icon": BUSINESS_KB["trade_license"]["icon"],
            "authority": BUSINESS_KB["trade_license"]["authority"],
            "official_portal": BUSINESS_KB["trade_license"]["official_portal"],
        },
        {
            "key": "professional_tax",
            "display_name": BUSINESS_KB["professional_tax"]["display_name"],
            "icon": BUSINESS_KB["professional_tax"]["icon"],
            "authority": BUSINESS_KB["professional_tax"]["authority"],
            "official_portal": BUSINESS_KB["professional_tax"]["official_portal"],
        },
        {
            "key": "pan_tan",
            "display_name": BUSINESS_KB["pan_tan"]["display_name"],
            "icon": BUSINESS_KB["pan_tan"]["icon"],
            "authority": BUSINESS_KB["pan_tan"]["authority"],
            "official_portal": BUSINESS_KB["pan_tan"]["official_portal"],
        },
        {
            "key": "startup_india",
            "display_name": BUSINESS_KB["startup_india"]["display_name"],
            "icon": BUSINESS_KB["startup_india"]["icon"],
            "authority": BUSINESS_KB["startup_india"]["authority"],
            "official_portal": BUSINESS_KB["startup_india"]["official_portal"],
        },
    ]


def get_business_guidance(business_type: str) -> dict | None:
    """Return full guidance for one business registration type."""
    normalized = _normalize_business_type(business_type)
    return BUSINESS_KB.get(normalized) if normalized else None


def get_business_checklist(business_type: str, service: str) -> list[str] | None:
    """Return document checklist for a specific service within a business type."""
    normalized = _normalize_business_type(business_type)
    if not normalized or normalized not in BUSINESS_KB:
        return None

    for svc in BUSINESS_KB[normalized].get("services", []):
        if svc["service"].lower() == service.lower():
            return svc.get("documents_required", [])

    return None


def _normalize_business_type(raw: str) -> str | None:
    """Normalize user input to canonical business type key."""
    if not raw:
        return None

    raw_lower = raw.lower().strip()

    # Exact match
    if raw_lower in BUSINESS_KB:
        return raw_lower

    # Alias map
    aliases = {
        "gst": "gst",
        "gst registration": "gst",
        "goods and services tax": "gst",
        "fssai": "fssai",
        "food safety": "fssai",
        "food license": "fssai",
        "msme": "msme",
        "udyam": "msme",
        "udyam registration": "msme",
        "micro small medium": "msme",
        "shop": "shop_establishment",
        "shop and establishment": "shop_establishment",
        "establishment license": "shop_establishment",
        "trade license": "trade_license",
        "municipal license": "trade_license",
        "iec": "iec",
        "import export code": "iec",
        "professional tax": "professional_tax",
        "pan": "pan_tan",
        "tan": "pan_tan",
        "pan/tan": "pan_tan",
        "startup india": "startup_india",
        "startup recognition": "startup_india",
    }

    return aliases.get(raw_lower)
