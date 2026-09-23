[README.md](https://github.com/user-attachments/files/32570793/README.md)
# MAINTAIN-AI - STEP BY STEP BUILD GUIDE FOR NIGERIA OIL SERVICE COMPANIES
# For Engineer with Little Python Knowledge

## WHAT YOU HAVE IN THIS FOLDER:
1. sample_maintenance_log.xlsx - Example logs (Bonny, Onne, Forcados)
2. app_rule_based.py - VERSION 1: Works offline, no AI key needed
3. app_ai_version.py - VERSION 2: Uses ChatGPT brain
4. requirements.txt - Libraries needed
5. run_rule_based.bat - Double click to start (Windows)

## STEP 1: INSTALL PYTHON (10 mins)
1. Go to python.org -> Downloads -> Download Python 3.11
2. During install, TICK "Add python.exe to PATH" (very important!)
3. Verify: Open CMD, type: python --version

## STEP 2: BUILD RULE-BASED VERSION (30 mins) - DO THIS FIRST
This is your MVP. No internet needed after install.

Commands in CMD (navigate to folder):
cd path\to\maintenance_agent
pip install -r requirements.txt
streamlit run app_rule_based.py

What it does:
- Reads your Excel
- Flags if Last Service > 90 days ago (you can change 90)
- Flags if same Asset Tag failed 3+ times
- Auto-drafts Work Order in NUPRC format

Logic you can understand and edit:
if Days_Since_Service > 90: OVERDUE
if Failure_Count > 2: RECURRING
if both: PRIORITY = CRITICAL

## STEP 3: TEST WITH YOUR DATA (15 mins)
1. Replace sample_maintenance_log.xlsx with your real log
2. Must have columns: Date | Asset Tag | Equipment | Failure | Hours Run | Last Service | Location
3. Re-upload in app

## STEP 4: BUILD AI VERSION (1 hour) - AFTER RULE-BASED WORKS
1. Get OpenAI API key:
   - Go to platform.openai.com -> Sign up -> API Keys -> Create
   - You need $5 credit (approx ₦8,000). One work order costs ~₦50.
2. Run: streamlit run app_ai_version.py
3. Paste API key in sidebar
4. Click "Generate AI Analysis"

What AI adds:
- Instead of just "3 failures", AI says: "Root cause likely fuel contamination due to dusty Niger Delta + irregular filter change - common on CAT 3512B in Bonny"
- Writes professional English work order you can send to Shell/Total
- Suggests local parts: "OEM: CAT 1R-1808, Alternative: Available at Ladipo Market, Lagos"

## STEP 5: DEPLOY FOR FIELD ENGINEERS (No-Code)
- Use Google Form -> Google Sheet -> Your Python app reads Sheet
- Engineers in field submit via WhatsApp: "GEN-02 vibrating again + photo"
- You get auto Work Order

## HOW TO SELL IN NIGERIA:
- Demo: Show client their own overdue assets in 2 mins (they love it)
- Price: ₦150k/month per 10 assets monitored (rule-based) or ₦250k (AI)
- Pitch: "We reduce unplanned downtime by 30% and give you monthly MTBF report for your NUPRC audit and IOC contract renewal"

## NEXT STEPS AFTER THIS:
- Add WhatsApp alert using Twilio (5 lines code)
- Connect to SAP PM if client has it (replace Excel with SAP export)
- Build dashboard with Power BI

Need help? Ask: "How do I add WhatsApp?" or "How to connect my SAP export?"
