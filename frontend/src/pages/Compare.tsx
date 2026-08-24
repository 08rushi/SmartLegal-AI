import { useState } from 'react'
import { Card } from '../components/Card'

export interface ArticleResource {
  title: string
  url: string
  source: string
  type: 'Official Portal' | 'Government Gazette' | 'Verified Legal Resource'
}

export interface ArticleClauseBreakdown {
  clauseName: string
  purpose: string
  redFlags: string
  recommendedPhrasing: string
}

export interface DocumentArticle {
  id: string
  title: string
  category: 'Housing' | 'Employment' | 'Finance' | 'Business' | 'Legal'
  description: string
  icon: string
  accent: string
  highlights: string[]
  fullContent: {
    overview: string
    legalFramework: string
    keyClauses: ArticleClauseBreakdown[]
    executionChecklist: string[]
    commonTraps: string[]
    officialResources: ArticleResource[]
  }
}

const documentArticles: DocumentArticle[] = [
  {
    id: 'rental-agreement',
    title: 'Rental Agreement',
    category: 'Housing',
    description: 'A complete guide to security deposits, lock-in clauses, notice periods, rent escalation, and landlord/tenant rights under Model Tenancy laws.',
    icon: '🏠',
    accent: 'from-[#2a3152] to-[#121a2d]',
    highlights: ['Deposit Caps', 'Notice Terms', 'Maintenance Duties'],
    fullContent: {
      overview:
        'A Rental Agreement (or Lease Agreement) is a legally binding contract executed between a property owner (landlord) and a tenant. It grants temporary occupancy rights in exchange for regular rent payments. Under Indian jurisprudence, a well-drafted rental agreement ensures clear boundaries for security deposits, maintenance obligations, eviction procedures, and notice periods.',
      legalFramework:
        'Regulated under state-specific Rent Control Acts (e.g., Delhi Rent Control Act, Maharashtra Rent Control Act), the Model Tenancy Act 2021 passed by the Union Cabinet, and Section 105 of the Transfer of Property Act 1882.',
      keyClauses: [
        {
          clauseName: 'Security Deposit Cap & Refund Timeline',
          purpose: 'Protects tenant funds and sets clear expectations for deduction rules upon move-out.',
          redFlags: 'Landlord reserving unlimited deduction rights or withholding refunds past 60 days without itemized receipts.',
          recommendedPhrasing: 'Security deposit shall not exceed 2 months rent for residential premises. The full deposit, less verified actual damages beyond normal wear and tear, must be refunded within 30 days of surrender of keys.',
        },
        {
          clauseName: 'Lock-in Period & Early Termination',
          purpose: 'Ensures both parties maintain stability for an initial agreed timeframe (e.g., 6 months).',
          redFlags: 'Harsh penalty clauses demanding payment for the entire remaining lease term if tenant relocates due to work or emergencies.',
          recommendedPhrasing: 'Either party may terminate this agreement after the 6-month lock-in period by serving 1 month written notice or paying 1 month rent in lieu of notice.',
        },
        {
          clauseName: 'Rent Escalation Cap',
          purpose: 'Prevents sudden, excessive rent increases mid-tenancy or upon automatic renewal.',
          redFlags: 'Unilateral rent increases at the landlord discretion without cap or pre-agreed percentage.',
          recommendedPhrasing: 'Rent shall remain fixed for the 11-month term. Any renewal shall be subject to a maximum escalation of 5% to 8% per annum upon mutual written agreement.',
        },
        {
          clauseName: 'Maintenance & Repairs Allocation',
          purpose: 'Clearly defines structural repairs vs routine day-to-day household maintenance.',
          redFlags: 'Forcing the tenant to pay for major structural defects, seepage, or pre-existing plumbing issues.',
          recommendedPhrasing: 'Tenant responsible for minor routine maintenance (e.g., bulb replacement). Landlord responsible for structural repairs, major plumbing/electrical overhauls, and building maintenance within 7 days of notice.',
        },
      ],
      executionChecklist: [
        'Execute on Non-Judicial Stamp Paper of appropriate state denomination (e.g., ₹100–₹500 or % of annual rent depending on state rules).',
        'If the tenancy duration exceeds 11 months, mandatory registration under Section 17 of the Indian Registration Act 1908 at the Sub-Registrar Office.',
        'Obtain mandatory Tenant Police Verification via the local police state portal or mobile app.',
        'Attach ID & Address proofs (Aadhaar/PAN) of both landlord and tenant alongside 2 independent witness signatures.',
      ],
      commonTraps: [
        'Oral promises regarding parking slots or pet permission not recorded in the written text.',
        'Not taking date-stamped move-in photos/videos of existing wall cracks, appliances, or fixtures.',
        'Paying deposit via cash without a signed paper/digital receipt.',
      ],
      officialResources: [
        {
          title: 'Model Tenancy Act 2021 Policy & Provisions',
          url: 'https://mohua.gov.in',
          source: 'Ministry of Housing & Urban Affairs (MoHUA)',
          type: 'Official Portal',
        },
        {
          title: 'Transfer of Property Act 1882 (Section 105 - Lease Defined)',
          url: 'https://www.indiacode.nic.in/handle/123456789/2338',
          source: 'India Code (Law Ministry Portal)',
          type: 'Government Gazette',
        },
        {
          title: 'Department of Revenue - State Stamp Duty Rules',
          url: 'https://dor.gov.in',
          source: 'Department of Revenue, Ministry of Finance',
          type: 'Verified Legal Resource',
        },
      ],
    },
  },
  {
    id: 'employment-contract',
    title: 'Employment Contract',
    category: 'Employment',
    description: 'Review probation durations, termination rules, non-compete enforcement, IP assignment, salary breakdown, and severance policies.',
    icon: '💼',
    accent: 'from-[#241d41] to-[#121a2d]',
    highlights: ['Probation Rules', 'Non-Compete', 'Notice Pay'],
    fullContent: {
      overview:
        'An Employment Contract establishes the contractual relationship between an employer and an employee. It details compensation structure, job role, probation criteria, intellectual property ownership, confidentiality, and termination terms.',
      legalFramework:
        'Governed by the Indian Contract Act 1872, Shops and Establishment Acts of respective states, the Industrial Disputes Act 1947, and the Code on Wages 2019 / New Labour Codes.',
      keyClauses: [
        {
          clauseName: 'Non-Compete & Restraint of Trade (Section 27)',
          purpose: 'Protects business interests, but subject to strict legal boundaries in India.',
          redFlags: 'Post-employment non-compete restrictions preventing you from working in your domain for 1–2 years after leaving.',
          recommendedPhrasing: 'Under Section 27 of the Indian Contract Act 1872, post-employment non-compete clauses are void in India. Restraint applies exclusively during active employment.',
        },
        {
          clauseName: 'Notice Period & Pay in Lieu',
          purpose: 'Sets mandatory timeline for exit transitions for both employer and employee.',
          redFlags: 'Unilateral 90-day notice period required from employee while company reserves 0-day immediate termination right without pay.',
          recommendedPhrasing: 'Either party may terminate employment by serving 30 days written notice or by paying basic salary in lieu of notice.',
        },
        {
          clauseName: 'Intellectual Property (IP) Work-for-Hire',
          purpose: 'Transfers ownership of code, designs, or inventions created during work hours to the employer.',
          redFlags: 'Broad clauses claiming ownership over personal side-projects or pre-existing code created prior to employment.',
          recommendedPhrasing: 'Company owns IP created exclusively during working hours using company equipment for company business. Personal independent side-projects remain employee property.',
        },
        {
          clauseName: 'Salary Structure & Variable Pay Conditions',
          purpose: 'Breaks down Base Salary, HRA, Provident Fund (EPF), Gratuity, and performance bonuses.',
          redFlags: 'Vague performance bonus criteria allowing discretionary forfeiture after employee completes full target year.',
          recommendedPhrasing: 'Variable pay shall be evaluated against quantifiable KPIs defined in Schedule B and disbursed within 30 days of financial year close.',
        },
      ],
      executionChecklist: [
        'Cross-check Offer Letter terms against final Employment Agreement before signing.',
        'Verify EPF (Universal Account Number - UAN) and ESIC enrollment details.',
        'Ensure non-disclosure and confidentiality obligations have a defined, reasonable expiry duration.',
      ],
      commonTraps: [
        'Signing employment bonds or training cost recovery clauses exceeding actual documented training expense.',
        'Assuming verbal remote-work promises will remain valid without formal written inclusion.',
      ],
      officialResources: [
        {
          title: 'Ministry of Labour & Employment India Portal',
          url: 'https://labour.gov.in',
          source: 'Ministry of Labour & Employment, Govt of India',
          type: 'Official Portal',
        },
        {
          title: 'Employees Provident Fund Organisation (EPFO)',
          url: 'https://www.epfindia.gov.in',
          source: 'EPFO Official Portal',
          type: 'Official Portal',
        },
        {
          title: 'Indian Contract Act 1872 - Section 27 (Agreement in Restraint of Trade)',
          url: 'https://www.indiacode.nic.in/handle/123456789/2187',
          source: 'India Code Legislative Portal',
          type: 'Government Gazette',
        },
      ],
    },
  },
  {
    id: 'loan-agreement',
    title: 'Loan & Debt Agreement',
    category: 'Finance',
    description: 'Understand floating vs fixed interest rates, collateral pledges, EMI schedule penalties, foreclosure fees, and default recovery terms.',
    icon: '🏦',
    accent: 'from-[#352341] to-[#121a2d]',
    highlights: ['Penalty Interest', 'Collateral Pledge', 'Prepayment'],
    fullContent: {
      overview:
        'A Loan Agreement is a formal financial contract binding a borrower and lender. It defines the principal loan amount, interest rate calculations, repayment schedule (EMIs), collateral hypothecation, default triggers, and recovery mechanisms.',
      legalFramework:
        'Regulated by Reserve Bank of India (RBI) Master Directions, Fair Practices Code for Lenders, Negotiable Instruments Act 1881 (Section 138), and the Recovery of Debts Act.',
      keyClauses: [
        {
          clauseName: 'Interest Rate Reset & Benchmark Type',
          purpose: 'Determines how interest changes over time (Fixed vs Floating linked to RBI Repo Rate/MCLR).',
          redFlags: 'Opaque benchmark rates allowing lender to hike interest without notifying borrower.',
          recommendedPhrasing: 'Interest rate shall be benchmarked to RBI Repo Rate / EBLR. Any margin adjustments must be communicated 30 days in advance with option to switch or prepay.',
        },
        {
          clauseName: 'Foreclosure & Prepayment Penalty Waiver',
          purpose: 'Allows early loan payoff without financial penalties.',
          redFlags: 'Imposing 2%–4% prepayment penalty on individual borrowers with floating rate loans.',
          recommendedPhrasing: 'In accordance with RBI directives, no foreclosure or prepayment penalty shall be charged for individual borrowers on floating rate loans.',
        },
        {
          clauseName: 'Penal Interest Capping',
          purpose: 'Restricts punitive charges imposed when an EMI payment is delayed.',
          redFlags: 'Compounding penal interest on top of regular interest or charging exorbitant daily late fees.',
          recommendedPhrasing: 'Penal charges for delayed EMI shall be limited to 2% per month simple interest on the overdue EMI amount only, not on the total principal balance.',
        },
        {
          clauseName: 'Collateral Release Timeline',
          purpose: 'Mandates return of property title deeds or asset documents upon final repayment.',
          redFlags: 'Lender retaining original land documents or vehicle RC past 30 days after full settlement.',
          recommendedPhrasing: 'Lender shall release all original property title deeds and file NOC/No-Dues Certificate within 30 days of full loan repayment as per RBI Fair Lending practices.',
        },
      ],
      executionChecklist: [
        'Review Key Fact Statement (KFS) containing Annual Percentage Rate (APR) and total cost of loan.',
        'Verify NACH mandate / e-mandate details and check post-dated cheque (PDC) safety.',
        'Ensure stamp duty payment under state financial instrument laws.',
      ],
      commonTraps: [
        'Ignoring hidden processing fees or mandatory credit insurance bundled without consent.',
        'Not obtaining written No-Objection Certificate (NOC) after closing the loan account.',
      ],
      officialResources: [
        {
          title: 'Reserve Bank of India (RBI) Regulatory Framework',
          url: 'https://www.rbi.org.in',
          source: 'Reserve Bank of India',
          type: 'Official Portal',
        },
        {
          title: 'RBI Sachet Portal Against Illegal Lending Apps',
          url: 'https://sachet.rbi.org.in',
          source: 'RBI Financial Integrity Cell',
          type: 'Verified Legal Resource',
        },
        {
          title: 'Negotiable Instruments Act 1881 - Section 138 (Cheque Dishonour)',
          url: 'https://www.indiacode.nic.in/handle/123456789/2193',
          source: 'India Code Law Repository',
          type: 'Government Gazette',
        },
      ],
    },
  },
  {
    id: 'commercial-lease',
    title: 'Commercial Lease Agreement',
    category: 'Housing',
    description: 'Analyze fit-out free periods, Common Area Maintenance (CAM) charges, subletting restrictions, GST implications, and lease renewal options.',
    icon: '🏢',
    accent: 'from-[#1e2947] to-[#121a2d]',
    highlights: ['CAM Charges', 'Fit-out Period', 'Subleasing'],
    fullContent: {
      overview:
        'A Commercial Lease Agreement governs office spaces, retail stores, or industrial warehouses. It involves higher financial stakes, longer lease terms, complex maintenance charges (CAM), GST compliance, and specific business alteration permissions.',
      legalFramework:
        'Transfer of Property Act 1882, Indian Registration Act 1908, Income Tax Act 1961 (TDS Section 194-I), and Central Goods & Services Tax (CGST) Act 2017.',
      keyClauses: [
        {
          clauseName: 'Fit-out Rent-Free Period',
          purpose: 'Provides a rent-free window for tenant to construct interiors and setup office infrastructure.',
          redFlags: 'Demanding full rent during fit-out construction before municipal occupation certificate is granted.',
          recommendedPhrasing: 'Tenant shall be granted a 60-day fit-out rent-free period starting from Handover Date. Rent liability commences only on Commencement Date.',
        },
        {
          clauseName: 'CAM (Common Area Maintenance) Itemization',
          purpose: 'Defines exact operational costs shared among building tenants.',
          redFlags: 'Lender charging unverified lump-sum CAM amounts without audited annual expense statements.',
          recommendedPhrasing: 'CAM charges shall be billed based on actual audited utility and security costs proportional to leased area. Tenant has right to inspect annual CAM audit reports.',
        },
        {
          clauseName: 'Subleasing & Group Assignment Rights',
          purpose: 'Allows tenant to sublet space to subsidiaries, affiliates, or co-working partners.',
          redFlags: 'Total ban on subletting even to wholly-owned parent or subsidiary companies.',
          recommendedPhrasing: 'Tenant may sublet or assign premises to its group entities, subsidiaries, or affiliates with prior written notice to Lessor.',
        },
        {
          clauseName: 'Right of First Refusal (ROFR) for Renewal',
          purpose: 'Gives existing tenant priority to renew lease before space is offered to competitors.',
          redFlags: 'Lessor abruptly leasing space to third party at lease expiry without offering matching terms to current tenant.',
          recommendedPhrasing: 'Tenant holds Right of First Refusal to renew the lease for an additional 3-year term at market rates upon serving notice 90 days prior to expiry.',
        },
      ],
      executionChecklist: [
        'Mandatory registration at Sub-Registrar Office regardless of tenure for long-term commercial validity.',
        'Verify property title deed, commercial land usage approval, and Fire NOC from municipal corporation.',
        'Deduct 10% TDS on rent under Section 194-I if annual rent exceeds threshold.',
      ],
      commonTraps: [
        'Failing to verify building sanctioned plan and sanctioned electricity load (kVA).',
        'Not defining who pays municipal property tax increases during lease term.',
      ],
      officialResources: [
        {
          title: 'Income Tax Department India - Section 194-I Rent TDS Rules',
          url: 'https://incometaxindia.gov.in',
          source: 'Income Tax Department, Govt of India',
          type: 'Official Portal',
        },
        {
          title: 'CBIC GST Portal - Commercial Property Rent Taxation',
          url: 'https://www.cbic.gov.in',
          source: 'Central Board of Indirect Taxes and Customs',
          type: 'Official Portal',
        },
        {
          title: 'Transfer of Property Act 1882',
          url: 'https://www.indiacode.nic.in/handle/123456789/2338',
          source: 'India Code Legislative Portal',
          type: 'Government Gazette',
        },
      ],
    },
  },
  {
    id: 'nda',
    title: 'Non-Disclosure Agreement (NDA)',
    category: 'Legal',
    description: 'Learn the difference between unilateral and mutual secrecy, definition of proprietary data, carve-outs, and survival clauses.',
    icon: '🔒',
    accent: 'from-[#3a2046] to-[#121a2d]',
    highlights: ['Unilateral vs Mutual', 'Survival Period', 'Exceptions'],
    fullContent: {
      overview:
        'A Non-Disclosure Agreement (NDA) protects confidential business information, intellectual property, trade secrets, software algorithms, client lists, and financial records from unauthorized disclosure or misuse.',
      legalFramework:
        'Indian Contract Act 1872, Information Technology Act 2000 (Section 43A & 72A), and the Digital Personal Data Protection (DPDP) Act 2023.',
      keyClauses: [
        {
          clauseName: 'Definition & Scope of Confidential Information',
          purpose: 'Clearly specifies what materials and data are protected under secrecy.',
          redFlags: 'Overly vague definition claiming "all discussions ever held" are confidential without requiring written marking.',
          recommendedPhrasing: 'Confidential Information includes technical data, code, financials, and business plans disclosed in writing or marked "Confidential" at time of disclosure.',
        },
        {
          clauseName: 'Standard Exceptions & Carve-Outs',
          purpose: 'Exempts information that is already public or required by court order.',
          redFlags: 'Lacking standard exceptions, exposing receiving party to liability even if data was already public or ordered by court.',
          recommendedPhrasing: 'Obligations do not apply to data: (a) publicly known without breach, (b) already known prior to disclosure, (c) independently developed, or (d) required by court order.',
        },
        {
          clauseName: 'Term & Survival Period',
          purpose: 'Limits confidentiality obligations to a realistic duration.',
          redFlags: 'Perpetual non-disclosure requirements for standard commercial discussions.',
          recommendedPhrasing: 'Confidentiality obligations shall survive for a period of 2 years from the date of disclosure or termination of discussions.',
        },
        {
          clauseName: 'Return or Destruction of Data',
          purpose: 'Ensures receiving party deletes all copies of sensitive files when collaboration ends.',
          redFlags: 'Receiving party retaining active rights to use confidential data after business negotiations fail.',
          recommendedPhrasing: 'Upon written request, receiving party shall destroy or return all electronic and physical copies of confidential information within 14 days and certify in writing.',
        },
      ],
      executionChecklist: [
        'Verify correct legal corporate entity names and registered addresses.',
        'Ensure mutual NDA structure if both parties are exchanging sensitive information.',
        'Specify court jurisdiction (e.g. courts in Bengaluru, Delhi, or Mumbai).',
      ],
      commonTraps: [
        'Confusing non-disclosure with non-compete clauses embedded quietly in NDA text.',
        'Not obtaining NDA sign-offs from contractors or third-party advisors.',
      ],
      officialResources: [
        {
          title: 'Ministry of Electronics & IT - Data Protection Guidelines',
          url: 'https://www.meity.gov.in',
          source: 'Ministry of Electronics and Information Technology',
          type: 'Official Portal',
        },
        {
          title: 'Information Technology Act 2000 (Section 43A & 72A)',
          url: 'https://www.indiacode.nic.in/handle/123456789/1998',
          source: 'India Code Law Repository',
          type: 'Government Gazette',
        },
        {
          title: 'DPIIT Intellectual Property Rights Cell',
          url: 'https://dpiit.gov.in',
          source: 'DPIIT, Ministry of Commerce & Industry',
          type: 'Verified Legal Resource',
        },
      ],
    },
  },
  {
    id: 'service-contract',
    title: 'Service & Freelance Contract',
    category: 'Employment',
    description: 'Define Scope of Work (SOW), payment milestone triggers, revision limits, intellectual property transfer, and liability capping.',
    icon: '📋',
    accent: 'from-[#1a324b] to-[#121a2d]',
    highlights: ['SOW & Milestones', 'IP Ownership', 'Liability Limits'],
    fullContent: {
      overview:
        'A Service Contract or Freelance Agreement establishes the terms under which an independent contractor or vendor provides specialized services to a client. It governs Scope of Work (SOW), payment schedules, revision bounds, and IP rights.',
      legalFramework:
        'Indian Contract Act 1872, Copyright Act 1957, and Central Goods & Services Tax (CGST) Act 2017.',
      keyClauses: [
        {
          clauseName: 'Scope of Work (SOW) & Acceptance Criteria',
          purpose: 'Prevents scope creep by strictly defining deliverables and revision limits.',
          redFlags: 'Open-ended requirements like "work until client is satisfied" without capped revision rounds.',
          recommendedPhrasing: 'Service provider shall deliver milestones defined in Schedule A. Deliverables include up to 2 rounds of revisions. Additional changes billed at agreed hourly rate.',
        },
        {
          clauseName: 'IP Transfer Contingent on Full Payment',
          purpose: 'Ensures creator retains copyright until invoice is paid in full.',
          redFlags: 'Automatic IP transfer upon work creation before payment is received.',
          recommendedPhrasing: 'All intellectual property rights in deliverables transfer to Client exclusively upon receipt of 100% full payment.',
        },
        {
          clauseName: 'Payment Schedule & Late Fee Interest',
          purpose: 'Establishes clear payment milestone dates and late fees for overdue invoices.',
          redFlags: 'Client withholding payment indefinitely without providing formal written rejection of work.',
          recommendedPhrasing: 'Invoices due within 15 days of issue. Overdue payments accrue interest at 1.5% per month starting on 16th day.',
        },
        {
          clauseName: 'Limitation of Liability Cap',
          purpose: 'Protects contractor from catastrophic legal liability exceeding contract earnings.',
          redFlags: 'Unlimited liability clauses exposing freelancer to indirect or consequential loss claims.',
          recommendedPhrasing: 'Total aggregate liability of Service Provider under this agreement shall be capped at total fees paid by Client in preceding 3 months.',
        },
      ],
      executionChecklist: [
        'Attach itemized Schedule A specifying deliverables, milestones, and acceptance test criteria.',
        'Verify GST registration applicability (18% GST for services exceeding threshold).',
        'Signed written agreement or confirmed email contract before commencing work.',
      ],
      commonTraps: [
        'Starting work on verbal promises without an upfront advance deposit (e.g. 25%–50%).',
        'Failing to specify who owns raw source files vs finished export deliverables.',
      ],
      officialResources: [
        {
          title: 'Copyright Office India - Copyright Act Provisions',
          url: 'https://copyright.gov.in',
          source: 'Copyright Office, Govt of India',
          type: 'Official Portal',
        },
        {
          title: 'CBIC GST Portal - Services Taxation Rules',
          url: 'https://www.cbic.gov.in',
          source: 'Central Board of Indirect Taxes and Customs',
          type: 'Official Portal',
        },
        {
          title: 'Indian Contract Act 1872',
          url: 'https://www.indiacode.nic.in/handle/123456789/2187',
          source: 'India Code Legislative Portal',
          type: 'Government Gazette',
        },
      ],
    },
  },
  {
    id: 'partnership-deed',
    title: 'Partnership & Founder Deed',
    category: 'Business',
    description: 'Vesting schedules, equity allocation, profit sharing ratios, decision deadlock mechanisms, partner exit terms, and dissolution rules.',
    icon: '🤝',
    accent: 'from-[#2e264a] to-[#121a2d]',
    highlights: ['Equity Vesting', 'Deadlock Resolution', 'Exit Terms'],
    fullContent: {
      overview:
        'A Partnership Deed or Founder Agreement defines terms among business partners or co-founders. It establishes capital contribution, profit/loss sharing ratios, equity vesting schedules, decision-making powers, partner exit terms, and dispute resolution.',
      legalFramework:
        'Indian Partnership Act 1932, Limited Liability Partnership (LLP) Act 2008, and the Companies Act 2013.',
      keyClauses: [
        {
          clauseName: 'Founder Equity Reverse Vesting Schedule',
          purpose: 'Ensures co-founders earn equity over time rather than walking away on Day 1 with 50% shares.',
          redFlags: 'Immediate 100% upfront equity ownership without a 4-year vesting schedule or 1-year cliff.',
          recommendedPhrasing: 'Founder equity shall vest over 4 years with a 1-year cliff (25% vests at Month 12, remaining monthly over 36 months). Unvested shares repurchased at par upon early exit.',
        },
        {
          clauseName: 'Profit & Loss Allocation Ratio',
          purpose: 'Sets exact percentage of net profit or loss distributed to each partner.',
          redFlags: 'Ambiguous wording regarding operational reinvestment vs profit distribution.',
          recommendedPhrasing: 'Net profits/losses after taxes and partner salaries shall be shared strictly in ratio of capital contribution specified in Schedule A.',
        },
        {
          clauseName: 'Deadlock Resolution Mechanism',
          purpose: 'Prevents business paralysis when 50-50 co-founders disagree on major decisions.',
          redFlags: 'No deadlock provision, resulting in legal freeze of bank accounts during partner disputes.',
          recommendedPhrasing: 'In event of 50-50 voting deadlock, parties agree to 14-day mediation by named independent advisor, followed by binding arbitration if unresolved.',
        },
        {
          clauseName: 'Partner Exit Valuation Formula',
          purpose: 'Defines fair market buyout rules when a partner decides to leave or retire.',
          redFlags: 'Exiting partner demanding arbitrary inflated share valuation or threatening company shutdown.',
          recommendedPhrasing: 'Exiting partner shares valued at Fair Market Value determined by independent Registered Valuer using discounted cash flow / asset valuation.',
        },
      ],
      executionChecklist: [
        'Register Partnership Deed with Registrar of Firms (ROF) or file LLP agreement with Ministry of Corporate Affairs (MCA).',
        'Draft separate Founders Agreement alongside company Articles of Association (AoA).',
        'Define clear bank account operating mandate (single vs joint signatures for expenses above threshold).',
      ],
      commonTraps: [
        'Not addressing intellectual property transfer from personal founder accounts to company entity.',
        'Ignoring non-compete and non-solicitation restrictions during and after partner exit.',
      ],
      officialResources: [
        {
          title: 'Ministry of Corporate Affairs (MCA) Portal',
          url: 'https://www.mca.gov.in',
          source: 'Ministry of Corporate Affairs, Govt of India',
          type: 'Official Portal',
        },
        {
          title: 'Startup India Official Portal',
          url: 'https://www.startupindia.gov.in',
          source: 'DPIIT Startup Hub',
          type: 'Official Portal',
        },
        {
          title: 'Indian Partnership Act 1932',
          url: 'https://www.indiacode.nic.in/handle/123456789/2189',
          source: 'India Code Legislative Portal',
          type: 'Government Gazette',
        },
      ],
    },
  },
  {
    id: 'sale-deed',
    title: 'Property Sale & Conveyance Deed',
    category: 'Housing',
    description: 'Verify clear legal title, encumbrance certificates, indemnity clauses, stamp duty calculation, and vacant possession delivery.',
    icon: '📜',
    accent: 'from-[#3b2b1a] to-[#121a2d]',
    highlights: ['Title Verification', 'Encumbrance', 'Indemnity'],
    fullContent: {
      overview:
        'A Property Sale Deed (Conveyance Deed) is the primary legal instrument executed to transfer absolute ownership rights of immovable property (land, apartment, house) from seller (vendor) to buyer (vendee) upon payment of agreed sale consideration.',
      legalFramework:
        'Transfer of Property Act 1882 (Section 54), Registration Act 1908, Real Estate (Regulation and Development) Act 2016 (RERA), and State Stamp Acts.',
      keyClauses: [
        {
          clauseName: 'Clear & Marketable Title Warranty',
          purpose: 'Seller guarantees absolute legal ownership free from mortgages, liens, or court disputes.',
          redFlags: 'Seller providing no warranty against past legal disputes, property tax dues, or inheritance claims.',
          recommendedPhrasing: 'Vendor warrants clear, marketable, and unencumbered title to property, free from all claims, mortgages, liens, lis pendens, or municipal tax liabilities.',
        },
        {
          clauseName: 'Vendor Indemnity Clause',
          purpose: 'Protects buyer if third-party legal claims arise regarding past property ownership.',
          redFlags: 'Absence of indemnity clause leaving buyer financially liable for seller past debts.',
          recommendedPhrasing: 'Vendor agrees to indemnify and hold Vendee harmless against any loss, legal fees, or claims arising from defects in title or past encumbrances prior to execution date.',
        },
        {
          clauseName: 'Vacant Physical Possession Delivery',
          purpose: 'Ensures seller hands over keys and physical possession simultaneously with full payment.',
          redFlags: 'Full payment made while seller promises to hand over physical possession "in 30 days".',
          recommendedPhrasing: 'Vendor hands over peaceful, vacant physical possession of property alongside original keys to Vendee simultaneously upon receipt of full sale consideration.',
        },
        {
          clauseName: 'Stamp Duty & Registration Responsibility',
          purpose: 'Clarifies financial responsibility for government transfer charges.',
          redFlags: 'Ambiguity regarding who pays stamp duty, registration fees, and municipal transfer tax.',
          recommendedPhrasing: 'Stamp duty and registration fees shall be borne exclusively by Vendee. Vendor responsible for clearing all property tax, water, and electricity dues up to execution date.',
        },
      ],
      executionChecklist: [
        'Obtain Encumbrance Certificate (Form 15 & Form 16) for past 30 years from Sub-Registrar Office.',
        'Verify original Mother Deed, Title Search Report by Advocate, Khata Certificate, and RERA registration.',
        'Mandatory execution on Non-Judicial Stamp Paper and registration at Sub-Registrar Office with 2 witnesses.',
      ],
      commonTraps: [
        'Buying property without checking building plan sanction approval from municipal authority.',
        'Not publishing a Public Notice in 2 local newspapers prior to execution to invite title objections.',
      ],
      officialResources: [
        {
          title: 'RERA Real Estate Regulatory Portal',
          url: 'https://rera.mohua.gov.in',
          source: 'Ministry of Housing & Urban Affairs',
          type: 'Official Portal',
        },
        {
          title: 'Department of Land Resources (DoLR)',
          url: 'https://dolr.gov.in',
          source: 'Department of Land Resources, Govt of India',
          type: 'Official Portal',
        },
        {
          title: 'Transfer of Property Act 1882 - Section 54 (Sale Defined)',
          url: 'https://www.indiacode.nic.in/handle/123456789/2338',
          source: 'India Code Legislative Portal',
          type: 'Government Gazette',
        },
      ],
    },
  },
  {
    id: 'power-of-attorney',
    title: 'Power of Attorney (PoA)',
    category: 'Legal',
    description: 'Understand General PoA vs Special PoA, revocability conditions, NRI delegation rules, and court registration requirements.',
    icon: '⚖️',
    accent: 'from-[#1e3a34] to-[#121a2d]',
    highlights: ['General vs Special', 'Revocability', 'Registration'],
    fullContent: {
      overview:
        'A Power of Attorney (PoA) is a legal document authorizing an attorney-in-fact (agent) to act on behalf of the principal in business, legal, banking, or property matters. It can be general or limited to specific acts.',
      legalFramework:
        'Powers of Attorney Act 1882, Indian Stamp Act 1899, and the Indian Registration Act 1908.',
      keyClauses: [
        {
          clauseName: 'Specific Scope of Power (Special vs General)',
          purpose: 'Restricts agent authority strictly to necessary tasks.',
          redFlags: 'Granting blanket General PoA when agent only needs authority to register one specific vehicle or apartment.',
          recommendedPhrasing: 'This is a Special Power of Attorney strictly limited to representing Principal at Sub-Registrar Office for Flat No. 402 registration. Agent holds no authority to sell or mortgage property.',
        },
        {
          clauseName: 'Express Revocability Rights',
          purpose: 'Ensures principal can cancel PoA authority at any time.',
          redFlags: 'Irrevocable PoA clauses attached to simple service transactions.',
          recommendedPhrasing: 'Principal reserves absolute right to revoke this Power of Attorney at any time by serving written notice to Agent and issuing public revocation.',
        },
        {
          clauseName: 'NRI Consulate Attestation & Adjudication',
          purpose: 'Validates PoA executed outside India by NRIs.',
          redFlags: 'Executing PoA abroad without Indian Consulate attestation and local District Collector adjudication within 90 days.',
          recommendedPhrasing: 'PoA executed by non-resident Principal must be authenticated by Indian Embassy/Consulate and adjudicated by District Collector within 3 months of arrival in India.',
        },
        {
          clauseName: 'Prohibition of Self-Dealing or Gifting',
          purpose: 'Prevents agent from transferring principal property or funds to self or family.',
          redFlags: 'Lacking self-dealing restrictions, allowing dishonest agent to transfer principal asset to personal account.',
          recommendedPhrasing: 'Agent is strictly prohibited from transferring, gifting, or leasing Principal property or funds to Agent self, family members, or personal business entities.',
        },
      ],
      executionChecklist: [
        'Execute on stamp paper mandated by state stamp duty laws.',
        'Mandatory registration if PoA authorizes sale, transfer, or mortgage of immovable property.',
        'Affix passport photographs and thumb impressions of principal and agent.',
      ],
      commonTraps: [
        'Assuming PoA remains valid after death of principal (PoA automatically terminates upon death).',
        'Not sending formal written revocation notice to banks and sub-registrars when revoking PoA.',
      ],
      officialResources: [
        {
          title: 'Ministry of External Affairs - Consular Attestation Rules',
          url: 'https://www.mea.gov.in',
          source: 'Ministry of External Affairs, Govt of India',
          type: 'Official Portal',
        },
        {
          title: 'Powers of Attorney Act 1882',
          url: 'https://www.indiacode.nic.in/handle/123456789/2311',
          source: 'India Code Law Repository',
          type: 'Government Gazette',
        },
        {
          title: 'Department of Revenue - Stamp Duty & Adjudication Rules',
          url: 'https://dor.gov.in',
          source: 'Department of Revenue',
          type: 'Verified Legal Resource',
        },
      ],
    },
  },
  {
    id: 'mou',
    title: 'Memorandum of Understanding (MoU)',
    category: 'Business',
    description: 'Differentiate binding vs non-binding intent clauses, exclusivity timeframes, confidentiality, and transition to formal contracts.',
    icon: '✍️',
    accent: 'from-[#2c3325] to-[#121a2d]',
    highlights: ['Binding Clauses', 'Exclusivity', 'Transition'],
    fullContent: {
      overview:
        'A Memorandum of Understanding (MoU) expresses preliminary mutual intent and partnership framework between entities before entering formal binding commercial contracts.',
      legalFramework:
        'Indian Contract Act 1872 (distinguishing preliminary intent from binding contract obligations).',
      keyClauses: [
        {
          clauseName: 'Express Non-Binding Clause Declaration',
          purpose: 'Clarifies that MoU creates no enforceable financial liability except specific provisions.',
          redFlags: 'Ambiguous wording treating preliminary intent as a final binding commercial contract.',
          recommendedPhrasing: 'This MoU represents mutual intent only and is non-binding, with exception of Paragraphs 4 (Confidentiality), 5 (Exclusivity), and 7 (Governing Law).',
        },
        {
          clauseName: 'Exclusivity Window & Standstill',
          purpose: 'Prevents counterpart from negotiating with market competitors while due diligence occurs.',
          redFlags: 'Open-ended exclusivity binding you while counterpart explores third-party offers.',
          recommendedPhrasing: 'Parties agree to 60-day exclusive negotiation window. Neither party shall engage third parties for similar collaboration during this period.',
        },
        {
          clauseName: 'Definitive Agreement Target Timeline',
          purpose: 'Sets clear expiration date for signing final formal contracts.',
          redFlags: 'Indefinite MoU duration leading to business uncertainty.',
          recommendedPhrasing: 'This MoU expires automatically after 90 days unless superseded by a formal Definitive Agreement executed by both parties.',
        },
        {
          clauseName: 'Cost & Due Diligence Allocation',
          purpose: 'Ensures each party pays its own legal, audit, and advisory expenses during evaluation.',
          redFlags: 'One party attempting to invoice counterpart for preliminary due diligence costs.',
          recommendedPhrasing: 'Each party shall bear its own legal, financial, and administrative expenses incurred in connection with this MoU and due diligence.',
        },
      ],
      executionChecklist: [
        'Clearly separate non-binding intention sections from binding confidentiality and exclusivity terms.',
        'Define exact target execution date for final Definitive Agreement.',
        'Signatures by authorized corporate signatories alongside board resolution or authorization letter.',
      ],
      commonTraps: [
        'Including heavy penalty payment clauses in an MoU meant to be non-binding.',
        'Failing to convert MoU into a formal contract before starting commercial work.',
      ],
      officialResources: [
        {
          title: 'DPIIT Business Collaboration Guidelines',
          url: 'https://dpiit.gov.in',
          source: 'DPIIT, Ministry of Commerce & Industry',
          type: 'Official Portal',
        },
        {
          title: 'Indian Contract Act 1872',
          url: 'https://www.indiacode.nic.in/handle/123456789/2187',
          source: 'India Code Legislative Portal',
          type: 'Government Gazette',
        },
        {
          title: 'Ministry of Corporate Affairs Portal',
          url: 'https://www.mca.gov.in',
          source: 'Ministry of Corporate Affairs',
          type: 'Verified Legal Resource',
        },
      ],
    },
  },
  {
    id: 'affidavit',
    title: 'General Affidavit & Sworn Declaration',
    category: 'Legal',
    description: 'Rules for notarization, stamp paper denomination, perjury liabilities, and court admissibility under the Indian Evidence Act.',
    icon: '🛡️',
    accent: 'from-[#342426] to-[#121a2d]',
    highlights: ['Notarization', 'Stamp Duty', 'Legal Validity'],
    fullContent: {
      overview:
        'An Affidavit is a written statement of facts voluntarily made by an affiant under oath or affirmation administered by an authorized Notary Public, Magistrate, or Oath Commissioner.',
      legalFramework:
        'Oaths Act 1969, Indian Evidence Act 1872 (Section 3), Code of Civil Procedure 1908 (Order XIX), and Bharatiya Nyaya Sanhita (BNS) / IPC Sections 191 & 193 regarding perjury.',
      keyClauses: [
        {
          clauseName: 'Sworn Statement of Personal Knowledge',
          purpose: 'Affirms that facts stated are true based on personal knowledge or verified records.',
          redFlags: 'Stating hearsay or speculative opinions as sworn personal knowledge.',
          recommendedPhrasing: 'I, the Deponent above named, solemnly affirm that contents of Paragraphs 1 to 5 are true to my personal knowledge and belief, and nothing material has been concealed.',
        },
        {
          clauseName: 'Verification & Notarial Attestation',
          purpose: 'Official stamp and seal confirming identity of affiant.',
          redFlags: 'Signing affidavit outside presence of Notary Public or Oath Commissioner.',
          recommendedPhrasing: 'Verified at [City] on this [Date]. Deponent identified by Advocate, signed and sworn in my presence. [Notary Seal & Signature].',
        },
        {
          clauseName: 'Perjury Warning Notice',
          purpose: 'Reminds affiant of criminal prosecution liability for lying under oath.',
          redFlags: 'Submitting false statements leading to criminal charge under Section 193 BNS/IPC.',
          recommendedPhrasing: 'Deponent acknowledges that making false statements under oath is a punishable offense under Sections 191 & 193 of BNS / IPC with imprisonment up to 7 years.',
        },
      ],
      executionChecklist: [
        'Printed on Non-Judicial Stamp Paper of state-specified denomination (e.g. ₹20, ₹50, ₹100).',
        'Physical presence of affiant before Notary Public with photo identity proof (Aadhaar/PAN/Passport).',
        'Notary entry in official Register with Notarial Stamp and Seal.',
      ],
      commonTraps: [
        'Failing to cross-check spelling of names against passport or government records.',
        'Notary missing official registration number stamp on document pages.',
      ],
      officialResources: [
        {
          title: 'Ministry of Law and Justice Portal',
          url: 'https://lawmin.gov.in',
          source: 'Ministry of Law & Justice, Govt of India',
          type: 'Official Portal',
        },
        {
          title: 'Oaths Act 1969 Legislative Text',
          url: 'https://www.indiacode.nic.in/handle/123456789/2281',
          source: 'India Code Repository',
          type: 'Government Gazette',
        },
        {
          title: 'e-Courts Services Portal India',
          url: 'https://ecommitteesci.gov.in',
          source: 'Supreme Court e-Committee',
          type: 'Verified Legal Resource',
        },
      ],
    },
  },
  {
    id: 'vendor-agreement',
    title: 'Vendor & Supply Chain Agreement',
    category: 'Business',
    description: 'SLAs, delivery lead times, force majeure conditions, quality inspection, liquidated damages, and dispute arbitration venues.',
    icon: '🚚',
    accent: 'from-[#1c2c3e] to-[#121a2d]',
    highlights: ['SLA Standards', 'Force Majeure', 'Arbitration'],
    fullContent: {
      overview:
        'A Vendor & Supply Chain Agreement governs supply of goods, raw materials, or equipment. It establishes Service Level Agreements (SLAs), inspection turnaround, liquidated damages, MSME statutory 45-day payment rules, and arbitration venues.',
      legalFramework:
        'Sale of Goods Act 1930, Micro, Small and Medium Enterprises Development (MSMED) Act 2006 (Section 15), and Arbitration & Conciliation Act 1996.',
      keyClauses: [
        {
          clauseName: 'SLA Quality Inspection & Rejection Window',
          purpose: 'Defines procedure for inspecting delivered goods and rejecting defective stock.',
          redFlags: 'Vendor declaring delivery "final and non-returnable" upon unloading without inspection time.',
          recommendedPhrasing: 'Buyer has 7 business days from delivery to inspect goods against Schedule B quality standards. Defective items replaced by Vendor at Vendor expense within 5 days.',
        },
        {
          clauseName: 'MSME Statutory 45-Day Payment Rule (Section 15)',
          purpose: 'Mandates payment to registered MSME vendors within 45 days.',
          redFlags: 'Buyer delaying MSME vendor payment beyond 45 days, violating MSMED Act 2006.',
          recommendedPhrasing: 'In compliance with MSMED Act 2006, invoices of MSME registered Vendors shall be paid within 45 days of acceptance. Overdue payments attract RBI bank rate x 3 compound interest.',
        },
        {
          clauseName: 'Force Majeure Suspension',
          purpose: 'Excuses performance delay caused by events beyond reasonable control.',
          redFlags: 'Broad force majeure clauses including routine supply shortages or price inflation.',
          recommendedPhrasing: 'Neither party liable for delay caused by natural disaster, war, epidemic, or government embargo. Affected party must notify within 48 hours and mitigate impact.',
        },
        {
          clauseName: 'Liquidated Damages for Delay',
          purpose: 'Pre-estimates compensation for supply delivery delays.',
          redFlags: 'Exorbitant penalty charges exceeding actual loss incurred by buyer.',
          recommendedPhrasing: 'Delayed supply incurs liquidated damages at 0.5% per week of delayed order value, capped at a maximum of 5% of Total Purchase Order value.',
        },
      ],
      executionChecklist: [
        'Verify Udyam MSME Registration Certificate of Vendor if claiming MSME status.',
        'Attach detailed Purchase Order (PO) terms and technical specifications annexure.',
        'GSTIN verification and tax invoice compliance under CGST Rules.',
      ],
      commonTraps: [
        'Not specifying who pays transit insurance during freight shipping.',
        'Failing to define clear arbitration location and sole arbitrator appointment mechanism.',
      ],
      officialResources: [
        {
          title: 'MSME Samadhaan Delayed Payment Monitoring Portal',
          url: 'https://samadhaan.msme.gov.in',
          source: 'Ministry of MSME, Govt of India',
          type: 'Official Portal',
        },
        {
          title: 'Ministry of MSME Official Hub',
          url: 'https://msme.gov.in',
          source: 'Ministry of MSME',
          type: 'Official Portal',
        },
        {
          title: 'Sale of Goods Act 1930',
          url: 'https://www.indiacode.nic.in/handle/123456789/2388',
          source: 'India Code Repository',
          type: 'Government Gazette',
        },
      ],
    },
  },
]

