"""
Property Hub Knowledge Base for SmartLegal-AI Phase 4B.

Guidance platform for 5 Indian property transaction types:
- Property Sale (Transfer of Ownership)
- Property Rental (Leave & Licence Agreement)
- Mutation (Ownership Transfer at Revenue Office)
- Encumbrance Certificate (Proof of Clear Title)
- Registration (Sub-Registrar Property Registration)

All data is static, verified, and deterministic.
Sources: Official government portals, state revenue acts, and property law.
"""

PROPERTY_KB = {
    "sale": {
        "display_name": "Property Sale",
        "icon": "🏠",
        "authority": "State Sub-Registrar / District Revenue Office",
        "governing_law": "Transfer of Property Act, 1882 & State-Specific Registration Acts",
        "official_portal": "https://igrsup.gov.in (Uttar Pradesh) — state-specific portals available",
        "overview": "Complete guide to selling property in India. Covers registration, stamp duty, capital gains tax, and all legal requirements for residential, commercial, or agricultural property transfer.",

        "services": [
            {
                "service": "Prepare Sale Deed",
                "description": "Draft and prepare sale deed (Vikray Patra) with all legal clauses.",
                "where": "Advocate's office or notary; online templates available",
                "documents_required": [
                    "Title deed of seller (property ownership proof)",
                    "Latest property tax receipt (last 2 years)",
                    "Approved building plan and completion certificate",
                    "Energy/Water/Electricity connection copy",
                    "NOC from society/HOA (if applicable)",
                    "Seller's PAN and Aadhaar",
                    "Mutation extract from revenue office",
                    "Bank account proof of seller",
                ],
                "fee": "₹2,000–₹10,000 for deed drafting by advocate",
                "timeline": "3–7 days for drafting",
                "official_link": "https://www.barandbench.com/columns/property-law",
            },
            {
                "service": "Stamp Duty & Registration",
                "description": "Pay stamp duty and register sale deed at Sub-Registrar office.",
                "where": "State Sub-Registrar office (within district of property)",
                "documents_required": [
                    "Signed sale deed (both parties)",
                    "Identity proof of both parties (Aadhaar/PAN/DL/Passport)",
                    "Proof of residence for both parties",
                    "No Objection Certificate (NOC) from mortgagee if bank loan existed",
                    "Clear title documents (previous sale deeds, mutations, etc.)",
                    "Cheque for stamp duty and registration fee",
                ],
                "fee": "Stamp duty: 5-6% of property value (state-wise); Registration: 1-2% of value",
                "timeline": "15–30 days for registration",
                "official_link": "https://igrsup.gov.in/en/service/online-registration/",
            },
            {
                "service": "Capital Gains Tax Filing",
                "description": "File income tax return for long-term or short-term capital gains on property sale.",
                "where": "ITR filing via e-filing portal (income-tax.gov.in)",
                "documents_required": [
                    "Sale deed (registered copy)",
                    "Original purchase invoice/deed",
                    "Bank statements showing sale proceeds received",
                    "TDS certificate (if applicable)",
                    "Cost inflation index (CII) proof for long-term gains",
                    "PAN of seller and buyer",
                ],
                "fee": "No fee for ITR filing; tax liability depends on gains",
                "timeline": "Before July 31 of following financial year",
                "official_link": "https://www.incometaxindiaefiling.gov.in/",
            },
            {
                "service": "Mutation at Revenue Office",
                "description": "Update revenue records to reflect new owner's name (Dakhil Kharij).",
                "where": "Taluka/Block Revenue Office (Patwar office)",
                "documents_required": [
                    "Application form for mutation (state revenue dept template)",
                    "Registered sale deed photocopy",
                    "Identity proof of new owner",
                    "Self-attested copy of revenue record (old & proposed new owner)",
                    "NOC from old owner (often required)",
                    "Bank draft for mutation fees (₹500–₹2,000)",
                ],
                "fee": "₹500–₹2,000 (state-dependent)",
                "timeline": "30–90 days after application",
                "official_link": "https://revenue.maharashtra.gov.in/ (Maharashtra example)",
            },
            {
                "service": "Title Insurance & Verification",
                "description": "Optional: obtain title insurance to protect against ownership disputes.",
                "where": "General insurance companies (ICICI Lombard, HDFC Ergo, etc.)",
                "documents_required": [
                    "Registered sale deed",
                    "Property tax receipt",
                    "Building plan & completion certificate",
                    "Chain of title documents (previous deeds)",
                    "Mutation extract",
                    "Utility connection proofs",
                ],
                "fee": "₹1,500–₹5,000 (one-time; covers 10+ year period)",
                "timeline": "7–15 days for approval",
                "official_link": "https://www.iciciinsurance.com/property-owners-insurance.html",
            },
        ],

        "faqs": [
            {
                "q": "What is the difference between sale deed and conveyance deed?",
                "a": "Sale deed is a document where seller transfers property to buyer for a price. Conveyance is the legal act of transfer itself. Sale deed is the instrument; conveyance is the action. In India, 'sale deed' is the common term used in Transfer of Property Act."
            },
            {
                "q": "Is stamp duty the same as registration fee?",
                "a": "No. Stamp duty is a tax on the document value (typically 5–6% of property value). Registration fee is a separate government charge (1–2% of value). Both are mandatory to make the sale deed legally valid."
            },
            {
                "q": "Can I register a property sale online?",
                "a": "Many states now offer e-registration. You can apply online, pay fees online, and appointments are booked. Physical presence of both parties is usually still required at the Sub-Registrar office for signatures."
            },
            {
                "q": "What is capital gains tax on property sale?",
                "a": "If you held the property for 2+ years before sale, gains are 'long-term' and taxed at 20% (with cost inflation index benefit). If < 2 years, gains are 'short-term' and taxed at slab rates (15–45%). You can claim exemption under Section 54 if sale proceeds are reinvested in residential property."
            },
            {
                "q": "What happens if mutation is not done after property sale?",
                "a": "Revenue records still show the old owner. This creates title issues for future buyers, affects property tax assessment, and can delay loans/sales. Mutation should be done within 6 months of sale to avoid penalties and confusion."
            },
        ],

        "common_issues": [
            "Buyer discovers ownership dispute or previous sale not registered — always verify chain of title before payment",
            "Stamp duty incorrectly calculated — use official state stamps calculator to avoid undervaluation penalties",
            "Mutation delayed beyond 6 months — apply via SDM/Tahsildar petition to expedite if revenue office is slow",
            "TDS (Tax Deducted at Source) notice if sale is above threshold — ensure buyer withholds 1% TDS and submits before buyer gets clearance",
            "Property inherited before sale — ensure inheritance deed is registered first; joint heirs must sign sale deed together",
        ],

        "legal_protections": [
            "Transfer of Property Act, 1882 — governs all property sales in India; contract must be in writing and registered",
            "Registration Act, 1908 — mandates registration of sale deed at Sub-Registrar; unregistered sale deed is not valid evidence of ownership",
            "Stamp Act, 1899 — all sale deeds must bear correct stamp duty; under-stamped deeds can be impounded and penalty imposed",
            "Income Tax Act, 1961 — capital gains on property are taxable; long-term gains (₹2,000+) must be reported via ITR-2; exemptions available under Sections 54 & 54F",
        ],

        "disclaimer": "This guidance is for informational purposes only and does not constitute legal advice. Property laws vary by state (Maharashtra, Delhi, Karnataka, etc.) and differ for residential, commercial, and agricultural property. We strongly recommend consulting a registered advocate or legal expert before signing any sale deed, as property transactions carry significant financial and legal implications. Always verify title clearance with your state's Sub-Registrar or Land Records office.",
    },

    "rental": {
        "display_name": "Property Rental",
        "icon": "🔑",
        "authority": "State Housing Department / Local Municipal Corporation",
        "governing_law": "Indian Rent Control Act (varies by state), Indian Contract Act, 1872",
        "official_portal": "https://housing.maharashtra.gov.in (Maharashtra) — state-specific housing boards",
        "overview": "Complete guide to renting property in India. Covers Leave & Licence agreements, rent deposits, tenant rights, eviction procedures, and legal remedies for both landlord and tenant.",

        "services": [
            {
                "service": "Prepare Leave & Licence Agreement",
                "description": "Draft legal agreement between landlord and tenant defining terms of occupancy.",
                "where": "Advocate's office or online legal template services",
                "documents_required": [
                    "Property ownership proof (sale deed, mutation, will, etc.)",
                    "Property tax receipt (latest 2 years)",
                    "Building plan approval & completion certificate",
                    "Energy/Water/Electricity meter copy",
                    "Identity & address proof of landlord (Aadhaar, PAN, DL)",
                    "Identity & address proof of tenant",
                    "Bank account details of both parties",
                    "Passport-size photos of both parties",
                ],
                "fee": "₹3,000–₹8,000 for agreement drafting by advocate",
                "timeline": "3–5 days",
                "official_link": "https://www.moneycontrol.com/news/personalfinance/leave-and-licence-agreement/",
            },
            {
                "service": "Register Rental Agreement",
                "description": "Register Leave & Licence agreement with municipal corporation or revenue office (state-dependent).",
                "where": "Municipal Corporation office or Sub-Registrar (varies by state)",
                "documents_required": [
                    "Signed Leave & Licence agreement",
                    "Identity proofs of landlord and tenant",
                    "Property ownership document",
                    "Copy of rent receipt (if advance rent paid)",
                    "Building society NOC (if applicable)",
                    "Stamp duty payment receipt",
                ],
                "fee": "Registration: ₹500–₹1,500; Stamp duty: ₹100–₹500 (state-dependent)",
                "timeline": "7–15 days",
                "official_link": "https://www.iflr.com/article/rental-agreement-india",
            },
            {
                "service": "Understand Tenant Rights & Duties",
                "description": "Know legal rights (maintenance, repairs), duties (timely rent, property care), and protections under state rent acts.",
                "where": "Online resources or tenant welfare associations",
                "documents_required": [
                    "Copy of registered Leave & Licence agreement",
                    "Rent receipt records (monthly payments)",
                    "Maintenance & repair request correspondence",
                ],
                "fee": "Free (informational)",
                "timeline": "Self-study; 1–2 hours",
                "official_link": "https://www.thehindu.com/news/national/tenant-rights-in-india/",
            },
            {
                "service": "Eviction Process (if needed)",
                "description": "Legal eviction of tenant if lease terms violated (non-payment, illegal use, end of term).",
                "where": "Civil court under Rent Control Act or contract law",
                "documents_required": [
                    "Registered Leave & Licence agreement",
                    "Rent receipt records showing non-payment (if applicable)",
                    "Notice to quit (60–90 days advance notice as per agreement)",
                    "Registered letter/email proof of notice served",
                    "Proof of breach (photographs, bills, unauthorized occupants, etc.)",
                ],
                "fee": "Advocate fee: ₹10,000–₹30,000; court filing fee: ₹500–₹2,000",
                "timeline": "6–12 months (civil court proceedings)",
                "official_link": "https://www.livemint.com/opinion/online-views/eviction-of-tenants-in-india-11580385099.html",
            },
            {
                "service": "Disputes & Resolution (Rent Recovery, Damage Claims)",
                "description": "File case in civil court or consumer forum for non-payment, property damage, or security deposit disputes.",
                "where": "Civil court (Section 9 suit) or Consumer Disputes Redressal Commission",
                "documents_required": [
                    "Registered Leave & Licence agreement",
                    "Rent receipts / bank statements showing non-payment",
                    "Photographs or video proof of damage (if applicable)",
                    "Notice issued to tenant (registered mail proof)",
                    "Correspondence (emails, SMSes, letters)",
                ],
                "fee": "Advocate fee: ₹15,000–₹40,000; Court filing: ₹1,000–₹5,000",
                "timeline": "1–2 years (civil court); 6–12 months (consumer forum)",
                "official_link": "https://www.consumer.gov.in/",
            },
        ],

        "faqs": [
            {
                "q": "What is the difference between Leave & Licence and Lease agreement?",
                "a": "Lease transfers property ownership interest temporarily; Leave & Licence grants permission to occupy without ownership transfer. L&L is more landlord-friendly and used for short-term residential rentals. Leases are for long-term agricultural or commercial property."
            },
            {
                "q": "How much security deposit can a landlord ask?",
                "a": "Most states allow 1–2 months' rent as deposit. Some states cap it at 1 month for residential property. Check your state's Rent Control Act for exact limits. Deposit must be returned within 30 days of tenancy end, minus authorized deductions."
            },
            {
                "q": "Is a Leave & Licence agreement valid without registration?",
                "a": "Validity varies by state. In most states (including Maharashtra), unregistered agreements are valid between parties but cannot be used as evidence in court. Registration is recommended for legal protection and dispute resolution."
            },
            {
                "q": "Can a landlord increase rent anytime?",
                "a": "No. Most state Rent Control Acts restrict annual increases to 5–10% (varies by state). Rent increase notice must be given 60–90 days in advance. However, L&L agreements for <11 months can be renewed at fresh rent terms."
            },
            {
                "q": "What if landlord/tenant refuses to vacate after notice period?",
                "a": "File an eviction suit in civil court under Rent Control Act or contract law. Court will issue eviction order if breach is proven. If still non-compliant, landlord can request police help to execute court order."
            },
        ],

        "common_issues": [
            "Tenant non-payment of rent — issue 60-day notice to quit; file civil suit for arrears recovery if not paid within notice period",
            "Damage to property by tenant — document damage with photographs; deduct repair costs from security deposit; file suit for remaining damages",
            "Illegal subletting — L&L agreement typically prohibits subletting; landlord can issue notice to quit and file eviction suit",
            "Society objection to rental — some HOAs restrict rentals; check society bylaws; obtain NOC before signing rental agreement",
            "Tenant overstaying post-expiry — issue 60-day termination notice; if overstay continues, file eviction suit for property restitution",
        ],

        "legal_protections": [
            "Indian Contract Act, 1872 — governs rental agreements; both parties bound by terms; agreement must be registered to have full evidentiary value",
            "State-Specific Rent Control Acts — Maharashtra Rent Control Act 1999, Delhi Rent Control Act 1998, etc.; regulate rent increases, security deposit, eviction procedures",
            "Property Rights & Tenant Protection Act (varies by state) — grants tenants right to safe habitation, maintenance, repairs; landlord must provide livable condition",
            "Stamp Act, 1899 — Leave & Licence agreements should be stamped per state schedule; unstamped agreement may not be admissible as evidence",
        ],

        "disclaimer": "This guidance is for informational purposes only and does not constitute legal advice. Rental laws vary significantly by state and municipal corporation rules. We strongly recommend consulting a registered advocate before signing any Leave & Licence agreement, especially regarding security deposit terms, rent increase provisions, and eviction clauses. Tenant rights and landlord protections differ substantially across states.",
    },

    "mutation": {
        "display_name": "Mutation / Dakhil Kharij",
        "icon": "📋",
        "authority": "District Revenue Office / Taluka Patwar Office",
        "governing_law": "State-Specific Land Records Act (varies by state: Maharashtra, Karnataka, Gujarat)",
        "official_portal": "https://mahabhulekh.maharashtra.gov.in (Maharashtra) — state-specific land records portals",
        "overview": "Complete guide to updating revenue records after property transfer. Mutation (Dakhil Kharij in Maharashtra) is the process of recording new owner's name in revenue records. This is mandatory after property sale and required for property tax, loans, and future sales.",

        "services": [
            {
                "service": "File Mutation Application (Dakhil Kharij)",
                "description": "Submit mutation application to Taluka Revenue Office (Patwar) to update property records.",
                "where": "Taluka/Block Revenue Office (Patwar office) or online portal (state-dependent)",
                "documents_required": [
                    "Mutation application form (state revenue dept template, free)",
                    "Registered sale deed photocopy (attested by authorized person)",
                    "Old ownership document (sale deed, will, court order, etc.)",
                    "Identity proof of new owner (Aadhaar, PAN, DL, Passport)",
                    "Self-attested copy of revenue record (7/12 or 8A extract) — both old & proposed new owner names",
                    "NOC from old owner (often required; sometimes online attestation accepted)",
                    "Bank draft for mutation fees (₹500–₹2,000 depending on property value and state)",
                ],
                "fee": "₹500–₹2,000 (Maharashtra: ₹1,000–₹2,000; varies by state and property value)",
                "timeline": "30–90 days from filing (can vary; follow-up may be needed)",
                "official_link": "https://mahabhulekh.maharashtra.gov.in/",
            },
            {
                "service": "Obtain 7/12 Extract (Record of Rights) with New Name",
                "description": "After mutation is approved, obtain updated 7/12 extract showing new owner's name and ownership details.",
                "where": "Taluka Revenue Office or online state land records portal",
                "documents_required": [
                    "Mutation approval order",
                    "Identity proof of new owner",
                    "Proof of residence of new owner",
                ],
                "fee": "₹10–₹100 per copy (varies by state)",
                "timeline": "2–7 days after mutation approval",
                "official_link": "https://mahabhulekh.maharashtra.gov.in/ (Maharashtra portal)",
            },
            {
                "service": "Obtain 8A Extract (Encumbrance Certificate) with New Name",
                "description": "Get updated 8A extract showing no legal encumbrances (mortgages, liens) on the property under new owner's name.",
                "where": "Sub-Registrar office (or state land records portal)",
                "documents_required": [
                    "Mutation approval order",
                    "Identity proof of new owner",
                    "Application form for 8A extract (Sub-Registrar office template)",
                ],
                "fee": "₹50–₹200 (varies by state and years searched)",
                "timeline": "5–10 days",
                "official_link": "https://igrsup.gov.in/en/service/encumbrance-certificate-ec/",
            },
            {
                "service": "Property Tax Registration / Update",
                "description": "Update property tax records with new owner's name and complete mutation at municipal corporation.",
                "where": "Municipal Corporation Property Tax Office (ward-specific)",
                "documents_required": [
                    "Mutation approval order from Revenue Office",
                    "Registered sale deed photocopy",
                    "Property tax receipt (old owner) for last 2 years",
                    "Identity proof of new owner",
                    "Application form for property tax transfer (municipal corporation form)",
                ],
                "fee": "Usually ₹500–₹1,500 (transfer/update fee; varies by municipal corporation)",
                "timeline": "15–30 days",
                "official_link": "https://www.mcgm.gov.in/ (Mumbai example)",
            },
            {
                "service": "Online Mutation Status Check & Follow-up",
                "description": "Track mutation application status online and follow up with revenue office if needed.",
                "where": "State land records online portal",
                "documents_required": [
                    "Mutation application reference number",
                    "Property details (Taluka, village, survey number)",
                ],
                "fee": "Free",
                "timeline": "Real-time online tracking available on most state portals",
                "official_link": "https://mahabhulekh.maharashtra.gov.in/ or state-specific portal",
            },
        ],

        "faqs": [
            {
                "q": "What is mutation (Dakhil Kharij)?",
                "a": "Mutation is the process of updating revenue records to reflect a change in property ownership. 'Dakhil' means entry (of new owner); 'Kharij' means removal (of old owner). After sale, mutation must be filed to legally establish new owner in government records."
            },
            {
                "q": "Is mutation mandatory after property sale?",
                "a": "Yes. Mutation is mandatory for legal proof of ownership in government records. Without mutation, property tax, loans, future sales, and inheritance become difficult. Mutation should be filed within 6 months of sale; delay can result in penalties."
            },
            {
                "q": "Who files the mutation application — buyer or seller?",
                "a": "Typically, both buyer and seller file jointly. Old owner must sign NOC (No Objection Certificate). In practice, buyer's advocate usually files on behalf of both with seller's consent documented."
            },
            {
                "q": "How long does mutation take?",
                "a": "Usually 30–90 days. Timeline varies by state and taluka workload. If Patwar raises queries (objections by third parties, incomplete documents), timeline extends. Most states have online status tracking."
            },
            {
                "q": "What if mutation is rejected?",
                "a": "If mutation is rejected, Patwar will issue order stating reasons (e.g., title dispute, incomplete documents). Buyer must address objections, submit additional documents, or appeal to Tahsildar (next authority level). Process can be re-filed."
            },
        ],

        "common_issues": [
            "Mutation delayed beyond 6 months — file petition with SDM/Tahsildar citing urgent need (loan, re-sale, property tax liability); bring all documents",
            "Old owner refuses to sign NOC — NOC can sometimes be obtained via online authenticated signature or through court order if old owner is untraced",
            "Third-party objection during mutation — if heir or mortgagee raises claim, mutation gets suspended; resolve through negotiation or small claims court",
            "Survey number/field mapping error in revenue records — Patwar corrects during mutation if sale deed reference is clear; seek Patwar's help to cross-verify",
            "Property tax not updated despite mutation approval — submit mutation order to municipal tax office separately; municipal and revenue offices operate independently",
        ],

        "legal_protections": [
            "State-Specific Land Records Act (Maharashtra: Land Records & Survey Act; varies by state) — mandates maintenance of accurate revenue records; Patwar is public servant liable for delays",
            "Transfer of Property Act, 1882 — establishes ownership transfer via registered deed; mutation is subsequent record update confirming transfer",
            "Right to Information Act, 2005 — property owner can file RTI to track mutation application status and demand reasons for delays",
            "Revenue Codes (state-specific) — outline mutation procedures, fee structures, and appeal mechanisms; variation exists across Maharashtra, Karnataka, Gujarat, etc.",
        ],

        "disclaimer": "This guidance is for informational purposes only and does not constitute legal advice. Mutation procedures, fees, and timelines vary significantly across states and talukas. Revenue department functioning may have delays beyond standard timelines. We recommend consulting a local revenue advocate or land agent familiar with your specific taluka to navigate mutation efficiently and handle any third-party objections. Keep all mutation documents and approvals for future property transactions.",
    },

    "encumbrance": {
        "display_name": "Encumbrance Certificate",
        "icon": "📜",
        "authority": "District Sub-Registrar Office",
        "governing_law": "Registration Act, 1908; State-Specific Land Records Act",
        "official_portal": "https://igrsup.gov.in/en/service/encumbrance-certificate-ec/ (UP) — varies by state",
        "overview": "Complete guide to obtaining Encumbrance Certificate (EC or Index II), a critical document proving clear property title. EC shows all mortgages, liens, and legal claims against the property. Required for property sales, bank loans, and inheritance.",

        "services": [
            {
                "service": "Apply for Encumbrance Certificate (EC / Index II)",
                "description": "Request EC from Sub-Registrar showing no mortgages, liens, or legal encumbrances on property.",
                "where": "Sub-Registrar office (or online application portal in advanced states)",
                "documents_required": [
                    "EC application form (Sub-Registrar template or online portal)",
                    "Property details: survey number, taluka, district, property address",
                    "Ownership proof (latest sale deed, will, mutation order, or property tax receipt)",
                    "Identity proof of applicant (Aadhaar, PAN, DL, Passport)",
                    "Proof of residence of applicant",
                    "Checque/cash for EC fee (₹50–₹200)",
                    "Specific year range for search (e.g., 'last 10 years' or '2010 onwards')",
                ],
                "fee": "₹50–₹200 per copy (varies by state and years searched; ₹100–₹150 for 10-year search)",
                "timeline": "5–10 working days",
                "official_link": "https://igrsup.gov.in/en/service/encumbrance-certificate-ec/",
            },
            {
                "service": "Verify EC Information & Title Chain",
                "description": "Review EC to ensure accuracy, check for any mortgages or claims, and verify ownership chain.",
                "where": "Self-review with Sub-Registrar or advocate consultation",
                "documents_required": [
                    "Obtained EC document",
                    "Sale deed copies (yours and previous owners)",
                    "Loan documentation (mortgage papers, if any)",
                    "Court case records (if any pending).",
                ],
                "fee": "Free (if self-reviewed); ₹2,000–₹5,000 if advocate reviews",
                "timeline": "1–2 hours for review",
                "official_link": "https://www.thehindu.com/news/national/encumbrance-certificate-explained/",
            },
            {
                "service": "Use EC for Bank Loan / Property Sale",
                "description": "Present EC to bank for mortgage/home loan approval or to buyer as proof of clear title.",
                "where": "Bank lending department or buyer's advocate",
                "documents_required": [
                    "Original EC document",
                    "Latest copy (EC is typically valid for 3–6 months; older copies may require re-application)",
                    "Loan application form (for bank)",
                    "Sale agreement (for buyer)",
                ],
                "fee": "No fee; cost covered by loan/sale process",
                "timeline": "Same-day submission to bank/buyer",
                "official_link": "https://www.sbicard.com/en/personal/loans/home-loan/documents-required.html",
            },
            {
                "service": "Resolve Encumbrances (if mortgages or claims exist)",
                "description": "If EC shows mortgage (due to past loan), obtain No Objection Certificate (NOC) from mortgagee bank; remove lien via discharge deed.",
                "where": "Bank lending department (mortgagee) for NOC/discharge",
                "documents_required": [
                    "Loan account number and original loan documents",
                    "Proof of loan repayment (statement showing zero balance)",
                    "Identity proof",
                    "Request letter to bank for NOC/discharge deed",
                ],
                "fee": "₹500–₹2,000 (bank discharge fee); ₹100–₹500 (Sub-Registrar registration of discharge)",
                "timeline": "5–10 working days for bank to issue NOC; 5–10 days for Sub-Registrar registration",
                "official_link": "https://www.moneycontrol.com/news/business/loan-discharge-certificate/",
            },
            {
                "service": "Track Property Litigation / Court Cases",
                "description": "Check if property is involved in ongoing court cases or disputes (shown in EC under 'pending litigation').",
                "where": "Sub-Registrar (EC records) or district court case database",
                "documents_required": [
                    "Property details (survey number, taluka, district)",
                    "Application for detailed court case search (if not shown in EC)",
                    "Identity proof",
                ],
                "fee": "₹50–₹200 for court case search; Sub-Registrar may provide summary in EC",
                "timeline": "5–10 days",
                "official_link": "https://www.highcourts.up.nic.in/index.html (state-specific court portal)",
            },
        ],

        "faqs": [
            {
                "q": "What does Encumbrance Certificate (EC) show?",
                "a": "EC is a legal certificate issued by Sub-Registrar showing: (1) all mortgages against the property (loans taken on property), (2) any legal liens or claims filed, (3) pending court cases affecting the property, (4) period covered by the search (usually 10–30 years). EC proves property is free from legal encumbrances if 'No Encumbrance' is stated."
            },
            {
                "q": "Is EC mandatory for property sale?",
                "a": "Not legally mandatory, but practically essential. Buyers insist on EC to ensure clear title and no hidden mortgages/claims. Banks require EC before approving home loans. Without EC, sale is risky and may be challenged later."
            },
            {
                "q": "How long is EC valid?",
                "a": "EC is typically valid for 3–6 months. For property transactions or loans, obtain EC close to transaction date. Older EC (>6 months) may be questioned; verify with bank/buyer if re-application is needed."
            },
            {
                "q": "What if EC shows a mortgage but I've already repaid the loan?",
                "a": "Obtain a 'Discharge Deed' or 'No Objection Certificate' from the bank confirming loan repayment. Register this discharge deed at Sub-Registrar. A new EC issued after discharge will show no encumbrance."
            },
            {
                "q": "Can I get EC for inherited property if deed is not registered?",
                "a": "Inheritance deed must be registered first (or obtain court succession certificate). Then apply for EC. Unregistered inheritance deed won't be recognized in EC; registration is prerequisite."
            },
        ],

        "common_issues": [
            "EC shows old mortgage from previous owner not discharged — obtain discharge deed from bank, register it, reapply for fresh EC",
            "EC shows pending court case — case must be resolved before clear title; if case is old/dormant, petition court for dismissal",
            "EC shows third-party claim (heir, mortgagee) — negotiate settlement and obtain NOC from claimant; register settlement deed",
            "EC application rejected or delayed — follow up with Sub-Registrar; provide complete property details and ownership proof; escalate to District Registrar if needed",
            "Different EC data for property (survey number mismatch) — verify survey number in revenue record; rectify mutation if number has changed",
        ],

        "legal_protections": [
            "Registration Act, 1908 — mandates EC issuance; Sub-Registrar is legally bound to issue EC within 10 days of application",
            "Transfer of Property Act, 1882 — establishes requirement of clear title for property sale; EC is statutory proof of clear title",
            "Right to Information Act, 2005 — applicant can file RTI if EC is delayed beyond 10 days",
            "Consumer Protection Act, 2019 — applies if bank/services provider uses false EC or delays EC issuance; remedies available for financial loss",
        ],

        "disclaimer": "This guidance is for informational purposes only and does not constitute legal advice. EC validity, search period, and procedures vary by state and Sub-Registrar office. A clear EC does not guarantee property title is absolutely free from all risks; it only reflects registered encumbrances up to the specified date. For comprehensive title verification, engage a title insurance company or registered advocate. Always verify the latest EC before major property transactions or loans.",
    },

    "7/12": {
        "display_name": "7/12 Extract (Record of Rights)",
        "icon": "📄",
        "authority": "District Taluka / Revenue Office",
        "governing_law": "State Land Records Act (varies by state); Maharashtra Land Survey Act, 1965",
        "official_portal": "https://mahabhulekh.maharashtra.gov.in (Maharashtra) — state-specific land records portal",
        "overview": "Complete guide to obtaining 7/12 Extract, the official document showing land ownership, cultivation rights, and property details. The '7/12' refers to specific columns in the revenue record: column 7 = rights holder, column 12 = nature of occupation. Essential for property transactions, bank loans, and legal ownership proof.",

        "services": [
            {
                "service": "Understand 7/12 Extract Components",
                "description": "Learn what each field in 7/12 extract means and how to verify accuracy.",
                "where": "Self-education or Taluka Revenue Office consultation",
                "documents_required": [
                    "Property details: survey number, village, taluka, district",
                    "Identity proof (Aadhaar, PAN, DL, Passport)",
                ],
                "fee": "Free (informational)",
                "timeline": "1–2 hours for understanding",
                "official_link": "https://mahabhulekh.maharashtra.gov.in/",
            },
            {
                "service": "Apply for 7/12 Extract Online",
                "description": "Request 7/12 extract digitally through state land records portal.",
                "where": "State land records online portal (Mahabhulekh in Maharashtra, etc.)",
                "documents_required": [
                    "Survey number and village name",
                    "Property address",
                    "Identity proof (Aadhaar/PAN)",
                ],
                "fee": "₹10–₹50 per copy (digital delivery)",
                "timeline": "Instant to 24 hours",
                "official_link": "https://mahabhulekh.maharashtra.gov.in/",
            },
            {
                "service": "Obtain 7/12 Extract from Taluka Office",
                "description": "Physical copy of 7/12 extract from Revenue Office (in-person application).",
                "where": "Taluka Revenue Office (Patwar/Lekhpal office)",
                "documents_required": [
                    "Application form (Taluka template)",
                    "Survey number and property details",
                    "Identity proof (Aadhaar/PAN/DL)",
                    "Proof of interest (ownership deed, rental agreement, etc.)",
                ],
                "fee": "₹25–₹100 per copy",
                "timeline": "3–7 days",
                "official_link": "https://mahabhulekh.maharashtra.gov.in/",
            },
            {
                "service": "Verify 7/12 Accuracy & Correct Errors",
                "description": "Check 7/12 for spelling, survey number, or rights holder errors and file correction petition.",
                "where": "Taluka Revenue Office (Patwar)",
                "documents_required": [
                    "Current 7/12 extract showing error",
                    "Proof of correct information (sale deed, mutation order, etc.)",
                    "Application for rectification (Taluka template)",
                    "Identity proof",
                ],
                "fee": "₹200–₹500 for rectification petition",
                "timeline": "15–30 days for rectification approval",
                "official_link": "https://mahabhulekh.maharashtra.gov.in/",
            },
            {
                "service": "Use 7/12 for Bank Loan / Property Transaction",
                "description": "Present 7/12 extract to banks, property buyers, or authorities as proof of ownership and land rights.",
                "where": "Bank, property buyer advocate, or municipal office",
                "documents_required": [
                    "Original or certified copy of 7/12 extract",
                    "Related transaction documents (sale agreement, loan form, etc.)",
                ],
                "fee": "No fee; cost covered by transaction",
                "timeline": "Same-day submission",
                "official_link": "https://www.sbicard.com/en/personal/loans/home-loan/documents-required.html",
            },
        ],

        "faqs": [
            {
                "q": "What does 7/12 extract show?",
                "a": "7/12 extract shows: (1) rights holder name (owner), (2) survey number and land area, (3) cultivation type (agriculture, residential, etc.), (4) mortgage/lien status, (5) crop history. Columns 7 and 12 are key: column 7 = rights holder, column 12 = nature of occupation. It's an official proof of land ownership."
            },
            {
                "q": "Can I apply for 7/12 if I'm not the owner?",
                "a": "Anyone with legal interest (tenant, mortgagee, heir) can apply. Proof of interest is required (rental agreement, mortgage deed, will, court order). Pure strangers cannot obtain 7/12; privacy restrictions apply."
            },
            {
                "q": "Is 7/12 valid forever or does it expire?",
                "a": "7/12 is a record of current property status, not a time-bound certificate. It's always valid as proof of current rights. However, banks may prefer a recent 7/12 (issued within 6 months) for loans and transactions."
            },
            {
                "q": "What if 7/12 shows wrong ownership?",
                "a": "File a rectification petition (Arz/Arzi) at Taluka Revenue Office with proof of correct ownership (sale deed, mutation order, will). Patwar investigates and corrects within 15–30 days if evidence is clear. If disputed, may go to Tahsildar or civil court."
            },
            {
                "q": "Is 7/12 the same as mutation extract?",
                "a": "No. 7/12 is a current rights record; mutation extract shows the transaction/approval of ownership transfer. 7/12 is the 'who owns today'; mutation record is 'how ownership changed.'"
            },
        ],

        "common_issues": [
            "7/12 shows agricultural classification but property is residential — file rectification petition with building plan/completion certificate",
            "7/12 shows old owner name despite mutation approval — verify mutation is complete; if not, accelerate mutation; then apply for fresh 7/12",
            "7/12 not available online or long delays — visit Taluka office in person; escalate to Tahsildar if delays exceed 7 days",
            "7/12 shows mortgage/lien from old loan — ensure loan is discharged; get bank's discharge deed and register it; apply for fresh 7/12",
            "Cannot access state portal (technical issues) — visit Taluka office with documents; Patwar can issue physical copy on spot",
        ],

        "legal_protections": [
            "State Land Records Act (Maharashtra: Land Survey Act, 1965) — mandates Taluka to maintain and issue 7/12 records; public can request anytime",
            "Right to Information Act, 2005 — applicant can RTI if 7/12 denied or delayed unreasonably",
            "Transfer of Property Act, 1882 — 7/12 with mutation order is strong proof of land ownership",
            "Evidence Act, 1872 — 7/12 issued by revenue officer is admissible evidence of land rights in court",
        ],

        "disclaimer": "This guidance is for informational purposes only and does not constitute legal advice. 7/12 procedures, fees, and portal availability vary by state (Maharashtra, Karnataka, Gujarat, etc.). Online portals may differ in layout and process. We recommend verifying current procedures with your local Taluka Revenue Office or accessing the state's official land records portal for real-time guidance.",
    },

    "ferfar": {
        "display_name": "Ferfar / Field Map (Naksha)",
        "icon": "🗺️",
        "authority": "District Survey Office / State Revenue Department",
        "governing_law": "State Land Survey Act; State Measurement & Records Rules",
        "official_portal": "https://mahabhulekh.maharashtra.gov.in (Maharashtra) — state-specific survey portals",
        "overview": "Complete guide to obtaining Ferfar (also called Field Map or Naksha), the official survey map showing exact boundaries, area measurements, and neighboring properties. Essential for land disputes, property sales, construction permits, and legal ownership disputes.",

        "services": [
            {
                "service": "Understand Ferfar Components",
                "description": "Learn how to read Ferfar: survey number, area, boundaries, neighbors, and measurements.",
                "where": "Self-education or District Survey Office consultation",
                "documents_required": [
                    "Property details: survey number, village, taluka",
                    "Identity proof (Aadhaar, PAN, DL)",
                ],
                "fee": "Free (informational)",
                "timeline": "1–2 hours",
                "official_link": "https://mahabhulekh.maharashtra.gov.in/",
            },
            {
                "service": "Obtain Ferfar Copy from Survey Office",
                "description": "Request official Ferfar map (paper or digital) from District Survey Office or state portal.",
                "where": "State land survey online portal or District Survey Office",
                "documents_required": [
                    "Survey number and village name",
                    "Property address",
                    "Identity proof (Aadhaar/PAN)",
                    "Application form (Survey Office template)",
                ],
                "fee": "₹50–₹200 per copy (paper); ₹10–₹50 (digital)",
                "timeline": "2–7 days (physical); instant (digital)",
                "official_link": "https://mahabhulekh.maharashtra.gov.in/",
            },
            {
                "service": "Verify Ferfar Boundaries & Neighbors",
                "description": "Check Ferfar against actual ground boundaries and adjacent properties; identify boundary disputes.",
                "where": "On-site inspection with Ferfar; verify with neighbors and local Taluka records",
                "documents_required": [
                    "Ferfar copy (official)",
                    "Property visit (survey verification)",
                    "Neighbor consent or acknowledgment (optional)",
                ],
                "fee": "Free (self-check); ₹5,000–₹15,000 if hiring land surveyor for professional verification",
                "timeline": "1 day for self-check; 5–10 days for professional survey",
                "official_link": "https://mahabhulekh.maharashtra.gov.in/",
            },
            {
                "service": "Correct Ferfar Errors (Boundary/Area Rectification)",
                "description": "File petition if Ferfar shows wrong area, incorrect boundaries, or survey errors.",
                "where": "District Survey Office or Taluka Revenue Office",
                "documents_required": [
                    "Current Ferfar showing error",
                    "Professional land survey report (if boundary dispute)",
                    "Rectification petition (Survey Office template)",
                    "Identity proof",
                    "Ground photos/evidence of boundary mismatch",
                ],
                "fee": "₹500–₹2,000 for rectification petition; ₹5,000–₹15,000 for professional survey",
                "timeline": "30–60 days for rectification approval",
                "official_link": "https://mahabhulekh.maharashtra.gov.in/",
            },
            {
                "service": "Use Ferfar for Property Sale / Construction Permit",
                "description": "Present Ferfar to buyers, builders, or municipal authorities as proof of exact land area and boundaries.",
                "where": "Property buyer advocate, builder, or municipal corporation",
                "documents_required": [
                    "Official Ferfar copy",
                    "Related sale/construction documents",
                ],
                "fee": "No fee; cost covered by transaction",
                "timeline": "Same-day submission",
                "official_link": "https://mahabhulekh.maharashtra.gov.in/",
            },
        ],

        "faqs": [
            {
                "q": "What is the difference between Ferfar and 7/12?",
                "a": "Ferfar is the MAP/BOUNDARIES (survey number, area, neighbors); 7/12 is the RIGHTS RECORD (who owns, occupation type). Ferfar = 'where'; 7/12 = 'who.' Both are needed for complete land ownership proof."
            },
            {
                "q": "Is Ferfar accepted as proof of ownership?",
                "a": "Ferfar alone is not proof of ownership; it's proof of land boundaries and area. Combined with 7/12 and sale deed, Ferfar establishes complete ownership and boundaries. Banks and buyers accept Ferfar + 7/12 + deed as strong ownership proof."
            },
            {
                "q": "What if Ferfar area doesn't match sale deed area?",
                "a": "Discrepancy must be resolved before sale. Compare old and new Ferfar; check if land was subdivided or merged. If error, file rectification petition. Both documents must match for legal validity."
            },
            {
                "q": "Can neighbors object based on Ferfar boundaries?",
                "a": "Yes. If neighbors dispute boundaries shown in Ferfar, case goes to revenue office or civil court. Professional land survey + Ferfar are used to resolve boundary disputes. Legal resolution required before property sale."
            },
            {
                "q": "How often is Ferfar updated?",
                "a": "Ferfar is updated when land is subdivided, merged, or boundaries change (mutation). Get fresh Ferfar copy after any subdivision/merger. Older Ferfar may not reflect current state."
            },
        ],

        "common_issues": [
            "Ferfar shows different area than sale deed — investigate if subdivided; request updated Ferfar; rectify deed if needed",
            "Ferfar boundaries don't match ground reality — hire land surveyor; file boundary rectification petition; resolve with neighbors",
            "Ferfar obtained from old survey (pre-mutation) — obtain fresh Ferfar after mutation approval to show current state",
            "Neighbor disputes Ferfar boundary — attempt negotiation; if failed, file suit in civil court for boundary declaration",
            "Ferfar not available in state portal — visit District Survey Office in person; request manual copy from survey records",
        ],

        "legal_protections": [
            "State Land Survey Act (varies by state) — mandates accurate surveying; survey errors can be challenged and corrected",
            "Transfer of Property Act, 1882 — sale deed must match Ferfar boundaries; mismatch raises title questions",
            "Specific Relief Act, 1963 — allows boundary rectification suits in civil court for disputed Ferfar boundaries",
            "Indian Easement Act, 1882 — disputes over boundaries shown in Ferfar may invoke easement or boundary-fixing provisions",
        ],

        "disclaimer": "This guidance is for informational purposes only and does not constitute legal advice. Ferfar procedures, availability, and accuracy vary by state (Maharashtra, Karnataka, Gujarat, etc.). Boundary disputes can involve legal proceedings; we recommend consulting a land surveyor or advocate familiar with your region's land records before making decisions based on Ferfar. Ground boundaries should always be verified independently.",
    },

    "index_ii": {
        "display_name": "Index II / Encumbrance Certificate",
        "icon": "📜",
        "authority": "District Sub-Registrar Office",
        "governing_law": "Registration Act, 1908; State-Specific Land Records Act",
        "official_portal": "https://igrsup.gov.in/en/service/encumbrance-certificate-ec/ (UP) — state-specific",
        "overview": "Complete guide to Index II, an official document showing all mortgages, liens, and legal claims registered against a property. Index II is the same as Encumbrance Certificate (EC). Essential for bank loans and property sales to prove clear title.",

        "services": [
            {
                "service": "Understand Index II / Encumbrance Certificate",
                "description": "Learn what Index II shows and why it's critical for property transactions.",
                "where": "Self-education or Sub-Registrar office consultation",
                "documents_required": [
                    "Property details: survey number, registration office district",
                    "Identity proof (Aadhaar, PAN, DL)",
                ],
                "fee": "Free (informational)",
                "timeline": "1 hour",
                "official_link": "https://igrsup.gov.in/en/service/encumbrance-certificate-ec/",
            },
            {
                "service": "Apply for Index II Online",
                "description": "Request Index II digitally through Sub-Registrar online portal.",
                "where": "Sub-Registrar online portal (state-specific)",
                "documents_required": [
                    "Property survey number and address",
                    "Identity proof (Aadhaar/PAN)",
                    "Proof of interest (ownership proof preferred but not always required)",
                ],
                "fee": "₹50–₹200 (varies by state and search years)",
                "timeline": "5–10 working days",
                "official_link": "https://igrsup.gov.in/en/service/encumbrance-certificate-ec/",
            },
            {
                "service": "Obtain Index II from Sub-Registrar Office",
                "description": "Apply in person for Index II / EC at Sub-Registrar office.",
                "where": "District Sub-Registrar Office",
                "documents_required": [
                    "EC application form (Sub-Registrar template)",
                    "Property details: survey number, taluka, district",
                    "Ownership proof (sale deed, 7/12, mutation order, etc.)",
                    "Identity proof (Aadhaar, PAN, DL, Passport)",
                    "Cheque/cash for Index II fee",
                ],
                "fee": "₹50–₹200 per copy (varies by state and search years; typically ₹100–₹150 for 10-year search)",
                "timeline": "5–10 working days",
                "official_link": "https://igrsup.gov.in/en/service/encumbrance-certificate-ec/",
            },
            {
                "service": "Verify Index II Information & Resolve Encumbrances",
                "description": "Review Index II to check for mortgages, liens, or claims; resolve if any exist.",
                "where": "Sub-Registrar office or mortgagee bank for resolution",
                "documents_required": [
                    "Obtained Index II document",
                    "Loan account details (if mortgage shown)",
                    "Bank discharge deed (if loan repaid)",
                ],
                "fee": "Free (review); ₹500–₹2,000 (bank discharge fee if needed)",
                "timeline": "1 hour (review); 5–10 days (discharge processing)",
                "official_link": "https://igrsup.gov.in/en/service/encumbrance-certificate-ec/",
            },
            {
                "service": "Use Index II for Bank Loan / Property Sale",
                "description": "Present Index II to banks and buyers as proof of clear title (no mortgages/claims).",
                "where": "Bank or property buyer",
                "documents_required": [
                    "Original Index II document",
                    "Recent copy (prefer <6 months old)",
                ],
                "fee": "No fee; cost covered by loan/sale",
                "timeline": "Same-day submission",
                "official_link": "https://www.sbicard.com/en/personal/loans/home-loan/documents-required.html",
            },
        ],

        "faqs": [
            {
                "q": "What is Index II or Encumbrance Certificate (EC)?",
                "a": "Index II and EC are the same document. Index II is the old term; Encumbrance Certificate (EC) is the current standard name. It lists all mortgages, liens, and registered claims against a property. If 'No Encumbrance' is stated, property is clear of mortgages and legal claims."
            },
            {
                "q": "Is Index II mandatory for property sale?",
                "a": "Not legally mandatory, but practically essential. Buyers and banks insist on Index II to ensure no hidden mortgages or claims. Without Index II, property sale is risky and may be challenged later by mortgagees."
            },
            {
                "q": "What if Index II shows a mortgage but loan is already repaid?",
                "a": "Obtain 'Discharge Deed' or 'No Objection Certificate' from the bank. Register the discharge deed at Sub-Registrar. Then apply for a fresh Index II, which will show 'No Encumbrance.'"
            },
            {
                "q": "How long is Index II valid?",
                "a": "Index II is technically valid indefinitely but reflects status as of issue date. For transactions, banks prefer recent Index II (issued within 6 months). If >6 months old, obtain a fresh copy."
            },
            {
                "q": "Can I apply for Index II if I'm not the owner?",
                "a": "Ownership proof is typically required, but many Sub-Registrars allow anyone to apply. Best practice: show property interest (ownership deed, rental agreement, mortgage). Always bring identification and property details."
            },
        ],

        "common_issues": [
            "Index II shows mortgage from previous owner not discharged — obtain discharge deed from bank, register it, request fresh Index II",
            "Index II shows pending court case — legal claim must be resolved before sale; petition court if case is dormant/old",
            "Index II delayed or application rejected — verify property details (survey number, office district); resubmit with complete documents; escalate to District Registrar",
            "Index II shows third-party lien (heir's claim, mortgagee) — negotiate settlement and obtain NOC; register settlement deed; request updated Index II",
            "Different Index II for same property — verify survey number; rectify if incorrect; request Index II for correct property details",
        ],

        "legal_protections": [
            "Registration Act, 1908 — mandates Sub-Registrar to issue Index II; issuance is a statutory right; delays can be challenged via RTI",
            "Transfer of Property Act, 1882 — clear Index II is strong proof of marketable title for property sale",
            "Right to Information Act, 2005 — applicant can RTI if Index II delayed beyond 10 days",
            "Consumer Protection Act, 2019 — applies if bank/provider misuses Index II or causes financial loss through delayed issuance",
        ],

        "disclaimer": "This guidance is for informational purposes only and does not constitute legal advice. Index II availability, search period, and procedures vary by state and Sub-Registrar office. A clear Index II does not guarantee property is absolutely free from all risks; it only shows registered encumbrances up to the specified date. For comprehensive title verification, we recommend engaging a title insurance company or registered advocate before major transactions.",
    },

    "registration": {
        "display_name": "Property Registration",
        "icon": "✅",
        "authority": "State Sub-Registrar Office",
        "governing_law": "Registration Act, 1908; Transfer of Property Act, 1882",
        "official_portal": "https://igrsup.gov.in/ (Uttar Pradesh) — state-specific portals vary",
        "overview": "Complete guide to registering property at the Sub-Registrar office. Registration is the final legal step after property sale, making the transaction binding and enforceable. Unregistered property sales have no legal validity in court.",

        "services": [
            {
                "service": "Prepare & Stamp Sale Deed",
                "description": "Draft sale deed with all legal clauses; affix correct stamp duty to make it valid.",
                "where": "Advocate's office or online legal services",
                "documents_required": [
                    "Seller ownership proof (previous sale deed, will, mutation, etc.)",
                    "Property details (survey number, area, address, market value)",
                    "Buyer's identity proof and residence proof",
                    "Seller's identity proof and residence proof",
                    "Property tax receipt (last 2 years)",
                    "Building plan and completion certificate",
                    "NOC from mortgagee if property is under loan",
                ],
                "fee": "Stamp duty: 5–6% of property value (state-dependent); Advocate: ₹2,000–₹10,000",
                "timeline": "3–5 days for drafting and stamping",
                "official_link": "https://www.thehindu.com/news/national/property-registration-in-india/",
            },
            {
                "service": "Apply for Registration at Sub-Registrar",
                "description": "Submit stamped sale deed and documents for official registration.",
                "where": "State Sub-Registrar office (property's district/taluka)",
                "documents_required": [
                    "Signed and stamped sale deed (original + copies)",
                    "Identity proofs of buyer & seller (Aadhaar/PAN/DL/Passport)",
                    "Proof of residence for both parties",
                    "Previous ownership documents (sale deed, will, mutation, etc.)",
                    "Property tax receipt (latest 2 years)",
                    "Encumbrance Certificate (EC) — 'No Encumbrance' or clearance from mortgagee",
                    "Cheque for registration fee (1–2% of property value)",
                    "Application form (Sub-Registrar template or online portal)",
                ],
                "fee": "Registration fee: 1–2% of property value (state-dependent); e-registration discount: 0.5–1% in some states",
                "timeline": "15–30 days (standard); e-registration may expedite to 5–10 days",
                "official_link": "https://igrsup.gov.in/en/service/online-registration/",
            },
            {
                "service": "E-Registration (Online Registration)",
                "description": "Register property online; faster and more secure than manual registration.",
                "where": "State Sub-Registrar online portal (available in Maharashtra, UP, Karnataka, etc.)",
                "documents_required": [
                    "Scanned copy of stamped sale deed",
                    "Digital identity proofs",
                    "Online application form (portal link)",
                    "Payment via online gateway (credit/debit/net banking)",
                ],
                "fee": "Same as manual registration; often 0.5–1% discount for e-registration",
                "timeline": "5–10 working days typically; appointment booked online",
                "official_link": "https://mahabhulekh.maharashtra.gov.in/ (Maharashtra e-registration)",
            },
            {
                "service": "Physical Appearance & Deed Signing",
                "description": "Appear in person at Sub-Registrar office, verify deed, and sign in presence of registrar and witnesses.",
                "where": "Sub-Registrar office (scheduled appointment date)",
                "documents_required": [
                    "Original stamped deed",
                    "Original identity proofs (both parties)",
                    "Original residence proofs",
                    "Previous ownership documents",
                ],
                "fee": "Included in registration fee",
                "timeline": "2–4 hours for completion (appointment on scheduled date)",
                "official_link": "https://igrsup.gov.in/en/service/online-registration/",
            },
            {
                "service": "Receive Registered Deed & Completion Certificate",
                "description": "Obtain original registered deed (with Sub-Registrar stamp & signature) and registration completion certificate.",
                "where": "Sub-Registrar office (same office where registered)",
                "documents_required": [
                    "Receipt of application (issued after registration)",
                    "Identification (ID proof for identity verification)",
                ],
                "fee": "₹50–₹100 per certified copy (if additional copies needed)",
                "timeline": "Immediate after registration completion (same day or next business day)",
                "official_link": "https://igrsup.gov.in/",
            },
        ],

        "faqs": [
            {
                "q": "Is registration mandatory for property sale?",
                "a": "Yes. Under Registration Act, 1908, property sale deed must be registered to be valid and enforceable. Unregistered deed has no legal validity in court. If dispute arises, unregistered deed cannot be used as evidence. Registration makes sale legally binding."
            },
            {
                "q": "What is the difference between stamping and registration?",
                "a": "Stamping is affixing tax (stamp duty) on the deed to make it a valid document. Registration is the official recording of the stamped deed with the government Sub-Registrar. Both are mandatory: first stamp, then register."
            },
            {
                "q": "Do both buyer and seller have to appear for registration?",
                "a": "Yes, typically both must appear in person at Sub-Registrar office and sign the deed in the registrar's presence. However, in some cases, power of attorney or authorized representative may be permitted (check state rules). E-registration may allow digital signatures in future."
            },
            {
                "q": "What happens if I register property in my name alone but spouse contributed to purchase?",
                "a": "Legal title rests with the registered owner. If spouse contributed, they should be registered as co-owner (joint deed) to protect their ownership right. Later claims by spouse may be disputed in court. Register property correctly at time of purchase."
            },
            {
                "q": "How long does registration take?",
                "a": "Manual registration: 15–30 days. E-registration (online): 5–10 days in most states. Timeline can extend if Sub-Registrar raises queries or requests additional documents. Follow up via online status tracker if available."
            },
        ],

        "common_issues": [
            "Deed rejected due to under-stamping — pay additional stamp duty + penalty (interest); resubmit deed for registration",
            "Sub-Registrar raises objection on property details — provide clear title documents; rectify mutation if needed; escalate to District Registrar if issue persists",
            "One party absent on registration date — registration cannot proceed; reschedule appointment; or file power of attorney allowing one party to sign on behalf of other",
            "Registration delayed beyond promised timeline — follow up with Sub-Registrar; file RTI if delayed >30 days; escalate to District Registrar",
            "Registered deed contains error (wrong address, name spelling) — apply for 'Rectification of Error' form at Sub-Registrar; pay rectification fee; submit corrected deed",
        ],

        "legal_protections": [
            "Registration Act, 1908 — mandates registration of property sales; Section 17 declares registered deed conclusive evidence of transaction",
            "Transfer of Property Act, 1882 — establishes requirement of registered deed for property transfer; unregistered deed not valid for ownership transfer",
            "Stamp Act, 1899 — requires stamp duty on all property deeds; under-stamped deed penalties can be 10x the deficiency amount",
            "Right to Information Act, 2005 — applicant can file RTI if registration is delayed beyond statutory timeline (typically 15–30 days)",
        ],

        "disclaimer": "This guidance is for informational purposes only and does not constitute legal advice. Registration procedures, timelines, and fees vary by state and Sub-Registrar office. E-registration availability is expanding but not uniformly available in all states or for all property types. We strongly recommend consulting a registered advocate before property registration to ensure deed is correctly drafted, properly stamped, and all documents are in order. Registration errors can have long-term legal consequences.",
    },
}


