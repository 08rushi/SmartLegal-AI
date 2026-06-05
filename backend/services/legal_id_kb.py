"""
Legal ID Knowledge Base for SmartLegal-AI Phase 4A.

Guidance platform for 6 Indian government ID types:
- Aadhaar
- PAN
- Driving Licence
- Passport
- Voter ID
- Government Certificates (Birth, Death, Caste, Income, Domicile)

All data is static, verified, and deterministic.
Sources: Official government portals and acts.
"""

LEGAL_ID_KB = {
    "aadhaar": {
        "display_name": "Aadhaar Card",
        "icon": "🪪",
        "authority": "UIDAI (Unique Identification Authority of India)",
        "governing_law": "Aadhaar (Targeted Delivery of Financial and Other Subsidies, Benefits and Services) Act, 2016",
        "official_portal": "https://myaadhaar.uidai.gov.in",
        "overview": "Aadhaar is a 12-digit unique identification number issued to all Indian residents. It is based on biometric and demographic data (iris, fingerprint, face) and is accepted as proof of identity and address.",
        "services": [
            {
                "service": "New Enrolment",
                "description": "Get your first Aadhaar card as an Indian resident.",
                "where": "Aadhaar Enrolment Centres (Post Offices, Bank Branches, State Govt offices)",
                "documents_required": [
                    "Proof of Identity: Pan card, Passport, Voter ID, DL, or other government ID",
                    "Proof of Address: Utility bill, bank statement, or property lease within last 3 months",
                    "Date of Birth proof: Birth certificate, school certificate, or passport"
                ],
                "fee": "Free",
                "timeline": "90 days for card delivery",
                "official_link": "https://uidai.gov.in/enrolment-update/",
            },
            {
                "service": "Update Name",
                "description": "Change registered name due to marriage, legal change, or error.",
                "where": "myAadhaar portal online OR Aadhaar Enrolment Centre offline",
                "documents_required": [
                    "New name proof: Marriage certificate, court order, gazette notification, or updated PAN",
                    "Old name proof: Original Aadhaar letter",
                    "Address proof (if address changed)"
                ],
                "fee": "Free online, free at centre",
                "timeline": "30 days online, 90 days offline",
                "official_link": "https://myaadhaar.uidai.gov.in/",
            },
            {
                "service": "Update Date of Birth",
                "description": "Correct registered DOB if there was an error during enrolment.",
                "where": "myAadhaar portal online OR Aadhaar Enrolment Centre",
                "documents_required": [
                    "Proof of DOB: Birth certificate, school certificate, passport, or PAN",
                    "Identity proof: Aadhaar letter"
                ],
                "fee": "Free",
                "timeline": "30-90 days",
                "official_link": "https://myaadhaar.uidai.gov.in/",
            },
            {
                "service": "Update Address",
                "description": "Change registered address due to relocation.",
                "where": "myAadhaar portal online OR Aadhaar Enrolment Centre",
                "documents_required": [
                    "New address proof: Utility bill, bank statement, property lease, or rental agreement (last 3 months)",
                    "Identity proof: Aadhaar letter"
                ],
                "fee": "Free online, free at centre",
                "timeline": "30 days online, 90 days offline",
                "official_link": "https://myaadhaar.uidai.gov.in/",
            },
            {
                "service": "Link Mobile Number",
                "description": "Link your mobile number to your Aadhaar for receiving OTPs and updates.",
                "where": "myAadhaar portal online OR Aadhaar Enrolment Centre OR authorized banking partners",
                "documents_required": [
                    "Aadhaar number",
                    "OTP sent to registered email/mobile"
                ],
                "fee": "Free",
                "timeline": "Instant online",
                "official_link": "https://myaadhaar.uidai.gov.in/",
            },
            {
                "service": "Lost or Damaged Card Replacement",
                "description": "Get a new card if your Aadhaar is lost, damaged, or destroyed.",
                "where": "myAadhaar portal online OR Aadhaar Enrolment Centre",
                "documents_required": [
                    "Identity proof (if lost)",
                    "Damaged card (if damaged)"
                ],
                "fee": "Free",
                "timeline": "90 days",
                "official_link": "https://uidai.gov.in/enrolment-update/",
            },
        ],
        "faqs": [
            {
                "q": "Is Aadhaar mandatory?",
                "a": "Aadhaar is optional under Section 7 of the Aadhaar Act. However, it is linked to many government and financial services, making it practically necessary for accessing subsidies, opening bank accounts, filing taxes, etc."
            },
            {
                "q": "Can my Aadhaar be rejected due to biometric data issues?",
                "a": "Yes. If your fingerprints or iris cannot be captured due to age (under 5 years old), injury, or disease, you may be unable to obtain Aadhaar. However, you can try at a later date."
            },
            {
                "q": "What happens if I lose my Aadhaar card?",
                "a": "It is safe to lose your card because Aadhaar is a number, not a physical document. Your identity remains secure. Get a duplicate card by applying online on myAadhaar portal or at an enrolment centre."
            },
            {
                "q": "Can Aadhaar be linked to multiple phone numbers?",
                "a": "Only one mobile number can be linked to your Aadhaar at a time. You can unlink and link a new number on myAadhaar portal."
            },
            {
                "q": "What is NREGA and how does it use Aadhaar?",
                "a": "NREGA (National Rural Employment Guarantee Act) is a job guarantee scheme. Aadhaar is mandatory for registration under NREGA for rural workers."
            },
        ],
        "common_issues": [
            "Biometric data not accepted at enrolment (older adults, physical disability)",
            "Aadhaar not received after 90 days (lost in transit, incorrect address)",
            "Name/DOB/address recorded incorrectly during enrolment",
            "Aadhaar temporarily blocked due to multiple incorrect OTP attempts",
            "Aadhaar stolen or used fraudulently (very rare due to biometric verification)"
        ],
        "legal_protections": [
            "Section 29 of Aadhaar Act: Aadhaar number cannot be published or displayed publicly.",
            "Section 33: Aadhaar data can only be accessed by court order or for national security reasons.",
            "Section 3: Aadhaar is voluntary unless a law specifically mandates it.",
            "UIDAI maintains strict data security with biometric encryption and limited access protocols."
        ],
        "disclaimer": "SmartLegal-AI provides guidance only. Aadhaar laws and procedures may change. Always verify current details on the official UIDAI portal (https://uidai.gov.in) before visiting an enrolment centre. For disputes, contact UIDAI Resident Grievance through the MyAadhaar portal."
    },

    "pan": {
        "display_name": "PAN Card",
        "icon": "📋",
        "authority": "Income Tax Department (Ministry of Finance)",
        "governing_law": "Income Tax Act, 1961",
        "official_portal": "https://www.incometaxindiaefiling.gov.in",
        "overview": "PAN (Permanent Account Number) is a 10-character alphanumeric identifier issued by the Income Tax Department. It is mandatory for financial transactions, tax filing, and business activities.",
        "services": [
            {
                "service": "New PAN Application",
                "description": "Apply for your first PAN if you don't have one.",
                "where": "NSDL or UTIITSL online portals OR through a CA or tax consultant",
                "documents_required": [
                    "Identity proof: Passport, Aadhaar, DL, Voter ID, or passport",
                    "Address proof: Utility bill, bank statement, or property lease",
                    "Birth certificate or age proof",
                    "Passport-sized color photograph"
                ],
                "fee": "Free if applied online, ₹93 if applied through intermediary",
                "timeline": "1-2 weeks for digital PAN, 15-30 days for physical card",
                "official_link": "https://www.nsdl.co.in/panning.html",
            },
            {
                "service": "PAN Correction / Modification",
                "description": "Correct errors in your name, DOB, or address recorded on your PAN.",
                "where": "NSDL or UTIITSL online portal OR Income Tax office",
                "documents_required": [
                    "Old PAN card or acknowledgment",
                    "Proof of corrected information: updated document (marriage cert, court order, etc.)",
                    "Affidavit on stamp paper for name/DOB changes"
                ],
                "fee": "₹93 application fee (if through intermediary)",
                "timeline": "1-2 weeks online, 30-45 days offline",
                "official_link": "https://www.utiitsl.com/",
            },
            {
                "service": "Duplicate / Lost PAN",
                "description": "Obtain a duplicate PAN or recover lost PAN after verification.",
                "where": "NSDL or UTIITSL online portal OR Income Tax office",
                "documents_required": [
                    "Identity proof",
                    "Address proof",
                    "Affidavit if original lost"
                ],
                "fee": "₹93 for replacement through portal",
                "timeline": "1-2 weeks",
                "official_link": "https://www.nsdl.co.in/",
            },
            {
                "service": "Link PAN with Aadhaar",
                "description": "Mandatory to link PAN with Aadhaar. Non-linking can lead to penalties and account suspension.",
                "where": "myIncometax or third-party portals online",
                "documents_required": [
                    "PAN number",
                    "Aadhaar number",
                    "OTP verification"
                ],
                "fee": "Free",
                "timeline": "Instant if names match (e-KYC), else 30 days for manual verification",
                "official_link": "https://www.incometaxindiaefiling.gov.in",
            },
            {
                "service": "e-PAN (Digital)",
                "description": "Get a digital PAN with all benefits of physical PAN but no physical card.",
                "where": "NSDL or UTIITSL online portal",
                "documents_required": [
                    "Identity proof with photo",
                    "Address proof",
                    "Birth certificate"
                ],
                "fee": "₹93 (optional if obtaining for first time)",
                "timeline": "Instant after verification",
                "official_link": "https://www.nsdl.co.in/panning.html",
            },
        ],
        "faqs": [
            {
                "q": "Is PAN mandatory for individuals?",
                "a": "PAN is optional unless your income exceeds ₹5 lakh/year, you want to open a bank account, invest in stock market, or conduct large financial transactions (>₹50,000)."
            },
            {
                "q": "What happens if I don't link PAN with Aadhaar?",
                "a": "Non-linking leads to: PAN deactivation, suspended bank transactions, loss of tax refunds, and penalties up to ₹10,000 after March 31, 2023."
            },
            {
                "q": "Can I have two PANs?",
                "a": "No. Having multiple PANs is illegal. If you have obtained a duplicate by mistake, inform the Income Tax Department immediately and surrender one."
            },
            {
                "q": "Can NRIs get PAN?",
                "a": "Yes. NRIs can apply for PAN online by providing proof of overseas address. PAN is required for NRI income and foreign investments."
            },
            {
                "q": "What is Form 49A vs Form 49?",
                "a": "Form 49A is for new PAN applicants. Form 49 is for PAN modification (correction of name, DOB, address). Form 60 is for individuals with no income."
            },
        ],
        "common_issues": [
            "PAN-Aadhaar mismatch due to name spelling differences",
            "PAN application rejected due to invalid documents",
            "Lost physical PAN card (digital copy serves the same purpose)",
            "Wrong PAN issued by mistake, requiring correction",
            "Inactive PAN due to non-filing of ITR or non-linking with Aadhaar"
        ],
        "legal_protections": [
            "PAN information is confidential under Income Tax Act Section 139A.",
            "Misuse of PAN for fraudulent purposes is a criminal offense.",
            "You have the right to correct incorrect PAN information free of cost.",
            "PAN cannot be cancelled without due notice and opportunity to explain."
        ],
        "disclaimer": "SmartLegal-AI provides guidance only. PAN rules change annually, especially regarding Aadhaar linking deadlines and penalties. Always check the official Income Tax Department portal or consult a CA before applying."
    },

    "driving_licence": {
        "display_name": "Driving Licence",
        "icon": "🚗",
        "authority": "State Road Transport Authority (RTA) / Motor Vehicles Department",
        "governing_law": "Motor Vehicles Act, 1988 and State-wise Rules",
        "official_portal": "https://sarathi.parivahan.gov.in (pan-India portal, state-specific links available)",
        "overview": "Driving Licence (DL) is the legal permission to operate motor vehicles on Indian roads. Different categories exist for cars, motorcycles, heavy vehicles, etc.",
        "services": [
            {
                "service": "Learner's Licence",
                "description": "Temporary permit to learn driving under supervision before obtaining permanent licence.",
                "where": "State RTA (Regional Transport Office) nearest to your address",
                "documents_required": [
                    "Identity proof: Aadhaar, PAN, Passport, Voter ID",
                    "Address proof: Same as above or utility bill",
                    "Date of birth proof: Birth certificate or school certificate",
                    "Passport-sized color photograph (4x6cm)",
                    "Filled Form 1 (Application for Learner's Licence)"
                ],
                "fee": "₹150 for two-wheeler, ₹200 for four-wheeler (varies by state)",
                "timeline": "Same day to 7 days after written test",
                "official_link": "https://sarathi.parivahan.gov.in",
            },
            {
                "service": "Permanent Driving Licence",
                "description": "Official license to drive vehicles legally on Indian roads. Valid for 5-10 years.",
                "where": "State RTA after holding learner's licence for minimum 30 days",
                "documents_required": [
                    "Learner's Licence (original + photocopy)",
                    "Identity proof",
                    "Address proof",
                    "Medical fitness certificate (Form 1A) from government doctor",
                    "Photograph",
                    "Form 8 (Application for Permanent Licence)"
                ],
                "fee": "₹600 for normal, ₹1,000 for heavy vehicle (varies by state)",
                "timeline": "30-60 days after application",
                "official_link": "https://sarathi.parivahan.gov.in",
            },
            {
                "service": "DL Renewal",
                "description": "Renew your expired or expiring Driving Licence.",
                "where": "State RTA or online through Sarathi portal (for many states)",
                "documents_required": [
                    "Old DL (original + photocopy)",
                    "Medical fitness certificate (Form 1A) if DL expired by >1 year or if age >50",
                    "Address proof (if changed)"
                ],
                "fee": "₹500-₹800 (varies by state and vehicle category)",
                "timeline": "1-30 days",
                "official_link": "https://sarathi.parivahan.gov.in",
            },
            {
                "service": "International Driving Permit (IDP)",
                "description": "Permit allowing you to drive in foreign countries. Valid only with passport and valid Indian DL.",
                "where": "State RTA with minimum 2 weeks notice",
                "documents_required": [
                    "Valid Driving Licence",
                    "Passport (original + photocopy)",
                    "Application Form",
                    "Photograph"
                ],
                "fee": "₹500-₹1,000",
                "timeline": "14-30 days",
                "official_link": "https://www.icmrindia.org",
            },
            {
                "service": "Duplicate or Lost DL",
                "description": "Obtain a replacement if your DL is lost, stolen, or damaged.",
                "where": "State RTA or online (for many states)",
                "documents_required": [
                    "Affidavit on stamp paper (for lost/stolen)",
                    "Identity proof",
                    "Address proof",
                    "Photograph"
                ],
                "fee": "₹500 (varies by state)",
                "timeline": "7-30 days",
                "official_link": "https://sarathi.parivahan.gov.in",
            },
        ],
        "faqs": [
            {
                "q": "Can I drive with just a Learner's Licence?",
                "a": "No. With LL, you must be accompanied by a licensed driver (age 21+, valid DL). Driving alone with LL is illegal and can result in ₹500-₹1000 fine."
            },
            {
                "q": "How long must I hold LL before getting permanent DL?",
                "a": "Minimum 30 days from the date of issue of Learner's Licence."
            },
            {
                "q": "What if my DL expires while I'm abroad?",
                "a": "Your expired DL is not valid. However, you can renew it online or through the RTA before traveling. An IDP (International Driving Permit) remains valid as long as your passport is valid."
            },
            {
                "q": "Can I hold two driving licences?",
                "a": "No. Having duplicate DLs from different states is illegal. You must surrender your old DL when obtaining a new one."
            },
            {
                "q": "What are DL categories?",
                "a": "Category LMV (cars), MCWG (motorcycles), MCWOG (heavy bikes), HMV (heavy commercial vehicles), PSV (public service vehicles for commercial use), etc."
            },
        ],
        "common_issues": [
            "Failing written test (rules, signs, safe driving)",
            "Failing practical driving test",
            "DL suspended due to traffic violations or unpaid fines",
            "DL disqualified due to serious traffic offense (drunk driving, rash driving)",
            "Address not updated after relocation"
        ],
        "legal_protections": [
            "Section 24, Motor Vehicles Act: Disqualification from driving is imposed only by court.",
            "Section 206: Suspension of DL requires government notification and opportunity to appeal.",
            "RTA must conduct written and practical tests fairly.",
            "Medical unfitness disqualification requires medical certificate review."
        ],
        "disclaimer": "SmartLegal-AI provides general guidance. Driving rules, fees, and procedures vary significantly by state. Check your state's RTA website (Sarathi portal) for specific timelines, fees, and required documents. Traffic violations and fines vary by state police and offense severity."
    },

    "passport": {
        "display_name": "Passport",
        "icon": "✈️",
        "authority": "Ministry of External Affairs (MEA) via Passport Seva Program",
        "governing_law": "Passport Act, 1967 and Passport Rules, 1980",
        "official_portal": "https://passportindia.gov.in",
        "overview": "Passport is the primary travel document issued to Indian citizens for international travel. It serves as proof of citizenship and identity.",
        "services": [
            {
                "service": "Fresh / New Passport",
                "description": "First time passport application as an Indian citizen.",
                "where": "Passport Seva Kendra (PSK) or post office (selected locations for normal service)",
                "documents_required": [
                    "Birth certificate or School certificate with DOB",
                    "Proof of identity: Aadhaar, PAN, voter ID, DL, or old passport",
                    "Proof of residence: Utility bill, bank statement, property deed (not older than 6 months)",
                    "Police Clearance Certificate (if applicable)",
                    "Self-attested photographs (4x6 cm, color, white background)",
                    "Filled Form 1 (New Passport Application)"
                ],
                "fee": "₹1,500 (36 pages, normal), ₹2,000 (60 pages, normal), ₹3,500 (36 pages, Tatkal), ₹4,500 (60 pages, Tatkal)",
                "timeline": "30-45 days (normal service), 1-2 weeks (Tatkal service)",
                "official_link": "https://passportindia.gov.in",
            },
            {
                "service": "Passport Renewal",
                "description": "Renew your passport when it is about to expire or has already expired.",
                "where": "Passport Seva Kendra or online for some states",
                "documents_required": [
                    "Old passport (original + photocopy of first and last pages)",
                    "Birth certificate (if changed, else old passport suffices)",
                    "Address proof (if changed)",
                    "Photographs",
                    "Filled Form 2 (Renewal Application)"
                ],
                "fee": "₹1,500 (36 pages, normal)",
                "timeline": "1-4 weeks (normal), 1 week (expedited, ₹3,500)",
                "official_link": "https://passportindia.gov.in",
            },
            {
                "service": "Reissue (Name, Address, DOB Change)",
                "description": "Reissue passport when your name, address, or DOB changes.",
                "where": "Passport Seva Kendra",
                "documents_required": [
                    "Old passport",
                    "Court order (for name change) or marriage certificate",
                    "New address proof",
                    "Affidavit on stamp paper",
                    "Police Clearance Certificate (if applicable)",
                    "Photographs"
                ],
                "fee": "₹2,000 (new passport issued, old one cancelled)",
                "timeline": "30-45 days (normal), 1-2 weeks (Tatkal, ₹4,500)",
                "official_link": "https://passportindia.gov.in",
            },
            {
                "service": "Lost / Damaged Passport",
                "description": "Apply for replacement if your passport is lost, stolen, or damaged.",
                "where": "Passport Seva Kendra",
                "documents_required": [
                    "FIR (if lost/stolen) or proof of damage (if damaged)",
                    "Birth certificate or age proof",
                    "Identity proof",
                    "Address proof",
                    "Affidavit on stamp paper",
                    "Photographs",
                    "Filled Form 1 (treated as fresh application)"
                ],
                "fee": "₹1,500-₹2,000 (fresh passport issued)",
                "timeline": "30-45 days (normal), 1-2 weeks (Tatkal)",
                "official_link": "https://passportindia.gov.in",
            },
            {
                "service": "Minor Passport",
                "description": "Passport for children under 18 years. Guardian consent required.",
                "where": "Passport Seva Kendra",
                "documents_required": [
                    "Birth certificate",
                    "Guardian's identity proof (Aadhaar, PAN, DL, etc.)",
                    "Guardian's address proof",
                    "Child's photograph and guardian's signature",
                    "Consent of both parents (if child is minor)"
                ],
                "fee": "₹1,500 (36 pages)",
                "timeline": "30-45 days",
                "official_link": "https://passportindia.gov.in",
            },
        ],
        "faqs": [
            {
                "q": "What is the difference between Normal and Tatkal passport?",
                "a": "Tatkal (urgent) service is processed in 1-2 weeks for an additional fee of ₹2,000-₹2,500. Applicants must have valid reason (work/medical emergency, booked travel). Tatkal service requires in-person application."
            },
            {
                "q": "Can I travel if my passport is in police verification stage?",
                "a": "No. You can only travel after police clearance is complete and your passport is issued. Police verification typically takes 7-14 days."
            },
            {
                "q": "What if my passport is damaged after issuance?",
                "a": "You can apply for a damaged passport replacement. Fee is the same as for new passport. Tatkal service is available."
            },
            {
                "q": "Can NRIs renew their passport online?",
                "a": "Yes. NRIs can renew their passport through Indian embassies/consulates in their country of residence or apply online through the Passport Seva portal."
            },
            {
                "q": "How long is a passport valid?",
                "a": "Adult passport is valid for 10 years. Minor passport (below 18) is valid for 5 years."
            },
        ],
        "common_issues": [
            "Police verification delayed due to address change or background checks",
            "Name spelling mismatch between documents",
            "Lost passport while traveling (requires embassy assistance)",
            "Passport damaged due to water, wear, or misuse",
            "Application rejected due to incorrect documents or missing signatures"
        ],
        "legal_protections": [
            "Section 4, Passport Act 1967: Citizens have right to obtain a passport.",
            "Section 10: Passport can be revoked only by government on specific grounds (fraud, crime, threat to national security).",
            "Section 12: Passport can be impounded during criminal proceedings.",
            "Applicants have right to appeal passport rejection to the Additional Secretary, MEA."
        ],
        "disclaimer": "SmartLegal-AI provides guidance only. Passport processing times, fees, and document requirements may change. Always check the official Passport Seva website (https://passportindia.gov.in) for current procedures. Processing times vary by PSK location and volume. Emergency services available for genuine urgent cases."
    },

    "voter_id": {
        "display_name": "Voter ID (EPIC)",
        "icon": "🗳️",
        "authority": "Election Commission of India (ECI) via State Election Commissions",
        "governing_law": "The Constitution of India (Article 325) and Representation of the People Act, 1950",
        "official_portal": "https://www.eci.gov.in (main portal, state-specific voter enrollment sites available)",
        "overview": "Voter ID (Electoral Photo ID Card - EPIC) is issued to Indian citizens aged 18+ to enable voting in elections. It serves as proof of citizenship and identity.",
        "services": [
            {
                "service": "New Voter Registration (Form 6)",
                "description": "Register as a voter if you are 18+ years old and an Indian citizen.",
                "where": "Local Election Commission office, Polling Station, or online through Electoral Roll portal (voter.eci.gov.in)",
                "documents_required": [
                    "Proof of age: Birth certificate, school certificate, or passport",
                    "Proof of address: Utility bill, bank statement, ration card, or property deed",
                    "Proof of citizenship: Aadhaar, PAN, or passport",
                    "Identification: Any government-issued ID with photo",
                    "Completed Form 6 (New Voter Application)"
                ],
                "fee": "Free",
                "timeline": "1-2 weeks after verification",
                "official_link": "https://eci.gov.in/",
            },
            {
                "service": "Voter ID Card Issuance",
                "description": "Get your EPIC (Electoral Photo ID Card) after successful voter registration.",
                "where": "Local polling station or Election Commission office",
                "documents_required": [
                    "Voter registration approval (you receive a registration confirmation)",
                    "Passport-sized photograph",
                    "Completed Form 10 (Application for voter card)"
                ],
                "fee": "Free",
                "timeline": "2-4 weeks after voter registration",
                "official_link": "https://eci.gov.in/",
            },
            {
                "service": "Address Update (Form 8)",
                "description": "Update your registered address in the voter roll due to relocation.",
                "where": "Local polling station or online through Electoral Roll",
                "documents_required": [
                    "Current voter ID card or registration number",
                    "New address proof: Utility bill, rental agreement, or property deed",
                    "Completed Form 8 (Address Update Application)",
                    "Identification proof"
                ],
                "fee": "Free",
                "timeline": "1-2 weeks",
                "official_link": "https://eci.gov.in/",
            },
            {
                "service": "Name Correction (Form 8/9)",
                "description": "Correct spelling or name errors in voter roll.",
                "where": "Local polling station or Election Commission office",
                "documents_required": [
                    "Voter ID card",
                    "Proof of correct name: Marriage certificate, court order, school certificate",
                    "Affidavit on stamp paper (if significant name change)",
                    "Completed Form 8 or 9"
                ],
                "fee": "Free",
                "timeline": "1-2 weeks",
                "official_link": "https://eci.gov.in/",
            },
            {
                "service": "Voter Status Check and Download",
                "description": "Check your voter registration status or download voter slip for voting.",
                "where": "Online through Electoral Roll (https://eci.gov.in)",
                "documents_required": [
                    "Name, Father's/Mother's name, and Assembly constituency",
                    "No documents needed, just search on electoral roll"
                ],
                "fee": "Free",
                "timeline": "Instant online",
                "official_link": "https://eci.gov.in/",
            },
        ],
        "faqs": [
            {
                "q": "Can I register as a voter if I am not an Indian citizen?",
                "a": "No. Only Indian citizens aged 18+ can register as voters. Citizenship is mandatory."
            },
            {
                "q": "What if my name is spelled differently in my documents?",
                "a": "The Election Commission will match your voter application with existing records (Aadhaar, PAN, passport). If there is a spelling mismatch, you may be asked to provide documents or file an affidavit. Minor spelling variations are usually overlooked."
            },
            {
                "q": "Can I vote from a different polling station than my registered one?",
                "a": "Typically, no. You must vote at your registered polling station unless you have officially changed your address in the voter roll."
            },
            {
                "q": "How often does the Electoral Roll get updated?",
                "a": "The Electoral Roll is updated on ongoing basis. Elections are conducted on the Electoral Roll that was latest published."
            },
            {
                "q": "Can NRIs register as voters?",
                "a": "Yes. NRIs are Indian citizens and can register as voters. However, they cannot vote overseas yet (as of 2024); they must vote in person at their registered polling station in India."
            },
        ],
        "common_issues": [
            "Voter registration rejected due to age verification failure",
            "Name in voter roll differs from government documents",
            "Address in voter roll is outdated or incorrect",
            "Duplicate voter registrations from different locations",
            "Unable to find yourself in electoral roll despite registration"
        ],
        "legal_protections": [
            "Article 325 of Constitution: Every Indian citizen aged 18+ has the right to vote regardless of caste, religion, gender, or economic status.",
            "Section 12, RPA 1950: Voter cannot be removed from roll except on specific grounds (death, non-citizenship, etc.).",
            "Election Commission must conduct fair voter verification process.",
            "Voters have the right to appeal wrongful deletion or non-registration to Election Commission."
        ],
        "disclaimer": "SmartLegal-AI provides guidance only. Voter registration procedures and timelines vary by state and are governed by state election commissions. Check your state's election commission website for exact procedures. Voter ID is optional for voting; you can vote with any government-issued ID."
    },

    "certificates": {
        "display_name": "Government Certificates",
        "icon": "📜",
        "authority": "State Government (Vital Statistics department, civil administration, or designated authorities)",
        "governing_law": "The Registration of Births and Deaths Act, 1969 (state variations); State-specific laws for caste, income, domicile certificates",
        "official_portal": "Varies by state. Most states use their own civil registration portals.",
        "overview": "Government certificates are official documents issued by state authorities as proof of vital events (birth, death) or personal status (caste, income, residence). These are essential for education, employment, marriage, and legal matters.",
        "services": [
            {
                "service": "Birth Certificate",
                "description": "Official record of birth issued by municipal/panchayat authority. Required for school admission, passport, marriage, employment.",
                "where": "Municipal Corporation office (urban) or Gram Panchayat (rural) or online through state portal",
                "documents_required": [
                    "Birth notification from hospital or local authority",
                    "Parent's ID proof",
                    "Parent's address proof",
                    "Declaration of birth (if not registered within 21 days, requires supporting documents)"
                ],
                "fee": "Free within 21 days of birth; ₹25-₹100 after 1 year (varies by state); ₹500-₹2,000 for late registration with court order",
                "timeline": "Same day to 1 week if done on time; 30-60 days if late",
                "official_link": "Check your state civil registration portal",
            },
            {
                "service": "Death Certificate",
                "description": "Official record of death issued after medical certification. Required for insurance claims, property transfer, pension closure.",
                "where": "Municipal Corporation office (urban) or Gram Panchayat (rural)",
                "documents_required": [
                    "Medical fitness certificate or doctor's certification of cause of death",
                    "Identity proof of deceased (Aadhaar, PAN, passport)",
                    "Informant's (family member's) ID and address proof"
                ],
                "fee": "Free within 21 days; ₹25-₹100 after (varies by state); ₹500+ for late registration",
                "timeline": "Same day to 1 week",
                "official_link": "Check your state civil registration portal",
            },
            {
                "service": "Caste Certificate",
                "description": "Proof of caste issued by state authorities. Required for reservations in education, employment, and government benefits.",
                "where": "Revenue Department or Tahsildar office",
                "documents_required": [
                    "Identity proof: Aadhaar, PAN, voter ID, or DL",
                    "Birth certificate or school certificate as age proof",
                    "Caste proof: Ration card, passport, or father's old caste certificate",
                    "Address proof",
                    "Affidavit on stamp paper with attested photograph"
                ],
                "fee": "₹50-₹500 (varies by state); Usually ₹100-₹300",
                "timeline": "7-30 days (normal verification process)",
                "official_link": "Check your state revenue department website",
            },
            {
                "service": "Income Certificate",
                "description": "Proof of annual income issued by Tahsildar or revenue official. Required for scholarships, fee concessions, reservations based on income.",
                "where": "Tahsildar office or Revenue Department (online in some states)",
                "documents_required": [
                    "Identity proof: Aadhaar, PAN, voter ID, DL",
                    "Address proof",
                    "Income proof: Salary slip, IT return, bank statement, or employer letter",
                    "Affidavit on stamp paper (if self-employed or agriculture-based income)",
                    "Self-attested photograph"
                ],
                "fee": "Free to ₹100 (varies by state)",
                "timeline": "3-7 days (if documents are in order)",
                "official_link": "Check your state revenue/tahsildar portal",
            },
            {
                "service": "Domicile / Residence Certificate",
                "description": "Proof of residence issued by revenue authority. Required for state-level quotas in education and employment.",
                "where": "Tahsildar office or Revenue Department",
                "documents_required": [
                    "Identity proof: Aadhaar, PAN, voter ID, DL, or passport",
                    "Address proof: Utility bill (electricity, water), bank statement, rent agreement, property deed (issued within 6 months)",
                    "Affidavit on stamp paper with photograph",
                    "For minors: Parent's documents + birth certificate"
                ],
                "fee": "Free to ₹100 (varies by state)",
                "timeline": "3-7 days",
                "official_link": "Check your state revenue/tahsildar portal",
            },
        ],
        "faqs": [
            {
                "q": "What if my birth certificate was not registered at birth?",
                "a": "You can apply for late registration. Registration within 1 year is simple; after 1 year, you need a court order. The process can take 30-60 days."
            },
            {
                "q": "Can I get a birth certificate after 18 years?",
                "a": "Yes, but you need to apply for 'Late Registration of Birth' with proof of age (school certificate, passport, Aadhaar). You may need an affidavit from a gazetted officer."
            },
            {
                "q": "Is caste certificate mandatory?",
                "a": "Only if you want to claim reserved category benefits in education/employment. General category applicants do not need caste certificate."
            },
            {
                "q": "How often does an income certificate need renewal?",
                "a": "Income certificates are typically valid for 1-2 years. You should apply for renewal if income has changed or certificate expired."
            },
            {
                "q": "Can I get a domicile certificate if I moved to the state recently?",
                "a": "Yes, but the state may require proof of residence for a minimum period (usually 1-7 years depending on state rules). Check your state's specific requirements."
            },
        ],
        "common_issues": [
            "Late registration of birth requires court involvement",
            "Caste or religion mismatch between documents",
            "Address proof rejected due to age (utility bills, statements older than 6 months not accepted)",
            "Death certificate delayed if cause of death is under investigation",
            "Income certificate rejected due to insufficient income proof",
            "Domicile certificate rejected if residence period does not meet state minimum"
        ],
        "legal_protections": [
            "Registration of Births and Deaths Act 1969: All births and deaths must be registered within 21 days (time limit varies slightly by state).",
            "Constitution Article 15: Caste-based discrimination is prohibited. Caste certificates for reservations are legal safeguards against past discrimination.",
            "Income and domicile certificates are statutory documents issued by authorized officers only.",
            "Falsifying any government certificate is a criminal offense (up to 5 years imprisonment and fine)."
        ],
        "disclaimer": "SmartLegal-AI provides general guidance. Certificate issuance procedures, fees, and timelines vary significantly by state. Always check your state's official civil registration or revenue department website for exact requirements. Processing times depend on document completeness and verification by local authorities. Some states allow online applications; contact your local office for latest options."
    }
}


