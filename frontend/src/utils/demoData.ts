import type { AnalysisResult, UploadedDocument } from '../types'

export const demoDocument: UploadedDocument = {
  id: 'demo',
  filename: 'Sample_Residential_Rental_Agreement.pdf',
  file_url: '/demo/Sample_Residential_Rental_Agreement.pdf',
  file_size: 428500, // ~418 KB
  document_type: 'Residential Rental Agreement',
  uploaded_at: new Date().toISOString(),
  status: 'ready',
}

export const demoAnalysisResult: AnalysisResult = {
  document_id: 'demo',
  analyzed_at: new Date().toISOString(),
  summary: {
    document_type: 'Residential Rental Agreement (Demo)',
    total_clauses: 6,
    high_risk_count: 2,
    medium_risk_count: 2,
    low_risk_count: 2,
    overall_risk: 'high',
    risk_summary:
      'High risk flags identified: Unilateral 15% annual rent escalation, 11-month lock-in period penalty with full security deposit forfeiture, and vague maintenance liability rules.',
    high_risk_clauses: [
      'Unilateral Rent Escalation: Rent increases automatically by 15% after 11 months without mutual consent.',
      'Security Deposit Forfeiture: Full ₹75,000 deposit forfeited if tenant vacates prior to 11 months.',
    ],
    beneficial_clauses: [
      'Landlord responsible for structural repairs, major plumbing, and building waterproofing.',
      'Tenant entitled to 24-hour advance written notice prior to any property inspection.',
    ],
    your_obligations: [
      'Pay monthly rent of ₹25,000 on or before the 5th of each calendar month.',
      'Maintain interior premises in good tenantable condition and pay utility bills directly.',
    ],
    other_party_rights: [
      'Landlord right to inspect premises with 24-hour advance written notice.',
      'Landlord right to deduct unpaid utility bills from security deposit at lease end.',
    ],
    parties: ['Mr. Rajesh Sharma (Lessor / Landlord)', 'Aarav Patel (Lessee / Tenant)'],
    key_dates: [
      { label: 'Commencement Date', date: '01-Apr-2026' },
      { label: 'Expiration Date', date: '28-Feb-2027' },
      { label: 'Rent Due Date', date: '5th of every month' },
    ],
  },
  clauses: [
    {
      id: 'demo-clause-1',
      title: 'Rent Amount & Unilateral Annual Escalation',
      clause_type: 'Financial / Rent',
      clause_number: 'Clause 3.1',
      page_number: 1,
      risk_level: 'high',
      risk_score: 8,
      risk_reason:
        'Automatic 15% annual rent increase is substantially above standard market benchmarks (5%–8%) and lacks mutual renegotiation rights.',
      plain_english:
        'You agree to pay ₹25,000 monthly rent. After 11 months, rent automatically increases by 15% without your consent or negotiation.',
      plain_hindi:
        'आप ₹25,000 का मासिक किराया देने पर सहमत हैं। 11 महीनों के बाद, आपकी सहमति या बातचीत के बिना किराया अपने आप 15% बढ़ जाएगा।',
      original_text:
        'The Lessee shall pay a monthly rent of Rs. 25,000/-. Upon completion of 11 months, the monthly rent shall automatically escalate by 15% per annum for any extension period without requiring fresh consent.',
    },
    {
      id: 'demo-clause-2',
      title: 'Security Deposit & Lock-In Forfeiture Penalty',
      clause_type: 'Security Deposit',
      clause_number: 'Clause 4.2',
      page_number: 2,
      risk_level: 'high',
      risk_score: 9,
      risk_reason:
        'Lock-in clause mandates total security deposit forfeiture if tenant vacates early, violating Model Tenancy guidelines.',
      plain_english:
        'Security deposit of ₹75,000 (3 months rent) will be forfeited entirely if you relocate or vacate before completing 11 months.',
      plain_hindi:
        'यदि आप 11 महीने पूरे करने से पहले घर खाली करते हैं तो ₹75,000 की सुरक्षा जमा राशि पूरी तरह से जब्त कर ली जाएगी।',
      original_text:
        'The Lessee has deposited Rs. 75,000/- as interest-free security deposit. In the event the Lessee vacates the premises prior to the completion of the 11-month lock-in period, the entire security deposit shall stand forfeited to the Lessor.',
    },
    {
      id: 'demo-clause-3',
      title: 'Maintenance & Day-to-Day Repair Responsibilities',
      clause_type: 'Maintenance',
      clause_number: 'Clause 6.1',
      page_number: 2,
      risk_level: 'medium',
      risk_score: 6,
      risk_reason:
        'Vague maintenance threshold shifts routine repair costs onto tenant up to ₹5,000 per incident.',
      plain_english:
        'Tenant is responsible for internal repairs up to ₹5,000 per incident. Landlord handles structural repairs.',
      plain_hindi:
        'किराएदार प्रति घटना ₹5,000 तक की आंतरिक मरम्मत के लिए जिम्मेदार है। मकान मालिक ढांचागत मरम्मत संभालता है।',
      original_text:
        'The Lessee shall bear costs for all minor day-to-day repairs up to Rs. 5,000 per occurrence. Major structural repairs shall be executed by the Lessor within reasonable time upon receiving notice.',
    },
    {
      id: 'demo-clause-4',
      title: 'Notice Period for Lease Termination',
      clause_type: 'Termination',
      clause_number: 'Clause 8.3',
      page_number: 3,
      risk_level: 'medium',
      risk_score: 5,
      risk_reason:
        '60-day notice requirement after lock-in period. Standard notice timeline for residential agreements.',
      plain_english:
        'After the lock-in period, either party can end the agreement by giving 60 days written notice or paying rent in lieu.',
      plain_hindi:
        'लॉक-इन अवधि के बाद, कोई भी पक्ष 60 दिनों का लिखित नोटिस देकर समझौते को समाप्त कर सकता है।',
      original_text:
        'Subsequent to the lock-in period, either party may terminate this lease by issuing a 60-day prior written notice or paying rent in lieu thereof to the other party.',
    },
    {
      id: 'demo-clause-5',
      title: 'Landlord Inspection Rights',
      clause_type: 'Inspection',
      clause_number: 'Clause 9.1',
      page_number: 3,
      risk_level: 'low',
      risk_score: 2,
      risk_reason:
        'Standard inspection right requiring 24-hour advance written notice to protect tenant privacy.',
      plain_english:
        'Landlord can inspect the property at reasonable daylight hours after giving 24 hours advance notice.',
      plain_hindi:
        'मकान मालिक 24 घंटे का नोटिस देने के बाद उचित दिन के समय संपत्ति का निरीक्षण कर सकता है।',
      original_text:
        'The Lessor or authorized representative may enter and inspect the premises during reasonable daylight hours after giving 24 hours advance notice to the Lessee.',
    },
    {
      id: 'demo-clause-6',
      title: 'Subletting & Alteration Prohibition',
      clause_type: 'Subletting',
      clause_number: 'Clause 10.2',
      page_number: 3,
      risk_level: 'low',
      risk_score: 3,
      risk_reason:
        'Standard protective restriction prohibiting tenant from subletting property to third parties without permission.',
      plain_english:
        'You cannot sublet the apartment or make structural alterations without written permission from the landlord.',
      plain_hindi:
        'आप बिना लिखित अनुमति के अपार्टमेंट को उप-किराए (sublet) पर नहीं दे सकते या संरचनात्मक बदलाव नहीं कर सकते।',
      original_text:
        'The Lessee shall not sublet, assign, or part with possession of the premises nor make any structural alterations without prior written consent of the Lessor.',
    },
  ],
}
