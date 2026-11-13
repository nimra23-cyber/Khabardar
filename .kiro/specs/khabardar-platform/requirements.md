# Requirements Document

## Introduction

KHABARDAR ("Think Before You Trust") is an AI-powered Personal Scam & Fraud Protection Platform built for Pakistani users with multilingual support across English, Urdu, and Roman Urdu. It is a serious cybersecurity application that helps users detect phishing, fraud, scam messages, malicious URLs, and fraudulent QR codes, while providing a Security Operations Center (SOC) inspired threat intelligence experience.

The platform is implemented as a modular monorepo:
- **Frontend**: React, TypeScript, Vite, Tailwind CSS, Recharts (charts), Cytoscape.js (IOC relationship graph)
- **Backend**: Python, FastAPI, Pydantic, SQLAlchemy
- **Database**: SQLite for development, PostgreSQL-compatible schema for production

The platform is composed of six functional modules (A–F): AI Scam Detector, Advanced URL & Phishing Analyzer, Image/Screenshot/QR Scanner, Scam Intelligence & Safe Honeypot, SOC Threat Intelligence Dashboard, and Family Protection. It enforces strict security, privacy, honesty, and safety standards throughout.

The requirements below are organized to support seven staged implementation increments:
1. Project setup, branding, splash, dashboard, navigation
2. Backend, database, detection engine, rule-based logic, AI provider abstraction
3. URL analyzer, external integrations, URL security hardening
4. OCR and QR scanning
5. SOC dashboard, IOC extraction, campaign correlation, MITRE mapping
6. Honeypot simulation, family protection, notifications
7. Security testing, performance evaluation, documentation, deployment

## Glossary

- **Khabardar_Platform**: The complete AI-powered scam and fraud protection application comprising frontend, backend, and database.
- **Splash_Screen**: The dedicated full-screen branded entry screen shown once at application launch before the main dashboard.
- **Main_Dashboard**: The first interactive screen presented to the user after the splash screen auto-transitions.
- **Scam_Detector**: Module A. The AI component that analyzes submitted text messages for scam and fraud indicators.
- **URL_Analyzer**: Module B. The component that analyzes submitted URLs and domains for phishing and malicious indicators.
- **Media_Scanner**: Module C. The component that processes uploaded images/screenshots and QR codes, extracting text and links.
- **Intelligence_Engine**: Module D. The component that extracts, normalizes, deduplicates, and correlates Indicators of Compromise (IOCs).
- **Honeypot_Lab**: Module D sub-component. A fully simulated, controlled environment with synthetic scam conversations and an AI persona.
- **SOC_Dashboard**: Module E. The Security Operations Center inspired threat intelligence dashboard.
- **Family_Protection**: Module F. The component enabling trusted family members to share and receive scam alerts.
- **AI_Provider_Abstraction**: The modular backend layer that routes AI requests to configurable providers (Gemini, Groq, optional Ollama) with an offline rule-based fallback.
- **Rule_Based_Engine**: The deterministic detection component that analyzes text using heuristics, keyword patterns, and linguistic signals without external AI calls.
- **Threat_Intel_Enrichment**: The process of augmenting detection results with data from internal and external threat intelligence sources.
- **IOC**: Indicator of Compromise. A normalized artifact such as a phone number, email, domain, URL, wallet ID, bank account ID, or payment reference.
- **Risk_Score**: An integer from 0 to 100 representing the assessed threat level of a submission.
- **Classification**: One of the labels SAFE, SUSPICIOUS, or HIGH RISK assigned to a submission.
- **MITRE_Mapping**: A reference to a MITRE ATT&CK technique (e.g., T1566 Phishing) assigned to a detected behavior.
- **SSRF**: Server-Side Request Forgery, an attack where a server is induced to make unintended requests.
- **RBAC**: Role-Based Access Control.
- **Audit_Log**: A persistent record of security-relevant actions.
- **Official_Logo**: The official Khabardar shield logo asset as supplied, to be used without redesign, recoloring, or distortion.
- **Design_System**: The premium SOC-inspired visual system defining the color palette, themes, typography, and component styles.
- **Synthetic_Data**: Artificially generated non-real data used only in clearly labeled demo or simulation environments.

## Requirements

### Requirement 1: Branded Splash Screen

**User Story:** As a user, I want a clean branded splash screen when I launch Khabardar, so that I recognize the product and trust its identity before using it.

#### Acceptance Criteria

1. WHEN the Khabardar_Platform launches, THE Splash_Screen SHALL display only the Official_Logo, the name "KHABARDAR", and the tagline "Think Before You Trust", with no other textual or graphical content.
2. THE Splash_Screen SHALL render the Official_Logo exactly as supplied without redesigning, recoloring, or distorting the asset, preserving its original aspect ratio.
3. THE Splash_Screen SHALL display a full-screen Deep Navy background with the Official_Logo horizontally and vertically centered.
4. WHEN the Splash_Screen appears, THE Splash_Screen SHALL play an entrance animation for the logo and text that completes within 300 to 800 milliseconds.
5. WHEN the Splash_Screen has been displayed for 2 seconds, THE Khabardar_Platform SHALL automatically transition to the Main_Dashboard.
6. THE Splash_Screen SHALL exclude navigation elements, buttons, input forms, and footer content.
7. WHILE the viewport width is between 320 pixels and 3840 pixels, THE Splash_Screen SHALL keep the Official_Logo centered and fully visible within the viewport without clipping or overflow.
8. IF the Official_Logo asset fails to load, THEN THE Splash_Screen SHALL display the name "KHABARDAR" and the tagline "Think Before You Trust" centered on the Deep Navy background and SHALL still transition to the Main_Dashboard after 2 seconds.

### Requirement 2: Premium SOC-Inspired Design System

**User Story:** As a user, I want a premium security-operations-center visual experience, so that the platform feels professional, trustworthy, and readable.

#### Acceptance Criteria

1. THE Design_System SHALL define the color palette as Deep Navy #101D31, Midnight Blue #172A45, Metallic Silver #C5D0DC, Electric Blue #3987FF, light surface #F4F7FB, dark surface #0B1423, Danger #E5484D, Warning #E5A323, and Safe #1C9B70.
2. THE Design_System SHALL provide both a light theme and a dark theme.
3. WHEN a user has not previously selected a theme, THE Khabardar_Platform SHALL apply the dark theme as the default on initial load.
4. WHEN a user selects a theme, THE Khabardar_Platform SHALL apply the selected theme across all pages within 1 second and SHALL persist the selection across subsequent sessions.
5. THE Design_System SHALL use color and text combinations that achieve a contrast ratio of at least 4.5:1 for normal text and at least 3:1 for large text (18pt regular or 14pt bold) and user interface components, in accordance with WCAG 2.1 AA.
6. WHILE the viewport width is at most 767px, THE Khabardar_Platform SHALL present the mobile layout with no horizontal scrolling and no content overflow.
7. WHILE the viewport width is between 768px and 1023px inclusive, THE Khabardar_Platform SHALL present the tablet layout with no horizontal scrolling and no content overflow.
8. WHILE the viewport width is at least 1024px, THE Khabardar_Platform SHALL present the desktop layout with no horizontal scrolling and no content overflow.
9. THE Design_System SHALL represent risk states using Danger #E5484D for HIGH RISK, Warning #E5A323 for SUSPICIOUS, and Safe #1C9B70 for SAFE.