def get_all_id_types() -> list[dict]:
    """Return summary of all 6 ID types for the frontend hub card grid."""
    return [
        {
            "key": "aadhaar",
            "display_name": LEGAL_ID_KB["aadhaar"]["display_name"],
            "icon": LEGAL_ID_KB["aadhaar"]["icon"],
            "authority": LEGAL_ID_KB["aadhaar"]["authority"],
            "official_portal": LEGAL_ID_KB["aadhaar"]["official_portal"],
        },
        {
            "key": "pan",
            "display_name": LEGAL_ID_KB["pan"]["display_name"],
            "icon": LEGAL_ID_KB["pan"]["icon"],
            "authority": LEGAL_ID_KB["pan"]["authority"],
            "official_portal": LEGAL_ID_KB["pan"]["official_portal"],
        },
        {
            "key": "driving_licence",
            "display_name": LEGAL_ID_KB["driving_licence"]["display_name"],
            "icon": LEGAL_ID_KB["driving_licence"]["icon"],
            "authority": LEGAL_ID_KB["driving_licence"]["authority"],
            "official_portal": LEGAL_ID_KB["driving_licence"]["official_portal"],
        },
        {
            "key": "passport",
            "display_name": LEGAL_ID_KB["passport"]["display_name"],
            "icon": LEGAL_ID_KB["passport"]["icon"],
            "authority": LEGAL_ID_KB["passport"]["authority"],
            "official_portal": LEGAL_ID_KB["passport"]["official_portal"],
        },
        {
            "key": "voter_id",
            "display_name": LEGAL_ID_KB["voter_id"]["display_name"],
            "icon": LEGAL_ID_KB["voter_id"]["icon"],
            "authority": LEGAL_ID_KB["voter_id"]["authority"],
            "official_portal": LEGAL_ID_KB["voter_id"]["official_portal"],
        },
        {
            "key": "certificates",
            "display_name": LEGAL_ID_KB["certificates"]["display_name"],
            "icon": LEGAL_ID_KB["certificates"]["icon"],
            "authority": LEGAL_ID_KB["certificates"]["authority"],
            "official_portal": LEGAL_ID_KB["certificates"]["official_portal"],
        },
    ]