# ── Helper Functions ────────────────────────────────────────────────────────

def get_all_property_types() -> list[dict]:
    """Return summary list of all 8 property types for hub grid."""
    return [
        {
            "key": "sale",
            "display_name": PROPERTY_KB["sale"]["display_name"],
            "icon": PROPERTY_KB["sale"]["icon"],
            "authority": PROPERTY_KB["sale"]["authority"],
            "official_portal": PROPERTY_KB["sale"]["official_portal"],
        },
        {
            "key": "rental",
            "display_name": PROPERTY_KB["rental"]["display_name"],
            "icon": PROPERTY_KB["rental"]["icon"],
            "authority": PROPERTY_KB["rental"]["authority"],
            "official_portal": PROPERTY_KB["rental"]["official_portal"],
        },
        {
            "key": "mutation",
            "display_name": PROPERTY_KB["mutation"]["display_name"],
            "icon": PROPERTY_KB["mutation"]["icon"],
            "authority": PROPERTY_KB["mutation"]["authority"],
            "official_portal": PROPERTY_KB["mutation"]["official_portal"],
        },
        {
            "key": "encumbrance",
            "display_name": PROPERTY_KB["encumbrance"]["display_name"],
            "icon": PROPERTY_KB["encumbrance"]["icon"],
            "authority": PROPERTY_KB["encumbrance"]["authority"],
            "official_portal": PROPERTY_KB["encumbrance"]["official_portal"],
        },
        {
            "key": "registration",
            "display_name": PROPERTY_KB["registration"]["display_name"],
            "icon": PROPERTY_KB["registration"]["icon"],
            "authority": PROPERTY_KB["registration"]["authority"],
            "official_portal": PROPERTY_KB["registration"]["official_portal"],
        },
        {
            "key": "7/12",
            "display_name": PROPERTY_KB["7/12"]["display_name"],
            "icon": PROPERTY_KB["7/12"]["icon"],
            "authority": PROPERTY_KB["7/12"]["authority"],
            "official_portal": PROPERTY_KB["7/12"]["official_portal"],
        },
        {
            "key": "ferfar",
            "display_name": PROPERTY_KB["ferfar"]["display_name"],
            "icon": PROPERTY_KB["ferfar"]["icon"],
            "authority": PROPERTY_KB["ferfar"]["authority"],
            "official_portal": PROPERTY_KB["ferfar"]["official_portal"],
        },
        {
            "key": "index_ii",
            "display_name": PROPERTY_KB["index_ii"]["display_name"],
            "icon": PROPERTY_KB["index_ii"]["icon"],
            "authority": PROPERTY_KB["index_ii"]["authority"],
            "official_portal": PROPERTY_KB["index_ii"]["official_portal"],
        },
    ]