Note: Full WCAG 2.1 AA conformance (criterion 5) requires manual testing with assistive technologies and expert accessibility review beyond automated contrast checks.

### Requirement 3: Application Shell and Navigation

**User Story:** As a user, I want clear navigation between all platform areas, so that I can reach every feature efficiently.

#### Acceptance Criteria

1. THE Khabardar_Platform SHALL provide the pages Splash, Main Dashboard, Scam Detector, URL Analyzer, Screenshot & QR Scanner, Threat Intelligence, Honeypot Simulation Lab, Family Protection, Scan History, Reports, Settings, and About.
2. WHEN the Splash_Screen has been displayed for its 2-second duration, THE Khabardar_Platform SHALL complete the transition to the Main_Dashboard and display it as the first interactive screen within 1 to 3 seconds of launch.
3. WHEN a user selects a navigation destination, THE Khabardar_Platform SHALL navigate to the corresponding page within 1 second.
4. IF a navigation destination fails to load within 5 seconds, THEN THE Khabardar_Platform SHALL remain on the current page and display an error indication that the destination could not be loaded.
5. WHILE a page is active, THE Khabardar_Platform SHALL display the corresponding navigation destination in a visually distinct active state different from inactive destinations.
6. THE Main_Dashboard SHALL present a distinct selectable entry point for each of the Scam_Detector, URL_Analyzer, Media_Scanner, and SOC_Dashboard, where selecting an entry point navigates to that destination.

### Requirement 4: Multilingual Support

**User Story:** As a Pakistani user, I want to interact with the platform in English, Urdu, or Roman Urdu, so that I can understand scam analysis in my preferred language.

#### Acceptance Criteria

1. THE Khabardar_Platform SHALL support English, Urdu, and Roman Urdu for user-facing interface text.
2. WHEN a user selects an interface language, THE Khabardar_Platform SHALL display interface text in the selected language within 1 second and SHALL persist the selected language across subsequent sessions.
3. WHEN a user has not previously selected an interface language, THE Khabardar_Platform SHALL apply English as the default interface language.
4. IF a user-facing text string has no translation available in the selected language, THEN THE Khabardar_Platform SHALL display that string in English as a fallback.
5. WHEN the Scam_Detector produces an explanation, THE Scam_Detector SHALL provide the explanation in both English and Urdu.
6. WHEN a user submits text in English, Urdu, or Roman Urdu, THE Scam_Detector SHALL process the submission in the language provided.
7. WHILE Urdu text is displayed, THE Khabardar_Platform SHALL render Urdu using right-to-left text direction.

### Requirement 5: AI Scam Detector Submission and Classification

**User Story:** As a user, I want to submit a suspicious message and receive a clear risk assessment, so that I can decide whether to trust it.

#### Acceptance Criteria

1. WHEN a user submits SMS, WhatsApp, email, social media, job offer, financial, or suspicious text content of between 1 and 10000 characters, THE Scam_Detector SHALL accept the submission for analysis.
2. IF a submission is empty or exceeds 10000 characters, THEN THE Scam_Detector SHALL reject the submission and return an error indicating the content length is invalid.
3. WHEN the Scam_Detector completes analysis, THE Scam_Detector SHALL return an integer Risk_Score between 0 and 100 inclusive.
4. WHEN the Scam_Detector completes analysis, THE Scam_Detector SHALL assign a Classification of SAFE for a Risk_Score from 0 to 39, SUSPICIOUS for a Risk_Score from 40 to 69, and HIGH RISK for a Risk_Score from 70 to 100.
5. WHEN the Scam_Detector completes analysis, THE Scam_Detector SHALL assign a scam category to the submission.
6. WHEN the Scam_Detector completes analysis, THE Scam_Detector SHALL return a plain-language explanation in both English and Urdu.
7. WHEN the Scam_Detector identifies suspicious content, THE Scam_Detector SHALL list the specific suspicious phrases detected.
8. WHEN the Scam_Detector identifies attack behavior, THE Scam_Detector SHALL list the attack techniques identified.
9. WHEN the Scam_Detector completes analysis, THE Scam_Detector SHALL return recommended actions, a confidence level expressed on a 0.00 to 1.00 scale, and a timestamp.
10. WHEN the Scam_Detector completes analysis, THE Scam_Detector SHALL return the result within 15 seconds of accepting the submission.
11. IF no known scam keyword is found in a submission, THEN THE Scam_Detector SHALL NOT classify the submission as SAFE solely on that basis.

### Requirement 6: Scam Category Coverage

**User Story:** As a user, I want the detector to recognize the scam types common in Pakistan, so that I am protected against realistic threats.

#### Acceptance Criteria

1. WHEN the Scam_Detector analyzes a submission exhibiting phishing or OTP theft characteristics, THE Scam_Detector SHALL produce a result that labels the scam category as phishing or OTP theft respectively and indicates the submission is not SAFE.
2. WHEN the Scam_Detector analyzes a submission exhibiting prize or lottery scam characteristics, THE Scam_Detector SHALL produce a result that labels the scam category as prize or lottery scam and indicates the submission is not SAFE.
3. WHEN the Scam_Detector analyzes a submission exhibiting fake banking, JazzCash impersonation, or Easypaisa impersonation characteristics, THE Scam_Detector SHALL produce a result that labels the corresponding scam category and indicates the submission is not SAFE.
4. WHEN the Scam_Detector analyzes a submission exhibiting fake job offer or advance-fee fraud characteristics, THE Scam_Detector SHALL produce a result that labels the corresponding scam category and indicates the submission is not SAFE.
5. WHEN the Scam_Detector analyzes a submission exhibiting investment scam or romance scam characteristics, THE Scam_Detector SHALL produce a result that labels the corresponding scam category and indicates the submission is not SAFE.
6. WHEN the Scam_Detector analyzes a submission exhibiting social engineering, account takeover, urgent payment demand, or identity impersonation characteristics, THE Scam_Detector SHALL produce a result that labels the corresponding scam category and indicates the submission is not SAFE.
7. IF the Scam_Detector cannot assign a specific scam category to a non-SAFE submission, THEN THE Scam_Detector SHALL label the scam category as "uncategorized" rather than omitting the category.

### Requirement 7: Explainable Detection Signals

**User Story:** As a user, I want to understand why a message was flagged, so that I learn to recognize scams myself.

#### Acceptance Criteria