def get_id_guidance(id_type: str) -> dict | None:
    """Return full guidance for one ID type."""
    normalized = _normalize_id_type(id_type)
    return LEGAL_ID_KB.get(normalized) if normalized else None


def get_id_checklist(id_type: str, service: str) -> list[str] | None:
    """Return document checklist for a specific service within an ID type."""
    normalized = _normalize_id_type(id_type)
    if not normalized or normalized not in LEGAL_ID_KB:
        return None

    for svc in LEGAL_ID_KB[normalized].get("services", []):
        if svc["service"].lower() == service.lower():
            return svc.get("documents_required", [])

    return None


def _normalize_id_type(raw: str) -> str | None:
    """Normalize user input to canonical ID type key."""
    if not raw:
        return None

    raw_lower = raw.lower().strip()

    # Exact match
    if raw_lower in LEGAL_ID_KB:
        return raw_lower

    # Alias map
    aliases = {
        "aadhaar card": "aadhaar",
        "aadhar": "aadhaar",
        "uid": "aadhaar",
        "pan card": "pan",
        "income tax": "pan",
        "dl": "driving_licence",
        "driver licence": "driving_licence",
        "driving license": "driving_licence",
        "passport book": "passport",
        "voter": "voter_id",
        "voter id": "voter_id",
        "epic": "voter_id",
        "electoral": "voter_id",
        "birth": "certificates",
        "death": "certificates",
        "caste": "certificates",
        "income": "certificates",
        "domicile": "certificates",
        "residence": "certificates",
        "certificate": "certificates",
        "certificates": "certificates",
    }

    return aliases.get(raw_lower)