const categories = ['All', 'Housing', 'Employment', 'Finance', 'Business', 'Legal'] as const

/**
 * Calculates real dynamic reading time based on total word count of article content.
 */
function getDynamicReadingTime(article: DocumentArticle): string {
  const textToCount = [
    article.description,
    article.fullContent.overview,
    article.fullContent.legalFramework,
    ...article.fullContent.keyClauses.flatMap((c) => [c.clauseName, c.purpose, c.redFlags, c.recommendedPhrasing]),
    ...article.fullContent.executionChecklist,
    ...article.fullContent.commonTraps,
  ].join(' ')

  const wordCount = textToCount.trim().split(/\s+/).filter(Boolean).length
  const minutes = Math.max(3, Math.ceil(wordCount / 180)) // ~180 words per minute average reading speed
  return `${minutes} min read`
}

export default function Compare() {
  const [selectedCategory, setSelectedCategory] = useState<string>('All')
  const [searchQuery, setSearchQuery] = useState<string>('')
  const [selectedArticle, setSelectedArticle] = useState<DocumentArticle | null>(null)
  const [activeTabModal, setActiveTabModal] = useState<'overview' | 'clauses' | 'checklist' | 'resources'>('overview')

  const filteredArticles = documentArticles.filter((article) => {
    const matchesCategory = selectedCategory === 'All' || article.category === selectedCategory
    const matchesSearch =
      article.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      article.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      article.highlights.some((h) => h.toLowerCase().includes(searchQuery.toLowerCase()))
    return matchesCategory && matchesSearch
  })

  return (
    <div className="content-wrap py-5 sm:py-6">
      <Card variant="section" className="mx-auto max-w-7xl rounded-[32px] p-6 sm:p-8">

        {/* Top Header */}
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <span className="section-eyebrow">Legal Knowledge Base</span>
            <h1 className="mt-3 text-3xl font-semibold text-white sm:text-4xl lg:text-5xl">
              Learn the legal terms that shape your rights.
            </h1>
            <p className="mt-3 max-w-3xl text-sm leading-7 text-slate-400 sm:text-base">
              Comprehensive breakdowns, risk checkpoints, real official government links, and plain-language summaries for all major Indian agreement types.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <span className="rounded-full border border-[#f5c26b]/25 bg-[#f5c26b]/10 px-4 py-2 text-xs font-medium text-[#f5c26b]">
              {documentArticles.length} Document Types Available
            </span>
          </div>
        </div>

        {/* Filter & Search Toolbar */}
        <div className="mt-8 flex flex-col gap-4 border-t border-white/10 pt-6 sm:flex-row sm:items-center sm:justify-between">
          {/* Category Tabs */}
          <div className="flex flex-wrap items-center gap-2">
            {categories.map((cat) => (
              <button
                key={cat}
                type="button"
                onClick={() => setSelectedCategory(cat)}
                className={`rounded-full px-4 py-2 text-xs font-medium transition-all duration-200 ${
                  selectedCategory === cat
                    ? 'bg-[#f5c26b] text-slate-950 font-semibold shadow-[0_0_18px_rgba(245,194,107,0.3)]'
                    : 'border border-white/10 bg-white/[0.03] text-slate-300 hover:border-white/20 hover:text-white'
                }`}
              >
                {cat === 'All' ? 'All Document Types' : cat}
              </button>
            ))}
          </div>

          {/* Search Bar */}
          <div className="relative min-w-[240px]">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search document types or terms..."
              className="input-field py-2.5 pl-9 text-xs"
            />
            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500 text-xs">🔍</span>
            {searchQuery && (
              <button
                type="button"
                onClick={() => setSearchQuery('')}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-slate-400 hover:text-white"
              >
                ✕
              </button>
            )}
          </div>
        </div>

        {/* Article Cards Grid — Sized Exact Similar to Home Page Cards */}
        <div className="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {filteredArticles.map((article) => {
            const dynamicReadingTime = getDynamicReadingTime(article)
            return (
              <Card
                key={article.id}
                as="article"
                variant="section"
                hoverLift
                onClick={() => {
                  setSelectedArticle(article)
                  setActiveTabModal('overview')
                }}
                className="group relative flex h-full flex-col justify-between overflow-hidden rounded-[28px] p-5"
              >
                {/* Top Gradient Accent Line */}
                <div className={`absolute inset-x-0 top-0 h-1 bg-gradient-to-r ${article.accent}`} />

                <div>
                  {/* Header with Icon Box & Badge */}
                  <div className="mb-5 flex items-center justify-between">
                    <div className="flex h-14 w-14 items-center justify-center rounded-2xl border border-white/10 bg-white/[0.04] text-2xl shadow-inner">
                      {article.icon}
                    </div>
                    <span className="rounded-full border border-white/10 bg-white/[0.04] px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-400">
                      {article.category}
                    </span>
                  </div>

                  {/* Title & Description */}
                  <h3 className="text-xl font-semibold text-white transition-colors group-hover:text-[#f5c26b]">
                    {article.title}
                  </h3>
                  <p className="mt-3 text-sm leading-7 text-slate-400">
                    {article.description}
                  </p>

                  {/* Key Highlights */}
                  <div className="mt-4 flex flex-wrap gap-1.5">
                    {article.highlights.map((h) => (
                      <span key={h} className="rounded-md border border-white/8 bg-white/[0.02] px-2 py-0.5 text-[11px] text-slate-400">
                        • {h}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Card Footer — Exact similar style to Home Page cards with DYNAMIC reading time */}
                <div className="mt-8 flex items-center justify-between border-t border-white/8 pt-4 text-xs">
                  <span className="text-slate-500 font-medium">{dynamicReadingTime}</span>
                  <span className="flex items-center gap-1 font-medium text-[#f5c26b] transition-transform group-hover:translate-x-1">
                    Read article →
                  </span>
                </div>
              </Card>
            )
          })}
        </div>

        {filteredArticles.length === 0 && (
          <div className="mt-12 rounded-2xl border border-white/10 bg-white/[0.02] p-10 text-center">
            <p className="text-lg text-slate-400">No document types match "{searchQuery}" in category "{selectedCategory}".</p>
            <button
              type="button"
              onClick={() => {
                setSelectedCategory('All')
                setSearchQuery('')
              }}
              className="btn-secondary mt-4 px-4 py-2 text-xs"
            >
              Reset Filters
            </button>
          </div>
        )}
      </Card>

      {/* Full Described Article Viewer Modal */}
      {selectedArticle && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-slate-950/80 backdrop-blur-md">
          <Card variant="section" className="w-full max-w-4xl max-h-[92vh] overflow-y-auto rounded-[32px] p-6 sm:p-8 relative flex flex-col justify-between">
            
            {/* Modal Header */}
            <div>
              <button
                type="button"
                onClick={() => setSelectedArticle(null)}
                className="absolute top-6 right-6 flex h-9 w-9 items-center justify-center rounded-full border border-white/10 bg-white/5 text-slate-400 transition hover:bg-white/10 hover:text-white"
              >
                ✕
              </button>

              <div className="flex items-start gap-4">
                <div className="flex h-16 w-16 shrink-0 items-center justify-center rounded-2xl border border-white/10 bg-white/[0.04] text-3xl">
                  {selectedArticle.icon}
                </div>
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-xs uppercase tracking-[0.2em] font-semibold text-[#f5c26b]">{selectedArticle.category}</span>
                    <span className="text-xs text-slate-500">• {getDynamicReadingTime(selectedArticle)}</span>
                  </div>
                  <h2 className="text-2xl font-bold text-white sm:text-3xl mt-1">{selectedArticle.title}</h2>
                  <p className="text-sm text-slate-400 mt-1">{selectedArticle.description}</p>
                </div>
              </div>

              {/* Navigation Sub-Tabs inside Full Article */}
              <div className="mt-6 flex flex-wrap gap-2 border-b border-white/10 pb-4">
                <button
                  type="button"
                  onClick={() => setActiveTabModal('overview')}
                  className={`rounded-xl px-4 py-2 text-xs font-semibold transition ${
                    activeTabModal === 'overview'
                      ? 'bg-white/10 text-[#f5c26b] shadow-[0_0_0_1px_rgba(245,194,107,0.2)]'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  📖 Overview & Legal Acts
                </button>
                <button
                  type="button"
                  onClick={() => setActiveTabModal('clauses')}
                  className={`rounded-xl px-4 py-2 text-xs font-semibold transition ${
                    activeTabModal === 'clauses'
                      ? 'bg-white/10 text-[#f5c26b] shadow-[0_0_0_1px_rgba(245,194,107,0.2)]'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  ⚖️ Essential Clause Breakdown ({selectedArticle.fullContent.keyClauses.length})
                </button>
                <button
                  type="button"
                  onClick={() => setActiveTabModal('checklist')}
                  className={`rounded-xl px-4 py-2 text-xs font-semibold transition ${
                    activeTabModal === 'checklist'
                      ? 'bg-white/10 text-[#f5c26b] shadow-[0_0_0_1px_rgba(245,194,107,0.2)]'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  📋 Execution Checklist
                </button>
                <button
                  type="button"
                  onClick={() => setActiveTabModal('resources')}
                  className={`rounded-xl px-4 py-2 text-xs font-semibold transition ${
                    activeTabModal === 'resources'
                      ? 'bg-white/10 text-[#f5c26b] shadow-[0_0_0_1px_rgba(245,194,107,0.2)]'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  🌐 Official Portals & Acts ({selectedArticle.fullContent.officialResources.length})
                </button>
              </div>

              {/* Tab 1: Overview & Legal Framework */}
              {activeTabModal === 'overview' && (
                <div className="mt-6 space-y-6">
                  <div className="info-card rounded-2xl p-5">
                    <h3 className="text-sm font-semibold uppercase tracking-[0.18em] text-[#f5c26b] mb-2">Plain Language Overview</h3>
                    <p className="text-sm leading-7 text-slate-200">{selectedArticle.fullContent.overview}</p>
                  </div>

                  <div className="info-card rounded-2xl p-5">
                    <h3 className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-400 mb-2">Governing Legal Framework & Statutes</h3>
                    <p className="text-sm leading-7 text-slate-300">{selectedArticle.fullContent.legalFramework}</p>
                  </div>

                  <div className="rounded-2xl border border-[#fb7185]/20 bg-[#2a1320]/40 p-5">
                    <h3 className="text-sm font-semibold uppercase tracking-[0.18em] text-[#fecdd3] mb-3">Common Traps & Red Flags to Avoid</h3>
                    <ul className="space-y-2 text-xs sm:text-sm leading-6 text-slate-300">
                      {selectedArticle.fullContent.commonTraps.map((trap, i) => (
                        <li key={i} className="flex items-start gap-2">
                          <span className="text-[#fb7185] shrink-0">⚠️</span>
                          <span>{trap}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}

              {/* Tab 2: Key Clauses */}
              {activeTabModal === 'clauses' && (
                <div className="mt-6 space-y-4">
                  {selectedArticle.fullContent.keyClauses.map((clause, idx) => (
                    <div key={idx} className="info-card rounded-2xl p-5 border border-white/10">
                      <div className="flex items-center justify-between gap-3 mb-3">
                        <h4 className="text-base font-semibold text-white">
                          <span className="text-[#f5c26b] font-mono mr-2">0{idx + 1}.</span>
                          {clause.clauseName}
                        </h4>
                        <span className="rounded-full border border-white/10 bg-white/5 px-2.5 py-0.5 text-[10px] uppercase text-slate-400">
                          Critical Clause
                        </span>
                      </div>

                      <div className="space-y-3 text-xs sm:text-sm">
                        <div className="rounded-xl bg-white/[0.02] p-3 border border-white/5">
                          <span className="font-semibold text-slate-400 block mb-1">Purpose:</span>
                          <span className="text-slate-300 leading-6">{clause.purpose}</span>
                        </div>

                        <div className="rounded-xl bg-[#fb7185]/10 p-3 border border-[#fb7185]/20">
                          <span className="font-semibold text-[#fb7185] block mb-1">🚩 Red Flag / Risk:</span>
                          <span className="text-[#fecdd3] leading-6">{clause.redFlags}</span>
                        </div>

                        <div className="rounded-xl bg-[#34d399]/10 p-3 border border-[#34d399]/20">
                          <span className="font-semibold text-[#34d399] block mb-1">✓ Recommended Safe Phrasing:</span>
                          <span className="text-[#bbf7d0] leading-6 font-mono text-xs block mt-1">{clause.recommendedPhrasing}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Tab 3: Execution Checklist */}
              {activeTabModal === 'checklist' && (
                <div className="mt-6 space-y-4">
                  <div className="info-card rounded-2xl p-5">
                    <h3 className="text-sm font-semibold uppercase tracking-[0.18em] text-[#f5c26b] mb-4">Step-by-Step Execution Checklist</h3>
                    <div className="space-y-3">
                      {selectedArticle.fullContent.executionChecklist.map((step, idx) => (
                        <div key={idx} className="flex items-start gap-3.5 rounded-xl border border-white/8 bg-white/[0.02] p-3.5">
                          <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-[#f5c26b]/15 text-xs font-bold text-[#f5c26b]">
                            {idx + 1}
                          </span>
                          <p className="text-xs sm:text-sm leading-6 text-slate-200 mt-0.5">{step}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* Tab 4: Real Official Resources & Online Portals */}
              {activeTabModal === 'resources' && (
                <div className="mt-6 space-y-4">
                  <div className="info-card rounded-2xl p-5">
                    <h3 className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-400 mb-4">Verified Official Indian Government Portals & Acts</h3>
                    <div className="grid gap-3 sm:grid-cols-1">
                      {selectedArticle.fullContent.officialResources.map((res, idx) => (
                        <a
                          key={idx}
                          href={res.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="group flex flex-col sm:flex-row sm:items-center justify-between gap-3 rounded-2xl border border-white/10 bg-white/[0.03] p-4 transition-all hover:bg-white/[0.08] hover:border-[#f5c26b]/30"
                        >
                          <div>
                            <div className="flex items-center gap-2">
                              <span className="rounded-full border border-blue-500/30 bg-blue-500/10 px-2.5 py-0.5 text-[10px] font-semibold text-blue-400">
                                {res.type}
                              </span>
                              <span className="text-xs text-slate-400">{res.source}</span>
                            </div>
                            <h4 className="text-sm font-semibold text-white group-hover:text-[#f5c26b] transition-colors mt-2">
                              {res.title}
                            </h4>
                          </div>
                          <span className="inline-flex items-center gap-1 text-xs font-semibold text-[#f5c26b] shrink-0">
                            Visit Official Site <span className="transition-transform group-hover:translate-x-1">↗</span>
                          </span>
                        </a>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="mt-8 pt-4 border-t border-white/10 flex items-center justify-between">
              <span className="text-xs text-slate-500">
                Educational awareness guide — SmartLegal AI Knowledge Base
              </span>
              <button
                type="button"
                onClick={() => setSelectedArticle(null)}
                className="btn-secondary px-6 py-2.5 text-xs font-semibold"
              >
                Close Article
              </button>
            </div>
          </Card>
        </div>
      )}
    </div>
  )
}