1. WHEN analyzing a submission, THE Scam_Detector SHALL evaluate suspicious keywords, psychological manipulation, urgency and fear tactics, and authority impersonation, and SHALL record each evaluated signal as either contributing to the Risk_Score or not detected.
2. WHEN analyzing a submission, THE Scam_Detector SHALL evaluate credential and OTP requests, suspicious payment instructions, suspicious links, and linguistic patterns, and SHALL record each evaluated signal as either contributing to the Risk_Score or not detected.
3. THE Scam_Detector SHALL combine Rule_Based_Engine analysis, NLP analysis, AI_Provider_Abstraction classification, and Threat_Intel_Enrichment to produce a result, using available components and the Rule_Based_Engine fallback when an AI provider is unavailable.
4. WHEN the Scam_Detector returns a result, THE Scam_Detector SHALL present each contributing detection signal with its signal name or category, the specific detected content, and the direction of its contribution to the Risk_Score.
5. IF no detection signals are found in a submission, THEN THE Scam_Detector SHALL present an explicit indication that no contributing signals were detected.

### Requirement 8: AI Provider Abstraction and Fallback

**User Story:** As an operator, I want configurable AI providers with an offline fallback, so that the platform keeps working when external AI services are unavailable.

#### Acceptance Criteria

1. THE AI_Provider_Abstraction SHALL support the configurable providers Gemini, Groq, and Ollama.
2. WHEN a detection request is made, THE AI_Provider_Abstraction SHALL select exactly one configured provider and perform an availability health check against it using a configurable connectivity timeout with a default of 5 seconds.
3. WHEN the selected provider passes the availability health check, THE AI_Provider_Abstraction SHALL route the detection request to that provider.
4. IF the selected provider fails the availability health check, THEN THE AI_Provider_Abstraction SHALL return a result produced by the Rule_Based_Engine that includes a Risk_Score and Classification, and SHALL write an Audit_Log entry recording the provider unavailability.
5. IF no AI provider is configured, THEN THE AI_Provider_Abstraction SHALL use the Rule_Based_Engine as the offline fallback and return a result that includes a Risk_Score and Classification.
6. WHEN an AI provider request fails after at most 2 attempts, THE AI_Provider_Abstraction SHALL return a result produced by the Rule_Based_Engine and SHALL write an Audit_Log entry recording the provider failure.
7. THE Khabardar_Platform SHALL store AI provider credentials only on the backend and SHALL load them from environment-based configuration rather than source code.

### Requirement 9: URL and Phishing Analysis

**User Story:** As a user, I want to analyze a suspicious link, so that I know whether it is safe to visit.

#### Acceptance Criteria

1. WHEN a user submits a syntactically valid URL, THE URL_Analyzer SHALL extract the domain from the submission.
2. IF a submitted URL is syntactically invalid, THEN THE URL_Analyzer SHALL reject the submission and return an error indicating the URL is invalid.
3. WHEN a user submits a URL, THE URL_Analyzer SHALL evaluate domain age and WHOIS data, and IF WHOIS data is unavailable, THEN THE URL_Analyzer SHALL mark the domain age and WHOIS results as unavailable rather than omitting them.
4. WHEN a user submits a URL, THE URL_Analyzer SHALL validate HTTPS usage and inspect SSL certificate details, and IF certificate details cannot be retrieved, THEN THE URL_Analyzer SHALL mark the SSL result as unavailable.
5. WHEN a user submits a URL, THE URL_Analyzer SHALL detect redirects, URL shorteners, typosquatting, homograph attacks, suspicious subdomains, and IP-based URLs.
6. WHEN a user submits a URL, THE URL_Analyzer SHALL evaluate domain reputation, phishing database matches, and brand impersonation.
7. WHEN the URL_Analyzer completes analysis, THE URL_Analyzer SHALL return domain information, an integer Risk_Score between 0 and 100 inclusive, reputation data, the redirect chain, detected indicators, an explanation, and a recommended action selected from a defined set.
8. IF the target host is unreachable during analysis, THEN THE URL_Analyzer SHALL complete analysis using the available offline heuristics and mark network-dependent checks as unavailable.
9. WHEN the URL_Analyzer begins analysis, THE URL_Analyzer SHALL return a result within 30 seconds or return a timeout result if analysis does not complete within that time.

### Requirement 10: URL Analyzer External Integrations

**User Story:** As an operator, I want modular threat intelligence integrations for URL analysis, so that results improve when credentials are configured and degrade honestly when they are not.

#### Acceptance Criteria

1. THE URL_Analyzer SHALL provide modular integrations for Google Safe Browsing, VirusTotal, urlscan.io, and WHOIS.
2. WHEN integration credentials are configured for an integration, THE URL_Analyzer SHALL enrich results using that integration, enforcing a per-integration request timeout of 10 seconds.
3. IF integration credentials for an integration are absent, THEN THE URL_Analyzer SHALL display a clearly labeled "unavailable" state for that integration and apply local heuristics instead.
4. IF a configured integration request fails or exceeds its 10 second timeout, THEN THE URL_Analyzer SHALL display a clearly labeled "unavailable" state for that integration, continue the analysis using the remaining checks, and record the integration failure.
5. THE URL_Analyzer SHALL NOT present an integration result as available when the corresponding integration is unavailable.

### Requirement 11: URL Analyzer Security Hardening

**User Story:** As a security-conscious user, I want URL analysis to be performed without exposing my device or the server to risk, so that analysis never triggers an attack.

#### Acceptance Criteria

1. THE URL_Analyzer SHALL NOT open submitted URLs in a browser and SHALL NOT automatically visit submitted URLs outside of the controlled analysis requests defined in these criteria.
2. WHEN processing a URL or redirect destination, THE URL_Analyzer SHALL resolve the target hostname and SHALL block the request if the resolved address falls within loopback addresses (127.0.0.0/8, ::1), private IPv4 ranges (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16), link-local ranges (169.254.0.0/16, fe80::/10), or cloud metadata addresses (169.254.169.254).
3. IF a URL or redirect destination resolves to a blocked address range as defined in criterion 2, THEN THE URL_Analyzer SHALL abort the request without transmitting it and SHALL return a result indicating the request was blocked for security reasons.
4. WHEN processing a redirect chain, THE URL_Analyzer SHALL validate each redirect destination against criterion 2 before following it and SHALL follow no more than 10 redirects per analysis.
5. IF a redirect destination is blocked or the redirect chain exceeds 10 redirects, THEN THE URL_Analyzer SHALL stop following the chain and SHALL return a result indicating the redirect chain was terminated for security reasons.
6. WHEN performing a network request, THE URL_Analyzer SHALL enforce a connection and response timeout of 10 seconds and SHALL limit the downloaded response to a maximum of 5 megabytes.
7. IF a network request exceeds the 10 second timeout or the 5 megabyte response limit, THEN THE URL_Analyzer SHALL terminate the request and SHALL return a result indicating the request failed due to the exceeded limit.
8. THE URL_Analyzer SHALL NOT download to persistent storage or execute any file referenced by a submitted URL.
9. WHEN a user submits a URL, THE URL_Analyzer SHALL validate that the URL uses the http or https scheme and contains a syntactically valid hostname before processing.
10. IF a submitted URL fails format validation as defined in criterion 9, THEN THE URL_Analyzer SHALL reject the URL without performing any network request and SHALL return an error indicating the URL format is invalid.