def get_property_guidance(property_type: str) -> dict | None:
    """Return full guidance for one property type."""
    normalized = _normalize_property_type(property_type)
    return PROPERTY_KB.get(normalized) if normalized else None


def get_property_checklist(property_type: str, service: str) -> list[str] | None:
    """Return document checklist for a specific service within a property type."""
    normalized = _normalize_property_type(property_type)
    if not normalized or normalized not in PROPERTY_KB:
        return None

    for svc in PROPERTY_KB[normalized].get("services", []):
        if svc["service"].lower() == service.lower():
            return svc.get("documents_required", [])

    return None


def _normalize_property_type(raw: str) -> str | None:
    """Normalize user input to canonical property type key."""
    if not raw:
        return None

    raw_lower = raw.lower().strip()

    # Exact match
    if raw_lower in PROPERTY_KB:
        return raw_lower

    # Alias map
    aliases = {
        "property sale": "sale",
        "sale deed": "sale",
        "property transfer": "sale",
        "property rental": "rental",
        "rental agreement": "rental",
        "lease": "rental",
        "leave and licence": "rental",
        "mutation": "mutation",
        "dakhil kharij": "mutation",
        "ownership transfer": "mutation",
        "encumbrance": "encumbrance",
        "encumbrance certificate": "encumbrance",
        "ec": "encumbrance",
        "index ii": "index_ii",
        "index 2": "index_ii",
        "registration": "registration",
        "property registration": "registration",
        "sub-registrar": "registration",
        "7/12": "7/12",
        "712": "7/12",
        "record of rights": "7/12",
        "ferfar": "ferfar",
        "field map": "ferfar",
        "naksha": "ferfar",
        "survey map": "ferfar",
    }

    return aliases.get(raw_lower)