### Requirement 12: Image, Screenshot, and QR Scanning

**User Story:** As a user, I want to upload a screenshot or QR code and have it analyzed, so that I can check suspicious images without typing text.

#### Acceptance Criteria

1. WHEN a user uploads an image file in PNG, JPEG, or WEBP format of at most 10 megabytes, THE Media_Scanner SHALL accept the image for processing.
2. IF an uploaded file is not in an allowed format or exceeds 10 megabytes, THEN THE Media_Scanner SHALL reject the file and return an error identifying the validation failure.
3. WHEN the Media_Scanner processes an accepted image, THE Media_Scanner SHALL perform image preprocessing and extract text using OCR within 20 seconds.
4. IF OCR text extraction fails for an accepted image, THEN THE Media_Scanner SHALL return an error indicating text could not be extracted and SHALL retain the uploaded image for retry.
5. WHEN the Media_Scanner processes an accepted image, THE Media_Scanner SHALL extract any URLs present in the extracted text.
6. WHEN the Media_Scanner processes an accepted image containing a QR code, THE Media_Scanner SHALL decode the QR code to its encoded value within 20 seconds.
7. IF a QR code in an accepted image cannot be decoded, THEN THE Media_Scanner SHALL indicate that the QR code could not be decoded and continue processing any extracted text.
8. IF no text, URL, or QR content is found in an accepted image, THEN THE Media_Scanner SHALL display a "no content found" indication.
9. WHEN the Media_Scanner extracts text, THE Media_Scanner SHALL display the extracted text for user review before performing scam analysis.
10. WHEN the Media_Scanner extracts text or links and the user confirms analysis, THE Media_Scanner SHALL provide the extracted content to the Scam_Detector and URL_Analyzer for integrated analysis.
11. THE Media_Scanner SHALL NOT automatically open the destination decoded from a QR code.

### Requirement 13: IOC Extraction and Intelligence Correlation

**User Story:** As an analyst, I want the platform to extract and correlate indicators from analyzed content, so that I can see relationships between scam campaigns.

#### Acceptance Criteria

1. WHEN content is analyzed, THE Intelligence_Engine SHALL extract all IOCs present in the content, where extractable IOC types include phone numbers, emails, suspicious domains, URLs, wallet IDs, bank account IDs, payment references, brand impersonation indicators, scam categories, and campaign indicators.
2. IF analyzed content contains no extractable IOCs, THEN THE Intelligence_Engine SHALL record an extraction result containing zero IOCs without raising an error.
3. IF IOC extraction fails for a given content item, THEN THE Intelligence_Engine SHALL retain the original content unchanged and produce a result indicating extraction failure.
4. WHEN IOCs are extracted, THE Intelligence_Engine SHALL normalize each IOC to a canonical form by trimming surrounding whitespace and converting case-insensitive values (emails, domains, URLs) to lowercase.
5. WHEN IOCs are normalized, THE Intelligence_Engine SHALL deduplicate IOCs so that two IOCs with identical type and identical normalized value are stored as a single IOC.
6. WHEN an IOC is extracted and normalized, THE Intelligence_Engine SHALL add or update a corresponding node in the intelligence graph and create edges linking that IOC to the source message, and to any associated domain, phone number, payment ID, template, and campaign.
7. WHEN a newly extracted IOC has the same type and normalized value as an IOC already associated with an existing campaign, THE Intelligence_Engine SHALL associate the new IOC and its source message with that campaign.

### Requirement 14: Safe Honeypot Simulation Lab

**User Story:** As an analyst, I want a safe simulated honeypot, so that I can study scammer tactics without any contact with real scammers.

#### Acceptance Criteria

1. THE Honeypot_Lab SHALL operate as a simulated environment that uses only Synthetic_Data conversations as input and makes no outbound network connections to external systems or endpoints.
2. WHILE operating, THE Honeypot_Lab SHALL restrict all AI persona interactions to internal simulation components, producing no messages, requests, or data transmissions that leave the simulation boundary.
3. WHEN a simulated conversation is generated, THE Honeypot_Lab SHALL extract IOCs from that conversation within 5 seconds of generation completing.
4. IF IOC extraction from a simulated conversation fails, THEN THE Honeypot_Lab SHALL retain the source conversation unchanged, record an extraction-failure indication identifying the affected conversation, and continue processing subsequent conversations.
5. THE Honeypot_Lab SHALL label every record it produces with an origin indicator identifying it as simulated intelligence, distinct from the indicator used for verified real-world intelligence, such that the two origins are machine-distinguishable on every record.
6. IF any operation attempts to contact a scammer, message a phone number, impersonate a victim, or access an external system, THEN THE Honeypot_Lab SHALL block the operation before any outbound action occurs and record a blocked-action indication identifying the attempted operation.

### Requirement 15: SOC Threat Intelligence Dashboard

**User Story:** As a user, I want a SOC-style dashboard summarizing threats, so that I can understand the overall threat landscape at a glance.

#### Acceptance Criteria

1. WHEN the SOC_Dashboard loads, THE SOC_Dashboard SHALL display total analyzed messages, detected scams, high-risk URLs, suspicious domains, reported phone numbers, and scam categories as numeric counts, completing the initial render within 5 seconds.
2. IF any summary metric has a value of zero or no available data, THEN THE SOC_Dashboard SHALL display that metric as the numeric value 0 and SHALL NOT omit the metric or display a blank field.
3. WHEN the SOC_Dashboard loads, THE SOC_Dashboard SHALL display detection trends over the most recent 30 days, recent incidents from the most recent 7 days, and emerging campaigns first detected within the most recent 7 days.
4. WHEN the SOC_Dashboard loads, THE SOC_Dashboard SHALL render a threat trend chart, a category distribution chart, and a risk severity distribution chart, each completing render within 5 seconds.
5. WHEN the SOC_Dashboard loads, THE SOC_Dashboard SHALL render an IOC relationship graph using a NetworkX-based backend and a Cytoscape.js-based frontend visualization, displaying up to a maximum of 500 nodes and 2000 edges.
6. IF the IOC relationship graph fails to render or exceeds the 500-node or 2000-edge maximum, THEN THE SOC_Dashboard SHALL display an error indication informing the user that the graph could not be fully displayed and SHALL retain all other dashboard sections in their rendered state.
7. WHEN the SOC_Dashboard loads, THE SOC_Dashboard SHALL display an incident feed containing up to a maximum of 100 incidents ordered from most recent to oldest, and a campaign correlation visualization.
8. THE SOC_Dashboard SHALL label the environment as a prototype intelligence environment and SHALL NOT present it as a live nationwide feed.

### Requirement 16: MITRE ATT&CK Mapping

**User Story:** As an analyst, I want detected behaviors mapped to MITRE ATT&CK techniques, so that findings align with a recognized framework.

#### Acceptance Criteria

1. WHEN a detected behavior matches a MITRE ATT&CK technique with a mapping confidence score of at least 0.70 on a 0.00 to 1.00 scale, THE SOC_Dashboard SHALL assign the matching MITRE_Mapping, displaying both the technique identifier and technique name (for example, T1566 Phishing, T1583 Acquire Infrastructure, or T1204 User Execution).
2. THE SOC_Dashboard SHALL assign a MITRE_Mapping only when the mapping is supported by at least one detected behavior with a confidence score of at least 0.70.
3. THE SOC_Dashboard SHALL NOT assign a MITRE_Mapping to any detected behavior whose highest mapping confidence score is below 0.70.
4. WHEN a single detected behavior matches more than one MITRE ATT&CK technique with a confidence score of at least 0.70, THE SOC_Dashboard SHALL assign all such MITRE_Mappings, ordered from highest to lowest confidence score.
5. IF a detected behavior has no MITRE ATT&CK technique with a confidence score of at least 0.70, THEN THE SOC_Dashboard SHALL leave the behavior without a MITRE_Mapping and display an indication that no mapping was assigned, while retaining the detected behavior record.

### Requirement 17: Family Protection

**User Story:** As a user, I want to protect my family members, so that they receive alerts about scams I encounter.

#### Acceptance Criteria

1. WHEN a user adds a trusted family member, THE Family_Protection SHALL record the family member in the user's family group.
2. WHEN a user invites a family member, THE Family_Protection SHALL generate an invitation that expires 7 days after it is generated.
3. WHEN an invited family member accepts an invitation before it expires, THE Family_Protection SHALL add that member to the inviting user's family group and record the member's consent.
4. IF an invited family member attempts to accept an expired invitation, THEN THE Family_Protection SHALL reject the acceptance and indicate the invitation has expired.
5. WHEN a user configures notification preferences, THE Family_Protection SHALL store the selected preferences.
6. WHEN a user chooses to share a selected suspicious report, THE Family_Protection SHALL share only the selected report with the designated family members who have provided consent.
7. IF a user attempts to share a report with a family member who has not provided consent, THEN THE Family_Protection SHALL block the share and indicate that consent is required.
8. WHEN a high-risk scam is detected for a user, THE Family_Protection SHALL send a high-risk alert to family members according to their notification preferences within 60 seconds of detection.
9. THE Family_Protection SHALL require explicit consent and enforce access controls before sharing any report.
10. THE Family_Protection SHALL NOT automatically share a user's private messages.

### Requirement 18: Authentication and Authorization

**User Story:** As a user, I want secure authentication and role-based access, so that my account and data are protected.

#### Acceptance Criteria

1. WHEN a user authenticates successfully, THE Khabardar_Platform SHALL issue a JWT access token with an expiry of between 15 minutes and 24 hours from issuance.
2. WHEN a user registers or sets a password, THE Khabardar_Platform SHALL hash the password using Argon2 or bcrypt and SHALL NOT store the password in plaintext.
3. WHEN a user requests a protected resource, THE Khabardar_Platform SHALL enforce RBAC based on the user's role.
4. IF a request for a protected resource lacks a JWT token, presents an expired JWT token, or presents a malformed JWT token, THEN THE Khabardar_Platform SHALL reject the request with an authentication error and SHALL NOT return the protected resource.
5. IF a user requests a resource outside the user's authorized role, THEN THE Khabardar_Platform SHALL reject the request with an authorization error and SHALL NOT return the resource.
6. WHEN a user's authentication attempt fails, THE Khabardar_Platform SHALL reject the attempt without issuing a token, and IF a user exceeds 5 consecutive failed attempts within 15 minutes, THEN THE Khabardar_Platform SHALL temporarily block further attempts for that user for at least 15 minutes.

### Requirement 19: Platform Security Controls

**User Story:** As an operator, I want platform-wide security controls, so that the application resists common attacks.

#### Acceptance Criteria

1. WHEN the Khabardar_Platform receives input, THE Khabardar_Platform SHALL validate the input against expected type, format, and length before processing, and IF validation fails, THEN THE Khabardar_Platform SHALL reject the request with a validation error.
2. WHEN a client exceeds 100 API requests within a 60-second window, THE Khabardar_Platform SHALL reject further requests from that client for the remainder of the window with a rate-limit error.
3. THE Khabardar_Platform SHALL enforce a CORS configuration that allows requests only from an explicitly configured allowlist of origins.
4. THE Khabardar_Platform SHALL load secrets from environment-based configuration rather than source code.
5. WHEN authentication, authorization, data deletion, report sharing, provider failure, or a blocked security request occurs, THE Khabardar_Platform SHALL write an Audit_Log entry recording the action, the actor, and the timestamp.
6. IF input contains executable script or markup intended for XSS, THEN THE Khabardar_Platform SHALL neutralize the content before storing or rendering it.
7. THE Khabardar_Platform SHALL use parameterized queries for all database access to prevent SQL injection.
8. WHEN the Khabardar_Platform makes an outbound request on behalf of user input, THE Khabardar_Platform SHALL apply the SSRF protections defined in Requirement 11.
9. WHEN a user uploads a file, THE Khabardar_Platform SHALL apply the file validation defined in Requirement 12 before processing the file.

### Requirement 20: Data Model and Persistence

**User Story:** As a developer, I want a normalized database schema, so that platform data is stored consistently and portably.

#### Acceptance Criteria

1. THE Khabardar_Platform SHALL define normalized models for Users, ScanHistory, ScamReports, URLAnalysis, ThreatIndicators, ScamCampaigns, FamilyGroups, FamilyMembers, Notifications, AuditLogs, and HoneypotSessions.
2. THE Khabardar_Platform SHALL use SQLite for development and SHALL maintain a schema compatible with PostgreSQL.
3. WHEN a scan is performed, THE Khabardar_Platform SHALL persist the scan result to ScanHistory associated with the user who performed the scan.
4. IF persistence of a scan result fails, THEN THE Khabardar_Platform SHALL return an error indicating the result could not be saved and SHALL still display the computed result to the user.
5. WHEN a user views Scan History or Reports, THE Khabardar_Platform SHALL retrieve only the persisted records associated with that user.
6. IF a user has no persisted records when viewing Scan History or Reports, THEN THE Khabardar_Platform SHALL display an empty-state indication rather than an error.

### Requirement 21: Privacy and Sensitive Data Handling

**User Story:** As a user, I want my sensitive data minimized and protected, so that my privacy is preserved even when analyzing scam messages.

#### Acceptance Criteria

1. THE Khabardar_Platform SHALL store only the sensitive data items required to produce and display an analysis result, and SHALL NOT persist any sensitive data item not used by the analysis.
2. WHEN storing analyzed content containing OTPs, passwords, authentication tokens, or personally identifiable information (including full names, phone numbers, email addresses, physical addresses, government-issued identifiers, and financial account numbers), THE Khabardar_Platform SHALL replace each such value with a masked form that reveals at most the final 4 characters and from which the original value cannot be reconstructed.
3. WHEN an exact identifier value is not required for analysis or display, THE Khabardar_Platform SHALL store a one-way, irreversible hashed form of the identifier instead of the raw value.
4. THE Khabardar_Platform SHALL store any password or OTP contained in a scam message only in a masked or hashed form from which the original value cannot be recovered, and SHALL NOT persist it in readable plaintext.
5. THE Khabardar_Platform SHALL provide an administrator-configurable retention period for stored records, accepting values from 1 day to 3650 days (10 years) inclusive.
6. WHEN the configured retention period elapses for a record, THE Khabardar_Platform SHALL permanently delete that record, including all associated masked and hashed sensitive data, within 24 hours of the period elapsing.
7. IF deletion of a record fails, THEN THE Khabardar_Platform SHALL retain the record in its masked/hashed form, record a deletion-failure indication, and retry deletion on the next retention cycle.

### Requirement 22: Honesty and Integrity of Results

**User Story:** As a user, I want the platform to be honest about what it can and cannot do, so that I can trust the results it shows.

#### Acceptance Criteria

1. THE Khabardar_Platform SHALL NOT present non-functional placeholder UI as functional capability.
2. THE Khabardar_Platform SHALL NOT display hardcoded fabricated detection results within the real detection workflow.
3. WHERE Synthetic_Data is used, THE Khabardar_Platform SHALL display a persistent visible label identifying the content as demo or simulation data, and SHALL restrict such data to demo and simulation environments only.
4. THE Khabardar_Platform SHALL NOT expose API keys in the frontend or in source code.
5. IF an integration has not been tested as working, THEN THE Khabardar_Platform SHALL NOT claim the integration works.
6. WHEN a capability or integration is unavailable, THE Khabardar_Platform SHALL display a visible state indicating the capability is unavailable and SHALL disable the associated action controls so the capability cannot be invoked.
7. IF an error occurs during a user operation, THEN THE Khabardar_Platform SHALL display a user-facing message identifying the failed operation and SHALL preserve any user-entered data without partial modification.

### Requirement 23: Accuracy Reporting

**User Story:** As a user, I want reported accuracy to reflect real measurements, so that I am not misled by invented statistics.

#### Acceptance Criteria

1. THE Khabardar_Platform SHALL NOT display any accuracy metric value that was not produced by the measured evaluation process defined in Requirement 24.
2. WHEN the Khabardar_Platform displays accuracy metrics, THE Khabardar_Platform SHALL display only measured values of precision, recall, F1, false positive rate, false negative rate, and average response time obtained from the most recent completed evaluation run.
3. WHEN the Khabardar_Platform displays accuracy metrics, THE Khabardar_Platform SHALL display the date of the evaluation run and the size of the evaluation dataset used to produce those metrics.
4. IF no completed evaluation run exists, THEN THE Khabardar_Platform SHALL display a clearly labeled "accuracy not yet measured" state instead of any numeric accuracy metric.

### Requirement 24: Testing and Evaluation

**User Story:** As a developer, I want automated tests and a reproducible evaluation, so that detection quality is verifiable and measurable.

#### Acceptance Criteria

1. WHEN the automated test suite is executed, THE Khabardar_Platform SHALL run tests that submit English, Urdu, and Roman Urdu scam messages, legitimate banking messages, fake prize messages, and OTP theft messages to the Scam_Detector, and each such test SHALL assert the expected Classification and pass only when the returned Classification matches the expected label.
2. WHEN the automated test suite is executed, THE Khabardar_Platform SHALL run tests covering phishing URLs, typosquatting, malformed URLs, private-IP blocking, and SSRF protection, and each such test SHALL pass only when the URL_Analyzer returns the expected indicator detection, rejects the malformed input, and blocks requests to localhost, private IP ranges, and cloud metadata endpoints.
3. WHEN the automated test suite is executed, THE Khabardar_Platform SHALL run tests covering image upload validation, QR decoding, and AI provider failure, and each such test SHALL pass only when invalid files are rejected, a valid QR code is decoded to its encoded value, and an AI provider failure results in a Rule_Based_Engine fallback result with the provider failure recorded.
4. WHEN the automated test suite is executed, THE Khabardar_Platform SHALL run tests covering authentication, access control, and database operations, and each such test SHALL pass only when a request without a valid JWT token is rejected with an authentication error, a request outside the user's authorized role is rejected with an authorization error, and a persisted scan record is retrievable for its owning user.
5. WHEN the evaluation process is executed, THE Khabardar_Platform SHALL compute and record precision, recall, F1 score, false positive rate, and false negative rate as values between 0 and 1, and average response time in milliseconds, over a fixed labeled dataset of at least 100 examples containing both legitimate messages and Synthetic_Data scam examples.
6. WHEN the evaluation process is executed more than once on the same fixed labeled dataset without code or dataset changes, THE Khabardar_Platform SHALL produce identical precision, recall, F1 score, false positive rate, and false negative rate values across runs.

### Requirement 25: Local Operation and Documentation

**User Story:** As a developer, I want the platform to run locally on Windows with documented setup, so that I can build and demo it reliably.

#### Acceptance Criteria

1. THE Khabardar_Platform SHALL run locally on Windows 10 and Windows 11.
2. THE Khabardar_Platform SHALL provide setup documentation that lists the required prerequisites and their versions and the ordered setup commands for both the frontend and the backend.
3. WHEN a developer follows the documented setup commands, THE Khabardar_Platform SHALL start the frontend and the backend as locally accessible services reachable via local addresses within 120 seconds.
4. IF any documented setup command fails, THEN THE Khabardar_Platform SHALL halt the setup and present an error indicating which command failed and the cause.

---

## Hackathon Readiness Review and MVP Scoping

This section is an analysis layer added on top of the 25 requirements above. It does not remove or override any requirement. It classifies each requirement into **Scope A (Hackathon MVP, mandatory)** or **Scope B (Advanced / Future)**, flags risks and dependencies, and defines the measurable MVP acceptance bar. Where a requirement spans both scopes, the MVP portion is called out explicitly.

Guardrails honored throughout this review:
- No accuracy percentages or performance benchmarks are invented. The classification threshold boundaries (0–39 / 40–69 / 70–100) in Requirement 5.4 are treated as an untested initial heuristic to be calibrated against the evaluation dataset (Requirement 24), not as a validated standard.
- No threat-intelligence integration is assumed operational. All external integrations are treated as unverified until a real API key is configured and a live call succeeds.

### Scope Classification Summary

| Req | Area | Scope | MVP Notes |
|-----|------|-------|-----------|
| 1 | Branded splash screen | A | Mandatory. Pure frontend, no paid API. |
| 2 | Design system (palette, theme, responsive, contrast) | A | Mandatory. Pure frontend. |
| 3 | App shell & navigation (12 pages) | A (partial) | MVP ships all page routes; Honeypot and Family Protection pages exist as clearly-labeled "coming soon / advanced" placeholders per Req 22.1 (not fake-functional). |
| 4 | Multilingual (EN / Urdu / Roman Urdu) | A | Mandatory. UI i18n + detector language handling. No paid API required. |
| 5 | Scam detector submission & classification | A | Mandatory core. Threshold boundaries flagged as untested heuristic. |
| 6 | Scam category coverage | A | Mandatory. Rule-based categories cover MVP; AI improves recall when available. |
| 7 | Explainable detection signals | A | Mandatory. This is the key demo differentiator. |
| 8 | AI provider abstraction + offline fallback | A | Mandatory. MVP must be fully functional on the Rule_Based_Engine with zero API keys. AI providers are an enhancement layer. |
| 9 | URL & phishing analysis | A | Mandatory. Local heuristics (typosquatting, homograph, IP-URL, shortener, subdomain) require no paid API. |
| 10 | URL external integrations (Safe Browsing, VirusTotal, urlscan.io, WHOIS) | B | Future. Each requires an API key. MVP shows honest "unavailable" states (Req 10.3). WHOIS/SSL may work keyless but are network-dependent and unreliable — treat as best-effort, not MVP-blocking. |
| 11 | URL analyzer security hardening (SSRF, redirect, timeouts) | A | Mandatory and non-negotiable. Must ship even if no network checks run, because any outbound fetch without it is a live SSRF risk. |
| 12 | Image / screenshot / QR scanning | A | Mandatory. Local OCR (Tesseract) + local QR decode. No paid API. |
| 13 | IOC extraction & normalization | A (partial) | Extraction, normalization, dedup = MVP. Full cross-message campaign auto-association (13.7) = basic in MVP, advanced in Scope B. |
| 14 | Safe honeypot simulation lab | B | Future. High complexity (AI persona + synthetic generation). Not MVP-blocking. Safety constraints in Req 14 still apply whenever built. |
| 15 | SOC dashboard | A (partial) | Stat cards, charts, incident feed, and a basic IOC relationship graph = MVP. Rich campaign-correlation visualization = Scope B. |
| 16 | MITRE ATT&CK mapping | A (partial) | A small curated rule-to-technique map (e.g., T1566, T1204) tied to detected behavior = MVP-light. Broad confidence-scored mapping = Scope B. |
| 17 | Family protection & alerts | B | Future. Requires multi-user, invitations, consent, notification delivery. Not MVP-blocking. |
| 18 | Authentication & authorization | A (reduced) | MVP: single local account or no-auth local mode is acceptable for demo; password hashing used if auth is present. Full RBAC + multi-user = Scope B. |
| 19 | Platform security controls | A (partial) | Input validation, parameterized queries (SQLi), XSS neutralization, SSRF (via Req 11), upload validation (via Req 12), env secrets = MVP. Rate limiting + full audit log = recommended but can be minimal in MVP. |
| 20 | Data model & persistence | A | Mandatory. SQLite + SQLAlchemy. Scan history and reports depend on this. |
| 21 | Privacy & sensitive data handling | A (partial) | Masking OTP/passwords and not storing plaintext secrets = MVP. Configurable retention + scheduled deletion job = Scope B. |
| 22 | Honesty & integrity of results | A | Mandatory and cross-cutting. Governs how placeholders and unavailable integrations are shown. |
| 23 | Accuracy reporting | A | Mandatory discipline. MVP shows "accuracy not yet measured" until Req 24 evaluation runs. |
| 24 | Testing & evaluation | A (partial) | Core detector/URL/upload/SSRF tests + a reproducible evaluation harness = MVP. Full coverage of auth/RBAC/honeypot = Scope B. |
| 25 | Local operation & documentation | A | Mandatory. Must run on Windows with documented commands. |

### 1. Requirements Too Broad for a Hackathon

- **Req 8 (AI providers):** Supporting Gemini, Groq, and Ollama all at once is broad. MVP recommendation: ship the abstraction interface plus the Rule_Based_Engine fallback as the guaranteed path, and wire in exactly one optional provider (Groq or Gemini) behind an env key. The interface satisfies "modular"; the fallback satisfies "works offline."
- **Req 10 (four external integrations):** Four separate threat-intel integrations is broad and every one needs a key and live verification. MVP: build the modular adapter seam and render honest "unavailable" states; defer live integrations to Scope B.
- **Req 13.7 + Req 15 (campaign correlation):** Full campaign auto-correlation and a rich correlation visualization is a research-grade feature. MVP: a basic shared-IOC graph (nodes + edges) is enough to demo the concept.
- **Req 16 (MITRE mapping):** Confidence-scored mapping across the ATT&CK matrix is broad. MVP: a small, explicit, behavior-triggered lookup table for a handful of techniques.
- **Req 14 (honeypot) and Req 17 (family protection):** Both are self-contained advanced modules — correctly deferred to Scope B.

### 2. Overlapping / Redundant Requirements

- **SSRF appears in Req 11 and Req 19.8** — intentional: Req 11 is the detailed spec, Req 19.8 references it. No change needed; just implement once in a shared URL-safety guard.
- **Upload validation appears in Req 12.1–12.2 and Req 19.9** — same pattern; implement once, reference from both.
- **Credential storage appears in Req 8.7, Req 18.2, and Req 19.4** — all point to the same env-based secrets practice. Consolidate into one config/secrets module.
- **Risk_Score range (0–100) is restated in Req 5.3 and Req 9.7** — acceptable; they describe two different analyzers producing scores on the same scale.
- **"Unavailable" state honesty appears in Req 10, Req 22.6, and Req 9.3/9.4** — one shared UI pattern should serve all.

### 3. Missing Dependencies (recommend adding before/with design)

- **Tesseract OCR engine** (and Urdu language data if Urdu OCR is attempted) is an external system dependency for Req 12 — must be documented in Req 25 setup. Urdu OCR quality is known to be weak; MVP should not promise reliable Urdu OCR, only best-effort.
- **A QR decode library** (e.g., pyzbar/zbar or an OpenCV-based decoder) — native dependency that must be in setup docs.
- **A seed/sample dataset** is required for Req 24's reproducible evaluation and for a compelling demo. This is currently implied but not a standalone requirement. Recommend treating the labeled sample dataset as an explicit MVP deliverable.
- **Roman Urdu handling** has no normalization standard; the detector needs a defined keyword/lexicon strategy. This is a content dependency, not just code.
- **The Official_Logo asset** is not yet in the workspace. MVP cannot satisfy Req 1 until it is supplied; Req 1.8 fallback covers the interim.

### 4. Features Requiring Paid / Keyed API Access

- Req 10 integrations: **Google Safe Browsing, VirusTotal, urlscan.io** (all need API keys; free tiers exist but are rate-limited and still require signup).
- Req 8 cloud AI providers: **Gemini, Groq** (keyed; free tiers exist but are not guaranteed).
- None of these are MVP-blocking. All degrade to honest "unavailable" or to the local fallback.

### 5. Features That Operate With No Paid API

- Splash, design system, navigation, multilingual UI (Req 1–4).
- Rule-based + local NLP scam detection and explainability (Req 5–7 via the fallback path).
- Local URL heuristics and SSRF-safe analysis, keyless WHOIS/SSL as best-effort (Req 9, 11).
- Local OCR and QR decode (Req 12).
- IOC extraction/normalization and the local intelligence graph (Req 13, 15 basic).
- Ollama as a fully local, no-cost AI option (Req 8) if the demo machine can run it.
- SQLite persistence, scan history, reports (Req 20).

This means **the entire MVP can run and demo with zero paid keys**, which is the intended robustness.

### 6. Security Risks and Implementation Complexity

- **Highest risk — SSRF (Req 11):** The moment the server fetches a user-supplied URL, it can be coerced into hitting internal/cloud-metadata endpoints. The guard in Req 11 must exist before any outbound fetch is enabled. Complexity: medium. Non-negotiable for MVP.
- **Malicious file upload (Req 12, 19.9):** Validate type by content, cap size, never execute, store outside web root. Complexity: low–medium.
- **XSS from scam content (Req 19.6):** Scam messages are attacker-controlled text rendered back to the user — must be escaped/sanitized on display. Complexity: low.
- **Secret leakage (Req 8.7, 22.4):** Keys must never reach the frontend bundle. Complexity: low with discipline.
- **Privacy of stored scam content (Req 21):** Masking secrets inside analyzed messages is subtle. Complexity: medium. MVP does masking; scheduled deletion deferred.
- **Auth complexity (Req 18):** Full JWT + RBAC + lockout is medium-high effort with low demo payoff. Reducing MVP to a single local user lowers risk surface and build cost.

### 7. Measurable MVP Acceptance Criteria (the bar the MVP must clear)

The MVP is considered demo-ready only when ALL of the following hold, each verifiable:

1. **MVP-AC-1 (Splash):** On launch the splash shows only logo + "KHABARDAR" + tagline on Deep Navy, then auto-advances to the dashboard after ~2s (Req 1). If the logo asset is absent, the Req 1.8 fallback renders and still advances.
2. **MVP-AC-2 (Shell & theme):** All 12 pages are routable; dark theme is default; theme and language selections persist across reload; no horizontal overflow at 375px, 768px, and 1280px widths (Req 2, 3, 4).
3. **MVP-AC-3 (Detection, offline):** With no AI keys configured, submitting a known scam sample returns a Risk_Score, a SAFE/SUSPICIOUS/HIGH RISK Classification, a category, an EN+Urdu explanation, and at least one listed contributing signal — produced entirely by the Rule_Based_Engine (Req 5, 6, 7, 8.5).
4. **MVP-AC-4 (Detection honesty):** A message with no known keywords is never auto-labeled SAFE on that basis alone (Req 5.11), and a message with no signals shows an explicit "no signals detected" state (Req 7.5).
5. **MVP-AC-5 (URL analysis + SSRF):** Submitting a URL returns domain info, a Risk_Score, detected local indicators, an explanation, and a recommended action; a URL resolving to localhost / a private range / the cloud-metadata address is blocked with a security-blocked result and no outbound request is made (Req 9, 11).
6. **MVP-AC-6 (Media):** Uploading a valid screenshot returns OCR text shown for review before analysis; a QR image decodes to its value without auto-opening it; oversized/wrong-type files are rejected with a clear error (Req 12).
7. **MVP-AC-7 (Intelligence + dashboard):** Analyzed content yields normalized, deduplicated IOCs; the SOC dashboard renders stat cards (showing 0 when empty), the three charts, an incident feed, and a basic IOC relationship graph, and is labeled a prototype environment (Req 13, 15).
8. **MVP-AC-8 (History & reports):** A performed scan persists and is retrievable in Scan History and Reports for the acting user; an empty account shows an empty-state, not an error (Req 20).
9. **MVP-AC-9 (Integration honesty):** Every unconfigured external integration is shown as a labeled "unavailable" state and is never presented as a real result (Req 10, 22.5, 22.6).
10. **MVP-AC-10 (Accuracy honesty):** Until the Req 24 evaluation harness has been run on the sample dataset, the UI shows "accuracy not yet measured" and displays no invented metric (Req 23).
11. **MVP-AC-11 (Runs on Windows):** Documented setup commands bring up frontend and backend locally on Windows following Req 25.
12. **MVP-AC-12 (Baseline security):** Inputs are validated, DB access is parameterized, scam text is escaped on render, uploads are validated, and no secret appears in the frontend bundle (Req 19, 22.4).

### 8. Prioritized Build Order (technical value × demo impact × feasibility)

**P0 — Foundation + headline demo (build first):**
1. Project scaffold, SQLite + models, config/secrets module, security baseline (Req 19, 20, 22, 25).
2. Splash + design system + shell + i18n (Req 1–4).
3. Rule-based scam detector with explainability + EN/Urdu output (Req 5, 6, 7, offline path of 8).
4. SSRF-safe URL analyzer with local heuristics (Req 9, 11).

**P1 — Completes the MVP story:**
5. OCR + QR media scanner feeding the detector/URL analyzer (Req 12).
6. IOC extraction/normalization + SOC dashboard with charts and a basic graph (Req 13, 15 basic, 16-light).
7. Scan history + reports (Req 20 read paths).
8. Evaluation harness + sample dataset + measured-only accuracy display (Req 23, 24 core).

**P2 — Enhancements (only after MVP passes its acceptance bar):**
9. Optional live AI provider wiring (one provider) (Req 8 online path).
10. Live URL threat-intel integrations as keys become available (Req 10).

**Scope B — Advanced / Future (post-MVP):**
11. Honeypot simulation lab (Req 14).
12. Family protection + notifications (Req 17).
13. Advanced campaign intelligence + rich correlation viz (Req 13.7 advanced, 15 advanced).
14. Full auth + RBAC + multi-user deployment (Req 18 full, 21 retention automation).

### Vision Preservation Note

This scoping does not change the product vision: KHABARDAR remains a serious, multilingual, explainable, SOC-styled scam-protection platform. Scope B features stay first-class requirements (Req 14, 17, and the advanced portions of 8, 10, 13, 15, 16, 18, 21) — they are sequenced after the MVP clears its acceptance bar, not dropped. The honesty and safety requirements (Req 11, 14, 22, 23) apply to every scope at all times.
